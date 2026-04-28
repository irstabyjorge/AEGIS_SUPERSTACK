#!/usr/bin/env python3
# Copyright (c) 2024-2026 Jorge Francisco Paredes (irstabyjorge)
# Licensed under dual MIT/Commercial license. See LICENSE and COMMERCIAL_LICENSE.md
"""
AEGIS Log Analyzer — pattern-based security log analysis.
Scans system logs for attack signatures, anomalies, and suspicious patterns.
Produces structured threat reports from raw log data.
"""

import json, re, os
from datetime import datetime, UTC
from pathlib import Path
from collections import Counter

LOGS = Path.home() / "aegis_omni_xeon" / "logs"
LOGS.mkdir(parents=True, exist_ok=True)

ATTACK_PATTERNS = {
    "brute_force": [
        re.compile(r"Failed password for .+ from (\S+)", re.IGNORECASE),
        re.compile(r"authentication failure.*rhost=(\S+)", re.IGNORECASE),
        re.compile(r"pam_unix.*authentication failure", re.IGNORECASE),
    ],
    "privilege_escalation": [
        re.compile(r"sudo:\s+(\S+)\s+:.*COMMAND=", re.IGNORECASE),
        re.compile(r"su\[\d+\].*FAILED", re.IGNORECASE),
        re.compile(r"pkexec.*EXECUTING", re.IGNORECASE),
    ],
    "ssh_scan": [
        re.compile(r"Invalid user \S+ from (\S+)", re.IGNORECASE),
        re.compile(r"Connection closed by (\S+).*\[preauth\]", re.IGNORECASE),
        re.compile(r"Disconnected from (\S+).*\[preauth\]", re.IGNORECASE),
    ],
    "service_manipulation": [
        re.compile(r"systemctl.*(stop|disable|mask)", re.IGNORECASE),
        re.compile(r"service \S+ (stop|restart)", re.IGNORECASE),
    ],
    "suspicious_commands": [
        re.compile(r"COMMAND=.*(wget|curl|nc |ncat|netcat|/tmp/|chmod \+x|bash -i)", re.IGNORECASE),
        re.compile(r"COMMAND=.*(python.*-c|perl.*-e|ruby.*-e)", re.IGNORECASE),
    ],
    "account_changes": [
        re.compile(r"useradd|userdel|usermod|groupadd|passwd", re.IGNORECASE),
        re.compile(r"new user:|delete user:", re.IGNORECASE),
    ],
    "firewall_changes": [
        re.compile(r"ufw.*(allow|deny|delete|disable)", re.IGNORECASE),
        re.compile(r"iptables.*(INSERT|APPEND|DELETE|FLUSH)", re.IGNORECASE),
    ],
}

SEVERITY_MAP = {
    "brute_force": 8,
    "privilege_escalation": 9,
    "ssh_scan": 6,
    "service_manipulation": 7,
    "suspicious_commands": 9,
    "account_changes": 7,
    "firewall_changes": 8,
}


def analyze_file(filepath, max_lines=5000):
    findings = []
    ip_counter = Counter()
    pattern_counter = Counter()

    try:
        with open(filepath) as f:
            for i, line in enumerate(f):
                if i >= max_lines:
                    break
                line = line.strip()
                for category, patterns in ATTACK_PATTERNS.items():
                    for pattern in patterns:
                        match = pattern.search(line)
                        if match:
                            ip = match.group(1) if match.lastindex else None
                            if ip:
                                ip_counter[ip] += 1
                            pattern_counter[category] += 1
                            findings.append({
                                "line_number": i + 1,
                                "category": category,
                                "severity": SEVERITY_MAP.get(category, 5),
                                "ip": ip,
                                "excerpt": line[:200],
                            })
    except (PermissionError, FileNotFoundError) as e:
        return {"error": str(e), "file": str(filepath)}

    top_ips = [{"ip": ip, "count": count, "risk": "HIGH" if count >= 10 else "MEDIUM" if count >= 5 else "LOW"}
               for ip, count in ip_counter.most_common(20)]

    return {
        "file": str(filepath),
        "lines_scanned": min(i + 1 if 'i' in dir() else 0, max_lines),
        "total_findings": len(findings),
        "by_category": dict(pattern_counter.most_common()),
        "top_offending_ips": top_ips,
        "critical_findings": [f for f in findings if f["severity"] >= 8][:50],
        "recent_findings": findings[-20:],
    }


def analyze_system_logs():
    log_files = [
        "/var/log/auth.log",
        "/var/log/syslog",
        "/var/log/kern.log",
        "/var/log/ufw.log",
    ]
    results = []
    for fp in log_files:
        if Path(fp).exists():
            results.append(analyze_file(fp))

    all_ips = Counter()
    all_categories = Counter()
    total_findings = 0

    for r in results:
        if "error" not in r:
            total_findings += r["total_findings"]
            all_categories.update(r.get("by_category", {}))
            for ip_info in r.get("top_offending_ips", []):
                all_ips[ip_info["ip"]] += ip_info["count"]

    summary = {
        "timestamp": datetime.now(UTC).isoformat(),
        "files_analyzed": len(results),
        "total_findings": total_findings,
        "categories": dict(all_categories.most_common()),
        "top_threat_ips": [{"ip": ip, "total_hits": count} for ip, count in all_ips.most_common(10)],
        "file_reports": results,
    }

    with open(LOGS / "log_analysis.jsonl", "a") as f:
        f.write(json.dumps({"time": datetime.now(UTC).isoformat(), "summary": {
            "files": len(results), "findings": total_findings, "top_category": all_categories.most_common(1)
        }}) + "\n")

    return summary


def analyze_aegis_threats():
    threat_log = LOGS / "threat_log.jsonl"
    if not threat_log.exists():
        return {"status": "no_threat_log"}

    actions = Counter()
    levels = Counter()
    ips = Counter()
    signals = Counter()

    try:
        with open(threat_log) as f:
            for line in f:
                entry = json.loads(line.strip())
                actions[entry.get("recommended_action", entry.get("action", "UNKNOWN"))] += 1
                levels[entry.get("threat_level", entry.get("level", "UNKNOWN"))] += 1
                ips[entry.get("ip", "?")] += 1
                for s in entry.get("signals", []):
                    signals[s] += 1
    except (json.JSONDecodeError, OSError):
        return {"status": "parse_error"}

    return {
        "timestamp": datetime.now(UTC).isoformat(),
        "action_distribution": dict(actions.most_common()),
        "threat_levels": dict(levels.most_common()),
        "top_flagged_ips": [{"ip": ip, "count": c} for ip, c in ips.most_common(20)],
        "top_signals": [{"signal": s, "count": c} for s, c in signals.most_common(20)],
        "total_events": sum(actions.values()),
    }


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "threats":
        print(json.dumps(analyze_aegis_threats(), indent=2, default=str))
    else:
        print(json.dumps(analyze_system_logs(), indent=2, default=str))
