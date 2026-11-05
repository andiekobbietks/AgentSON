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

    event["agent"] = str(event.get("agent") or default_agent)
    if event.get("correlation_id") is not None:
        event["correlation_id"] = str(event["correlation_id"])
    else:
        event.pop("correlation_id", None)
    if event.get("duration_ms") is not None:
        try:
            event["duration_ms"] = int(event["duration_ms"])
        except (TypeError, ValueError):
            event.pop("duration_ms", None)
    if event.get("tool_call_id") is not None:
        event["tool_call_id"] = str(event["tool_call_id"])
    else:
        event.pop("tool_call_id", None)

    provenance = dict(_json_object(event.get("provenance")))
    allowed_confidence = {"confirmed", "inferred", "estimated", "ml_generated", "unknown"}
    allowed_sources = {"cdp", "mcp", "extension", "user", "system", "other", "export", "reconstructor"}
    if not isinstance(provenance.get("confidence"), str) or provenance.get("confidence") not in allowed_confidence:
        provenance["confidence"] = "inferred" if provenance else "unknown"
    if not isinstance(provenance.get("source"), str) or provenance.get("source") not in allowed_sources:
        provenance["source"] = "export"
    provenance.setdefault("source", "export")
    if provenance.get("timestamp_ms") is not None:
        try:
            provenance["timestamp_ms"] = int(provenance["timestamp_ms"])
        except (TypeError, ValueError):
            provenance.pop("timestamp_ms", None)
    event["provenance"] = provenance

    if event_type in {"user-query", "thought", "answer", "user-feedback"}:
        text_value = event.get("text")
        if text_value is None:
            text_value = event.get("query", "")
        event["text"] = str(text_value)
        if event.get("query") is not None and not isinstance(event["query"], str):
            event["query"] = str(event["query"])
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
        if isinstance(status, str) and status in {"completed", "complete", "done"}:
            event["status"] = "success"
        elif isinstance(status, str) and status in {"failed", "failure"}:
            event["status"] = "error"
        elif status is not None and (not isinstance(status, str) or status not in {"success", "error", "partial", "pending", "running"}):
            event["status"] = "partial"
    elif event_type == "observation":
        event["text"] = str(event.get("text", event.get("output", "")))
        source = event.get("source", "other")
        event["source"] = source if isinstance(source, str) and source in OBSERVATION_SOURCES else "other"
        if event.get("attachments") is not None and not isinstance(event["attachments"], list):
            event["attachments"] = [event["attachments"]]
    elif event_type == "system-event":
        event["text"] = str(event.get("text", event.get("message", "Source system event")))
        source = event.get("source", "other")
        event["source"] = source if isinstance(source, str) and source in SYSTEM_SOURCES else "other"
    elif event_type == "handoff":
        event["from"] = str(event.get("from") or default_agent)
        event["to"] = str(event.get("to") or "unknown")
        event["conch"] = str(event.get("conch") or event["to"])
    elif event_type == "presence":
        if not isinstance(event.get("status"), str) or event.get("status") not in {"online", "offline", "busy", "idle"}:
            event["status"] = "idle"
        if event.get("message") is not None:
            event["message"] = str(event["message"])
    elif event_type == "user-feedback":
        if not isinstance(event.get("sentiment"), str) or event.get("sentiment") not in {"positive", "negative", "neutral", "correction", "clarification"}:
            event["sentiment"] = "neutral"
    elif event_type == "capabilities":
        event["capabilities"] = _json_object(event.get("capabilities"))
    elif event_type == "side-effect":
        for field in ("action", "text", "status", "path", "diff"):
            if event.get(field) is not None and not isinstance(event[field], str):
                event[field] = json.dumps(event[field], ensure_ascii=False, default=str)

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
        if not isinstance(source_entries[0], dict):
            raise ValueError("Existing JSONL stream metadata at position 0 must be an object")
        meta = dict(source_entries[0])
        events = [meta]
        for position, item in enumerate(source_entries[1:], start=1):
            if not isinstance(item, dict):
                raise ValueError(f"Existing JSONL event at position {position} must be an object")
            events.append(_map_event(item, agent_id))

        meta.setdefault("schema_version", "1.2")
        meta.setdefault("stream_id", sid)
        meta.setdefault("mode", "single")
        meta.setdefault("agents", [{"id": agent_id, "name": agent_name}])
        source_session = _json_object(meta.get("source_session"))
        source_session.setdefault("tool", source_tool or str(tool_data.get("name") or "other"))
        source_session.setdefault("session_id", str(tool_data.get("session_id") or sid))
        source_session.setdefault("tool_metadata", tool_data)
        source_session.setdefault("agent_metadata", agent_data)
        for field in ("started_at", "ended_at", "heartbeat", "task", "outcome", "context", "metadata"):
            if field not in source_session and session.get(field) is not None:
                source_session[field] = session[field]
        reader_source_metadata = _json_object(session.get("source_metadata"))
        reader_source_metadata.update({
            key: value for key, value in session.items()
            if key not in {"entries", "id", "tool", "agent", "started_at", "ended_at", "heartbeat", "task", "outcome", "context", "metadata", "source_metadata"}
        })
        source_session.setdefault("source_metadata", reader_source_metadata)
        meta["source_session"] = source_session
        return events

    meta: Dict[str, Any] = {
        "type": "stream-meta",
        "schema_version": "1.2",
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
            # Preserve reader-specific session fields (for example Antigravity
            # variant/metrics/version) instead of silently dropping them.
            "source_metadata": {
                **_json_object(session.get("source_metadata")),
                **{
                    key: value for key, value in session.items()
                    if key not in {"entries", "id", "tool", "agent", "started_at", "ended_at", "heartbeat", "task", "outcome", "context", "metadata", "source_metadata"}
                },
            },
        },
    }
    events = [meta]
    for item in source_entries:
        events.append(_map_event(item, agent_id))
    return events



