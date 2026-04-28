#!/usr/bin/env python3
# Copyright (c) 2024-2026 Jorge Francisco Paredes (irstabyjorge)
# Licensed under dual MIT/Commercial license. See LICENSE and COMMERCIAL_LICENSE.md
"""
AEGIS Honeypot — lightweight decoy service for detecting intrusion attempts.
Opens configurable fake ports (SSH, FTP, Telnet, HTTP, MySQL, Redis, etc.)
and logs every connection attempt with full metadata for threat intelligence.
"""

import json, socket, threading, time, select
from datetime import datetime, UTC
from pathlib import Path
from collections import Counter

LOGS = Path.home() / "aegis_omni_xeon" / "logs"
LOGS.mkdir(parents=True, exist_ok=True)
HONEYPOT_LOG = LOGS / "honeypot_events.jsonl"

DECOY_BANNERS = {
    22: "SSH-2.0-OpenSSH_8.9p1 Ubuntu-3ubuntu0.1\r\n",
    21: "220 (vsFTPd 3.0.5)\r\n",
    23: "\xff\xfd\x18\xff\xfd\x20\xff\xfd\x23\xff\xfd\x27",
    25: "220 mail.localdomain ESMTP Postfix\r\n",
    80: "HTTP/1.1 200 OK\r\nServer: Apache/2.4.54\r\nContent-Length: 0\r\n\r\n",
    443: "HTTP/1.1 400 Bad Request\r\nServer: nginx/1.24.0\r\n\r\n",
    3306: "\x4a\x00\x00\x00\x0a\x38\x2e\x30\x2e\x33\x33",
    5432: "E\x00\x00\x00\x4dSFATAL\x00",
    6379: "-ERR unknown command\r\n",
    8080: "HTTP/1.1 403 Forbidden\r\nServer: Jetty(9.4.51)\r\n\r\n",
    8443: "HTTP/1.1 401 Unauthorized\r\nWWW-Authenticate: Basic\r\n\r\n",
    27017: "",
    9200: '{"error":"security_exception","status":403}\n',
    2222: "SSH-2.0-OpenSSH_7.4\r\n",
    11211: "ERROR\r\n",
}

DEFAULT_PORTS = [2222, 2121, 2323, 8080, 9200, 11211, 6380, 27018]


def _log(event, payload):
    with open(HONEYPOT_LOG, "a") as f:
        f.write(json.dumps({
            "time": datetime.now(UTC).isoformat(),
            "event": event,
            "payload": payload,
        }, default=str) + "\n")


def _handle_connection(client_sock, addr, port, banner):
    ip, src_port = addr
    received = b""
    try:
        if banner:
            client_sock.sendall(banner.encode() if isinstance(banner, str) else banner)

        client_sock.settimeout(5)
        try:
            received = client_sock.recv(4096)
        except (socket.timeout, ConnectionResetError):
            pass

        _log("honeypot_connection", {
            "source_ip": ip,
            "source_port": src_port,
            "decoy_port": port,
            "data_received": received.decode("utf-8", errors="replace")[:500] if received else "",
            "data_length": len(received),
        })
    except Exception as e:
        _log("honeypot_error", {"source_ip": ip, "port": port, "error": str(e)})
    finally:
        try:
            client_sock.close()
        except Exception:
            pass


def _run_listener(port, banner, stop_event):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        sock.bind(("0.0.0.0", port))
        sock.listen(5)
        sock.settimeout(1)
        _log("honeypot_start", {"port": port})

        while not stop_event.is_set():
            try:
                client, addr = sock.accept()
                t = threading.Thread(target=_handle_connection, args=(client, addr, port, banner), daemon=True)
                t.start()
            except socket.timeout:
                continue
            except OSError:
                break
    except OSError as e:
        _log("honeypot_bind_error", {"port": port, "error": str(e)})
    finally:
        sock.close()


def start(ports=None):
    ports = ports or DEFAULT_PORTS
    stop_event = threading.Event()
    threads = []

    for port in ports:
        banner = DECOY_BANNERS.get(port, "")
        t = threading.Thread(target=_run_listener, args=(port, banner, stop_event), daemon=True)
        t.start()
        threads.append(t)

    return stop_event, threads


def analyze_honeypot_logs():
    if not HONEYPOT_LOG.exists():
        return {"status": "no_honeypot_data"}

    connections = []
    ip_counter = Counter()
    port_counter = Counter()
    payloads = []

    try:
        with open(HONEYPOT_LOG) as f:
            for line in f:
                entry = json.loads(line.strip())
                if entry.get("event") == "honeypot_connection":
                    p = entry["payload"]
                    connections.append(p)
                    ip_counter[p["source_ip"]] += 1
                    port_counter[p["decoy_port"]] += 1
                    if p.get("data_received"):
                        payloads.append({
                            "ip": p["source_ip"],
                            "port": p["decoy_port"],
                            "data": p["data_received"][:200],
                            "time": entry["time"],
                        })
    except (json.JSONDecodeError, OSError):
        return {"status": "parse_error"}

    return {
        "timestamp": datetime.now(UTC).isoformat(),
        "total_connections": len(connections),
        "unique_ips": len(ip_counter),
        "top_attackers": [{"ip": ip, "count": c} for ip, c in ip_counter.most_common(20)],
        "targeted_ports": [{"port": p, "count": c} for p, c in port_counter.most_common()],
        "payloads_captured": len(payloads),
        "recent_payloads": payloads[-20:],
    }


def run_interactive(ports=None):
    ports = ports or DEFAULT_PORTS
    print(f"AEGIS Honeypot — listening on {len(ports)} decoy ports. Ctrl+C to stop.")
    print(f"Ports: {', '.join(str(p) for p in ports)}")
    print(f"Logging to: {HONEYPOT_LOG}\n")

    stop_event, threads = start(ports)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down honeypot...")
        stop_event.set()
        for t in threads:
            t.join(timeout=3)
        print("Honeypot stopped.")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "analyze":
        print(json.dumps(analyze_honeypot_logs(), indent=2, default=str))
    else:
        run_interactive()
