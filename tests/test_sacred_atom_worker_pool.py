import unittest

from modules.pets.universal_formula.sacred_atom_pool import build_sacred_atom_engine
from modules.pets.universal_formula import Task, TaskStatus


class SacredAtomWorkerPoolTests(unittest.TestCase):
    def test_pool_uses_existing_specialists_and_caps_workers(self):
        engine = build_sacred_atom_engine(max_workers=25)
        self.assertEqual(engine.max_workers, 25)
        self.assertIn("ATOM_CORE", engine.handlers)
        self.assertIn("CENTER_GOVERNOR", engine.handlers)
        self.assertLessEqual(len(engine.handlers), 25)

    def test_specialist_task_runs_through_policy_gate(self):
        engine = build_sacred_atom_engine(max_workers=4)
        engine.add_tasks([
            Task("objective", "ATOM_CORE", payload={"objective": "Validate architecture"})
        ])
        state = engine.run_until_blocked()
        self.assertEqual(state["objective"]["status"], TaskStatus.PASSED.value)
        self.assertEqual(state["objective"]["result"]["agent_id"], "ATOM_CORE")


if __name__ == "__main__":
    unittest.main()
