# PETS Universal Formula — Value and Monetization Ledger

The ValueLedger records validated positive outcomes, attribution, provenance,
rights status, and monetization stage. It is an append-only accounting record,
not a sales engine and not proof of intellectual-property ownership.

## Required distinctions

- Potential value: an estimate, not income.
- Under review: commercial and rights checks are pending.
- Commercialized: an authorized commercial use exists, but revenue is not
  necessarily realized.
- Revenue realized: requires an actual revenue amount.
- Not commercial: retained as a useful outcome without a commercial path.

Every record requires an outcome, provenance reference, attribution, rights
status, and timestamp. Reusing a record ID with identical content is
idempotent; changing a prior record is rejected. Database triggers prevent
updates and deletes.

Do not monetize private or sensitive personal information, confidential
records, third-party intellectual property without rights, or material whose
ownership/licensing status is unresolved. Route uncertain rights to human
review. The ledger does not contact customers, publish assets, issue licenses,
or process payments.

Estimated value and realized revenue are reported separately. Currency and
valuation method should be recorded consistently by the calling application.