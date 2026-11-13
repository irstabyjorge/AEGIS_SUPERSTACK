# Legacy Modules — Cloud Admission and Security Matrix

**Review basis:** source inspection of branch base and integration branch files.
**Disposition:** quarantined from the new public cloud control plane.

This is a source-level review, not a penetration test, runtime audit, or compliance
certification. Findings below are based on the inspected code and must be retested
against a pinned deployment artifact before release.

| Component | Observed behavior / concern | Cloud disposition | Admission requirements |
|---|---|---|---|
| `modules/api_server.py` | Exposes status, connection, scan, forensic, password, IOC, vulnerability, and honeypot routes without authentication; binds to `0.0.0.0`; scan route calls automatic blocklisting | **Prohibited from public exposure** | Replace with authenticated, role-scoped API; remove privileged actions; rate limits; audit trail; explicit authorization |
| `aegis_daemon.py` | Persistent host-oriented loop, periodic scans, local state/log assumptions | **Not a serverless function** | Dedicated isolated worker, least privilege, bounded jobs, shutdown handling, monitoring, explicit task allowlist |
| `install_service.sh` | Creates user systemd services, starts daemon/API, enables lingering | **Do not run in managed/serverless hosting** | Separate VM/container deployment design; signed release; service account; hardening; rollback and uninstall procedure |
| `modules/forensics.py` | Host data collection and shell-command execution | **No cloud request path** | Strictly scoped collection, no shell interpolation, consent/authority, data minimization, access controls, retention schedule, evidence integrity |
| `modules/ioc_scanner.py` | Host-oriented scanning and external/process/file inspection | **No public invocation** | Explicit authorized targets, bounded read-only scope, isolated worker, safe parsers, time/resource limits |
| `modules/vuln_scanner.py` | Local system and service inspection | **No public invocation** | Asset ownership verification, allowlisted scope, non-invasive checks, rate limits, worker isolation |
| `modules/honeypot.py` | Opens TCP listeners on configured interfaces/ports | **Not suitable for serverless** | Dedicated network segment, firewall review, abuse monitoring, legal review, isolated telemetry storage |
| `scheduler.py` | FastAPI + NATS; accepts task type and arbitrary payload; routes by task type/risk | **Not connected** | AuthN/AuthZ, schema allowlist, payload limits, queue ACLs, signed task envelope, replay protection, dead-letter policy, tenant isolation |

## Mandatory cloud boundary

The new `cloud_control_plane.py` intentionally imports none of these modules.
It exposes only a public liveness endpoint and two authenticated, static, read-only
PETS metadata routes. Do not add imports or route handlers for legacy components
without a separate threat model and test suite.

## Release gate for each legacy component

1. Identify the exact supported use case and authorized asset owner.
2. Remove shell execution where possible; otherwise use fixed argument arrays,
   no shell, strict allowlists, timeouts, and bounded output.
3. Separate control plane from worker and data plane.
4. Enforce identity, roles, least privilege, tenant isolation, and audit logging.
5. Ensure no endpoint can trigger blocking, scanning, listener creation, or host
   collection without an explicit, separately approved job.
6. Add unit, integration, abuse-case, and dependency tests.
7. Test resource ceilings, cancellation, retries, duplicate delivery, and rollback.
8. Complete privacy, retention, and incident-response reviews.
9. Verify the exact release artifact and its dependency inventory.
10. Obtain an independent security review before production admission.

## Known deployment blockers

- No verified cloud project is linked to this repository yet.
- No production secret configuration or identity provider has been provisioned.
- No durable database, evidence vault, queue, or isolated worker has been provisioned.
- No infrastructure-as-code, backup/restore drill, or disaster-recovery test has
  been completed.
- No independent penetration test or compliance assessment has been performed.

A green unit-test run for the new control plane does not clear these blockers.
