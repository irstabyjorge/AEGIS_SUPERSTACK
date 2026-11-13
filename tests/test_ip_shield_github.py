import hashlib
import importlib.util
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).parents[1] / "tools" / "ip_shield_github.py"
SPEC = importlib.util.spec_from_file_location("ip_shield_github", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

class SnapshotTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old = os.getcwd()
        os.chdir(self.tmp.name)
        subprocess.run(["git","init","-q"],check=True)
        subprocess.run(["git","config","user.name","Test Author"],check=True)
        subprocess.run(["git","config","user.email","author@example.invalid"],check=True)
        Path("sample.txt").write_text("sample data\n",encoding="utf-8")
        subprocess.run(["git","add","."],check=True)
        subprocess.run(["git","commit","-qm","test commit"],check=True)

    def tearDown(self):
        os.chdir(self.old)
        self.tmp.cleanup()

    def test_hash_inventory_does_not_include_file_contents(self):
        files,total,truncated=MODULE.inventory(MODULE.git("rev-parse","HEAD").decode().strip())
        self.assertEqual(total,1)
        self.assertFalse(truncated)
        self.assertEqual(files[0]["sha256"],hashlib.sha256(b"sample data\n").hexdigest())
        self.assertNotIn("sample data",str(files))

    def test_commit_history_records_declared_author(self):
        commits,total,truncated=MODULE.history(MODULE.git("rev-parse","HEAD").decode().strip())
        self.assertEqual(total,1)
        self.assertEqual(commits[0]["author_name_declared"],"Test Author")
        self.assertNotIn("author@example.invalid",str(commits))

if __name__=="__main__":
    unittest.main()
