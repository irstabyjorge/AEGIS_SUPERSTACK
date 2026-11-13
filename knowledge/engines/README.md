# AEGIS Unified Knowledge v5.1 — integrated engine

The original Unified Knowledge v5.0.0 engine and Guarded Evolution v1.0.0 scanner were recovered from the user's Library and installed as source under this directory.

## Components
- aegis_unified.py: SQLite/FTS5 metadata and safe-text index, SHA-256 verification, duplicate reporting, read-only search UI.
- aegis_guarded_evolution.py: static triage into admit-knowledge, manual-review, metadata-only, and quarantine.
- upstream/: exact original source snapshots preserved for provenance.
- capabilities.json and FUSION_POLICY.md: original package contracts.
- SOURCE_PROVENANCE.json: source Library IDs, original SHA-256 digests, and local patch record.

## Local integration hardening
The active copies preserve the original architecture and commands, with narrow safety patches:
1. FTS5 input is tokenized and quoted so punctuation cannot inject FTS operators.
2. Symlinks and paths outside the selected source root are skipped.
3. VCS, virtual-environment, package-cache, and bytecode directories are excluded.
4. The search server refuses non-loopback bind addresses and adds no-store/security headers.
5. Guarded Evolution remains static-only; it never imports or executes candidate files.

## Build a curated index
Run from the repository root:

    python knowledge/build_curated_index.py

The builder indexes only selected AEGIS/PETS project manifests, framework files, and integration notes. It does not ingest the complete Library, medical records, incident reports, or evidence archives.

## Local-only search server
After building:

    python knowledge/engines/run_local_search.py

The server binds to 127.0.0.1:8766 only. It is read-only and has no upload or mutation routes.

The full 8.39 MB original archive was inspected by listing only. It contains 408 entries / about 51.7 MB uncompressed, including DICOM inventories and incident/evidence material; those records remain isolated in the Library.
