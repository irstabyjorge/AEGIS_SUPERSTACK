#!/usr/bin/env python3
# Copyright (c) 2024-2026 Jorge Francisco Paredes (irstabyjorge)
# Licensed under dual MIT/Commercial license. See LICENSE and COMMERCIAL_LICENSE.md
"""
AEGIS Forensics Toolkit — system forensic analysis and evidence collection.
Captures volatile system state, analyzes file timelines, inspects loaded
kernel modules, open file handles, and network socket state for incident response.
"""

import json, os, subprocess, hashlib
from datetime import datetime, UTC
from pathlib import Path
from collections import Counter

LOGS = Path.home() / "aegis_omni_xeon" / "logs"
LOGS.mkdir(parents=True, exist_ok=True)


def _run(cmd, timeout=15):
    try:
        r = subprocess.run(cmd, shell=True, text=True, capture_output=True, timeout=timeout)
        return r.stdout.strip()
    except Exception:
        return ""


def _log(event, payload):
    with open(LOGS / "forensics.jsonl", "a") as f:
        f.write(json.dumps({"time": datetime.now(UTC).isoformat(), "event": event, "payload": payload}, default=str) + "\n")


def capture_volatile_state():
    state = {
        "timestamp": datetime.now(UTC).isoformat(),
        "hostname": _run("hostname"),
        "uptime": _run("uptime -p"),
        "current_users": _run("who 2>/dev/null"),
        "last_logins": _run("last -n 20 2>/dev/null"),
        "running_processes": _run("ps auxf --no-headers 2>/dev/null | head -100"),
        "network_connections": _run("ss -tunapo 2>/dev/null | head -50"),
        "listening_ports": _run("ss -tlnp 2>/dev/null"),
        "routing_table": _run("ip route 2>/dev/null"),
        "arp_cache": _run("ip neigh 2>/dev/null"),
        "dns_config": _run("cat /etc/resolv.conf 2>/dev/null"),
        "mounted_filesystems": _run("mount 2>/dev/null"),
        "loaded_kernel_modules": _run("lsmod 2>/dev/null | head -50"),
        "environment_variables": _run("env 2>/dev/null | grep -v 'PASSWORD\\|SECRET\\|TOKEN\\|KEY\\|CREDENTIAL' | head -50"),
    }
    _log("volatile_state_capture", {"fields": list(state.keys())})
    return state


def analyze_recent_file_changes(hours=24):
    findings = []
    critical_dirs = ["/etc", "/usr/bin", "/usr/sbin", "/usr/lib", "/bin", "/sbin"]

    for d in critical_dirs:
        output = _run(f"find {d} -type f -mmin -{hours * 60} 2>/dev/null | head -30", timeout=20)
        for filepath in output.splitlines():
            if not filepath.strip():
                continue
            try:
                st = os.stat(filepath)
                findings.append({
                    "path": filepath,
                    "modified": datetime.fromtimestamp(st.st_mtime, UTC).isoformat(),
                    "size": st.st_size,
                    "uid": st.st_uid,
                    "mode": oct(st.st_mode),
                })
            except (PermissionError, OSError):
                pass

    return {
        "check": "recent_system_file_changes",
        "hours_scanned": hours,
        "dirs_scanned": critical_dirs,
        "total_changed": len(findings),
        "severity": 7 if findings else 1,
        "findings": findings[:50],
    }


def check_loaded_modules():
    output = _run("lsmod 2>/dev/null")
    modules = []
    suspicious = []

    known_suspicious = {"reptile", "diamorphine", "rootkit", "suterusu", "bdvl", "jynx", "azazel", "vlany", "brootus"}

    for line in output.splitlines()[1:]:
        parts = line.split()
        if not parts:
            continue
        name = parts[0].lower()
        size = parts[1] if len(parts) > 1 else "?"
        used_by = parts[3] if len(parts) > 3 else ""
        modules.append({"name": parts[0], "size": size, "used_by": used_by})

        if name in known_suspicious:
            suspicious.append({"module": parts[0], "reason": "known_rootkit_module", "severity": 10})

    unsigned = _run("for mod in $(lsmod | tail -n+2 | awk '{print $1}'); do modinfo $mod 2>/dev/null | grep -q 'sig_id' || echo $mod; done 2>/dev/null")
    unsigned_list = [m.strip() for m in unsigned.splitlines() if m.strip()]

    return {
        "check": "kernel_modules",
        "total_modules": len(modules),
        "suspicious_modules": suspicious,
        "unsigned_modules": unsigned_list[:20],
        "severity": 10 if suspicious else (5 if unsigned_list else 1),
    }


