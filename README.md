# AEGIS SUPERSTACK

**Master AI Sovereign Stack — Enterprise Security & Intelligence Platform**

AEGIS SUPERSTACK is a comprehensive security intelligence platform combining real-time threat detection, ML-powered prediction, enterprise task scheduling, GPU-accelerated analysis, and autonomous defense capabilities.

---

## Core Components

| Module | File | Purpose |
|--------|------|---------|
| **QByte-22 Engine** | `qbyte_engine.py` | Production IP threat scoring with 50+ signal vectors |
| **AEGIS Unified** | `aegis_unified.py` | Full security platform with interactive CLI |
| **AEGIS OMNI-XEON** | `aegis_omni.py` | Autonomous security operations center |
| **AEGIS Real** | `aegis_real.py` | Live system monitoring and forensics |
| **Task Scheduler** | `scheduler.py` | FastAPI task routing with NATS message bus |
| **GPU Worker** | `gpu_worker.py` | Async GPU-accelerated threat classification |
| **Quantum Service** | `quantum_service.py` | Quantum security decision engine |
| **GPU Benchmark** | `gpu_benchmark.py` | PyTorch/TensorFlow GPU performance testing |

## External Design Reference

- ChatGPT shared context/reference: https://chatgpt.com/s/cd_6a1519fdd3588191a5a202b0a35b31f4
- **Source-of-truth notice:** this shared link is supplemental context only. The source of truth for behavior, architecture, and implementation is this repository (code + docs in git).

## Repository File Map (What each file is)

### Top-level Python services
- `aegis_unified.py` — Main unified CLI/security platform entrypoint.
- `aegis_omni.py` — Autonomous SOC-style operations workflow.
- `aegis_real.py` — Real-time monitoring and live forensics checks.
- `aegis_brain.py` — Core AI/security reasoning orchestration logic.
- `aegis_chat.py` — Chat-style interface for interacting with AEGIS modules.
- `aegis_daemon.py` — Background daemon/service runner for persistent tasks.

### Threat scoring, scheduling, and acceleration
- `qbyte_engine.py` — QByte-22 threat scoring engine (IP/signal analysis).
- `scheduler.py` — FastAPI task scheduling and routing layer.
- `gpu_worker.py` — Async GPU-backed worker for heavy analysis jobs.
- `gpu_benchmark.py` — GPU performance benchmark utility.
- `quantum_service.py` — Quantum decision/scoring service integration layer.

### Security modules (`modules/`)
- `modules/api_server.py` — REST API exposing AEGIS capabilities.
- `modules/log_analyzer.py` — Security-focused log pattern analysis.
- `modules/uptime_monitor.py` — Service health, DNS/port/SSL availability checks.
- `modules/vuln_scanner.py` — Local vulnerability posture scanning/scoring.
- `modules/ioc_scanner.py` — Indicators-of-compromise detection routines.
- `modules/forensics.py` — Forensic collection and evidence-oriented inspection.
- `modules/password_audit.py` — Password policy and credential hygiene audit.
- `modules/payload_detector.py` — Web attack payload/signature detection.
- `modules/honeypot.py` — Decoy service/honeypot telemetry collection.
- `modules/__init__.py` — Package marker for module imports.

### Sovereign AI JavaScript components (`sovereign-ai/`)
- `sovereign-ai/core/system.js` — Core system orchestration (JS stack).
- `sovereign-ai/matrix/agents.js` — Agent matrix coordination logic.
- `sovereign-ai/vector/memory.js` — Vector/memory subsystem implementation.
- `sovereign-ai/economic/economic.js` — Economic/finance simulation module.
- `sovereign-ai/package.json` — Node package metadata and scripts.

### Setup, docs, and policy files
- `requirements.txt` — Python dependencies.
- `install_service.sh` — Service installation/bootstrap script.
- `LICENSE` — AEGIS MIT-style non-commercial license terms.
- `COMMERCIAL_LICENSE.md` — Commercial license terms/pricing details.
- `README.md` — Project overview and operational guidance.
- `CONTRIBUTING.md` — Contribution process and standards.
- `SECURITY.md` — Security reporting and policy notes.

### Other assets/utilities
- `aegis_icon.svg` — Project icon/branding asset.
- `search_truepeoplesearch.py` — Auxiliary search utility script.

## Features

### Threat Intelligence (QByte-22)
- Real-time IP reputation scoring against Tor exit nodes, threat intel feeds, and scanner networks
- Behavioral analysis: brute force detection, credential stuffing, injection attempts
- Reverse DNS analysis for hosting provider identification
- Session velocity tracking and repeat offender escalation
- Auto-blocklisting with persistent threat database
- Confidence scoring across 50+ signal vectors

