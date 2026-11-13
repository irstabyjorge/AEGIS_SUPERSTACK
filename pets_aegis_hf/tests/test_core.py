import json
import tempfile
import unittest
from pathlib import Path

from pets_aegis_hf.core import make_manifest, verify_manifest, append_ledger, verify_ledger


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


if __name__ == "__main__":
    unittest.main()
