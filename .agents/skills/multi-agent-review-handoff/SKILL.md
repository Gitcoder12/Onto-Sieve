---
name: multi-agent-review-handoff
description: Coordinate standards research, schema design, implementation and independent provenance review for Onto-Sieve. Use when changing triple semantics, validation rules or adapters.
---

# Multi-Agent Review Handoff — Onto-Sieve

## Roles
- **Standards researcher (for example, Claude):** identify the exact RDF/RDFS/OWL/SHACL concept and authoritative specification section relevant to a proposed feature. State whether it is a syntax rule, validation constraint or entailment rule.
- **Implementation engineer (for example, ChatGPT/Codex):** implement only the agreed subset, add fixtures and tests, and preserve the existing JSONL contract unless a migration is specified.
- **Independent reviewer (for example, DeepSeek):** inspect semantics and diff read-only; challenge false claims of standards compliance, data loss, incorrect conflict resolution and ambiguous reason codes.
- **Verifier:** run unit tests and compare accepted/quarantined results line-by-line against fixture inputs.
- **Human maintainer:** approves semantic changes and any new dependency or standards-compatibility claim.

## Handoff contract
A standards proposal must identify the term, version, exact specification/reference, input example, expected validation result and unsupported edge cases. Distinguish parsing, validation, inference and reasoning; they are not synonyms.

## Parallel-work rules
- One writer per schema/source/test file at a time.
- Researcher does not edit core validation logic while implementation is in progress.
- Reviewer checks a pinned commit SHA read-only.
- Never allow two agents to independently define the same predicate's cardinality or datatype.
- Use test fixtures and source preservation to resolve disagreements.

## Release gate
Reconcile every non-empty input line to accepted/quarantined/diagnostic outcomes. Confirm no fabricated triples, no silent repair, no lost provenance and no overwrite. Any unexplained source disappearance or standards claim without conformance evidence blocks release.
