#!/usr/bin/env python3
"""Read-only AST audit for risky subprocess shell execution in Python sources.

This tool reports findings; it does not execute inspected code or modify files.
"""
from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
from datetime import datetime, timezone

SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", "node_modules", "dist", "build"}


def inspect_file(path: Path, root: Path) -> list[dict]:
    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
    except (OSError, UnicodeError, SyntaxError) as exc:
        return [{"path": str(path.relative_to(root)), "line": 0,
                 "rule": "source_unreadable_or_invalid", "detail": str(exc)}]

    findings = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = func.id if isinstance(func, ast.Name) else (
            func.attr if isinstance(func, ast.Attribute) else ""
        )
        if name != "run":
            continue
        shell_true = any(
            keyword.arg == "shell"
            and isinstance(keyword.value, ast.Constant)
            and keyword.value.value is True
            for keyword in node.keywords
        )
        if shell_true:
            findings.append({
                "path": str(path.relative_to(root)),
                "line": node.lineno,
                "rule": "subprocess_shell_true",
                "detail": "Review command construction; prefer argument arrays and shell=False.",
            })
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".")
    parser.add_argument("--output", default="security-static-audit.json")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    findings = []
    for path in root.rglob("*.py"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        findings.extend(inspect_file(path, root))

    report = {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "Python AST scan; tracked working-tree files under repository root",
        "finding_count": len(findings),
        "findings": findings,
        "limitations": [
            "Static heuristic only; not a penetration test or proof of exploitability.",
            "Does not inspect Git history, binaries, runtime behavior, or external secrets.",
            "A shell=True finding requires manual data-flow and trust-boundary review.",
        ],
    }
    output = Path(args.output)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"finding_count": len(findings), "report": str(output)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
