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


if __name__ == "__main__":
    unittest.main()
