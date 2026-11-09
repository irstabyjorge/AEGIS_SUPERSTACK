import io
import json
import unittest

from cloud_control_plane import create_app


TOKEN = "test-token-with-at-least-thirty-two-characters"


def request(app, path="/api/v1/pets/status", method="GET", authorization=None):
    captured = {}

    def start_response(status, headers):
        captured["status"] = status
        captured["headers"] = dict(headers)

    environ = {
        "REQUEST_METHOD": method,
        "PATH_INFO": path,
        "wsgi.input": io.BytesIO(b""),
    }
    if authorization is not None:
        environ["HTTP_AUTHORIZATION"] = authorization
    body = b"".join(app(environ, start_response))
    captured["body"] = json.loads(body.decode("utf-8"))
    return captured


class CloudControlPlaneTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TOKEN)

    def test_health_is_minimal_and_public(self):
        result = request(self.app, "/healthz")
        self.assertEqual(result["status"], "200 OK")
        self.assertEqual(result["body"], {"status": "ok"})

    def test_status_requires_bearer_token(self):
        self.assertEqual(request(self.app)["status"], "401 Unauthorized")
        self.assertEqual(
            request(self.app, authorization="Bearer wrong-token")["status"],
            "401 Unauthorized",
        )

    def test_status_is_explicitly_read_only(self):
        result = request(self.app, authorization=f"Bearer {TOKEN}")
        self.assertEqual(result["status"], "200 OK")
        self.assertEqual(result["body"]["mode"], "read_only")
        self.assertFalse(result["body"]["state_changes_enabled"])
        self.assertFalse(result["body"]["production_deployment"])

    def test_evidence_policy_disables_collection_and_remote_actions(self):
        result = request(
            self.app, "/api/v1/pets/evidence-policy",
            authorization=f"Bearer {TOKEN}",
        )
        policy = result["body"]
        self.assertFalse(policy["evidence_handling"]["collects_host_data"])
        self.assertFalse(policy["evidence_handling"]["accepts_uploads"])
        self.assertFalse(policy["governance"]["automatic_blocking"])
        self.assertFalse(policy["governance"]["remote_host_scanning"])
        self.assertTrue(policy["governance"]["human_approval_required_for_state_changes"])

    def test_unknown_route_is_not_exposed(self):
        self.assertEqual(request(self.app, "/api/v1/forensics")["status"], "404 Not Found")

    def test_mutating_method_is_rejected(self):
        result = request(
            self.app, "/api/v1/pets/status", method="POST",
            authorization=f"Bearer {TOKEN}",
        )
        self.assertEqual(result["status"], "405 Method Not Allowed")

    def test_missing_or_short_token_fails_closed(self):
        app = create_app("too-short")
        self.assertEqual(request(app)["status"], "503 Service Unavailable")

    def test_security_headers_are_present(self):
        result = request(self.app, "/healthz")
        self.assertEqual(result["headers"]["Cache-Control"], "no-store")
        self.assertEqual(result["headers"]["X-Content-Type-Options"], "nosniff")

    def test_framework_registry_requires_auth_and_returns_registry(self):
        result = request(
            self.app, "/api/v1/pets/frameworks",
            authorization=f"Bearer {TOKEN}",
        )
        self.assertEqual(result["status"], "200 OK")
        ids = {module["id"] for module in result["body"]["modules"]}
        self.assertIn("SACRED_ATOM", ids)
        self.assertIn("DIVINITY_EARTH_CIRCLE", ids)

    def test_framework_registry_fails_closed_without_auth(self):
        result = request(self.app, "/api/v1/pets/frameworks")
        self.assertEqual(result["status"], "401 Unauthorized")


if __name__ == "__main__":
    unittest.main()