def check_open_file_handles():
    deleted = _run("ls -la /proc/*/fd 2>/dev/null | grep '(deleted)' | head -20")
    findings = []
    for line in deleted.splitlines():
        if "(deleted)" in line:
            findings.append(line.strip()[:200])

    suspicious_fd = _run("ls -la /proc/*/fd 2>/dev/null | grep -E '/tmp/|/dev/shm/|/var/tmp/' | head -20")
    temp_refs = []
    for line in suspicious_fd.splitlines():
        if line.strip():
            temp_refs.append(line.strip()[:200])

    return {
        "check": "open_file_handles",
        "deleted_files_still_open": len(findings),
        "deleted_entries": findings,
        "temp_file_references": temp_refs,
        "severity": 6 if findings or temp_refs else 1,
    }


def check_user_accounts():
    findings = []

    passwd_output = _run("cat /etc/passwd 2>/dev/null")
    for line in passwd_output.splitlines():
        parts = line.strip().split(":")
        if len(parts) < 7:
            continue
        username, uid, gid, home, shell = parts[0], int(parts[2]), int(parts[3]), parts[5], parts[6]

        if uid == 0 and username != "root":
            findings.append({
                "type": "uid_zero_user",
                "username": username,
                "shell": shell,
                "severity": 10,
            })

        if shell in ("/bin/bash", "/bin/sh", "/bin/zsh", "/usr/bin/bash", "/usr/bin/zsh"):
            if uid >= 1000 or uid == 0:
                continue
            if username not in ("root", "sync", "shutdown", "halt"):
                findings.append({
                    "type": "system_user_with_shell",
                    "username": username,
                    "uid": uid,
                    "shell": shell,
                    "severity": 5,
                })

    sudoers_output = _run("sudo -n cat /etc/sudoers 2>/dev/null; ls /etc/sudoers.d/ 2>/dev/null")
    nopasswd_users = []
    for line in sudoers_output.splitlines():
        if "NOPASSWD" in line and not line.strip().startswith("#"):
            nopasswd_users.append(line.strip()[:200])

    if nopasswd_users:
        findings.append({
            "type": "nopasswd_sudo",
            "entries": nopasswd_users,
            "severity": 6,
        })

    max_sev = max((f["severity"] for f in findings), default=1)
    return {
        "check": "user_account_audit",
        "severity": max_sev,
        "findings": findings,
    }


def hash_critical_binaries():
    critical_bins = [
        "/usr/bin/ssh", "/usr/bin/sudo", "/usr/bin/su",
        "/usr/bin/passwd", "/usr/bin/login", "/usr/bin/curl",
        "/usr/bin/wget", "/usr/sbin/sshd", "/usr/bin/crontab",
        "/bin/bash", "/bin/sh", "/usr/bin/python3",
    ]
    hashes = {}
    for b in critical_bins:
        p = Path(b)
        if p.exists():
            try:
                h = hashlib.sha256(p.read_bytes()).hexdigest()
                hashes[b] = {
                    "sha256": h,
                    "size": p.stat().st_size,
                    "modified": datetime.fromtimestamp(p.stat().st_mtime, UTC).isoformat(),
                }
            except (PermissionError, OSError):
                hashes[b] = {"error": "permission_denied"}

    return {
        "check": "critical_binary_hashes",
        "binaries_hashed": len(hashes),
        "hashes": hashes,
        "severity": 1,
    }


def full_forensic_capture():
    results = {
        "timestamp": datetime.now(UTC).isoformat(),
        "volatile_state": capture_volatile_state(),
        "recent_changes": analyze_recent_file_changes(24),
        "kernel_modules": check_loaded_modules(),
        "file_handles": check_open_file_handles(),
        "user_accounts": check_user_accounts(),
        "binary_hashes": hash_critical_binaries(),
    }

    checks = [results["recent_changes"], results["kernel_modules"],
              results["file_handles"], results["user_accounts"]]
    max_severity = max(c["severity"] for c in checks)

    results["overall_severity"] = max_severity
    results["risk_level"] = "CRITICAL" if max_severity >= 8 else "WARNING" if max_severity >= 5 else "NORMAL"

    _log("full_forensic_capture", {
        "risk_level": results["risk_level"],
        "severity": max_severity,
    })

    report_path = LOGS / f"forensic_report_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_path, "w") as f:
        json.dump(results, f, indent=2, default=str)

    results["report_saved_to"] = str(report_path)
    return results


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "volatile":
        print(json.dumps(capture_volatile_state(), indent=2, default=str))
    elif len(sys.argv) > 1 and sys.argv[1] == "hashes":
        print(json.dumps(hash_critical_binaries(), indent=2, default=str))
    else:
        print(json.dumps(full_forensic_capture(), indent=2, default=str))
