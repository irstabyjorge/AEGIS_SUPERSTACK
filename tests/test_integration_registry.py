import json
import unittest
from pathlib import Path


class IntegrationRegistryTests(unittest.TestCase):
    def setUp(self):
        self.registry = json.loads(
            Path(__file__).resolve().parents[1].joinpath("integration_registry.json").read_text()
        )

    def test_core_frameworks_are_registered(self):
        modules = {item["id"]: item for item in self.registry["modules"]}
        sacred_atom = modules["SACRED_ATOM"]
        # CI status is deliberately not promoted to "tested" until all
        # configured platform jobs have passed. The registry may lag CI by
        # one commit, so accept the explicit pending/partial states only.
        self.assertIn(sacred_atom["state"], {"implemented_ci_pending", "tested_partial"})
        self.assertEqual(modules["DIVINITY_EARTH_CIRCLE"]["state"], "integrated_knowledge")
        self.assertEqual(modules["TAUROS_100K"]["state"], "conceptual_only")

    def test_recovered_engines_are_installed_and_unverified_modules_stay_inactive(self):
        modules = {item["id"]: item for item in self.registry["modules"]}
        self.assertEqual(modules["AG_UNIFIED_KNOWLEDGE_V5"]["state"], "installed_tested")
        self.assertEqual(modules["AEGIS_GUARDED_EVOLUTION"]["state"], "installed_tested")
        self.assertEqual(modules["SPECIALIST_HANDLERS_22"]["state"], "historically_reported")
        self.assertEqual(modules["ANDROID_TERMUX_BRIDGE"]["state"], "not_verified")
        self.assertEqual(modules["NEURAL_INTERFACE_RESEARCH_CATALOG"]["state"], "research_only")
        self.assertIn("no_rf_interception", modules["NEURAL_INTERFACE_RESEARCH_CATALOG"]["limits"])
        self.assertEqual(modules["DEVICE_FORENSIC_EVIDENCE"]["state"], "local_private_evidence_only")
        self.assertEqual(modules["SPECULATIVE_ENGINEERING_ARCHIVE"]["state"], "conceptual_only")

    def test_global_safety_invariants_remain_fail_closed(self):
        policy = self.registry["global_invariants"]
        self.assertTrue(policy["default_deny"])
        self.assertTrue(policy["read_only_default"])
        self.assertFalse(policy["production_deploy"])
        self.assertFalse(policy["generated_code_auto_execution"])
        self.assertFalse(policy["autonomous_self_modification"])


if __name__ == "__main__":
    unittest.main()
