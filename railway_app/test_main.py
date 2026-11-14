import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from railway_app.main import app


class RailwayApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_public_health_is_minimal(self):
        response = self.client.get("/healthz")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_status_fails_closed_without_token_configuration(self):
        with patch.dict(os.environ, {}, clear=True):
            response = self.client.get("/api/v1/status")
        self.assertEqual(response.status_code, 503)

    def test_status_rejects_missing_or_invalid_token(self):
        with patch.dict(os.environ, {"AEGIS_API_TOKEN": "test-secret"}):
            self.assertEqual(self.client.get("/api/v1/status").status_code, 401)
            self.assertEqual(
                self.client.get(
                    "/api/v1/status",
                    headers={"Authorization": "Bearer wrong"},
                ).status_code,
                401,
            )

    def test_status_accepts_valid_token(self):
        with patch.dict(os.environ, {"AEGIS_API_TOKEN": "test-secret"}):
            response = self.client.get(
                "/api/v1/status",
                headers={"Authorization": "Bearer test-secret"},
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["readiness"], "api-online")
        self.assertEqual(response.json()["mode"], "read-only-foundation")

    def test_formula_endpoint_requires_authentication(self):
        with patch.dict(os.environ, {"AEGIS_API_TOKEN": "test-secret"}):
            response = self.client.post(
                "/api/v1/formula/evaluate",
                json={"objective": "Review PETS architecture"},
            )
        self.assertEqual(response.status_code, 401)

    def test_formula_runs_nine_bounded_stages(self):
        with patch.dict(os.environ, {"AEGIS_API_TOKEN": "test-secret"}):
            response = self.client.post(
                "/api/v1/formula/evaluate",
                headers={"Authorization": "Bearer test-secret"},
                json={
                    "objective": "Review PETS and AEGIS integration",
                    "domains": ["engineering", "governance"],
                    "options": ["document", "test"],
                    "evidence": [{
                        "evidence_id": "E-001",
                        "source": "user-supplied-test-fixture",
                        "claim": "Example claim for provenance validation",
                    }],
                },
            )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["formula"], "PETS Universal Formula")
        self.assertEqual(len(data["cycle"]), 9)
        self.assertEqual(data["task_counts"], {"passed": 9})
        self.assertTrue(data["evidence_validation"]["provenance_fields_present"])
        self.assertIn("remain unverified", data["evidence_validation"]["epistemic_limit"])
        self.assertFalse(data["safety"]["network_access"])
        self.assertFalse(data["safety"]["external_actions"])
        self.assertFalse(data["safety"]["source_mutation"])
        self.assertFalse(data["safety"]["persistent_storage"])

    def test_formula_rejects_empty_objective_and_extra_fields(self):
        with patch.dict(os.environ, {"AEGIS_API_TOKEN": "test-secret"}):
            headers = {"Authorization": "Bearer test-secret"}
            empty = self.client.post(
                "/api/v1/formula/evaluate", headers=headers,
                json={"objective": "  "},
            )
            extra = self.client.post(
                "/api/v1/formula/evaluate", headers=headers,
                json={"objective": "Review architecture", "execute_shell": True},
            )
        self.assertEqual(empty.status_code, 422)
        self.assertEqual(extra.status_code, 422)


if __name__ == "__main__":
    unittest.main()
