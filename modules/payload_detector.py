#!/usr/bin/env python3
# Copyright (c) 2024-2026 Jorge Francisco Paredes (irstabyjorge)
# Licensed under dual MIT/Commercial license. See LICENSE and COMMERCIAL_LICENSE.md
"""
AEGIS Payload Detector — web attack payload and exploit signature detection.
Scans web server logs, application logs, and files for known attack patterns
including SQL injection, XSS, command injection, path traversal, and
web shell signatures. Inspired by SecLists and PayloadsAllTheThings.
"""

import json, re, os
from datetime import datetime, UTC
from pathlib import Path
from collections import Counter

LOGS = Path.home() / "aegis_omni_xeon" / "logs"
LOGS.mkdir(parents=True, exist_ok=True)

ATTACK_SIGNATURES = {
    "sql_injection": [
        re.compile(r"(?:UNION\s+(?:ALL\s+)?SELECT|SELECT\s+.*FROM\s+information_schema)", re.IGNORECASE),
        re.compile(r"(?:OR|AND)\s+['\"]?\d+['\"]?\s*=\s*['\"]?\d+", re.IGNORECASE),
        re.compile(r"(?:DROP|ALTER|DELETE|INSERT|UPDATE)\s+(?:TABLE|DATABASE|INTO)", re.IGNORECASE),
        re.compile(r"(?:SLEEP|BENCHMARK|WAITFOR\s+DELAY|pg_sleep)\s*\(", re.IGNORECASE),
        re.compile(r"(?:LOAD_FILE|INTO\s+(?:OUT|DUMP)FILE|UTL_HTTP)", re.IGNORECASE),
        re.compile(r"(?:0x[0-9a-f]{8,}|CHAR\s*\(\s*\d+(?:\s*,\s*\d+)*\s*\))", re.IGNORECASE),
        re.compile(r"(?:CONCAT|GROUP_CONCAT|CONCAT_WS)\s*\(.*(?:SELECT|0x)", re.IGNORECASE),
    ],
    "xss": [
        re.compile(r"<script[^>]*>", re.IGNORECASE),
        re.compile(r"(?:javascript|vbscript|data)\s*:", re.IGNORECASE),
        re.compile(r"on(?:error|load|click|mouseover|focus|blur|submit)\s*=", re.IGNORECASE),
        re.compile(r"(?:document\.cookie|document\.location|window\.location)", re.IGNORECASE),
        re.compile(r"(?:eval|setTimeout|setInterval|Function)\s*\(", re.IGNORECASE),
        re.compile(r"<(?:img|svg|iframe|object|embed|video|audio)[^>]*(?:src|href)\s*=\s*['\"]?(?:javascript|data):", re.IGNORECASE),
    ],
    "command_injection": [
        re.compile(r"(?:;|\||`|\$\()\s*(?:cat|ls|id|whoami|uname|pwd|wget|curl|nc|bash|sh|python|perl|ruby)", re.IGNORECASE),
        re.compile(r"(?:/etc/passwd|/etc/shadow|/proc/self|/dev/tcp)", re.IGNORECASE),
        re.compile(r"(?:&&|\|\|)\s*(?:wget|curl|nc|bash|sh|python|perl|ruby|php)", re.IGNORECASE),
        re.compile(r"\$\{(?:IFS|PATH|HOME|SHELL)\}", re.IGNORECASE),
    ],
    "path_traversal": [
        re.compile(r"(?:\.\./|\.\.\\){2,}"),
        re.compile(r"(?:%2e%2e%2f|%2e%2e/|\.%2e/|%2e\./)"),
        re.compile(r"(?:/etc/passwd|/etc/shadow|/windows/system32|boot\.ini)", re.IGNORECASE),
        re.compile(r"(?:file://|php://|data://|expect://|zip://)", re.IGNORECASE),
    ],
    "web_shell": [
        re.compile(r"(?:eval|assert|system|exec|passthru|shell_exec|popen)\s*\(\s*(?:\$_(?:GET|POST|REQUEST|COOKIE)|base64_decode)", re.IGNORECASE),
        re.compile(r"(?:c99|r57|b374k|wso|alfa|FilesMan|AnonymousFox)", re.IGNORECASE),
        re.compile(r"(?:preg_replace\s*\(.*['\"/]e['\"]|create_function|call_user_func)", re.IGNORECASE),
        re.compile(r"(?:cmd|command|exec|execute|run|shell)\s*=", re.IGNORECASE),
    ],
    "xxe": [
        re.compile(r"<!(?:DOCTYPE|ENTITY)\s+\S+\s+SYSTEM", re.IGNORECASE),
        re.compile(r"<!ENTITY\s+\S+\s+(?:SYSTEM|PUBLIC)", re.IGNORECASE),
        re.compile(r"(?:file://|expect://|php://)", re.IGNORECASE),
    ],
    "ssrf": [
        re.compile(r"(?:127\.0\.0\.1|localhost|0\.0\.0\.0|::1|0x7f)", re.IGNORECASE),
        re.compile(r"(?:169\.254\.169\.254|metadata\.google|metadata\.azure)", re.IGNORECASE),
        re.compile(r"(?:http://|https://)\s*(?:127\.|10\.|172\.(?:1[6-9]|2\d|3[01])\.|192\.168\.)", re.IGNORECASE),
    ],
    "log4shell": [
        re.compile(r"\$\{jndi:(?:ldap|rmi|dns|iiop)s?://", re.IGNORECASE),
        re.compile(r"\$\{(?:lower|upper|env|sys|java):.*\}", re.IGNORECASE),
    ],
}

