# PETS / AEGIS IP Shield — Coverage Charter

**Status:** technical provenance and integrity policy; not an insurance contract, surety bond, legal opinion, copyright registration, or guarantee of exclusivity.

## 1. Coverage intent

Treat every included contribution as a protected project asset for inventory, attribution, provenance, integrity monitoring, and evidence preservation. Coverage follows the recorded asset and its version, not merely a repository name.

PETS remains the master architecture. AEGIS OMEGA / IP Shield is the cross-cutting protection layer. Hugging Face models, datasets, Spaces, GitHub source, documentation, configuration, schemas, test suites, workflows, generated manifests, and approved derivative artifacts may be inventoried when their repository and revision are explicitly in scope.

## 2. Additive-only preservation rule

- Never delete, rename, overwrite, force-push, or replace an existing asset as part of an IP Shield operation.
- Add new manifests, snapshots, audit events, coverage records, and documentation alongside existing material.
- If a target path already exists, preserve it and create a new versioned evidence record; do not silently update it.
- A failed, partial, inaccessible, or unverified item remains recorded as such. It is never silently omitted.
- Merges must preserve source history and identify the base revision, incoming revision, merge commit, and conflicts/resolutions.
- No automated workflow may change repository visibility, access control, billing, model weights, dataset contents, Space runtime settings, or licensing.

## 3. Evidence and attribution record

For each asset/version, record where available:
- platform, owner/namespace, repository ID, repository type, path, revision/commit, and parent/base revision;
- file size, platform blob identifiers, platform-provided LFS digests, and independently computed SHA-256 only when bytes were actually retrieved and hashed;
- contributor identity as declared by the platform, commit/event timestamps, source URL, collection time, and collection method;
- license and terms metadata exactly as observed, with unknown or conflicting rights marked for review;
- manifest digest, evidence location, custody transfers, verification results, and known limitations.

Separate **observed facts**, **user-supplied claims**, **inferences**, **hypotheses**, **symbolic concepts**, and **unknowns**. Never promote an inference into a verified fact.

## 4. Errors, omissions, and exceptions register

Every inventory or integration run must account for each requested namespace and asset class. Record:
- successful inventory;
- not found / inaccessible / permission denied;
- unsupported endpoint or repository type;
- pagination incomplete or rate-limited;
- transient network or API error;
- metadata missing, stale, or inconsistent;
- integrity mismatch, unexpected revision, or changed file list;
- skipped item and the explicit reason;
- operator action needed and review status.

A run is **complete** only when all requested owners, repository types, pages, and assets have terminal statuses. A successful command with partial coverage is still **partial**, never green. Error records should retain safe diagnostic categories and correlation IDs, not credentials, private tokens, or unnecessary personal data.

## 5. Integrity and monitoring controls

- Canonical JSON manifests with SHA-256 digest.
- Append-only, sequence-checked, hash-chained audit ledger.
- Verify the existing ledger before appending; fail closed on corruption.
- Verify every manifest and inventory-index digest before audit or publication.
- Capture revision drift and file-list changes as new evidence; never auto-revert remote changes.
- Prefer independent, separately controlled evidence backups and trusted timestamps.
- Report algorithm and provenance accurately: Git blob IDs are SHA-1; Hub LFS digests are provider-supplied metadata unless independently recomputed from downloaded bytes.

## 6. IP coverage and claim handling

For a suspected unauthorized reuse, omission, attribution error, license conflict, or unexplained change:
1. Preserve the current source and evidence; do not confront, accuse, or modify the remote asset.
2. Record the exact asset, version, URL, observation time, and reproducible comparison.
3. Preserve relevant licenses, platform terms, contribution records, and permission documents.
4. Classify the issue as confirmed technical discrepancy, possible rights issue, or unresolved report.
5. Require human review before contacting a platform, contributor, institution, or legal representative.
6. Record the resolution and any corrected attribution as a new append-only event.

## 7. Exclusions and limitations

The shield cannot prevent copying, platform-side deletion, account compromise, administrator actions, or lawful reuse under applicable licenses. A hash proves byte-level identity relative to the hashed input, not authorship, ownership, originality, date of creation, or infringement. Metadata-only inventories do not prove the contents of model weights or datasets. The system does not guarantee recovery or indemnification and is not an insurance policy or legally enforceable bond.

## 8. Safe operation policy

Use only accounts, repositories, assets, and data the operator owns or is authorized to inspect. Use read-only credentials for scheduled inventory. Keep write credentials out of CI and out of logs. Any remote write requires a separate explicit approval, a verified evidence baseline, a reviewed diff, and a no-overwrite check. No covert collection, unauthorized access, mass surveillance, credential harvesting, or destructive response is permitted.

## 9. Release gate

Do not label protection as deployed or complete until:
- tests pass in CI;
- the PR diff is reviewed and merged;
- all in-scope repositories have an inventory status;
- the baseline evidence is verified and independently backed up;
- limitations and exceptions are reported;
- remote write paths remain disabled unless separately authorized.
