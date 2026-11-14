"""Deterministic unit tests for QByte scoring and confidence calculations."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import qbyte_engine


class QByteScoringTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.log_path = Path(self.temp.name) / "threat_log.jsonl"
        self.engine = qbyte_engine.QuantumSecurityEngine()
        self.patches = [
            patch.object(qbyte_engine, "THREAT_LOG", self.log_path),
            patch.object(qbyte_engine, "reverse_dns_check", return_value=None),
            patch.object(qbyte_engine, "BLOCKLIST", set()),
            patch.object(qbyte_engine, "KNOWN_GOOD", set()),
            patch.object(qbyte_engine, "matches_prefix_set", return_value=False),
            patch.object(qbyte_engine, "is_bogon", return_value=False),
            patch.object(qbyte_engine.time, "time", return_value=1000.0),
        ]
        for item in self.patches:
            item.start()

    def tearDown(self):
        for item in reversed(self.patches):
            item.stop()
        self.temp.cleanup()

    def test_empty_event_baseline_score_and_confidence(self):
        result = self.engine.analyze({"ip": "8.8.8.8", "hour": 12})
        self.assertEqual(result["threat_score"], 0.05)
        self.assertEqual(result["confidence"], 0.58)
        self.assertEqual(result["threat_level"], "CLEAR")
        self.assertEqual(result["recommended_action"], "ALLOW")

    def test_signal_weights_accumulate_and_confidence_tracks_signal_count(self):
        result = self.engine.analyze(
            {
                "ip": "8.8.8.8",
                "hour": 12,
                "failed_auth": True,
                "new_device": True,
            }
        )
        self.assertEqual(result["threat_score"], 0.50)
        self.assertEqual(result["confidence"], 0.74)
        self.assertEqual(result["threat_level"], "MEDIUM")
        self.assertEqual(result["recommended_action"], "CHALLENGE_MFA")

    def test_confidence_is_capped(self):
        event = {
            "ip": "8.8.8.8",
            "hour": 12,
            "failed_auth": True,
            "failed_auth_count": 12,
            "new_device": True,
            "impossible_travel": True,
            "geo_mismatch": True,
            "suspicious_ip": True,
            "credential_stuffing": True,
            "password_spray": True,
            "api_abuse": True,
            "port_scan": True,
            "sql_injection": True,
            "path_traversal": True,
            "requests_per_minute": 900,
            "privilege_escalation": True,
            "lateral_movement": True,
            "data_exfiltration": True,
        }
        result = self.engine.analyze(event)
        self.assertEqual(result["confidence"], 0.95)
        self.assertEqual(result["threat_score"], 1.0)

    def test_threat_log_is_jsonl_and_contains_event_hash(self):
        result = self.engine.analyze({"ip": "8.8.8.8", "hour": 12})
        record = json.loads(self.log_path.read_text().splitlines()[0])
        self.assertEqual(record["event_hash"], result["event_hash"])
        self.assertEqual(record["ip"], "8.8.8.8")


if __name__ == "__main__":
    unittest.main()