### Network Security
- Live connection scanning with suspicious port detection
- Listening service inventory with risk classification
- Authentication log auditing (failed logins, privilege escalation)
- Firewall status inspection (UFW + iptables)
- High-frequency connection detection

### Enterprise Architecture
- FastAPI-based task scheduler with intelligent routing
- NATS message bus integration for distributed processing
- GPU worker pool for compute-intensive analysis
- Quantum decision service with multi-signal threat scoring
- Kubernetes-ready deployment architecture

### ML & Prediction
- Random Forest classifier trained on real threat history
- Predictive threat scoring with confidence intervals
- Continuous model retraining on accumulated data

## Security Modules

### API Server (`modules/api_server.py`)
REST API exposing all AEGIS capabilities — 18 endpoints, zero external dependencies.

| Endpoint | Description |
|----------|-------------|
| `GET /api/status` | System health overview |
| `GET /api/threats` | Scan live connections with QByte-22 |
| `GET /api/scan/<ip>` | Analyze specific IP threat level |
| `GET /api/connections` | Active network connections |
| `GET /api/entropy` | Generate cryptographic key material |
| `GET /api/blocklist` | Auto-blocked IP list |
| `GET /api/uptime` | Service availability report |
| `GET /api/logs/analysis` | System log security analysis |
| `GET /api/predict` | ML-based threat prediction |
| `GET /api/vuln` | Vulnerability scan with security score |
| `GET /api/ioc` | Indicators of Compromise scan |
| `GET /api/forensics` | Full forensic state capture |
| `GET /api/passwords` | Password policy & credential audit |
| `GET /api/payloads` | Web attack payload detection |
| `GET /api/honeypot` | Honeypot connection analytics |

### Log Analyzer (`modules/log_analyzer.py`)
Pattern-based security log analysis — scans auth.log, syslog, kern.log for brute force, privilege escalation, SSH scanning, suspicious commands, and firewall changes.

### Uptime Monitor (`modules/uptime_monitor.py`)
Service availability tracking with HTTP endpoint monitoring, TCP port checks, DNS resolution, and SSL certificate expiry warnings.

### Vulnerability Scanner (`modules/vuln_scanner.py`)
Local system security assessment: SUID files, world-writable files, SSH config, firewall, exposed ports, sensitive file permissions, kernel hardening. Produces a 0-10 security score.

### Honeypot (`modules/honeypot.py`)
Lightweight decoy service that opens fake ports with realistic banners (SSH, FTP, MySQL, Redis, Elasticsearch). Logs every connection attempt with full metadata for threat intelligence.

### IOC Scanner (`modules/ioc_scanner.py`)
Indicators of Compromise detection: suspicious processes (crypto miners, reverse shells), persistence mechanisms, rogue SSH keys, hidden temp files, DNS hijacking, and shell history analysis.

### Forensics Toolkit (`modules/forensics.py`)
System forensic analysis and evidence collection. Captures volatile state, analyzes file timelines, inspects kernel modules, audits user accounts, and SHA-256 hashes critical binaries.

### Password Auditor (`modules/password_audit.py`)
Credential security assessment: password aging policies, empty passwords, PAM configuration, password hashing strength, and brute force login detection.

### Payload Detector (`modules/payload_detector.py`)
Web attack payload detection engine. Scans logs and files for SQL injection, XSS, command injection, path traversal, web shells, XXE, SSRF, and Log4Shell signatures.

## Responsible Use

AEGIS SUPERSTACK is intended for defensive security, blue-team operations, and authorized testing only.

### Allowed Use Cases
- Security monitoring for infrastructure you own or are contractually authorized to assess.
- Internal threat hunting, incident response support, and controlled purple-team validation.
- Lab and educational experiments in isolated, non-production environments.

### Prohibited Use Cases
- Building unrestricted or safety-disabled AI systems.
- Deploying offensive automation against systems you do not own or explicitly control.
- Mass surveillance, unauthorized data collection, or policy/law-violating telemetry capture.
- Automating destructive actions without auditable human approval.

### Operational Guardrails
- Keep human oversight for any autonomous response workflow.
- Define explicit scope (targets, time window, and data retention) before any scan.
- Run high-impact actions in simulation or dry-run mode first when available.
- Maintain logs for all scans, blocks, and automated decisions for audit/review.
- Follow all applicable laws, contracts, and organizational policies before running scans or collecting telemetry.

## MCP Apps & ChatGPT Compatibility Notes

If you build ChatGPT-facing UI surfaces for AEGIS integrations, prefer the MCP Apps standard first for portability.

### Recommended Baseline (Portable)
- Declare UI resources with `_meta.ui.resourceUri`.
- Use the standard `ui/*` JSON-RPC bridge over `postMessage` for initialization, notifications, and host interaction.
- Use MCP tool calls (`tools/call`) from UI components instead of host-specific globals by default.

