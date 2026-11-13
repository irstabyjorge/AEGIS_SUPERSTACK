import json
import tempfile
import unittest
from pathlib import Path

from modules.pets.universal_formula import ActionClass, ExecutionEngine, Task, TaskStatus


class UniversalFormulaTests(unittest.TestCase):
    def test_dependency_order_and_checkpoint(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            engine = ExecutionEngine(
                handlers={"ok": lambda payload: {"value": payload["value"]}},
                max_workers=25,
                checkpoint_path=path,
            )
            engine.add_tasks([
                Task("a", "ok", payload={"value": 1}),
                Task("b", "ok", depends_on=["a"], payload={"value": 2}),
            ])
            state = engine.run_until_blocked()
            self.assertEqual(state["a"]["status"], TaskStatus.PASSED.value)
            self.assertEqual(state["b"]["status"], TaskStatus.PASSED.value)
            self.assertTrue(path.is_file())

    def test_protected_action_is_blocked_without_consuming_attempt(self):
        engine = ExecutionEngine({"ok": lambda payload: {"ok": True}})
        engine.add_tasks([Task("publish", "ok", action=ActionClass.PUBLISH.value)])
        state = engine.run_until_blocked()
        self.assertEqual(state["publish"]["status"], TaskStatus.BLOCKED.value)
        self.assertEqual(state["publish"]["attempts"], 0)

    def test_worker_limit(self):
        with self.assertRaises(ValueError):
            ExecutionEngine({}, max_workers=26)

    def test_dependency_cycle_rejected_without_partial_registration(self):
        engine = ExecutionEngine({"ok": lambda payload: {}})
        with self.assertRaises(ValueError):
            engine.add_tasks([
                Task("a", "ok", depends_on=["b"]),
                Task("b", "ok", depends_on=["a"]),
            ])
        self.assertEqual(engine.tasks, {})

    def test_checkpoint_restore_requeues_interrupted_task(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            path.write_text(json.dumps({
                "a": {
                    "task_id": "a", "handler": "ok", "action": "analyze",
                    "depends_on": [], "payload": {}, "max_attempts": 3,
                    "status": "running", "attempts": 1, "result": None, "error": None
                }
            }), encoding="utf-8")
            engine = ExecutionEngine({"ok": lambda payload: {"resumed": True}},
                                     checkpoint_path=path)
            state = engine.load_checkpoint()
            self.assertEqual(state["a"]["status"], TaskStatus.PENDING.value)
            self.assertEqual(state["a"]["attempts"], 1)
            final = engine.run_until_blocked()
            self.assertEqual(final["a"]["status"], TaskStatus.PASSED.value)

    def test_invalid_checkpoint_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            path.write_text('{"a": {"task_id": "wrong"}}', encoding="utf-8")
            engine = ExecutionEngine({"ok": lambda payload: {}})
            with self.assertRaises((ValueError, TypeError)):
                engine.load_checkpoint(path)
            self.assertEqual(engine.tasks, {})


if __name__ == "__main__":
    unittest.main()
