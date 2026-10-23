"""Data Rights Intelligence Platform — crawl, classify, report.

Crawl -> Classify -> Report. Each stage is a module:

    tool_registry  where each tool keeps its session data
    crawler        export every session the readers can parse
    classifier     Tier 1 rules (PII, secrets, telemetry)
    classifier_slm optional SLM pass, falls back to rules
    digest         ComplianceDigest, the shape both reports read
    report         Markdown + JSON renderers
    scan           run_scan(), the `agentson platform scan` entry point

The platform reads local session data only. It makes no network calls of
its own: the SLM path is opt-in via --slm and fails closed to rules.
"""

__all__ = [
    "tool_registry",
    "crawler",
    "digest",
    "classifier",
    "classifier_slm",
    "report",
    "scan",
]
