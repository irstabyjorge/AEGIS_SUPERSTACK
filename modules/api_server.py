#!/usr/bin/env python3
# Copyright (c) 2024-2026 Jorge Francisco Paredes (irstabyjorge)
# Licensed under dual MIT/Commercial license. See LICENSE and COMMERCIAL_LICENSE.md
"""
AEGIS API Server — REST API exposing all AEGIS capabilities.
Built with http.server (zero external deps). For production, use with FastAPI.
"""

import json, os, sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime, UTC
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from aegis_omni import QByteEngine, SystemAnalyzer, EntropyModule, PredictiveEngine, BLOCKLIST, __version__
from modules.uptime_monitor import run_checks as uptime_checks
from modules.log_analyzer import analyze_system_logs, analyze_aegis_threats


qbyte = QByteEngine()
system = SystemAnalyzer()
entropy_mod = EntropyModule()
predictor = PredictiveEngine()


class AegisAPIHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split("?")[0]
        routes = {
            "/": self._index,
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
        }

        handler = routes.get(path)
        if handler:
            handler()
        elif path.startswith("/api/scan/"):
            ip = path.split("/api/scan/")[1]
            self._scan_ip(ip)
        else:
            self._respond(404, {"error": "not_found", "path": path, "endpoints": list(routes.keys())})

    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()

    def _respond(self, code, data):
        body = json.dumps(data, default=str, indent=2).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Engine", f"AEGIS-QByte22-v{__version__}")
        self.end_headers()
        self.wfile.write(body)

    def _index(self):
        self._respond(200, {
            "service": "AEGIS OMNI-XEON API",
            "version": __version__,
            "engine": "QByte-22",
            "endpoints": [
                "GET /healthz",
                "GET /api/status",
                "GET /api/threats",
                "GET /api/listeners",
                "GET /api/connections",
                "GET /api/scan/<ip>",
                "GET /api/entropy",
                "GET /api/blocklist",
                "GET /api/uptime",
                "GET /api/logs/analysis",
                "GET /api/logs/threats",
                "GET /api/predict",
            ],
        })

    def _healthz(self):
        self._respond(200, {"status": "ok", "engine": f"QByte-22 v{__version__}", "time": datetime.now(UTC).isoformat()})

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
        qbyte.auto_blocklist(threat)
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

    def log_message(self, format, *args):
        pass


def main():
    port = int(os.environ.get("AEGIS_PORT", 8443))
    server = HTTPServer(("0.0.0.0", port), AegisAPIHandler)
    print(f"AEGIS API Server v{__version__} running on http://0.0.0.0:{port}")
    print(f"Endpoints: http://localhost:{port}/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        server.server_close()


if __name__ == "__main__":
    main()
