"""Canonical AgentSON v1.2 JSONL serialization.

The public .agentson extension is intentionally retained. Files written by this
module contain one v1.2 event per line; legacy document exports remain readable
through the compatibility loader.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

VALID_TYPES = {
    "stream-meta", "handoff", "presence", "capabilities", "action",
    "observation", "thought", "side-effect", "answer", "user-query",
    "user-feedback", "system-event",
}
OBSERVATION_SOURCES = {"agent", "user", "system", "tool", "sensor", "extension", "other"}
SYSTEM_SOURCES = {"cron", "webhook", "timer", "healthcheck", "manual", "other", "reconstructor"}


def _session_id(value: Any) -> str:
    candidate = re.sub(r"[^a-zA-Z0-9_-]+", "-", str(value or "session")).strip("-_")
    return candidate or "session"


def _timestamp_ms(value: Any) -> Optional[int]:
    """Convert a source timestamp to Unix milliseconds without inventing one."""
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        number = int(value)
        return number if abs(number) >= 10**12 else number * 1000
    if isinstance(value, str):
        stripped = value.strip()
        if stripped.isdigit():
            number = int(stripped)
            return number if number >= 10**12 else number * 1000
        try:
            parsed = datetime.fromisoformat(stripped.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                return None
            return int(parsed.timestamp() * 1000)
        except (ValueError, OverflowError):
            return None
    return None


def _json_object(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _map_event(source_event: Any, default_agent: str) -> Dict[str, Any]:
    raw = source_event if isinstance(source_event, dict) else {"value": source_event}
    event = dict(raw)
    old_type = str(event.get("type") or event.get("event") or "").strip()
    aliases = {
        "user": "user-query", "human": "user-query", "prompt": "user-query",
        "assistant": "answer", "tool_call": "action", "tool_use": "action",
        "tool_result": "observation", "error": "system-event",
    }
    event_type = aliases.get(old_type, old_type)
    if event_type not in VALID_TYPES or event_type == "stream-meta":
        event_type = "system-event"
        event["text"] = (
            "Unmapped source event retained in source_payload"
            if old_type else "Source record retained in source_payload"
        )
        event["source"] = "other"
        event["provenance"] = {"source": "export", "confidence": "unknown"}
    event["type"] = event_type

    timestamp = _timestamp_ms(event.get("timestamp"))
    if timestamp is None:
        event.pop("timestamp", None)
    else:
        event["timestamp"] = timestamp

    event.setdefault("agent", default_agent)
    provenance = _json_object(event.get("provenance"))
    if not provenance:
        provenance = {"source": "export", "confidence": "inferred"}
    event["provenance"] = provenance

    if event_type in {"user-query", "thought", "answer", "user-feedback"}:
        text_value = event.get("text")
        if text_value is None:
            text_value = event.get("query", "")
        event["text"] = str(text_value)
    elif event_type == "action":
        tool = event.get("tool") or event.get("tool_name") or event.get("name")
        event["tool"] = str(tool or "unknown")
        args = event.get("args")
        if not isinstance(args, dict):
            event.pop("args", None)
        if event.get("code") is not None and not isinstance(event["code"], str):
            event["code"] = json.dumps(event["code"], ensure_ascii=False, default=str)
        if event.get("output") is not None and not isinstance(event["output"], str):
            event["output"] = json.dumps(event["output"], ensure_ascii=False, default=str)
        status = event.get("status")
        if status in {"completed", "complete", "done"}:
            event["status"] = "success"
        elif status in {"failed", "failure"}:
            event["status"] = "error"
        elif status not in {None, "success", "error", "partial", "pending", "running"}:
            event["status"] = "partial"
    elif event_type == "observation":
        event["text"] = str(event.get("text", event.get("output", "")))
        source = event.get("source", "other")
        event["source"] = source if source in OBSERVATION_SOURCES else "other"
    elif event_type == "system-event":
        event["text"] = str(event.get("text", event.get("message", "Source system event")))
        source = event.get("source", "other")
        event["source"] = source if source in SYSTEM_SOURCES else "other"
    elif event_type == "handoff":
        event.setdefault("from", default_agent)
        event.setdefault("to", "unknown")
        event.setdefault("conch", event.get("to", "unknown"))
    elif event_type == "presence":
        event.setdefault("status", "idle")
    elif event_type == "capabilities":
        event["capabilities"] = _json_object(event.get("capabilities"))
    elif event_type == "side-effect":
        if event.get("action") is not None:
            event["action"] = str(event["action"])

    # Preserve the exact reader-level record alongside its canonical projection.
    if "source_payload" not in event and raw != event:
        event["source_payload"] = raw
    return event


def to_v1_2_events(document: Any, source_tool: Optional[str] = None) -> List[Dict[str, Any]]:
    """Convert a reader's legacy session document (or event list) to v1.2 events."""
    if isinstance(document, list):
        session: Dict[str, Any] = {}
        source_entries = document
    elif isinstance(document, dict):
        session = document
        source_entries = document.get("entries", [])
        if not isinstance(source_entries, list):
            raise ValueError("Session document 'entries' must be a list")
    else:
        raise ValueError("Reader must return a session object or a list of events")

    tool_data = _json_object(session.get("tool"))
    agent_data = _json_object(session.get("agent"))
    sid = _session_id(session.get("id") or tool_data.get("session_id") or "session")
    agent_id = "assistant"
    agent_name = str(agent_data.get("name") or agent_data.get("model") or "Assistant")

    existing_stream = bool(source_entries and isinstance(source_entries[0], dict)
                           and source_entries[0].get("type") == "stream-meta")
    if existing_stream:
        events = [dict(item) if isinstance(item, dict) else {"type": "system-event", "text": str(item), "source": "other"}
                  for item in source_entries]
        meta = events[0]
        meta.setdefault("stream_id", sid)
        meta.setdefault("mode", "single")
        meta.setdefault("agents", [{"id": agent_id, "name": agent_name}])
        if source_tool and "source_session" not in meta:
            meta["source_session"] = {
                "tool": source_tool,
                "session_id": str(tool_data.get("session_id") or sid),
            }
        return events

    meta: Dict[str, Any] = {
        "type": "stream-meta",
        "stream_id": sid,
        "mode": "single",
        "agents": [{"id": agent_id, "name": agent_name}],
        "provenance": {"source": "export", "confidence": "inferred"},
        "source_session": {
            "tool": source_tool or str(tool_data.get("name") or "other"),
            "session_id": str(tool_data.get("session_id") or sid),
            "tool_metadata": tool_data,
            "agent_metadata": agent_data,
            "started_at": session.get("started_at") or session.get("timestamp"),
            "ended_at": session.get("ended_at"),
            "heartbeat": session.get("heartbeat"),
            "task": session.get("task"),
            "outcome": session.get("outcome"),
            "context": session.get("context"),
            "metadata": session.get("metadata"),
        },
    }
    events = [meta]
    for item in source_entries:
        events.append(_map_event(item, agent_id))
    return events


