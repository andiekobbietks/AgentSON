"""Version 1 severity and risk classification model for AgentSON.

This module defines the public assessment contract. A ``FindingAssessment``
is a separate, versioned object that interprets evidence without modifying
the original event stream. Every assessment records the evidence it came
from, the method used to produce it, and when it was produced.

Design principles:

* Severity, priority, confidence and status are separate dimensions.
* Severity identifiers (SEV-1..SEV-5) are stable machine-readable values.
* Categories describe the nature of a finding; they are not severity levels.
* Assessments are evidence-derived and reference event IDs, not excerpts.
* Assessment method is recorded so consumers know whether a value came from
  a deterministic rule, a scoring model, AI-assisted classification or human
  approval.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class SeverityLevel(str, Enum):
    """Stable machine-readable severity identifiers."""

    SEV1 = "SEV-1"
    SEV2 = "SEV-2"
    SEV3 = "SEV-3"
    SEV4 = "SEV-4"
    SEV5 = "SEV-5"


class SeverityLabel(str, Enum):
    """Human-readable severity labels that map one-to-one to ``SeverityLevel``."""

    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    INFORMATIONAL = "Informational"


class PriorityLevel(str, Enum):
    """Urgency identifiers, from emergency to deferred."""

    P0 = "P0"
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"
    P4 = "P4"


class PriorityLabel(str, Enum):
    """Human-readable priority labels."""

    EMERGENCY = "Emergency"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    DEFERRED = "Deferred"


class ConfidenceLevel(str, Enum):
    """Certainty in the finding and its severity assignment.

    This combines the ``provenance.confidence`` values from the AgentSON
    ontology (``confirmed``, ``inferred``, ``estimated``, ``ml_generated``,
    ``unknown``) with the ``high`` / ``medium`` / ``low`` gradations commonly
    used by scoring models.
    """

    CONFIRMED = "confirmed"
    INFERRED = "inferred"
    ESTIMATED = "estimated"
    ML_GENERATED = "ml_generated"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


class Status(str, Enum):
    """Lifecycle state of a finding."""

    DETECTED = "detected"
    TRIAGED = "triaged"
    ACCEPTED = "accepted"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    VERIFIED = "verified"
    DISMISSED = "dismissed"


class Category(str, Enum):
    """Nature of the underlying finding.

    A category is independent of severity: a privacy issue can be SEV-5 or
    SEV-1 depending on impact and evidence.
    """

    SECURITY = "security"
    PRIVACY = "privacy"
    DATA_INTEGRITY = "data_integrity"
    AVAILABILITY = "availability"
    RELIABILITY = "reliability"
    CORRECTNESS = "correctness"
    SAFETY = "safety"
    COMPLIANCE = "compliance"
    SUPPLY_CHAIN = "supply_chain"
    PERFORMANCE = "performance"
    COMPATIBILITY = "compatibility"
    MAINTAINABILITY = "maintainability"


class ImpactScope(str, Enum):
    """How widely the finding's impact is felt."""

    SINGLE_SESSION = "single_session"
    MULTI_SESSION = "multi_session"
    SINGLE_AGENT = "single_agent"
    MULTI_AGENT = "multi_agent"
    SYSTEM_WIDE = "system_wide"
    EXTERNAL = "external"


class ImpactDimension(str, Enum):
    """Dimensions the finding affects."""

    CONFIDENTIALITY = "confidentiality"
    INTEGRITY = "integrity"
    AVAILABILITY = "availability"
    ACCOUNTABILITY = "accountability"
    SAFETY = "safety"
    PRIVACY = "privacy"
    RELIABILITY = "reliability"
    CORRECTNESS = "correctness"


class AssessmentMethod(str, Enum):
    """How the assessment was produced.

    Severity must never depend exclusively on AI judgement. The method field
    records which of the four approved mechanisms produced the assessment,
    so downstream reporting can weight it accordingly.
    """

    RULE = "rule"
    SCORING_MODEL = "scoring_model"
    AI_ASSISTED = "ai_assisted"
    HUMAN_APPROVAL = "human_approval"


# ---------------------------------------------------------------------------
# Composite models
# ---------------------------------------------------------------------------

_SEVERITY_LABEL_FOR_LEVEL: Dict[SeverityLevel, SeverityLabel] = {
    SeverityLevel.SEV1: SeverityLabel.CRITICAL,
    SeverityLevel.SEV2: SeverityLabel.HIGH,
    SeverityLevel.SEV3: SeverityLabel.MEDIUM,
    SeverityLevel.SEV4: SeverityLabel.LOW,
    SeverityLevel.SEV5: SeverityLabel.INFORMATIONAL,
}


