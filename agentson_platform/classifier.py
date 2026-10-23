"""Tier 1 rule-based classifier — PII, secrets, telemetry.

Two rule sources, deliberately:

1. **Reused** — email, phone and secret detection is delegated to
   ``tools/pii_redactor.PIIRedactor.redact_text()``. Its patterns are
   local variables inside ``_redact_with_regex``, so they cannot be
   imported piecemeal; calling the engine keeps this classifier in step
   with the redactor for free. The same patterns under two roofs would
   drift the first time one is fixed.

2. **Added here** — file paths, telemetry signals and URLs. The redactor
   declares ``private_url`` in its category list but implements no URL
   rule, so these three exist only here.

Severity is a **judgement table**, not a measurement: nobody derived
critical/medium from data. It is written once, below, and every rule
reads from it so the opinion is visible in a single place.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import List, Optional

from .digest import Finding

# --------------------------------------------------------------------------
# Severity — one opinion, stated once. Change it here, nowhere else.
# --------------------------------------------------------------------------
SEVERITY = {
    "api-key": "critical",   # a live credential beats any PII in urgency
    "email": "high",         # GDPR Art. 4(1) direct identifier
    "phone": "high",         # same
    "telemetry": "medium",   # third-party transmission signal, not user data
    "file-path": "medium",   # reveals local structure and often a username
    "url": "low",            # usually benign context
}

# Map redactor output types onto this classifier's categories. Dates are
# deliberately absent: AGENTS.md defines six categories and a date is not
# one of them.
_FROM_REDACTOR = {
    "secret": "api-key",
    "private_email": "email",
    "private_phone": "phone",
}

# Telemetry endpoints worth naming. A mention in a transcript means some
# component in that session is configured to transmit.
_TELEMETRY_MARKERS = (
    "posthog", "i.posthog.com", "scarf.sh", "segment.com", "segment.io",
    "mixpanel.com", "sentry.io", "amplitude.com", "google-analytics.com",
    "googletagmanager.com", "fullstory.com", "hotjar.com", "datadog.com",
    "newrelic.com", "heap.io", "intercom.io", "intercomcdn.com",
    "optimizely.com", "vwo.com", "ketch.co", "cookiebot.com",
    "branch.io", "appsflyer.com", "bugsnag.com", "launchdarkly.com",
)

_FILE_PATH = re.compile(
    r"""(?x)
      [A-Za-z]:\\[^\s'"<>|]{2,}          # C:\...
    | \\\\ [^\s'"<>|]{2,}                # UNC \\server\share
    | / (?: home | Users | var | opt | usr | etc) /[^\s'"<>|]{2,}
    | ~/ [^\s'"<>|]{2,}
    """
)

_URL = re.compile(r"https?://[^\s'\"<>)\]}]+", re.IGNORECASE)

# One redactor for the process. Construction only sets flags, but building
# it per call would mean re-parsing the same regexes on every message.
_REDACTOR = None
_PII_PATH = Path(__file__).resolve().parent.parent / "tools" / "pii_redactor.py"


def _redactor():
    """Load PIIRedactor by **file path**, not by the name ``tools``.

    ``from tools.pii_redactor import`` is not dependable here. This machine
    has an unrelated regular package called ``tools`` in global
    site-packages, and per PEP 420 a regular package beats this repo's
    namespace ``tools`` even when the repo root is earlier on ``sys.path``.
    The import therefore succeeds inside the pipx venv (no competitor) and
    fails under global Python -- so the same classifier would report three
    fewer categories depending on which interpreter ran it. Loading the
    file sidesteps the name collision while still reading one copy of the
    patterns.
    """
    global _REDACTOR
    if _REDACTOR is None:
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "_agentson_pii_redactor", _PII_PATH
        )
        if spec is None or spec.loader is None:
            raise ModuleNotFoundError(
                "cannot load PIIRedactor from %s" % _PII_PATH
            )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        _REDACTOR = module.PIIRedactor(use_model=False)
    return _REDACTOR


def _overlaps(start: int, end: int, spans: List[tuple]) -> bool:
    """True when ``[start, end)`` meets any span already reported.

    Standard interval overlap. The earlier strict-containment test
    (``start < s and e < end``) returned False for two identical spans, so
    a telemetry URL was also reported as a plain URL, and two markers over
    the same host produced duplicate telemetry findings.
    """
    return any(start < e and s < end for s, e in spans)


def classify(
    text: str,
    tool: str = "",
    session_id: str = "",
    rule_prefix: str = "tier1",
) -> List[Finding]:
    """Run every Tier 1 rule over ``text``.

    Pure function: no I/O, no mutation of ``text``. The transcript is
    referenced by offset, never rewritten.
    """
    if not text:
        return []

    findings: List[Finding] = []
    claimed: List[tuple] = []  # spans reported, for cross-rule URL dedup
    claimed_by_cat: dict = {}  # spans reported, per category

    def add(category: str, evidence: str, start: int, end: int, rule: str):
        severity = SEVERITY[category]
        # Exact-substring guard: rules must not report something the text
        # does not actually contain.
        if text[start:end] != evidence:
            return
        # One concern per span per category. Two redactor patterns match the
        # same phone number nested inside itself, which would count a single
        # concern twice in every total the digest reports.
        if _overlaps(start, end, claimed_by_cat.get(category, ())):
            return
        findings.append(
            Finding(
                tool=tool,
                session_id=session_id,
                category=category,
                severity=severity,
                evidence=evidence,
                start=start,
                end=end,
                rule=rule,
            )
        )
        claimed_by_cat.setdefault(category, []).append((start, end))
        claimed.append((start, end))

    # ---- 1. reused: redactor engine ------------------------------------
    # No try/except here. Swallowing failures once hid three entire
    # categories -- email, phone and api-key -- behind a clean run. A rule
    # that cannot execute must fail where it stands.
    _, hits = _redactor().redact_text(text)
    # Longest span first. Where two patterns match the same concern nested
    # inside each other, the outer and more complete evidence must claim the
    # category slot -- otherwise the result depends on the order the redactor
    # happens to list its patterns in.
    hits.sort(key=lambda h: -(h.get("end", -1) - h.get("start", -1)))
    for hit in hits:
        category = _FROM_REDACTOR.get(hit.get("type", ""))
        if not category:
            continue
        start, end = hit.get("start", -1), hit.get("end", -1)
        if start < 0 or end < 0:
            continue
        add(category, hit.get("text", ""), start, end, "redactor:%s" % hit["type"])

    # ---- 2. telemetry signals -------------------------------------------
    lowered = text.lower()
    for marker in _TELEMETRY_MARKERS:
        needle = marker.lower()
        at = lowered.find(needle)
        while at != -1:
            # Report the whole host-ish token, not the bare substring.
            start = at
            while start > 0 and text[start - 1] not in " \t\r\n'\"<>":
                start -= 1
            end = at + len(needle)
            while end < len(text) and text[end] not in " \t\r\n'\"<>),;":
                end += 1
            if not _overlaps(start, end, claimed):
                add("telemetry", text[start:end], start, end, "telemetry:marker")
            at = lowered.find(needle, end)

    # ---- 3. file paths ---------------------------------------------------
    for m in _FILE_PATH.finditer(text):
        add("file-path", m.group(), m.start(), m.end(), "path:native")

    # ---- 4. URLs, skipping anything already reported ---------------------
    for m in _URL.finditer(text):
        if _overlaps(m.start(), m.end(), claimed):
            continue
        add("url", m.group(), m.start(), m.end(), "url:scheme")

    findings.sort(key=lambda f: (f.start, f.category))
    return findings


def classify_many(
    texts, tool: str = "", session_id: str = ""
) -> List[Finding]:
    """Classify an iterable of text chunks under one tool/session label."""
    out: List[Finding] = []
    for text in texts:
        out.extend(classify(text or "", tool=tool, session_id=session_id))
    return out


def rule_catalogue() -> dict:
    """The rules in play, for reports and for tests."""
    return {
        "severity": dict(SEVERITY),
        "from_redactor": dict(_FROM_REDACTOR),
        "telemetry_markers": list(_TELEMETRY_MARKERS),
        "categories": sorted(SEVERITY),
        "rules": [
            "redactor:secret",
            "redactor:private_email",
            "redactor:private_phone",
            "telemetry:marker",
            "path:native",
            "url:scheme",
        ],
    }
