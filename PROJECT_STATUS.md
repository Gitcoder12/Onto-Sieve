# Project Status — Onto-Sieve

**Updated:** 2026-11-16
**Current stage:** Deterministic JSONL validation MVP

## Implemented
- JSONL triple parser with absolute IRI validation.
- Local JSON schema for predicate kind, literal datatype, domains, allowed values and functional constraints.
- Duplicate detection and functional-property conflict quarantine.
- Subject-level missing-required-predicate diagnostics.
- Accepted/quarantine/report outputs that preserve original record and provenance.
- Refusal to overwrite existing outputs unless `--force` is passed.
- Unit tests for valid records, unknown predicates, conflicts, malformed JSON, missing requirements and duplicates.

## Not implemented
- Full RDF/Turtle/N-Triples parser.
- OWL/RDFS entailment or SHACL execution.
- Remote ontology imports or URI dereferencing.
- Graph database integration or agent runtime integration.

## Known limitations
- Schema syntax is a project-specific JSON profile, not a standardized SHACL document.
- Domain checks require explicit `rdf:type` triples in the same input batch.
- Supported XSD datatypes are intentionally limited.
- A subject with missing required predicates is reported but no triple is synthesized.

## Next steps
1. Add SHACL interoperability through an optional, pinned adapter after choosing a standards-compliant dependency.
2. Add RDFLib import/export support behind explicit format adapters.
3. Add schema versioning and validation of the schema itself.
4. Benchmark memory and streaming behavior on large JSONL inputs.

## Verification
Run `python -m unittest discover -s tests -v` and the documented CLI example using new output paths.
