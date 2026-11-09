"""Command-line interface for PETS–AEGIS Device Identity Registry."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path

try:
    from .registry import build_report, load_registry, sha256_file
except ImportError:  # direct execution: python modules/device_identity/main.py
    from registry import build_report, load_registry, sha256_file


def render_html(report: dict) -> str:
    rows = []
    for item in report["devices"]:
        rows.append(
            "<tr>"
            f"<td>{html.escape(item['record_id'])}</td>"
            f"<td>{html.escape(item['model'])}</td>"
            f"<td>{html.escape(item.get('platform', ''))}</td>"
            f"<td>{html.escape(item['classification'])}</td>"
            f"<td>{'Yes' if item['verified'] else 'No'}</td>"
            "</tr>"
        )
    return (
        "<!doctype html><html lang='en'><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        "<title>PETS–AEGIS Device Registry</title>"
        "<h1>PETS–AEGIS Device Registry</h1>"
        f"<p>Generated: {html.escape(report['report_generated_utc'])}</p>"
        f"<p>Total historical/device records: {report['device_count']}</p>"
        "<table border='1' cellpadding='6'><thead><tr>"
        "<th>Record</th><th>Model</th><th>Platform</th>"
        "<th>Classification</th><th>Verified</th>"
        "</tr></thead><tbody>" + "".join(rows) + "</tbody></table>"
        "<h2>Limitations</h2><ul>"
        + "".join(f"<li>{html.escape(x)}</li>" for x in report["limitations"])
        + "</ul></html>"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="PETS–AEGIS device registry (read-only by default)")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list", help="List recorded devices")
    report_parser = sub.add_parser("report", help="Generate a local inventory report")
    report_parser.add_argument("--format", choices=("json", "html"), default="json")
    report_parser.add_argument("--output", type=Path)
    hash_parser = sub.add_parser("hash-evidence", help="Calculate SHA-256 for an existing evidence file")
    hash_parser.add_argument("path", type=Path)
    args = parser.parse_args()

    if args.command == "hash-evidence":
        if not args.path.is_file():
            parser.error("Evidence path must be an existing regular file")
        print(json.dumps({"file_name": args.path.name, "sha256": sha256_file(args.path)}, indent=2))
        return 0

    report = build_report(load_registry())
    if args.command == "list":
        for device in report["devices"]:
            print(f"{device['record_id']} | {device['model']} | {device['classification']} | verified={device['verified']}")
        return 0

    rendered = json.dumps(report, ensure_ascii=False, indent=2) if args.format == "json" else render_html(report)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
        print(f"Report written: {args.output}")
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
