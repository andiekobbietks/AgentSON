"""
GRC evidence exporter.

WHY: the premium module turns AgentSON's provenance artifacts (digest,
.agentson JSONL, transcript references) into evidence packages that a GRC
platform (Vanta, Drata, Hyperproof, OneTrust, or any REST endpoint) can ingest.
The format is generic JSON (not locked to a vendor) so it remains portable.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


SCHEMA_VERSION = "agentson.grc.evidence/v1"


def build_evidence(
    digest_path: Optional[str] = None,
    findings_filter: Optional[List[str]] = None,
    controls: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Build a GRC-compatible evidence package from a platform digest."""
    if digest_path and Path(digest_path).exists():
        import json as _json
        with open(digest_path, encoding="utf-8") as f:
            digest = _json.load(f)
    else:
        digest = {
            "generated_at": datetime.now(timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            ),
            "classifier": "tier1-rules",
            "slm_used": False,
            "totals": {
                "tools": 0,
                "sessions": 0,
                "entries": 0,
                "findings": 0,
                "high_or_critical": 0,
            },
            "by_severity": {},
            "by_category": {},
            "by_tool": {},
            "findings": [],
        }

    # Generic GRC evidence mapping — vendor-agnostic.
    findings_list: List[Dict[str, Any]] = digest.get("findings", [])
    if findings_filter:
        findings_list = [
            f for f in findings_list if f.get("category") in findings_filter
        ]

    evidence = []
    for f in findings_list:
        evidence.append(
            {
                "control_reference": "AI-ACT-ART12-LOG",
                "control_title": "Agent session provenance record",
                "framework_refs": ["EU-AI-Act-Art12", "ISO-42001", "SOC2-CC7.2"],
                "subject": {
                    "system": f.get("tool", "unknown"),
                    "session_id": f.get("session_id", ""),
                    "agent_version": "v1.2",
                },
                "finding": {
                    "category": f.get("category", ""),
                    "severity": f.get("severity", "low"),
                    "rule": f.get("rule", ""),
                },
                "evidence_text": f.get("evidence", ""),
                "evidence_location": {
                    "source_file": "session.agentson",
                    "start_offset": f.get("start", -1),
                    "end_offset": f.get("end", -1),
                },
                "generated_at": digest.get("generated_at"),
                "verified_digest": digest.get("digest", ""),
            }
        )

    summary = {
        "total_findings": len(evidence),
        "by_severity": {},
        "by_category": {},
        "high_or_critical": sum(
            1 for e in evidence if e["finding"]["severity"] in ("critical", "high")
        ),
    }

    package = {
        "schema": SCHEMA_VERSION,
        "generated_at": digest.get("generated_at"),
        "source": {
            "tool": "AgentSON",
            "version": "0.1.0",
            "pipeline": "agentson_platform.scan",
        },
        "evidence": evidence,
        "summary": summary,
        "export_metadata": {
            "premium": True,
            "export_command": "grc-export",
            "digest_ref": digest.get("digest", ""),
        },
    }
    return package


def write_evidence(
    package: Dict[str, Any],
    out_path: str,
    format_type: str = "json",
) -> str:
    """Write the evidence package to disk."""
    if format_type == "json":
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(package, f, indent=2, ensure_ascii=False)
    else:
        raise ValueError(f"unsupported format: {format_type}")
    return out_path
