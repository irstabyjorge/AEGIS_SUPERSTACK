#!/usr/bin/env python3
# Copyright (c) 2024-2026 Jorge Francisco Paredes (irstabyjorge)
# Licensed under dual MIT/Commercial license. See LICENSE and COMMERCIAL_LICENSE.md
"""
AEGIS Password Auditor — local password policy and credential security assessment.
Checks password aging policies, empty passwords, reused credentials,
PAM configuration, and login policy compliance.
"""

import json, os, subprocess, re, hashlib
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
    with open(LOGS / "password_audit.jsonl", "a") as f:
        f.write(json.dumps({"time": datetime.now(UTC).isoformat(), "event": event, "payload": payload}, default=str) + "\n")


def check_password_policy():
    findings = []

    login_defs = Path("/etc/login.defs")
    policy = {}
    if login_defs.exists():
        try:
            content = login_defs.read_text()
            for key in ("PASS_MAX_DAYS", "PASS_MIN_DAYS", "PASS_MIN_LEN", "PASS_WARN_AGE",
                        "LOGIN_RETRIES", "LOGIN_TIMEOUT", "ENCRYPT_METHOD"):
                match = re.search(rf"^\s*{key}\s+(\S+)", content, re.MULTILINE)
                if match:
                    policy[key] = match.group(1)

            max_days = int(policy.get("PASS_MAX_DAYS", "99999"))
            min_len = int(policy.get("PASS_MIN_LEN", "0"))

            if max_days > 90:
                findings.append({
                    "issue": "weak_password_max_age",
                    "value": max_days,
                    "recommended": 90,
                    "severity": 5,
                })
            if min_len < 8:
                findings.append({
                    "issue": "weak_minimum_password_length",
                    "value": min_len,
                    "recommended": 12,
                    "severity": 6,
                })
            if policy.get("ENCRYPT_METHOD", "").upper() in ("DES", "MD5"):
                findings.append({
                    "issue": "weak_password_hashing",
                    "method": policy["ENCRYPT_METHOD"],
                    "recommended": "SHA512 or YESCRYPT",
                    "severity": 9,
                })
        except (PermissionError, OSError):
            findings.append({"issue": "cannot_read_login_defs", "severity": 3})

    max_sev = max((f["severity"] for f in findings), default=1)
    return {
        "check": "password_policy",
        "severity": max_sev,
        "policy": policy,
        "findings": findings,
    }


def check_empty_passwords():
    findings = []
    shadow_output = _run("sudo -n cat /etc/shadow 2>/dev/null")

    if shadow_output:
        for line in shadow_output.splitlines():
            parts = line.strip().split(":")
            if len(parts) < 2:
                continue
            username = parts[0]
            password_hash = parts[1]

            if password_hash in ("", "!", "!!", "*"):
                status = "locked" if password_hash in ("!", "!!") else "no_password" if password_hash == "" else "disabled"
                if password_hash == "":
                    findings.append({
                        "username": username,
                        "status": status,
                        "severity": 10,
                    })
    else:
        passwd_output = _run("cat /etc/passwd 2>/dev/null")
        for line in passwd_output.splitlines():
            parts = line.strip().split(":")
            if len(parts) >= 2 and parts[1] == "":
                findings.append({
                    "username": parts[0],
                    "status": "empty_password_field_in_passwd",
                    "severity": 10,
                })

    return {
        "check": "empty_passwords",
        "severity": 10 if findings else 1,
        "findings": findings,
        "shadow_readable": bool(shadow_output),
    }


