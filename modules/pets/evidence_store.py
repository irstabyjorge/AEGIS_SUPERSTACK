"""Local SQLite append-only evidence ledger with a SHA-256 hash chain.

This stores only records explicitly supplied by the caller. It does not scan
devices, collect telemetry, upload files, or transmit evidence externally.
For production, place the database on encrypted storage and restrict OS access.
"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


GENESIS = "0" * 64


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


class EvidenceStore:
    def __init__(self, database_path: str | Path):
        self.path = Path(database_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()
        try:
            os.chmod(self.path, 0o600)
        except OSError:
            # Windows and some mounted filesystems do not implement POSIX modes.
            pass

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(str(self.path), timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA busy_timeout=10000")
        return connection

    def _initialize(self) -> None:
        with self._connect() as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.execute("""
                CREATE TABLE IF NOT EXISTS evidence (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                    record_id TEXT NOT NULL UNIQUE,
                    source TEXT NOT NULL,
                    observed_at TEXT NOT NULL,
                    collected_by TEXT NOT NULL,
                    classification TEXT NOT NULL,
                    consent_basis TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    previous_hash TEXT NOT NULL,
                    record_hash TEXT NOT NULL UNIQUE
                )
            """)
            db.execute("""
                CREATE TRIGGER IF NOT EXISTS evidence_no_update
                BEFORE UPDATE ON evidence
                BEGIN SELECT RAISE(ABORT, 'append_only'); END
            """)
            db.execute("""
                CREATE TRIGGER IF NOT EXISTS evidence_no_delete
                BEFORE DELETE ON evidence
                BEGIN SELECT RAISE(ABORT, 'append_only'); END
            """)

    def append(self, *, source: str, collected_by: str, payload: dict,
               classification: str = "private", consent_basis: str,
               observed_at: str | None = None) -> dict:
        fields = {
            "source": source,
            "collected_by": collected_by,
            "classification": classification,
            "consent_basis": consent_basis,
        }
        if any(not isinstance(v, str) or not v.strip() or len(v) > 256
               for v in fields.values()):
            raise ValueError("invalid_metadata")
        if not isinstance(payload, dict):
            raise ValueError("payload_must_be_object")
        payload_json = _canonical(payload)
        if len(payload_json.encode("utf-8")) > 1_000_000:
            raise ValueError("payload_too_large")
        timestamp = observed_at or datetime.now(timezone.utc).isoformat()
        record_id = str(uuid.uuid4())

        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            previous = db.execute(
                "SELECT record_hash FROM evidence ORDER BY sequence DESC LIMIT 1"
            ).fetchone()
            previous_hash = previous["record_hash"] if previous else GENESIS
            body = {
                "record_id": record_id, **fields,
                "observed_at": timestamp, "payload_json": payload_json,
                "previous_hash": previous_hash,
            }
            record_hash = hashlib.sha256(_canonical(body).encode("utf-8")).hexdigest()
            db.execute("""
                INSERT INTO evidence
                (record_id, source, observed_at, collected_by, classification,
                 consent_basis, payload_json, previous_hash, record_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (record_id, source, timestamp, collected_by, classification,
                  consent_basis, payload_json, previous_hash, record_hash))
        return {**body, "record_hash": record_hash}

    def list_records(self, limit: int = 100) -> list[dict]:
        if not isinstance(limit, int) or not 1 <= limit <= 1000:
            raise ValueError("limit_out_of_range")
        with self._connect() as db:
            rows = db.execute(
                "SELECT * FROM evidence ORDER BY sequence DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(row) for row in rows]

    def verify_chain(self) -> dict:
        with self._connect() as db:
            rows = db.execute("SELECT * FROM evidence ORDER BY sequence ASC").fetchall()
        previous_hash = GENESIS
        for expected_sequence, row in enumerate(rows, start=1):
            item = dict(row)
            if item["sequence"] != expected_sequence:
                return {"valid": False, "records_checked": expected_sequence - 1,
                        "reason": "sequence_gap"}
            if item["previous_hash"] != previous_hash:
                return {"valid": False, "records_checked": expected_sequence - 1,
                        "reason": "previous_hash_mismatch"}
            body = {key: item[key] for key in (
                "record_id", "source", "observed_at", "collected_by",
                "classification", "consent_basis", "payload_json", "previous_hash"
            )}
            expected_hash = hashlib.sha256(_canonical(body).encode("utf-8")).hexdigest()
            if not hashlib.compare_digest(expected_hash, item["record_hash"]):
                return {"valid": False, "records_checked": expected_sequence,
                        "reason": "record_hash_mismatch"}
            previous_hash = item["record_hash"]
        return {"valid": True, "records_checked": len(rows), "head": previous_hash}
