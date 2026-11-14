#!/usr/bin/env python3
# Copyright (c) 2024-2026 Jorge Francisco Paredes (irstabyjorge)
# Licensed under dual MIT/Commercial license. See LICENSE and COMMERCIAL_LICENSE.md
"""Local-first AEGIS REST API with fail-closed token authentication and JSON audit logs."""

import json
import logging
import os
import re
import sys
import uuid
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime, UTC
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from aegis_omni import QByteEngine, SystemAnalyzer, EntropyModule, PredictiveEngine, BLOCKLIST, __version__
from modules.uptime_monitor import run_checks as uptime_checks
from modules.log_analyzer import analyze_system_logs, analyze_aegis_threats
from modules.vuln_scanner import full_scan as vuln_scan
from modules.ioc_scanner import full_scan as ioc_scan
from modules.forensics import full_forensic_capture
from modules.password_audit import full_audit as password_audit
from modules.payload_detector import scan_web_logs as payload_scan
from modules.honeypot import analyze_honeypot_logs


qbyte = QByteEngine()
system = SystemAnalyzer()
entropy_mod = EntropyModule()
predictor = PredictiveEngine()
LOGGER = logging.getLogger("aegis.api")
REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9._-]{1,80}$")

# Least-privilege policy. A missing/invalid token map denies every API route.
ROLE_LEVEL = {"viewer": 1, "operator": 2, "admin": 3}
ROUTE_LEVEL = {
    "/api/status": 1, "/api/uptime": 1,
    "/api/logs/analysis": 1, "/api/logs/threats": 1,
    "/api/threats": 2, "/api/listeners": 2, "/api/connections": 2,
    "/api/scan/": 2, "/api/vuln": 2, "/api/ioc": 2,
    "/api/payloads": 2, "/api/honeypot": 2,
    "/api/entropy": 3, "/api/blocklist": 3, "/api/forensics": 3,
    "/api/passwords": 3, "/api/predict": 3,
}


def load_token_roles():
    """Read token-to-role mapping from AEGIS_API_TOKENS JSON environment variable."""
    raw = os.environ.get("AEGIS_API_TOKENS", "")
    if not raw:
        return {}
    try:
        values = json.loads(raw)
    except (TypeError, ValueError):
        return {}
    if not isinstance(values, dict):
        return {}
    return {
        token: role for token, role in values.items()
        if isinstance(token, str) and len(token) >= 24
        and isinstance(role, str) and role in ROLE_LEVEL and token.strip()
    }


def _json_log(record):
    LOGGER.info(json.dumps(record, sort_keys=True, separators=(",", ":")))


