"""Executable baseline tests for the canonical AgentSON v1.2 archive.

These tests verify the archive contract and preservation behaviour of a
neutral JSON consumer. They do NOT claim that two real harness adapters
interoperate; that requires producer/consumer adapter tests per the
conformance plan.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests" / "fixtures" / "conformance" / "cross_harness_session_v1_2.json"
SCHEMA_PATH = ROOT / "spec" / "v1.2.json"
ENTRY_SCHEMA_PATH = ROOT / "spec" / "v1.2-entries.json"


@pytest.fixture(scope="module")
def archive() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def validators():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    entry_schema = json.loads(ENTRY_SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    Draft202012Validator.check_schema(entry_schema)
    return Draft202012Validator(schema), Draft202012Validator(entry_schema)


def test_reference_archive_validates_as_v1_2_envelope(archive, validators):
    full_validator, _ = validators
    errors = sorted(full_validator.iter_errors(archive), key=lambda error: list(error.path))
    assert not errors, "\n".join(error.message for error in errors)


def test_each_entry_validates_against_entry_contract(archive, validators):
    _, entry_validator = validators
    for index, entry in enumerate(archive["entries"]):
        errors = list(entry_validator.iter_errors(entry))
        assert not errors, f"entry[{index}] ({entry.get('type')}): " + "; ".join(
            error.message for error in errors
        )


def test_consumer_round_trip_preserves_order_and_source_identity(archive):
    """A neutral JSON parse/serialise cycle must not reorder the event array."""
    consumer_view = json.loads(json.dumps(archive, ensure_ascii=False))
    assert [e["source_event_id"] for e in consumer_view["entries"]] == [
        e["source_event_id"] for e in archive["entries"]
    ]
    assert [e["source_sequence"] for e in consumer_view["entries"]] == [1, 2, 3, 4]


def test_consumer_round_trip_preserves_source_extensions(archive):
    """Unknown source-specific fields survive a consumer that preserves JSON."""
    consumer_view = json.loads(json.dumps(archive, ensure_ascii=False))
    action = next(entry for entry in consumer_view["entries"] if entry["type"] == "action")
    assert action["extensions"]["fixture-source"] == {
        "native_part_type": "tool",
        "native_call_id": "src-call-001",
    }
    assert consumer_view["extensions"]["fixture"]["synthetic"] is True


def test_action_and_observation_correlation_is_preserved(archive):
    action = next(entry for entry in archive["entries"] if entry["type"] == "action")
    observation = next(entry for entry in archive["entries"] if entry["type"] == "observation")
    assert action["correlation_id"] == observation["correlation_id"] == "corr-001"


def test_action_without_observation_is_a_valid_partial_record(archive, validators):
    """Missing observations are not fabricated to make an action look complete."""
    full_validator, _ = validators
    partial = copy.deepcopy(archive)
    partial["entries"] = [
        entry for entry in partial["entries"] if entry["type"] != "observation"
    ]
    assert not list(full_validator.iter_errors(partial))
    assert not any(entry["type"] == "observation" for entry in partial["entries"])


def test_canonical_archive_does_not_require_stream_meta(archive, validators):
    """Stream framing metadata is not mandatory in a canonical archive."""
    full_validator, _ = validators
    assert not any(entry["type"] == "stream-meta" for entry in archive["entries"])
    assert not list(full_validator.iter_errors(archive))


def test_invalid_entry_type_is_rejected(archive, validators):
    full_validator, _ = validators
    invalid = copy.deepcopy(archive)
    invalid["entries"][0]["type"] = "not-an-agentson-primitive"
    assert list(full_validator.iter_errors(invalid))


def test_fixture_is_explicitly_synthetic_and_contains_no_real_credentials(archive):
    """The baseline fixture must never be misrepresented as a real export."""
    assert archive["extensions"]["fixture"]["synthetic"] is True
    serialised = json.dumps(archive).lower()
    for marker in ("bearer ", "ghp_", "github_pat_", "-----begin private key-----"):
        assert marker not in serialised
