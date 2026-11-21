"""Tests for the AgentSON severity and risk classification model.

WHY: SEVERITY.md introduces a new public contract. These tests make sure the
Pydantic model, the JSON Schema and the on-disk fixtures stay consistent.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import ValidationError as SchemaValidationError
from pydantic import ValidationError

from agentson_platform.severity.v1 import (
    Category,
    Confidence,
    ConfidenceLevel,
    EvidenceRef,
    FindingAssessment,
    Impact,
    ImpactDimension,
    ImpactScope,
    PriorityLevel,
    Severity,
    SeverityLabel,
    SeverityLevel,
    Status,
)

REPO = Path(__file__).parent.parent
FIXTURES = REPO / "tests" / "fixtures" / "severity"
SCHEMA_PATH = REPO / "spec" / "severity" / "v1.json"

with open(SCHEMA_PATH, encoding="utf-8") as _f:
    SCHEMA = json.load(_f)


def _is_date_time(value: object) -> bool:
    """Return True for an offset-aware RFC 3339 date-time string.

    ``jsonschema`` only registers the ``date-time`` checker when the
    optional ``rfc3339-validator`` package is installed. It is not a
    declared dependency, so register an equivalent dependency-free
    checker here to make the ``format: date-time`` assertion real.
    """
    if not isinstance(value, str):
        return True
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None


_FORMAT_CHECKER = FormatChecker()
_FORMAT_CHECKER.checks("date-time")(_is_date_time)
SCHEMA_VALIDATOR = Draft202012Validator(SCHEMA, format_checker=_FORMAT_CHECKER)

VALID_FIXTURES = [
    "sev1_critical_security.json",
    "sev2_high_privacy.json",
    "sev3_medium_data_integrity.json",
    "sev4_low_performance.json",
    "sev5_informational_maintainability.json",
    "edge_multi_session.json",
    "edge_low_confidence.json",
    "edge_human_override.json",
]


def _load_json(name: str) -> dict:
    """Load a JSON fixture by file name."""
    with open(FIXTURES / name, encoding="utf-8") as f:
        return json.load(f)


class TestSeverityLevels:
    """Each of the five severity levels round-trips through the model."""

    @pytest.mark.parametrize("fixture", VALID_FIXTURES[:5])
    def test_fixture_loads_as_model(self, fixture: str) -> None:
        """A fixture must instantiate without validation errors."""
        data = _load_json(fixture)
        assessment = FindingAssessment(**data)
        assert assessment.schema_version == "agentson.severity.v1"

    @pytest.mark.parametrize("fixture", VALID_FIXTURES[:5])
    def test_fixture_validates_against_schema(self, fixture: str) -> None:
        """A fixture must pass the published JSON Schema."""
        data = _load_json(fixture)
        SCHEMA_VALIDATOR.validate(data)

    def test_all_five_levels_represented(self) -> None:
        """The five base fixtures cover SEV-1 through SEV-5."""
        levels = {
            _load_json(name)["severity"]["level"]
            for name in VALID_FIXTURES[:5]
        }
        assert levels == {"SEV-1", "SEV-2", "SEV-3", "SEV-4", "SEV-5"}


class TestEdgeCases:
    """Cross-session correlation, low confidence and human overrides."""

    def test_multi_session_evidence(self) -> None:
        """A finding can reference events from multiple sessions."""
        data = _load_json("edge_multi_session.json")
        assessment = FindingAssessment(**data)
        assert assessment.evidence.session_ids == ["sess_a1", "sess_a2", "sess_a3"]
        assert len(assessment.evidence.event_ids) == 6

    def test_low_confidence_is_allowed(self) -> None:
        """A medium-severity finding can carry low confidence."""
        data = _load_json("edge_low_confidence.json")
        assessment = FindingAssessment(**data)
        assert assessment.confidence.level == ConfidenceLevel.LOW
        assert assessment.confidence.score == 0.25
        assert assessment.severity.level == SeverityLevel.SEV3

    def test_human_override_trail(self) -> None:
        """A dismissed finding can carry an override history."""
        data = _load_json("edge_human_override.json")
        assessment = FindingAssessment(**data)
        assert assessment.status == Status.DISMISSED
        assert assessment.method.value == "human_approval"
        assert assessment.overrides is not None
        assert assessment.overrides["previous_severity"]["level"] == "SEV-2"


class TestSeverityValidation:
    """The model rejects inconsistent or incomplete assessments."""

    def test_mismatched_label_rejected(self) -> None:
        """A SEV-1 severity cannot carry a Low label."""
        with pytest.raises(ValidationError):
            Severity(
                level=SeverityLevel.SEV1,
                label=SeverityLabel.LOW,
                category=Category.SECURITY,
            )

    def test_invalid_priority_rejected(self) -> None:
        """Only P0..P4 are valid priority values."""
        data = _load_json("sev1_critical_security.json")
        data["priority"] = "P5"
        with pytest.raises(ValidationError):
            FindingAssessment(**data)

    def test_missing_evidence_event_ids_defaults_to_empty(self) -> None:
        """An assessment may reference sessions/offsets when event IDs are unavailable."""
        data = _load_json("sev1_critical_security.json")
        data["evidence"] = {
            "session_ids": ["sess_abc123"],
            "start_offset": 0,
            "end_offset": 10,
        }
        assessment = FindingAssessment(**data)
        assert assessment.evidence.event_ids == []

    def test_wrong_schema_version_rejected(self) -> None:
        """The literal schema version is enforced."""
        data = _load_json("sev1_critical_security.json")
        data["schema_version"] = "agentson.severity.v2"
        with pytest.raises(ValidationError):
            FindingAssessment(**data)

    def test_confidence_score_out_of_range_rejected(self) -> None:
        """Confidence scores must be between 0 and 1."""
        with pytest.raises(ValidationError):
            Confidence(level=ConfidenceLevel.HIGH, score=1.5)

    def test_invalid_assessed_at_rejected(self) -> None:
        """An assessment timestamp must be a parseable date-time."""
        data = _load_json("sev1_critical_security.json")
        data["assessed_at"] = "not-a-date"
        with pytest.raises(ValidationError):
            FindingAssessment(**data)

    def test_naive_assessed_at_rejected(self) -> None:
        """The assessment timestamp must carry an offset."""
        data = _load_json("sev1_critical_security.json")
        data["assessed_at"] = "2026-11-04T17:00:00"
        with pytest.raises(ValidationError):
            FindingAssessment(**data)

    def test_missing_assessed_by_rejected(self) -> None:
        """Every assessment must name its assessor."""
        data = _load_json("sev1_critical_security.json")
        del data["assessed_by"]
        with pytest.raises(ValidationError):
            FindingAssessment(**data)

    def test_rule_method_requires_rule_id(self) -> None:
        """A rule assessment must name the rule that produced it."""
        data = _load_json("sev1_critical_security.json")
        assert data["method"] == "rule"
        data["rule_id"] = None
        with pytest.raises(ValidationError):
            FindingAssessment(**data)

    def test_scoring_model_method_requires_rule_id(self) -> None:
        """A scoring-model assessment must name the model that produced it."""
        data = _load_json("sev3_medium_data_integrity.json")
        assert data["method"] == "scoring_model"
        del data["rule_id"]
        with pytest.raises(ValidationError):
            FindingAssessment(**data)

    def test_override_without_reason_rejected(self) -> None:
        """An override record must carry a reason and an approver."""
        data = _load_json("edge_human_override.json")
        data["overrides"] = {
            "previous_severity": {"level": "SEV-2", "label": "High", "category": "security"}
        }
        with pytest.raises(ValidationError):
            FindingAssessment(**data)

    def test_empty_override_rejected(self) -> None:
        """An empty override object is not a recorded override."""
        data = _load_json("edge_human_override.json")
        data["overrides"] = {}
        with pytest.raises(ValidationError):
            FindingAssessment(**data)


class TestSchemaAndModelAgreement:
    """The JSON Schema and the Pydantic model must describe the same contract."""

    def test_schema_has_required_top_level_fields(self) -> None:
        """The schema requires all fields that have no default in the model."""
        required = set(SCHEMA["required"])
        # schema_version and assessed_at have defaults and are therefore not
        # required. rule_id is conditionally required, not top-level required.
        model_required = {
            "severity",
            "priority",
            "confidence",
            "status",
            "impact",
            "evidence",
            "method",
            "assessed_by",
        }
        assert required == model_required

    def test_schema_version_is_literal(self) -> None:
        """schema_version is fixed in the published schema."""
        assert SCHEMA["properties"]["schema_version"]["const"] == "agentson.severity.v1"

    def test_enum_values_match_severity_levels(self) -> None:
        """Schema severity level enum matches the Python enum."""
        defs = SCHEMA["$defs"]
        schema_levels = set(defs["SeverityLevel"]["enum"])
        model_levels = {level.value for level in SeverityLevel}
        assert schema_levels == model_levels

    def test_enum_values_match_categories(self) -> None:
        """Schema category enum matches the Python enum."""
        schema_cats = set(SCHEMA["$defs"]["Category"]["enum"])
        model_cats = {cat.value for cat in Category}
        assert schema_cats == model_cats

    def test_schema_rejects_mismatched_level_label(self) -> None:
        """The schema enforces the same level/label pairing as the model."""
        data = _load_json("sev1_critical_security.json")
        data["severity"]["label"] = "Low"
        with pytest.raises(SchemaValidationError):
            SCHEMA_VALIDATOR.validate(data)

    def test_schema_rejects_invalid_assessed_at(self) -> None:
        """The schema enforces the date-time format on assessed_at."""
        data = _load_json("sev1_critical_security.json")
        data["assessed_at"] = "not-a-date"
        with pytest.raises(SchemaValidationError):
            SCHEMA_VALIDATOR.validate(data)

    def test_schema_requires_assessed_by(self) -> None:
        """The schema requires an assessor for every assessment."""
        data = _load_json("sev1_critical_security.json")
        del data["assessed_by"]
        with pytest.raises(SchemaValidationError):
            SCHEMA_VALIDATOR.validate(data)

    def test_schema_requires_rule_id_for_rule_method(self) -> None:
        """The schema requires rule_id when the method derives from a rule."""
        data = _load_json("sev1_critical_security.json")
        assert data["method"] == "rule"
        del data["rule_id"]
        with pytest.raises(SchemaValidationError):
            SCHEMA_VALIDATOR.validate(data)

    def test_schema_override_requires_reason_and_approver(self) -> None:
        """The schema rejects an override without a reason and approver."""
        data = _load_json("edge_human_override.json")
        data["overrides"] = {}
        with pytest.raises(SchemaValidationError):
            SCHEMA_VALIDATOR.validate(data)


class TestRoundTrip:
    """Serialization and deserialization preserve data."""

    def test_model_serializes_and_deserializes(self) -> None:
        """A model instance dumps to JSON and loads back identically."""
        original = FindingAssessment(
            severity=Severity(
                level=SeverityLevel.SEV2,
                label=SeverityLabel.HIGH,
                category=Category.PRIVACY,
            ),
            priority=PriorityLevel.P1,
            confidence=Confidence(level=ConfidenceLevel.CONFIRMED, score=0.95),
            status=Status.DETECTED,
            impact=Impact(
                scope=ImpactScope.SINGLE_SESSION,
                dimensions=[ImpactDimension.PRIVACY],
            ),
            evidence=EvidenceRef(event_ids=["evt_001"]),
            method="rule",
            assessed_by="test",
            rule_id="test-rule",
        )
        dumped = original.model_dump(mode="json")
        restored = FindingAssessment(**dumped)
        assert restored.severity.level == SeverityLevel.SEV2
        assert restored.confidence.score == 0.95
