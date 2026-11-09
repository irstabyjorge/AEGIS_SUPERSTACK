# AEGIS/PETS Full-Stack Enhancement Audit — 2026-11-09

## Scope and method

This audit combines:
- Read-only inspection of the current `aegis-pets-cloud-integration` branch in `irstabyjorge/AEGIS_SUPERSTACK`.
- GitHub Actions run/job metadata and available logs.
- Current official documentation for WebAssembly/WASI, LLVM, GitHub Actions supply-chain security, ChatGPT capabilities, and OpenAI audio transcription/translation.
- The ChatGPT host tools currently available in this session.

This is a source-level and CI review, not a penetration test, physical-device test, privacy certification, or production-readiness approval.

## Verified repository state

- Repository default branch: `main`.
- Work is being kept on `aegis-pets-cloud-integration`; PR #8 remains open.
- No production deployment is authorized or claimed.
- The cloud control plane remains read-only.
- ChatGPT host connectors are not automatically available inside a separately deployed PETS runtime. Each repository adapter needs a separately approved API integration and scoped credentials.

## Improvements added in this pass

### 1. Cross-platform evidence-store correction

- Updated `modules/pets/evidence_store.py` to explicitly close SQLite connections.
- Updated the direct-connection test to close its handle.
- Reason: Python's SQLite connection context manager commits or rolls back transactions but does not itself close the connection. Windows CI had reported file-lock errors during temporary-directory cleanup.

### 2. Registry-test correction

- Updated `tests/test_integration_registry.py` so it no longer requires an implementation marked `implemented_ci_pending` to claim it is already `tested`.
- This preserves honest capability status.

### 3. CI action maintenance

- Updated workflow action references to Node 24-compatible major releases: checkout v7, setup-python v7, setup-node v7, setup-java v6, upload-artifact v7, and Gradle setup v6.
- Selected Gradle's `basic` cache provider to keep the caching path open-source.
- Kept the Gradle distribution at 8.9 because the Android source archive is currently invalid and its Android Gradle Plugin compatibility cannot yet be verified.
- Kept `npm install` because the current `sovereign-ai` directory does not contain a committed lockfile; `npm ci` would therefore be inappropriate until a lockfile is generated and reviewed.
- Added weekly Dependabot checks for GitHub Actions, Python requirements and the Sovereign AI npm package. Updates create reviewable PRs; nothing auto-merges.

### 4. PETS Universal Translation Engine foundation

Added:
- `modules/pets/qbyte_format_scanner.py`: bounded, header-only recognition of PE/COFF, ELF, Mach-O, WebAssembly, ZIP containers and selected script formats.
- `modules/pets/universal_ir.py`: allowlisted, JSON-compatible task representation for file inspection, text analysis, audio transcription, text/audio translation, recording summaries and reports.
- `modules/pets/compatibility_switch.py`: explicit runtime registry and plan-only route selection.
- `tests/test_pets_ute.py`: synthetic format, IR and compatibility tests.
- `docs/PETS_UNIVERSAL_TRANSLATION_ENGINE.md`: design and boundaries.
- Exports and registry entries for the three new modules.

The scanner reads at most 64 KiB from one explicitly selected regular file. It does not recurse through storage, extract archives, install packages, launch executables, rewrite binaries, or inspect devices.

The compatibility switch selects a registered runtime only if the descriptor is explicitly verified and sandboxed and matches the host platform and architecture. Native-loader matches are candidates, not launches. Unknown or incompatible files remain blocked.

The IR is a task contract, not a replacement for CPU instructions, OS APIs, ABIs, libraries or executable formats. The user's Spanish request is a natural-language input; the IR is the normalized contract; a platform adapter is still required to map the contract to a supported runtime/API.

## CI evidence observed

- AEGIS PETS Cloud Control Plane push run: Python 3.11 job passed compilation, unit tests, curated-index build and integrity verification.
- PETS Foundation push run: Linux and Windows jobs passed compilation, PETS tests and Sacred Atom engine tests.
- Other matrix legs and pull-request checks did not all return a complete, inspectable success result in this audit window. Do not mark the entire matrix green yet.
- Android bridge: the prior CI log failed while checking the ZIP central directory. The checked-in Base64 source bundle is invalid/truncated. No Android build was reached and no APK was produced.
- No physical Honor installation has been verified.

## Legacy module risk review

These modules remain outside the new cloud control plane. They are not enabled by this audit.

