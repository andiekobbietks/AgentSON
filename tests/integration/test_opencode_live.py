"""Live integration test against a real OpenCode server.

Run with OpenCode listening on 127.0.0.1:4096:
    python -m pytest -q -s tests/integration/test_opencode_live.py
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.request import Request, urlopen

from consumers.opencode import _request_json, import_archive, verify_import

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests" / "fixtures" / "conformance" / "cross_harness_session_v1_2.json"
BASE_URL = os.environ.get("AGENTSON_OPENCODE_URL", "http://127.0.0.1:4096")


def test_live_opencode_import_and_readback():
    archive = json.loads(FIXTURE.read_text(encoding="utf-8"))
    health_request = Request(f"{BASE_URL}/global/health", headers={"Accept": "application/json"})
    with urlopen(health_request, timeout=10) as response:
        health = json.loads(response.read().decode("utf-8"))
    assert health.get("healthy") is True
    assert isinstance(health.get("version"), str) and health["version"]

    imported = import_archive(archive, base_url=BASE_URL)
    assert imported["execution_triggered"] is False
    try:
        verified = verify_import(imported, archive, base_url=BASE_URL)
        assert verified["verified"] is True
        assert verified["archive_sha256"] == imported["archive_sha256"]
        assert verified["entry_count"] == len(archive["entries"])
        print(
            json.dumps(
                {
                    "opencode_version": health["version"],
                    "session_id": imported["session_id"],
                    "archive_sha256": verified["archive_sha256"],
                    "entry_count": verified["entry_count"],
                    "readback": verified["verification"],
                    "native_event_reconstruction": False,
                    "resumption_supported": False,
                },
                sort_keys=True,
            )
        )
    finally:
        _request_json(
            BASE_URL,
            f"/session/{imported['session_id']}",
            {},
            "DELETE",
            15.0,
        )
