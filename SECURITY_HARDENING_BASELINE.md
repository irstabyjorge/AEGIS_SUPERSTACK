# AEGIS/PETS Security Hardening — Universal Formula Baseline

Status: proposed baseline on an isolated security branch. This document does not certify the repository or connected accounts as secure.

## Universal Formula control cycle

Observe → Classify → Constrain → Reason → Validate → Authorize → Act → Record → Learn.

All remediation must be bounded, traceable, reversible, and independently verifiable. Keep conceptual architecture separate from deployed controls.

## Confirmed observations from the inspected source files

1. Several Python modules use `subprocess.run(..., shell=True)`, including `aegis_real.py`, `aegis_unified.py`, `modules/vuln_scanner.py`, `modules/forensics.py`, `modules/password_audit.py`, and `modules/ioc_scanner.py`. These are review targets, not proof of an exploitable vulnerability. Each call needs input-flow review before conversion to argument arrays.
2. `aegis_real.py` generates a Fernet key and reports `stored: False`. A generated-but-unpersisted key cannot support later decryption. Do not replace or rotate any production key until a recovery plan exists.
3. The inspected Hugging Face workflow uses `contents: read` and separates tests from an authenticated read-only inventory.
4. The inspected `hub-docs` TruffleHog workflow checks full Git history and uses `contents: read`. Execution success and repository-wide coverage remain unverified.
5. The IP SHIELD workflow writes snapshots to a ledger branch and therefore needs write access. Do not remove that permission without redesigning and testing the ledger publishing mechanism.

## Changes in this branch

- Adds `tools/security_static_audit.py`, a read-only Python AST heuristic that reports explicit `shell=True` calls.
- Adds `.github/workflows/security-static-audit.yml` with read-only repository permissions, pinned action SHAs, disabled checkout credential persistence, and a 30-day report artifact.
- This audit is advisory: it does not prove exploitability, inspect Git history, inspect secret values, or alter the source tree.

## Remediation sequence

1. Review each flagged subprocess call and its input sources. Convert safe cases to argument arrays with `shell=False`; preserve legitimate shell pipelines only where required and with fixed commands and strictly validated inputs.
2. Add tests for command construction, path handling, timeouts, and error behavior.
3. Define key lifecycle: generation, encrypted storage, access control, backup, recovery test, rotation procedure, and audit event. Never log key material.
4. Run secret scanning over all branches and history; rotate only confirmed exposed credentials, after mapping dependencies.
5. Pin every third-party Action to a verified full commit SHA and review release provenance.
6. Keep `GITHUB_TOKEN` permissions job-scoped and least-privilege. Preserve write access only for jobs that demonstrably need it.
7. Enable branch protection/rulesets, required reviews, and required checks where the account plan and repository settings support them.
8. Verify signed release artifacts, APK manifest permissions, signing certificate fingerprints, and reproducible build provenance.
9. Test backups by restoring into an isolated location and comparing hashes.
10. Re-run the audit and retain reports with timestamp, commit SHA, SHA-256 digest, and reviewer decision.

## Explicitly not verified by this repository-only change

- Personal access token inventory/revocation, account sessions, MFA, recovery codes, OAuth approvals, or organization policy.
- GitHub Actions secrets/variables values or their rotation.
- Branch protection/rulesets and collaborator membership.
- Railway deployment health or secret configuration.
- Hugging Face account permissions and token scopes.
- Local device firewall, OS patch level, Android app installation state, or backup restoration.
- Any claim of compromise or attribution.

## Evidence requirements

For each change, record source commit, branch, file path, diff, author, UTC timestamp, validation result, reviewer, and rollback procedure. Do not include credentials, private keys, personal data, or raw secret values in reports.
