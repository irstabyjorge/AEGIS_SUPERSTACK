import unittest
from modules.pets.sacred_atom_agents import (
    Evidence, MetatronGridAgent, SacredAtomOrchestrator,
    TesseractForesightAgent, ValidatorAgent, CenterGovernorAgent,
)

class SacredAtomMultiAgentTests(unittest.TestCase):
    def setUp(self):
        self.engine = SacredAtomOrchestrator()

    def test_roster_contains_independent_specialists(self):
        ids = {a["agent_id"] for a in self.engine.status()["agents"]}
        self.assertIn("ATOM_CORE", ids)
        self.assertIn("FLOWER_MAP", ids)
        self.assertIn("TESSERACT_FORESIGHT", ids)
        self.assertGreaterEqual(len(ids), 10)

    def test_atom_core_decomposes_objective(self):
        result = self.engine.run_agent("ATOM_CORE", {"objective": "organize knowledge"})
        self.assertIn("classify_evidence", result.output["work_packages"])

    def test_tesseract_caps_horizon_at_ten(self):
        result = TesseractForesightAgent().run({"subject": "project"})
        self.assertEqual(len(result.output["scenarios"]), 10)
        self.assertTrue(all(x["status"] == "scenario_not_prediction"
                            for x in result.output["scenarios"]))

    def test_validator_requires_provenance(self):
        result = ValidatorAgent().run({"evidence": [
            Evidence("E-1", "source-A", "claim"), Evidence("", "", "claim")]})
        self.assertFalse(result.output["all_valid"])
        self.assertTrue(result.output["checks"][0]["valid"])
        self.assertFalse(result.output["checks"][1]["valid"])

    def test_dependency_cycle_rejected(self):
        with self.assertRaises(ValueError):
            MetatronGridAgent().run({"dependencies": {"a": ["b"], "b": ["a"]}})

    def test_governor_denies_privileged_capabilities(self):
        result = CenterGovernorAgent().run({
            "objective": "review", "requested_capabilities": ["read", "execute", "network"]})
        self.assertEqual(result.output["denied_capabilities"], ["execute", "network"])
        self.assertFalse(result.output["external_action_authorized"])

    def test_no_background_or_external_actions(self):
        status = self.engine.status()
        self.assertFalse(status["background_execution"])
        self.assertFalse(status["network_access"])
        self.assertFalse(status["external_actions"])

if __name__ == "__main__":
    unittest.main()
