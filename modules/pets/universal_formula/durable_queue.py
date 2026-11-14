"""SQLite-backed local work queue for restartable Universal Formula tasks.

The queue stores declarative task data only. It never stores executable code,
credentials, or grants permissions. Registered engine handlers and PolicyGate
remain authoritative at execution time.
"""
from contextlib import contextmanager
import json
import sqlite3
import time
from pathlib import Path

from .engine import Task, TaskStatus


class DurableTaskQueue:
    def __init__(self, database_path, lease_seconds=300, clock=None):
        if lease_seconds <= 0:
            raise ValueError("lease_seconds must be positive")
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.lease_seconds = float(lease_seconds)
        self._clock = clock or time.time
        with self._connect() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS work_items (
                    task_id TEXT PRIMARY KEY,
                    handler TEXT NOT NULL,
                    action TEXT NOT NULL,
                    depends_on TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    max_attempts INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    lease_until REAL,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    outcome TEXT
                )
            """)
            db.execute("CREATE INDEX IF NOT EXISTS work_items_ready ON work_items(status, lease_until, created_at)")

    @contextmanager
    def _connect(self):
        """Yield a configured connection and always close it after the transaction."""
        db = sqlite3.connect(str(self.database_path), timeout=30)
        db.row_factory = sqlite3.Row
        try:
            db.execute("PRAGMA journal_mode=WAL")
            db.execute("PRAGMA synchronous=FULL")
            with db:
                yield db
        finally:
            db.close()

    def enqueue(self, task):
        if not isinstance(task, Task):
            raise TypeError("enqueue expects a Task")
        if task.status != TaskStatus.PENDING.value or task.attempts != 0:
            raise ValueError("only new pending tasks may be enqueued")
        try:
            payload = json.dumps(task.payload, sort_keys=True, allow_nan=False)
            dependencies = json.dumps(list(task.depends_on), sort_keys=True, allow_nan=False)
        except (TypeError, ValueError) as exc:
            raise ValueError("task payload and dependencies must be JSON serializable") from exc
        now = self._clock()
        with self._connect() as db:
            db.execute("""
                INSERT INTO work_items
                (task_id, handler, action, depends_on, payload, max_attempts,
                 status, lease_until, created_at, updated_at, outcome)
                VALUES (?, ?, ?, ?, ?, ?, 'queued', NULL, ?, ?, NULL)
            """, (task.task_id, task.handler, task.action, dependencies, payload,
                  task.max_attempts, now, now))
        return task.task_id

    def discover(self, engine, limit=25):
        """Lease eligible items using keyset pages to avoid blocked-row starvation."""
        if limit < 1:
            raise ValueError("limit must be positive")
        now = self._clock()
        discovered = []
        page_size = max(limit * 2, 50)
        cursor_created_at = None
        cursor_task_id = None
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            selected_ids = set(engine.tasks)
            while len(discovered) < limit:
                if cursor_created_at is None:
                    rows = db.execute("""
                        SELECT * FROM work_items
                        WHERE status = 'queued' OR (status = 'leased' AND lease_until <= ?)
                        ORDER BY created_at, task_id LIMIT ?
                    """, (now, page_size)).fetchall()
                else:
                    rows = db.execute("""
                        SELECT * FROM work_items
                        WHERE (status = 'queued' OR (status = 'leased' AND lease_until <= ?))
                          AND (created_at > ? OR (created_at = ? AND task_id > ?))
                        ORDER BY created_at, task_id LIMIT ?
                    """, (now, cursor_created_at, cursor_created_at, cursor_task_id, page_size)).fetchall()
                if not rows:
                    break
                for row in rows:
                    cursor_created_at = row["created_at"]
                    cursor_task_id = row["task_id"]
                    if row["task_id"] in selected_ids:
                        continue
                    dependencies = json.loads(row["depends_on"])
                    if any(dep not in selected_ids for dep in dependencies):
                        continue
                    changed = db.execute("""
                        UPDATE work_items SET status='leased', lease_until=?, updated_at=?
                        WHERE task_id=? AND (status='queued' OR (status='leased' AND lease_until <= ?))
                    """, (now + self.lease_seconds, now, row["task_id"], now)).rowcount
                    if not changed:
                        continue
                    discovered.append(Task(
                        task_id=row["task_id"],
                        handler=row["handler"],
                        action=row["action"],
                        depends_on=dependencies,
                        payload=json.loads(row["payload"]),
                        max_attempts=row["max_attempts"],
                    ))
                    selected_ids.add(row["task_id"])
                    if len(discovered) >= limit:
                        break
                if len(rows) < page_size:
                    break
        return discovered

    def reconcile(self, snapshot):
        """Mark terminal engine outcomes; keep nonterminal work leased for recovery."""
        now = self._clock()
        terminal = {
            TaskStatus.PASSED.value: "completed",
            TaskStatus.FAILED.value: "failed",
            TaskStatus.BLOCKED.value: "blocked",
        }
        with self._connect() as db:
            for task_id, task in snapshot.items():
                outcome = terminal.get(task["status"])
                if outcome:
                    db.execute("""
                        UPDATE work_items SET status=?, lease_until=NULL,
                            updated_at=?, outcome=? WHERE task_id=? AND status='leased'
                    """, (outcome, now, outcome, task_id))

    def task_source(self, engine, health_snapshot=None):
        return self.discover(engine)

    def after_cycle(self, snapshot):
        self.reconcile(snapshot)

    def counts(self):
        with self._connect() as db:
            return {row["status"]: row["count"] for row in db.execute(
                "SELECT status, COUNT(*) AS count FROM work_items GROUP BY status"
            )}
