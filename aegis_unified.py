#!/usr/bin/env python3
# Copyright (c) 2024-2026 Jorge Francisco Paredes (irstabyjorge)
# Licensed under dual MIT/Commercial license. See LICENSE and COMMERCIAL_LICENSE.md

__version__ = "2.0.0"

import os, json, subprocess, hashlib, time, ipaddress, socket
from pathlib import Path
from datetime import datetime, UTC
from collections import Counter
import psutil
from rich.console import Console
from rich.table import Table
from cryptography.fernet import Fernet

console = Console()
BASE = Path.home() / "aegis_omni_xeon"
LOGS = BASE / "logs"
DATA = BASE / "data"
LOGS.mkdir(parents=True, exist_ok=True)
DATA.mkdir(parents=True, exist_ok=True)
LOGFILE = LOGS / "aegis_unified_events.jsonl"
BLOCKLIST_FILE = DATA / "blocklist.txt"
KNOWN_GOOD_FILE = DATA / "known_good.txt"
THREAT_LOG = LOGS / "threat_log.jsonl"

SUSPICIOUS_PORTS = {22, 23, 25, 3389, 4444, 5555, 6667, 8333, 9735, 18080, 18081}
CRYPTO_PORTS = {8332, 8333, 18332, 18333, 30303, 9735, 18080, 18081}

BOGON_RANGES = [
    ipaddress.ip_network("0.0.0.0/8"), ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("100.64.0.0/10"), ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"), ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.0.0.0/24"), ipaddress.ip_network("192.0.2.0/24"),
    ipaddress.ip_network("192.168.0.0/16"), ipaddress.ip_network("198.18.0.0/15"),
    ipaddress.ip_network("198.51.100.0/24"), ipaddress.ip_network("203.0.113.0/24"),
    ipaddress.ip_network("224.0.0.0/4"), ipaddress.ip_network("240.0.0.0/4"),
]

TOR_EXIT_SIGNATURES = {
    "45.33.22.", "185.220.100.", "185.220.101.", "185.220.102.",
    "171.25.193.", "199.249.230.", "204.85.191.", "104.244.76.",
    "109.70.100.", "51.15.", "62.210.", "91.218.203.",
}

THREAT_INTEL_PATTERNS = {
    "23.94.", "23.95.", "45.33.", "45.55.", "45.76.", "45.77.",
    "64.225.", "68.183.", "104.131.", "104.236.", "104.248.",
    "128.199.", "134.209.", "138.68.", "139.59.", "142.93.",
    "157.245.", "159.65.", "159.89.", "161.35.", "164.90.",
    "165.22.", "165.227.", "167.71.", "167.99.", "174.138.",
    "178.128.", "178.62.", "188.166.", "192.241.", "198.199.",
    "206.189.", "209.97.",
}

SCANNER_NETS = {
    "71.6.135.", "71.6.146.", "71.6.158.", "71.6.165.",
    "80.82.77.", "93.174.95.", "162.142.125.", "167.248.",
    "198.235.24.", "205.210.31.",
}

def _load_lines(path):
    if path.exists():
        return set(path.read_text().strip().splitlines())
    return set()

BLOCKLIST = _load_lines(BLOCKLIST_FILE)
KNOWN_GOOD = _load_lines(KNOWN_GOOD_FILE)

def now():
    return datetime.now(UTC).isoformat()

def log(event, payload):
    with open(LOGFILE, "a") as f:
        f.write(json.dumps({"time": now(), "event": event, "payload": payload}, default=str) + "\n")

def run_cmd(cmd):
    try:
        r = subprocess.run(cmd, shell=True, text=True, capture_output=True, timeout=8)
        return {"ok": r.returncode == 0, "stdout": r.stdout[-4000:], "stderr": r.stderr[-2000:]}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def _is_bogon(ip):
    try:
        return any(ipaddress.ip_address(ip) in net for net in BOGON_RANGES)
    except ValueError:
        return False

def _matches_prefix(ip, prefixes):
    return any(ip.startswith(p) for p in prefixes)

def _reverse_dns(ip):
    try:
        return socket.gethostbyaddr(ip)[0]
    except (socket.herror, socket.gaierror, OSError):
        return None

def _compute_hash(data):
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()[:16]


def status():
    data = {
        "hostname": os.uname().nodename,
        "user": os.getenv("USER"),
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage("/").percent,
        "logical_cpus": psutil.cpu_count(logical=True),
        "physical_cpus": psutil.cpu_count(logical=False),
        "boot_time": datetime.fromtimestamp(psutil.boot_time(), UTC).isoformat(),
        "uptime_hours": round((time.time() - psutil.boot_time()) / 3600, 1),
    }
    log("status", data)
    return data

def listeners():
    rows = []
    for c in psutil.net_connections(kind="inet"):
        if c.status == "LISTEN":
            proc = None
            try:
                proc = psutil.Process(c.pid).name() if c.pid else None
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
            port = c.laddr.port if c.laddr else None
            rows.append({
                "local": f"{c.laddr.ip}:{c.laddr.port}" if c.laddr else "",
                "port": port,
                "pid": c.pid,
                "process": proc,
                "status": c.status,
                "suspicious": port in SUSPICIOUS_PORTS if port else False,
            })
    log("listeners", rows)
    return rows

