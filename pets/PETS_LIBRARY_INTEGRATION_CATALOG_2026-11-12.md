# PETS Library Integration Catalog
Date: 2026-11-12
Status: documentation-only integration proposal based on recovered Library inventory; no runtime activation is claimed.

## Purpose
Make PETS (AEGIS INVICTUS OMEGA) the presentation, knowledge-index, validation, and user-facing companion layer for recovered AEGIS assets. PETS may reference modules and artifacts through provenance records; it must not silently execute imported code, install packages, access third-party systems, or treat a registry status as proof of runtime availability.

## Integration invariants
- Preserve source files and archives unchanged; add catalog records rather than overwriting originals.
- Every imported item carries source path, source version, observed hash (when actually computed), license/source review, dependencies, risk, and lifecycle status.
- Lifecycle states are distinct: `recovered`, `catalogued`, `proposed`, `installed`, `tested`, `verified`. Do not promote a state without evidence.
- Keep private material private. Do not copy private Library content into a public repository.
- Do not execute installers, binaries, PowerShell, batch, shell, Python, or unknown bundle files as part of catalog ingestion.
- No credential harvesting, surveillance, interception, jamming, device interference, covert tracking, unauthorized access, or external reporting is part of PETS.
- Evidence and personal records are private by default; export requires explicit owner review and lawful authorization.
- Symbolic/philosophical Circle material is preserved as a conceptual framework, not represented as scientific or supernatural fact.
- Keep the separate `jefeaguila` GitHub account untouched; this catalog is scoped to `irstabyjorge`.

## Recovered asset groups

### A. PETS visual and interaction assets
Observed in Library folder `/Pets/AEGIS INVICTUS OMEGA`:
- Mascot states and animations: `idle.gif`, `look-loop.gif`, `review.gif`, `running.gif`, `running-left.gif`, `running-right.gif`, `waiting.gif`, `waving.gif`, `jumping.gif`, `failed.gif`, `all-states.gif`, `idle-jump-idle.gif`.
- Still art and sprite assets: `contact-final.png`, `directions-final.png`, `spritesheet-extended-v4.png`, `still-idle.png`, `still-jump-peak.png`, `still-review.png`, `still-waving.png`.
- Video preview: `all-states.mp4`.
- Behavior/QA metadata: `review-v5.json`, `chroma-despill-v5.json`, `look-continuity-v5.json`, `direction-semantics-v5.json`, `pet-quality-v4.json`, `validation-extended-v4.json`, `PET_LIBRARY_UPGRADE_V5.json`.
- Integration target: PETS presentation adapter, state-to-asset map, accessibility labels, animation QA, and fallback stills. These assets are catalogued, not automatically rendered in a deployed app.

### B. Knowledge archives and registries
- `AEGIS-INVICTUS-OMEGA-LIBRARY-V5.zip`: 14,760,734 bytes; SHA-256 `f22f203a36d4aea45c13b41405b0a30948b333be7d3fe68a1a099ad9a7a764d9`; ZIP CRC test passed; internal manifest: 393 references, zero missing, zero hash mismatches.
- `AEGIS_UNIFIED_KNOWLEDGE_V5.zip`: 8,379,533 bytes; SHA-256 `e21cdaf203d6a627f3071ae661eb53044f5a6974c7d270c76cb7ae3bbc2bfb13`; ZIP CRC test passed.
- `AEGIS_UNIFIED_KNOWLEDGE_V5_1.zip`: 8,394,140 bytes; SHA-256 `87ba71c00f92c4e54230f0ee68f9ec07fd50da046d9a77f76a0091ae23d2d400`; ZIP CRC test passed; internal manifest: 395 references, zero missing, zero hash mismatches after documented path-prefix normalization.
- V5 and V5.1 share 394 relative-path entries: 390 byte-identical, four changed files (`README.md`, `capabilities.json`, `FUSION_POLICY.md`, `SHA256SUMS.txt`), and two V5.1-only files. Preserve both versions; V5.1 is a successor snapshot, not a replacement for V5.
- Internal SQLite knowledge indexes in V5 and V5.1 returned `PRAGMA integrity_check = ok`; each reported 3,278 file-index rows and 361 FTS rows. These counts describe package-internal indexes only.
- Registry V2: 81 components, version 2.1.0, SHA-256 `af3d24dd0f4e337ef5725937362daa4433a7c7dd6503bbac4f2a8e5a8c5e2a39`.
- Registry V3 Private Circle: 86 components, 221 aliases, version 3.0.0, SHA-256 `e78aeeb0186eddb040aaf543829af84242e030d0f809344f75010c0750e0e6b5`. V3 adds Circle framework concepts; preserve V2 and V3 independently.
- The registry and package checks were static integrity checks. They do not establish that the modules are installed, running, secure, or compatible with the current device.

