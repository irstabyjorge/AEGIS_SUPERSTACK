import tempfile
import unittest
from pathlib import Path

from modules.pets.universal_formula.value_ledger import ValueLedger


class ValueLedgerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.ledger = ValueLedger(Path(self.temp.name) / "value.sqlite")

    def tearDown(self):
        self.temp.cleanup()

    def record(self, **kwargs):
        defaults = dict(record_id="v1", outcome="validated reusable component",
            value_type="engineering", provenance="commit:abc123", attribution="project contributor",
            rights_status="review_required", created_at="2026-11-13T00:00:00Z")
        defaults.update(kwargs)
        return self.ledger.record(**defaults)

    def test_records_potential_separately_from_realized_revenue(self):
        self.record(estimated_value=1000, monetization_status="potential", currency="USD")
        summary = self.ledger.summary()
        self.assertEqual(summary["potential"]["estimated_value_total"], 1000)
        self.assertEqual(summary["potential"]["actual_revenue_total"], 0)

    def test_realized_revenue_requires_amount_and_status(self):
        with self.assertRaises(ValueError):
            self.record(monetization_status="revenue_realized")
        with self.assertRaises(ValueError):
            self.record(actual_revenue=100, monetization_status="potential")

    def test_append_only_and_idempotent(self):
        self.assertTrue(self.record())
        self.assertFalse(self.record())
        with self.assertRaises(ValueError):
            self.record(outcome="changed outcome")
        with self.ledger._connect() as db:
            with self.assertRaises(Exception):
                db.execute("DELETE FROM value_records WHERE record_id='v1'")

    def test_rights_and_provenance_required(self):
        with self.assertRaises(ValueError):
            self.record(provenance="")
        with self.assertRaises(ValueError):
            self.record(rights_status="")


if __name__ == "__main__":
    unittest.main()
