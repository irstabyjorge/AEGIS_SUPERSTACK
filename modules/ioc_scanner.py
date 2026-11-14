#!/usr/bin/env python3
# Copyright (c) 2024-2026 Jorge Francisco Paredes (irstabyjorge)
# Licensed under dual MIT/Commercial license. See LICENSE and COMMERCIAL_LICENSE.md
"""Read-only IOC checks. Process and file inspection only; no automatic remediation."""

import json
import os
import subprocess
import re
import stat
from datetime import datetime, UTC
from pathlib import Path

import psutil

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
    "/var/spool/cron/crontabs/", "/etc/systemd/system/",
    "/etc/init.d/", "/etc/rc.local", "/etc/profile.d/", "/etc/ld.so.preload",
]


def _run(args, timeout=10):
    """Execute only an explicit argv vector; shell metacharacters are never parsed."""
    if not isinstance(args, (list, tuple)) or not args or not all(isinstance(x, str) for x in args):
        return ""
    try:
        result = subprocess.run(list(args), shell=False, text=True, capture_output=True, timeout=timeout, check=False)
        return result.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def _log(event, payload):
    with open(LOGS / "ioc_scan.jsonl", "a") as f:
        f.write(json.dumps({"time": datetime.now(UTC).isoformat(), "event": event, "payload": payload}, default=str) + "\n")


def check_suspicious_processes():
    findings = []
    for proc in psutil.process_iter(["pid", "username", "name", "cmdline", "cpu_percent", "memory_percent"]):
        try:
            info = proc.info
            cmd_parts = info.get("cmdline") or []
            cmd = " ".join(str(part) for part in cmd_parts)
            name = (info.get("name") or (cmd_parts[0] if cmd_parts else "")).split("/")[-1].lower()
            cpu = float(info.get("cpu_percent") or 0)
            mem = float(info.get("memory_percent") or 0)
            reasons = []
            if name in SUSPICIOUS_PROCESS_NAMES:
                reasons.append("known_malicious_name")
            if any(path in cmd for path in SUSPICIOUS_PATHS):
                reasons.append("suspicious_path")
            if cpu > 90:
                reasons.append("high_cpu")
                if any(term in cmd.lower() for term in ("miner", "xmr", "stratum", "pool")):
                    reasons.append("crypto_mining_indicators")
            if re.search(r'(bash|sh|python|perl|ruby)\s+-[a-z]*c\s+.*base64', cmd, re.IGNORECASE):
                reasons.append("encoded_command_execution")
            if re.search(r'(nc|ncat|socat)\s+.*-[el]', cmd):
                reasons.append("reverse_shell_pattern")
            if reasons:
                findings.append({"pid": info.get("pid"), "user": info.get("username"), "cpu": cpu, "mem": mem, "command": cmd[:300], "reasons": reasons})
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess, OSError, ValueError):
            continue
    return {"check": "suspicious_processes", "severity": 9 if findings else 1, "findings": findings, "total_flagged": len(findings)}


def _cron_lines():
    lines = []
    current = _run(["crontab", "-l"])
    if current:
        lines.extend(current.splitlines())
    paths = [Path("/etc/cron.d"), Path("/var/spool/cron/crontabs")]
    for directory in paths:
        try:
            for entry in directory.iterdir():
                if entry.is_file():
                    try:
                        lines.extend(entry.read_text(errors="replace").splitlines())
                    except (PermissionError, OSError):
                        continue
        except (PermissionError, OSError):
            continue
    return lines


def check_persistence_mechanisms():
    findings = []
    for line in _cron_lines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        lower = line.lower()
        if any(token in lower for token in ("/tmp/", "/dev/shm/", "curl ", "wget ", "base64", "python -c", "bash -i", "nc ", "|sh", "|bash")):
            findings.append({"type": "cron", "content": line[:200], "severity": 8})

    now = datetime.now(UTC)
    for location in PERSISTENCE_LOCATIONS:
        path = Path(location)
        try:
            entries = [path] if path.is_file() else list(path.iterdir()) if path.is_dir() else []
            for entry in entries:
                try:
                    age_days = (now - datetime.fromtimestamp(entry.stat().st_mtime, UTC)).days
                    if age_days < (7 if entry.is_file() else 3):
                        findings.append({"type": "recently_modified_persistence" if entry.is_file() else "new_persistence_entry", "path": str(entry), "modified_days_ago": age_days, "severity": 7})
                except (PermissionError, OSError):
                    continue
        except (PermissionError, OSError):
            continue

    preload = Path("/etc/ld.so.preload")
    try:
        content = preload.read_text().strip() if preload.exists() else ""
        if content:
            findings.append({"type": "ld_preload_hijack", "content": content[:200], "severity": 10})
    except (PermissionError, OSError):
        pass

    return {"check": "persistence_mechanisms", "severity": max((f["severity"] for f in findings), default=1), "findings": findings, "total_flagged": len(findings)}


def check_ssh_keys():
    findings = []
    paths = []
    try:
        homes = Path("/home").iterdir()
        for home in homes:
            candidate = home / ".ssh" / "authorized_keys"
            if candidate.exists():
                paths.append(candidate)
    except (PermissionError, OSError):
        pass
    root_keys = Path("/root/.ssh/authorized_keys")
    if root_keys.exists():
        paths.append(root_keys)

    for key_path in paths:
        try:
            content = key_path.read_text()
            keys = [line.strip() for line in content.splitlines() if line.strip() and not line.startswith("#")]
            age_days = (datetime.now(UTC) - datetime.fromtimestamp(key_path.stat().st_mtime, UTC)).days
            for key in keys:
                parts = key.split()
                key_type = parts[0] if parts else "unknown"
                comment = parts[-1] if len(parts) >= 3 else "no_comment"
                if age_days < 7 or comment in ("", "no_comment") or "@" not in comment:
                    findings.append({"file": str(key_path), "key_type": key_type, "comment": comment[:100], "modified_days_ago": age_days, "severity": 8 if age_days < 2 else 5})
        except (PermissionError, OSError):
            continue
    return {"check": "ssh_authorized_keys", "severity": max((f["severity"] for f in findings), default=1), "findings": findings, "total_keys_checked": len(findings)}


