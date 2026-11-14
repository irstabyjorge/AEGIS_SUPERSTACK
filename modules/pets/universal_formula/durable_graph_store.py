"""Append-only SQLite snapshots for the UF-COSMIC unified graph."""
import hashlib
import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Optional

from .cosmic_system import _finite_tree


class DurableGraphStore:
    """Persist immutable, hash-verified graph snapshots in a local SQLite file."""

    def __init__(self, database_path):
        self.database_path = str(database_path)
        if self.database_path != ":memory:":
            Path(self.database_path).expanduser().parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    @contextmanager
    def _connection(self):
        connection = sqlite3.connect(self.database_path, timeout=30)
        try:
            connection.execute("PRAGMA foreign_keys=ON")
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _initialize(self):
        with self._connection() as connection:
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute("PRAGMA synchronous=FULL")
            connection.execute("""
                CREATE TABLE IF NOT EXISTS graph_snapshots (
                    snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    system_id TEXT NOT NULL,
                    version INTEGER NOT NULL CHECK(version >= 0),
                    snapshot_hash TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    UNIQUE(system_id, version)
                )
            """)
            connection.execute("""
                CREATE TRIGGER IF NOT EXISTS graph_snapshots_no_update
                BEFORE UPDATE ON graph_snapshots
                BEGIN SELECT RAISE(ABORT, 'graph snapshots are append-only'); END
            """)
            connection.execute("""
                CREATE TRIGGER IF NOT EXISTS graph_snapshots_no_delete
                BEFORE DELETE ON graph_snapshots
                BEGIN SELECT RAISE(ABORT, 'graph snapshots are append-only'); END
            """)

    @staticmethod
    def _canonical_payload(snapshot: Dict[str, Any]) -> str:
        if not isinstance(snapshot, dict):
            raise ValueError("snapshot must be an object")
        _finite_tree(snapshot, "snapshot")
        required = {"system_id", "version", "created_at", "entities",
                    "relationships", "history", "claims"}
        missing = required.difference(snapshot)
        if missing:
            raise ValueError("snapshot missing fields: " + ", ".join(sorted(missing)))
        if not isinstance(snapshot["system_id"], str) or not snapshot["system_id"].strip():
            raise ValueError("snapshot system_id is required")
        if isinstance(snapshot["version"], bool) or not isinstance(snapshot["version"], int) or snapshot["version"] < 0:
            raise ValueError("snapshot version must be a non-negative integer")
        for field in ("entities", "relationships"):
            if not isinstance(snapshot[field], dict):
                raise ValueError(field + " must be an object")
        for field in ("history", "claims"):
            if not isinstance(snapshot[field], list):
                raise ValueError(field + " must be an array")
        return json.dumps(snapshot, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    def save(self, graph_or_snapshot) -> str:
        snapshot = graph_or_snapshot.snapshot() if hasattr(graph_or_snapshot, "snapshot") else graph_or_snapshot
        payload = self._canonical_payload(snapshot)
        digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        system_id, version = snapshot["system_id"], snapshot["version"]
        with self._connection() as connection:
            existing = connection.execute(
                "SELECT snapshot_hash FROM graph_snapshots WHERE system_id=? AND version=?",
                (system_id, version),
            ).fetchone()
            if existing:
                if existing[0] == digest:
                    return digest
                raise ValueError("a different snapshot already exists for this system/version")
            connection.execute(
                "INSERT INTO graph_snapshots(system_id,version,snapshot_hash,payload,created_at) VALUES(?,?,?,?,?)",
                (system_id, version, digest, payload, str(snapshot["created_at"])),
            )
        return digest

    def load_latest(self, system_id: str) -> Optional[Dict[str, Any]]:
        if not isinstance(system_id, str) or not system_id.strip():
            raise ValueError("system_id is required")
        with self._connection() as connection:
            row = connection.execute(
                "SELECT snapshot_hash,payload FROM graph_snapshots WHERE system_id=? ORDER BY version DESC LIMIT 1",
                (system_id,),
            ).fetchone()
        if row is None:
            return None
        expected_hash, payload = row
        actual_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        if actual_hash != expected_hash:
            raise ValueError("snapshot integrity check failed")
        snapshot = json.loads(payload)
        self._canonical_payload(snapshot)
        return snapshot

    def count(self, system_id: Optional[str] = None) -> int:
        with self._connection() as connection:
            if system_id is None:
                row = connection.execute("SELECT COUNT(*) FROM graph_snapshots").fetchone()
            else:
                row = connection.execute(
                    "SELECT COUNT(*) FROM graph_snapshots WHERE system_id=?", (system_id,)
                ).fetchone()
        return int(row[0])