def connections():
    rows = []
    for c in psutil.net_connections(kind="inet"):
        if c.raddr:
            proc = None
            try:
                proc = psutil.Process(c.pid).name() if c.pid else None
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
            rows.append({
                "local": f"{c.laddr.ip}:{c.laddr.port}" if c.laddr else "",
                "remote": f"{c.raddr.ip}:{c.raddr.port}",
                "remote_ip": c.raddr.ip,
                "remote_port": c.raddr.port,
                "pid": c.pid,
                "process": proc,
                "status": c.status,
            })
    log("connections", rows[:300])
    return rows[:300]

def analyze_ip(ip, context=None):
    """QByte-22 real IP threat analysis."""
    context = context or {}
    signals = []
    score = 0.0

    if ip in BLOCKLIST:
        score += 0.30
        signals.append("blocklisted")
    if _matches_prefix(ip, TOR_EXIT_SIGNATURES):
        score += 0.20
        signals.append("tor_exit_node")
    if _matches_prefix(ip, THREAT_INTEL_PATTERNS):
        score += 0.15
        signals.append("threat_intel_match")
    if _matches_prefix(ip, SCANNER_NETS):
        score += 0.20
        signals.append("known_scanner")
    if _is_bogon(ip):
        score += 0.10
        signals.append("bogon_range")

    rdns = _reverse_dns(ip)
    if rdns and any(x in rdns.lower() for x in ("vps", "cloud", "server", "host")):
        score += 0.10
        signals.append(f"hosting_rdns({rdns})")
    elif not rdns and not _is_bogon(ip):
        score += 0.05
        signals.append("no_rdns")

    port = context.get("port")
    if port:
        if port in CRYPTO_PORTS:
            score += 0.25
            signals.append(f"crypto_port({port})")
        elif port in SUSPICIOUS_PORTS:
            score += 0.15
            signals.append(f"suspicious_port({port})")

    if ip in KNOWN_GOOD and score < 0.60:
        score *= 0.5
        signals.append("known_good_dampened")

    score = min(1.0, score)
    if score >= 0.80:
        action, level = "BLOCK", "CRITICAL"
    elif score >= 0.60:
        action, level = "BLOCK", "HIGH"
    elif score >= 0.40:
        action, level = "CHALLENGE_MFA", "MEDIUM"
    elif score >= 0.25:
        action, level = "MONITOR", "LOW"
    else:
        action, level = "ALLOW", "CLEAR"

    result = {
        "ip": ip, "score": round(score, 4), "level": level,
        "action": action, "signals": signals,
        "confidence": round(min(0.95, 0.50 + len(signals) * 0.08), 3),
        "event_hash": _compute_hash({"ip": ip, **context}),
    }
    log("qbyte_analysis", result)
    return result

def threat_scan():
    conns = connections()
    lst = listeners()
    findings = []

    for x in conns:
        ip = x.get("remote_ip", "")
        port = x.get("remote_port")
        if port in SUSPICIOUS_PORTS or _matches_prefix(ip, THREAT_INTEL_PATTERNS):
            analysis = analyze_ip(ip, {"port": port, "process": x.get("process")})
            findings.append({
                "type": "connection_threat",
                "severity": int(analysis["score"] * 10),
                "analysis": analysis,
                "connection": x,
            })

    for x in lst:
        port = x.get("port")
        if port in SUSPICIOUS_PORTS:
            findings.append({
                "type": "suspicious_listener",
                "severity": 8 if port in {23, 3389, 4444, 5555} else 5,
                "item": x,
                "recommendation": "verify_service_is_expected",
            })

    ips = [x["remote_ip"] for x in conns if x.get("remote_ip")]
    for ip, count in Counter(ips).most_common():
        if count >= 10:
            findings.append({
                "type": "high_connection_count",
                "severity": 6,
                "remote_ip": ip,
                "count": count,
                "recommendation": "investigate_repeated_connections",
            })

    auto_blocked = 0
    for f in findings:
        analysis = f.get("analysis", {})
        if analysis.get("action") == "BLOCK":
            ip = analysis.get("ip", "")
            if ip and ip not in BLOCKLIST:
                try:
                    with open(BLOCKLIST_FILE, "a") as bf:
                        bf.write(ip + "\n")
                    BLOCKLIST.add(ip)
                    auto_blocked += 1
                except OSError:
                    pass

    log("threat_scan", {"findings": len(findings), "auto_blocked": auto_blocked})
    return {"findings": findings, "total": len(findings), "auto_blocked": auto_blocked}

def auth():
    files = ["/var/log/auth.log", "/var/log/syslog"]
    findings = []
    for fp in files:
        if Path(fp).exists():
            r = run_cmd(f"sudo tail -n 300 {fp} | grep -Ei 'failed|invalid|authentication|sudo|session|password' || true")
            findings.append({"file": fp, "events": r.get("stdout", "")})
    log("auth", findings)
    return findings

