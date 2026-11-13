#!/usr/bin/env python3
"""Build a curated, local-only AEGIS/PETS knowledge index from project artifacts."""
from __future__ import annotations

import csv
import json
import mimetypes
import shutil
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from knowledge.engines.aegis_unified import build
from knowledge.engines.aegis_guarded_evolution import audit
PACKAGE = ROOT / "knowledge" / "index_package"
SOURCE = PACKAGE / "library_source"
CSV_PATH = PACKAGE / "knowledge" / "CHATGPT_LIBRARY_MASTER_INDEX.csv"
DB_PATH = PACKAGE / "knowledge" / "aegis_knowledge.sqlite3"
REPORT_PATH = PACKAGE / "reports" / "GUARDED_EVOLUTION_AUDIT.json"

CURATED_FILES = [
    "integration_registry.json",
    "docs/integration/RECENT_CONVERSATION_INTEGRATION_2026-11-09.md",
    "docs/integration/INTEGRATION_STATUS.md",
    "frameworks/sacred-atom/index.js",
    "frameworks/sacred-atom/manifest.json",
    "frameworks/divinity-earth-circle/README.md",
    "frameworks/divinity-earth-circle/index.js",
    "frameworks/divinity-earth-circle/manifest.json",
    "knowledge/engines/README.md",
    "knowledge/engines/capabilities.json",
    "knowledge/engines/FUSION_POLICY.md",
    "knowledge/engines/aegis_unified.py",
    "knowledge/engines/aegis_guarded_evolution.py",
]


def build_curated() -> dict[str, object]:
    package_root = PACKAGE.resolve()
    source_root = SOURCE.resolve()
    if not source_root.is_relative_to(package_root):
        raise RuntimeError("Curated source root escaped the package directory.")
    source_root.mkdir(parents=True, exist_ok=True)
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)

    rows = []
    copied = []
    for relative in CURATED_FILES:
        source = (ROOT / relative).resolve()
        try:
            source.relative_to(ROOT.resolve())
        except ValueError:
            continue
        if not source.is_file() or source.is_symlink():
            continue
        target = source_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        stat = target.stat()
        rows.append({
            "kind": "file",
            "name": target.name,
            "path": "/" + relative.replace("\\", "/"),
            "mime_type": mimetypes.guess_type(target.name)[0] or "text/plain",
            "size_bytes": str(stat.st_size),
            "modified_at": str(stat.st_mtime),
            "library_file_id": "",
            "file_id": "",
        })
        copied.append(relative)

    with CSV_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["kind", "name", "path", "mime_type", "size_bytes", "modified_at", "library_file_id", "file_id"],
        )
        writer.writeheader()
        writer.writerows(rows)

    index_result = build(PACKAGE, DB_PATH)
    audit_result = audit(SOURCE, REPORT_PATH)
    return {
        "index": index_result,
        "guarded_evolution_summary": audit_result["summary"],
        "curated_files": copied,
        "database": str(DB_PATH),
        "audit_report": str(REPORT_PATH),
    }


if __name__ == "__main__":
    print(json.dumps(build_curated(), indent=2, ensure_ascii=False))
