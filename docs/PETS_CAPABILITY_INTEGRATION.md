# PETS / AEGIS Capability Integration

**Target repository:** `irstabyjorge/AEGIS_SUPERSTACK`  
**Working branch:** `aegis-pets-cloud-integration`  
**Baseline:** `PETS_AEGIS_SCHEMA_INTEGRATION_MANIFEST v8.0.0`  
**Deployment status:** Development only; production deployment is disabled.

## Purpose

This document records the capabilities discoverable through the ChatGPT host and their current relationship to the AEGIS_SUPERSTACK repository. It does not imply that host tools have been installed as services in the repository.

## Capability planes

| Plane | Available capability | Current status | Repository adapter |
|---|---|---|---|
| Public research | Web search and source review | Host available | Pending |
| Academic evidence | Consensus, PubMed, ClinicalTrials.gov, Scite, CoChat | Host tools listed | Pending |
| AI/ML discovery | Hugging Face model, dataset, Space and paper discovery | Host tools listed | Pending |
| Source control | GitHub repository and branch operations | Read access verified on target branch | Pending |
| Knowledge archive | ChatGPT Files search/read | Read access verified for project manifest | Pending |
| Documents | Adobe Acrobat and Files workflows | Host tools listed | Pending |
| Local execution | Android, Termux, Windows and Linux | Not connected to this repository runtime | Not available |

## Integration lifecycle

Use the following states consistently:

1. `discovered` — a tool or capability has been identified.
2. `host_tools_listed` — the host exposes a tool; no repository adapter is implied.
3. `connected_read_verified` — a real read operation succeeded.
4. `adapter_implemented` — repository-side adapter code exists.
5. `configured` — required non-secret configuration is present.
6. `tested` — automated tests pass.
7. `validated` — behavior, permissions, provenance and failure modes have been reviewed.
8. `pinned` — a version and dependency set are recorded for reproducibility.

Never promote a capability to a later state without evidence.

## Required adapter contract

Every future adapter must define:

- Provider and operation identifiers.
- Input and output schemas.
- Authentication mechanism, with secrets injected at runtime only.
- Permission scope and data classification.
- Timeout, retry and rate-limit behavior.
- Provenance fields and source citations.
- Audit event format.
- Failure-closed behavior.
- Unit and integration tests.
- Disable and rollback procedure.

## PETS security invariants

- Default-deny and read-only by default.
- No credentials or access tokens in source files, manifests or logs.
- TLS verification remains enabled.
- No automatic execution of generated code.
- No autonomous privilege escalation or security-policy self-modification.
- Human approval for external writes, publication, deployment and state-changing actions.
- Preserve original files and source claims.
- Separate verified evidence, inference and speculative concepts.
- Keep personal evidence local/private unless a specific, authorized transfer is approved.
- Child-protection research uses aggregated public statistics only; no identification or localization of individual minors.
- Security tooling is limited to defensive, authorized, bounded assessments; no stealth, interception, jamming, tracking or destructive response automation.

## Verified in this integration pass

- GitHub repository `irstabyjorge/AEGIS_SUPERSTACK` was found in the connected installation.
- Branch `aegis-pets-cloud-integration` was found.
- `cloud_control_plane.py` and `tests/test_cloud_control_plane.py` were read from that branch.
- `integration_registry.json` was read and updated on the working branch.
- The project manifest was retrieved from the Files library.

## Not yet implemented or claimed

- Repository-side adapters for Consensus, Hugging Face, PubMed, ClinicalTrials.gov, Scite, CoChat or document services.
- Persistent append-only evidence storage.
- Role-based access control.
- Worker queues and scheduler integration.
- Local Android/Termux or desktop installation.
- Staging or production deployment.
- Independent rerun of the previously reported test suite in this pass.

## Next engineering sequence

1. Add schema validation for the integration registry.
2. Add provider adapter interfaces with mock implementations only.
3. Add provenance and append-only audit event schemas.
4. Add permission and data-classification tests.
5. Add adapter-specific read-only tests.
6. Run CI and inspect the branch diff.
7. Open a draft pull request for review; do not merge or deploy automatically.