def firewall():
    data = {
        "ufw": run_cmd("sudo ufw status verbose"),
        "iptables": run_cmd("sudo iptables -S | head -n 120"),
    }
    log("firewall", data)
    return data

def packages():
    data = {
        "python": run_cmd("python3 --version"),
        "pip": run_cmd("pip3 list 2>/dev/null | head -40"),
        "apt_preview": run_cmd("apt list --installed 2>/dev/null | wc -l"),
        "snap": run_cmd("snap list 2>/dev/null | wc -l || true"),
    }
    log("packages", {"captured": True})
    return data

def entropy():
    key = Fernet.generate_key()
    digest = hashlib.sha512(key).hexdigest()
    data = {"fernet_key_generated": True, "sha512_digest": digest, "key_bytes": len(key), "entropy_bits": len(key) * 8}
    log("entropy", {"sha512_digest": digest})
    return data

def blocklist_info():
    return {"blocklist": sorted(BLOCKLIST), "count": len(BLOCKLIST), "file": str(BLOCKLIST_FILE)}

def full_audit():
    data = {
        "status": status(),
        "listeners": listeners(),
        "connections": connections(),
        "threat_scan": threat_scan(),
        "auth": auth(),
        "firewall": firewall(),
        "packages": packages(),
        "entropy": entropy(),
        "blocklist": blocklist_info(),
        "logfile": str(LOGFILE),
    }
    log("full_audit", {"complete": True})
    return data

def print_table(title, rows):
    t = Table(title=title)
    if not rows:
        console.print("[yellow]No results.[/yellow]")
        return
    keys = list(rows[0].keys())
    for k in keys:
        t.add_column(str(k))
    for r in rows[:50]:
        t.add_row(*[str(r.get(k, "")) for k in keys])
    console.print(t)

def help_menu():
    return {
        "commands": [
            "status           — system health overview",
            "listeners        — show listening ports",
            "connections      — show active connections",
            "threats          — scan connections with QByte-22 engine",
            "scan <ip> [port] — analyze specific IP",
            "auth             — audit authentication logs",
            "firewall         — show firewall status",
            "packages         — list installed packages",
            "entropy          — generate cryptographic key material",
            "blocklist        — show blocked IPs",
            "all              — run full security audit",
            "watch            — continuous threat monitoring",
            "logs             — view recent event log",
            "exit             — quit",
        ],
        "engine": f"QByte-22 v{__version__}",
    }

def main():
    console.print(f"[bold cyan]AEGIS UNIFIED v{__version__} — QByte-22 Engine[/bold cyan]")
    console.print("Type help. Type all for full audit. Type watch for continuous monitoring.")

    while True:
        try:
            cmd = input("AEGIS-UNIFIED> ").strip().lower()

            if cmd in {"exit", "quit"}:
                break
            elif cmd == "help":
                console.print_json(json.dumps(help_menu()))
            elif cmd == "status":
                console.print_json(json.dumps(status(), default=str))
            elif cmd == "listeners":
                print_table("Listening Services", listeners())
            elif cmd == "connections":
                print_table("Active Connections", connections())
            elif cmd in {"threats", "scan"}:
                console.print_json(json.dumps(threat_scan(), default=str))
            elif cmd.startswith("scan "):
                parts = cmd.split()
                ip = next((t for t in parts[1:] if t.count(".") == 3), None)
                port = next((int(t) for t in parts[1:] if t.isdigit()), None)
                if ip:
                    console.print_json(json.dumps(analyze_ip(ip, {"port": port} if port else {}), default=str))
                else:
                    console.print("[red]Usage: scan <ip> [port][/red]")
            elif cmd == "auth":
                console.print_json(json.dumps(auth(), default=str))
            elif cmd == "firewall":
                console.print_json(json.dumps(firewall(), default=str))
            elif cmd == "packages":
                console.print_json(json.dumps(packages(), default=str))
            elif cmd == "entropy":
                console.print_json(json.dumps(entropy(), default=str))
            elif cmd in {"blocklist", "blocked"}:
                console.print_json(json.dumps(blocklist_info(), default=str))
            elif cmd == "logs":
                console.print(run_cmd(f"tail -n 80 {LOGFILE}")["stdout"])
            elif cmd == "all":
                console.print_json(json.dumps(full_audit(), default=str))
            elif cmd == "watch":
                console.print("[green]Live threat monitoring (10s interval). Ctrl+C to stop.[/green]")
                while True:
                    scan_result = threat_scan()
                    console.print_json(json.dumps({
                        "time": now(),
                        "cpu": psutil.cpu_percent(interval=1),
                        "memory": psutil.virtual_memory().percent,
                        "threats_found": scan_result["total"],
                        "auto_blocked": scan_result["auto_blocked"],
                        "blocklist_size": len(BLOCKLIST),
                        "findings": scan_result["findings"],
                    }, default=str))
                    time.sleep(10)
            else:
                console.print({"unknown": cmd, "hint": "type help"})
        except KeyboardInterrupt:
            console.print("\nExiting.")
            break

if __name__ == "__main__":
    main()
