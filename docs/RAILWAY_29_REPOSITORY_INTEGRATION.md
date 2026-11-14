# Railway integration registry — 29 repositories

**Status:** audit and preparation only. No production deployment is authorized by this registry.
**Project:** `AEGIS_OMEGA_SUPERSTACK`
**Railway project ID:** `0da09a2b-55dd-47c7-bad2-9b0a15b36cfc`
**Current environment:** `production` (only environment currently listed)
**Current service:** `aegis-api-foundation` (`81acae22-637c-4bfd-b86f-db384d0b873c`)

## Deployment rules

1. A Git repository is not automatically a Railway service. Only independently runnable, licensed, owned, dependency-audited applications with a defined entrypoint and security boundary qualify.
2. Local Android/desktop utilities, libraries, source mirrors, documentation, empty repositories, and build toolchains stay out of Railway runtime services.
3. Do not expose administrative, forensic, command-execution, network-scanning, firewall, device-control, or autonomous-remediation functions as public cloud endpoints.
4. Every candidate requires a pinned source branch/commit, reproducible build, health check, non-root runtime, least-privilege secrets, authentication/authorization review, data-retention decision, and passing CI.
5. Production changes require a separate explicit review/approval. No production deploy, domain, TCP proxy, database, volume, or secret mutation is authorized by this preparation document.

## Repository disposition

| # | Repository | Disposition | Railway treatment / reason |
|---:|---|---|---|
| 1 | `nroduit.github.io` | Exclude | Weasis documentation source; static documentation, not an AEGIS runtime service. |
| 2 | `https-github.com-getCUJO-ThreatIntel` | Hold | GitHub reports repository empty; no source to build. |
| 3 | `android_device_nubia_NX709J` | Exclude | Android device tree/build toolchain; device-side project, not a cloud service. README unavailable during this pass. |
| 4 | `blackboxai-1741230618297` | Hold | README is a placeholder; application purpose and entrypoint unverified. |
| 5 | `PythonApplication2` | Hold | README unavailable; inspect project files and entrypoint before classifying. |
| 6 | `python-project` | Hold | README identifies only a generic Python project; framework, entrypoint and dependencies unverified. |
| 7 | `ai-sdk-computer-use` | Hold / isolate | Next.js computer-use demo with third-party model and sandbox integrations. Not an AEGIS production service; requires code, license, provider, sandbox isolation and credential review. |
| 8 | `ai-sdk` | Hold / deduplicate | README matches `ai-sdk-computer-use`; compare complete trees and provenance before selecting one. Do not deploy both duplicates. |
| 9 | `openai-realtime-solar-system` | Optional demo only | Next.js/WebRTC demo requiring an API credential and browser-facing session controls; separate demo environment only after secrets and cost controls review. |
| 10 | `AEGISWALLS-GODMODE` | Local-first / exclude from cloud for now | README describes a Windows local runtime and warns against public exposure without authentication, TLS and network policy. |
| 11 | `AEGIS_SUPERSTACK` | Canonical API | Existing Railway service `aegis-api-foundation`; authenticated, bounded, read-only API foundation. Repair and validate in an isolated preview before production. |
| 12 | `azura-codex` | Hold | README unavailable; inspect files, provenance and entrypoint. |
| 13 | `GOD_GPU_CORE` | Hold / local compute | README is a placeholder; hardware/runtime requirements unverified. Do not provision cloud compute without a concrete workload and budget. |
| 14 | `Project_AEGIS_AI` | Local module / consolidation review | README describes network scanning and automatic blocklisting. Do not deploy privileged scanning or remediation to Railway. Compare with canonical API and consolidate only after review. |
| 15 | `MR_WALLS` | Local-first / exclude | README describes local Ollama and local evidence workflows; not a hosted Railway service. |
| 16 | `Forensic_Chat_System` | Hold | README is a placeholder; inspect before any integration. |
| 17 | `Azura` | Hold | README is a placeholder; inspect before any integration. |
| 18 | `JefeAguila` | Hold | README is a placeholder; inspect before any integration. |
| 19 | `JARVIS` | Exclude / superseded | README explicitly marks this project outdated and points to JARVIS-MARK5. Preserve as source history. |
| 20 | `JARVIS-MARK5` | Hold / local app | Broad assistant with provider integrations and automation. Requires dependency, dataflow, authorization and execution-boundary audit before any cloud adaptation. |
| 21 | `JMRTD` | Exclude from runtime | Java smart-card/document library; library integration requires a specific reviewed service wrapper. README unavailable in this pass. |
| 22 | `pragma-git.github.io` | Hold / static docs | README unavailable; verify ownership and content before static hosting. |
| 23 | `aegisgodmode` | Hold / adapter candidate | Remix + Cloudflare Workers starter. Audit actual app code and platform bindings before porting; README is still generic template text. |
| 24 | `termux-api` | Exclude | Android API application requiring same signing key as Termux; keep device-side, not Railway. |
| 25 | `aegis_omni_xeon` | Local security tooling / exclude | CLI monitor includes host/network inspection and auto-blocklisting. Keep local and read-only; do not expose privileged actions as cloud service. |
| 26 | `hub-docs` | Exclude | Hugging Face Hub documentation source, unrelated third-party documentation. |
| 27 | `AEGIS_UNIFIED_AI` | Local-first / exclude for now | README states loopback binding and local Ollama dependency; keep local unless a separately secured stateless adapter is designed. |
| 28 | `git` | Exclude | Upstream Git source mirror, not an AEGIS application. |
| 29 | `NewRepo` | Hold / quarantine | README unavailable. Inspect archives, provenance, hashes, license and contents in isolation before execution or integration. |

