#!/usr/bin/env python3
# Copyright (c) 2024-2026 Jorge Francisco Paredes (irstabyjorge)
# Licensed under dual MIT/Commercial license. See LICENSE and COMMERCIAL_LICENSE.md
"""
AEGIS Uptime Monitor — service availability tracking.
Monitors HTTP endpoints, TCP ports, and DNS resolution.
Logs response times and status for SLA reporting.
"""

import json, socket, time, ssl, hashlib
from datetime import datetime, UTC
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError

LOGS = Path.home() / "aegis_omni_xeon" / "logs"
LOGS.mkdir(parents=True, exist_ok=True)
MONITOR_LOG = LOGS / "uptime_events.jsonl"


def _log(event, payload):
    with open(MONITOR_LOG, "a") as f:
        f.write(json.dumps({"time": datetime.now(UTC).isoformat(), "event": event, "payload": payload}, default=str) + "\n")


def check_http(url, timeout=10):
    start = time.time()
    try:
        ctx = ssl.create_default_context()
        req = Request(url, headers={"User-Agent": "AEGIS-Monitor/2.0"})
        resp = urlopen(req, timeout=timeout, context=ctx)
        elapsed = round((time.time() - start) * 1000, 1)
        result = {
            "url": url,
            "status": "up",
            "http_code": resp.getcode(),
            "response_ms": elapsed,
            "content_length": len(resp.read()),
        }
    except URLError as e:
        elapsed = round((time.time() - start) * 1000, 1)
        result = {
            "url": url,
            "status": "down",
            "error": str(e.reason) if hasattr(e, "reason") else str(e),
            "response_ms": elapsed,
        }
    except Exception as e:
        elapsed = round((time.time() - start) * 1000, 1)
        result = {"url": url, "status": "error", "error": str(e), "response_ms": elapsed}

    _log("http_check", result)
    return result


def check_tcp(host, port, timeout=5):
    start = time.time()
    try:
        sock = socket.create_connection((host, port), timeout=timeout)
        elapsed = round((time.time() - start) * 1000, 1)
        sock.close()
        result = {"host": host, "port": port, "status": "open", "response_ms": elapsed}
    except (socket.timeout, ConnectionRefusedError, OSError) as e:
        elapsed = round((time.time() - start) * 1000, 1)
        result = {"host": host, "port": port, "status": "closed", "error": str(e), "response_ms": elapsed}

    _log("tcp_check", result)
    return result


def check_dns(hostname, timeout=5):
    start = time.time()
    try:
        socket.setdefaulttimeout(timeout)
        ips = socket.getaddrinfo(hostname, None)
        elapsed = round((time.time() - start) * 1000, 1)
        resolved = list({addr[4][0] for addr in ips})
        result = {"hostname": hostname, "status": "resolved", "ips": resolved, "response_ms": elapsed}
    except socket.gaierror as e:
        elapsed = round((time.time() - start) * 1000, 1)
        result = {"hostname": hostname, "status": "failed", "error": str(e), "response_ms": elapsed}

    _log("dns_check", result)
    return result


def check_ssl_cert(hostname, port=443):
    try:
        ctx = ssl.create_default_context()
        with ctx.wrap_socket(socket.socket(), server_hostname=hostname) as s:
            s.settimeout(5)
            s.connect((hostname, port))
            cert = s.getpeercert()
            not_after = cert.get("notAfter", "")
            expiry = datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z") if not_after else None
            days_left = (expiry - datetime.now()).days if expiry else None
            result = {
                "hostname": hostname,
                "status": "valid",
                "issuer": dict(x[0] for x in cert.get("issuer", [])),
                "subject": dict(x[0] for x in cert.get("subject", [])),
                "expires": not_after,
                "days_until_expiry": days_left,
                "warning": days_left is not None and days_left < 30,
            }
    except Exception as e:
        result = {"hostname": hostname, "status": "error", "error": str(e)}

    _log("ssl_check", result)
    return result


DEFAULT_TARGETS = [
    {"type": "http", "url": "https://github.com"},
    {"type": "http", "url": "https://google.com"},
    {"type": "dns", "hostname": "github.com"},
    {"type": "dns", "hostname": "google.com"},
    {"type": "tcp", "host": "8.8.8.8", "port": 53},
    {"type": "ssl", "hostname": "github.com"},
]


def run_checks(targets=None):
    targets = targets or DEFAULT_TARGETS
    results = []
    for t in targets:
        if t["type"] == "http":
            results.append(check_http(t["url"]))
        elif t["type"] == "tcp":
            results.append(check_tcp(t["host"], t["port"]))
        elif t["type"] == "dns":
            results.append(check_dns(t["hostname"]))
        elif t["type"] == "ssl":
            results.append(check_ssl_cert(t["hostname"]))
    return {
        "timestamp": datetime.now(UTC).isoformat(),
        "checks": len(results),
        "up": sum(1 for r in results if r.get("status") in ("up", "open", "resolved", "valid")),
        "down": sum(1 for r in results if r.get("status") not in ("up", "open", "resolved", "valid")),
        "results": results,
    }


def watch(interval=30, targets=None):
    print(f"AEGIS Uptime Monitor — checking every {interval}s. Ctrl+C to stop.")
    while True:
        report = run_checks(targets)
        for r in report["results"]:
            status = r.get("status", "unknown")
            name = r.get("url") or r.get("hostname") or f"{r.get('host')}:{r.get('port')}"
            ms = r.get("response_ms", "?")
            icon = "UP" if status in ("up", "open", "resolved", "valid") else "DOWN"
            print(f"  [{icon}] {name} — {ms}ms")
        print(f"  [{report['up']}/{report['checks']} up] {report['timestamp']}\n")
        time.sleep(interval)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "watch":
        watch()
    else:
        results = run_checks()
        print(json.dumps(results, indent=2, default=str))
