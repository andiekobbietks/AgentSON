"""End-to-end reader conformance using synthetic native-format fixtures.

Fixtures are deliberately labelled synthetic: they model documented source
shapes and contain no user data. They exercise the adapters, not just the
shared serializer.
"""
import base64
import hashlib
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
    assert any(e["type"] == "answer" and e["text"] == "The test suite passed." for e in session["entries"])
    assert any(e["type"] == "action" and e.get("tool_call_id") == "toolu_fixture_01" for e in session["entries"])
    unknown_block = next(e for e in session["entries"] if e["type"] == "system-event" and "future_block_kind" in e["text"])
    assert unknown_block["source_payload"]["block"]["payload"]["preserve"] is True
    unknown_record = next(e for e in session["entries"] if e["type"] == "system-event" and "queue-operation" in e["text"])
    assert unknown_record["source_payload"]["payload"]["id"] == "queued-01"
    assert session["source_metadata"]["unparsed_lines"][0]["raw_line"].startswith("{malformed")
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
    raw_markdown = (FIXTURES / "chrome_devtools_native_synthetic.md").read_text(encoding="utf-8")
    assert session["source_metadata"]["source_markdown"] == raw_markdown
    assert any(e["source_payload"].get("raw_ai_subsection") for e in session["entries"] if e["type"] == "action")
    events = _export_and_validate(session, tmp_path / "chrome.agentson", "chrome-devtools")
    assert events[0]["source_session"]["metadata"]["source_filename"].endswith("chrome_devtools_native_synthetic.md")
    assert events[0]["source_session"]["source_metadata"]["source_markdown_sha256"] == session["source_metadata"]["source_markdown_sha256"]


def test_libre_csv_fixture_through_reader(tmp_path):
    from readers.libre import read_libre_csv

    session = read_libre_csv(str(FIXTURES / "libre_sensor_native_synthetic.csv"))
    assert len(session["entries"]) == 3
    assert session["entries"][0]["data"]["reading_type"] == "CGM"
    assert session["entries"][0]["source_payload"]["raw_row"]["Glucose (mmol/L)"] == "5.5"
    assert session["source_metadata"]["source_headers"][0] == "Timestamp"
    assert len(session["source_metadata"]["rejected_rows"]) == 1
    assert session["source_metadata"]["rejected_rows"][0]["row"]["Timestamp"] == "not-a-timestamp"
    assert session["entries"][1]["data"]["source_raw"] == "Manual"
    assert session["entries"][1]["status"] == "low"
    events = _export_and_validate(session, tmp_path / "libre.agentson", "libre")
    observations = [e for e in events if e["type"] == "observation"]
    assert len(observations) == 3
    assert events[0]["source_session"]["source_metadata"]["metrics"]["total_readings"] == 3
    assert len(events[0]["source_session"]["source_metadata"]["rejected_rows"]) == 1
    exported_reading = next(e for e in events if e["type"] == "observation")
    assert exported_reading["source_payload"]["raw_row"]["Type"] == "CGM"


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
            cache_write_tokens INTEGER, cost_usd REAL, ts INTEGER, raw TEXT
        );
        CREATE TABLE session_peers (
            session_id TEXT, parent_session_id TEXT, agent_name TEXT,
            task_tree_id TEXT, created_at INTEGER
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
        }, {
            "tool_name": "bash", "tool_call_id": "mavis_tool_partial",
            "tool_call_status": 1, "tool_call_args": "not-json",
            "tool_call_result_data": "",
        }, {
            "tool_name": "bash", "tool_call_id": "mavis_tool_error",
            "tool_call_status": 3, "tool_call_args": json.dumps({"command": "false"}),
            "tool_call_result_data": "exit code 1",
        }],
        "msg_content": "The tests passed.",
    }
    conn.execute("INSERT INTO session_messages VALUES (?,?,?,?,?)",
                 ("msg-user", "mavis-fixture-001", "user", json.dumps(user_blob), 1793869201000))
    conn.execute("INSERT INTO session_messages VALUES (?,?,?,?,?)",
                 ("msg-assistant", "mavis-fixture-001", "assistant", json.dumps(assistant_blob), 1793869202000))
    conn.execute("INSERT INTO token_usage VALUES (?,?,?,?,?,?,?,?,?)",
                 ("mavis-fixture-001", 100, 50, 20, 10, 5, 0.01, 1793869202000,
                  json.dumps({"source": "mavis", "billing": "recorded"})))
    conn.execute("INSERT INTO session_peers VALUES (?,?,?,?,?)",
                 ("mavis-fixture-001", "parent-session", "planner", "tree-001", 1793869201500))
    conn.commit()
    conn.close()

    reader = MiniMaxReader(str(db_path))
    reader.connect()
    try:
        import pytest
        with pytest.raises(sqlite3.OperationalError):
            reader.conn.execute("CREATE TABLE should_not_be_created (id TEXT)")
        session = reader.read_session("mavis-fixture-001")
    finally:
        reader.disconnect()
    assert any(e["type"] == "user-query" for e in session["entries"])
    mavis_action = next(e for e in session["entries"] if e["type"] == "action" and e.get("tool_call_id") == "mavis_tool_01")
    assert mavis_action["source_payload"]["tool_call"]["tool_call_args"] == json.dumps({"command": "pytest -q"})
    assert mavis_action["source_payload"]["tool_call_args_raw"] == json.dumps({"command": "pytest -q"})
    mavis_actions = {e.get("tool_call_id"): e for e in session["entries"] if e["type"] == "action"}
    assert mavis_actions["mavis_tool_partial"]["status"] == "partial"
    assert mavis_actions["mavis_tool_partial"]["source_payload"]["tool_call_args_raw"] == "not-json"
    assert mavis_actions["mavis_tool_error"]["status"] == "error"
    assert any(e["type"] == "observation" and e.get("correlation_id") == "mavis_tool_01" for e in session["entries"])
    assert session["source_metadata"]["session_row"]["framework_session_id"] == "native-framework-session"
    assert session["source_metadata"]["token_usage_rows"][0]["reasoning_tokens"] == 20
    assert json.loads(session["source_metadata"]["token_usage_rows"][0]["raw"])["billing"] == "recorded"
    assert session["source_metadata"]["peer_rows"][0]["task_tree_id"] == "tree-001"
    events = _export_and_validate(session, tmp_path / "minimax.agentson", "minimax")
    assert events[0]["mode"] == "collab"
    assert events[0]["stream_id"] == "mavis-fixture-001"


