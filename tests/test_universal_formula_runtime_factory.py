import tempfile
import unittest
from pathlib import Path

from modules.pets.universal_formula import ExecutionEngine, Task
from modules.pets.universal_formula.durable_queue import DurableTaskQueue
from modules.pets.universal_formula.runtime_factory import build_durable_runtime


class DurableRuntimeFactoryTests(unittest.TestCase):
    def test_factory_discovers_executes_and_reconciles(self):
        with tempfile.TemporaryDirectory() as directory:
            queue = DurableTaskQueue(Path(directory) / "queue.sqlite")
            queue.enqueue(Task("task-1", "ok", payload={"answer": 42}))
            engine = ExecutionEngine({"ok": lambda payload: {"answer": payload["answer"]}})
            runtime = build_durable_runtime(engine, queue, idle_wait_seconds=0)
            result = runtime.run(max_cycles=3, max_runtime_seconds=5)
            self.assertEqual(result["state"], "stopped")
            self.assertEqual(queue.counts(), {"completed": 1})


if __name__ == "__main__":
    unittest.main()