class AegisAPIHandler(BaseHTTPRequestHandler):
    server_version = "AEGIS"
    sys_version = ""

    def _request_context(self):
        supplied = self.headers.get("X-Request-ID", "")
        request_id = supplied if REQUEST_ID_RE.fullmatch(supplied) else str(uuid.uuid4())
        self.request_id = request_id
        self.scan_id = request_id if self.path.split("?")[0].startswith("/api/scan/") else None
        self.send_header("X-Request-ID", request_id)
        if self.scan_id:
            self.send_header("X-Scan-ID", self.scan_id)
        return request_id

    def _authorize(self, path):
        if path == "/healthz":
            return True
        roles = load_token_roles()
        if not roles:
            self._respond(503, {"error": "authentication_not_configured"})
            return False
        scheme, _, token = self.headers.get("Authorization", "").partition(" ")
        role = roles.get(token) if scheme.lower() == "bearer" else None
        required = next((level for prefix, level in ROUTE_LEVEL.items()
                         if path == prefix or path.startswith(prefix)), None)
        if required is None:
            self._respond(404, {"error": "not_found", "path": path})
            return False
        if role is None or ROLE_LEVEL[role] < required:
            self._respond(401 if role is None else 403, {"error": "unauthorized" if role is None else "forbidden"})
            return False
        self.request_role = role
        return True

    def do_GET(self):
        path = self.path.split("?")[0]
        supplied_id = self.headers.get("X-Request-ID", "")
        self.request_id = supplied_id if REQUEST_ID_RE.fullmatch(supplied_id) else str(uuid.uuid4())
        self.scan_id = self.request_id if path.startswith("/api/scan/") else None
        if not self._authorize(path):
            return
        routes = {
            "/healthz": self._healthz,
            "/api/status": self._status,
            "/api/threats": self._threats,
            "/api/listeners": self._listeners,
            "/api/connections": self._connections,
            "/api/entropy": self._entropy,
            "/api/blocklist": self._blocklist,
            "/api/uptime": self._uptime,
            "/api/logs/analysis": self._log_analysis,
            "/api/logs/threats": self._threat_analysis,
            "/api/predict": self._predict,
            "/api/vuln": self._vuln_scan,
            "/api/ioc": self._ioc_scan,
            "/api/forensics": self._forensics,
            "/api/passwords": self._password_audit,
            "/api/payloads": self._payload_scan,
            "/api/honeypot": self._honeypot_stats,
        }
        handler = routes.get(path)
        if handler:
            handler()
        elif path.startswith("/api/scan/"):
            ip = path.split("/api/scan/", 1)[1]
            self._scan_ip(ip)
        else:
            self._respond(404, {"error": "not_found", "path": path})

    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()

    def _respond(self, code, data):
        body = json.dumps(data, default=str, separators=(",", ":")).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Engine", f"AEGIS-QByte22-v{__version__}")
        request_id = getattr(self, "request_id", str(uuid.uuid4()))
        self.send_header("X-Request-ID", request_id)
        scan_id = getattr(self, "scan_id", None)
        if scan_id:
            self.send_header("X-Scan-ID", scan_id)
        self.end_headers()
        self.wfile.write(body)
        _json_log({
            "timestamp": datetime.now(UTC).isoformat(),
            "event": "http_request",
            "request_id": request_id,
            "scan_id": scan_id,
            "method": self.command,
            "path": self.path.split("?")[0],
            "status": code,
            "role": getattr(self, "request_role", None),
        })

    def _healthz(self):
        self._respond(200, {"status": "ok", "time": datetime.now(UTC).isoformat()})

    def _status(self):
        self._respond(200, system.status())

    def _threats(self):
        threats = qbyte.scan_live_connections()
        self._respond(200, {
            "threats_found": len(threats),
            "results": [{"ip": t.ip, "score": t.score, "level": t.level, "action": t.action, "signals": t.signals} for t in threats],
        })

    def _listeners(self):
        self._respond(200, {"listeners": qbyte.scan_listeners()})

    def _connections(self):
        import psutil
        conns = []
        for c in psutil.net_connections(kind="inet"):
            if c.raddr:
                proc = None
                try:
                    proc = psutil.Process(c.pid).name() if c.pid else None
                except Exception:
                    pass
                conns.append({
                    "local": f"{c.laddr.ip}:{c.laddr.port}" if c.laddr else "",
                    "remote": f"{c.raddr.ip}:{c.raddr.port}",
                    "pid": c.pid, "process": proc, "status": c.status,
                })
        self._respond(200, {"connections": conns[:200]})

    def _scan_ip(self, ip):
        threat = qbyte.analyze_ip(ip)
        # Analysis only: blocking is deliberately not performed by an HTTP GET.
        self._respond(200, {
            "ip": threat.ip, "score": threat.score, "level": threat.level,
            "action": threat.action, "signals": threat.signals,
            "confidence": threat.confidence,
        })

    def _entropy(self):
        self._respond(200, entropy_mod.generate())

    def _blocklist(self):
        self._respond(200, {"blocked_ips": sorted(BLOCKLIST), "count": len(BLOCKLIST)})

    def _uptime(self):
        self._respond(200, uptime_checks())

    def _log_analysis(self):
        self._respond(200, analyze_system_logs())

    def _threat_analysis(self):
        self._respond(200, analyze_aegis_threats())

    def _predict(self):
        self._respond(200, predictor.train_on_history())

    def _vuln_scan(self):
        self._respond(200, vuln_scan())

    def _ioc_scan(self):
        self._respond(200, ioc_scan())

    def _forensics(self):
        self._respond(200, full_forensic_capture())

    def _password_audit(self):
        self._respond(200, password_audit())

    def _payload_scan(self):
        self._respond(200, payload_scan())

    def _honeypot_stats(self):
        self._respond(200, analyze_honeypot_logs())

    def log_message(self, format, *args):
        # BaseHTTPRequestHandler logs are suppressed; structured records are emitted in _respond.
        return


def main():
    port = int(os.environ.get("AEGIS_PORT", 8443))
    host = os.environ.get("AEGIS_HOST", "127.0.0.1")
    server = HTTPServer((host, port), AegisAPIHandler)
    print(f"AEGIS API Server v{__version__} running on http://{host}:{port}")
    print("Health endpoint: /healthz; all /api/* routes require role-mapped bearer tokens.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        server.server_close()


if __name__ == "__main__":
    main()
