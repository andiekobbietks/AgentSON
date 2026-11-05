"""Exercise the production OpenCode reader against a sanitised real-shape sample.

Unlike a copied mapping function, this test calls OpencodeReader's actual
conversion method. The fixture is a single source message/parts export, so
session metadata is supplied as a minimal source-shaped record.
"""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from jsonschema import Draft202012Validator
from readers.opencode import OpencodeReader


ROOT = Path(__file__).resolve().parent
FIXTURE_PATH = ROOT / "fixtures" / "opencode_real_sample.json"
SCHEMA_PATH = ROOT.parent / "spec" / "v1.2.json"


def _convert_with_production_reader(fixture: dict) -> dict:
    message = fixture["message"]
    parts = fixture["parts"]
    session = {
        "id": message["sessionID"],
        "model": json.dumps({
            "id": message.get("modelID", "unknown"),
            "providerID": message.get("providerID", "opencode"),
            "variant": message.get("variant", "default"),
        }),
        "time_created": message["time"]["created"],
        "time_updated": message["time"]["completed"],
        "directory": message.get("path", {}).get("cwd", ""),
        "tokens_input": message.get("tokens", {}).get("input", 0),
        "tokens_output": message.get("tokens", {}).get("output", 0),
        "cost": message.get("cost", 0.0),
    }
    messages = [{
        "id": message["id"],
        "time_created": message["time"]["created"],
        "data": json.dumps({"role": message.get("role", "unknown")}),
    }]
    source_parts = [
        {
            "id": part.get("id", f"part-{index}"),
            "message_id": message["id"],
            "time_created": (part.get("time") or {}).get("start", message["time"]["created"]),
            "data": json.dumps(part),
        }
        for index, part in enumerate(parts)
    ]

    # The conversion method is the production mapping path used by read_session.
    reader = OpencodeReader.__new__(OpencodeReader)
    return reader._convert_to_agentson(session, messages, source_parts, [])


def test_real_sample_exercises_production_reader_and_keeps_reasoning():
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    archive = _convert_with_production_reader(fixture)

    thoughts = [entry for entry in archive["entries"] if entry["type"] == "thought"]
    assert len(thoughts) == 1
    assert thoughts[0]["text"] == "Now run the test script."


def test_real_sample_exercises_production_reader_and_keeps_tool_action():
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    archive = _convert_with_production_reader(fixture)

    actions = [entry for entry in archive["entries"] if entry["type"] == "action"]
    assert len(actions) == 1
    action = actions[0]
    assert action["tool"] == "bash"
    assert action["status"] == "success"
    assert "test_claude_code_run.py" in action["code"]
    assert "ALL TESTS PASSED" in action["output"]


def test_real_sample_reader_output_validates_against_v1_2_envelope():
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    archive = _convert_with_production_reader(fixture)
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    errors = list(Draft202012Validator(schema).iter_errors(archive))
    assert not errors, "; ".join(error.message for error in errors)


def test_real_sample_does_not_invent_an_observation():
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    archive = _convert_with_production_reader(fixture)
    assert any(entry["type"] == "action" for entry in archive["entries"])
    assert not any(entry["type"] == "observation" for entry in archive["entries"])
