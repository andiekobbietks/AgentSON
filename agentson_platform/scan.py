"""``agentson platform scan`` -- Crawl -> Classify -> Report.

Signature matches the call in ``cli/main.py`` exactly::

    run_scan(output_dir=..., tool_filter=..., use_slm=..., slm_model=...)

``output_dir`` is a *base* directory (the help text says so), so each scan
writes into its own timestamped folder beneath it. Two scans therefore
cannot overwrite each other's evidence.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from .classifier import rule_catalogue
from .classifier_slm import classify_with_slm, slm_status
from .crawler import DEFAULT_LIMIT, crawl
from .digest import ComplianceDigest, Finding, ToolSummary
from .report import write_reports
from .tool_registry import get_registry


def _stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def run_scan(
    output_dir: Optional[str] = None,
    tool_filter: Optional[List[str]] = None,
    use_slm: bool = False,
    slm_model: Optional[str] = None,
) -> ComplianceDigest:
    """Run a full scan and write both reports. Returns the digest."""
    base = Path(output_dir or ".")
    run_dir = base / ("scan-" + _stamp())
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")

    print("=" * 78)
    print("Data Rights scan")
    print("=" * 78)

    # ---- validate the tool filter before touching any data -------------
    # get_registry raises on an unknown tool; surface it as a clean message
    # instead of a traceback from inside the crawl.
    try:
        registry = get_registry(tool_filter)
    except ValueError as exc:
        print("Error: %s" % exc)
        raise SystemExit(2) from exc

    print("Tools in scope: %s" % ", ".join(registry))

    # ---- 1. crawl -------------------------------------------------------
    print("\n[1/3] Crawl", flush=True)
    docs, summaries, skipped = crawl(
        tool_filter=tool_filter, limit=DEFAULT_LIMIT
    )
    for summary in summaries:
        if summary.error:
            print("  ! %-14s %s" % (summary.tool, summary.error))
        else:
            print(
                "  - %-14s %3d sessions, %5d entries"
                % (summary.tool, summary.sessions, summary.entries)
            )
    for tool, why in sorted(skipped.items()):
        print("  . %-14s skipped: %s" % (tool, why))

    # ---- 2. classify ----------------------------------------------------
    print("\n[2/3] Classify", flush=True)
    findings: List[Finding] = []
    for doc in docs:
        result = classify_with_slm(
            doc.blob,
            tool=doc.tool,
            session_id=doc.session_id,
            use_slm=use_slm,
            model=slm_model,
        )
        if result.findings:
            findings.extend(result.findings)
    print("  %d findings across %d sessions" % (len(findings), len(docs)))

    # ---- 3. digest + report ---------------------------------------------
    print("\n[3/3] Report", flush=True)

    digest = ComplianceDigest(
        generated_at=generated_at,
        findings=findings,
        tools=summaries,
        classifier="tier1-rules",
        slm_used=False,  # never True unless an SLM actually produced findings
        slm_model=slm_model or "",
        output_dir=str(run_dir),
        tool_filter=list(tool_filter) if tool_filter else [],
    )

    paths = write_reports(digest, str(run_dir), skipped)

    _print_summary(digest, skipped)
    print("Rules     : %d categories, %d rule ids"
          % (len(rule_catalogue()["categories"]), len(rule_catalogue()["rules"])))
    status = slm_status(slm_model)
    if use_slm:
        print("SLM       : not used (%s)" % status["reason"])
    print("\nMarkdown  : %s" % paths["markdown"])
    print("JSON      : %s" % paths["json"])
    return digest


def _print_summary(digest: ComplianceDigest, skipped: Dict[str, str]) -> None:
    print("\n" + "-" * 78)
    print(
        "Sessions %d | Entries %d | Messages %d | Findings %d | High+ %d"
        % (
            digest.total_sessions,
            digest.total_entries,
            digest.total_messages,
            digest.total_findings,
            digest.high_or_critical,
        )
    )
    severity = digest.count_by_severity()
    print(
        "Severity : "
        + "  ".join("%s=%d" % (k, v) for k, v in severity.items() if v)
    )
    categories = digest.count_by_category()
    if categories:
        print(
            "Category : "
            + "  ".join("%s=%d" % (k, v) for k, v in categories.items())
        )
    if digest.tools_in_error:
        print("Errors   : %d tool(s) failed - see report.md" % digest.tools_in_error)
    if skipped:
        print("Not read : %d tool(s) - see report.md" % len(skipped))
    print("-" * 78)
