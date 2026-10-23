"""
Premium gate for AgentSON Platform features.

WHY: the free core must stay installable and runnable with no account, no
network call and no key. A premium feature therefore checks for a locally
present licence, and when it is absent, points the user at the upgrade path
with a scannable barcode. The check never phones home: it reads a local
file or an environment variable only, so the "no DNS, no TCP" property of
the core (measured) is preserved.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

from cli.barcode import platform_upgrade_url, render_text

ENV_LICENSE = "AGENTSON_PLATFORM_LICENSE"
LICENSE_PATH = Path.home() / ".agentson" / "platform-license.json"

PREMIUM_FEATURES = {
    "grc-export": "Export GRC evidence packages to compliance platforms",
    "structure": "Structure pipelines, graph and lake builds",
    "audit-log": "Continuous audit logging with retention policy",
}


def _load_license() -> Optional[dict]:
    """Read the local licence record, if one exists. Never raises."""
    raw = os.environ.get(ENV_LICENSE)
    if raw:
        try:
            return json.loads(raw)
        except (ValueError, TypeError):
            return {"key": raw, "tier": "unknown"}
    if LICENSE_PATH.exists():
        try:
            return json.loads(LICENSE_PATH.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            return None
    return None


def is_premium(feature: str = "grc-export") -> bool:
    """True when a licence covering ``feature`` is present locally."""
    lic = _load_license()
    if not lic:
        return False
    if lic.get("revoked"):
        return False
    features = lic.get("features")
    if isinstance(features, list):
        return feature in features
    tier = str(lic.get("tier", "")).lower()
    return tier in ("premium", "platform", "enterprise", "pro")


def upgrade_notice(feature: str = "grc-export") -> str:
    """The message shown when a premium feature is used without a licence."""
    url = platform_upgrade_url()
    desc = PREMIUM_FEATURES.get(feature, feature)
    return "\n".join(
        [
            "",
            "  AgentSON Platform — premium feature",
            f"  {desc}",
            "",
            "  This command is part of AgentSON Platform (commercial licence).",
            "  The free core stays Apache-2.0 and needs no account.",
            "",
            "  Scan to open the upgrade page:",
            render_text(url),
            "",
            f"  Or visit: {url}",
            "",
        ]
    )


def require_premium(feature: str = "grc-export") -> bool:
    """Return True when the feature may run, False after printing the notice."""
    if is_premium(feature):
        return True
    print(upgrade_notice(feature))
    return False
