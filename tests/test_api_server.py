"""HTTP integration tests for the legacy API using isolated dependency fixtures."""

import importlib.util
import json
import sys
import threading
import types
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from unittest.mock import patch


def _module(name, **attrs):
    item = types.ModuleType(name)
    for key, value in attrs.items():
        setattr(item, key, value)
    return item


def _load_api_module():
    class Threat:
        ip = "203.0.113.8"
        score = 0.2
        level = "CLEAR"
        action = "ALLOW"
        signals = []
        confidence = 0.6

    class QByte:
        def analyze_ip(self, ip):
            return Threat()

        def scan_live_connections(self):
            return []

        def scan_listeners(self):
            return []

    class System:
        def status(self):
            return {"status": "fixture"}

    class Entropy:
        def generate(self):
            return {"mode": "fixture"}

    class Predictor:
        def train_on_history(self):
            return {"mode": "fixture"}

    aegis = _module(
        "aegis_omni",
        QByteEngine=QByte,
        SystemAnalyzer=System,
        EntropyModule=Entropy,
        PredictiveEngine=Predictor,
        BLOCKLIST=set(),
        __version__="test",
    )
    fixtures = {
        "modules.uptime_monitor": {"run_checks": lambda: {"fixture": True}},
        "modules.log_analyzer": {
            "analyze_system_logs": lambda: {},
            "analyze_aegis_threats": lambda: {},
        },
        "modules.vuln_scanner": {"full_scan": lambda: {}},
        "modules.ioc_scanner": {"full_scan": lambda: {}},
        "modules.forensics": {"full_forensic_capture": lambda: {}},
        "modules.password_audit": {"full_audit": lambda: {}},
        "modules.payload_detector": {"scan_web_logs": lambda: {}},
        "modules.honeypot": {"analyze_honeypot_logs": lambda: {}},
    }
    modules = {"aegis_omni": aegis}
    modules.update({name: _module(name, **attrs) for name, attrs in fixtures.items()})
    with patch.dict(sys.modules, modules):
        spec = importlib.util.spec_from_file_location(
            "aegis_api_server_test_target",
            Path(__file__).resolve().parents[1] / "modules" / "api_server.py",
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    return module


class ApiServerIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.api = _load_api_module()
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), cls.api.AegisAPIHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.server.server_address[1]}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def request(self, path, token=None, request_id=None):
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        if request_id:
            headers["X-Request-ID"] = request_id
        req = Request(self.base + path, headers=headers)
        try:
            with urlopen(req, timeout=3) as response:
                return response.status, response.headers, json.loads(response.read())
        except HTTPError as error:
            return error.code, error.headers, json.loads(error.read())

    def test_health_is_public_and_minimal(self):
        code, headers, body = self.request("/healthz")
        self.assertEqual(code, 200)
        self.assertEqual(body["status"], "ok")
        self.assertTrue(headers.get("X-Request-ID"))

    def test_api_fails_closed_when_tokens_are_not_configured(self):
        with patch.dict("os.environ", {}, clear=True):
            code, _, body = self.request("/api/status")
        self.assertEqual(code, 503)
        self.assertEqual(body["error"], "authentication_not_configured")

    def test_viewer_role_can_read_status_but_cannot_scan(self):
        token = "v" * 32
        with patch.dict(
            "os.environ", {"AEGIS_API_TOKENS": json.dumps({token: "viewer"})}
        ):
            status_code, _, _ = self.request("/api/status", token)
            scan_code, _, _ = self.request("/api/scan/203.0.113.8", token)
        self.assertEqual(status_code, 200)
        self.assertEqual(scan_code, 403)

    def test_operator_scan_is_read_only_and_has_scan_id(self):
        token = "o" * 32
        with patch.dict(
            "os.environ", {"AEGIS_API_TOKENS": json.dumps({token: "operator"})}
        ):
            code, headers, body = self.request(
                "/api/scan/203.0.113.8", token, "scan-fixture-001"
            )
        self.assertEqual(code, 200)
        self.assertEqual(body["ip"], "203.0.113.8")
        self.assertEqual(headers.get("X-Request-ID"), "scan-fixture-001")
        self.assertEqual(headers.get("X-Scan-ID"), "scan-fixture-001")

    def test_invalid_request_id_is_replaced(self):
        code, headers, _ = self.request("/healthz", request_id="bad id with spaces")
        self.assertEqual(code, 200)
        self.assertNotEqual(headers.get("X-Request-ID"), "bad id with spaces")


if __name__ == "__main__":
    unittest.main()
