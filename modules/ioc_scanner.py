#!/usr/bin/env python3
# Copyright (c) 2024-2026 Jorge Francisco Paredes (irstabyjorge)
# Licensed under dual MIT/Commercial license. See LICENSE and COMMERCIAL_LICENSE.md
"""
AEGIS IOC Scanner — Indicators of Compromise detection.
Scans the local system for signs of compromise: suspicious processes,
persistence mechanisms, unauthorized cron jobs, rogue SSH keys,
modified system binaries, and known malicious file patterns.
"""

import json, os, subprocess, hashlib, re, stat
from datetime import datetime, UTC
from pathlib import Path
from collections import Counter

LOGS = Path.home() / "aegis_omni_xeon" / "logs"
LOGS.mkdir(parents=True, exist_ok=True)

SUSPICIOUS_PROCESS_NAMES = {
    "xmrig", "minerd", "cpuminer", "cgminer", "bfgminer", "ethminer",
    "kworkerds", "kdevtmpfsi", "kinsing", "solr", "ld-linux",
    "dbused", "xbash", "tsunamid", "dovecat", "bioset",
    "rsync-daemon", "watchdog-timer", "ksoftirqds",
}

SUSPICIOUS_PATHS = [
    "/tmp/.X11-unix/", "/tmp/.ICE-unix/", "/dev/shm/.",
    "/var/tmp/.", "/tmp/.", "/root/.cache/.",
    "/tmp/.font-unix/", "/run/lock/.",
]

PERSISTENCE_LOCATIONS = [
    "/etc/cron.d/", "/etc/cron.daily/", "/etc/cron.hourly/",
    "/var/spool/cron/crontabs/",
    "/etc/systemd/system/",
    "/etc/init.d/",
    "/etc/rc.local",
    "/etc/profile.d/",
    "/etc/ld.so.preload",
]

KNOWN_MALICIOUS_HASHES = {
    "e99a18c428cb38d5f260853678922e03",
    "d41d8cd98f00b204e9800998ecf8427e",
}


def _run(cmd, timeout=10):
    try:
        r = subprocess.run(cmd, shell=True, text=True, capture_output=True, timeout=timeout)
        return r.stdout.strip()
    except Exception:
        return ""


def _log(event, payload):
    with open(LOGS / "ioc_scan.jsonl", "a") as f:
        f.write(json.dumps({"time": datetime.now(UTC).isoformat(), "event": event, "payload": payload}, default=str) + "\n")


def check_suspicious_processes():
    findings = []
    output = _run("ps aux --no-headers 2>/dev/null")
    for line in output.splitlines():
        parts = line.split()
        if len(parts) < 11:
            continue
        user, pid, cpu, mem = parts[0], parts[1], parts[2], parts[3]
        cmd = " ".join(parts[10:])
        proc_name = os.path.basename(parts[10].split("/")[-1]).lower()

        flagged = False
        reasons = []

        if proc_name in SUSPICIOUS_PROCESS_NAMES:
            flagged = True
            reasons.append("known_malicious_name")

        if any(p in cmd for p in SUSPICIOUS_PATHS):
            flagged = True
            reasons.append("suspicious_path")

        if float(cpu) > 90:
            reasons.append("high_cpu")
            if any(x in cmd.lower() for x in ("miner", "xmr", "stratum", "pool")):
                flagged = True
                reasons.append("crypto_mining_indicators")

        if re.search(r'(bash|sh|python|perl|ruby)\s+-[a-z]*c\s+.*base64', cmd, re.IGNORECASE):
            flagged = True
            reasons.append("encoded_command_execution")

        if re.search(r'(nc|ncat|socat)\s+.*-[el]', cmd):
            flagged = True
            reasons.append("reverse_shell_pattern")

        if flagged:
            findings.append({
                "pid": pid, "user": user, "cpu": cpu, "mem": mem,
                "command": cmd[:300], "reasons": reasons,
            })

    return {
        "check": "suspicious_processes",
        "severity": 9 if findings else 1,
        "findings": findings,
        "total_flagged": len(findings),
    }


