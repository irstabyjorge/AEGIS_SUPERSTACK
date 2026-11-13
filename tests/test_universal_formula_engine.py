import tempfile
import unittest
from pathlib import Path

from modules.pets.universal_formula import ActionClass, ExecutionEngine, PolicyGate, Task, TaskStatus


class UniversalFormulaTests(unittest.TestCase):
    def test_dependency_order_and_checkpoint(self):
        with tempfile.TemporaryDirectory() as directory:
            engine = ExecutionEngine(
                handlers={"ok": lambda payload: {"value": payload["value"]}},
                max_workers=25,
                checkpoint_path=Path(directory) / "state.json",
            )
            engine.add_tasks([
                Task("a", "ok", payload={"value": 1}),
                Task("b", "ok", depends_on=["a"], payload={"value": 2}),
            ])
            state = engine.run_until_blocked()
            self.assertEqual(state["a"]["status"], TaskStatus.PASSED.value)
            self.assertEqual(state["b"]["status"], TaskStatus.PASSED.value)
            self.assertTrue((Path(directory) / "state.json").is_file())

    def test_protected_action_is_blocked_by_default(self):
        engine = ExecutionEngine({"ok": lambda payload: {"ok": True}})
        engine.add_tasks([Task("publish", "ok", action=ActionClass.PUBLISH.value)])
        state = engine.run_until_blocked()
        self.assertEqual(state["publish"]["status"], TaskStatus.BLOCKED.value)

    def test_worker_limit(self):
        with self.assertRaises(ValueError):
            ExecutionEngine({}, max_workers=26)

    def test_dependency_cycle_rejected(self):
        engine = ExecutionEngine({"ok": lambda payload: {}})
        with self.assertRaises(ValueError):
            engine.add_tasks([
                Task("a", "ok", depends_on=["b"]),
                Task("b", "ok", depends_on=["a"]),
            ])


if __name__ == "__main__":
    unittest.main()
