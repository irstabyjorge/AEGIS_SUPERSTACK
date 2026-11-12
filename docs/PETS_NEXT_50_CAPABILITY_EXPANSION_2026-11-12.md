# PETS Next 50 Capability Expansion
**Date:** 2026-11-12  
**Target:** PETS / AEGIS unified architecture  
**Status:** Proposed architecture backlog — not yet implemented or runtime-verified  
**Source boundary:** Derived from the currently recovered AEGIS/PETS records and the 2026-11-12 recovery register. Preserve V2, V3, V5 and V5.1 originals unchanged.

## Operating contract
This is a versioned proposal for additive integration. Each capability must pass compatibility, privacy, safety, provenance and test gates before implementation. “Accepted for planning” does not authorize destructive changes, external disclosure, account-security changes, autonomous actions, or deployment. No component is considered installed merely because it appears in this catalog.

## 50 proposed enhancements

### A. Governance, provenance and asset integrity
1. **Canonical asset registry** — one index of source path, owner/repository, version, digest, license, dependencies and recovery date.
2. **Immutable source snapshots** — retain original archives and source exports; perform all transformations on copies.
3. **Content-addressed identity** — use SHA-256 digests to detect duplicates and changes without relying on filenames.
4. **Provenance graph** — link each component to source records, commits, derived artifacts and validation results.
5. **Evidence-class labels** — distinguish direct observation, source-reported claim, inference, hypothesis and unresolved item.
6. **Version lineage map** — preserve V2/V3 registry and V5/V5.1 archive relationships without overwriting predecessors.
7. **Change decision records** — record rationale, author, date, scope, tests and rollback plan for every accepted change.
8. **License and attribution ledger** — record third-party origin and usage terms before redistributing code or assets.
9. **Recovery completeness scorecard** — measure coverage of known sources and explicitly list inaccessible or missing sources.
10. **Reproducible integrity reports** — regenerate checksums, archive tests and database integrity findings from read-only inputs.

### B. Architecture and interoperability
11. **Capability interface contract** — define stable input/output schemas, error types and version negotiation for modules.
12. **Adapter boundary layer** — isolate legacy module interfaces behind small, testable adapters.
13. **Dependency manifest** — declare runtime, library, platform and optional-service dependencies with pinned versions.
14. **Compatibility matrix** — track supported Android, Linux, Windows, Python and Node versions based on actual tests.
15. **Plugin lifecycle model** — define discovery, validation, enablement, disablement and removal states.
16. **Capability registry API** — expose read-only search and metadata queries over registered modules.
17. **Event envelope standard** — define timestamp, source, event type, correlation ID and integrity metadata.
18. **Schema migration policy** — require additive migrations, backups and tested rollback for persistent data.
19. **Local-first execution profile** — default to offline operation and require explicit opt-in for network-dependent features.
20. **Degraded-mode behavior** — document safe behavior when optional tools, models or connectors are unavailable.

### C. Security, privacy and safety
21. **Threat model per module** — document assets, trust boundaries, misuse cases and mitigations before implementation.
22. **Least-privilege permissions** — grant each module only the minimum local or connector access required.
23. **Secrets exclusion scanner** — detect likely credentials in commits and generated artifacts; never print secret values.
24. **Local data classification** — label public, internal, private and highly sensitive records with handling rules.
25. **Privacy-preserving logs** — redact identifiers and sensitive payloads; retain only operational metadata where possible.
26. **Human approval gates** — require explicit review before external writes, exports, publication or irreversible actions.
27. **Safe network policy** — deny by default; allow only documented, user-approved endpoints for a specific task.
28. **No covert monitoring policy** — prohibit hidden tracking, interception, jamming, implant interference or unauthorized surveillance.
29. **Child-safety boundary** — support aggregate, public-interest safeguarding information; never locate or profile individual minors.
30. **Incident response playbook** — define containment, evidence preservation, credential rotation by the owner and recovery steps.

### D. Quality, testing and reliability
31. **Unit-test baseline** — require tests for parsers, validators, adapters and state transitions.
32. **Integration contract tests** — validate module boundaries with synthetic, non-sensitive fixtures.
33. **Cross-platform CI matrix** — run supported OS/runtime combinations and publish the exact tested matrix.
34. **Static analysis gate** — check formatting, type consistency, dependency risks and unsafe patterns.
35. **Software bill of materials** — generate and retain an SBOM for each release candidate.
36. **Reproducible build metadata** — record toolchain versions, source commit and artifact digest.
37. **Artifact verification gate** — verify package signatures/checksums and inspect archive contents before use.
38. **Failure-injection tests** — test missing files, malformed input, unavailable dependencies and interrupted writes.
39. **Backup/restore drills** — periodically test restore procedures using copies and non-production data.
40. **Release readiness checklist** — require tests, provenance, privacy review, rollback plan and maintainer approval.

### E. Knowledge, research and user workflows
41. **Source quality rubric** — assess authority, recency, methodology, conflicts and reproducibility without treating search rank as proof.
42. **Citation/provenance binding** — attach source references to factual claims in research outputs.
43. **Hypothesis ledger** — keep unverified interpretations separate from established observations and tested conclusions.
44. **Research question tracker** — record question, scope, search strategy, findings, gaps and next review date.
45. **Document ingestion quarantine** — parse untrusted files as data; never execute embedded scripts or macros during ingestion.
46. **Forensic timeline workspace** — organize user-provided records chronologically while preserving original timestamps and source context.
47. **Evidence export manifest** — include hashes, filenames, acquisition notes and transformations with each authorized export.
48. **Accessibility and localization layer** — support Spanish/English labels, readable contrast, keyboard navigation and clear error messages.
49. **Termux companion profile** — provide optional, transparent local setup guidance and read-only diagnostics; no hidden persistence or privileged actions.
50. **PETS health dashboard** — report component status as proposed, recovered, installed, tested or verified, with last-check time and evidence link.

## Acceptance and implementation gates
A proposal advances through: **proposed → specified → reviewed → implemented → tested → independently verified**. Record each transition and its evidence. A failed gate returns the component to proposed or blocked; do not relabel it as active.

## Current known blockers and constraints
- The Android bridge source archive previously failed ZIP validation; recover a valid source archive or reconstruct from independently verified source files before building.
- Azure deployment remains unconfigured and is not part of this proposal.
- Private Library evidence must not be copied into public repositories.
- No unknown binary, installer or script is to be executed as part of catalog integration.
- Keep the `jefeaguila` GitHub account untouched; operational repository work remains under `irstabyjorge`.

## Next implementation sequence
1. Reconcile this backlog against the V3 registry and existing module inventory.
2. Mark existing capabilities as recovered only where source artifacts and digests support that status.
3. Select low-risk documentation and validation work first (items 1–10, 13–14, 31–40).
4. Add tests and CI before any runtime integration.
5. Review each proposed module for privacy, safety, licensing and dependencies.
6. Publish changes as a reviewable pull request; do not merge or deploy automatically.
