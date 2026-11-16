---
name: quarantine-and-provenance-audit
description: Review Onto-Sieve quarantine behavior, reason codes and source preservation. Use when changing validation outcomes, duplicate handling, conflicts or file outputs.
---

# quarantine-and-provenance-audit

## Required invariants
- Input is never rewritten.
- Every non-empty source line is accounted for as accepted or quarantined; missing-property diagnostics are separate.
- Malformed JSON is preserved as original line text.
- Valid records retain all original fields, including provenance.
- Each quarantine entry has source line number and one or more reason codes.
- Input, accepted, quarantine and report paths are distinct.
- Existing outputs are not overwritten without explicit `--force`.

## Conflict handling
For a functional property with multiple distinct values, quarantine all conflicting values. Never use first-write-wins or last-write-wins. For exact duplicates, preserve a deterministic rule and explain which source row remains accepted. Document whether lexically different but semantically equivalent values count as duplicates.

## Audit procedure
1. Build a line-by-line ledger of input → accepted/quarantined/diagnostic result.
2. Reconcile counts against non-empty input rows.
3. Compare each output record with its source record.
4. Check line numbers across blank and malformed rows.
5. Test output collisions, malformed schema, encoding failures and permission errors.
6. Ensure partial output writes cannot be mistaken for a completed run.

Any unexplained source disappearance is a release blocker. Report provenance loss, ambiguous reason codes, overwrite risk and ordering changes.
