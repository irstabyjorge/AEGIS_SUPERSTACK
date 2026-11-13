# PETS / AEGIS Connector Integration Registry

**Status:** additive integration registry and operating contract  
**Baseline:** `main` at the time this branch was created  
**Change policy:** additive-only; no existing assets, settings, permissions, model weights, datasets, or repository visibility are modified.

## 1. Purpose

This document records the connector surfaces available to the PETS master architecture and AEGIS OMEGA / IP Shield. It distinguishes a connector that has authenticated successfully from a production integration that has been implemented, tested, and deployed inside a runtime.

The current connected tools are exposed through the ChatGPT connector environment. Their availability does **not** mean that this repository's local Python/JavaScript services can call them directly. A local runtime adapter requires a separately implemented, reviewed, configured, and tested API/MCP client.

## 2. Verified connector status (2026-11-13)

| System | Observed status | Verified capability / scope | Limitation / next step |
|---|---|---|---|
| GitHub | Authenticated | Repository listing succeeded for `irstabyjorge`; 29 repositories were returned; current account reported admin/push access on listed repositories | Repository-level CI, branch rules, and artifact attestations must be checked separately; no collaborator invitations performed |
| Hugging Face | Authenticated as `AEGISGODMODE` | Read scopes: `read-mcp`, `read-repos`, plus profile/openid/jobs; organization `AEGISWALLS` role reported as admin | No write scope in the current OAuth credential; inventory is read-only; do not attempt publishing or settings changes |
| Consensus | Connector call succeeded | Academic search returned research records | Fetch each result before citing; a search result is not a full-text paper; use source IDs and retrieval dates in research provenance |
| Dropbox | Authenticated as `jefeaguila777@gmail.com` | Root listing succeeded; root listing page reported `has_more=false` | No PETS evidence archive folder was created; do not move or copy personal files without an explicit destination and scope |
| SharePoint / OneDrive | Authenticated as `senorparedes@outlook.com` | Drive discovery returned one visible drive named `OneDrive` | This verifies the connected OneDrive drive only, not every SharePoint site/library in the tenant |
| Box | Not verified connected | Previously surfaced as an optional connector suggestion | User must complete connection in the product UI; do not claim connected until an authenticated call succeeds |
| PETS Research Intelligence v0.3.0 | Project-reported identifier only | Prior project context reports release label `v0.3.0` and reference `pluginrel_6af56dd9c044819190773fc9c60857aa` | Plugin dependency lookup did not resolve that reference as a public global plugin; installation, deployment, and live integration are unverified |

## 3. Target architecture

```text
PETS Master Registry
  ├── GitHub adapter (repositories, commits, PRs, workflow artifacts)
  ├── Hugging Face adapter (read-only repo metadata and revisions)
  ├── Consensus adapter (search -> fetch -> evidence record)
  ├── Dropbox adapter (approved evidence archive)
  ├── Microsoft Graph adapter (visible OneDrive / approved SharePoint libraries)
  └── Box adapter (pending user connection)
          |
          v
AEGIS OMEGA / IP Shield
  ├── provenance normalization
  ├── manifest generation and SHA-256 (only for bytes actually retrieved)
  ├── append-only, hash-chained audit ledger
  ├── integrity verification
  ├── coverage / omission / error register
  └── human review and approval gates
```

The diagram is a target integration design, not a claim that all adapters are deployed in the local runtime.

## 4. Common evidence record

Each captured item should record, when available:

- `evidence_id`: stable, locally generated identifier;
- `source_platform`, `source_account`, `owner_or_namespace`;
- `repository_or_drive_id`, `item_id`, `path`, `canonical_url`;
- `source_revision`, `parent_revision`, `provider_blob_id`, `provider_digest`;
- `sha256`: only after the original bytes are retrieved and independently hashed;
- `captured_at_utc`, `collection_method`, `collector_version`;
- `license_metadata`, `access_classification`, `authorization_basis`;
- `status`: observed, partial, inaccessible, permission_denied, not_found, unsupported, rate_limited, transient_error, integrity_mismatch, pending_review;
- `custody_events`, `manifest_digest`, `verification_result`, `limitations`.

Keep observed platform metadata, user-supplied statements, inferences, hypotheses, symbolic concepts, and unknowns in separate fields or classifications.

## 5. Connector operating contracts

### GitHub
- Begin with repository and revision discovery; capture default branch, commit SHA, visibility, and permissions as observed.
- Use pull requests for proposed repository changes; never force-push or overwrite existing files.
- Record workflow run IDs, job outcomes, artifact identifiers, and attestation references when available.
- Do not invite collaborators or change permissions without an exact identity, least-privilege role, and resource scope.

### Hugging Face
- Use read-only discovery for models, datasets, and Spaces.
- Record repository type, owner, revision, file metadata, gating/visibility, and provider LFS digest when exposed.
- Do not publish, delete, alter gating, or change repository settings with the current read-only credential.
- Do not equate a provider digest or Git blob ID with an independently computed SHA-256.

### Consensus
- Treat search as discovery, not evidence verification.
- Fetch the selected paper record before citing or relying on bibliographic metadata.
- Store exact paper ID, canonical URL, authors, year, journal, DOI when present, retrieval timestamp, and the question/query used.
- Clearly label abstracts and summaries; do not imply full-text review where full text was unavailable.

### Dropbox and Microsoft Graph
- Inventory the intended destination before writing.
- Create a dedicated archive folder only after its exact path/library is approved.
- Preserve source files; copy rather than move when an approved backup is needed.
- Do not create public/shared links or invite recipients by default.
- Record version IDs, file IDs, modified timestamps, and permission scope where available.

### Box
- Keep in pending state until the user completes the connector authorization.
- After connection, verify identity and available storage scope before creating folders or uploading evidence.

## 6. Safe orchestration sequence

1. Discover source accounts and enumerate in-scope repositories/items.
2. Record pagination and every omission/error; never label partial scans complete.
3. Normalize metadata into the common evidence record.
4. Retrieve bytes only where authorized and necessary; independently compute SHA-256.
5. Write a new, uniquely named manifest and append-only ledger event.
6. Verify the manifest and ledger before any archive operation.
7. Copy only approved evidence into a dedicated archive destination.
8. Re-read archived objects and verify available version/digest metadata.
9. Produce a coverage report distinguishing complete, partial, blocked, and pending.
10. Require human review for external sharing, legal conclusions, publication, or rights claims.

## 7. Explicit non-goals and safety boundaries

- No autonomous access escalation, credential harvesting, covert collection, or surveillance.
- No automatic publication of private or sensitive material.
- No external invitations or broad sharing based on unspecified recipients.
- No destructive response, auto-revert, or remote settings changes.
- No claim that a hash proves authorship, ownership, originality, infringement, or creation date.
- No claim that a connector is deployed in the local runtime solely because its ChatGPT connector is authenticated.

## 8. Current activation summary

**Operational in the connected ChatGPT environment:** GitHub read/write operations within the authenticated account's granted repository permissions; Hugging Face read-only; Consensus search/fetch; Dropbox; OneDrive through Microsoft Graph.

**Pending:** Box connection; local-runtime adapters; a dedicated approved evidence archive destination; end-to-end integration tests; CI attestation verification; confirmation of the PETS Research Intelligence plugin package/release.

**Completion rule:** The integration is complete only when the adapter is implemented in its target runtime, permissions are least-privilege, tests pass, provenance is recorded, and the resulting artifact can be independently verified.
