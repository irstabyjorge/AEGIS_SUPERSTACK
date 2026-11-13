import tempfile
import unittest
from pathlib import Path

from modules.pets.universal_formula import ExecutionEngine, Task
from modules.pets.universal_formula.durable_queue import DurableTaskQueue


class DurableQueueTests(unittest.TestCase):
    def test_enqueue_discover_execute_and_reconcile(self):
        with tempfile.TemporaryDirectory() as directory:
            queue = DurableTaskQueue(Path(directory) / "queue.sqlite")
            queue.enqueue(Task("q1", "ok", payload={"value": 7}))
            engine = ExecutionEngine({"ok": lambda payload: {"value": payload["value"]}})
            batch = queue.discover(engine)
            self.assertEqual([task.task_id for task in batch], ["q1"])
            engine.add_tasks(batch)
            snapshot = engine.run_until_blocked()
            queue.reconcile(snapshot)
            self.assertEqual(queue.counts(), {"completed": 1})

    def test_leased_item_reappears_after_expiry(self):
        with tempfile.TemporaryDirectory() as directory:
            clock = {"now": 100.0}
            queue = DurableTaskQueue(Path(directory) / "queue.sqlite",
                                     lease_seconds=5, clock=lambda: clock["now"])
            queue.enqueue(Task("q1", "ok"))
            engine1 = ExecutionEngine({"ok": lambda payload: {}})
            self.assertEqual(len(queue.discover(engine1)), 1)
            engine2 = ExecutionEngine({"ok": lambda payload: {}})
            self.assertEqual(queue.discover(engine2), [])
            clock["now"] = 106.0
            self.assertEqual(len(queue.discover(engine2)), 1)

    def test_checkpointed_engine_item_is_not_double_enqueued(self):
        with tempfile.TemporaryDirectory() as directory:
            queue = DurableTaskQueue(Path(directory) / "queue.sqlite")
            queue.enqueue(Task("q1", "ok"))
            engine = ExecutionEngine({"ok": lambda payload: {}})
            engine.add_tasks([Task("q1", "ok")])
            self.assertEqual(queue.discover(engine), [])


    def test_dependency_batch_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            queue = DurableTaskQueue(Path(directory) / "queue.sqlite")
            queue.enqueue(Task("02_child", "ok", depends_on=["01_parent"]))
            queue.enqueue(Task("01_parent", "ok"))
            engine = ExecutionEngine({"ok": lambda payload: {"ok": True}})
            first = queue.discover(engine)
            self.assertEqual([task.task_id for task in first], ["01_parent"])
            engine.add_tasks(first)
            second = queue.discover(engine)
            self.assertEqual([task.task_id for task in second], ["02_child"])

    def test_non_json_payload_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            queue = DurableTaskQueue(Path(directory) / "queue.sqlite")
            with self.assertRaises(ValueError):
                queue.enqueue(Task("bad", "ok", payload={"not_json": object()}))


if __name__ == "__main__":
    unittest.main()
