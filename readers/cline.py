"""
AgentSON Reader: cline
======================

Reads session data from Cline (formerly Claude Dev) VS Code extension.

Storage locations:
  - macOS: ~/Library/Application Support/Code/User/globalStorage/saoudrizwan.claude-dev/tasks/
  - Linux: ~/.config/Code/User/globalStorage/saoudrizwan.claude-dev/tasks/
  - Windows: %APPDATA%\\Code\\User\\globalStorage\\saoudrizwan.claude-dev\\tasks\\

  Also supports Cursor, Windsurf, and other VS Code variants:
  - Cursor: Cursor/User/globalStorage/saoudrizwan.claude-dev/tasks/
  - Windsurf: Windsurf/User/globalStorage/saoudrizwan.claude-dev/tasks/

Each task is a ULID-named directory containing:
  - ui_messages.json              — messages formatted for the Webview UI
  - api_conversation_history.json — raw conversation history for LLM API
  - task_metadata.json            — files in context, model usage, env history
  - history_item.json             — per-task history (tokens, timestamps, status)
  - context_history.json          — context tracking history

Message roles in api_conversation_history.json:
  - "user" with content as array of blocks:
      { type: "text", text: "..." }
      { type: "tool_use", id: "...", name: "...", input: {...} }
  - "assistant" with content blocks:
      { type: "text", text: "..." }
      { type: "thinking", thinking: "..." }
      { type: "tool_result", tool_use_id: "...", content: "..." }
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


SCHEMA_URI = "https://agentson.dev/schema/v1.1.json"

# Extension ID used by Cline (originally "Claude Dev")
CLINE_EXT_ID = "saoudrizwan.claude-dev"


def _get_tasks_dir() -> Optional[Path]:
    """Return the default Cline tasks directory for the current OS."""
    home = Path.home()
    candidates = [
        home / "Library" / "Application Support" / "Code" / "User" / "globalStorage" / CLINE_EXT_ID / "tasks",
        home / ".config" / "Code" / "User" / "globalStorage" / CLINE_EXT_ID / "tasks",
        home / "Library" / "Application Support" / "Cursor" / "User" / "globalStorage" / CLINE_EXT_ID / "tasks",
        home / ".config" / "Cursor" / "User" / "globalStorage" / CLINE_EXT_ID / "tasks",
        home / ".cline" / "data" / "tasks",
    ]
    appdata = os.environ.get("APPDATA")
    if appdata:
        candidates.insert(0, Path(appdata) / "Code" / "User" / "globalStorage" / CLINE_EXT_ID / "tasks")
    for p in candidates:
        if p.exists():
            return p
    return None


def list_sessions(tasks_dir: str, limit: int = 50) -> List[Dict]:
    """List all Cline tasks in the given directory."""
    td = Path(tasks_dir)
    if not td.exists():
        raise FileNotFoundError(f"Tasks directory not found: {td}")

    sessions = []
    for task_dir in sorted(td.iterdir(), reverse=True):
        if not task_dir.is_dir():
            continue
        history_file = task_dir / "history_item.json"
        if history_file.exists():
            try:
                with open(history_file, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                sessions.append({
                    "id": task_dir.name,
                    "title": meta.get("task", task_dir.name)[:100],
                    "created": meta.get("ts"),
                    "model": meta.get("modelId", ""),
                    "tokens_in": meta.get("tokensIn", 0),
                    "tokens_out": meta.get("tokensOut", 0),
                    "status": meta.get("status", ""),
                })
            except (json.JSONDecodeError, OSError):
                continue
        if len(sessions) >= limit:
            break
    return sessions


def read_session(tasks_dir: str, task_id: str) -> Dict:
    """Read a Cline session by task ID (ULID directory name) and convert to AgentSON."""
    td = Path(tasks_dir)
    task_dir = td / task_id
    if not task_dir.exists():
        raise FileNotFoundError(f"Task directory not found: {task_dir}")

    # Load API conversation history (primary source)
    api_file = task_dir / "api_conversation_history.json"
    history_file = task_dir / "history_item.json"
    metadata_file = task_dir / "task_metadata.json"

    api_messages = _load_json(api_file) or []
    history = _load_json(history_file) or {}
    metadata = _load_json(metadata_file) or {}

    # Convert to AgentSON entries
    entries = _api_messages_to_entries(api_messages)

    # Build document
    model_id = history.get("modelId", "")
    doc = {
        "$schema": SCHEMA_URI,
        "id": task_id,
        "title": history.get("task", task_id[:20]),
        "tool": {
            "name": "cline",
            "version": "latest",
            "session_id": task_id,
        },
        "agent": {
            "name": model_id,
            "provider": _extract_provider(model_id),
            "variant": history.get("mode", "act"),
        },
        "entries": entries,
    }

    # v1.1 trajectory fields
    first_user = next((e for e in entries if e["type"] == "user-query"), None)
    if first_user:
        doc["task"] = first_user["text"][:200]

    answers = sum(1 for e in entries if e["type"] == "answer")
    if answers == 0:
        doc["outcome"] = "aborted"
    elif entries and entries[-1]["type"] == "answer":
        doc["outcome"] = "success"
    else:
        doc["outcome"] = "partial"

    if history.get("ts"):
        doc["started_at"] = _ms_to_iso(history["ts"])

    total_in = sum(m.get("tokensIn", 0) for m in metadata.get("model_usage", []))
    total_out = sum(m.get("tokensOut", 0) for m in metadata.get("model_usage", []))
    doc["metadata"] = {
        "exported_at": datetime.utcnow().isoformat() + "Z",
        "source": "cline",
        "total_tokens_in": total_in,
        "total_tokens_out": total_out,
        "messages": len(api_messages),
        "files_in_context": len(metadata.get("files_in_context", [])),
    }

    return doc


def _api_messages_to_entries(messages: List[Dict]) -> List[Dict]:
    """Convert Cline API conversation history to AgentSON entries."""
    entries: List[Dict] = []

    for msg in messages:
        role = msg.get("role", "")
        content = msg.get("content", "")
        ts = msg.get("ts")

        if role == "user":
            # content can be string or array of blocks
            if isinstance(content, str):
                if content.strip():
                    entries.append({"type": "user-query", "text": content, "timestamp": ts})
            elif isinstance(content, list):
                for block in content:
                    if not isinstance(block, dict):
                        continue
                    btype = block.get("type", "")
                    if btype == "text":
                        text = block.get("text", "").strip()
                        if text:
                            entries.append({"type": "user-query", "text": text, "timestamp": ts})
                    elif btype == "tool_result":
                        entries.append({
                            "type": "observation",
                            "text": str(block.get("content", ""))[:2000],
                            "source": "tool",
                            "correlation_id": block.get("tool_use_id", ""),
                            "status": "error" if block.get("is_error") else "success",
                            "timestamp": ts,
                        })

        elif role == "assistant":
            if isinstance(content, list):
                for block in content:
                    if not isinstance(block, dict):
                        continue
                    btype = block.get("type", "")
                    if btype == "text":
                        text = block.get("text", "").strip()
                        if text:
                            entries.append({"type": "answer", "text": text, "timestamp": ts})
                    elif btype == "thinking":
                        thinking = block.get("thinking", "").strip()
                        if thinking:
                            entries.append({"type": "thought", "text": thinking, "timestamp": ts})
                    elif btype == "tool_use":
                        entries.append({
                            "type": "action",
                            "tool": block.get("name", "unknown"),
                            "code": _safe_json(block.get("input", {})),
                            "tool_call_id": block.get("id", ""),
                            "status": "success",
                            "timestamp": ts,
                        })
            elif isinstance(content, str) and content.strip():
                entries.append({"type": "answer", "text": content, "timestamp": ts})

    return entries


def _extract_provider(model_id: str) -> str:
    """Infer provider from model ID."""
    low = model_id.lower()
    if "claude" in low or "anthropic" in low:
        return "anthropic"
    if "gpt" in low or "openai" in low:
        return "openai"
    if "gemini" in low or "google" in low:
        return "google"
    return "unknown"


def _load_json(path: Path):
    """Load a JSON file, returning None on error."""
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def _safe_json(val) -> str:
    """Safely serialize a value to JSON string."""
    if isinstance(val, str):
        return val
    try:
        return json.dumps(val, ensure_ascii=False)
    except (TypeError, ValueError):
        return str(val)


def _ms_to_iso(ms: int) -> str:
    """Convert millisecond timestamp to ISO 8601."""
    try:
        return datetime.utcfromtimestamp(ms / 1000).isoformat() + "Z"
    except (ValueError, OSError, OverflowError):
        return ""


def read(tasks_dir: str, task_id: str) -> Dict:
    """Convenience function to read a Cline session."""
    return read_session(tasks_dir, task_id)


# ---------------------------------------------------------------------------
# Class-based API
# ---------------------------------------------------------------------------

class ClineReader:
    """Reads Cline VS Code extension sessions into AgentSON format."""

    def __init__(self, tasks_dir: str | Path):
        self.tasks_dir = Path(tasks_dir)

    def read(self, task_id: str) -> Dict:
        return read_session(str(self.tasks_dir), task_id)

    def list_sessions(self, limit: int = 50) -> List[Dict]:
        return list_sessions(str(self.tasks_dir), limit)
