# AEGIS GitHub IP SHIELD

This repository-level extension complements AEGIS OMEGA IP SHIELD.

## Operation

- Runs on pushes, pull requests, manual dispatches and a weekly schedule.
- Inventories tracked files at the triggering commit and records Git blob IDs, sizes and SHA-256 fingerprints.
- Records the triggering commit/tree/ref and up to 500 commit metadata entries.
- Hashes commit email addresses rather than publishing raw addresses.
- Uploads a JSON report and checksum as a GitHub Actions artifact (90-day retention).
- For non-PR runs, copies the report to the `ip-shield-ledger` branch.
- Does not upload source contents, modify source branches, alter permissions or execute repository code.

## Enablement

Merge this workflow and `tools/ip_shield_github.py` into the default branch. GitHub Actions must be enabled. The workflow token needs **Contents: Read and write** permission to maintain the ledger branch. Organization or repository policy may block that write; artifact upload may still work.

After merge:
1. Pushes to branches other than `ip-shield-ledger` generate snapshots.
2. Pull-request runs generate an artifact but do not write the ledger.
3. A weekly scheduled run snapshots the default branch.
4. Manual runs are available under Actions → AEGIS GitHub IP SHIELD → Run workflow.

Verify an exported report with `sha256sum -c ip-shield-report.json.sha256`.

## Provenance and legal limits

Git author names and timestamps are self-declared commit metadata, not verified identity or independently certified time. SHA-256 identifies snapshot bytes but does not prove originality, ownership or infringement. The runner clock is not a trusted timestamp authority.

The ledger branch is versioned evidence, not immutable storage: administrators can rewrite or delete it. Keep independent backups and consider GitHub rulesets/branch protection.

Third-party, joint, licensed and AI-assisted contributions retain their applicable rights. This tool does not register copyright or patents, prevent copying, claim rights over abstract ideas or revoke third-party rights.

## Scope

This workflow covers only this repository and refs that trigger it. It does not silently install into every repository on the GitHub account or monitor repositories where it has not been configured. Additional repositories need their own authorized installation.
