"""MCP (Model Context Protocol) Importer for AgentSON.

Maps MCP protocol traces to AgentSON 12-primitive ontology.
MCP tools/call → action. tools/result → observation. error → system-event.
"""

import json
from datetime import datetime, timezone
from typing import Dict, List, Optional
import uuid


def import_mcp(
    trace_path: str,
    output_path: Optional[str] = None,
    session_id: Optional[str] = None,
) -> dict:
    """Import MCP trace file into AgentSON format.

    Args:
        trace_path: Path to MCP trace JSON file (array of MCP events)
        output_path: Optional path to write .agentson file
        session_id: Optional custom session ID

    Returns:
        AgentSON session dict
    """
    with open(trace_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    events = data if isinstance(data, list) else [data]

    if session_id is None:
        session_id = f"mcp-{uuid.uuid4().hex[:8]}"

    entries = []
    for event in events:
        entry = _mcp_event_to_entry(event)
        if entry:
            entries.append(entry)

    started_at = entries[0].get("timestamp") if entries else None
    ended_at = entries[-1].get("timestamp") if entries else None

    agentson = {
        "$schema": "https://agentson.dev/schema/v1.json",
        "id": session_id,
        "tool": {"name": "mcp", "version": "1.0", "session_id": session_id},
        "agent": {"name": "mcp-agent", "provider": "mcp", "variant": "default"},
        "started_at": _ts_to_iso(started_at) if started_at else None,
        "ended_at": _ts_to_iso(ended_at) if ended_at else None,
        "context": {"working_directory": "", "platform": "mcp", "shell": "mcp"},
        "entries": entries,
        "metadata": {
            "total_tokens": 0,
            "cost": 0.0,
            "messages": len(entries),
            "parts": len(events),
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "source_format": "mcp-trace",
        },
    }

    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(agentson, f, indent=2, ensure_ascii=False, default=str)

    return agentson


def _mcp_event_to_entry(event: dict) -> Optional[dict]:
    """Map a single MCP event to AgentSON entry."""
    method = event.get("method", "")
    params = event.get("params", {}) or {}
    result = event.get("result", {}) or {}
    error = event.get("error")
    ts = event.get("timestamp") or event.get("ts")

    if method == "tools/call":
        return {
            "type": "action",
            "tool": f"mcp/{params.get('name', 'unknown')}",
            "text": json.dumps(params.get("arguments", {}), default=str),
            "agent": "mcp-agent",
            "timestamp": ts,
        }

    if method == "tools/result":
        return {
            "type": "observation",
            "text": json.dumps(result, default=str)[:10000],
            "source": "mcp",
            "timestamp": ts,
        }

    if method in ("resources/read", "resources/list"):
        return {
            "type": "action",
            "tool": f"mcp/{method.replace('/', '.')}",
            "text": json.dumps(params, default=str),
            "agent": "mcp-agent",
            "timestamp": ts,
        }

    if method in ("prompts/get", "prompts/list"):
        return {
            "type": "action",
            "tool": f"mcp/{method.replace('/', '.')}",
            "text": json.dumps(params, default=str),
            "agent": "mcp-agent",
            "timestamp": ts,
        }

    if error:
        return {
            "type": "system-event",
            "text": json.dumps(error, default=str),
            "source": "mcp.error",
            "timestamp": ts,
        }

    if method == "initialize":
        return {
            "type": "system-event",
            "text": f"MCP initialized: {json.dumps(params, default=str)}",
            "source": "mcp.initialize",
            "timestamp": ts,
        }

    if method == "notifications/tools/list_changed":
        return {
            "type": "system-event",
            "text": "Tool list changed",
            "source": "mcp.notification",
            "timestamp": ts,
        }

    # Unrecognized events become observations
    if method:
        return {
            "type": "observation",
            "text": json.dumps({"method": method, "params": params, "result": result}, default=str)[:10000],
            "source": f"mcp.{method}",
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