class Severity(BaseModel):
    """Severity assignment for a single finding.

    ``level`` is the stable, machine-readable value. ``label`` is the
    human-readable form and must agree with ``level``. ``category`` describes
    what kind of problem the finding represents.
    """

    level: SeverityLevel = Field(
        ..., description="Stable severity identifier such as SEV-2."
    )
    label: SeverityLabel = Field(
        ..., description="Human-readable label that matches ``level``."
    )
    category: Category = Field(
        ..., description="Nature of the finding; not a severity level."
    )

    @field_validator("label")
    @classmethod
    def _label_matches_level(cls, value: SeverityLabel, info) -> SeverityLabel:
        """Reject mismatched level/label pairs."""
        level = info.data.get("level")
        if level is None:
            return value
        expected = _SEVERITY_LABEL_FOR_LEVEL.get(level)
        if expected != value:
            raise ValueError(
                f"label {value.value!r} does not match level {level.value!r} "
                f"(expected {expected.value!r})"
            )
        return value


class Confidence(BaseModel):
    """Certainty in the finding and its classification."""

    level: ConfidenceLevel = Field(
        ..., description="Confidence tier."
    )
    score: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Optional numeric score, e.g. from a scoring model.",
    )
    source: Optional[str] = Field(
        None,
        description="Source of the confidence value, e.g. 'provenance.confidence'.",
    )


class EvidenceRef(BaseModel):
    """Reference to originating evidence.

    An assessment never modifies the original event stream. It correlates
    events by ID and, where available, by session and byte offsets so a
    reviewer can open the source transcript and inspect the evidence in place.
    """

    event_ids: List[str] = Field(
        default_factory=list,
        description="IDs of the events that constitute the evidence.",
    )
    session_ids: Optional[List[str]] = Field(
        None,
        description="Sessions that contain the referenced events.",
    )
    start_offset: Optional[int] = Field(
        None,
        description="Start offset of the evidence in the source text, if known.",
    )
    end_offset: Optional[int] = Field(
        None,
        description="End offset of the evidence in the source text, if known.",
    )
    excerpt: Optional[str] = Field(
        None,
        description="Short, read-only excerpt for display; not the evidence itself.",
    )


class Impact(BaseModel):
    """Impact statement for a finding."""

    scope: ImpactScope = Field(
        ..., description="How widely the impact is felt."
    )
    dimensions: List[ImpactDimension] = Field(
        default_factory=list,
        description="CIA-style impact dimensions affected.",
    )
    description: Optional[str] = Field(
        None,
        description="Free-form impact statement.",
    )


class FindingAssessment(BaseModel):
    """A complete, versioned finding assessment.

    This object is the public contract for severity, priority, confidence,
    status and impact in AgentSON. It is designed to be embedded in reports,
    stored in derived indexes, or carried as a separate assessment stream
    without changing the original JSONL event stream.
    """

    schema_version: str = Field(
        default="agentson.severity.v1",
        json_schema_extra={"const": "agentson.severity.v1"},
        description="Version of this assessment object.",
    )
    severity: Severity = Field(
        ..., description="Severity of the finding."
    )
    priority: PriorityLevel = Field(
        ..., description="Urgency of response."
    )
    confidence: Confidence = Field(
        ..., description="Certainty in the finding."
    )
    status: Status = Field(
        ..., description="Lifecycle state of the finding."
    )
    impact: Impact = Field(
        ..., description="Scope and dimensions of impact."
    )
    evidence: EvidenceRef = Field(
        ..., description="Originating evidence, referenced by ID."
    )
    method: AssessmentMethod = Field(
        ..., description="Mechanism that produced this assessment."
    )
    assessed_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc)
        .isoformat()
        .replace("+00:00", "Z"),
        description="ISO 8601 timestamp when the assessment was produced.",
    )
    assessed_by: Optional[str] = Field(
        None,
        description="Identifier of the classifier, model or human assessor.",
    )
    rule_id: Optional[str] = Field(
        None,
        description="ID of the deterministic rule or scoring model used.",
    )
    rationale: Optional[str] = Field(
        None,
        description="Short explanation of how severity was derived.",
    )
    overrides: Optional[Dict[str, Any]] = Field(
        None,
        description="Human override trail: previous value, reason, approver.",
    )

    @field_validator("schema_version")
    @classmethod
    def _schema_version_is_literal(cls, value: str) -> str:
        """Ensure the declared version matches the model version."""
        if value != "agentson.severity.v1":
            raise ValueError(f"expected schema_version 'agentson.severity.v1', got {value!r}")
        return value
