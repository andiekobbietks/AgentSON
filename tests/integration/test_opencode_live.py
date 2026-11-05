"""Live integration test against a real OpenCode v2 server."""
from __future__ import annotations

import json
import os
from pathlib import Path

from consumers.opencode import _request_json, import_archive, verify_import

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests" / "fixtures" / "conformance" / "cross_harness_session_v1_2.json"
BASE_URL = os.environ.get("AGENTSON_OPENCODE_URL", "http://127.0.0.1:4096")
SERVER_PASSWORD = os.environ["OPENCODE_PASSWORD"]


def test_live_opencode_import_and_readback():
    archive = json.loads(FIXTURE.read_text(encoding="utf-8"))
    health = _request_json(
        BASE_URL, "/api/info", {}, "GET", 10.0, password=SERVER_PASSWORD
    )
    assert isinstance(health.get("version"), str) and health["version"]

    imported = import_archive(
        archive, base_url=BASE_URL, password=SERVER_PASSWORD
    )
    assert imported["execution_triggered"] is False
    assert imported["immediate_agent_loop_started"] is False
    assert imported["future_model_context_exposure"] is True
    try:
        verified = verify_import(
            imported, archive, base_url=BASE_URL, password=SERVER_PASSWORD
        )
        assert verified["verified"] is True
        assert verified["archive_sha256"] == imported["archive_sha256"]
        assert verified["entry_count"] == len(archive["entries"])
        assert verified["inbox_item_count"] == 1
        print(
            json.dumps(
                {
                    "opencode_version": health["version"],
                    "session_id": imported["session_id"],
                    "archive_sha256": verified["archive_sha256"],
                    "entry_count": verified["entry_count"],
                    "inbox_item_count": verified["inbox_item_count"],
                    "readback": verified["verification"],
                    "immediate_agent_loop_started": imported["immediate_agent_loop_started"],
                    "future_model_context_exposure": imported["future_model_context_exposure"],
                    "native_event_reconstruction": False,
                    "resumption_supported": False,
                },
                sort_keys=True,
            )
        )
    finally:
        _request_json(
            BASE_URL,
            f"/api/session/{imported['session_id']}",
            {},
            "DELETE",
            15.0,
            password=SERVER_PASSWORD,
        )