def test_antigravity_sqlite_fixture_through_reader(tmp_path):
    from readers.antigravity import _connect_readonly, read_antigravity_session

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

    readonly = _connect_readonly(str(db_path))
    try:
        import pytest
        with pytest.raises(sqlite3.OperationalError):
            readonly.execute("CREATE TABLE should_not_be_created (id TEXT)")
    finally:
        readonly.close()

    session = read_antigravity_session({"db_path": str(db_path), "session_id": "antigravity-fixture-001"})
    assert "timestamp" not in session["entries"][0]
    assert session["metadata"]["extracted_at"]
    assert session["entries"][0]["code"] == "pytest -q"
    events = _export_and_validate(session, tmp_path / "antigravity.agentson", "antigravity")
    assert events[0]["source_session"]["source_metadata"]["variant"]["name"] == "Antigravity IDE"
    assert events[1]["source_payload"]["step_row"]["step_type"] == 21
    raw_step = base64.b64decode(events[1]["source_payload"]["step_payload_base64"])
    assert raw_step == payload
    assert events[1]["source_payload"]["step_payload_sha256"] == hashlib.sha256(payload).hexdigest()
    assert base64.b64decode(events[0]["source_session"]["source_metadata"]["trajectory_metadata_blobs"][0]["data_base64"]) == b"{}"


