#!/usr/bin/env python3
# Copyright (c) 2024-2026 Jorge Francisco Paredes (irstabyjorge)
# Licensed under dual MIT/Commercial license. See LICENSE and COMMERCIAL_LICENSE.md

__version__ = "1.0.0"

import os, json, subprocess, hashlib
from datetime import datetime, UTC
from pathlib import Path
import psutil
from rich.console import Console
from rich.table import Table
from cryptography.fernet import Fernet

console = Console()
BASE = Path.home() / "aegis_omni_xeon"
LOGS = BASE / "logs"
LOGS.mkdir(parents=True, exist_ok=True)

def now():
    return datetime.now(UTC).isoformat()

def log(event, payload):
    with open(LOGS / "aegis_real_events.jsonl", "a") as f:
        f.write(json.dumps({"time": now(), "event": event, "payload": payload}, default=str) + "\n")

def run_cmd(cmd):
    try:
        r = subprocess.run(cmd, shell=True, text=True, capture_output=True, timeout=8)
        return {"ok": r.returncode == 0, "stdout": r.stdout[-4000:], "stderr": r.stderr[-2000:]}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def system_status():
    data = {
        "hostname": os.uname().nodename,
        "user": os.getenv("USER"),
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage("/").percent,
        "logical_cpus": psutil.cpu_count(logical=True),
        "physical_cpus": psutil.cpu_count(logical=False),
        "boot_time": datetime.fromtimestamp(psutil.boot_time(), UTC).isoformat()
    }
    log("system_status", data)
    return data

def network_connections():
    rows = []
    for c in psutil.net_connections(kind="inet"):
        if c.status == "LISTEN":
            rows.append({
                "local": f"{c.laddr.ip}:{c.laddr.port}" if c.laddr else "",
                "pid": c.pid,
                "process": psutil.Process(c.pid).name() if c.pid else None,
                "status": c.status
            })
    log("network_listeners", rows)
    return rows

def active_connections():
    rows = []
    for c in psutil.net_connections(kind="inet"):
        if c.raddr:
            rows.append({
                "local": f"{c.laddr.ip}:{c.laddr.port}" if c.laddr else "",
                "remote": f"{c.raddr.ip}:{c.raddr.port}",
                "pid": c.pid,
                "process": psutil.Process(c.pid).name() if c.pid else None,
                "status": c.status
            })
    log("active_connections", rows[:200])
    return rows[:200]

def auth_report():
    files = ["/var/log/auth.log", "/var/log/syslog"]
    findings = []
    for fp in files:
        if Path(fp).exists():
            result = run_cmd(f"sudo tail -n 200 {fp} | grep -Ei 'failed|invalid|authentication|sudo|session' || true")
            findings.append({"file": fp, "events": result.get("stdout", "")})
    log("auth_report", findings)
    return findings

def firewall_status():
    ufw = run_cmd("sudo ufw status verbose")
    iptables = run_cmd("sudo iptables -S | head -n 80")
    data = {"ufw": ufw, "iptables_preview": iptables}
    log("firewall_status", data)
    return data

def entropy_key():
    key = Fernet.generate_key()
    digest = hashlib.sha512(key).hexdigest()
    data = {
        "fernet_key_created": True,
        "sha512_digest": digest,
        "stored": False
    }
    log("entropy_key", {"sha512_digest": digest})
    return data

def full_report():
    data = {
        "system": system_status(),
        "listeners": network_connections(),
        "connections": active_connections(),
        "auth": auth_report(),
        "firewall": firewall_status(),
        "entropy": entropy_key(),
        "log_file": str(LOGS / "aegis_real_events.jsonl")
    }
    log("full_report", {"complete": True})
    return data

def print_table(title, rows):
    table = Table(title=title)
    if not rows:
        console.print("[yellow]No rows.[/yellow]")
        return
    for k in rows[0].keys():
        table.add_column(str(k))
    for row in rows:
        table.add_row(*[str(row.get(k, "")) for k in rows[0].keys()])
    console.print(table)

def main():
    console.print("[bold cyan]AEGIS REAL SYSTEM MODE[/bold cyan]")
    console.print("Commands: status, listeners, connections, auth, firewall, entropy, all, exit")

    while True:
        cmd = input("AEGIS-REAL> ").strip().lower()

        if cmd in {"exit", "quit"}:
            break
        elif cmd == "status":
            console.print_json(json.dumps(system_status(), default=str))
        elif cmd == "listeners":
            print_table("Listening Network Services", network_connections())
        elif cmd == "connections":
            print_table("Active Network Connections", active_connections())
        elif cmd == "auth":
            console.print_json(json.dumps(auth_report(), default=str))
        elif cmd == "firewall":
            console.print_json(json.dumps(firewall_status(), default=str))
        elif cmd == "entropy":
            console.print_json(json.dumps(entropy_key(), default=str))
        elif cmd == "all":
            console.print_json(json.dumps(full_report(), default=str))
        else:
            console.print({"unknown": cmd, "commands": ["status","listeners","connections","auth","firewall","entropy","all","exit"]})

if __name__ == "__main__":
    main()