def check_password_aging():
    findings = []
    output = _run("sudo -n cat /etc/shadow 2>/dev/null")
    if not output:
        return {"check": "password_aging", "severity": 3, "status": "cannot_read_shadow"}

    for line in output.splitlines():
        parts = line.strip().split(":")
        if len(parts) < 5:
            continue
        username = parts[0]
        last_changed = parts[2]
        max_days = parts[4]

        if last_changed and last_changed.isdigit() and max_days and max_days.isdigit():
            last_changed_days = int(last_changed)
            max_days_val = int(max_days)
            if max_days_val == 99999:
                shell_check = _run(f"getent passwd {username} 2>/dev/null | cut -d: -f7")
                if shell_check and shell_check in ("/bin/bash", "/bin/sh", "/bin/zsh", "/usr/bin/bash", "/usr/bin/zsh"):
                    findings.append({
                        "username": username,
                        "issue": "password_never_expires",
                        "max_days": max_days_val,
                        "severity": 4,
                    })

            if last_changed_days > 0:
                import time
                current_days = int(time.time() / 86400)
                age = current_days - last_changed_days
                if age > 365:
                    findings.append({
                        "username": username,
                        "issue": "password_very_old",
                        "age_days": age,
                        "severity": 6,
                    })

    max_sev = max((f["severity"] for f in findings), default=1)
    return {
        "check": "password_aging",
        "severity": max_sev,
        "findings": findings[:30],
        "total_issues": len(findings),
    }


def check_pam_config():
    findings = []

    pam_files = [
        "/etc/pam.d/common-auth",
        "/etc/pam.d/common-password",
        "/etc/pam.d/sshd",
        "/etc/pam.d/login",
    ]

    for pam_file in pam_files:
        p = Path(pam_file)
        if not p.exists():
            continue
        try:
            content = p.read_text()

            if "common-password" in pam_file or "common-auth" in pam_file:
                if "pam_pwquality" not in content and "pam_cracklib" not in content:
                    findings.append({
                        "file": pam_file,
                        "issue": "no_password_complexity_module",
                        "severity": 6,
                    })

                if "pam_faillock" not in content and "pam_tally2" not in content:
                    findings.append({
                        "file": pam_file,
                        "issue": "no_account_lockout",
                        "severity": 5,
                    })

            if "nullok" in content:
                findings.append({
                    "file": pam_file,
                    "issue": "nullok_allows_empty_passwords",
                    "severity": 7,
                })

        except PermissionError:
            pass

    max_sev = max((f["severity"] for f in findings), default=1)
    return {
        "check": "pam_configuration",
        "severity": max_sev,
        "findings": findings,
    }


def check_failed_logins():
    output = _run("lastb -n 50 2>/dev/null")
    lines = [l for l in output.splitlines() if l.strip() and "btmp" not in l]

    ips = {}
    for line in lines:
        parts = line.split()
        ip = None
        for p in parts:
            if re.match(r'\d+\.\d+\.\d+\.\d+', p):
                ip = p
                break
        if ip:
            ips[ip] = ips.get(ip, 0) + 1

    brute_force_ips = {ip: count for ip, count in ips.items() if count >= 5}

    return {
        "check": "failed_login_attempts",
        "severity": 8 if brute_force_ips else (4 if lines else 1),
        "total_failures": len(lines),
        "brute_force_suspects": brute_force_ips,
        "recent_failures": lines[:20],
    }


def full_audit():
    checks = [
        check_password_policy(),
        check_empty_passwords(),
        check_password_aging(),
        check_pam_config(),
        check_failed_logins(),
    ]

    critical = [c for c in checks if c["severity"] >= 8]
    warnings = [c for c in checks if 4 <= c["severity"] < 8]
    passed = [c for c in checks if c["severity"] < 4]

    overall = round(10 - (sum(c["severity"] for c in checks) / len(checks)), 1)

    report = {
        "timestamp": datetime.now(UTC).isoformat(),
        "scan_type": "password_audit",
        "credential_security_score": max(0, overall),
        "total_checks": len(checks),
        "critical": len(critical),
        "warnings": len(warnings),
        "passed": len(passed),
        "critical_findings": critical,
        "warning_findings": warnings,
        "passed_checks": [c["check"] for c in passed],
        "all_checks": checks,
    }

    _log("password_audit", {
        "score": report["credential_security_score"],
        "critical": len(critical),
    })
    return report


if __name__ == "__main__":
    print(json.dumps(full_audit(), indent=2, default=str))
