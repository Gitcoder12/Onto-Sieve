# Onto-Sieve — Agent Engineering Contract

## Mission
A deterministic JSONL triple-validation profile with provenance-preserving quarantine. It is not a full RDF parser, OWL reasoner or SHACL engine.

## Codebase map
`onto_sieve.py` parses JSONL records against a local project-specific JSON schema. `examples/schema.json` and `examples/triples.jsonl` document the supported format. `tests/test_onto_sieve.py` defines behavior.

## Before every task
1. Read this file, `SKILLS.md`, `PROJECT_STATUS.md` and the relevant skill.
2. Inspect the current branch and files; do not rely on stale notes.
3. Trace input parsing, validation, quarantine, output-writing and tests before editing.
4. State the problem, intended behavior, files at risk and verification plan.
5. Make the smallest coherent patch.

## Non-negotiable invariants
- Input JSONL is read-only; accepted, quarantine and report outputs must be distinct paths.
- Never silently repair, normalize away, discard or fabricate source triples.
- Every quarantined row retains the original record, line number and stable reason codes.
- Conflicting values for a declared functional property are quarantined as a conflict group; do not choose a winner.
- Missing required predicates are subject-level diagnostics; never synthesize a triple.
- The schema is a project-specific validation profile, not SHACL, OWL or complete RDF semantics.
- No URI dereferencing, remote ontology import or network request is part of the MVP.

## Verification commands
- `python -m unittest discover -s tests -v`
- `python -m py_compile onto_sieve.py tests/test_onto_sieve.py`
- `python onto_sieve.py --help`
- `python onto_sieve.py --schema examples/schema.json --input examples/triples.jsonl --accepted /tmp/accepted.jsonl --quarantine /tmp/quarantine.jsonl --report /tmp/report.json`

Inspect actual output contents and reconcile counts; do not infer correctness from exit code alone. If a command cannot run, say not run.

## Engineering standards
Use explicit validation, stable reason codes, type hints and minimal dependencies. Keep malformed source lines recoverable. Guard overwrites. Avoid broad exception swallowing and hidden network work. Test malformed input and error paths as well as valid records.

## Documentation and handoff
Update README, examples and PROJECT_STATUS when semantics change. State changed files, actual test commands/results, unrun checks, data-preservation effects and residual limitations.

Do not edit main, merge, force-push or rewrite history unless explicitly requested. Never claim standards compliance without conformance evidence.

## Skills
Canonical skills live in `.agents/skills/`; Claude Code discovery entries live in `.claude/skills/`. See `SKILLS.md`.