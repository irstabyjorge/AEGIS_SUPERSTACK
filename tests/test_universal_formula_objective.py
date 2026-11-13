import unittest

from modules.pets.universal_formula.objective import build_objective_tasks, run_objective
from modules.pets.universal_formula import TaskStatus


class UniversalFormulaObjectiveTests(unittest.TestCase):
    def test_objective_graph_completes_and_aggregates_specialist_outputs(self):
        engine, state = run_objective(
            "Review the architecture",
            domains=["engineering", "governance"],
            options=["option-a", "option-b"],
            max_workers=8,
        )
        self.assertEqual(len(state), 9)
        self.assertTrue(all(item["status"] == TaskStatus.PASSED.value
                            for item in state.values()))
        coordinator = state["08_coordinate"]["result"]["output"]
        self.assertEqual(coordinator["result_count"], 5)
        self.assertEqual(len(coordinator["participating_agents"]), 5)

    def test_empty_objective_rejected(self):
        with self.assertRaises(ValueError):
            build_objective_tasks("  ")

    def test_plan_is_explicit_and_bounded(self):
        tasks = build_objective_tasks("Check task dependencies")
        self.assertEqual(len(tasks), 9)
        self.assertEqual(tasks[-1].task_id, "09_report")
        self.assertEqual(tasks[-1].depends_on, ["08_coordinate"])


if __name__ == "__main__":
    unittest.main()
