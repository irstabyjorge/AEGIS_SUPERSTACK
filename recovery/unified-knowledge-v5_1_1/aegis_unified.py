#!/usr/bin/env python3
"""AEGIS Unified Knowledge Engine.

Indexes Library metadata and locally materialized text/source files without
executing, importing, installing, or modifying any indexed content.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import mimetypes
import os
import sqlite3
import sys
import time
from collections import Counter
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

VERSION = "5.1.0"
MAX_TEXT_BYTES = 8 * 1024 * 1024
SAFE_TEXT_EXTENSIONS = {
    ".bat", ".bash", ".c", ".cc", ".cfg", ".cmd", ".cpp", ".css", ".csv",
    ".cxx", ".go", ".h", ".hh", ".hpp", ".html", ".ini", ".ipynb", ".java",
    ".js", ".json", ".jsonl", ".jsx", ".lua", ".md", ".php", ".pl", ".ps1",
    ".py", ".pyw", ".rb", ".rs", ".scss", ".sh", ".sql", ".toml", ".ts",
    ".tsx", ".txt", ".ubundle", ".yaml", ".yml", ".zsh",
}
BLOCKED_EXECUTABLE_EXTENSIONS = {
    ".apk", ".appimage", ".com", ".dmg", ".dll", ".exe", ".iso", ".msi",
    ".scr", ".sys",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def classify(name: str, mime_type: str = "") -> str:
    suffix = Path(name).suffix.lower()
    if suffix in BLOCKED_EXECUTABLE_EXTENSIONS:
        return "isolated-executable"
    if suffix in {".py", ".pyw"}:
        return "python"
    if suffix in {".js", ".jsx", ".ts", ".tsx"}:
        return "javascript-typescript"
    if suffix in {".ps1", ".bat", ".cmd", ".sh", ".bash", ".zsh"}:
        return "shell-automation"
    if suffix in {".c", ".cc", ".cpp", ".cxx", ".h", ".hh", ".hpp", ".rs", ".go", ".java"}:
        return "compiled-source"
    if suffix in {".json", ".jsonl", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".ubundle"}:
        return "configuration"
    if suffix in {".md", ".txt", ".html", ".csv"}:
        return "knowledge-document"
    if mime_type.startswith("image/"):
        return "image-reference"
    if mime_type == "application/pdf":
        return "pdf-reference"
    if suffix in {".zip", ".7z", ".rar", ".tar", ".gz"}:
        return "isolated-archive"
    return "metadata-reference"


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("PRAGMA foreign_keys=ON")
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS files (
            path TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            mime_type TEXT,
            category TEXT NOT NULL,
            size_bytes INTEGER,
            modified_at TEXT,
            library_file_id TEXT,
            file_id TEXT,
            materialized INTEGER NOT NULL DEFAULT 0,
            local_path TEXT,
            sha256 TEXT,
            indexed_bytes INTEGER NOT NULL DEFAULT 0,
            content_status TEXT NOT NULL DEFAULT 'metadata-only'
        );
        CREATE TABLE IF NOT EXISTS build_info (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_fts USING fts5(
            path UNINDEXED,
            name,
            category,
            content,
            tokenize='unicode61'
        );
        """
    )
    return connection


def load_master_inventory(connection: sqlite3.Connection, inventory_csv: Path) -> int:
    count = 0
    with inventory_csv.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            if row.get("kind") != "file":
                continue
            name = row.get("name", "")
            path = row.get("path", "")
            mime_type = row.get("mime_type", "")
            connection.execute(
                """
                INSERT INTO files(
                    path, name, mime_type, category, size_bytes, modified_at,
                    library_file_id, file_id
                ) VALUES(?,?,?,?,?,?,?,?)
                ON CONFLICT(path) DO UPDATE SET
                    name=excluded.name,
                    mime_type=excluded.mime_type,
                    category=excluded.category,
                    size_bytes=excluded.size_bytes,
                    modified_at=excluded.modified_at,
                    library_file_id=excluded.library_file_id,
                    file_id=excluded.file_id
                """,
                (
                    path,
                    name,
                    mime_type,
                    classify(name, mime_type),
                    int(row["size_bytes"]) if row.get("size_bytes") else None,
                    row.get("modified_at", ""),
                    row.get("library_file_id", ""),
                    row.get("file_id", ""),
                ),
            )
            count += 1
    return count


