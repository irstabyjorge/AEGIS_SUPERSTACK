import unittest

from modules.pets.universal_formula.cosmic_system import (
    CosmicSystem, Entity, Relationship, Transition
)


class CosmicSystemTests(unittest.TestCase):
    def setUp(self):
        self.system = CosmicSystem()
        self.system.add_entity(Entity(
            "earth", "Earth", "other",
            properties={"radius_km": 6371.0},
            units={"radius_km": "km"},
            epistemic_class="established_model",
            source="test fixture",
        ))
        self.system.add_entity(Entity(
            "life", "Living systems", "life",
            epistemic_class="established_model",
            source="test fixture",
        ))

    def test_connectivity_and_versioned_history(self):
        self.system.connect(Relationship(
            "earth-life", "earth", "life", "supports_ecological_systems",
            epistemic_class="established_model", source="test fixture"
        ))
        self.assertEqual(self.system.neighbors("earth"), ["life"])
        self.assertEqual(self.system.version, 3)
        self.assertEqual(len(self.system.history), 3)

    def test_transition_is_validated_before_mutation(self):
        bad = Transition(
            "bad",
            additions=[Entity("moon", "Moon", "other", source="test")],
            relationships=[Relationship("bad-edge", "moon", "missing", "unknown")]
        )
        with self.assertRaises(ValueError):
            self.system.apply_transition(bad)
        self.assertNotIn("moon", self.system.entities)

    def test_transition_adds_new_configuration(self):
        transition = Transition(
            "new-moon",
            additions=[Entity("moon", "Moon", "other", source="astronomy record")],
            relationships=[Relationship(
                "earth-moon", "earth", "moon", "gravitational_interaction",
                epistemic_class="established_model", source="astronomy model"
            )],
            rationale="Add a related astronomical entity",
            evidence_refs=["fixture:earth-moon"],
            epistemic_class="established_model",
        )
        self.system.apply_transition(transition)
        self.assertIn("moon", self.system.entities)
        self.assertEqual(self.system.neighbors("earth"), ["life", "moon"])

    def test_non_finite_values_rejected(self):
        with self.assertRaises(ValueError):
            Entity("bad", "Bad", "matter", properties={"mass": float("nan")}).validate()

    def test_duplicate_ids_rejected(self):
        with self.assertRaises(ValueError):
            self.system.add_entity(Entity("earth", "Second Earth", "other", source="test"))

    def test_purpose_possibility_and_constraint_records(self):
        self.system.add_purpose("understand", "Investigate system relationships")
        self.system.add_constraint("evidence", "Claims require provenance")
        self.system.add_possibility("cyclic", "A cyclic cosmological model", status="hypothesis")
        snapshot = self.system.snapshot()
        self.assertEqual(snapshot["purposes"][0]["purpose_id"], "understand")
        self.assertEqual(snapshot["possibilities"][0]["status"], "hypothesis")


if __name__ == "__main__":
    unittest.main()
