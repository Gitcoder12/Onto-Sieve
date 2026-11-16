---
name: rdf-standards-interoperability
description: Plan standards-aware RDF, OWL or SHACL interoperability without overstating current support. Use when evaluating standards adapters or compatibility claims.
---

# rdf-standards-interoperability

## Current boundary
The MVP consumes project-specific JSONL and JSON schema. It is not a complete RDF parser, OWL reasoner or SHACL processor.

## Adapter-first strategy
1. Keep the JSONL core deterministic and independent.
2. Define format adapters that map supported RDF inputs to an internal record model while preserving source identifiers and provenance.
3. Evaluate a mature RDF library such as RDFLib rather than writing an incomplete Turtle/N-Triples parser.
4. Evaluate a dedicated SHACL implementation such as pySHACL behind an optional dependency and explicit command.
5. Preserve language tags, datatype IRIs, blank nodes, named graphs, namespaces and source locations where the library exposes them.
6. Distinguish syntax errors, project-profile violations, SHACL reports and OWL entailment results.
7. Pin optional dependencies and document versions and supported syntax.

## Tests
Use golden fixtures for each claimed serialization, literal/language-tag round trips, blank nodes, named graphs and known-valid/invalid SHACL shapes. Prove adapters do not change core JSONL behavior.

Do not claim RDF compliance, OWL reasoning or SHACL support until behavior is demonstrated with conformance-oriented fixtures.
