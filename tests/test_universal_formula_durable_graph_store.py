import os
import sqlite3
import tempfile
import unittest

from modules.pets.universal_formula.cosmic_system import Entity
from modules.pets.universal_formula.unified_graph import UnifiedCosmicGraph
from modules.pets.universal_formula.durable_graph_store import DurableGraphStore


class DurableGraphStoreTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tempdir.name, "graph.sqlite")
        self.store = DurableGraphStore(self.path)
        self.graph = UnifiedCosmicGraph(system_id="shared-universe")
        self.graph.add_entity(Entity(
            "earth", "Earth", "space",
            epistemic_class="established_model", source="fixture",
        ))

    def tearDown(self):
        self.tempdir.cleanup()

    def test_round_trip_latest_snapshot(self):
        self.store.save(self.graph)
        self.graph.add_entity(Entity(
            "life", "Life", "life",
            epistemic_class="established_model", source="fixture",
        ))
        self.store.save(self.graph)
        restored = self.store.load_latest("shared-universe")
        self.assertEqual(restored["version"], self.graph.version)
        self.assertIn("earth", restored["entities"])
        self.assertIn("life", restored["entities"])
        self.assertEqual(self.store.count("shared-universe"), 2)

    def test_identical_version_save_is_idempotent(self):
        first = self.store.save(self.graph)
        second = self.store.save(self.graph.snapshot())
        self.assertEqual(first, second)
        self.assertEqual(self.store.count(), 1)

    def test_conflicting_version_is_rejected(self):
        self.store.save(self.graph)
        altered = self.graph.snapshot()
        altered["created_at"] = "different"
        with self.assertRaises(ValueError):
            self.store.save(altered)

    def test_missing_snapshot_returns_none(self):
        self.assertIsNone(self.store.load_latest("absent"))

    def test_invalid_snapshot_rejected(self):
        with self.assertRaises(ValueError):
            self.store.save({"system_id": "x", "version": float("nan")})

    def test_sqlite_rows_are_append_only(self):
        self.store.save(self.graph)
        with sqlite3.connect(self.path) as connection:
            with self.assertRaises(sqlite3.IntegrityError):
                connection.execute("UPDATE graph_snapshots SET payload='{}'")
            with self.assertRaises(sqlite3.IntegrityError):
                connection.execute("DELETE FROM graph_snapshots")


if __name__ == "__main__":
    unittest.main()
