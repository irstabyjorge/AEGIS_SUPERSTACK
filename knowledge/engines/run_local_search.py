#!/usr/bin/env python3
"""Start the curated Unified Knowledge search UI on loopback only."""
from pathlib import Path
from aegis_unified import serve

HERE = Path(__file__).resolve().parent
DB = HERE.parent / "index_package" / "knowledge" / "aegis_knowledge.sqlite3"

if __name__ == "__main__":
    if not DB.is_file():
        raise SystemExit("Knowledge index is not built. Run: python knowledge/build_curated_index.py")
    serve(DB, "127.0.0.1", 8766)
