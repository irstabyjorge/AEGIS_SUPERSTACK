# PETS/AEGIS Conversation-by-Conversation Knowledge & IP Protection Protocol

Status: proposed operating protocol; documentation only.
Owner/author attribution: preserve the repository's existing author and copyright notices. This document does not independently establish legal title or register intellectual property.
Applies to: each source conversation, attachment, code artifact, design, formula, decision, and derivative record admitted into the PETS/AEGIS knowledge base.

## 1. Governing rule

PETS is the master activation and orchestration system. The Universal Formula is its objective-directed reasoning framework. Every source conversation is processed as a distinct, traceable unit before its knowledge is mapped into PETS/AEGIS modules.

No conversation is silently overwritten, merged destructively, or treated as fully reviewed merely because a summary exists.

## 2. Per-conversation record

Create one record per conversation with these fields:

- Stable source ID and original conversation URL or export filename, when available.
- Original timestamp/time zone, if present in the source.
- Source integrity: original file hash (SHA-256) when bytes are available; otherwise mark hash as unavailable.
- Coverage: complete, partial, excerpt, summary-only, inaccessible, or pending.
- User-originated material: ideas, requirements, decisions, original text, and explicit instructions.
- Assistant-originated material: suggestions, generated drafts, hypotheses, and code proposals.
- Adopted decisions: only items explicitly accepted by the owner.
- Artifacts: file paths, repository URLs, commit SHAs, attachment references, and their own hashes where available.
- IP/provenance classification and any third-party material or license constraints.
- Formula mapping: objective O, current state Z, constraints/context C, history/provenance H, and relevant transformation/evaluation dimensions.
- PETS/AEGIS destination module(s).
- Verification status, reviewer/date, unresolved questions, and next action.

Do not invent missing IDs, dates, source files, hashes, authorship, or evidence.

## 3. Ownership and IP safeguards

- Preserve the owner's existing copyright and attribution notices in source files and derivative documentation.
- Record authorship claims as claims unless supported by source history, contemporaneous records, contracts, or other evidence.
- Separate owner-created material from assistant-generated material, third-party content, open-source components, and jointly authored contributions.
- Record license, permission, and attribution obligations before incorporating third-party material.
- Do not remove attribution, strip metadata, falsify timestamps, or represent generated content as independently authored source material.
- Keep original source artifacts unchanged; create additive derivatives and link them to their source.
- Keep sensitive source conversations private by default. Do not publish personal data, credentials, private correspondence, or confidential attachments.
- Do not send material to external repositories, services, collaborators, or public links unless the owner explicitly authorizes that specific disclosure.
- Hashes support integrity checking; they do not by themselves prove authorship, ownership, creation date, or legal priority.
- Maintain an evidence trail for each transformation: input IDs, output IDs, tool/process version, timestamp, and validation result.

## 4. Clean integration workflow

For each conversation:

1. Acquire the original source or explicitly record why it is unavailable.
2. Preserve it unchanged and calculate a cryptographic hash when possible.
3. Extract claims and content into separate epistemic classes: verified fact, user assertion, explicit decision, assistant proposal, inference, hypothesis, and symbolic concept.
4. Identify duplicate or conflicting passages without deleting either source.
5. Link every extracted item to its source location or mark its source locator unavailable.
6. Map accepted knowledge to the Universal Formula and PETS/AEGIS module registry.
7. Run safety, privacy, license, security, and provenance checks.
8. Produce a reviewable proposed integration.
9. Admit it to the canonical knowledge base only after the owner's acceptance or a clearly documented pre-authorized rule.
10. Record status and retain the original.

## 5. Universal Formula mapping

Use the current conceptual baseline without silently changing its definitions:

\[
\mathbb U(O)=\mathcal T[S,Z,O,\mathbb I,\mathbb R,\mathbb G,\mathbb H]
\]

\[
Z_{n+1}=F(Z_n,O,C_n,H_n)
\]

For each conversation, record the objective (O), current state (Z), constraints/context (C), and provenance/history (H). The remaining dimensions and operators must retain their canonical definitions once formally approved. This is an architectural model, not a claim of a proven universal scientific law.

## 6. Corpus coverage and completion criteria

Maintain a corpus manifest with one row per source conversation. Report:

- discovered / expected source count, with the basis for the expected count;
- complete, partial, summary-only, inaccessible, and pending counts;
- duplicate clusters and unresolved conflicts;
- artifact and attachment coverage;
- records mapped to PETS/AEGIS;
- records reviewed and approved;
- known gaps and last audit time.

Never claim that all 300 conversations have been processed unless the source inventory supports that exact coverage. A summary or memory note is not a substitute for the original conversation.

## 7. Protection limits and legal review

This protocol improves traceability, preservation, and responsible handling. It does not guarantee exclusive ownership, prevent copying, create a patent, register copyright, establish trade-secret status, or replace legal advice. For material intended for commercial licensing, patent filing, or dispute resolution, obtain jurisdiction-specific intellectual-property advice before public disclosure.

## 8. Default operational policy

Read-only; local/private by default; additive-only changes; least privilege; no secret collection; no autonomous publication; no destructive cleanup; no privilege escalation. Any external disclosure or high-impact change requires explicit, specific owner authorization.