def test_opencode_sqlite_native_fixture_through_reader(tmp_path):
    from readers.opencode import OpencodeReader

    db_path = tmp_path / "opencode-synthetic.sqlite"
    conn = sqlite3.connect(db_path)
    conn.executescript("""
        CREATE TABLE session (
            id TEXT PRIMARY KEY, title TEXT, time_created INTEGER, time_updated INTEGER,
            model TEXT, agent TEXT, tokens_input INTEGER, tokens_output INTEGER,
            cost REAL, directory TEXT
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
    created = 1793869200000
    updated = 1793869500000
    conn.execute(
        "INSERT INTO session VALUES (?,?,?,?,?,?,?,?,?,?)",
        ("opencode-fixture-001", "Fixture task", created, updated,
         json.dumps({"id": "openai/gpt-test", "providerID": "openai", "variant": "high"}),
         "build", 120, 80, 0.02, "/workspace/agentson"),
    )
    conn.execute(
        "INSERT INTO message VALUES (?,?,?,?,?)",
        ("msg-user", "opencode-fixture-001", created + 1000, created + 1000,
         json.dumps({"role": "user", "agent": "build", "model": {"id": "openai/gpt-test"}})),
    )
    conn.execute(
        "INSERT INTO message VALUES (?,?,?,?,?)",
        ("msg-assistant", "opencode-fixture-001", created + 2000, created + 5000,
         json.dumps({"role": "assistant", "agent": "build", "model": {"id": "openai/gpt-test"},
                     "tokens": {"input": 120, "output": 80}, "cost": 0.02,
                     "finish": "tool-calls"})),
    )
    parts = [
        ("part-user", "msg-user", created + 1000,
         {"type": "text", "text": "Run the project tests."}),
        ("part-reasoning", "msg-assistant", created + 2100,
         {"type": "reasoning", "text": "Inspect the repository test configuration.",
          "time": {"start": created + 2100, "end": created + 2200}}),
        ("part-tool", "msg-assistant", created + 2300,
         {"type": "tool", "tool": "bash", "callID": "call_fixture_01",
          "state": {"status": "completed", "input": {"command": "pytest -q"},
                    "output": "5 passed", "time": {"start": created + 2300, "end": created + 4000}}}),
        ("part-answer", "msg-assistant", created + 4100,
         {"type": "text", "text": "All five tests passed."}),
    ]
    for part_id, message_id, timestamp, data in parts:
        conn.execute(
            "INSERT INTO part VALUES (?,?,?,?,?,?)",
            (part_id, "opencode-fixture-001", message_id, timestamp, timestamp, json.dumps(data)),
        )
    conn.execute(
        "INSERT INTO todo VALUES (?,?,?,?,?)",
        ("opencode-fixture-001", "Add native SQLite regression coverage", "completed", "high", 0),
    )
    conn.commit()
    conn.close()

    reader = OpencodeReader(str(db_path))
    reader.connect()
    try:
        import pytest
        with pytest.raises(sqlite3.OperationalError):
            reader.conn.execute("CREATE TABLE should_not_be_created (id TEXT)")
        listed = reader.list_sessions()
        session = reader.read_session("opencode-fixture-001")
    finally:
        reader.disconnect()

    assert listed[0]["id"] == "opencode-fixture-001"
    assert listed[0]["tokens_input"] == 120
    assert listed[0]["tokens_output"] == 80
    assert listed[0]["cost"] == 0.02
    assert session["tool"]["name"] == "opencode"
    assert session["agent"]["name"] == "openai/gpt-test"
    assert session["metadata"]["total_tokens"] == 200
    assert session["metadata"]["cost"] == 0.02
    assert session["metadata"]["messages"] == 2
    assert session["metadata"]["parts"] == 4
    assert session["context"]["working_directory"] == "/workspace/agentson"
    user_event = next(e for e in session["entries"] if e["type"] == "user-query")
    assert user_event["text"] == "Run the project tests."
    assert user_event["source_payload"]["message"]["id"] == "msg-user"
    assert json.loads(user_event["source_payload"]["part"]["data"])["text"] == "Run the project tests."
    thought = next(e for e in session["entries"] if e["type"] == "thought")
    assert "test configuration" in thought["text"]
    assert thought["source_payload"]["part"]["id"] == "part-reasoning"
    action = next(e for e in session["entries"] if e["type"] == "action")
    assert action["source_payload"]["part"]["id"] == "part-tool"
    assert json.loads(action["source_payload"]["part"]["data"])["callID"] == "call_fixture_01"
    assert action["tool"] == "bash"
    assert json.loads(action["code"]) == {"command": "pytest -q"}
    assert action["output"] == "5 passed"
    assert action["status"] == "success"
    assert any(e["type"] == "answer" and e["text"] == "All five tests passed." for e in session["entries"])
    todo = next(e for e in session["entries"] if e["type"] == "side-effect")
    assert todo["action"] == "todo_update"
    assert todo["source_payload"]["todo"]["content"] == "Add native SQLite regression coverage"
    assert "timestamp" not in todo

    events = _export_and_validate(session, tmp_path / "opencode.agentson", "opencode")
    assert events[0]["source_session"]["metadata"]["total_tokens"] == 200
    assert events[0]["source_session"]["context"]["working_directory"] == "/workspace/agentson"
    assert events[0]["source_session"]["source_metadata"]["session_row"]["id"] == "opencode-fixture-001"
    exported_action = next(e for e in events if e["type"] == "action" and e.get("tool") == "bash")
    assert exported_action["source_payload"]["part"]["id"] == "part-tool"
    assert any(e["type"] == "action" and e.get("tool") == "bash" for e in events)
    assert any(e["type"] == "side-effect" and e.get("action") == "todo_update" for e in events)


def test_opencode_sqlite_reader_rejects_unknown_session(tmp_path):
    from readers.opencode import OpencodeReader

    db_path = tmp_path / "empty-opencode.sqlite"
    conn = sqlite3.connect(db_path)
    conn.executescript("""
        CREATE TABLE session (
            id TEXT PRIMARY KEY, title TEXT, time_created INTEGER, time_updated INTEGER,
            model TEXT, agent TEXT, tokens_input INTEGER, tokens_output INTEGER,
            cost REAL, directory TEXT
        );
        CREATE TABLE message (id TEXT, session_id TEXT, time_created INTEGER, time_updated INTEGER, data TEXT);
        CREATE TABLE part (id TEXT, session_id TEXT, message_id TEXT, time_created INTEGER, time_updated INTEGER, data TEXT);
        CREATE TABLE todo (session_id TEXT, content TEXT, status TEXT, priority TEXT, position INTEGER);
    """)
    conn.commit()
    conn.close()
    reader = OpencodeReader(str(db_path))
    reader.connect()
    try:
        import pytest
        with pytest.raises(ValueError, match="not found"):
            reader.read_session("missing-session")
    finally:
        reader.disconnect()


def test_opencode_v2_sqlite_schema_and_state_fidelity(tmp_path):
    """Exercise the current session_v2/session_message/session_part schema."""
    from readers.opencode import OpencodeReader

    db_path = tmp_path / "opencode-v2-synthetic.sqlite"
    conn = sqlite3.connect(str(db_path))
    conn.executescript("""
        CREATE TABLE session_v2 (
            id TEXT PRIMARY KEY, project_id TEXT, workspace_id TEXT, parent_id TEXT,
            slug TEXT, directory TEXT, path TEXT, title TEXT, version TEXT,
            metadata TEXT, cost REAL, tokens_input INTEGER, tokens_output INTEGER,
            tokens_reasoning INTEGER, tokens_cache_read INTEGER, tokens_cache_write INTEGER,
            agent TEXT, model TEXT, time_created INTEGER, time_updated INTEGER,
            time_archived INTEGER
        );
        CREATE TABLE session_message (
            id TEXT PRIMARY KEY, session_id TEXT, type TEXT, seq INTEGER,
            time_created INTEGER, time_updated INTEGER, data TEXT
        );
        CREATE TABLE session_part (
            message_id TEXT, session_id TEXT, ordinal INTEGER, type TEXT,
            call_id TEXT, time_created INTEGER, time_updated INTEGER, data TEXT
        );
        CREATE TABLE session_inbox (
            id TEXT PRIMARY KEY, session_id TEXT, type TEXT, payload TEXT,
            delivery TEXT, enqueued_seq INTEGER, time_created INTEGER
        );
    """)
    start = 1793869200000
    model = {"id": "openai/gpt-test", "providerID": "openai", "variant": "high"}
    conn.execute(
        "INSERT INTO session_v2 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        ("ses-v2-fixture", "project-fixture", None, None, "fixture", "/workspace/v2",
         "{}", "OpenCode v2 fidelity", "2.2.5", json.dumps({"purpose": "conformance"}),
         0.03, 200, 90, 12, 40, 5, "build", json.dumps(model),
         start, start + 9000, None),
    )
    messages = [
        ("msg-v2-user", "user", 1, {"text": "Run the v2 test suite.", "files": [], "agents": [], "skills": []}),
        ("msg-v2-assistant", "assistant", 2, {
            "agent": "build", "model": model, "finish": "tool-calls",
            "cost": 0.03, "tokens": {"input": 200, "output": 90, "reasoning": 12},
            "time": {"created": start + 1000, "completed": start + 8000},
        }),
        ("msg-v2-shell", "shell", 3, {
            "command": "git status --short", "status": "completed", "exit": 0,
            "output": "working tree clean",
        }),
        ("msg-v2-idle", "idle", 4, {"outcome": "succeeded"}),
        ("msg-v2-future", "future-kind", 5, {"opaque": {"preserve": True}}),
    ]
    for message_id, msg_type, seq, data in messages:
        conn.execute(
            "INSERT INTO session_message VALUES (?,?,?,?,?,?,?)",
            (message_id, "ses-v2-fixture", msg_type, seq, start + seq * 1000,
             start + seq * 1000, json.dumps(data)),
        )
    parts = [
        ("msg-v2-assistant", 0, "reasoning", None, start + 2100,
         {"type": "reasoning", "text": "Inspect the current v2 schema.",
          "time": {"created": start + 2100, "completed": start + 2200}}),
        ("msg-v2-assistant", 1, "tool", "call-v2-complete", start + 3000,
         {"type": "tool", "id": "tool-v2-complete", "name": "bash",
          "state": {"status": "completed", "input": {"command": "pytest -q"},
                    "content": [{"type": "text", "text": "7 passed"}],
                    "metadata": {"exit": 0}}}),
        ("msg-v2-assistant", 2, "tool", "call-v2-error", start + 4000,
         {"type": "tool", "id": "tool-v2-error", "name": "bash",
          "state": {"status": "error", "input": {"command": "false"},
                    "error": {"name": "ToolError", "message": "exit code 1"},
                    "content": [{"type": "text", "text": "exit code 1"}]}}),
        ("msg-v2-assistant", 3, "tool", "call-v2-running", start + 5000,
         {"type": "tool", "id": "tool-v2-running", "name": "read",
          "state": {"status": "running", "input": {"filePath": "README.md"},
                    "metadata": {"partial": True}}}),
        ("msg-v2-assistant", 4, "text", None, start + 6000,
         {"type": "text", "text": "The v2 export has completed."}),
    ]
    for message_id, ordinal, part_type, call_id, timestamp, data in parts:
        conn.execute(
            "INSERT INTO session_part VALUES (?,?,?,?,?,?,?,?)",
            (message_id, "ses-v2-fixture", ordinal, part_type, call_id,
             timestamp, timestamp, json.dumps(data)),
        )
    inbox_payload = {"text": "Please also inspect the README."}
    conn.execute(
        "INSERT INTO session_inbox VALUES (?,?,?,?,?,?,?)",
        ("inbox-v2-1", "ses-v2-fixture", "user", json.dumps(inbox_payload),
         "delivered", 6, start + 7000),
    )
    conn.commit()
    conn.close()

    reader = OpencodeReader(str(db_path))
    reader.connect()
    try:
        assert reader.schema_generation == "2.x"
        import pytest
        with pytest.raises(sqlite3.OperationalError):
            reader.conn.execute("CREATE TABLE should_not_be_created (id TEXT)")
        listed = reader.list_sessions()
        session = reader.read_session("ses-v2-fixture")
    finally:
        reader.disconnect()

    assert listed[0]["id"] == "ses-v2-fixture"
    assert listed[0]["parent_id"] is None
    assert listed[0]["tokens_input"] == 200
    assert session["tool"]["version"] == "2.2.5"
    assert session["agent"]["name"] == "openai/gpt-test"
    assert session["metadata"]["tokens_reasoning"] == 12
    assert session["metadata"]["tokens_cache_read"] == 40
    assert session["metadata"]["total_tokens"] == 302
    assert session["context"]["working_directory"] == "/workspace/v2"

    user = next(e for e in session["entries"] if e["type"] == "user-query")
    assert user["text"] == "Run the v2 test suite."
    thought = next(e for e in session["entries"] if e["type"] == "thought")
    assert thought["text"] == "Inspect the current v2 schema."
    actions = [e for e in session["entries"] if e["type"] == "action"]
    by_id = {e.get("tool_call_id"): e for e in actions}
    assert by_id["call-v2-complete"]["status"] == "success"
    assert by_id["call-v2-complete"]["output"] == "7 passed"
    assert by_id["call-v2-error"]["status"] == "error"
    assert "exit code 1" in by_id["call-v2-error"]["output"]
    assert by_id["call-v2-running"]["status"] == "running"
    assert by_id["call-v2-running"]["source_payload"]["part_data"]["state"]["metadata"]["partial"]
    shell = next(e for e in actions if e["tool"] == "shell")
    assert shell["code"] == "git status --short"
    assert shell["output"] == "working tree clean"

    future = next(e for e in session["entries"] if e["type"] == "system-event" and "future-kind" in e["text"])
    assert future["source_payload"]["message_data"]["opaque"]["preserve"] is True
    inbox = next(e for e in session["entries"] if e["type"] == "system-event" and "inbox" in e["text"])
    assert inbox["source_payload"]["inbox"]["payload"] == json.dumps(inbox_payload)

    events = _export_and_validate(session, tmp_path / "opencode-v2.agentson", "opencode")
    exported = next(e for e in events if e.get("tool_call_id") == "call-v2-complete")
    assert exported["source_payload"]["part_data"]["id"] == "tool-v2-complete"
    assert events[0]["source_session"]["source_metadata"]["schema_generation"] == "2.x"
    assert events[0]["source_session"]["source_metadata"]["session_row"]["version"] == "2.2.5"
