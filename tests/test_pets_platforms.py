import unittest
from modules.pets.platforms import PlatformAdapterRegistry, detect_platform, supported_targets

class FakeAdapter:
    adapter_id = "fixture"
    platforms = ("linux", "macos")
    def health_check(self): return True

class PlatformTests(unittest.TestCase):
    def test_detect_returns_profile(self):
        p = detect_platform()
        self.assertTrue(p.os_name)
        self.assertTrue(p.architecture)
        self.assertTrue(p.python_version)
    def test_registry_requires_explicit_registration(self):
        r = PlatformAdapterRegistry()
        self.assertEqual(r.for_platform("linux"), ())
        a = FakeAdapter(); r.register(a)
        self.assertEqual(r.for_platform("linux"), (a,))
        self.assertEqual(r.health(), {"fixture": True})
    def test_duplicate_adapter_rejected(self):
        r = PlatformAdapterRegistry(); r.register(FakeAdapter())
        with self.assertRaises(ValueError): r.register(FakeAdapter())
    def test_target_matrix_is_explicit(self):
        t = supported_targets()
        self.assertIn("linux", t); self.assertIn("ios_ipados", t); self.assertIn("embedded_iot", t)

if __name__ == "__main__": unittest.main()