### Optional ChatGPT Extensions
- Use `window.openai` only for capabilities that are ChatGPT-specific (for example checkout, file APIs, and modals).
- Feature-detect extensions and provide fallback behavior for hosts where these APIs are unavailable.

### Mapping Guidance

| Goal | MCP Apps standard | ChatGPT extension (optional) |
|------|-------------------|------------------------------|
| Link a tool to a UI resource | `_meta.ui.resourceUri` | `_meta["openai/outputTemplate"]` |
| Receive tool input | `ui/initialize` + `ui/notifications/tool-input` | `window.openai.toolInput` |
| Receive tool results | `ui/notifications/tool-result` | `window.openai.toolOutput` |
| Call a tool from UI | `tools/call` | `window.openai.callTool` |
| Send follow-up message | `ui/message` | `window.openai.sendFollowUpMessage` |
| Update model-visible UI context | `ui/update-model-context` | `window.openai.setWidgetState` |

### Extension Best Practice Snippet
```js
const openai = typeof window !== "undefined" ? window.openai : undefined;

if (openai?.requestModal) {
  await openai.requestModal({
    /* modal payload */
  });
} else {
  // Fallback behavior for hosts without this extension.
}
```

This approach keeps AEGIS app surfaces portable across MCP-compatible hosts while still allowing enhanced ChatGPT experiences when available.

## How to Run Locally (Safe / Defensive)

```bash
git clone https://github.com/irstabyjorge/AEGIS_SUPERSTACK.git
cd AEGIS_SUPERSTACK
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Primary interface (interactive defensive tooling)
python3 aegis_unified.py
```

Optional local runs:

```bash
# API mode (local-only unless you intentionally expose it)
python3 modules/api_server.py

# Autonomous SOC workflow (authorized environments only)
python3 aegis_omni.py

# Real-time monitoring and forensics
python3 aegis_real.py
```

## Testing

Run these checks locally before opening a PR:

```bash
# 1) Validate Python syntax across repository
python3 -m compileall .

# 2) Validate imports for key entry points
python3 -c "import aegis_unified, aegis_omni, aegis_real, qbyte_engine, scheduler, gpu_worker, quantum_service, gpu_benchmark"

# 3) Optional: run API module import check
python3 -c "from modules import api_server, log_analyzer, uptime_monitor, vuln_scanner, ioc_scanner, forensics, password_audit, payload_detector, honeypot"
```

## Security Boundaries (Authorized Defensive Use Only)

- Use AEGIS only on systems you own or where you have explicit written authorization.
- Do not use AEGIS for credential harvesting, malware development, stealth/persistence abuse, destructive actions, or unauthorized access.
- Keep scans and response actions auditable, minimal, and scoped to approved targets.
- Treat collected telemetry as sensitive security data; store and retain it according to policy.
- Require human approval for high-impact actions (blocking, quarantine, active response).

## Next Implementation Steps

- [ ] Add a centralized configuration file (`config.example.yaml`) with safe defaults and local-only bindings.
- [ ] Add unit tests for `qbyte_engine.py` scoring signals and confidence calculations.
- [ ] Add integration tests for `modules/api_server.py` endpoints using sample fixtures.
- [ ] Add structured JSON logging with request/scan IDs for auditability.
- [ ] Add role-based access controls and API auth middleware for multi-user deployments.
- [ ] Add CI pipeline checks (format, lint, compile, import smoke tests).
- [ ] Add threat-intel feed stubbing/mocking for deterministic offline tests.

## License

- **Personal & Academic**: Free under the [AEGIS MIT-style Non-Commercial License](LICENSE)
- **Commercial**: See [COMMERCIAL_LICENSE.md](COMMERCIAL_LICENSE.md)


### License FAQ
- **Why is there a license if this is your project?** Because you own the copyright by default, and the license is how you decide what other people are allowed to do with your code.
- This repository uses an MIT-style non-commercial license for personal/academic use, while commercial use requires the separate terms in `COMMERCIAL_LICENSE.md`.

| Tier | Monthly | Annual |
|------|---------|--------|
| Professional | $2,499 | $29,988 |
| Business | $9,999 | $119,988 |
| Enterprise | $24,999 | $299,988 |
| Enterprise Plus | $49,999 | $599,988 |
| Sovereign / Gov | $99,999 | $1,199,988 |

## Author

**Jorge Francisco Paredes** (irstabyjorge)
- GitHub: [github.com/irstabyjorge](https://github.com/irstabyjorge)
- Email: IRSTAXBYJORGE@GMAIL.COM

[![GitHub Sponsors](https://img.shields.io/badge/Sponsor-GitHub-ea4aaa?logo=github)](https://github.com/sponsors/irstabyjorge)

---

Copyright (c) 2024-2026 Jorge Francisco Paredes. All rights reserved.
