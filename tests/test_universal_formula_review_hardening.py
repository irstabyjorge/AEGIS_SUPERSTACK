import json
import tempfile
import threading
import time
import unittest
from pathlib import Path

from modules.pets.sacred_atom_agents import Evidence
from modules.pets.universal_formula import ExecutionEngine, Task, TaskStatus


class ReviewHardeningTests(unittest.TestCase):
    def test_new_tasks_must_start_pending_without_history(self):
        engine = ExecutionEngine({"ok": lambda payload: {"ok": True}})
        with self.assertRaises(ValueError):
            engine.add_tasks([Task("fake", "ok", status=TaskStatus.PASSED.value)])
        with self.assertRaises(ValueError):
            engine.add_tasks([Task("fake2", "ok", attempts=1)])
        self.assertEqual(engine.tasks, {})

    def test_interrupted_final_attempt_is_not_retried(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "checkpoint.json"
            path.write_text(json.dumps({
                "task": {
                    "task_id": "task", "handler": "ok", "action": "analyze",
                    "depends_on": [], "payload": {}, "max_attempts": 2,
                    "status": "running", "attempts": 2, "result": None, "error": None
                }
            }), encoding="utf-8")
            engine = ExecutionEngine({"ok": lambda payload: {"ok": True}}, checkpoint_path=path)
            restored = engine.load_checkpoint()
            self.assertEqual(restored["task"]["status"], TaskStatus.FAILED.value)
            self.assertEqual(restored["task"]["attempts"], 2)

    def test_blocked_state_propagates_through_reverse_order_dependencies(self):
        def handler(payload):
            if payload.get("fail"):
                raise RuntimeError("expected test failure")
            return {"ok": True}
        engine = ExecutionEngine({"worker": handler})
        engine.add_tasks([
            Task("A", "worker", depends_on=["B"]),
            Task("B", "worker", depends_on=["C"]),
            Task("C", "worker", payload={"fail": True}, max_attempts=1),
        ])
        state = engine.run_until_blocked()
        self.assertEqual(state["C"]["status"], TaskStatus.FAILED.value)
        self.assertEqual(state["B"]["status"], TaskStatus.BLOCKED.value)
        self.assertEqual(state["A"]["status"], TaskStatus.BLOCKED.value)

    def test_concurrent_scheduler_calls_do_not_execute_task_twice(self):
        calls = []
        guard = threading.Lock()
        def handler(payload):
            time.sleep(0.05)
            with guard:
                calls.append(payload["id"])
            return {"ok": True}
        engine = ExecutionEngine({"worker": handler}, max_workers=1)
        engine.add_tasks([Task("one", "worker", payload={"id": "one"})])
        threads = [threading.Thread(target=engine.run_until_blocked) for _ in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertEqual(calls, ["one"])

    def test_checkpoint_rehydrates_evidence_payload(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "checkpoint.json"
            engine = ExecutionEngine({"worker": lambda payload: {"seen": isinstance(
                payload["evidence"][0], Evidence)}}, checkpoint_path=path)
            engine.add_tasks([Task("one", "worker", payload={
                "evidence": [Evidence("E1", "local-source", "sample claim")]
            })])
            engine.run_until_blocked()
            resumed = ExecutionEngine({"worker": lambda payload: {"seen": isinstance(
                payload["evidence"][0], Evidence)}}, checkpoint_path=path)
            resumed.load_checkpoint()
            self.assertIsInstance(resumed.tasks["one"].payload["evidence"][0], Evidence)


if __name__ == "__main__":
    unittest.main()
