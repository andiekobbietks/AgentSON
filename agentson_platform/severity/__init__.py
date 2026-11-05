"""AgentSON severity and risk classification models.

This package holds versioned assessment vocabularies. Code that needs to
assign, read or translate severity should import from the versioned module
rather than hard-coding strings, so the public contract can evolve without
silent drift.
"""

from __future__ import annotations

from .v1 import (
    AssessmentMethod,
    Category,
    Confidence,
    ConfidenceLevel,
    EvidenceRef,
    FindingAssessment,
    Impact,
    ImpactDimension,
    ImpactScope,
    PriorityLabel,
    PriorityLevel,
    Severity,
    SeverityLabel,
    SeverityLevel,
    Status,
)

__all__ = [
    "AssessmentMethod",
    "Category",
    "Confidence",
    "ConfidenceLevel",
    "EvidenceRef",
    "FindingAssessment",
    "Impact",
    "ImpactDimension",
    "ImpactScope",
    "PriorityLabel",
    "PriorityLevel",
    "Severity",
    "SeverityLabel",
    "SeverityLevel",
    "Status",
]
