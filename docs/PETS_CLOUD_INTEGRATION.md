# AEGIS/PETS Cloud Integration — Development Branch

**Status:** development only; not production deployed.

## Integration boundary

This branch adds `cloud_control_plane.py`, a small WSGI control-plane entry point.
It is intentionally separate from the existing host-oriented AEGIS services.

The first PETS integration is a governance and evidence-policy contract, not a
claim that a complete evidence-management system has been implemented. The
control plane does not collect host data, accept evidence uploads, run scanners,
start listeners, inspect processes, change firewall state, or launch background
daemons. The evidence-policy endpoint describes the proposed provenance fields
for future evidence records; it does not create or retain those records.

## Routes

| Method | Route | Access | Behavior |
|---|---|---|---|
| GET | `/healthz` | Public | Minimal liveness response |
| GET | `/api/v1/pets/status` | Bearer token | Static read-only service status |
| GET | `/api/v1/pets/evidence-policy` | Bearer token | PETS evidence and governance contract |

All other routes are not exposed. Non-GET methods are rejected. The protected
routes fail closed unless `AEGIS_CLOUD_API_TOKEN` is configured with at least
32 characters. Use a unique, randomly generated secret stored in the hosting
provider's secret manager; never commit it to Git.

## Local verification

Requires Python 3.10+ and no third-party packages for the control-plane tests:

```sh
python -m unittest discover -s tests -v
python -m py_compile cloud_control_plane.py
```

## Deployment constraints

- No production deployment is authorized by this branch.
- Do not run `install_service.sh` or `aegis_daemon.py` in a serverless runtime.
- Do not expose the legacy `modules/api_server.py` publicly: its existing
  routes are unauthenticated and include host-sensitive operations.
- Do not connect public endpoints to the legacy scanners, forensics, honeypot,
  scheduler, or blocklist routines until they have separate authorization,
  isolation, privacy, and security reviews.
- No automatic blocking, firewall edits, remote scanning, or autonomous
  remediation is part of this control plane.
- Use TLS at the hosting edge, strict secret management, least privilege,
  request logging with sensitive-data redaction, and tested backups before any
  future staging or production proposal.
- A persistent worker, queue, and durable evidence store are intentionally
  not provisioned here. Their requirements and threat models must be designed
  and reviewed before implementation.

## Repository and license note

The repository's `LICENSE` states that commercial use requires a separate
commercial license. Review that restriction before using this software in a
revenue-generating or organizational environment. This development branch
does not grant or imply any additional license rights.

## Acceptance boundary

Passing the included tests establishes only the tested behavior of this
isolated WSGI control plane. It does not certify the full AEGIS SUPERSTACK,
legacy modules, hosting configuration, or production security.
