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

## Quick Start

```bash
git clone https://github.com/irstabyjorge/AEGIS_SUPERSTACK.git
cd AEGIS_SUPERSTACK
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python3 aegis_unified.py
```

## License

- **Personal & Academic**: Free under [MIT License](LICENSE)
- **Commercial**: See [COMMERCIAL_LICENSE.md](COMMERCIAL_LICENSE.md)

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
