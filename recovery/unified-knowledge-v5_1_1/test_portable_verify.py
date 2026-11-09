import hashlib
import importlib.util
import sqlite3
import tempfile
import unittest
from pathlib import Path

ENGINE = Path(__file__).resolve().parent / "aegis_unified.py"
spec = importlib.util.spec_from_file_location("aegis_unified", ENGINE)
aegis = importlib.util.module_from_spec(spec)
spec.loader.exec_module(aegis)

class PortableVerifyTests(unittest.TestCase):
    def test_relocates_by_hash_inside_package_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "knowledge").mkdir()
            (root / "library_source").mkdir()
            payload = b"verified local content"
            (root / "library_source" / "renamed.txt").write_bytes(payload)
            db = root / "knowledge" / "aegis_knowledge.sqlite3"
            con = sqlite3.connect(db)
            con.execute("CREATE TABLE files (path TEXT PRIMARY KEY, local_path TEXT, sha256 TEXT, materialized INTEGER)")
            con.execute("INSERT INTO files VALUES(?,?,?,1)", (
                "/old-name.txt", "/obsolete/build/path/old-name.txt",
                hashlib.sha256(payload).hexdigest()))
            con.commit()
            con.close()
            result = aegis.verify(db, root)
            self.assertTrue(result["ok"])
            self.assertEqual(len(result["relocated"]), 1)
            self.assertEqual(result["relocated"][0]["resolved_path"], "library_source/renamed.txt")

    def test_missing_hash_remains_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "knowledge").mkdir()
            (root / "library_source").mkdir()
            db = root / "knowledge" / "aegis_knowledge.sqlite3"
            con = sqlite3.connect(db)
            con.execute("CREATE TABLE files (path TEXT PRIMARY KEY, local_path TEXT, sha256 TEXT, materialized INTEGER)")
            con.execute("INSERT INTO files VALUES(?,?,?,1)", ("/missing.txt", "/not/here", "0" * 64))
            con.commit()
            con.close()
            result = aegis.verify(db, root)
            self.assertFalse(result["ok"])
            self.assertEqual(result["missing"], ["/missing.txt"])

if __name__ == "__main__":
    unittest.main()