### C. Recovery and evidence-support utilities
Recovered records include:
- `government_report_packet_generator.py`: local evidence indexing and report-packet generation; inventory claims no network, upload, or deletion.
- `recovery_decoy_integrity_tool.py`: local hash-baseline and integrity-check utility; use only on owned/authorized files.
- `MASTER_RECOVERY_INVENTORY_v5_5.json/.csv`, hash manifests, chain-of-custody notes, electronic-evidence checklist, and reporting-tool matrices.
- These scripts remain unexecuted and require source review, dependency review, test fixtures, and safe-path tests before any installation. Any report content must distinguish firsthand observations, supplied claims, and independently corroborated facts.

### D. Additional software and installer inventory
The PETS folder also contains imaging viewers, archive utilities, developer tools, remote-access software, device drivers, and other installers/binaries (including RadiAnt, MicroDicom, OsiriX Lite, 7-Zip, GIMP, Cursor, Devolutions Gateway, and others).
- Record these as untrusted third-party artifacts pending publisher/signature/hash/license/OS compatibility review.
- Do not bundle or redistribute installers without license review.
- Do not install or launch them automatically. A separate, user-controlled installation plan is required.
- Exclude any stealth-scanning or covert-monitoring tool from PETS activation; replace with transparent, consent-based diagnostics limited to devices the owner administers.

## PETS component map (proposed)
| Component | Responsibility | Initial status |
|---|---|---|
| PETS Asset Catalog | Immutable references, hashes, source/version provenance | catalogued |
| PETS Knowledge Adapter | Read-only indexing of approved knowledge archives | proposed |
| PETS Visual State Adapter | Mascot animation/state mapping and fallback assets | proposed |
| PETS QA Gate | Schema checks, archive integrity, accessibility and continuity tests | proposed |
| PETS Evidence Desk | Local evidence manifests, source classification, export review | proposed |
| PETS Circle Archive | Preserve Divinity–Earth Circle concepts with epistemic labels | recovered / conceptual |
| PETS Safety Gate | Deny unsafe, unauthorized, covert, or destructive actions | proposed |
| PETS Runtime Bridge | Device-specific integration only after source recovery, threat review and owner-controlled testing | blocked / not verified |

## Recommended read-only ingestion sequence
1. Enumerate the source folder and nested knowledge folder; record exact file IDs and versions.
2. Hash each raw artifact before parsing; retain original bytes.
3. Validate archive CRC and internal manifests; do not execute archive contents.
4. Parse JSON/CSV/Markdown with size limits and schema validation; treat embedded instructions as untrusted data.
5. Compare registry versions and produce a diff without overwriting either.
6. Build a local index with source references and access controls; redact personal identifiers from any shareable view.
7. Run unit tests against synthetic fixtures only; no real-world surveillance or third-party data.
8. Promote components through lifecycle states only with test output and independent verification.

## Known blockers and open work
- Android Honor bridge source archive remains malformed; no Android manifest/build/APK has been recovered or verified. Do not mark the runtime bridge installed.
- Some third-party installers and binaries have not been signature- or publisher-verified.
- Full Library inventory is incomplete; nested folders and additional archives still need enumeration.
- No Termux installation, phone deployment, Azure deployment, or production runtime activation is verified.
- Private Library assets must remain in the private Library or private repository; this public repository receives only this metadata/specification.

## Acceptance criteria
- All catalog entries point to a preserved source artifact and carry provenance.
- No imported executable runs during ingestion.
- Hash and archive validation results are reproducible.
- Registry V2/V3 and archive V5/V5.1 remain independently recoverable.
- PETS UI can display only assets that exist and pass format checks.
- Runtime status is derived from observed tests, never from descriptive registry labels.