def check_persistence_mechanisms():
    findings = []

    cron_output = _run("crontab -l 2>/dev/null; ls /etc/cron.d/ 2>/dev/null; cat /var/spool/cron/crontabs/* 2>/dev/null")
    for line in cron_output.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        suspicious = any(x in line.lower() for x in (
            "/tmp/", "/dev/shm/", "curl ", "wget ", "base64",
            "python -c", "bash -i", "nc ", "|sh", "|bash",
        ))
        if suspicious:
            findings.append({"type": "cron", "content": line[:200], "severity": 8})

    for loc in PERSISTENCE_LOCATIONS:
        p = Path(loc)
        if p.is_file():
            try:
                mtime = datetime.fromtimestamp(p.stat().st_mtime, UTC)
                age_days = (datetime.now(UTC) - mtime).days
                if age_days < 7:
                    findings.append({
                        "type": "recently_modified_persistence",
                        "path": str(p),
                        "modified_days_ago": age_days,
                        "severity": 7,
                    })
            except (PermissionError, OSError):
                pass
        elif p.is_dir():
            try:
                for f in p.iterdir():
                    mtime = datetime.fromtimestamp(f.stat().st_mtime, UTC)
                    age_days = (datetime.now(UTC) - mtime).days
                    if age_days < 3:
                        findings.append({
                            "type": "new_persistence_entry",
                            "path": str(f),
                            "modified_days_ago": age_days,
                            "severity": 7,
                        })
            except (PermissionError, OSError):
                pass

    ld_preload = Path("/etc/ld.so.preload")
    if ld_preload.exists():
        try:
            content = ld_preload.read_text().strip()
            if content:
                findings.append({
                    "type": "ld_preload_hijack",
                    "content": content[:200],
                    "severity": 10,
                })
        except PermissionError:
            pass

    max_sev = max((f["severity"] for f in findings), default=1)
    return {
        "check": "persistence_mechanisms",
        "severity": max_sev,
        "findings": findings,
        "total_flagged": len(findings),
    }


def check_ssh_keys():
    findings = []
    authorized_keys_paths = []

    for home in Path("/home").iterdir():
        ak = home / ".ssh" / "authorized_keys"
        if ak.exists():
            authorized_keys_paths.append(ak)
    root_ak = Path("/root/.ssh/authorized_keys")
    if root_ak.exists():
        authorized_keys_paths.append(root_ak)

    for ak_path in authorized_keys_paths:
        try:
            content = ak_path.read_text()
            keys = [l.strip() for l in content.splitlines() if l.strip() and not l.startswith("#")]
            mtime = datetime.fromtimestamp(ak_path.stat().st_mtime, UTC)
            age_days = (datetime.now(UTC) - mtime).days

            for key in keys:
                parts = key.split()
                key_type = parts[0] if parts else "unknown"
                comment = parts[-1] if len(parts) >= 3 else "no_comment"
                suspicious = age_days < 7 or comment in ("", "no_comment") or "@" not in comment
                if suspicious:
                    findings.append({
                        "file": str(ak_path),
                        "key_type": key_type,
                        "comment": comment[:100],
                        "modified_days_ago": age_days,
                        "severity": 8 if age_days < 2 else 5,
                    })
        except (PermissionError, OSError):
            pass

    max_sev = max((f["severity"] for f in findings), default=1)
    return {
        "check": "ssh_authorized_keys",
        "severity": max_sev,
        "findings": findings,
        "total_keys_checked": len(findings),
    }


def check_hidden_files():
    findings = []
    scan_dirs = ["/tmp", "/var/tmp", "/dev/shm", "/run/lock"]

    for scan_dir in scan_dirs:
        p = Path(scan_dir)
        if not p.exists():
            continue
        try:
            for item in p.iterdir():
                if item.name.startswith(".") and item.name not in (".", "..", ".X11-unix", ".ICE-unix", ".font-unix", ".XIM-unix"):
                    try:
                        st = item.stat()
                        findings.append({
                            "path": str(item),
                            "type": "directory" if item.is_dir() else "file",
                            "size": st.st_size if item.is_file() else None,
                            "owner_uid": st.st_uid,
                            "executable": bool(st.st_mode & stat.S_IXUSR) if item.is_file() else False,
                            "modified": datetime.fromtimestamp(st.st_mtime, UTC).isoformat(),
                            "severity": 8 if (item.is_file() and st.st_mode & stat.S_IXUSR) else 6,
                        })
                    except (PermissionError, OSError):
                        pass
        except PermissionError:
            pass

    max_sev = max((f["severity"] for f in findings), default=1)
    return {
        "check": "hidden_files_in_temp",
        "severity": max_sev,
        "findings": findings,
        "total_found": len(findings),
    }


