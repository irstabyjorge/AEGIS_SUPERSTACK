#!/usr/bin/env python3
# Copyright (c) 2024-2026 Jorge Francisco Paredes (irstabyjorge)
# Licensed under dual MIT/Commercial license. See LICENSE and COMMERCIAL_LICENSE.md
"""Read-only local vulnerability checks. All subprocess calls use fixed argv."""

import json
import os
import stat
import subprocess
from datetime import datetime, UTC
from pathlib import Path

LOGS = Path.home() / "aegis_omni_xeon" / "logs"
LOGS.mkdir(parents=True, exist_ok=True)

_SKIP_DIRS = {"/proc", "/sys", "/dev", "/run"}
_MAX_WALK_DIRS = 10000


def _run(args, timeout=10):
    """Run a fixed argument vector; never interpret shell syntax."""
    if not isinstance(args, (list, tuple)) or not args or not all(isinstance(x, str) for x in args):
        return ""
    try:
        result = subprocess.run(
            list(args), shell=False, text=True, capture_output=True, timeout=timeout,
            check=False,
        )
        return result.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def _bounded_files(roots, predicate, limit):
    found = []
    visited = 0
    for root in roots:
        root_path = Path(root)
        if not root_path.exists():
            continue
        if root_path.is_file():
            candidates = (root_path,)
        else:
            def walk():
                nonlocal visited
                for current, dirs, names in os.walk(root_path, followlinks=False):
                    dirs[:] = [d for d in dirs if str(Path(current) / d) not in _SKIP_DIRS]
                    visited += 1
                    if visited > _MAX_WALK_DIRS:
                        return
                    for name in names:
                        yield Path(current) / name
            candidates = walk()
        for candidate in candidates:
            try:
                if candidate.is_file() and predicate(candidate.stat()):
                    found.append(str(candidate))
                    if len(found) >= limit:
                        return found
            except (PermissionError, OSError):
                continue
        if visited > _MAX_WALK_DIRS:
            break
    return found


def _log(event, payload):
    with open(LOGS / "vuln_scan.jsonl", "a") as f:
        f.write(json.dumps({"time": datetime.now(UTC).isoformat(), "event": event, "payload": payload}, default=str) + "\n")


def check_suid_files():
    files = _bounded_files(
        ["/"], lambda st: bool(st.st_mode & stat.S_ISUID), 50
    )
    dangerous = [f for f in files if any(x in f for x in ("/tmp/", "/home/", "/var/tmp/", "/dev/shm/"))]
    return {
        "check": "suid_files",
        "severity": 8 if dangerous else 3,
        "total_suid": len(files),
        "suspicious_locations": dangerous,
        "all_suid": files,
    }


def check_world_writable():
    files = _bounded_files(
        ["/etc", "/usr", "/var"],
        lambda st: stat.S_ISREG(st.st_mode) and bool(st.st_mode & stat.S_IWOTH),
        30,
    )
    return {
        "check": "world_writable_files",
        "severity": 7 if files else 1,
        "count": len(files),
        "files": files,
    }


def check_ssh_config():
    findings = []
    ssh_config = Path("/etc/ssh/sshd_config")
    if ssh_config.exists():
        try:
            content = ssh_config.read_text()
            if "PermitRootLogin yes" in content:
                findings.append({"issue": "root_login_enabled", "severity": 9})
            if "PasswordAuthentication yes" in content:
                findings.append({"issue": "password_auth_enabled", "severity": 6})
            if "PermitEmptyPasswords yes" in content:
                findings.append({"issue": "empty_passwords_allowed", "severity": 10})
            if "X11Forwarding yes" in content:
                findings.append({"issue": "x11_forwarding_enabled", "severity": 4})
        except PermissionError:
            findings.append({"issue": "cannot_read_sshd_config", "severity": 3})
    else:
        findings.append({"issue": "no_sshd_config", "severity": 2})
    return {"check": "ssh_configuration", "severity": max((f["severity"] for f in findings), default=0), "findings": findings}