| Component | Source-level observation | Disposition |
|---|---|---|
| `modules/api_server.py` | Existing security matrix reports unauthenticated routes, a public-interface bind and a route that can trigger automatic blocklisting | Do not expose publicly; keep out of cloud control plane |
| `modules/forensics.py` | Uses `subprocess.run(..., shell=True)` and collects host process, account, filesystem and network state | Do not run as a general-purpose collector; requires a narrow, consent-based, read-only redesign |
| `modules/honeypot.py` | Opens TCP listeners on `0.0.0.0` and records remote source addresses and received data | Keep inactive; no network listener is enabled by PETS |
| `install_service.sh` | Installs systemd user services, enables them and configures lingering for persistence | Do not run as part of this integration |
| `aegis_daemon.py` | Runs periodic host scans and writes persistent local state/logs | Keep inactive pending explicit task, scope and consent controls |
| `scheduler.py` | Accepts task types and arbitrary JSON payloads and routes them to NATS subjects; no authentication is visible in the inspected endpoint | Not connected or publicly exposed |
| `gpu_worker.py` | Current worker is a stub returning a fixed classification/confidence; it is not verified GPU computation | Do not advertise GPU acceleration |
| `quantum_service.py` | Uses random jitter in a risk score; this is not quantum computation | Rename/document as a heuristic prototype before any use |
| `search_truepeoplesearch.py` | Filename indicates a people-search workflow; source and privacy basis were not reviewed here | Excluded from enhancement and execution pending a legitimate, privacy-reviewed purpose |

The existing `docs/LEGACY_MODULES_SECURITY_MATRIX.md` already documents important admission blockers. Keep those modules quarantined from the public cloud control plane.

## Capability truth table

| Capability | Current status |
|---|---|
| PETS RBAC policy | Implemented as a local policy library; trusted identity binding is not implemented |
| Evidence ledger | Implemented with SQLite append-only triggers and a SHA-256 chain; not tamper-proof, not encrypted at rest by the module, and not independently anchored |
| Provider adapters | Read-only protocol and fixture adapter only; no live provider API integration |
| Cross-platform Python profile | Implemented; native mobile, IoT and board validation remain pending |
| Sacred Atom geometry | Implemented as an organizational graph/metaphor, not machine consciousness |
| CPU compute baseline | Implemented for a minimal identity operation |
| GPU | No validated GPU adapter or hardware proof |
| Auto-assembly | Dependency planning only; no download, install, import or execution |
| Sacred Atom GUI | Static preview; not connected to an authenticated live API |
| UTE/QBYTE | Format recognition, task IR and route planning implemented; no binary translation or execution |
| Android/Termux | Source bundle invalid; no APK or device installation verified |
| Apple iOS/iPadOS | No native bridge implemented |
| IoT / firmware | No device-control adapter; no firmware operations |
| Vercel | No production deployment claimed |
| Recordings | IR operations are defined; no repository-side audio provider adapter is connected |
| Languages | Language tags can be carried in IR; actual model/provider language coverage must be checked per operation |

## Recording and language pipeline

For recordings, normalize results into:
- Original audio asset reference (not copied into the evidence ledger by default).
- Detected/source language and requested target language.
- Transcript segments with timestamps where supported.
- Speaker labels only where the selected transcription provider supports them and the recording was lawfully/consensually supplied.
- Translation, summary and provenance as separate outputs.

Current OpenAI documentation distinguishes file transcription (`gpt-transcribe`), low-latency streaming transcription (`gpt-live-transcribe`) and Realtime translation. The older audio-translation endpoint is deprecated and scheduled to remain only until February 26, 2027. Whisper supports many languages, but recognition quality varies by language; model choice must follow the task rather than assuming every model translates every language.

## Next engineering gates

1. Obtain a valid Android source tree in ordinary reviewable source files; do not rely on the current corrupt Base64 archive.
2. Finish the full Linux/Windows/macOS and Python-version CI matrix and investigate the PR checks that returned incomplete job data.
3. Add explicit language-tag validation and provider capability declarations without claiming unsupported languages.
4. Add a WASI Component Model adapter only after a runtime version, imports, filesystem/network grants, resource ceilings and sandbox tests are recorded.
5. Keep LLVM as an optional source/IR compiler toolchain; do not treat it as an opaque-binary translator.
6. Add SBOM generation, dependency review, immutable action SHA pinning and artifact attestations before release.
7. Keep host tools, connected apps and PETS runtime adapters as separate states. A tool being available in ChatGPT does not mean its credentials or APIs are installed in PETS.
8. Perform an independent security/privacy review before any public deployment or device bridge release.

## Non-goals and safety invariants

- No automatic self-modification or autonomous deployment.
- No stealth persistence, broad device collection, radio interception/jamming, firmware flashing or remote device control.
- No arbitrary binary launch, shell execution or unreviewed plugin execution.
- No person-level targeting or people-search data aggregation.
- Read-only by default, explicit user selection, bounded inputs, provenance and human approval for writes.
