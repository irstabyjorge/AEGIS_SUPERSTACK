"""Bounded task orchestration with dependencies, checkpoints, and retries.

This module schedules registered local handlers. It does not create AI agents,
execute generated source, access networks, or grant external permissions.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass, field
from enum import Enum
import json
import os
from pathlib import Path
import tempfile
from threading import Lock
from typing import Callable, Dict, Iterable, Optional

from .policy import ActionClass, PolicyGate


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    BLOCKED = "blocked"


@dataclass
class Task:
    task_id: str
    handler: str
    action: str = ActionClass.ANALYZE.value
    depends_on: list = field(default_factory=list)
    payload: dict = field(default_factory=dict)
    max_attempts: int = 2
    status: str = TaskStatus.PENDING.value
    attempts: int = 0
    result: Optional[dict] = None
    error: Optional[str] = None


class ExecutionEngine:
    """Run independent tasks concurrently, never exceeding max_workers (1..25)."""

    def __init__(self, handlers: Dict[str, Callable], policy=None, max_workers=25,
                 checkpoint_path=None):
        if not 1 <= int(max_workers) <= 25:
            raise ValueError("max_workers must be between 1 and 25")
        self.handlers = dict(handlers)
        self.policy = policy or PolicyGate()
        self.max_workers = int(max_workers)
        self.checkpoint_path = Path(checkpoint_path) if checkpoint_path else None
        self._lock = Lock()
        self._run_lock = Lock()
        self.tasks = {}

    def add_tasks(self, tasks: Iterable[Task]):
        """Validate a complete batch before changing engine state."""
        batch = list(tasks)
        candidate = dict(self.tasks)
        for task in batch:
            if task.task_id in candidate:
                raise ValueError("duplicate task_id: " + task.task_id)
            if task.handler not in self.handlers:
                raise ValueError("unregistered handler: " + task.handler)
            if task.max_attempts < 1 or task.attempts < 0:
                raise ValueError("invalid attempt limits")
            if task.status != TaskStatus.PENDING.value:
                raise ValueError("new tasks must start pending")
            if task.attempts != 0 or task.result is not None or task.error is not None:
                raise ValueError("new tasks cannot contain execution history")
            candidate[task.task_id] = task
        self._validate_dependencies(candidate)
        self.tasks = candidate
        self.checkpoint()

    @staticmethod
    def _validate_dependencies(tasks):
        for task in tasks.values():
            missing = set(task.depends_on) - set(tasks)
            if missing:
                raise ValueError("unknown dependencies for %s: %s" % (task.task_id, sorted(missing)))
        visiting, visited = set(), set()

        def visit(task_id):
            if task_id in visiting:
                raise ValueError("dependency cycle detected")
            if task_id in visited:
                return
            visiting.add(task_id)
            for dep in tasks[task_id].depends_on:
                visit(dep)
            visiting.remove(task_id)
            visited.add(task_id)

        for task_id in tasks:
            visit(task_id)

    def load_checkpoint(self, path=None):
        """Restore validated task metadata; interrupted RUNNING tasks become PENDING.

        Worker handlers must be idempotent because a process can stop after a
        handler's effect but before its checkpoint is durably written.
        """
        source = Path(path) if path else self.checkpoint_path
        if source is None:
            raise ValueError("checkpoint path is required")
        raw = json.loads(source.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValueError("checkpoint root must be an object")
        restored = {}
        allowed_fields = set(Task.__dataclass_fields__)
        for task_id, record in raw.items():
            if not isinstance(record, dict) or set(record) - allowed_fields:
                raise ValueError("invalid checkpoint record: " + str(task_id))
            if record.get("task_id") != task_id:
                raise ValueError("checkpoint task ID mismatch")
            if record.get("handler") not in self.handlers:
                raise ValueError("unregistered checkpoint handler: " + str(record.get("handler")))
            task = Task(**record)
            if task.status == TaskStatus.RUNNING.value:
                if task.attempts >= task.max_attempts:
                    task.status = TaskStatus.FAILED.value
                    task.error = "interrupted on final allowed attempt; not retried"
                else:
                    task.status = TaskStatus.PENDING.value
                    task.error = "requeued after interrupted execution; handler must be idempotent"
            if task.attempts > task.max_attempts:
                raise ValueError("checkpoint attempts exceed configured maximum")
            evidence = task.payload.get("evidence") if isinstance(task.payload, dict) else None
            if isinstance(evidence, list):
                from modules.pets.sacred_atom_agents import Evidence
                task.payload["evidence"] = [
                    Evidence(**item) if isinstance(item, dict) and
                    {"evidence_id", "source", "claim"}.issubset(item) else item
                    for item in evidence
                ]
            restored[task_id] = task
        self._validate_dependencies(restored)
        self.tasks = restored
        self.checkpoint()
        return self.snapshot()

    def _run_one(self, task):
        if not self.policy.authorize(task.action):
            task.status = TaskStatus.BLOCKED.value
            task.error = "action requires explicit authorization: " + task.action
            return task
        with self._lock:
            task.status = TaskStatus.RUNNING.value
            task.attempts += 1
        try:
            payload = dict(task.payload)
            payload["_dependency_results"] = {
                dep: self.tasks[dep].result for dep in task.depends_on
            }
            result = self.handlers[task.handler](payload)
            if not isinstance(result, dict):
                raise TypeError("worker handlers must return a dict")
            task.result = result
            task.error = None
            task.status = TaskStatus.PASSED.value
        except Exception as exc:
            task.error = "%s: %s" % (type(exc).__name__, exc)
            task.status = (TaskStatus.PENDING.value if task.attempts < task.max_attempts
                           else TaskStatus.FAILED.value)
        return task

    def run_until_blocked(self):
        """Serialize scheduler runs and propagate blocked dependencies to a fixed point."""
        with self._run_lock:
            while True:
                changed = True
                while changed:
                    changed = False
                    for task in self.tasks.values():
                        if task.status == TaskStatus.PENDING.value and any(
                            self.tasks[d].status in (TaskStatus.FAILED.value, TaskStatus.BLOCKED.value)
                            for d in task.depends_on
                        ):
                            task.status = TaskStatus.BLOCKED.value
                            task.error = "dependency did not pass"
                            changed = True

                ready = [t for t in self.tasks.values()
                         if t.status == TaskStatus.PENDING.value
                         and all(self.tasks[d].status == TaskStatus.PASSED.value for d in t.depends_on)]
                if not ready:
                    self.checkpoint()
                    return self.snapshot()
                with ThreadPoolExecutor(max_workers=self.max_workers) as pool:
                    futures = [pool.submit(self._run_one, task) for task in ready]
                    for future in as_completed(futures):
                        future.result()
                self.checkpoint()

    def snapshot(self):
        with self._lock:
            return {task_id: asdict(task) for task_id, task in self.tasks.items()}

    def checkpoint(self):
        if not self.checkpoint_path:
            return
        self.checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        data = json.dumps(self.snapshot(), sort_keys=True, indent=2)
        fd, tmp_name = tempfile.mkstemp(prefix=".pets-checkpoint-", dir=str(self.checkpoint_path.parent))
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(tmp_name, self.checkpoint_path)
        finally:
            if os.path.exists(tmp_name):
                os.unlink(tmp_name)
