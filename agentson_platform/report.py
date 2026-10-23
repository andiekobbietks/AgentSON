# AgentSON core runtime: report
"""Markdown + JSON report renderers.

Both files are written from the same digest, so they cannot disagree on a
total. The Markdown carries every critical and high finding in full and
summarises medium/low by category; the JSON always carries all of them,
and the Markdown says so rather than quietly truncating.

A report written by this tool **contains the sensitive values it found**.
That is the point of a compliance scan -- the reader needs the actual
credential to revoke it -- but it means report.md and report.json belong
to the same handling class as the sessions they came from.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

from .digest import SEVERITIES, ComplianceDigest, Finding

_SEVERITY_RANK = {s: i for i, s in enumerate(SEVERITIES)}
_FULL_LIST = ("critical", "high")


def _table(headers: List[str], rows: List[List[str]]) -> str:
    """One markdown table builder. Every table in this file uses it."""
    if not rows:
        return "_none_\n"
    widths = [
        max(len(str(h)), *(len(str(r[i])) for r in rows))
        for i, h in enumerate(headers)
    ]

    def line(cells):
        return "| " + " | ".join(
            str(c).ljust(w) for c, w in zip(cells, widths)
        ) + " |"

    out = [line(headers), "|" + "|".join("-" * (w + 2) for w in widths) + "|"]
    out.extend(line(r) for r in rows)
    return "\n".join(out) + "\n"


def _sorted_findings(findings: List[Finding]) -> List[Finding]:
    return sorted(
        findings,
        key=lambda f: (
            _SEVERITY_RANK.get(f.severity, 99),
            f.tool,
            f.start,
        ),
    )


def render_markdown(
    digest: ComplianceDigest, skipped: Optional[Dict[str, str]] = None
) -> str:
    """Render the digest as a Markdown report."""
    lines: List[str] = []
    add = lines.append

    add("# Data Rights Scan")
    add("")
    add(f"- **Generated:** {digest.generated_at}")
    add(f"- **Classifier:** {digest.classifier}")
    if digest.slm_used:
        add(f"- **SLM:** {digest.slm_model or 'default'}")
    else:
        add("- **SLM:** not used (Tier 1 rules only)")
    if digest.tool_filter:
        add(f"- **Tool filter:** {', '.join(digest.tool_filter)}")
    add("")
    add(
        "> **This report reproduces the sensitive values it found** "
        "(credentials, emails, paths). Handle it as you would the "
        "sessions themselves."
    )
    add("")

    add("## Totals")
    add("")
    add(
        _table(
            ["Metric", "Value"],
            [
                ["Tools scanned", str(len(digest.tools))],
                ["Sessions", str(digest.total_sessions)],
                ["Entries", str(digest.total_entries)],
                [
                    "Messages (reader-reported)",
                    str(digest.total_messages),
                ],
                ["Findings", str(digest.total_findings)],
                ["High or critical", str(digest.high_or_critical)],
                ["Tools with errors", str(digest.tools_in_error)],
            ],
        )
    )

    add("## By severity")
    add("")
    add(
        _table(
            ["Severity", "Count"],
            [[s, str(c)] for s, c in digest.count_by_severity().items()],
        )
    )

    add("## By category")
    add("")
    add(
        _table(
            ["Category", "Count", "Severity"],
            [
                [c, str(n), digest_severity(c)]
                for c, n in digest.count_by_category().items()
            ],
        )
    )

    add("## By tool")
    add("")
    matrix = digest.session_matrix()
    add(
        _table(
            ["Tool", "Sessions", "Entries", "Messages", "Findings", "High+", "Error"],
            [
                [
                    tool,
                    str(v["sessions"]),
                    str(v["entries"]),
                    str(v["messages"]),
                    str(v["findings"]),
                    str(v["high_or_critical"]),
                    "yes" if v["error"] else "-",
                ]
                for tool, v in matrix.items()
            ],
        )
    )

    errors = [t for t in digest.tools if t.error]
    if errors:
        add("## Tool errors")
        add("")
        add(
            _table(
                ["Tool", "Error"],
                [[t.tool, t.error] for t in errors],
            )
        )

    if skipped:
        add("## Not scanned")
        add("")
        add(
            _table(
                ["Tool", "Reason"],
                [[t, why] for t, why in sorted(skipped.items())],
            )
        )

    ordered = _sorted_findings(digest.findings)
    headline = [f for f in ordered if f.severity in _FULL_LIST]
    summary = [f for f in ordered if f.severity not in _FULL_LIST]

    add("## Critical and high findings")
    add("")
    if headline:
        add(
            _table(
                ["Severity", "Tool", "Session", "Category", "Evidence", "Offset"],
                [
                    [
                        f.severity,
                        f.tool,
                        f.session_id[:16],
                        f.category,
                        _cell(f.evidence),
                        f"{f.start}:{f.end}",
                    ]
                    for f in headline
                ],
            )
        )
    else:
        add("_none_")
        add("")

    add("## Medium and low findings")
    add("")
    if summary:
        counts: Dict[str, int] = {}
        for f in summary:
            counts[f.category] = counts.get(f.category, 0) + 1
        add(
            _table(
                ["Category", "Severity", "Count"],
                [
                    [c, digest_severity(c), str(n)]
                    for c, n in sorted(
                        counts.items(), key=lambda kv: (-kv[1], kv[0])
                    )
                ],
            )
        )
        add(
            f"\nAll **{len(summary)}** medium/low findings are listed in "
            "`report.json`, which always carries the complete set."
        )
        add("")
    else:
        add("_none_")
        add("")

    add("## Method")
    add("")
    add(
        "Tier 1 rules only: email, phone and API-key patterns are delegated "
        "to `tools/pii_redactor.py` so the classifier and the redactor share "
        "one copy of those patterns; file paths, telemetry hosts and URLs are "
        "classified here. **Severity is a judgement, not a measurement** -- "
        "it is stated once in `agentson_platform/classifier.py` as "
        "`SEVERITY` and read from there by every rule."
    )
    add("")
    return "\n".join(lines)


def _cell(text: str, limit: int = 90) -> str:
    """Table-safe evidence. Report files are Markdown, so pipes and newlines
    in a transcript excerpt would break the row."""
    flat = str(text).replace("|", "\\|").replace("\r", " ").replace("\n", " ")
    if len(flat) > limit:
        return flat[: limit - 1] + "…"
    return flat


def digest_severity(category: str) -> str:
    from .classifier import SEVERITY

    return SEVERITY.get(category, "?")


def write_reports(
    digest: ComplianceDigest,
    output_dir: str,
    skipped: Optional[Dict[str, str]] = None,
) -> Dict[str, str]:
    """Write ``report.md`` and ``report.json``. Returns their paths."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    md_path = out / "report.md"
    json_path = out / "report.json"

    md_path.write_text(render_markdown(digest, skipped), encoding="utf-8")
    json_path.write_text(
        json.dumps(digest.as_dict(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return {"markdown": str(md_path), "json": str(json_path)}
