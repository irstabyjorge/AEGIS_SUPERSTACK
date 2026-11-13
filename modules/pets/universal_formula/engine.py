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
        self.tasks = {}

    def add_tasks(self, tasks: Iterable[Task]):
        for task in tasks:
            if task.task_id in self.tasks:
                raise ValueError("duplicate task_id: " + task.task_id)
            if task.handler not in self.handlers:
                raise ValueError("unregistered handler: " + task.handler)
            if task.max_attempts < 1:
                raise ValueError("max_attempts must be positive")
            self.tasks[task.task_id] = task
        self._validate_dependencies()
        self.checkpoint()

    def _validate_dependencies(self):
        for task in self.tasks.values():
            missing = set(task.depends_on) - set(self.tasks)
            if missing:
                raise ValueError("unknown dependencies for %s: %s" % (task.task_id, sorted(missing)))
        visiting, visited = set(), set()
        def visit(task_id):
            if task_id in visiting:
                raise ValueError("dependency cycle detected")
            if task_id in visited:
                return
            visiting.add(task_id)
            for dep in self.tasks[task_id].depends_on:
                visit(dep)
            visiting.remove(task_id)
            visited.add(task_id)
        for task_id in self.tasks:
            visit(task_id)

    def _run_one(self, task):
        with self._lock:
            task.status = TaskStatus.RUNNING.value
            task.attempts += 1
        try:
            if not self.policy.authorize(task.action):
                task.status = TaskStatus.BLOCKED.value
                task.error = "action requires explicit authorization: " + task.action
                return task
            result = self.handlers[task.handler](dict(task.payload))
            if not isinstance(result, dict):
                raise TypeError("worker handlers must return a dict")
            task.result = result
            task.error = None
            task.status = TaskStatus.PASSED.value
        except Exception as exc:  # surfaced in checkpoint; no silent success
            task.error = "%s: %s" % (type(exc).__name__, exc)
            task.status = (TaskStatus.PENDING.value if task.attempts < task.max_attempts
                           else TaskStatus.FAILED.value)
        return task

    def run_until_blocked(self):
        """Run ready tasks in waves until complete or no safe progress is possible."""
        while True:
            for task in self.tasks.values():
                if task.status == TaskStatus.PENDING.value and any(
                    self.tasks[d].status in (TaskStatus.FAILED.value, TaskStatus.BLOCKED.value)
                    for d in task.depends_on
                ):
                    task.status = TaskStatus.BLOCKED.value
                    task.error = "dependency did not pass"
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
