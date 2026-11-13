"""Bounded supervisor for repeated Universal Formula execution cycles.

The supervisor is deliberately finite: callers must provide cycle and time
budgets. It only invokes already-registered local handlers through ExecutionEngine.
"""
from collections import Counter
from datetime import datetime, timezone
import time

from .engine import TaskStatus


class RuntimeSupervisor:
    """Repeat objective discovery and execution within explicit resource bounds."""

    def __init__(self, engine, task_source=None, idle_wait_seconds=0.0,
                 wait_fn=None, clock=None):
        if idle_wait_seconds < 0:
            raise ValueError("idle_wait_seconds cannot be negative")
        self.engine = engine
        self.task_source = task_source
        self.idle_wait_seconds = float(idle_wait_seconds)
        self._wait = wait_fn or time.sleep
        self._clock = clock or time.monotonic
        self.state = "ready"
        self.cycle_count = 0
        self.started_at = None
        self.last_error = None
        self.stopped_reason = None
        self._last_snapshot = {}

    def _discover(self):
        if self.task_source is None:
            return []
        tasks = self.task_source(self.health_snapshot())
        if tasks is None:
            return []
        return list(tasks)

    def run_once(self):
        """Discover one batch, execute all currently runnable tasks, and report."""
        discovered = self._discover()
        if discovered:
            self.engine.add_tasks(discovered)
        self._last_snapshot = self.engine.run_until_blocked()
        self.cycle_count += 1
        return self.health_snapshot()

    def health_snapshot(self):
        statuses = Counter(item["status"] for item in self._last_snapshot.values())
        return {
            "state": self.state,
            "cycle_count": self.cycle_count,
            "task_counts": dict(statuses),
            "total_tasks": len(self._last_snapshot),
            "last_error": self.last_error,
            "stopped_reason": self.stopped_reason,
            "started_at": self.started_at,
        }

    def run(self, *, max_cycles, max_runtime_seconds, stop_requested=None):
        """Run until complete/idle-stop, requested stop, or a finite budget expires.

        max_cycles and max_runtime_seconds are mandatory to prevent an
        accidentally unbounded service loop. stop_requested is polled between
        cycles; a running handler is not forcefully interrupted.
        """
        if not isinstance(max_cycles, int) or max_cycles < 1:
            raise ValueError("max_cycles must be a positive integer")
        if max_runtime_seconds <= 0:
            raise ValueError("max_runtime_seconds must be positive")
        if self.state == "running":
            raise RuntimeError("supervisor is already running")

        start = self._clock()
        self.started_at = datetime.now(timezone.utc).isoformat()
        self.state = "running"
        self.stopped_reason = None
        self.last_error = None
        try:
            while self.cycle_count < max_cycles:
                if stop_requested and stop_requested():
                    self.stopped_reason = "stop_requested"
                    break
                if self._clock() - start >= max_runtime_seconds:
                    self.stopped_reason = "runtime_budget_exhausted"
                    break

                before = len(self.engine.tasks)
                snapshot = self.run_once()
                terminal = {TaskStatus.PASSED.value, TaskStatus.FAILED.value,
                            TaskStatus.BLOCKED.value}
                all_terminal = all(
                    task["status"] in terminal for task in snapshot["tasks"].values()
                ) if "tasks" in snapshot else all(
                    task.status in terminal for task in self.engine.tasks.values()
                )
                after = len(self.engine.tasks)
                if all_terminal and self.task_source is None:
                    self.stopped_reason = "all_known_tasks_terminal"
                    break
                if all_terminal and self.task_source is not None and after == before:
                    if self.idle_wait_seconds:
                        remaining = max_runtime_seconds - (self._clock() - start)
                        if remaining <= 0:
                            self.stopped_reason = "runtime_budget_exhausted"
                            break
                        self._wait(min(self.idle_wait_seconds, remaining))
                    else:
                        self.stopped_reason = "no_new_work_available"
                        break
            else:
                self.stopped_reason = "cycle_budget_exhausted"

            if self.stopped_reason is None:
                self.stopped_reason = "cycle_budget_exhausted"
            self.state = "stopped"
        except Exception as exc:
            self.last_error = "%s: %s" % (type(exc).__name__, exc)
            self.stopped_reason = "execution_error"
            self.state = "error"
        return self.health_snapshot()
