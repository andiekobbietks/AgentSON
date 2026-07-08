"""AGNTCY Agent Protocol Importer for AgentSON.

Maps AGNTCY protocol traces to AgentSON 12-primitive ontology.
AGNTCY task → system-event. step → action. artifact → observation.
"""

import json
from datetime import datetime, timezone
from typing import Dict, List, Optional
import uuid


def import_agntcy(
    trace_path: str,
    output_path: Optional[str] = None,
    session_id: Optional[str] = None,
) -> dict:
    """Import AGNTCY trace file into AgentSON format.

    Args:
        trace_path: Path to AGNTCY trace JSON file (array of AGNTCY events)
        output_path: Optional path to write .agentson file
        session_id: Optional custom session ID

    Returns:
        AgentSON session dict
    """
    with open(trace_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    events = data if isinstance(data, list) else [data]

    if session_id is None:
        session_id = f"agntcy-{uuid.uuid4().hex[:8]}"

    entries = []
    for event in events:
        entry = _agntcy_event_to_entry(event)
        if entry:
            entries.append(entry)

    started_at = entries[0].get("timestamp") if entries else None
    ended_at = entries[-1].get("timestamp") if entries else None

    agentson = {
        "$schema": "https://agentson.dev/schema/v1.json",
        "id": session_id,
        "tool": {"name": "agntcy", "version": "1.0", "session_id": session_id},
        "agent": {"name": "agntcy-agent", "provider": "agntcy", "variant": "default"},
        "started_at": _ts_to_iso(started_at) if started_at else None,
        "ended_at": _ts_to_iso(ended_at) if ended_at else None,
        "context": {"working_directory": "", "platform": "agntcy", "shell": "agntcy"},
        "entries": entries,
        "metadata": {
            "total_tokens": 0,
            "cost": 0.0,
            "messages": len(entries),
            "parts": len(events),
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "source_format": "agntcy-trace",
        },
    }

    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(agentson, f, indent=2, ensure_ascii=False, default=str)

    return agentson


def _agntcy_event_to_entry(event: dict) -> Optional[dict]:
    """Map a single AGNTCY event to AgentSON entry."""
    kind = event.get("kind", event.get("type", ""))
    spec = event.get("spec", event.get("payload", {})) or {}
    status = event.get("status", {}) or {}
    ts = event.get("timestamp") or event.get("ts")

    if kind == "Task":
        return {
            "type": "system-event",
            "text": json.dumps({"task": spec.get("input", spec), "status": status}, default=str),
            "source": "agntcy.task",
            "timestamp": ts,
        }

    if kind == "Step":
        step_input = spec.get("input", {})
        step_name = spec.get("name", spec.get("id", "unknown"))
        tool_call = step_input.get("tool") or spec.get("tool")
        if tool_call:
            return {
                "type": "action",
                "tool": f"agntcy/{tool_call}",
                "text": json.dumps(step_input, default=str)[:10000],
                "agent": spec.get("agent", "agntcy-agent"),
                "timestamp": ts,
            }
        return {
            "type": "action",
            "tool": f"agntcy/step.{step_name}",
            "text": json.dumps(step_input, default=str)[:10000],
            "agent": spec.get("agent", "agntcy-agent"),
            "timestamp": ts,
        }

    if kind == "Artifact":
        return {
            "type": "observation",
            "text": json.dumps(spec.get("content", spec), default=str)[:10000],
            "source": f"agntcy/artifact.{spec.get('name', 'unknown')}",
            "timestamp": ts,
        }

    if kind == "AgentMessage":
        role = spec.get("role", "unknown")
        text = spec.get("text", spec.get("content", ""))
        if role == "user":
            return {"type": "user-query", "text": text, "agent": spec.get("agent"), "timestamp": ts}
        if role == "assistant":
            return {"type": "answer", "text": text, "agent": spec.get("agent"), "timestamp": ts}
        return {"type": "observation", "text": text, "source": f"agntcy/{role}", "timestamp": ts}

    if kind == "Error":
        return {
            "type": "system-event",
            "text": json.dumps(status.get("error", spec), default=str),
            "source": "agntcy.error",
            "timestamp": ts,
        }

    if kind in ("TaskState", "StateChange"):
        return {
            "type": "system-event",
            "text": json.dumps({"state": status, "spec": spec}, default=str),
            "source": f"agntcy.{kind.lower()}",
            "timestamp": ts,
        }

    if kind == "ToolCall":
        return {
            "type": "action",
            "tool": f"agntcy/{spec.get('name', 'unknown')}",
            "text": json.dumps(spec.get("arguments", spec), default=str),
            "agent": spec.get("agent", "agntcy-agent"),
            "timestamp": ts,
        }

    if kind == "ToolResult":
        return {
            "type": "observation",
            "text": json.dumps(spec.get("result", spec), default=str)[:10000],
            "source": f"agntcy/tool.{spec.get('name', 'unknown')}",
            "timestamp": ts,
        }

    if kind:
        return {
            "type": "observation",
            "text": json.dumps({"kind": kind, "spec": spec, "status": status}, default=str)[:10000],
            "source": f"agntcy.{kind.lower()}",
            "timestamp": ts,
        }

    return None


def _ts_to_iso(ts) -> Optional[str]:
    if ts is None:
        return None
    try:
        return datetime.fromtimestamp(ts / 1000, tz=timezone.utc).isoformat()
    except (TypeError, OSError):
        try:
            return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
        except (TypeError, OSError):
            return str(ts)
