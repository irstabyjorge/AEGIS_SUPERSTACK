# Master Asset Recovery Register
Date: 2026-11-12
Account scope: irstabyjorge
Status: inventory snapshot; not a complete source backup; no repositories merged or deleted.

## Preservation rules
- Preserve original repositories, branches, tags, commit history, and source blobs.
- Keep private repositories private. Do not copy private contents into public repositories.
- Keep the separate `jefeaguila` account untouched; no account linking, identity changes, or credential changes.
- Treat this register as a discovery index, not proof that every listed component is installed or functional.
- Use original-vs-working copies, provenance, hashes, and test evidence for any future repair.
- No deployment, secret rotation, access revocation, destructive cleanup, or PR merge is authorized by this recovery pass.

## GitHub repository inventory
The authenticated `irstabyjorge` account exposed 29 repositories at inventory time.

| Repository | Visibility | GitHub reported size (KB) |
|---|---:|---:|
| [nroduit.github.io](https://github.com/irstabyjorge/nroduit.github.io) | public | 26919 |
| [https-github.com-getCUJO-ThreatIntel](https://github.com/irstabyjorge/https-github.com-getCUJO-ThreatIntel) | public | 0 |
| [android_device_nubia_NX709J](https://github.com/irstabyjorge/android_device_nubia_NX709J) | public | 7 |
| [blackboxai-1741230618297](https://github.com/irstabyjorge/blackboxai-1741230618297) | public | 13 |
| [PythonApplication2](https://github.com/irstabyjorge/PythonApplication2) | private | 6 |
| [python-project](https://github.com/irstabyjorge/python-project) | public | 22 |
| [ai-sdk-computer-use](https://github.com/irstabyjorge/ai-sdk-computer-use) | private | 243 |
| [ai-sdk](https://github.com/irstabyjorge/ai-sdk) | public | 140 |
| [openai-realtime-solar-system](https://github.com/irstabyjorge/openai-realtime-solar-system) | public | 1064 |
| [AEGISWALLS-GODMODE](https://github.com/irstabyjorge/AEGISWALLS-GODMODE) | private | 18556 |
| [AEGIS_SUPERSTACK](https://github.com/irstabyjorge/AEGIS_SUPERSTACK) | public | 348 |
| [azura-codex](https://github.com/irstabyjorge/azura-codex) | public | 0 |
| [GOD_GPU_CORE](https://github.com/irstabyjorge/GOD_GPU_CORE) | public | 0 |
| [Project_AEGIS_AI](https://github.com/irstabyjorge/Project_AEGIS_AI) | public | 130 |
| [MR_WALLS](https://github.com/irstabyjorge/MR_WALLS) | public | 27 |
| [Forensic_Chat_System](https://github.com/irstabyjorge/Forensic_Chat_System) | public | 0 |
| [Azura](https://github.com/irstabyjorge/Azura) | public | 0 |
| [JefeAguila](https://github.com/irstabyjorge/JefeAguila) | public | 0 |
| [JARVIS](https://github.com/irstabyjorge/JARVIS) | public | 27269 |
| [JARVIS-MARK5](https://github.com/irstabyjorge/JARVIS-MARK5) | public | 67179 |
| [JMRTD](https://github.com/irstabyjorge/JMRTD) | public | 4004 |
| [pragma-git.github.io](https://github.com/irstabyjorge/pragma-git.github.io) | public | 23 |
| [aegisgodmode](https://github.com/irstabyjorge/aegisgodmode) | public | 223 |
| [termux-api](https://github.com/irstabyjorge/termux-api) | public | 1342 |
| [aegis_omni_xeon](https://github.com/irstabyjorge/aegis_omni_xeon) | public | 141 |
| [hub-docs](https://github.com/irstabyjorge/hub-docs) | public | 24817 |
| [AEGIS_UNIFIED_AI](https://github.com/irstabyjorge/AEGIS_UNIFIED_AI) | private | 2 |
| [git](https://github.com/irstabyjorge/git) | public | 308517 |
| [NewRepo](https://github.com/irstabyjorge/NewRepo) | private | 31 |

## Core AEGIS/PETS source lines
- `AEGIS_SUPERSTACK` — public; 64 tree entries on `main`; includes Python orchestration, API, evidence/forensics modules, QBYTE, sovereign-ai JS, tests and CI.
- `AEGISWALLS-GODMODE` — private; 403 tree entries on `main`; includes PETS/AEGIS documentation, Android defense app, external-origin snapshots, asset guard module, recovery register and integration docs.
- `Project_AEGIS_AI` — public; 38 tree entries on `main`; its core Python modules share identical Git blob SHAs with several files in `AEGIS_SUPERSTACK`, indicating duplicated source lineage rather than independent implementations.
- `MR_WALLS` — public; 21 tree entries on `main`; includes defensive configuration, evidence doctrine, prompts and install examples.
- `AEGIS_UNIFIED_AI` — private; small repository (2 KB reported); preserve and inspect independently.
- Additional related repositories include `JARVIS`, `JARVIS-MARK5`, `aegisgodmode`, `aegis_omni_xeon`, `Azura`, `azura-codex`, `GOD_GPU_CORE`, `JefeAguila`, and `Forensic_Chat_System`.

## Recovered Library records
- `JEFEAGUILA_TOTAL_UNIFIED_SAFE_ARCHITECTURE.md`
- `PETS_AEGIS_SCHEMA_INTEGRATION_MANIFEST_2026-09-29.json`
- `AEGIS-JEFEAGUILA-FUSION-status.md`
- `JEFEAGUILA_AI_CHEAT_SHEET.csv` — 80 registered entries; registry status labels are conceptual/configuration metadata, not runtime verification.
- Earlier workbench/recovery reports and cross-reference artifacts were also found in Library search. Their contents and file versions still require a full inventory and hashing pass.

## Current Android CI blocker
Latest PR #9 run: https://github.com/irstabyjorge/AEGIS_SUPERSTACK/actions/runs/43165208627
- `recovered-knowledge` job passed.
- Android job failed in `Unpack Honor bridge source`; Java/Gradle setup, unit tests, and APK artifact steps were skipped.
- The embedded `android/honor-local-bridge/bridge-source.zip.b64` decodes to a ZIP whose local file headers fail with `BadZipFile: Bad magic number for file header`. All required project files (including `AndroidManifest.xml`, Gradle files and Java sources) were skipped; the workflow then correctly stopped because the manifest was absent.
- Do not suppress this failure or silently skip corrupted members. Replace the damaged archive with individually tracked, verified source files or a newly generated archive from verified originals. Then require manifest, Gradle wrapper/build files, tests, and APK artifact before marking the bridge recovered.

## Verification already observed
- AEGIS_SUPERSTACK control-plane workflow run 43161469398 passed (Python matrix and Node integration).
- PETS Foundation run 43161469318 passed.
- AEGISWALLS-GODMODE CI run 43161364698 passed.
- Azure deployment remains intentionally disabled in the CI-only replacement; no Azure resource was deployed.
- Android bridge compilation and APK production remain unverified.

## Next recovery sequence
1. Enumerate every repository tree, branch, tag, release, workflow artifact, and accessible private repository without changing originals.
2. Inventory Library files and prior workbench archives; materialize only when needed for byte-level inspection.
3. Compare repeated blob SHAs across repositories to identify shared lineage and divergent revisions.
4. Recover Android bridge source from valid originals; rebuild the source tree as normal tracked files and validate it.
5. Build a canonical component registry with fields for source, version, SHA-256, dependencies, status (recovered/proposed/installed/tested/verified), risk and provenance.
6. Create immutable backups and a manifest before proposing consolidation PRs.