def safe_text(path: Path) -> tuple[str | None, str]:
    suffix = path.suffix.lower()
    if suffix in BLOCKED_EXECUTABLE_EXTENSIONS:
        return None, "isolated-executable"
    if suffix not in SAFE_TEXT_EXTENSIONS:
        return None, "metadata-only"
    size = path.stat().st_size
    if size > MAX_TEXT_BYTES:
        return None, "text-too-large"
    try:
        return path.read_text(encoding="utf-8", errors="replace"), "indexed"
    except OSError as exc:
        return None, f"read-error:{type(exc).__name__}"


def canonical_library_path(source_root: Path, path: Path) -> str:
    relative = path.relative_to(source_root).as_posix()
    return "/" + relative.lstrip("/")


def index_materialized(connection: sqlite3.Connection, source_root: Path) -> dict[str, int]:
    connection.execute("DELETE FROM knowledge_fts")
    stats = Counter()
    for path in sorted(source_root.rglob("*")):
        if not path.is_file():
            continue
        library_path = canonical_library_path(source_root, path)
        name = path.name
        mime_type = mimetypes.guess_type(name)[0] or ""
        category = classify(name, mime_type)
        digest = sha256_file(path)
        content, status = safe_text(path)
        indexed_bytes = len(content.encode("utf-8")) if content is not None else 0
        connection.execute(
            """
            INSERT INTO files(
                path, name, mime_type, category, size_bytes, materialized,
                local_path, sha256, indexed_bytes, content_status
            ) VALUES(?,?,?,?,?,1,?,?,?,?)
            ON CONFLICT(path) DO UPDATE SET
                materialized=1,
                local_path=excluded.local_path,
                sha256=excluded.sha256,
                indexed_bytes=excluded.indexed_bytes,
                content_status=excluded.content_status,
                category=excluded.category
            """,
            (
                library_path,
                name,
                mime_type,
                category,
                path.stat().st_size,
                str(path),
                digest,
                indexed_bytes,
                status,
            ),
        )
        if content is not None:
            connection.execute(
                "INSERT INTO knowledge_fts(path,name,category,content) VALUES(?,?,?,?)",
                (library_path, name, category, content),
            )
            stats["indexed"] += 1
            stats["indexed_bytes"] += indexed_bytes
        else:
            stats[status] += 1
        stats["materialized"] += 1
    return dict(stats)


def build(package_root: Path, db_path: Path) -> dict[str, object]:
    inventory_csv = package_root / "knowledge" / "CHATGPT_LIBRARY_MASTER_INDEX.csv"
    source_root = package_root / "library_source"
    if not inventory_csv.is_file():
        raise SystemExit(f"Missing inventory: {inventory_csv}")
    if not source_root.is_dir():
        raise SystemExit(f"Missing materialized source directory: {source_root}")
    connection = connect(db_path)
    metadata_count = load_master_inventory(connection, inventory_csv)
    source_stats = index_materialized(connection, source_root)
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    build_info = {
        "engine_version": VERSION,
        "built_at_utc": now,
        "metadata_files": str(metadata_count),
        "materialized_files": str(source_stats.get("materialized", 0)),
        "indexed_files": str(source_stats.get("indexed", 0)),
    }
    connection.executemany(
        "INSERT OR REPLACE INTO build_info(key,value) VALUES(?,?)",
        build_info.items(),
    )
    connection.commit()
    total = connection.execute("SELECT COUNT(*) FROM files").fetchone()[0]
    connection.close()
    return {
        "ok": True,
        "engine_version": VERSION,
        "database": str(db_path),
        "metadata_records": total,
        "source_stats": source_stats,
        "built_at_utc": now,
    }


