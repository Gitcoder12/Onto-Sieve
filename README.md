# Onto-Sieve
Validate + Quarantine bad triples for ontology-grounded agents.

---

## Engineering Audit & Handover — 2026-11-17

**Reviewed commit:** `757052405c849ad0cd82faa9c7c384474e57ffa3` (`main`).

### Confirmed findings
- The reviewed branch contains only `README.md`; no executable ontology parser, triple validator, quarantine store, or automated tests were found.
- The stated validation/quarantine behavior for ontology-grounded agents is not demonstrated by code on this branch.

### Next actions
1. Define supported RDF/OWL formats, ontology constraints, and validation error taxonomy.
2. Implement a minimal parser/validator with a reversible quarantine record and provenance.
3. Add tests for malformed triples, schema violations, namespace handling, and safe release from quarantine.

**Verification status:** source-tree inspection only; no runnable product or test suite verified.
