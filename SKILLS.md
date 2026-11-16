# Onto-Sieve — Skills Index

Read `AGENTS.md` first, then select the workflow:
- **triple-schema-design** — Design and review Onto-Sieve's explicit JSON validation profile. Use when adding predicates, object kinds, datatypes, domains, allowed values or required-by-type constraints.
  - Canonical: [`.agents/skills/triple-schema-design/SKILL.md`](.agents/skills/triple-schema-design/SKILL.md)
  - Claude discovery: [`.claude/skills/triple-schema-design/SKILL.md`](.claude/skills/triple-schema-design/SKILL.md)

- **quarantine-and-provenance-audit** — Review Onto-Sieve quarantine behavior, reason codes and source preservation. Use when changing validation outcomes, duplicate handling, conflicts or file outputs.
  - Canonical: [`.agents/skills/quarantine-and-provenance-audit/SKILL.md`](.agents/skills/quarantine-and-provenance-audit/SKILL.md)
  - Claude discovery: [`.claude/skills/quarantine-and-provenance-audit/SKILL.md`](.claude/skills/quarantine-and-provenance-audit/SKILL.md)

- **rdf-standards-interoperability** — Plan standards-aware RDF, OWL or SHACL interoperability without overstating current support. Use when evaluating standards adapters or compatibility claims.
  - Canonical: [`.agents/skills/rdf-standards-interoperability/SKILL.md`](.agents/skills/rdf-standards-interoperability/SKILL.md)
  - Claude discovery: [`.claude/skills/rdf-standards-interoperability/SKILL.md`](.claude/skills/rdf-standards-interoperability/SKILL.md)

## Required workflow
Inspect implementation and tests; state assumptions; preserve source rows; add regression tests; run exact commands; report checks not run. Codex discovers `.agents/skills`; Claude Code discovers `.claude/skills`; other models should read this index and open the canonical skill. Claude entries point to canonical text to prevent drift.

## `multi-agent-review-handoff`

Coordinate standards research, schema design, implementation and independent provenance review for Onto-Sieve. Use when changing triple semantics, validation rules or adapters.

- Canonical: [`.agents/skills/multi-agent-review-handoff/SKILL.md`](.agents/skills/multi-agent-review-handoff/SKILL.md)
- Claude discovery: [`.claude/skills/multi-agent-review-handoff/SKILL.md`](.claude/skills/multi-agent-review-handoff/SKILL.md)
