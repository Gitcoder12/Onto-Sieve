"""Validate ontology-oriented JSON triples and quarantine unsafe records.

MVP scope: JSON triple records with an explicit namespace/predicate contract.
This is not an RDF/OWL parser or SHACL implementation. Unsupported RDF formats
must be rejected or converted by an independently reviewed ingestion adapter.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

DEFAULT_SCHEMA = Path(__file__).resolve().parent / "config" / "ontology.json"


def _is_absolute_iri(value: str) -> bool:
    parsed = urlparse(value)
    return bool(parsed.scheme) and (bool(parsed.netloc) or parsed.scheme == "urn")


def _known_compact_iri(value: str, namespaces: dict[str, str]) -> bool:
    if ":" not in value:
        return False
    prefix, local = value.split(":", 1)
    return bool(local) and prefix in namespaces


def _valid_iri(value: Any, namespaces: dict[str, str]) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    return _is_absolute_iri(value) or _known_compact_iri(value, namespaces)


def _valid_source(source: Any) -> bool:
    if not isinstance(source, dict):
        return False
    url = source.get("source_url")
    if not isinstance(url, str):
        return False
    parsed = urlparse(url)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _validate_literal(value: Any, datatype: str | None) -> str | None:
    if datatype in (None, "xsd:string"):
        return None if isinstance(value, str) else "literal must be a string"
    if datatype == "xsd:decimal":
        if isinstance(value, bool):
            return "decimal literal cannot be boolean"
        try:
            number = float(value)
        except (TypeError, ValueError):
            return "literal must be a decimal number"
        return None if math.isfinite(number) else "decimal literal must be finite"
    if datatype == "xsd:integer":
        if isinstance(value, bool) or not isinstance(value, int):
            return "literal must be an integer"
        return None
    if datatype == "xsd:boolean":
        return None if isinstance(value, bool) else "literal must be boolean"
    if datatype == "xsd:anyURI":
        return None if _valid_iri(value, {}) else "literal must be an absolute IRI"
    return f"unsupported datatype: {datatype}"


def load_schema(path: Path = DEFAULT_SCHEMA) -> dict[str, Any]:
    schema = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(schema, dict) or schema.get("schema_version") != "1.0":
        raise ValueError("ontology schema must be a version 1.0 JSON object")
    namespaces = schema.get("namespaces")
    predicates = schema.get("predicates")
    if not isinstance(namespaces, dict) or not namespaces:
        raise ValueError("schema namespaces must be a non-empty object")
    if not isinstance(predicates, dict) or not predicates:
        raise ValueError("schema predicates must be a non-empty object")
    for prefix, namespace in namespaces.items():
        if not isinstance(prefix, str) or not prefix:
            raise ValueError("namespace prefixes must be non-empty strings")
        if not isinstance(namespace, str) or not _is_absolute_iri(namespace):
            raise ValueError(f"namespace {prefix!r} must be an absolute IRI")
    return schema


def validate_triple(triple: Any, schema: dict[str, Any]) -> list[str]:
    """Return all validation reasons for one triple; an empty list means valid."""
    if not isinstance(triple, dict):
        return ["triple_must_be_object"]
    reasons: list[str] = []
    required = {"id", "subject", "predicate", "object", "object_type", "provenance"}
    missing = sorted(required - triple.keys())
    if missing:
        return [f"missing_fields:{','.join(missing)}"]

    namespaces = schema["namespaces"]
    predicates = schema["predicates"]
    if not isinstance(triple["id"], str) or not triple["id"].strip():
        reasons.append("invalid_id")
    if not _valid_iri(triple["subject"], namespaces):
        reasons.append("invalid_subject_iri")

    predicate = triple["predicate"]
    if not isinstance(predicate, str) or predicate not in predicates:
        reasons.append("predicate_not_allowed")
    if triple["object_type"] not in {"iri", "literal"}:
        reasons.append("invalid_object_type")
    elif triple["object_type"] == "iri":
        if not _valid_iri(triple["object"], namespaces):
            reasons.append("invalid_object_iri")
        if isinstance(predicate, str) and predicate in predicates:
            expected = predicates[predicate].get("object_type")
            if expected != "iri":
                reasons.append("object_type_mismatch")
    else:
        if isinstance(predicate, str) and predicate in predicates:
            definition = predicates[predicate]
            if definition.get("object_type") != "literal":
                reasons.append("object_type_mismatch")
            literal_error = _validate_literal(
                triple["object"], definition.get("datatype")
            )
            if literal_error:
                reasons.append(literal_error)

    provenance = triple["provenance"]
    if not _valid_source(provenance):
        reasons.append("missing_or_invalid_source_provenance")
    elif not isinstance(provenance.get("extracted_at"), str) or not provenance["extracted_at"].strip():
        reasons.append("missing_extraction_timestamp")
    return reasons


def partition_triples(
    triples: list[Any], schema: dict[str, Any]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Separate valid records from quarantined originals with explicit reasons."""
    seen: set[str] = set()
    accepted: list[dict[str, Any]] = []
    quarantined: list[dict[str, Any]] = []
    for index, triple in enumerate(triples):
        reasons = validate_triple(triple, schema)
        record_id = triple.get("id") if isinstance(triple, dict) else None
        if isinstance(record_id, str) and record_id in seen:
            reasons.append("duplicate_id")
        elif isinstance(record_id, str):
            seen.add(record_id)
        if reasons:
            quarantined.append(
                {
                    "quarantine_id": f"q-{index + 1}",
                    "record_id": record_id,
                    "original": triple,
                    "reasons": sorted(set(reasons)),
                    "status": "quarantined",
                }
            )
        else:
            accepted.append(triple)
    return accepted, quarantined


