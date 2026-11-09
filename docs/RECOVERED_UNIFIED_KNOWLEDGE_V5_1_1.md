# Recovered AEGIS Unified Knowledge v5.1.1

## Provenance
- Recovered originals: `aegis_unified.py` (v5.0.0 engine source inside the package labeled v5.1) and `aegis_guarded_evolution.py` v1.0.0 from the ChatGPT Library.
- Package label: AEGIS INVICTUS OMEGA Unified Knowledge v5.1.
- Original source archive is preserved unchanged in the Library. The portable fork is stored in this branch under `recovery/unified-knowledge-v5_1_1/`.

## Repair
The original database stored absolute `local_path` values from its former build workspace. The original `verify` therefore reported 380 files missing after extraction to a different directory. The repaired verifier checks the recorded path first, then resolves by SHA-256 only inside the package's own `library_source/`. It never searches outside the package.

## Validation performed
- 380 materialized records checked.
- 380 relocated by matching SHA-256.
- 0 missing and 0 mismatches; portable verification returned `ok=true`.
- Guarded evolution audit reproduced: 92 admit-knowledge, 198 manual-review, 19 metadata-only, 71 quarantine.
- Two regression tests cover relocated and missing files.
- No indexed source was executed.

## Guarded evolution boundary
Static classification is not proof that a file is safe. Scripts remain in manual review; opaque executables and archives remain quarantined. Admission to the knowledge index never authorizes execution.

## Honor bridge boundary
The Android app in `android/honor-local-bridge/` is separate from the cloud control plane. It uses the Android Storage Access Framework for a user-selected local folder, has no INTERNET permission, and does not grant ChatGPT background filesystem access.