def check_firewall():
    ufw = _run(["sudo", "-n", "ufw", "status"])
    if not ufw:
        ufw = "no_access"
    active = "Status: active" in ufw
    return {"check": "firewall_status", "severity": 1 if active else 8, "active": active, "output": ufw[:500]}


def check_unattended_upgrades():
    installed = _run(["dpkg-query", "-W", "-f=${db:Status-Status}", "unattended-upgrades"])
    present = installed.strip() == "installed"
    return {"check": "auto_updates", "severity": 1 if present else 5, "installed": present}


def check_open_ports():
    import psutil
    listeners = []
    for conn in psutil.net_connections(kind="inet"):
        if conn.status == "LISTEN" and conn.laddr:
            ip, port = conn.laddr.ip, conn.laddr.port
            if ip in ("0.0.0.0", "::"):
                proc = None
                try:
                    proc = psutil.Process(conn.pid).name() if conn.pid else None
                except (psutil.Error, OSError):
                    pass
                listeners.append({"ip": ip, "port": port, "pid": conn.pid, "process": proc})
    high_risk = [item for item in listeners if item["port"] in {21, 23, 25, 3306, 5432, 6379, 27017, 9200}]
    return {"check": "exposed_ports", "severity": 8 if high_risk else 2, "total_listening": len(listeners), "exposed_to_all": listeners, "high_risk_services": high_risk}


def check_sensitive_files():
    sensitive = ["/etc/shadow", "/etc/gshadow", "/root/.ssh/id_rsa", "/root/.bash_history", "/root/.mysql_history"]
    readable = []
    for fp in sensitive:
        path = Path(fp)
        if path.exists():
            try:
                st = path.stat()
                if st.st_mode & stat.S_IROTH:
                    readable.append({"file": fp, "mode": oct(st.st_mode)})
            except (PermissionError, OSError):
                pass
    return {"check": "sensitive_file_permissions", "severity": 9 if readable else 1, "world_readable": readable}


def check_running_as_root():
    return {"check": "running_as_root", "severity": 3 if os.geteuid() == 0 else 1, "is_root": os.geteuid() == 0, "uid": os.getuid(), "user": os.getenv("USER")}


def check_kernel_hardening():
    checks = {
        "aslr": ("/proc/sys/kernel/randomize_va_space", "2"),
        "sysrq_disabled": ("/proc/sys/kernel/sysrq", "0"),
        "core_dumps_restricted": ("/proc/sys/fs/suid_dumpable", "0"),
        "ptrace_restricted": ("/proc/sys/kernel/yama/ptrace_scope", "1"),
    }
    results = {}
    max_sev = 1
    for name, (filename, expected) in checks.items():
        try:
            value = Path(filename).read_text().strip()
        except (OSError, PermissionError):
            value = ""
        compliant = value == expected
        results[name] = {"value": value, "expected": expected, "compliant": compliant}
        if not compliant:
            max_sev = max(max_sev, 5)
    return {"check": "kernel_hardening", "severity": max_sev, "settings": results}


def full_scan():
    checks = [check_running_as_root(), check_ssh_config(), check_firewall(), check_open_ports(), check_suid_files(), check_world_writable(), check_sensitive_files(), check_unattended_upgrades(), check_kernel_hardening()]
    critical = [c for c in checks if c["severity"] >= 8]
    warnings = [c for c in checks if 4 <= c["severity"] < 8]
    passed = [c for c in checks if c["severity"] < 4]
    score = round(10 - (sum(c["severity"] for c in checks) / len(checks)), 1)
    report = {
        "timestamp": datetime.now(UTC).isoformat(), "security_score": max(0, score),
        "total_checks": len(checks), "critical": len(critical), "warnings": len(warnings),
        "passed": len(passed), "critical_findings": critical, "warning_findings": warnings,
        "passed_checks": [c["check"] for c in passed], "all_checks": checks,
    }
    _log("full_vuln_scan", {"score": report["security_score"], "critical": len(critical), "warnings": len(warnings)})
    return report


if __name__ == "__main__":
    print(json.dumps(full_scan(), indent=2, default=str))
