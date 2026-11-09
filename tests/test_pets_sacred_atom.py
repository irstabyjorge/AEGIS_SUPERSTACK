import unittest
from modules.pets.sacred_atom import SacredAtomGraph
from modules.pets.compute_engine import ComputeEngine
from modules.pets.auto_assembly import AssemblyPlanner, Component

class SacredAtomTests(unittest.TestCase):
    def test_geometry_has_center_and_valid_edges(self):
        graph = SacredAtomGraph()
        self.assertTrue(graph.validate())
        self.assertEqual(graph.snapshot()["center"], "conscious_center")
        self.assertEqual(len(graph.nodes), 19)
    def test_cpu_fallback_executes_identity(self):
        engine = ComputeEngine()
        result = engine.execute("identity", {"sample": 7})
        self.assertEqual(result["backend"], "cpu")
        self.assertEqual(result["result"], {"sample": 7})
    def test_unknown_backend_rejected(self):
        with self.assertRaises(ValueError): ComputeEngine().select("gpu")
    def test_assembler_is_plan_only(self):
        planner = AssemblyPlanner([
            Component("core", "1.0", trusted=True, tests_passed=True),
            Component("gui", "1.0", ("core",), ("dashboard",), trusted=True, tests_passed=True),
        ])
        plan = planner.plan(["gui"])
        self.assertEqual(plan["approved_order"], ["core", "gui"])
        self.assertFalse(plan["execution_performed"])
    def test_untrusted_component_blocked(self):
        plan = AssemblyPlanner([Component("unknown", "0", trusted=False)]).plan(["unknown"])
        self.assertIn("unknown", plan["blocked"])
    def test_dependency_cycle_blocks_entire_chain(self):
        planner = AssemblyPlanner([
            Component("a", "1", ("b",), trusted=True, tests_passed=True),
            Component("b", "1", ("a",), trusted=True, tests_passed=True),
            Component("top", "1", ("a",), trusted=True, tests_passed=True),
        ])
        plan = planner.plan(["top"])
        self.assertEqual(plan["approved_order"], [])
        self.assertIn("a", plan["blocked"])
        self.assertIn("b", plan["blocked"])
        self.assertIn("top", plan["blocked"])

if __name__ == "__main__": unittest.main()
