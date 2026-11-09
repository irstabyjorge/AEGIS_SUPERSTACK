# Fusion and Isolation Policy

## Integrated as searchable knowledge

- Source code and scripts
- Configuration files
- Markdown, text, HTML, and CSV documentation
- Library metadata and stable file identities

## Indexed by reference only

- PDF and office documents not materialized in this package
- Medical images and medical archives
- Evidence packages and forensic archives
- Large media files
- Library items whose bytes were unavailable during materialization

## Isolated and never executed

- EXE, MSI, DLL, APK, DMG, ISO, SYS, SCR, and COM files
- Compressed archives until separately reviewed
- Scripts whose behavior has not been audited
- Files containing credentials, tokens, private keys, or personal records

## Integrity

Each materialized file receives a SHA-256 digest in the SQLite knowledge
database. `aegis_unified.py verify` recomputes those hashes and reports missing
or changed files.

## Guarded evolution

`aegis_guarded_evolution.py` performs static triage without executing any
candidate. Passive text and configuration may be admitted as searchable
knowledge when no behavior indicators match. Scripts remain in manual review,
and opaque executables, installers, archives, or critical indicators remain
quarantined. A clean static result is not proof that a program is safe.

## Non-destructive behavior

The package leaves every original ChatGPT Library item unchanged. Library file
identifiers in the master index provide traceability back to the source.