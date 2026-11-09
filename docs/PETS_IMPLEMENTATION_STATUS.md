# PETS implementation status — development branch

This is a development implementation, not a production release.

## Implemented in source

- Local SQLite evidence ledger with append-only database triggers and SHA-256 hash-chain verification.
- Deny-by-default role/permission policy.
- Read-only provider adapter contract and deterministic fixture adapter.
- Unit tests for ledger append/verification, mutation rejection, RBAC and adapter write denial.

## Important limitations

- SQLite hash chaining detects record modification but does not provide an independently anchored timestamp or prevent an administrator with filesystem access from replacing the entire database. Production needs encrypted storage, protected backups, external checkpointing and key management.
- The RBAC module is a policy library, not a complete identity provider. The API must obtain roles from trusted server-side authentication, never from client-supplied fields.
- Provider adapters are contracts and fixtures only. ChatGPT-hosted connectors do not automatically become API credentials or runtime integrations for a deployed service. Each provider requires an approved API, credential provisioning, terms review, rate-limit handling and provider-specific tests.
- No Android APK has been built or installed by this commit. The existing PR #8 reports an Android CI source-bundle failure; repair and a physical-device install test remain outstanding.
- No CI workflow was run by these commits. Run the repository's full CI and the new tests before merging.
- No Vercel project, database, production secrets, domain, or production deployment is created by this change.

## Production gate

Do not deploy until identity/authentication, encrypted persistent storage, backup/restore, migration strategy, provider adapters, security review, CI, Android build/install validation, monitoring, rollback, and data-retention policy have been tested and approved.
