"""Live archive-capsule import/read-back test against a pinned OpenCode server."""
from __future__ import annotations

import json
import os
from pathlib import Path

from consumers.opencode import _request_json, import_archive, verify_import

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests" / "fixtures" / "conformance" / "cross_harness_session_v1_2.json"
BASE_URL = os.environ.get("AGENTSON_OPENCODE_URL", "http://127.0.0.1:4096")
SERVER_PASSWORD = os.environ["OPENCODE_SERVER_PASSWORD"]


def test_live_opencode_archive_import_and_readback():
    """Import a synthetic v1.2 archive, verify its digest, then delete the session."""
    archive = json.loads(FIXTURE.read_text(encoding="utf-8"))
    health = _request_json(BASE_URL, "/api/info", {}, "GET", 10.0, password=SERVER_PASSWORD)
    assert isinstance(health.get("version"), str) and health["version"]

    imported = import_archive(archive, base_url=BASE_URL, password=SERVER_PASSWORD)
    assert imported["execution_triggered"] is False
    assert imported["immediate_agent_loop_started"] is False
    assert imported["future_model_context_exposure"] is True
    try:
        verified = verify_import(imported, archive, base_url=BASE_URL, password=SERVER_PASSWORD)
        assert verified["verified"] is True
        assert verified["archive_sha256"] == imported["archive_sha256"]
        assert verified["entry_count"] == len(archive["entries"])
        assert verified["inbox_item_count"] == 1
    finally:
        _request_json(
            BASE_URL,
            f"/api/session/{imported['session_id']}",
            {},
            "DELETE",
            15.0,
            password=SERVER_PASSWORD,
        )
