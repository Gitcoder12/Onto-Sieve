"""Deterministic JSONL triple validation with provenance-preserving quarantine.

This is a deliberately small validation profile, not a complete RDF, OWL or
SHACL implementation. It never edits the input file or dereferences URLs.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

XSD = "http://www.w3.org/2001/XMLSchema#"


@dataclass(frozen=True)
class ParsedTriple:
    line_number: int
    raw: dict[str, Any]
    subject: str
    predicate: str
    object_kind: str
    object_value: Any
    datatype: str | None

    @property
    def object_key(self) -> str:
        return json.dumps({"kind": self.object_kind, "value": self.object_value, "datatype": self.datatype}, sort_keys=True, ensure_ascii=False)

    @property
    def triple_key(self) -> tuple[str, str, str]:
        return self.subject, self.predicate, self.object_key


def is_absolute_iri(value: Any) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https", "urn"} and (bool(parsed.netloc) if parsed.scheme in {"http", "https"} else bool(parsed.path))


def load_schema(path: Path) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or not isinstance(raw.get("properties"), dict):
        raise ValueError("schema must contain a 'properties' object")
    for predicate, rule in raw["properties"].items():
        if not is_absolute_iri(predicate) or not isinstance(rule, dict):
            raise ValueError(f"invalid property rule for {predicate!r}")
        if rule.get("object_kind") not in {"iri", "literal"}:
            raise ValueError(f"property {predicate} must declare object_kind 'iri' or 'literal'")
        if not isinstance(rule.get("functional", False), bool):
            raise ValueError(f"property {predicate} functional must be boolean")
        domains = rule.get("domains", [])
        if not isinstance(domains, list) or any(not is_absolute_iri(item) for item in domains):
            raise ValueError(f"property {predicate} domains must be a list of absolute IRIs")
        allowed_values = rule.get("allowed_values")
        if allowed_values is not None and not isinstance(allowed_values, list):
            raise ValueError(f"property {predicate} allowed_values must be a list")
    if "type_predicate" in raw and raw["type_predicate"] not in raw["properties"]:
        raise ValueError("type_predicate must have a property rule")
    required = raw.get("required_by_type", {})
    if not isinstance(required, dict):
        raise ValueError("required_by_type must be an object")
    for subject_type, predicates in required.items():
        if not is_absolute_iri(subject_type) or not isinstance(predicates, list) or any(not is_absolute_iri(item) for item in predicates):
            raise ValueError("required_by_type must map absolute type IRIs to lists of absolute predicate IRIs")
    return raw


def parse_triple(raw: Any, line_number: int) -> ParsedTriple:
    if not isinstance(raw, dict):
        raise ValueError("record must be a JSON object")
    subject, predicate, obj = raw.get("subject"), raw.get("predicate"), raw.get("object")
    if not is_absolute_iri(subject):
        raise ValueError("subject must be an absolute IRI (http, https or urn)")
    if not is_absolute_iri(predicate):
        raise ValueError("predicate must be an absolute IRI (http, https or urn)")
    if not isinstance(obj, dict):
        raise ValueError("object must be an object with kind and value")
    kind, value, datatype = obj.get("kind"), obj.get("value"), obj.get("datatype")
    if kind == "iri":
        if not is_absolute_iri(value):
            raise ValueError("IRI object value must be an absolute IRI")
        if datatype is not None:
            raise ValueError("IRI objects cannot declare a literal datatype")
    elif kind == "literal":
        if not isinstance(value, (str, int, float, bool)) or value is None:
            raise ValueError("literal value must be a string, number or boolean")
        if isinstance(value, float) and not math.isfinite(value):
            raise ValueError("literal number must be finite")
        if datatype is not None and not is_absolute_iri(datatype):
            raise ValueError("literal datatype must be an absolute IRI")
    else:
        raise ValueError("object.kind must be 'iri' or 'literal'")
    return ParsedTriple(line_number, raw, subject, predicate, kind, value, datatype)


def _literal_matches(value: Any, datatype: str | None) -> bool:
    if datatype is None or datatype == XSD + "string":
        return isinstance(value, str)
    if datatype == XSD + "integer":
        if isinstance(value, bool):
            return False
        try:
            return str(int(value)) == str(value).strip()
        except (TypeError, ValueError, OverflowError):
            return False
    if datatype in {XSD + "decimal", XSD + "double", XSD + "float"}:
        if isinstance(value, bool):
            return False
        try:
            return math.isfinite(float(value))
        except (TypeError, ValueError, OverflowError):
            return False
    if datatype == XSD + "boolean":
        return value in {True, False, "true", "false", "1", "0"}
    if datatype == XSD + "date":
        try:
            date.fromisoformat(str(value))
            return True
        except ValueError:
            return False
    return False


def validate_records(lines: list[str], schema: dict[str, Any]) -> dict[str, Any]:
    parsed: list[ParsedTriple] = []
    quarantine_reasons: dict[int, list[str]] = defaultdict(list)
    raw_by_line: dict[int, Any] = {}

    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            raw = json.loads(line)
            raw_by_line[line_number] = raw
            triple = parse_triple(raw, line_number)
            rule = schema["properties"].get(triple.predicate)
            if rule is None:
                quarantine_reasons[line_number].append("unknown_predicate")
                continue
            if rule["object_kind"] != triple.object_kind:
                quarantine_reasons[line_number].append("object_kind_mismatch")
            if triple.object_kind == "literal":
                expected = rule.get("datatype")
                if expected and triple.datatype != expected:
                    quarantine_reasons[line_number].append("datatype_mismatch")
                elif expected and not _literal_matches(triple.object_value, expected):
                    quarantine_reasons[line_number].append("invalid_literal_value")
                allowed = rule.get("allowed_values")
                if allowed is not None and triple.object_value not in allowed:
                    quarantine_reasons[line_number].append("value_not_allowed")
            parsed.append(triple)
        except (json.JSONDecodeError, ValueError) as exc:
            raw_by_line[line_number] = line.rstrip("\n")
            quarantine_reasons[line_number].append(f"invalid_record: {exc}")

    type_predicate = schema.get("type_predicate")
    subject_types: dict[str, set[str]] = defaultdict(set)
    if type_predicate:
        for triple in parsed:
            if triple.predicate == type_predicate and triple.object_kind == "iri" and not quarantine_reasons[triple.line_number]:
                subject_types[triple.subject].add(triple.object_value)

    for triple in parsed:
        if quarantine_reasons[triple.line_number]:
            continue
        domains = schema["properties"][triple.predicate].get("domains", [])
        if domains and not (subject_types.get(triple.subject, set()) & set(domains)):
            quarantine_reasons[triple.line_number].append("domain_not_satisfied_or_subject_type_missing")

    seen: set[tuple[str, str, str]] = set()
    for triple in parsed:
        if quarantine_reasons[triple.line_number]:
            continue
        if triple.triple_key in seen:
            quarantine_reasons[triple.line_number].append("duplicate_triple")
        else:
            seen.add(triple.triple_key)

    functional_groups: dict[tuple[str, str], list[ParsedTriple]] = defaultdict(list)
    for triple in parsed:
        if not quarantine_reasons[triple.line_number] and schema["properties"][triple.predicate].get("functional", False):
            functional_groups[(triple.subject, triple.predicate)].append(triple)
    for group in functional_groups.values():
        if len({item.object_key for item in group}) > 1:
            for item in group:
                quarantine_reasons[item.line_number].append("functional_property_conflict")

    accepted, quarantined = [], []
    for line_number, raw in sorted(raw_by_line.items()):
        reasons = quarantine_reasons.get(line_number, [])
        if reasons:
            quarantined.append({"line_number": line_number, "reasons": sorted(set(reasons)), "record": raw})
        elif isinstance(raw, dict):
            accepted.append(raw)

    subject_violations = []
    required_by_type = schema.get("required_by_type", {})
    if required_by_type:
        present: dict[str, set[str]] = defaultdict(set)
        for triple in parsed:
            if not quarantine_reasons[triple.line_number]:
                present[triple.subject].add(triple.predicate)
        for subject, types in sorted(subject_types.items()):
            for subject_type in sorted(types):
                for required_predicate in required_by_type.get(subject_type, []):
                    if required_predicate not in present[subject]:
                        subject_violations.append({"subject": subject, "subject_type": subject_type, "missing_predicate": required_predicate})

    return {
        "accepted": accepted,
        "quarantined": quarantined,
        "subject_violations": subject_violations,
        "summary": {
            "input_records": len(raw_by_line),
            "accepted_records": len(accepted),
            "quarantined_records": len(quarantined),
            "subjects_with_missing_required_predicates": len({v["subject"] for v in subject_violations}),
        },
        "limitations": [
            "This validator implements only the rules in the supplied JSON schema; it is not an RDF parser or OWL/SHACL reasoner.",
            "No URI dereferencing, ontology import, inference, entailment or external vocabulary validation is performed.",
            "Missing required predicates are reported at subject level; no synthetic triple is created or quarantined for a missing value.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate JSONL triples and quarantine invalid records.")
    parser.add_argument("--schema", type=Path, required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--accepted", type=Path, required=True)
    parser.add_argument("--quarantine", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--force", action="store_true", help="allow replacing existing output files")
    args = parser.parse_args(argv)
    try:
        input_path = args.input.resolve()
        outputs = [args.accepted.resolve(), args.quarantine.resolve(), args.report.resolve()]
        if len(set(outputs)) != len(outputs) or input_path in outputs:
            raise ValueError("input, accepted, quarantine and report paths must all be different")
        if not args.force and any(path.exists() for path in outputs):
            raise FileExistsError("an output path already exists; choose new paths or pass --force")
        schema = load_schema(args.schema)
        result = validate_records(args.input.read_text(encoding="utf-8").splitlines(), schema)
        output_rows = [
            (args.accepted, "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in result["accepted"])),
            (args.quarantine, "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in result["quarantined"])),
            (args.report, json.dumps({key: value for key, value in result.items() if key not in {"accepted", "quarantined"}}, indent=2) + "\n"),
        ]
        for path, content in output_rows:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        print(json.dumps(result["summary"], indent=2))
        return 0
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"onto-sieve: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
