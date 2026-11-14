import unittest

from modules.pets.universal_formula.cosmic_system import Entity, Relationship
from modules.pets.universal_formula.unified_graph import UnifiedCosmicGraph


class UnifiedCosmicGraphTests(unittest.TestCase):
    def setUp(self):
        self.graph = UnifiedCosmicGraph()
        self.graph.add_entity(Entity(
            "earth", "Earth", "space", source="fixture",
            epistemic_class="established_model",
        ))
        self.graph.add_entity(Entity(
            "life", "Living systems", "life", source="fixture",
            epistemic_class="established_model",
        ))
        self.graph.connect(Relationship(
            "earth-life", "earth", "life", "supports",
            epistemic_class="established_model", source="fixture",
        ))

    def test_domains_share_one_canonical_registry(self):
        space_view = self.graph.domain_view("space")
        life_view = self.graph.domain_view("life")
        self.assertIs(space_view["entities"]["earth"], self.graph.entities["earth"])
        self.assertIs(life_view["entities"]["life"], self.graph.entities["life"])
        self.assertIn("earth-life", space_view["relationships"])
        self.assertIn("earth-life", life_view["relationships"])
        self.assertIs(space_view["relationships"]["earth-life"],
                      life_view["relationships"]["earth-life"])
        self.assertTrue(space_view["shared_graph"])
        self.assertTrue(life_view["shared_graph"])

    def test_competing_claims_are_preserved_not_overwritten(self):
        self.graph.add_claim(
            "claim-a", "earth", "example_property", "value-A", "science",
            "hypothesis", "source-A", ["evidence:A"],
        )
        self.graph.add_claim(
            "claim-b", "earth", "example_property", "value-B", "science",
            "user_report", "source-B", ["evidence:B"],
        )
        claims = self.graph.competing_claims("earth", "example_property")
        self.assertEqual([item["claim_id"] for item in claims], ["claim-a", "claim-b"])
        self.assertEqual({item["epistemic_class"] for item in claims},
                         {"hypothesis", "user_report"})

    def test_invalid_claim_does_not_mutate_graph(self):
        before = self.graph.snapshot()
        with self.assertRaises(ValueError):
            self.graph.add_claim(
                "bad", "missing", "property", "value", "science",
                "measured", "unknown-source",
            )
        self.assertEqual(self.graph.snapshot(), before)

    def test_duplicate_claim_id_rejected(self):
        args = ("claim-a", "earth", "property", "one", "science",
                "hypothesis", "source")
        self.graph.add_claim(*args)
        with self.assertRaises(ValueError):
            self.graph.add_claim(*args)

    def test_non_finite_claim_value_rejected(self):
        with self.assertRaises(ValueError):
            self.graph.add_claim(
                "bad-number", "earth", "measurement", float("inf"),
                "science", "measured", "instrument",
            )

    def test_snapshot_contains_claims_and_history(self):
        self.graph.add_claim(
            "claim-a", "earth", "property", "value", "science",
            "hypothesis", "source",
        )
        snapshot = self.graph.snapshot()
        self.assertEqual(snapshot["claims"][0]["claim_id"], "claim-a")
        self.assertEqual(snapshot["history"][-1]["event_type"], "claim_added")


if __name__ == "__main__":
    unittest.main()
