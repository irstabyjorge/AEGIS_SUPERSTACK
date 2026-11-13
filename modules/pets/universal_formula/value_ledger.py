"""Append-only ledger for verified PETS/AEGIS outcomes and commercial potential."""
import json
import sqlite3
from pathlib import Path


class ValueLedger:
    """Record value evidence without initiating sales, licensing, or payments."""

    STATUSES = {"potential", "under_review", "commercialized", "revenue_realized", "not_commercial"}

    def __init__(self, database_path):
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS value_records (
                record_id TEXT PRIMARY KEY, outcome TEXT NOT NULL, value_type TEXT NOT NULL,
                provenance TEXT NOT NULL, attribution TEXT NOT NULL, rights_status TEXT NOT NULL,
                monetization_status TEXT NOT NULL, estimated_value REAL, actual_revenue REAL,
                currency TEXT, created_at TEXT NOT NULL, metadata TEXT NOT NULL
            )""")
            db.execute("""CREATE TRIGGER IF NOT EXISTS value_records_no_update
                BEFORE UPDATE ON value_records BEGIN
                SELECT RAISE(ABORT, "value ledger is append-only"); END""")
            db.execute("""CREATE TRIGGER IF NOT EXISTS value_records_no_delete
                BEFORE DELETE ON value_records BEGIN
                SELECT RAISE(ABORT, "value ledger is append-only"); END""")

    def _connect(self):
        db = sqlite3.connect(str(self.database_path), timeout=30)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("PRAGMA synchronous=FULL")
        return db

    def record(self, *, record_id, outcome, value_type, provenance, attribution,
               rights_status, monetization_status="potential", estimated_value=None,
               actual_revenue=None, currency=None, created_at, metadata=None):
        required = (record_id, outcome, value_type, provenance, attribution, rights_status, created_at)
        if any(not isinstance(item, str) or not item.strip() for item in required):
            raise ValueError("record identity, outcome, provenance, attribution, rights, and timestamp are required")
        if monetization_status not in self.STATUSES:
            raise ValueError("invalid monetization status")
        if estimated_value is not None and estimated_value < 0:
            raise ValueError("estimated_value cannot be negative")
        if actual_revenue is not None and actual_revenue < 0:
            raise ValueError("actual_revenue cannot be negative")
        if actual_revenue is not None and monetization_status != "revenue_realized":
            raise ValueError("actual revenue requires revenue_realized status")
        if monetization_status == "revenue_realized" and actual_revenue is None:
            raise ValueError("revenue_realized requires an actual revenue amount")
        encoded = json.dumps(metadata or {}, sort_keys=True)
        values = (record_id, outcome, value_type, provenance, attribution, rights_status,
                  monetization_status, estimated_value, actual_revenue, currency, created_at, encoded)
        with self._connect() as db:
            existing = db.execute("SELECT * FROM value_records WHERE record_id=?", (record_id,)).fetchone()
            if existing:
                if tuple(existing) != values:
                    raise ValueError("record_id already exists with different content")
                return False
            db.execute("INSERT INTO value_records VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", values)
        return True

    def summary(self):
        with self._connect() as db:
            rows = db.execute("""SELECT monetization_status, COUNT(*) AS count,
                SUM(COALESCE(estimated_value,0)) AS estimated,
                SUM(COALESCE(actual_revenue,0)) AS realized
                FROM value_records GROUP BY monetization_status""").fetchall()
        return {row["monetization_status"]: {
            "records": row["count"], "estimated_value_total": row["estimated"],
            "actual_revenue_total": row["realized"]
        } for row in rows}

    def get(self, record_id):
        with self._connect() as db:
            row = db.execute("SELECT * FROM value_records WHERE record_id=?", (record_id,)).fetchone()
        return dict(row) if row else None
