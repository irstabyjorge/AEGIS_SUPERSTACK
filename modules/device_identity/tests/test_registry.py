import unittest

from modules.device_identity.registry import build_report, load_registry, validate_registry


class DeviceRegistryTests(unittest.TestCase):
    def test_seed_registry_has_eight_historical_devices(self):
        data = load_registry()
        self.assertEqual(len(data["devices"]), 8)
        self.assertTrue(all(x["classification"] == "HISTORICAL" for x in data["devices"]))
        self.assertTrue(all(x["verified"] is False for x in data["devices"]))

    def test_report_preserves_historical_count(self):
        report = build_report(load_registry())
        self.assertEqual(report["classification_counts"]["HISTORICAL"], 8)
        self.assertEqual(report["device_count"], 8)

    def test_historical_cannot_be_marked_verified(self):
        data = load_registry()
        data["devices"][0]["verified"] = True
        with self.assertRaises(ValueError):
            validate_registry(data)


if __name__ == "__main__":
    unittest.main()