SEVERITY_MAP = {
    "sql_injection": 9,
    "xss": 7,
    "command_injection": 10,
    "path_traversal": 8,
    "web_shell": 10,
    "xxe": 8,
    "ssrf": 8,
    "log4shell": 10,
}


def _log(event, payload):
    with open(LOGS / "payload_detection.jsonl", "a") as f:
        f.write(json.dumps({"time": datetime.now(UTC).isoformat(), "event": event, "payload": payload}, default=str) + "\n")


def scan_file(filepath, max_lines=10000):
    findings = []
    ip_counter = Counter()
    category_counter = Counter()

    try:
        with open(filepath, errors="replace") as f:
            for i, line in enumerate(f):
                if i >= max_lines:
                    break
                line = line.strip()
                for category, patterns in ATTACK_SIGNATURES.items():
                    for pattern in patterns:
                        match = pattern.search(line)
                        if match:
                            ip_match = re.search(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', line)
                            ip = ip_match.group(1) if ip_match else None
                            if ip:
                                ip_counter[ip] += 1
                            category_counter[category] += 1
                            findings.append({
                                "line_number": i + 1,
                                "category": category,
                                "severity": SEVERITY_MAP.get(category, 5),
                                "matched": match.group(0)[:100],
                                "ip": ip,
                                "excerpt": line[:300],
                            })
                            break
    except (PermissionError, FileNotFoundError) as e:
        return {"error": str(e), "file": str(filepath)}

    return {
        "file": str(filepath),
        "lines_scanned": min(i + 1 if 'i' in dir() else 0, max_lines),
        "total_detections": len(findings),
        "by_category": dict(category_counter.most_common()),
        "top_attacking_ips": [{"ip": ip, "hits": c} for ip, c in ip_counter.most_common(20)],
        "critical_detections": [f for f in findings if f["severity"] >= 9][:30],
        "recent_detections": findings[-20:],
    }


def scan_web_logs():
    log_paths = [
        "/var/log/apache2/access.log",
        "/var/log/apache2/error.log",
        "/var/log/nginx/access.log",
        "/var/log/nginx/error.log",
        "/var/log/httpd/access_log",
        "/var/log/httpd/error_log",
    ]

    results = []
    for lp in log_paths:
        if Path(lp).exists():
            results.append(scan_file(lp))

    total_detections = 0
    all_categories = Counter()
    all_ips = Counter()

    for r in results:
        if "error" not in r:
            total_detections += r["total_detections"]
            all_categories.update(r.get("by_category", {}))
            for ip_info in r.get("top_attacking_ips", []):
                all_ips[ip_info["ip"]] += ip_info["hits"]

    report = {
        "timestamp": datetime.now(UTC).isoformat(),
        "scan_type": "web_log_payload_scan",
        "files_scanned": len(results),
        "total_detections": total_detections,
        "attack_categories": dict(all_categories.most_common()),
        "top_attackers": [{"ip": ip, "total_hits": c} for ip, c in all_ips.most_common(15)],
        "severity": 9 if total_detections > 0 else 1,
        "file_reports": results,
    }

    _log("web_log_scan", {
        "files": len(results),
        "detections": total_detections,
        "categories": dict(all_categories),
    })
    return report


def scan_directory(directory, extensions=None):
    extensions = extensions or {".php", ".py", ".js", ".sh", ".pl", ".rb", ".jsp", ".asp", ".aspx"}
    findings = []
    files_scanned = 0

    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if d not in (".git", "node_modules", "__pycache__", ".venv", "venv")]
        for fname in files:
            if Path(fname).suffix.lower() in extensions:
                fpath = os.path.join(root, fname)
                try:
                    result = scan_file(fpath, max_lines=2000)
                    files_scanned += 1
                    if result.get("total_detections", 0) > 0:
                        findings.append(result)
                except Exception:
                    pass

    return {
        "timestamp": datetime.now(UTC).isoformat(),
        "scan_type": "directory_payload_scan",
        "directory": directory,
        "files_scanned": files_scanned,
        "files_with_detections": len(findings),
        "findings": findings,
    }


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "web":
        print(json.dumps(scan_web_logs(), indent=2, default=str))
    elif len(sys.argv) > 2 and sys.argv[1] == "scan":
        print(json.dumps(scan_file(sys.argv[2]), indent=2, default=str))
    elif len(sys.argv) > 2 and sys.argv[1] == "dir":
        print(json.dumps(scan_directory(sys.argv[2]), indent=2, default=str))
    else:
        print(json.dumps(scan_web_logs(), indent=2, default=str))
