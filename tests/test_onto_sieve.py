"""Tests for Onto-Sieve triple validation and human release workflow."""

from __future__ import annotations

import json

import pytest

from onto_sieve import load_schema, partition_triples, release_quarantined, validate_file


@pytest.fixture
def schema():
    return load_schema()


def provenance():
    return {
        "source_url": "https://example.org/evidence/record-1",
        "extracted_at": "2026-11-17T12:00:00Z",
    }


def triple(**overrides):
    item = {
        "id": "t-1",
        "subject": "ex:system-a",
        "predicate": "ex:confidence",
        "object": 0.92,
        "object_type": "literal",
        "provenance": provenance(),
    }
    item.update(overrides)
    return item


def test_valid_triple_is_accepted(schema):
    accepted, quarantined = partition_triples([triple()], schema)
    assert len(accepted) == 1
    assert quarantined == []


def test_unknown_predicate_is_quarantined_with_original(schema):
    bad = triple(predicate="ex:unregistered")
    accepted, quarantined = partition_triples([bad], schema)
    assert accepted == []
    assert quarantined[0]["original"] == bad
    assert "predicate_not_allowed" in quarantined[0]["reasons"]


def test_invalid_object_datatype_is_quarantined(schema):
    bad = triple(object="high", object_type="literal")
    accepted, quarantined = partition_triples([bad], schema)
    assert accepted == []
    assert "literal must be a decimal number" in quarantined[0]["reasons"]


def test_invalid_subject_and_missing_source_are_quarantined(schema):
    bad = triple(subject="not-an-iri", provenance={})
    _, quarantined = partition_triples([bad], schema)
    assert "invalid_subject_iri" in quarantined[0]["reasons"]
    assert "missing_or_invalid_source_provenance" in quarantined[0]["reasons"]


def test_duplicate_record_id_is_quarantined(schema):
    accepted, quarantined = partition_triples([triple(), triple()], schema)
    assert len(accepted) == 1
    assert "duplicate_id" in quarantined[0]["reasons"]


def test_validate_file_persists_quarantine(tmp_path):
    input_path = tmp_path / "triples.json"
    quarantine_path = tmp_path / "quarantine.json"
    input_path.write_text(
        json.dumps([triple(), triple(id="t-bad", predicate="ex:bad")]),
        encoding="utf-8",
    )

    result = validate_file(input_path, quarantine_path=quarantine_path)

    assert result["accepted_count"] == 1
    assert result["quarantined_count"] == 1
    saved = json.loads(quarantine_path.read_text(encoding="utf-8"))
    assert saved[0]["record_id"] == "t-bad"
    assert saved[0]["status"] == "quarantined"


def test_quarantine_release_requires_human_reviewer_and_note(tmp_path):
    quarantine = tmp_path / "quarantine.json"
    accepted = tmp_path / "accepted.jsonl"
    quarantine.write_text(
        json.dumps(
            [
                {
                    "record_id": "t-bad",
                    "original": triple(id="t-bad", predicate="ex:bad"),
                    "status": "quarantined",
                    "reasons": ["predicate_not_allowed"],
                }
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="reviewer and review note"):
        release_quarantined(
            quarantine,
        record_id="t-bad",
        corrected_record=triple(id="t-bad", predicate="ex:bad"),
        reviewer="",
        accepted_path=accepted,
        note="",
        )

    event = release_quarantined(
        quarantine,
        record_id="t-bad",
        corrected_record=triple(id="t-bad", object=0.5),
        reviewer="human-reviewer",
        accepted_path=accepted,
        note="Checked source and corrected the ontology mapping.",
    )

    assert event["release_review"]["decision"] == "released_by_human"
    assert event["record"]["predicate"] == "ex:confidence"
    assert event["original_quarantined_record"]["predicate"] == "ex:bad"
    assert accepted.exists()
    saved = json.loads(quarantine.read_text(encoding="utf-8"))
    assert saved[0]["status"] == "released_by_human"


def test_cli_schema_defaults_reject_missing_input(tmp_path):
    schema_path = tmp_path / "schema.json"
    schema_path.write_text(json.dumps({"schema_version": "wrong"}), encoding="utf-8")
    with pytest.raises(ValueError, match="schema_version"):
        load_schema(schema_path)



def test_invalid_corrected_record_cannot_leave_quarantine(tmp_path):
    quarantine = tmp_path / "quarantine.json"
    accepted = tmp_path / "accepted.jsonl"
    quarantine.write_text(
        json.dumps(
            [
                {
                    "record_id": "t-bad",
                    "original": triple(id="t-bad", predicate="ex:bad"),
                    "status": "quarantined",
                    "reasons": ["predicate_not_allowed"],
                }
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="still fails validation"):
        release_quarantined(
            quarantine,
            record_id="t-bad",
            corrected_record=triple(id="t-bad", predicate="ex:bad"),
            reviewer="human-reviewer",
            accepted_path=accepted,
            note="Reviewed.",
        )

    saved = json.loads(quarantine.read_text(encoding="utf-8"))
    assert saved[0]["status"] == "quarantined"
    assert not accepted.exists()