def search(db_path: Path, query: str, limit: int) -> list[dict[str, object]]:
    connection = connect(db_path)
    try:
        rows = connection.execute(
            """
            SELECT f.path, f.name, f.category, f.mime_type, f.size_bytes,
                   f.sha256, f.materialized, f.content_status,
                   snippet(knowledge_fts, 3, '[', ']', ' … ', 24) AS snippet,
                   bm25(knowledge_fts) AS rank
            FROM knowledge_fts
            JOIN files f ON f.path = knowledge_fts.path
            WHERE knowledge_fts MATCH ?
            ORDER BY rank
            LIMIT ?
            """,
            (query, limit),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        connection.close()


def stats(db_path: Path) -> dict[str, object]:
    connection = connect(db_path)
    try:
        total = connection.execute("SELECT COUNT(*) FROM files").fetchone()[0]
        materialized = connection.execute(
            "SELECT COUNT(*) FROM files WHERE materialized=1"
        ).fetchone()[0]
        indexed = connection.execute(
            "SELECT COUNT(*) FROM files WHERE content_status='indexed'"
        ).fetchone()[0]
        categories = {
            row["category"]: row["count"]
            for row in connection.execute(
                "SELECT category, COUNT(*) AS count FROM files GROUP BY category ORDER BY count DESC"
            )
        }
        build_info = {
            row["key"]: row["value"]
            for row in connection.execute("SELECT key,value FROM build_info")
        }
        return {
            "engine_version": VERSION,
            "total_library_files": total,
            "materialized_files": materialized,
            "content_indexed_files": indexed,
            "categories": categories,
            "build_info": build_info,
        }
    finally:
        connection.close()


def verify(db_path: Path, package_root: Path | None = None) -> dict[str, object]:
    """Verify files and resolve stale absolute paths by SHA-256 inside the package."""
    root = (package_root or db_path.parent.parent).resolve()
    source_root = root / "library_source"
    connection = connect(db_path)
    checked = 0
    mismatches = []
    missing = []
    relocated = []
    hash_index: dict[str, list[Path]] | None = None
    try:
        rows = connection.execute(
            "SELECT path,local_path,sha256 FROM files WHERE materialized=1"
        )
        for row in rows:
            checked += 1
            expected = str(row["sha256"] or "")
            local_path = Path(row["local_path"] or "")
            if local_path.is_file() and sha256_file(local_path) == expected:
                continue
            if hash_index is None:
                hash_index = {}
                if source_root.is_dir():
                    for candidate in source_root.rglob("*"):
                        if candidate.is_file():
                            digest = sha256_file(candidate)
                            hash_index.setdefault(digest, []).append(candidate)
            matches = hash_index.get(expected, []) if expected else []
            if matches:
                relocated.append({
                    "path": row["path"],
                    "resolved_path": str(matches[0].relative_to(root)),
                })
            elif local_path.is_file():
                mismatches.append({
                    "path": row["path"],
                    "expected": expected,
                    "actual": sha256_file(local_path),
                })
            else:
                missing.append(row["path"])
    finally:
        connection.close()
    return {
        "ok": not missing and not mismatches,
        "checked": checked,
        "relocated": relocated,
        "missing": missing,
        "mismatches": mismatches,
    }


def duplicates(db_path: Path) -> dict[str, object]:
    connection = connect(db_path)
    try:
        rows = connection.execute(
            """
            SELECT sha256, COUNT(*) AS copies, SUM(size_bytes) AS total_bytes
            FROM files
            WHERE materialized=1 AND sha256 IS NOT NULL
            GROUP BY sha256
            HAVING COUNT(*) > 1
            ORDER BY copies DESC, total_bytes DESC
            """
        ).fetchall()
        groups = []
        for row in rows:
            paths = [
                item["path"]
                for item in connection.execute(
                    "SELECT path FROM files WHERE sha256=? ORDER BY path",
                    (row["sha256"],),
                )
            ]
            groups.append(
                {
                    "sha256": row["sha256"],
                    "copies": row["copies"],
                    "total_bytes": row["total_bytes"],
                    "paths": paths,
                }
            )
        return {
            "duplicate_groups": len(groups),
            "duplicate_files": sum(group["copies"] for group in groups),
            "groups": groups,
        }
    finally:
        connection.close()


class SearchHandler(BaseHTTPRequestHandler):
    db_path: Path

    def _json(self, payload: object, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/api/stats":
            self._json(stats(self.db_path))
            return
        if parsed.path == "/api/search":
            query = parse_qs(parsed.query).get("q", [""])[0].strip()
            if not query:
                self._json({"error": "Missing q parameter"}, 400)
                return
            self._json({"query": query, "results": search(self.db_path, query, 25)})
            return
        if parsed.path != "/":
            self._json({"error": "Not found"}, 404)
            return
        page = """<!doctype html><meta charset="utf-8">
<title>AEGIS Unified Knowledge</title>
<style>
body{font:16px system-ui;max-width:900px;margin:40px auto;padding:0 20px;background:#111;color:#eee}
input{width:70%;padding:12px;background:#222;color:#fff;border:1px solid #555}
button{padding:12px 18px}.result{padding:14px 0;border-bottom:1px solid #333}
code{color:#ffb347;word-break:break-all}
</style>
<h1>AEGIS Unified Knowledge</h1>
<p>Local, read-only search. Indexed files are never executed.</p>
<input id="q" placeholder="Search Library-derived knowledge"><button onclick="go()">Search</button>
<div id="out"></div>
<script>
async function go(){
 const q=document.getElementById('q').value;
 const r=await fetch('/api/search?q='+encodeURIComponent(q)); const j=await r.json();
 document.getElementById('out').innerHTML=(j.results||[]).map(x =>
  `<div class=result><code>${esc(x.path)}</code><p>${esc(x.snippet||'')}</p></div>`).join('');
}
function esc(x){return String(x).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
</script>"""
        body = page.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        sys.stderr.write("[AEGIS] " + format % args + "\n")


def serve(db_path: Path, host: str, port: int) -> None:
    SearchHandler.db_path = db_path
    server = ThreadingHTTPServer((host, port), SearchHandler)
    print(f"AEGIS Unified Knowledge: http://{host}:{port}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def default_package_root() -> Path:
    return Path(__file__).resolve().parent.parent


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--package-root", type=Path, default=default_package_root(),
        help="Root containing knowledge/ and library_source/",
    )
    parser.add_argument("--db", type=Path, default=None)
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("build")
    search_parser = subparsers.add_parser("search")
    search_parser.add_argument("query")
    search_parser.add_argument("--limit", type=int, default=20)
    subparsers.add_parser("stats")
    subparsers.add_parser("verify")
    subparsers.add_parser("duplicates")
    serve_parser = subparsers.add_parser("serve")
    serve_parser.add_argument("--host", default="127.0.0.1")
    serve_parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()

    package_root = args.package_root.resolve()
    db_path = (args.db or package_root / "knowledge" / "aegis_knowledge.sqlite3").resolve()
    if args.command == "build":
        payload = build(package_root, db_path)
    elif args.command == "search":
        payload = {"query": args.query, "results": search(db_path, args.query, args.limit)}
    elif args.command == "stats":
        payload = stats(db_path)
    elif args.command == "verify":
        payload = verify(db_path, package_root)
    elif args.command == "duplicates":
        payload = duplicates(db_path)
    else:
        serve(db_path, args.host, args.port)
        return
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()