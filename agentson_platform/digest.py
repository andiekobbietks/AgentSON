"""ComplianceDigest — the shape both report renderers read.

Every count here is derived from the findings list at call time, never
stored twice. A digest that carries a stored total alongside the findings
it summarises is two places to keep correct, and they drift.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

SEVERITIES = ("critical", "high", "medium", "low")


@dataclass
class Finding:
    """One concern in one session.

    ``evidence`` is the exact substring the rule matched -- the transcript
    itself is never edited, only referenced by offset. ``start``/``end``
    locate it in the source text so a reviewer can find it in place.
    """

    tool: str
    session_id: str
    category: str
    severity: str
    evidence: str
    start: int = -1
    end: int = -1
    rule: str = ""

    def as_dict(self) -> dict:
        return {
            "tool": self.tool,
            "session_id": self.session_id,
            "category": self.category,
            "severity": self.severity,
            "evidence": self.evidence,
            "start": self.start,
            "end": self.end,
            "rule": self.rule,
        }


@dataclass
class ToolSummary:
    """Per-tool counters, recounted from findings rather than kept in sync."""

    tool: str
    sessions: int = 0
    entries: int = 0
    messages: int = 0
    """Sum of reader-reported message counts.

    Kept separate from ``entries`` deliberately: the VibeEdge summary
    reports ``messages`` (66 for a session the CLI also prints as
    ``Msgs: 66``), while the OpenCode summary carries no message count at
    all. Adding those into one number would mix two different
    measurements.
    """
    error: str = ""

    def findings_for(self, findings: List[Finding]) -> List[Finding]:
        return [f for f in findings if f.tool == self.tool]


@dataclass
class ComplianceDigest:
    """Result of a scan: what was read, and what it flagged."""

    generated_at: str
    findings: List[Finding] = field(default_factory=list)
    tools: List[ToolSummary] = field(default_factory=list)
    classifier: str = "tier1-rules"
    slm_used: bool = False
    slm_model: str = ""
    output_dir: str = ""
    tool_filter: List[str] = field(default_factory=list)

    # ---- totals, all derived from self.findings ----------------------

    @property
    def total_findings(self) -> int:
        return len(self.findings)

    @property
    def total_sessions(self) -> int:
        return sum(t.sessions for t in self.tools)

    @property
    def total_entries(self) -> int:
        return sum(t.entries for t in self.tools)

    @property
    def total_messages(self) -> int:
        return sum(t.messages for t in self.tools)

    @property
    def high_or_critical(self) -> int:
        return sum(
            1 for f in self.findings if f.severity in ("critical", "high")
        )

    @property
    def tools_in_error(self) -> int:
        return sum(1 for t in self.tools if t.error)

    def count_by_severity(self) -> Dict[str, int]:
        counts = {s: 0 for s in SEVERITIES}
        for f in self.findings:
            if f.severity in counts:
                counts[f.severity] += 1
        return counts

    def count_by_category(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for f in self.findings:
            counts[f.category] = counts.get(f.category, 0) + 1
        return dict(sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])))

    def count_by_tool(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for f in self.findings:
            counts[f.tool] = counts.get(f.tool, 0) + 1
        return dict(sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])))

    def session_matrix(self) -> Dict[str, Dict[str, int]]:
        """Per tool: sessions scanned, findings raised, high/critical."""
        by_tool_findings = self.count_by_tool()
        out: Dict[str, Dict[str, int]] = {}
        for t in self.tools:
            tool_findings = t.findings_for(self.findings)
            out[t.tool] = {
                "sessions": t.sessions,
                "entries": t.entries,
                "messages": t.messages,
                "findings": by_tool_findings.get(t.tool, 0),
                "high_or_critical": sum(
                    1
                    for f in tool_findings
                    if f.severity in ("critical", "high")
                ),
                "error": 1 if t.error else 0,
            }
        return out

    def as_dict(self) -> dict:
        """Full serialisable form — the ``.json`` half of the report pair."""
        return {
            "generated_at": self.generated_at,
            "classifier": self.classifier,
            "slm_used": self.slm_used,
            "slm_model": self.slm_model,
            "tool_filter": self.tool_filter,
            "totals": {
                "tools": len(self.tools),
                "sessions": self.total_sessions,
                "entries": self.total_entries,
                "messages": self.total_messages,
                "findings": self.total_findings,
                "high_or_critical": self.high_or_critical,
                "tools_in_error": self.tools_in_error,
            },
            "by_severity": self.count_by_severity(),
            "by_category": self.count_by_category(),
            "by_tool": self.count_by_tool(),
            "tools": [
                {
                    "tool": t.tool,
                    "sessions": t.sessions,
                    "entries": t.entries,
                    "messages": t.messages,
                    "error": t.error,
                }
                for t in self.tools
            ],
            "findings": [f.as_dict() for f in self.findings],
        }
