import json
import tempfile
import unittest
from pathlib import Path

from pets_aegis_hf.core import (
    append_ledger, make_manifest, verify_ledger, verify_manifest
)


class IntegrityTests(unittest.TestCase):
    def test_manifest_detects_mutation(self):
        manifest = make_manifest({
            "repo_id": "AEGISGODMODE/example",
            "repo_type": "model",
            "revision": "abc123",
            "files": []
        })
        self.assertTrue(verify_manifest(manifest))
        manifest["repository"]["revision"] = "tampered"
        self.assertFalse(verify_manifest(manifest))

    def test_manifest_rejects_non_object(self):
        self.assertFalse(verify_manifest([]))
        self.assertFalse(verify_manifest(None))

    def test_hash_chain_detects_mutation(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "audit.jsonl"
            append_ledger(path, {"action": "inventory"})
            append_ledger(path, {"action": "audit"})
            self.assertTrue(verify_ledger(path)["valid"])
            records = path.read_text(encoding="utf-8").splitlines()
            first = json.loads(records[0])
            first["event"]["action"] = "tampered"
            records[0] = json.dumps(first)
            path.write_text("\n".join(records) + "\n", encoding="utf-8")
            self.assertFalse(verify_ledger(path)["valid"])

    def test_corrupt_ledger_refuses_append(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "audit.jsonl"
            path.write_text("{broken}\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                append_ledger(path, {"action": "must-not-append"})

    def test_sequence_number_is_verified(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "audit.jsonl"
            append_ledger(path, {"action": "inventory"})
            record = json.loads(path.read_text(encoding="utf-8"))
            record["sequence"] = 9
            body = dict(record)
            body.pop("event_hash")
            from pets_aegis_hf.core import digest
            record["event_hash"] = digest(body)
            path.write_text(json.dumps(record) + "\n", encoding="utf-8")
            result = verify_ledger(path)
            self.assertFalse(result["valid"])
            self.assertEqual(result["error"], "sequence_mismatch")


if __name__ == "__main__":
    unittest.main()