def validate_file(
    input_path: Path,
    *,
    schema_path: Path = DEFAULT_SCHEMA,
    quarantine_path: Path,
) -> dict[str, Any]:
    """Validate a JSON array and append new quarantined items to the store."""
    raw = json.loads(input_path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError("input file must contain a JSON array of triples")
    schema = load_schema(schema_path)
    accepted, quarantined = partition_triples(raw, schema)
    existing: list[Any] = []
    if quarantine_path.exists():
        current = json.loads(quarantine_path.read_text(encoding="utf-8"))
        if not isinstance(current, list):
            raise ValueError("quarantine file must contain a JSON array")
        existing = current
    known_ids = {
        item.get("record_id")
        for item in existing
        if isinstance(item, dict) and item.get("record_id")
    }
    new_items = [
        item for item in quarantined
        if not item.get("record_id") or item["record_id"] not in known_ids
    ]
    quarantine_path.parent.mkdir(parents=True, exist_ok=True)
    quarantine_path.write_text(
        json.dumps(existing + new_items, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return {
        "input_count": len(raw),
        "accepted_count": len(accepted),
        "quarantined_count": len(new_items),
        "accepted": accepted,
        "quarantined": new_items,
    }


def release_quarantined(
    quarantine_path: Path,
    *,
    record_id: str,
    corrected_record: dict[str, Any],
    schema_path: Path = DEFAULT_SCHEMA,
    reviewer: str,
    accepted_path: Path,
    note: str,
) -> dict[str, Any]:
    """Release only a corrected record that passes the schema after human review."""
    if not reviewer.strip() or not note.strip():
        raise ValueError("reviewer and review note are required")
    if not isinstance(corrected_record, dict):
        raise ValueError("corrected_record must be a JSON object")
    corrected_errors = validate_triple(corrected_record, load_schema(schema_path))
    if corrected_errors:
        raise ValueError(
            "corrected record still fails validation: " + ", ".join(corrected_errors)
        )
    if corrected_record.get("id") != record_id:
        raise ValueError("corrected record id must match the quarantined record id")
    store = json.loads(quarantine_path.read_text(encoding="utf-8"))
    if not isinstance(store, list):
        raise ValueError("quarantine file must contain a JSON array")
    match = next(
        (
            item for item in store
            if isinstance(item, dict)
            and item.get("record_id") == record_id
            and item.get("status") == "quarantined"
        ),
        None,
    )
    if match is None:
        raise ValueError(f"no quarantined record found for id {record_id!r}")
    event = {
        "record": corrected_record,
        "original_quarantined_record": match["original"],
        "release_review": {
            "reviewer": reviewer.strip(),
            "note": note.strip(),
            "reviewed_at": datetime.now(timezone.utc).isoformat(),
            "decision": "released_by_human",
        },
    }
    accepted_path.parent.mkdir(parents=True, exist_ok=True)
    with accepted_path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(event, ensure_ascii=False) + "\n")
    match["status"] = "released_by_human"
    match["release_review"] = event["release_review"]
    quarantine_path.write_text(
        json.dumps(store, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return event


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Onto-Sieve triple validation and quarantine")
    sub = parser.add_subparsers(dest="command", required=True)
    validate = sub.add_parser("validate", help="validate triples and quarantine invalid records")
    validate.add_argument("input", type=Path)
    validate.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    validate.add_argument("--quarantine", type=Path, default=Path("quarantine.json"))
    release = sub.add_parser("release", help="release a quarantined record after human review")
    release.add_argument("record_id")
    release.add_argument("--quarantine", type=Path, default=Path("quarantine.json"))
    release.add_argument("--accepted", type=Path, default=Path("accepted.jsonl"))
    release.add_argument("--reviewer", required=True)
    release.add_argument("--note", required=True)
    release.add_argument("--corrected-json", type=Path, required=True)
    release.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    args = parser.parse_args(argv)
    try:
        if args.command == "validate":
            result = validate_file(
                args.input, schema_path=args.schema, quarantine_path=args.quarantine
            )
        else:
            corrected_record = json.loads(args.corrected_json.read_text(encoding="utf-8"))
            result = release_quarantined(
                args.quarantine,
                record_id=args.record_id,
                corrected_record=corrected_record,
                schema_path=args.schema,
                reviewer=args.reviewer,
                accepted_path=args.accepted,
                note=args.note,
            )
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"onto-sieve: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
