import tempfile
import unittest
from pathlib import Path

from modules.pets.adapters import AdapterRegistry, FixtureAdapter
from modules.pets.evidence_store import EvidenceStore
from modules.pets.permissions import Permission, Role, authorize


class EvidenceStoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.store = EvidenceStore(Path(self.tmp.name) / "evidence.sqlite3")

    def test_append_and_verify_chain(self):
        self.store.append(source="test-fixture", collected_by="test",
                          payload={"sample": 1}, consent_basis="synthetic_test")
        self.store.append(source="test-fixture", collected_by="test",
                          payload={"sample": 2}, consent_basis="synthetic_test")
        self.assertEqual(self.store.verify_chain()["records_checked"], 2)
        self.assertTrue(self.store.verify_chain()["valid"])

    def test_update_and_delete_are_rejected(self):
        record = self.store.append(source="fixture", collected_by="test",
                                   payload={}, consent_basis="synthetic_test")
        with self.store._connect() as db:
            with self.assertRaises(Exception):
                db.execute("UPDATE evidence SET source='changed' WHERE record_id=?",
                           (record["record_id"],))
            with self.assertRaises(Exception):
                db.execute("DELETE FROM evidence WHERE record_id=?",
                           (record["record_id"],))

    def test_invalid_payload_rejected(self):
        with self.assertRaises(ValueError):
            self.store.append(source="fixture", collected_by="test",
                              payload="not-object", consent_basis="synthetic_test")


class PermissionTests(unittest.TestCase):
    def test_roles_are_deny_by_default(self):
        self.assertTrue(authorize(Role.ANALYST, Permission.CREATE_EVIDENCE))
        self.assertFalse(authorize(Role.AUDITOR, Permission.CREATE_EVIDENCE))
        self.assertFalse(authorize(Role.READER, Permission.READ_EVIDENCE))
        self.assertFalse(authorize("unknown", Permission.DEPLOY))


class AdapterTests(unittest.TestCase):
    def test_fixture_read_and_write_denial(self):
        registry = AdapterRegistry()
        registry.register(FixtureAdapter("fixture", {"search": {"count": 1}}))
        self.assertEqual(registry.read("fixture", "search")["data"]["count"], 1)
        with self.assertRaises(PermissionError):
            registry.read("fixture", "delete_record")


if __name__ == "__main__":
    unittest.main()