## Railway topology — proposed, not created

- **Existing:** `aegis-api-foundation` — canonical read-only API.
- **Possible later:** a separate public UI only if a repository is verified as owned, non-duplicate, licensed, and does not contain privileged device/host controls.
- **Possible later:** a separate demo service for `openai-realtime-solar-system`, isolated from the API and with explicit usage limits and server-side secret handling.
- **Not services:** local Windows/Android tools, Python/Java libraries, docs, source mirrors, empty/placeholder repos, and security scanners that require host privileges.

No additional Railway services have been created. This avoids creating empty or unsafe services and avoids triggering deployments while the only available Railway environment is production.

## Existing service findings

The existing service is configured to use `irstabyjorge/AEGIS_SUPERSTACK`, Dockerfile builder, `Dockerfile`, and start command `uvicorn railway_app.main:app --host 0.0.0.0 --port $PORT`, with health check `/healthz`. It has no public domain, TCP proxy, or volume. The latest recorded deployment is failed (`4a638ac5-155d-4613-8199-14d18ef64b95`). The service has an `AEGIS_API_TOKEN` variable name configured; secret values were not read.

The checked `main` Dockerfile uses Python 3.12 slim, installs `railway_app/requirements.txt`, copies `railway_app` and `modules`, runs as UID 10001, and starts Uvicorn. The API code accepts `AEGIS_API_TOKENS` JSON role mapping and backward-compatible `AEGIS_API_TOKEN`; this should be reconciled with the intended role model before production. The API exposes a minimal health endpoint, authenticated status, and a bounded formula-evaluation endpoint. No host telemetry or privileged remediation should be added to this API.

## Completion gates

- [ ] Inspect all held repositories and record default branch, license, ownership/provenance, build system, entrypoint, tests, dependencies, secret use, data stores, network exposure and local hardware assumptions.
- [ ] Compare duplicate repositories and choose a canonical source only with evidence.
- [ ] Resolve the existing API deployment failure in a preview/non-production environment.
- [ ] Add isolated preview environment or separate Railway project before any deployment validation.
- [ ] Add service manifests/config only for approved runnable applications.
- [ ] Verify CI, build, health, auth/RBAC, secret handling, logs, retention, backups and rollback.
- [ ] Obtain explicit production release approval.

**Audit limitation:** This is a repository-level triage, not a complete source-code/security/license audit of all 29 repositories. “Hold” means evidence is insufficient, not that the repository is safe or unsafe.
