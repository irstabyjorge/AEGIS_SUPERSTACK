#!/usr/bin/env python3
"""Static admission gate for Library-derived AEGIS material.

This tool never imports, executes, installs, compiles, or opens network
connections. It classifies material for knowledge admission, manual review, or
quarantine and records cryptographic hashes for traceability.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

VERSION = "1.0.0"
MAX_SCAN_BYTES = 8 * 1024 * 1024

EXECUTABLE_EXTENSIONS = {
    ".apk", ".appimage", ".com", ".dmg", ".dll", ".exe", ".iso", ".msi",
    ".scr", ".sys",
}
ARCHIVE_EXTENSIONS = {".7z", ".bz2", ".gz", ".rar", ".tar", ".tgz", ".xz", ".zip"}
SOURCE_EXTENSIONS = {
    ".bat", ".bash", ".c", ".cc", ".cmd", ".cpp", ".cxx", ".go", ".h",
    ".hh", ".hpp", ".java", ".js", ".jsx", ".lua", ".php", ".pl", ".ps1",
    ".py", ".pyw", ".rb", ".rs", ".sh", ".sql", ".ts", ".tsx", ".zsh",
}
PASSIVE_EXTENSIONS = {
    ".cfg", ".csv", ".css", ".html", ".ini", ".json", ".jsonl", ".md",
    ".toml", ".txt", ".ubundle", ".yaml", ".yml",
}

RULES = [
    ("destructive-delete", "critical", r"(?i)\b(rm\s+-rf|format(?:\.com)?\b|diskpart\b|Remove-Item\b[^\n]*-Recurse|del\s+/[fsq])"),
    ("credential-access", "critical", r"(?i)(/etc/shadow|sam\\|security\\|credential\s*manager|browser.*password|private[_ -]?key)"),
    ("persistence", "high", r"(?i)(schtasks\b|new-service\b|systemctl\s+enable|crontab\b|runonce|startup\\)"),
    ("privilege-change", "high", r"(?i)(sudo\b|runas\b|setuid|takeown\b|icacls\b|executionpolicy\s+bypass)"),
    ("remote-download", "high", r"(?i)(invoke-webrequest|start-bitstransfer|curl\b|wget\b|downloadstring|urlretrieve)"),
    ("dynamic-execution", "high", r"(?i)(\beval\s*\(|\bexec\s*\(|invoke-expression|\biex\b|powershell\s+-(?:enc|encodedcommand))"),
    ("process-launch", "medium", r"(?i)(subprocess\.|os\.system\s*\(|start-process\b|createprocess|shell_execute|child_process)"),
    ("network-listener", "medium", r"(?i)(listen\s*\(|bind\s*\(|http\.server|threadinghttpserver|net\.createServer)"),
    ("registry-or-firewall", "medium", r"(?i)(reg\s+(?:add|delete)|set-netfirewall|netsh\s+advfirewall)"),
    ("obfuscation", "medium", r"(?i)(frombase64string|base64\.b64decode|certutil\s+-decode|charcodeat)"),
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def scan_one(root: Path, path: Path) -> dict[str, object]:
    relative = path.relative_to(root).as_posix()
    suffix = path.suffix.lower()
    if path.is_symlink():
        return {
            "path": relative,
            "size_bytes": None,
            "sha256": None,
            "extension": suffix,
            "findings": [],
            "decision": "manual-review",
            "reason": "symlink requires manual review; target is not followed",
        }
    size = path.stat().st_size
    result: dict[str, object] = {
        "path": relative,
        "size_bytes": size,
        "sha256": sha256_file(path),
        "extension": suffix,
        "findings": [],
    }
    if suffix in EXECUTABLE_EXTENSIONS:
        result.update(
            decision="quarantine",
            reason="opaque executable/installer; static text review is insufficient",
        )
        return result
    if suffix in ARCHIVE_EXTENSIONS:
        result.update(
            decision="quarantine",
            reason="archive requires separate extraction and recursive review",
        )
        return result
    if suffix not in SOURCE_EXTENSIONS | PASSIVE_EXTENSIONS:
        result.update(decision="metadata-only", reason="unsupported passive file type")
        return result
    if size > MAX_SCAN_BYTES:
        result.update(decision="manual-review", reason="file exceeds static scan limit")
        return result

    text = path.read_text(encoding="utf-8", errors="replace")
    findings = []
    severity_score = {"medium": 1, "high": 3, "critical": 10}
    score = 0
    for rule, severity, pattern in RULES:
        matches = list(re.finditer(pattern, text))
        if matches:
            findings.append(
                {
                    "rule": rule,
                    "severity": severity,
                    "matches": min(len(matches), 999),
                    "lines": sorted(
                        {text.count("\n", 0, match.start()) + 1 for match in matches}
                    )[:20],
                }
            )
            score += severity_score[severity]
    result["findings"] = findings
    result["risk_score"] = score
    if any(item["severity"] == "critical" for item in findings):
        result.update(decision="quarantine", reason="critical static indicator")
    elif suffix in SOURCE_EXTENSIONS or score:
        result.update(
            decision="manual-review",
            reason="executable source or behavior indicator requires human review",
        )
    else:
        result.update(
            decision="admit-knowledge",
            reason="passive text/configuration with no matched behavior indicators",
        )
    return result


def audit(source_root: Path, output: Path) -> dict[str, object]:
    root = source_root.resolve()
    records = []
    excluded = {".git", ".venv", "node_modules", "__pycache__"}
    for path in sorted(root.rglob("*")):
        if path.is_symlink() or not path.is_file():
            continue
        relative_parts = path.relative_to(root).parts
        if any(part in excluded for part in relative_parts):
            continue
        try:
            path.resolve().relative_to(root)
        except ValueError:
            continue
        records.append(scan_one(root, path))
    decisions = Counter(str(item["decision"]) for item in records)
    report = {
        "schema": "aegis-guarded-evolution/v1",
        "scanner_version": VERSION,
        "source_root": str(source_root),
        "policy": {
            "execution_performed": False,
            "admit_knowledge_does_not_authorize_execution": True,
            "unknown_is_not_safe": True,
        },
        "summary": dict(sorted(decisions.items())),
        "records": records,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "library_source",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parent.parent
        / "reports"
        / "GUARDED_EVOLUTION_AUDIT.json",
    )
    args = parser.parse_args()
    report = audit(args.source.resolve(), args.output.resolve())
    print(json.dumps(report["summary"], indent=2))


if __name__ == "__main__":
    main()