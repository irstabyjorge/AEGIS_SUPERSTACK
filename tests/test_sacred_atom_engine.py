import unittest
from modules.pets.sacred_atom_engine import SacredAtomEngine, ComponentSpec

class BrokenGPU:
    name = "optional-gpu"
    def map_values(self, values, operation): raise RuntimeError("backend unavailable")

class SacredAtomTests(unittest.TestCase):
    def test_default_geometry_has_center_and_layers(self):
        engine = SacredAtomEngine()
        status = engine.status()
        self.assertEqual(status["center"], "human-defined purpose and policy")
        self.assertIn("validation", status["layers"])
    def test_assembly_is_allowlisted_and_dependency_ordered(self):
        engine = SacredAtomEngine()
        engine.register_component(ComponentSpec("base", "1", trusted=True))
        engine.register_component(ComponentSpec("report", "1", dependencies=("base",), trusted=True, capabilities=("read", "report")))
        self.assertEqual(engine.assemble_plan(("report",)), ("base", "report"))
    def test_untrusted_component_rejected(self):
        engine = SacredAtomEngine()
        with self.assertRaises(PermissionError): engine.register_component(ComponentSpec("x", "1"))
    def test_gpu_fallback_to_cpu(self):
        engine = SacredAtomEngine(gpu_backend=BrokenGPU())
        backend, result = engine.compute([2.0, 3.0], "square")
        self.assertEqual(backend, "cpu")
        self.assertEqual(result, [4.0, 9.0])
    def test_invalid_operation_rejected(self):
        engine = SacredAtomEngine()
        with self.assertRaises(ValueError): engine.compute([1.0], "unknown")

if __name__ == "__main__": unittest.main()