def check_hidden_files():
    findings = []
    for directory in (Path("/tmp"), Path("/var/tmp"), Path("/dev/shm"), Path("/run/lock")):
        try:
            for item in directory.iterdir():
                if item.name.startswith(".") and item.name not in (".", "..", ".X11-unix", ".ICE-unix", ".font-unix", ".XIM-unix"):
                    try:
                        st = item.stat()
                        findings.append({"path": str(item), "type": "directory" if item.is_dir() else "file", "size": st.st_size if item.is_file() else None, "owner_uid": st.st_uid, "executable": bool(st.st_mode & stat.S_IXUSR) if item.is_file() else False, "modified": datetime.fromtimestamp(st.st_mtime, UTC).isoformat(), "severity": 8 if item.is_file() and st.st_mode & stat.S_IXUSR else 6})
                    except (PermissionError, OSError):
                        continue
        except (PermissionError, OSError):
            continue
    return {"check": "hidden_files_in_temp", "severity": max((f["severity"] for f in findings), default=1), "findings": findings, "total_found": len(findings)}


def check_network_iocs():
    findings = []
    hosts = Path("/etc/hosts")
    try:
        suspicious = []
        for line in hosts.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                parts = line.split()
                if len(parts) >= 2 and parts[0] not in ("127.0.0.1", "::1", "127.0.1.1", "255.255.255.255", "ff02::1", "ff02::2"):
                    suspicious.append(line)
        if suspicious:
            findings.append({"type": "hosts_file_modification", "entries": suspicious[:20], "severity": 7})
    except (PermissionError, OSError):
        pass

    resolv = Path("/etc/resolv.conf")
    try:
        safe_dns = {"8.8.8.8", "8.8.4.4", "1.1.1.1", "1.0.0.1", "9.9.9.9", "208.67.222.222", "208.67.220.220", "127.0.0.53"}
        for line in resolv.read_text().splitlines():
            parts = line.split()
            if len(parts) >= 2 and parts[0] == "nameserver":
                server = parts[1]
                if server not in safe_dns and not server.startswith(("192.168.", "10.")):
                    findings.append({"type": "unknown_dns_server", "nameserver": server, "severity": 6})
    except (PermissionError, OSError):
        pass

    output = _run(["sudo", "-n", "iptables", "-L", "-n"])
    redirections = [line for line in output.splitlines() if any(term in line.lower() for term in ("dnat", "redirect", "masquerade"))]
    if redirections:
        findings.append({"type": "iptables_redirection", "rules": "\n".join(redirections)[:500], "severity": 7})
    return {"check": "network_iocs", "severity": max((f.get("severity", 1) for f in findings), default=1), "findings": findings}


def check_shell_history():
    findings = []
    history_files = []
    try:
        for home in Path("/home").iterdir():
            for filename in (".bash_history", ".zsh_history", ".sh_history"):
                candidate = home / filename
                if candidate.exists():
                    history_files.append(candidate)
    except (PermissionError, OSError):
        pass
    for filename in (".bash_history", ".zsh_history"):
        candidate = Path("/root") / filename
        if candidate.exists():
            history_files.append(candidate)

    patterns = [
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
    for history in history_files:
        try:
            lines = history.read_text(errors="replace").splitlines()
            offset = max(0, len(lines) - 500)
            for index, line in enumerate(lines[offset:]):
                for pattern, tag in patterns:
                    if pattern.search(line):
                        findings.append({"file": str(history), "line_number": offset + index + 1, "command": line.strip()[:200], "tag": tag, "severity": 8})
                        break
        except (PermissionError, OSError):
            continue
    return {"check": "shell_history_analysis", "severity": max((f["severity"] for f in findings), default=1), "findings": findings[:50], "total_suspicious": len(findings)}


def full_scan():
    checks = [check_suspicious_processes(), check_persistence_mechanisms(), check_ssh_keys(), check_hidden_files(), check_network_iocs(), check_shell_history()]
    critical = [c for c in checks if c["severity"] >= 8]
    warnings = [c for c in checks if 4 <= c["severity"] < 8]
    clean = [c for c in checks if c["severity"] < 4]
    total = sum(c.get("total_flagged", c.get("total_found", c.get("total_suspicious", len(c.get("findings", []))))) for c in checks)
    report = {
        "timestamp": datetime.now(UTC).isoformat(), "scan_type": "ioc_full_scan",
        "total_checks": len(checks), "total_findings": total, "critical": len(critical),
        "warnings": len(warnings), "clean": len(clean),
        "compromise_likelihood": "HIGH" if critical else "MEDIUM" if warnings else "LOW",
        "critical_findings": critical, "warning_findings": warnings,
        "clean_checks": [c["check"] for c in clean], "all_checks": checks,
    }
    _log("ioc_full_scan", {"total_findings": total, "critical": len(critical), "likelihood": report["compromise_likelihood"]})
    return report


if __name__ == "__main__":
    print(json.dumps(full_scan(), indent=2, default=str))
