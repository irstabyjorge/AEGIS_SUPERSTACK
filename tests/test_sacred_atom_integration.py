import unittest

from modules.pets.sacred_atom_integration import SacredAtomSystem


class SacredAtomIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.system = SacredAtomSystem()

    def test_geometry_has_one_center_six_inner_and_twelve_outer_nodes(self):
        snapshot = self.system.geometry.snapshot()
        self.assertTrue(snapshot["valid"])
        self.assertEqual(len(snapshot["nodes"]), 19)
        self.assertEqual(snapshot["center"], "conscious_center")

    def test_geometry_maps_to_agent_knowledge_graph(self):
        graph = self.system.geometry_knowledge_graph()
        self.assertEqual(len(graph.nodes), 19)
        self.assertGreater(len(graph.edges), 0)
        self.assertIn("conscious_center", graph.nodes)
        self.assertIn("android", graph.nodes)

    def test_agent_dispatch_remains_bounded(self):
        result = self.system.run_agent(
            "ATOM_CORE", {"objective": "validate integration boundary"})
        self.assertEqual(result.agent_id, "ATOM_CORE")
        self.assertIn("classify_evidence", result.output["work_packages"])

    def test_status_exposes_non_execution_invariants(self):
        status = self.system.status()
        self.assertFalse(status["external_actions"])
        self.assertFalse(status["source_mutation"])
        self.assertFalse(status["orchestration"]["background_execution"])
        self.assertFalse(status["orchestration"]["network_access"])


if __name__ == "__main__":
    unittest.main()
