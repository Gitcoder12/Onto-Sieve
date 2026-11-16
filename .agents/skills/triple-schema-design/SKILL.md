---
name: triple-schema-design
description: Design and review Onto-Sieve's explicit JSON validation profile. Use when adding predicates, object kinds, datatypes, domains, allowed values or required-by-type constraints.
---

# triple-schema-design

## Supported model
Each JSONL record contains subject, predicate, object and optional provenance. Object kind is `iri` or `literal`. The local schema maps absolute predicate IRIs to validation rules.

## Procedure
1. Read the schema loader and examples before extending the contract.
2. Define each predicate's object kind explicitly.
3. For literal predicates, specify datatype and allowed values only when implemented by the validator.
4. Use domains only where required subject `rdf:type` is expected in the same batch; the MVP does not fetch ontologies or infer types.
5. Declare a predicate functional only when domain semantics require at most one distinct value per subject/predicate.
6. Add required predicates only when absence is meaningful and testable in the batch.
7. Add valid, invalid, malformed and boundary fixtures before enabling a rule.
8. Update README, examples and PROJECT_STATUS together.

Use full absolute IRIs; do not silently resolve prefixes. Do not claim unsupported datatype coverage. Preserve provenance exactly. Reject invalid schema shape rather than guessing.
