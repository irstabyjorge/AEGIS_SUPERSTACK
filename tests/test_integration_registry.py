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
        self.assertEqual(modules["SACRED_ATOM"]["state"], "tested")
        self.assertEqual(modules["DIVINITY_EARTH_CIRCLE"]["state"], "integrated_knowledge")
        self.assertEqual(modules["TAUROS_100K"]["state"], "conceptual_only")

    def test_unrecovered_engines_are_not_marked_installed(self):
        modules = {item["id"]: item for item in self.registry["modules"]}
        self.assertEqual(modules["AG_UNIFIED_KNOWLEDGE_V5"]["state"], "recovered_spec_only")
        self.assertEqual(modules["AEGIS_GUARDED_EVOLUTION"]["state"], "recovered_spec_only")

    def test_global_safety_invariants_remain_fail_closed(self):
        policy = self.registry["global_invariants"]
        self.assertTrue(policy["default_deny"])
        self.assertTrue(policy["read_only_default"])
        self.assertFalse(policy["production_deploy"])
        self.assertFalse(policy["generated_code_auto_execution"])
        self.assertFalse(policy["autonomous_self_modification"])


if __name__ == "__main__":
    unittest.main()
