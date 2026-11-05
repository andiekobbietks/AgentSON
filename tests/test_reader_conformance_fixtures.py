"""End-to-end reader conformance using synthetic native-format fixtures.

Fixtures are deliberately labelled synthetic: they model documented source
shapes and contain no user data. They exercise the adapters, not just the
shared serializer.
"""
import json
import sqlite3
from pathlib import Path

from exporters.jsonl import validate_v1_2_events, write_agentson_stream

FIXTURES = Path(__file__).parent / "fixtures"


def _export_and_validate(session, path, source_tool):
    with path.open("w", encoding="utf-8") as handle:
        write_agentson_stream(session, handle, source_tool=source_tool)
    events = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    validate_v1_2_events(events)
    assert events[0]["type"] == "stream-meta"
    assert events[0]["schema_version"] == "1.2"
    return events


def test_claude_code_native_jsonl_fixture_through_reader(tmp_path):
    from readers.claude_code import ClaudeCodeReader

    project = tmp_path / "projects" / "fixture-project"
    project.mkdir(parents=True)
    source = project / "claude-fixture-001.jsonl"
    source.write_text(
        (FIXTURES / "claude_code_native_synthetic.jsonl").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    session = ClaudeCodeReader(config_dir=str(tmp_path)).read_session("claude-fixture-001")
    assert session["tool"]["name"] == "claude-code"
    assert any(e["type"] == "user-query" for e in session["entries"])
    assert any(e["type"] == "action" and e.get("tool_call_id") == "toolu_fixture_01" for e in session["entries"])
    observations = [e for e in session["entries"] if e["type"] == "observation" and e.get("correlation_id") == "toolu_fixture_01"]
    assert observations
    assert observations[0]["source_payload"]["block"]["type"] == "tool_result"
    events = _export_and_validate(session, tmp_path / "claude.agentson", "claude-code")
    assert any(e["type"] == "action" and e.get("tool_call_id") == "toolu_fixture_01" for e in events)
    exported_observation = next(e for e in events if e["type"] == "observation")
    assert exported_observation["source_payload"]["block"]["tool_use_id"] == "toolu_fixture_01"


def test_chrome_devtools_markdown_fixture_through_reader(tmp_path):
    from readers.chrome_devtools import read as read_chrome

    session = read_chrome(FIXTURES / "chrome_devtools_native_synthetic.md")
    assert session["tool"]["name"] == "chrome-devtools"
    assert any(e["type"] == "user-query" and e.get("attachments") for e in session["entries"])
    assert any(e["type"] == "action" and e.get("code") for e in session["entries"])
    assert any(e["type"] == "answer" for e in session["entries"])
    events = _export_and_validate(session, tmp_path / "chrome.agentson", "chrome-devtools")
    assert events[0]["source_session"]["metadata"]["source_filename"].endswith("chrome_devtools_native_synthetic.md")


def test_libre_csv_fixture_through_reader(tmp_path):
    from readers.libre import read_libre_csv

    session = read_libre_csv(str(FIXTURES / "libre_sensor_native_synthetic.csv"))
    assert len(session["entries"]) == 3
    assert session["entries"][0]["data"]["reading_type"] == "CGM"
    assert session["entries"][1]["data"]["source_raw"] == "Manual"
    assert session["entries"][1]["status"] == "low"
    events = _export_and_validate(session, tmp_path / "libre.agentson", "libre")
    observations = [e for e in events if e["type"] == "observation"]
    assert len(observations) == 3
    assert events[0]["source_session"]["source_metadata"]["metrics"]["total_readings"] == 3


def test_minimax_sqlite_fixture_through_reader(tmp_path):
    from readers.minimax import MiniMaxReader

    db_path = tmp_path / "mavis-synthetic.sqlite"
    conn = sqlite3.connect(db_path)
    conn.executescript("""
        CREATE TABLE sessions (
            session_id TEXT PRIMARY KEY, agent_name TEXT, title TEXT,
            framework_type TEXT, effective_model TEXT, effective_model_variant TEXT,
            status TEXT, created_at INTEGER, updated_at INTEGER, last_active_at INTEGER,
            workspace_dir TEXT, framework_session_id TEXT, session_data_dir TEXT
        );
        CREATE TABLE session_messages (
            msg_id TEXT, session_id TEXT, role TEXT, data TEXT, timestamp INTEGER
        );
        CREATE TABLE token_usage (
            session_id TEXT, input_tokens INTEGER, output_tokens INTEGER,
            reasoning_tokens INTEGER, cache_read_tokens INTEGER,
            cache_write_tokens INTEGER, cost_usd REAL, ts INTEGER
        );
    """)
    conn.execute(
        "INSERT INTO sessions VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
        ("mavis-fixture-001", "mavis", "Fixture task", "opencode", "model-test",
         "thinking", "completed", 1793869200000, 1793869500000,
         1793869500000, "/workspace/demo", "native-framework-session", "/tmp/mavis"),
    )
    user_blob = {"role": "user", "msg_content": "Run the test suite."}
    assistant_blob = {
        "role": "assistant", "thinking_content": "I will run pytest.",
        "tool_calls": [{
            "tool_name": "bash", "tool_call_id": "mavis_tool_01",
            "tool_call_status": 2, "tool_call_args": json.dumps({"command": "pytest -q"}),
            "tool_call_result_data": "5 passed",
        }],
        "msg_content": "The tests passed.",
    }
    conn.execute("INSERT INTO session_messages VALUES (?,?,?,?,?)",
                 ("msg-user", "mavis-fixture-001", "user", json.dumps(user_blob), 1793869201000))
    conn.execute("INSERT INTO session_messages VALUES (?,?,?,?,?)",
                 ("msg-assistant", "mavis-fixture-001", "assistant", json.dumps(assistant_blob), 1793869202000))
    conn.execute("INSERT INTO token_usage VALUES (?,?,?,?,?,?,?,?)",
                 ("mavis-fixture-001", 100, 50, 20, 10, 5, 0.01, 1793869202000))
    conn.commit()
    conn.close()

    reader = MiniMaxReader(str(db_path))
    reader.connect()
    try:
        session = reader.read_session("mavis-fixture-001")
    finally:
        reader.disconnect()
    assert any(e["type"] == "user-query" for e in session["entries"])
    assert any(e["type"] == "action" and e.get("tool_call_id") == "mavis_tool_01" for e in session["entries"])
    assert any(e["type"] == "observation" and e.get("correlation_id") == "mavis_tool_01" for e in session["entries"])
    events = _export_and_validate(session, tmp_path / "minimax.agentson", "minimax")
    assert events[0]["mode"] == "single"
    assert events[0]["stream_id"] == "mavis-fixture-001"


def test_antigravity_sqlite_fixture_through_reader(tmp_path):
    from readers.antigravity import read_antigravity_session

    db_path = tmp_path / "antigravity-synthetic.sqlite"
    conn = sqlite3.connect(db_path)
    conn.executescript("""
        CREATE TABLE steps (
            idx INTEGER, step_type INTEGER, status INTEGER,
            has_subtrajectory INTEGER, step_payload BLOB, step_format INTEGER
        );
        CREATE TABLE trajectory_metadata_blob (id TEXT, data BLOB);
        CREATE TABLE gen_metadata (idx INTEGER, data BLOB);
    """)
    payload = b'{"CommandLine":"pytest -q","cwd":"/workspace/demo"}'
    conn.execute("INSERT INTO steps VALUES (?,?,?,?,?,?)", (0, 21, 2, 0, payload, 1))
    conn.execute("INSERT INTO trajectory_metadata_blob VALUES (?,?)", ("meta", b"{}"))
    conn.execute("INSERT INTO gen_metadata VALUES (?,?)", (0, b"{}"))
    conn.commit()
    conn.close()

    session = read_antigravity_session({"db_path": str(db_path), "session_id": "antigravity-fixture-001"})
    assert "timestamp" not in session["entries"][0]
    assert session["metadata"]["extracted_at"]
    assert session["entries"][0]["code"] == "pytest -q"
    events = _export_and_validate(session, tmp_path / "antigravity.agentson", "antigravity")
    assert events[0]["source_session"]["source_metadata"]["variant"]["name"] == "Antigravity IDE"
    assert events[1]["source_payload"]["type"] == 21
