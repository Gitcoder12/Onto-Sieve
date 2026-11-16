# Onto-Sieve

Validate and quarantine bad triples for ontology-grounded agents.

Onto-Sieve is a deterministic JSONL triple validator. It checks records against an explicit, local property schema and writes accepted records, quarantined records and a report to separate output files. Input records are never edited in place, and provenance fields are retained in both accepted and quarantined output.

## MVP scope

- Validate absolute subject/predicate/object IRIs.
- Validate literal versus IRI object kinds and a small set of XSD literal datatypes.
- Check known predicates, optional domains, allowed values and functional-property constraints.
- Detect exact duplicate triples.
- Report missing required predicates at subject level without fabricating missing triples.
- Preserve malformed source lines and reason codes in quarantine output.
- Refuse to overwrite output files unless `--force` is supplied.

This is **not** a full RDF parser, OWL reasoner or SHACL implementation. It does not import remote ontologies, dereference IRIs, perform entailment or validate all RDF/RDFS semantics. Use a full standards-compliant toolchain when those semantics are required.

## Requirements

- Python 3.10 or later
- Standard library only

## Input format

One JSON object per line:

```json
{
  "subject": "https://example.org/id/person-1",
  "predicate": "https://example.org/vocab/name",
  "object": {
    "kind": "literal",
    "value": "Ada Example",
    "datatype": "http://www.w3.org/2001/XMLSchema#string"
  },
  "provenance": {"source": "https://example.org/source-a"}
}
```

## Run

```bash
python onto_sieve.py \
  --schema examples/schema.json \
  --input examples/triples.jsonl \
  --accepted /tmp/accepted.jsonl \
  --quarantine /tmp/quarantine.jsonl \
  --report /tmp/report.json
```

Use new output paths for each run. Pass `--force` only when intentionally replacing existing output files.

Run tests:

```bash
python -m unittest discover -s tests -v
```

## Quarantine semantics

A quarantined record contains the original record, its input line number and one or more reason codes. For conflicting values of a functional property, every value in the conflict group is quarantined rather than arbitrarily selecting a winner. Missing required predicates are reported separately because no source triple exists to quarantine.

## Data integrity

The input is read-only. No source rows are silently repaired, dropped or overwritten. Review quarantine output before deciding whether to correct source data.

## Working with coding agents

Start with [`AGENTS.md`](AGENTS.md) for repository-wide invariants, architecture, commands and review rules. Use [`SKILLS.md`](SKILLS.md) to select a task-specific workflow. Canonical skills are stored in `.agents/skills/`; Claude Code discovery entries are stored in `.claude/skills/`. Read the relevant skill before changing domain logic. All agent output remains subject to human review; documentation and tests do not replace scientific, operational or safety validation.
