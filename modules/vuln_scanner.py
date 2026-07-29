#!/usr/bin/env python3
# Copyright (c) 2024-2026 Jorge Francisco Paredes (irstabyjorge)
# Licensed under dual MIT/Commercial license. See LICENSE and COMMERCIAL_LICENSE.md
"""
AEGIS Vulnerability Scanner — local system security assessment.
Checks for common misconfigurations, weak permissions, outdated packages,
exposed services, and security policy compliance.
"""

import json, os, subprocess, stat
from datetime import datetime, UTC
from pathlib import Path

LOGS = Path.home() / "aegis_omni_xeon" / "logs"
LOGS.mkdir(parents=True, exist_ok=True)


def _run(cmd, timeout=10):
    try:
        r = subprocess.run(cmd, shell=True, text=True, capture_output=True, timeout=timeout)
        return r.stdout.strip()
    except Exception:
        return ""


def _log(event, payload):
    with open(LOGS / "vuln_scan.jsonl", "a") as f:
        f.write(json.dumps({"time": datetime.now(UTC).isoformat(), "event": event, "payload": payload}, default=str) + "\n")


def check_suid_files():
    output = _run("find / -perm -4000 -type f 2>/dev/null | head -50", timeout=30)
    files = [f for f in output.splitlines() if f]
    dangerous = [f for f in files if any(x in f for x in ("/tmp/", "/home/", "/var/tmp/", "/dev/shm/"))]
    return {
        "check": "suid_files",
        "severity": 8 if dangerous else 3,
        "total_suid": len(files),
        "suspicious_locations": dangerous,
        "all_suid": files,
    }


def check_world_writable():
    output = _run("find /etc /usr /var -perm -o+w -type f 2>/dev/null | head -30", timeout=15)
    files = [f for f in output.splitlines() if f]
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

    max_sev = max((f["severity"] for f in findings), default=0)
    return {"check": "ssh_configuration", "severity": max_sev, "findings": findings}


def check_firewall():
    ufw = _run("sudo -n ufw status 2>/dev/null || echo 'no_access'")
    active = "Status: active" in ufw
    return {
        "check": "firewall_status",
        "severity": 8 if not active else 1,
        "active": active,
        "output": ufw[:500],
    }


def check_unattended_upgrades():
    installed = _run("dpkg -l unattended-upgrades 2>/dev/null | grep '^ii'")
    return {
        "check": "auto_updates",
        "severity": 5 if not installed else 1,
        "installed": bool(installed),
    }


def check_open_ports():
    import psutil
    listeners = []
    for c in psutil.net_connections(kind="inet"):
        if c.status == "LISTEN" and c.laddr:
            ip, port = c.laddr.ip, c.laddr.port
            if ip in ("0.0.0.0", "::"):
                proc = None
                try:
                    proc = psutil.Process(c.pid).name() if c.pid else None
                except Exception:
                    pass
                listeners.append({"ip": ip, "port": port, "pid": c.pid, "process": proc})

    high_risk = [l for l in listeners if l["port"] in {21, 23, 25, 3306, 5432, 6379, 27017, 9200}]
    return {
        "check": "exposed_ports",
        "severity": 8 if high_risk else 2,
        "total_listening": len(listeners),
        "exposed_to_all": listeners,
        "high_risk_services": high_risk,
    }


def check_sensitive_files():
    sensitive = [
        "/etc/shadow", "/etc/gshadow", "/root/.ssh/id_rsa",
        "/root/.bash_history", "/root/.mysql_history",
    ]
    readable = []
    for fp in sensitive:
        p = Path(fp)
        if p.exists():
            try:
                st = p.stat()
                if st.st_mode & stat.S_IROTH:
                    readable.append({"file": fp, "mode": oct(st.st_mode)})
            except PermissionError:
                pass

    return {
        "check": "sensitive_file_permissions",
        "severity": 9 if readable else 1,
        "world_readable": readable,
    }


def check_running_as_root():
    return {
        "check": "running_as_root",
        "severity": 3 if os.geteuid() == 0 else 1,
        "is_root": os.geteuid() == 0,
        "uid": os.getuid(),
        "user": os.getenv("USER"),
    }


def check_kernel_hardening():
    checks = {
        "aslr": ("cat /proc/sys/kernel/randomize_va_space", "2"),
        "sysrq_disabled": ("cat /proc/sys/kernel/sysrq", "0"),
        "core_dumps_restricted": ("cat /proc/sys/fs/suid_dumpable", "0"),
        "ptrace_restricted": ("cat /proc/sys/kernel/yama/ptrace_scope", "1"),
    }
    results = {}
    max_sev = 1
    for name, (cmd, expected) in checks.items():
        val = _run(cmd)
        ok = val.strip() == expected
        results[name] = {"value": val, "expected": expected, "compliant": ok}
        if not ok:
            max_sev = max(max_sev, 5)

    return {"check": "kernel_hardening", "severity": max_sev, "settings": results}


def full_scan():
    checks = [
        check_running_as_root(),
        check_ssh_config(),
        check_firewall(),
        check_open_ports(),
        check_suid_files(),
        check_world_writable(),
        check_sensitive_files(),
        check_unattended_upgrades(),
        check_kernel_hardening(),
    ]

    critical = [c for c in checks if c["severity"] >= 8]
    warnings = [c for c in checks if 4 <= c["severity"] < 8]
    passed = [c for c in checks if c["severity"] < 4]
    overall_score = round(10 - (sum(c["severity"] for c in checks) / len(checks)), 1)

    report = {
        "timestamp": datetime.now(UTC).isoformat(),
        "security_score": max(0, overall_score),
        "total_checks": len(checks),
        "critical": len(critical),
        "warnings": len(warnings),
        "passed": len(passed),
        "critical_findings": critical,
        "warning_findings": warnings,
        "passed_checks": [c["check"] for c in passed],
        "all_checks": checks,
    }

    _log("full_vuln_scan", {"score": report["security_score"], "critical": len(critical), "warnings": len(warnings)})
    return report


if __name__ == "__main__":
    print(json.dumps(full_scan(), indent=2, default=str))