def validate_v1_2_events(events: Iterable[Dict[str, Any]]) -> None:
    """Validate event structure and stream ordering against the packaged schema."""
    try:
        from jsonschema import Draft202012Validator, FormatChecker
    except ImportError as exc:
        raise RuntimeError("JSON Schema validation requires the 'jsonschema' package") from exc

    schema_path = Path(__file__).resolve().parent.parent / "spec" / "v1.2-entries.json"
    with schema_path.open("r", encoding="utf-8") as handle:
        schema = json.load(handle)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    materialised = list(events)
    if not materialised or materialised[0].get("type") != "stream-meta":
        raise ValueError("A v1.2 JSONL stream must begin with a stream-meta event")
    errors = []
    for index, event in enumerate(materialised, start=1):
        for error in validator.iter_errors(event):
            errors.append("line {}: {}".format(index, error.message))
    if errors:
        raise ValueError("Invalid AgentSON v1.2 stream:\n" + "\n".join(errors))


def write_agentson_stream(document: Any, handle: Any, source_tool: Optional[str] = None) -> List[Dict[str, Any]]:
    """Write canonical v1.2 JSONL while retaining the .agentson filename extension."""
    events = to_v1_2_events(document, source_tool=source_tool)
    validate_v1_2_events(events)
    for event in events:
        handle.write(json.dumps(event, ensure_ascii=False, separators=(",", ":"), default=str))
        handle.write("\n")
    return events
