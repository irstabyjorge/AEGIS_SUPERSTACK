import tempfile
import unittest
from pathlib import Path

from knowledge.engines import aegis_unified, aegis_guarded_evolution


class UnifiedKnowledgeTests(unittest.TestCase):
    def test_fts_query_quotes_tokens_and_ignores_punctuation(self):
        self.assertEqual(
            aegis_unified.safe_fts_query("Sacred Atom + (Torus): 100K"),
            '"Sacred" AND "Atom" AND "Torus" AND "100K"',
        )
        self.assertEqual(aegis_unified.safe_fts_query("***"), "")

    def test_build_search_verify_and_skip_symlinks(self):
        with tempfile.TemporaryDirectory() as temp:
            package = Path(temp) / "package"
            knowledge = package / "knowledge"
            source = package / "library_source"
            knowledge.mkdir(parents=True)
            source.mkdir(parents=True)
            (knowledge / "CHATGPT_LIBRARY_MASTER_INDEX.csv").write_text(
                "kind,name,path,mime_type,size_bytes,modified_at,library_file_id,file_id\n"
                "file,metadata.txt,/metadata.txt,text/plain,12,2026-11-09,,\n",
                encoding="utf-8",
            )
            (source / "notes.md").write_text("Sacred Atom Torus feedback framework", encoding="utf-8")
            (source / "notes-copy.md").write_text("Sacred Atom Torus feedback framework", encoding="utf-8")
            (source / "payload.exe").write_bytes(b"MZ-not-an-executable-fixture")
            outside = Path(temp) / "outside-secret.txt"
            outside.write_text("must not be indexed", encoding="utf-8")
            try:
                (source / "outside-link.txt").symlink_to(outside)
            except OSError:
                pass

            db = knowledge / "aegis_knowledge.sqlite3"
            result = aegis_unified.build(package, db)
            self.assertTrue(result["ok"])
            results = aegis_unified.search(db, "Sacred Atom + (Torus)", 20)
            self.assertGreaterEqual(len(results), 2)
            self.assertTrue(aegis_unified.verify(db)["ok"])
            self.assertNotIn("outside-link.txt", [r["path"] for r in results])
            self.assertEqual(aegis_unified.safe_text(source / "payload.exe")[1], "isolated-executable")
            self.assertGreaterEqual(aegis_unified.duplicates(db)["duplicate_groups"], 1)

    def test_search_server_rejects_non_loopback_bind(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(ValueError):
                aegis_unified.serve(Path(temp) / "db.sqlite", "0.0.0.0", 8766)


class GuardedEvolutionTests(unittest.TestCase):
    def test_static_triage_never_executes_candidates(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "source"
            root.mkdir()
            (root / "notes.md").write_text("A harmless project note.", encoding="utf-8")
            (root / "candidate.py").write_text("print('review only')", encoding="utf-8")
            (root / "archive.zip").write_bytes(b"PK-not-an-archive-fixture")
            (root / "opaque.exe").write_bytes(b"MZ-not-an-executable-fixture")
            report = aegis_guarded_evolution.audit(root, Path(temp) / "report.json")
            self.assertFalse(report["policy"]["execution_performed"])
            decisions = {item["path"]: item["decision"] for item in report["records"]}
            self.assertEqual(decisions["notes.md"], "admit-knowledge")
            self.assertEqual(decisions["candidate.py"], "manual-review")
            self.assertEqual(decisions["archive.zip"], "quarantine")
            self.assertEqual(decisions["opaque.exe"], "quarantine")

    def test_symlinks_are_not_followed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "source"
            root.mkdir()
            outside = Path(temp) / "outside.py"
            outside.write_text("credential = 'not-read'", encoding="utf-8")
            link = root / "linked.py"
            try:
                link.symlink_to(outside)
            except OSError:
                self.skipTest("symlinks unavailable")
            report = aegis_guarded_evolution.audit(root, Path(temp) / "report.json")
            self.assertEqual(report["records"], [])


if __name__ == "__main__":
    unittest.main()
