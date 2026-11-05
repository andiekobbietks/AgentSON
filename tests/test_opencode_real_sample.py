"""
Exercise the real OpenCode export sample through the production SQLite reader.

The checked-in fixture contains a real captured assistant message and its
native reasoning/tool parts. We wrap those records in a temporary legacy
SQLite container so the test verifies database discovery, row decoding,
projection, provenance retention and canonical JSONL export end-to-end.
"""
import json
import sqlite3
from pathlib import Path

from exporters.jsonl import validate_v1_2_events, write_agentson_stream
from readers.opencode import OpencodeReader


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "opencode_real_sample.json"


def _database_from_real_sample(tmp_path):
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    message = fixture["message"]
    session_id = message["sessionID"]
    db_path = tmp_path / "opencode-real-sample.sqlite"
    conn = sqlite3.connect(str(db_path))
    conn.executescript("""
        CREATE TABLE session (
            id TEXT PRIMARY KEY, title TEXT, time_created INTEGER, time_updated INTEGER,
            model TEXT, agent TEXT, tokens_input INTEGER, tokens_output INTEGER,
            cost REAL, directory TEXT, version TEXT
        );
        CREATE TABLE message (
            id TEXT PRIMARY KEY, session_id TEXT, time_created INTEGER,
            time_updated INTEGER, data TEXT
        );
        CREATE TABLE part (
            id TEXT PRIMARY KEY, session_id TEXT, message_id TEXT,
            time_created INTEGER, time_updated INTEGER, data TEXT
        );
        CREATE TABLE todo (
            session_id TEXT, content TEXT, status TEXT, priority TEXT, position INTEGER
        );
    """)
    conn.execute(
        "INSERT INTO session VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (session_id, "Real OpenCode sample", message["time"]["created"],
         message["time"]["completed"],
         json.dumps({"id": message["modelID"], "providerID": message["providerID"],
                     "variant": message["variant"]}),
         message["agent"], message["tokens"]["input"], message["tokens"]["output"],
         message["cost"], message["path"]["cwd"], "captured"),
    )
    conn.execute(
        "INSERT INTO message VALUES (?,?,?,?,?)",
        (message["id"], session_id, message["time"]["created"],
         message["time"]["completed"], json.dumps(message)),
    )
    for part in fixture["parts"]:
        start = (part.get("time") or {}).get("start")
        if start is None:
            start = (part.get("state") or {}).get("time", {}).get("start")
        conn.execute(
            "INSERT INTO part VALUES (?,?,?,?,?,?)",
            (part["id"], session_id, message["id"], start or message["time"]["created"],
             (part.get("time") or {}).get("end") or
             (part.get("state") or {}).get("time", {}).get("end") or start or message["time"]["created"],
             json.dumps(part)),
        )
    conn.commit()
    conn.close()
    return db_path, fixture


def test_real_opencode_sample_runs_through_actual_reader_and_jsonl(tmp_path):
    db_path, fixture = _database_from_real_sample(tmp_path)
    message = fixture["message"]

    reader = OpencodeReader(str(db_path))
    reader.connect()
    try:
        sessions = reader.list_sessions()
        session = reader.read_session(message["sessionID"])
    finally:
        reader.disconnect()

    assert sessions[0]["id"] == message["sessionID"]
    assert session["agent"]["name"] == message["modelID"]
    assert session["agent"]["provider"] == message["providerID"]
    assert session["metadata"]["tokens_input"] == message["tokens"]["input"]
    assert session["metadata"]["tokens_output"] == message["tokens"]["output"]
    assert session["metadata"]["total_tokens"] == (
        message["tokens"]["input"] + message["tokens"]["output"]
    )

    thought = next(e for e in session["entries"] if e["type"] == "thought")
    assert thought["text"] == "Now run the test script."
    assert thought["source_payload"]["part_data"]["id"] == fixture["parts"][0]["id"]

    action = next(e for e in session["entries"] if e["type"] == "action")
    native_tool = fixture["parts"][1]
    assert action["tool"] == native_tool["tool"] == "bash"
    assert action["tool_call_id"] == native_tool["callID"]
    assert action["status"] == "success"
    assert "test_claude_code_run.py" in action["code"]
    assert "ALL TESTS PASSED" in action["output"]
    assert action["source_payload"]["part_data"] == native_tool
    assert action["source_payload"]["message_data"]["finish"] == "tool-calls"

    target = tmp_path / "real-opencode.agentson"
    with target.open("w", encoding="utf-8") as handle:
        write_agentson_stream(session, handle, source_tool="opencode")
    events = [json.loads(line) for line in target.read_text(encoding="utf-8").splitlines()]
    validate_v1_2_events(events)
    exported_action = next(e for e in events if e["type"] == "action")
    assert exported_action["tool_call_id"] == native_tool["callID"]
    assert exported_action["source_payload"]["part_data"] == native_tool
    assert events[0]["source_session"]["source_metadata"]["schema_generation"] == "1.x"
    assert events[0]["source_session"]["source_metadata"]["session_row"]["id"] == message["sessionID"]


def test_v2_untimestamped_inbox_rows_remain_after_timestamped_events():
    reader = OpencodeReader(":memory:")
    session = {
        "id": "session-order",
        "title": "Ordering fixture",
        "time_created": 100,
        "time_updated": 200,
        "model": "{}",
    }
    messages = [
        {"id": "later", "type": "user", "time_created": 200, "data": json.dumps({"text": "later"})},
        {"id": "earlier", "type": "user", "time_created": 100, "data": json.dumps({"text": "earlier"})},
    ]
    inbox = [
        {"type": "user", "time_created": None, "payload": {"text": "queued item"}},
    ]

    result = reader._convert_v2(session, messages, [], inbox)
    entries = result["entries"]

    assert [event["text"] for event in entries[:2]] == ["earlier", "later"]
    assert entries[-1]["text"].startswith("OpenCode inbox item")
    assert entries[-1].get("timestamp") is None
