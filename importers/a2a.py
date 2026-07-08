"""A2A (Agent-to-Agent) Protocol Importer for AgentSON.

Maps A2A protocol traces to AgentSON 12-primitive ontology.
A2A handoff → handoff. delegation → action. result → observation. status → presence.
"""

import json
from datetime import datetime, timezone
from typing import Dict, List, Optional
import uuid


def import_a2a(
    trace_path: str,
    output_path: Optional[str] = None,
    session_id: Optional[str] = None,
) -> dict:
    """Import A2A trace file into AgentSON format.

    Args:
        trace_path: Path to A2A trace JSON file (array of A2A events)
        output_path: Optional path to write .agentson file
        session_id: Optional custom session ID

    Returns:
        AgentSON session dict
    """
    with open(trace_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    events = data if isinstance(data, list) else [data]

    if session_id is None:
        session_id = f"a2a-{uuid.uuid4().hex[:8]}"

    entries = []
    agents_seen = set()
    for event in events:
        entry = _a2a_event_to_entry(event)
        if entry:
            entries.append(entry)
            agent = entry.get("agent") or entry.get("to") or entry.get("from")
            if agent:
                agents_seen.add(agent)

    started_at = entries[0].get("timestamp") if entries else None
    ended_at = entries[-1].get("timestamp") if entries else None

    agentson = {
        "$schema": "https://agentson.dev/schema/v1.json",
        "id": session_id,
        "tool": {"name": "a2a", "version": "1.0", "session_id": session_id},
        "agent": {"name": "a2a-orchestrator", "provider": "a2a", "variant": "default"},
        "started_at": _ts_to_iso(started_at) if started_at else None,
        "ended_at": _ts_to_iso(ended_at) if ended_at else None,
        "context": {"working_directory": "", "platform": "a2a", "shell": "a2a"},
        "entries": entries,
        "metadata": {
            "total_tokens": 0,
            "cost": 0.0,
            "messages": len(entries),
            "parts": len(events),
            "agents_involved": list(agents_seen),
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "source_format": "a2a-trace",
        },
    }

    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(agentson, f, indent=2, ensure_ascii=False, default=str)

    return agentson


def _a2a_event_to_entry(event: dict) -> Optional[dict]:
    """Map a single A2A event to AgentSON entry."""
    event_type = event.get("type", "")
    payload = event.get("payload", {}) or {}
    ts = event.get("timestamp") or event.get("ts")

    if event_type == "handoff":
        return {
            "type": "handoff",
            "from": payload.get("from", "unknown"),
            "to": payload.get("to", "unknown"),
            "conch": payload.get("conch", payload.get("context", "")),
            "timestamp": ts,
        }

    if event_type == "delegation":
        return {
            "type": "action",
            "tool": f"a2a/delegate.{payload.get('target', 'unknown')}",
            "text": json.dumps(payload.get("task", {}), default=str),
            "agent": payload.get("from", "unknown"),
            "timestamp": ts,
        }

    if event_type == "result":
        return {
            "type": "observation",
            "text": json.dumps(payload.get("output", payload), default=str)[:10000],
            "source": f"a2a/{payload.get('from', 'unknown')}",
            "timestamp": ts,
        }

    if event_type == "status":
        return {
            "type": "presence",
            "status": payload.get("status", "unknown"),
            "agent": payload.get("agent", "unknown"),
            "timestamp": ts,
        }

    if event_type == "capabilities":
        return {
            "type": "capabilities",
            "agent": payload.get("agent", "unknown"),
            "capabilities": payload.get("capabilities", []),
            "timestamp": ts,
        }

    if event_type == "error":
        return {
            "type": "system-event",
            "text": json.dumps(payload.get("error", payload), default=str),
            "source": "a2a.error",
            "timestamp": ts,
        }

    if event_type == "message":
        role = payload.get("role", "unknown")
        text = payload.get("text", "")
        if role == "user":
            return {"type": "user-query", "text": text, "agent": payload.get("agent"), "timestamp": ts}
        if role == "assistant":
            return {"type": "answer", "text": text, "agent": payload.get("agent"), "timestamp": ts}
        return {"type": "observation", "text": text, "source": f"a2a/{role}", "timestamp": ts}

    if event_type in ("task/create", "task/assign"):
        return {
            "type": "system-event",
            "text": json.dumps(payload, default=str),
            "source": f"a2a.{event_type.replace('/', '.')}",
            "timestamp": ts,
        }

    if event_type:
        return {
            "type": "observation",
            "text": json.dumps({"type": event_type, "payload": payload}, default=str)[:10000],
            "source": f"a2a.{event_type}",
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
