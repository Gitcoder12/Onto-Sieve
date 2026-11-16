import json
import unittest

from onto_sieve import validate_records

EX = "https://example.org/"
RDF_TYPE = "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"
XSD_STRING = "http://www.w3.org/2001/XMLSchema#string"
SCHEMA = {
    "type_predicate": RDF_TYPE,
    "properties": {
        RDF_TYPE: {"object_kind": "iri", "functional": False},
        EX + "name": {"object_kind": "literal", "datatype": XSD_STRING, "functional": True, "domains": [EX + "Person"]},
        EX + "knows": {"object_kind": "iri", "functional": False, "domains": [EX + "Person"]},
    },
    "required_by_type": {EX + "Person": [EX + "name"]},
}


def triple(subject, predicate, object_value, kind="literal", datatype=XSD_STRING):
    obj = {"kind": kind, "value": object_value}
    if kind == "literal":
        obj["datatype"] = datatype
    return {"subject": subject, "predicate": predicate, "object": obj, "provenance": {"source": "https://source.example.org/item"}}


class OntoSieveTests(unittest.TestCase):
    def test_accepts_valid_typed_subject_and_name(self):
        lines = [json.dumps(triple(EX+"p1", RDF_TYPE, EX+"Person", "iri", None)), json.dumps(triple(EX+"p1", EX+"name", "Ada"))]
        result = validate_records(lines, SCHEMA)
        self.assertEqual(result["summary"]["accepted_records"], 2)
        self.assertEqual(result["summary"]["quarantined_records"], 0)

    def test_unknown_predicate_is_quarantined(self):
        result = validate_records([json.dumps(triple(EX+"p1", EX+"unknown", "x"))], SCHEMA)
        self.assertIn("unknown_predicate", result["quarantined"][0]["reasons"])

    def test_functional_property_conflict_quarantines_both_values(self):
        lines = [json.dumps(triple(EX+"p1", RDF_TYPE, EX+"Person", "iri", None)), json.dumps(triple(EX+"p1", EX+"name", "Ada")), json.dumps(triple(EX+"p1", EX+"name", "Grace"))]
        result = validate_records(lines, SCHEMA)
        conflicts = [row for row in result["quarantined"] if "functional_property_conflict" in row["reasons"]]
        self.assertEqual(len(conflicts), 2)

    def test_malformed_json_is_preserved_in_quarantine(self):
        result = validate_records(["{not json"], SCHEMA)
        self.assertEqual(result["summary"]["quarantined_records"], 1)
        self.assertEqual(result["quarantined"][0]["record"], "{not json")

    def test_missing_required_predicate_is_reported_without_fabrication(self):
        line = json.dumps(triple(EX+"p1", RDF_TYPE, EX+"Person", "iri", None))
        result = validate_records([line], SCHEMA)
        self.assertEqual(len(result["subject_violations"]), 1)
        self.assertEqual(result["summary"]["accepted_records"], 1)

    def test_duplicate_triple_is_quarantined_after_first(self):
        line = json.dumps(triple(EX+"p1", EX+"name", "Ada"))
        schema = {"properties": {EX+"name": {"object_kind":"literal", "datatype":XSD_STRING, "functional":False}}}
        result = validate_records([line, line], schema)
        self.assertEqual(result["summary"]["accepted_records"], 1)
        self.assertIn("duplicate_triple", result["quarantined"][0]["reasons"])


if __name__ == "__main__":
    unittest.main()
