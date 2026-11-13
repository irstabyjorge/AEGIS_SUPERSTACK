# PETS/AEGIS Hugging Face Protection Security Model

## Threat model
This subsystem protects integrity and traceability of repository metadata and manifest records. It is not an anti-copying system and cannot stop a repository owner, platform administrator, or authorized collaborator from changing or deleting remote content.

## Credential handling
- Hugging Face credentials are supplied only through the local Hugging Face credential store or a GitHub Actions secret named HF_TOKEN.
- Never place tokens in source, command-line arguments, artifacts, logs, issues, or chat.
- The scheduled inventory job uses the token for read-only Hub API operations.
- Pull-request jobs do not receive HF_TOKEN.
- No workflow automatically publishes or overwrites remote files.
- Rotate a token immediately if it is exposed; scope it to only the repositories required.

## Protection layers
1. Repository revision capture.
2. File path, size, Git blob ID and Hub-provided LFS SHA-256 metadata capture.
3. Canonical SHA-256 digest of each generated manifest.
4. Local hash-chained audit ledger.
5. Scheduled drift comparison can be added after a baseline inventory is reviewed.
6. GitHub Actions artifacts retain evidence for 30 days; download and preserve important evidence independently.

## Integrity semantics
Git blob IDs use SHA-1 and are not SHA-256. LFS SHA-256 values are reported as Hub-provided metadata. This implementation does not download every model weight or dataset to independently hash all bytes. Hash chains are tamper-evident, not immutable against full control of the storage location. Use an independent trusted timestamping and separately controlled evidence store for stronger evidentiary assurance.

## Safe defaults
Read-only inventory is the only automated Hub operation. Publishing requires a separate explicit local command and a write-scoped token. Existing manifest paths are skipped; this release does not overwrite them.


## Additive-only evidence preservation
- Every inventory execution is written to a unique `run-<UTC timestamp>` directory.
- Existing evidence files are never replaced. The JSON writer fails if its destination already exists.
- Each run reports `complete` only when every discovered repository was inventoried; otherwise it reports `partial`.
- Audit and publish require every manifest to verify and the index digest to be anchored in a valid hash-chained ledger.
- A missing, malformed, or unanchored index fails closed.
- See `docs/PETS_AEGIS_IP_SHIELD_COVERAGE_CHARTER.md` for coverage, exceptions, omissions, attribution, and claim-handling policy.

## Bond-like coverage meaning
"Coverage" means technical recording and integrity monitoring of declared project assets. It is not an insurance policy, surety bond, indemnity, copyright registration, or guarantee against copying, platform loss, or infringement. Rights and license questions require qualified human/legal review.