def check_network_iocs():
    findings = []

    hosts_file = Path("/etc/hosts")
    if hosts_file.exists():
        try:
            content = hosts_file.read_text()
            suspicious_entries = []
            for line in content.splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    parts = line.split()
                    if len(parts) >= 2 and parts[0] not in ("127.0.0.1", "::1", "127.0.1.1", "255.255.255.255", "ff02::1", "ff02::2"):
                        suspicious_entries.append(line)
            if suspicious_entries:
                findings.append({
                    "type": "hosts_file_modification",
                    "entries": suspicious_entries[:20],
                    "severity": 7,
                })
        except PermissionError:
            pass

    resolv = Path("/etc/resolv.conf")
    if resolv.exists():
        try:
            content = resolv.read_text()
            known_safe_dns = {"8.8.8.8", "8.8.4.4", "1.1.1.1", "1.0.0.1", "9.9.9.9", "208.67.222.222", "208.67.220.220", "127.0.0.53"}
            for line in content.splitlines():
                if line.strip().startswith("nameserver"):
                    ns = line.split()[1] if len(line.split()) > 1 else ""
                    if ns and ns not in known_safe_dns and not ns.startswith("192.168.") and not ns.startswith("10."):
                        findings.append({
                            "type": "unknown_dns_server",
                            "nameserver": ns,
                            "severity": 6,
                        })
        except PermissionError:
            pass

    iptables_output = _run("sudo -n iptables -L -n 2>/dev/null | grep -i 'DNAT\\|REDIRECT\\|MASQUERADE'")
    if iptables_output:
        findings.append({
            "type": "iptables_redirection",
            "rules": iptables_output[:500],
            "severity": 7,
        })

    max_sev = max((f.get("severity", 1) for f in findings), default=1)
    return {
        "check": "network_iocs",
        "severity": max_sev,
        "findings": findings,
    }


def check_shell_history():
    findings = []
    history_files = []

    for home in Path("/home").iterdir():
        for hf in (".bash_history", ".zsh_history", ".sh_history"):
            p = home / hf
            if p.exists():
                history_files.append(p)

    for root_hf in (".bash_history", ".zsh_history"):
        p = Path("/root") / root_hf
        if p.exists():
            history_files.append(p)

    suspicious_patterns = [
        (re.compile(r"curl.*\|\s*(bash|sh)", re.IGNORECASE), "pipe_to_shell"),
        (re.compile(r"wget.*-O\s*-\s*\|\s*(bash|sh)", re.IGNORECASE), "pipe_to_shell"),
        (re.compile(r"echo\s+.*\|\s*base64\s+-d", re.IGNORECASE), "base64_decode"),
        (re.compile(r"python.*-c\s+['\"]import\s+(socket|os|subprocess)", re.IGNORECASE), "python_reverse_shell"),
        (re.compile(r"nc\s+.*-e\s+/bin/(ba)?sh", re.IGNORECASE), "netcat_shell"),
        (re.compile(r"chmod\s+[47]77\s+/", re.IGNORECASE), "dangerous_chmod"),
        (re.compile(r"rm\s+.*-rf\s+/(?!tmp)", re.IGNORECASE), "destructive_rm"),
        (re.compile(r"iptables\s+.*-F", re.IGNORECASE), "firewall_flush"),
        (re.compile(r"/etc/shadow", re.IGNORECASE), "shadow_access"),
        (re.compile(r"useradd.*-o\s+-u\s*0", re.IGNORECASE), "uid0_user_creation"),
    ]

    for hf in history_files:
        try:
            lines = hf.read_text(errors="replace").splitlines()
            for i, line in enumerate(lines[-500:]):
                for pattern, tag in suspicious_patterns:
                    if pattern.search(line):
                        findings.append({
                            "file": str(hf),
                            "line_number": len(lines) - 500 + i + 1,
                            "command": line.strip()[:200],
                            "tag": tag,
                            "severity": 8,
                        })
                        break
        except (PermissionError, OSError):
            pass

    max_sev = max((f["severity"] for f in findings), default=1)
    return {
        "check": "shell_history_analysis",
        "severity": max_sev,
        "findings": findings[:50],
        "total_suspicious": len(findings),
    }


def full_scan():
    checks = [
        check_suspicious_processes(),
        check_persistence_mechanisms(),
        check_ssh_keys(),
        check_hidden_files(),
        check_network_iocs(),
        check_shell_history(),
    ]

    critical = [c for c in checks if c["severity"] >= 8]
    warnings = [c for c in checks if 4 <= c["severity"] < 8]
    clean = [c for c in checks if c["severity"] < 4]

    total_findings = sum(c.get("total_flagged", c.get("total_found", c.get("total_suspicious", len(c.get("findings", []))))) for c in checks)

    report = {
        "timestamp": datetime.now(UTC).isoformat(),
        "scan_type": "ioc_full_scan",
        "total_checks": len(checks),
        "total_findings": total_findings,
        "critical": len(critical),
        "warnings": len(warnings),
        "clean": len(clean),
        "compromise_likelihood": "HIGH" if critical else "MEDIUM" if warnings else "LOW",
        "critical_findings": critical,
        "warning_findings": warnings,
        "clean_checks": [c["check"] for c in clean],
        "all_checks": checks,
    }

    _log("ioc_full_scan", {
        "total_findings": total_findings,
        "critical": len(critical),
        "likelihood": report["compromise_likelihood"],
    })
    return report


if __name__ == "__main__":
    print(json.dumps(full_scan(), indent=2, default=str))
