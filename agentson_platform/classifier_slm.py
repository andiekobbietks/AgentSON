"""SLM-enhanced classification, with fallback to Tier 1 rules.

Described in AGENTS.md as a stub with graceful fallback, and that is
exactly what this is: it **probes** for a local runtime and reports what
it found. It does not invent an inference protocol that the repository
never defined -- ADR-019, which was to specify the three-tier privacy
model, does not exist in the repo.

The rule that matters: ``used`` is True only when a model actually
produced the findings. A report that claims an SLM pass which never
happened is worse than no SLM at all, because it changes how much a
reviewer trusts every number underneath it.
"""

from __future__ import annotations

import importlib.util
import shutil
from dataclasses import dataclass
from typing import List, Optional

from .classifier import classify
from .digest import Finding

# Ordered by how much would be needed to make one work locally.
_PROBES = (
    ("ollama", "local ollama daemon (CLI on PATH)"),
    ("transformers", "HuggingFace transformers + torch"),
    ("sentence_transformers", "sentence-transformers"),
)


@dataclass
class SlmResult:
    """What the SLM pass did, including the reason it did not run."""

    used: bool
    runtime: str = ""
    reason: str = ""
    findings: Optional[List[Finding]] = None

    @property
    def label(self) -> str:
        return self.runtime if self.used else ""


def probe(model: Optional[str] = None) -> SlmResult:
    """Look for something that could run a small local model.

    Returns a result with ``used=False`` and a reason in every case where
    no runtime is present, so callers always have an explanation to
    record rather than a bare False.
    """
    for name, description in _PROBES:
        if name == "ollama":
            if shutil.which("ollama"):
                return SlmResult(
                    used=False,
                    runtime="ollama",
                    reason="%s found, but no inference step is defined for it"
                    % description,
                )
            continue
        if importlib.util.find_spec(name) is not None:
            return SlmResult(
                used=False,
                runtime=name,
                reason="%s found, but no inference step is defined for it"
                % description,
            )

    return SlmResult(
        used=False,
        runtime="",
        reason="no local SLM runtime found (looked for: %s)"
        % ", ".join(name for name, _ in _PROBES),
    )


def classify_with_slm(
    text: str,
    tool: str = "",
    session_id: str = "",
    use_slm: bool = False,
    model: Optional[str] = None,
) -> SlmResult:
    """Classify ``text``, preferring an SLM when one is genuinely usable.

    Always returns findings -- from the SLM if one ran, otherwise from the
    Tier 1 rules. Never raises: a classification failure must degrade to
    rules, not abort a scan that has already read every session.
    """
    if not text:
        return SlmResult(used=False, reason="empty text", findings=[])

    if use_slm:
        candidate = probe(model)
        # No SLM path exists that returns findings, so every probe outcome
        # falls through to rules. The reason is preserved for the report.
        _ = candidate.reason
    else:
        candidate = SlmResult(
            used=False,
            reason="--slm not requested; Tier 1 rules only",
        )

    findings = classify(text, tool=tool, session_id=session_id)
    return SlmResult(
        used=False,
        runtime=candidate.runtime,
        reason=candidate.reason,
        findings=findings,
    )


def slm_status(model: Optional[str] = None) -> dict:
    """Serialisable status for the report header and for `--help`."""
    result = probe(model)
    return {
        "requested": False,
        "used": result.used,
        "runtime": result.runtime,
        "reason": result.reason,
        "fallback": "tier1-rules",
    }