def load_agentson_document(path: Any) -> Dict[str, Any]:
    """Load canonical JSONL or a legacy document into the shared session view.

    The returned view keeps original stream events in entries and restores
    source-session metadata when it was recorded in stream-meta.
    """
    source_path = Path(path)
    content = source_path.read_text(encoding="utf-8").strip()
    if not content:
        raise ValueError("AgentSON file is empty")
    lines = [line.strip() for line in content.splitlines() if line.strip()]
    try:
        first_value = json.loads(lines[0])
    except json.JSONDecodeError:
        first_value = None

    is_jsonl = (
        isinstance(first_value, dict) and first_value.get("type") == "stream-meta"
    )
    if not is_jsonl and len(lines) > 1:
        try:
            for line in lines:
                json.loads(line)
            is_jsonl = True
        except json.JSONDecodeError:
            is_jsonl = False

    if is_jsonl:
        events = [json.loads(line) for line in lines]
        meta = events[0] if events and isinstance(events[0], dict) else {}
        source = _json_object(meta.get("source_session"))
        tool_data = _json_object(source.get("tool_metadata"))
        if not tool_data:
            tool_data = {
                "name": source.get("tool", "other"),
                "session_id": source.get("session_id", source_path.stem),
            }
        agent_data = _json_object(source.get("agent_metadata"))
        return {
            "id": meta.get("stream_id", source_path.stem),
            "tool": tool_data,
            "agent": agent_data,
            "started_at": source.get("started_at"),
            "ended_at": source.get("ended_at"),
            "heartbeat": source.get("heartbeat"),
            "task": source.get("task"),
            "outcome": source.get("outcome"),
            "context": source.get("context"),
            "metadata": source.get("metadata") or {},
            "source_session": source,
            "entries": events,
            "_format": "jsonl",
        }

    data = json.loads(content)
    if isinstance(data, list):
        return {
            "id": source_path.stem,
            "tool": {"name": "other", "session_id": source_path.stem},
            "entries": data,
            "_format": "legacy-list",
        }
    if not isinstance(data, dict):
        raise ValueError("Legacy AgentSON document must be a JSON object or event list")
    data.setdefault("_format", "document")
    return data


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

def write_agentson_stream_file(document: Any, output_path: Any, source_tool: Optional[str] = None) -> List[Dict[str, Any]]:
    """Validate and serialise a stream before atomically replacing its destination."""
    import os
    import tempfile

    events = to_v1_2_events(document, source_tool=source_tool)
    validate_v1_2_events(events)
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", dir=str(destination.parent), delete=False
        ) as temporary:
            temporary_path = temporary.name
            for event in events:
                temporary.write(json.dumps(event, ensure_ascii=False, separators=(",", ":"), default=str))
                temporary.write("\\n")
            temporary.flush()
            os.fsync(temporary.fileno())
        os.replace(temporary_path, destination)
        temporary_path = None
    finally:
        if temporary_path and os.path.exists(temporary_path):
            os.unlink(temporary_path)
    return events
