"""
AgentSON Reader: cursor
=======================

Reads session data from Cursor IDE's SQLite databases.

Cursor stores sessions in two locations:
- Desktop App: `state.vscdb` (SQLite key-value store)
- Agent CLI: `store.db` (content-addressed blobs)

Desktop App storage (primary):
  - macOS: ~/Library/Application Support/Cursor/User/
  - Windows: %APPDATA%\\Cursor\\User\\
  - Linux: ~/.config/Cursor/User/

  Key files:
    globalStorage/state.vscdb         — ALL conversations (key-value)
    workspaceStorage/<hash>/state.vscdb — per-workspace UI state

Agent CLI storage:
  - ~/.cursor/chats/<session-id>/store.db

Key patterns in state.vscdb (cursorDiskKV table):
  composerData:<composerId>     — session header/metadata
  bubbleId:<composerId>:<bubbleId> — individual messages
  checkpointId:<composerId>:<checkpointId> — workspace snapshots

Message types (bubble.type):
  1 = user message
  2 = assistant message
"""
from __future__ import annotations

import json
import re
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


SCHEMA_URI = "https://agentson.dev/schema/v1.1.json"


def _get_global_storage_path() -> Optional[Path]:
    """Return the default Cursor globalStorage path for the current OS."""
    home = Path.home()
    candidates = [
        home / "Library" / "Application Support" / "Cursor" / "User" / "globalStorage",
        home / ".config" / "Cursor" / "User" / "globalStorage",
    ]
    import os
    appdata = os.environ.get("APPDATA")
    if appdata:
        candidates.insert(0, Path(appdata) / "Cursor" / "User" / "globalStorage")
    for p in candidates:
        if p.exists():
            return p
    return None


def _open_db(db_path: Path) -> sqlite3.Connection:
    """Open a Cursor SQLite DB in read-only WAL-safe mode."""
    uri = f"file:{db_path}?mode=ro&immutable=1"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _load_json_value(raw: Optional[str]) -> Optional[Dict]:
    """Try to parse a JSON value from the DB."""
    if not raw:
        return None
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None


def list_sessions(db_path: str, limit: int = 50) -> List[Dict]:
    """List all Cursor sessions from a globalStorage state.vscdb."""
    db = Path(db_path)
    if not db.exists():
        raise FileNotFoundError(f"Database not found: {db}")

    conn = _open_db(db)
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT key, value FROM cursorDiskKV WHERE key LIKE 'composerData:%' "
            "ORDER BY rowid DESC LIMIT ?",
            (limit,),
        )
        sessions = []
        for row in cursor.fetchall():
            data = _load_json_value(row["value"])
            if not data:
                continue
            sessions.append({
                "id": data.get("composerId", row["key"].split(":", 1)[-1]),
                "title": data.get("name", ""),
                "created": data.get("createdAt"),
                "updated": data.get("lastUpdatedAt"),
                "mode": data.get("unifiedMode", ""),
                "status": data.get("status", ""),
            })
        return sessions
    finally:
        conn.close()


def read_session(db_path: str, composer_id: str) -> Dict:
    """Read a Cursor session by composerId and convert to AgentSON format."""
    db = Path(db_path)
    if not db.exists():
        raise FileNotFoundError(f"Database not found: {db}")

    conn = _open_db(db)
    try:
        cursor = conn.cursor()

        # 1. Get session header
        cursor.execute(
            "SELECT value FROM cursorDiskKV WHERE key = ?",
            (f"composerData:{composer_id}",),
        )
        row = cursor.fetchone()
        if not row:
            raise ValueError(f"Session {composer_id} not found")
        header = _load_json_value(row["value"])
        if not header:
            raise ValueError(f"Corrupt session header for {composer_id}")

        # 2. Get all message bubbles
        cursor.execute(
            "SELECT key, value FROM cursorDiskKV WHERE key LIKE ?",
            (f"bubbleId:{composer_id}:%",),
        )
        bubbles = []
        for brow in cursor.fetchall():
            bdata = _load_json_value(brow["value"])
            if bdata:
                bubbles.append(bdata)

        # Sort by type (user=1 first), then by createdAt
        bubbles.sort(key=lambda b: (b.get("type", 9), b.get("createdAt", 0)))

        # 3. Convert to AgentSON entries
        entries = _bubbles_to_entries(bubbles, header)

        # 4. Build document
        model_name = _extract_model_name(bubbles)
        usage = header.get("usageData", {}).get("default", {})

        doc = {
            "$schema": SCHEMA_URI,
            "id": composer_id,
            "title": header.get("name", composer_id[:20]),
            "tool": {
                "name": "cursor",
                "version": "3.0+",
                "session_id": composer_id,
            },
            "agent": {
                "name": model_name,
                "provider": "cursor",
                "variant": header.get("unifiedMode", "agent"),
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

        if header.get("createdAt"):
            doc["started_at"] = _ms_to_iso(header["createdAt"])
        if header.get("lastUpdatedAt"):
            doc["ended_at"] = _ms_to_iso(header["lastUpdatedAt"])

        doc["metadata"] = {
            "exported_at": datetime.utcnow().isoformat() + "Z",
            "source": "cursor-desktop",
            "mode": header.get("unifiedMode", ""),
            "status": header.get("status", ""),
            "total_tokens_in": usage.get("costInCents", 0),
            "messages": len(bubbles),
        }

        return doc
    finally:
        conn.close()


def _bubbles_to_entries(bubbles: List[Dict], header: Dict) -> List[Dict]:
    """Convert Cursor bubbles to AgentSON entries."""
    entries: List[Dict] = []
    conversation_order = header.get("fullConversationHeadersOnly", [])

    # Use conversation order if available, otherwise fall back to bubbles list
    if conversation_order:
        bubble_map = {b.get("bubbleId"): b for b in bubbles}
        ordered = []
        for ref in conversation_order:
            bid = ref.get("bubbleId")
            if bid and bid in bubble_map:
                ordered.append(bubble_map[bid])
        bubbles = ordered if ordered else bubbles

    for bubble in bubbles:
        btype = bubble.get("type")
        text = (bubble.get("text") or "").strip()

        if btype == 1:  # User message
            if text:
                entry: Dict = {"type": "user-query", "text": text}
                if bubble.get("createdAt"):
                    entry["timestamp"] = bubble["createdAt"]
                entries.append(entry)

        elif btype == 2:  # Assistant message
            # Thinking / reasoning
            thinking = bubble.get("thinking")
            if isinstance(thinking, dict):
                think_text = thinking.get("text", "")
            elif isinstance(thinking, str):
                think_text = thinking
            else:
                think_text = ""

            if think_text:
                entries.append({
                    "type": "thought",
                    "text": think_text,
                    "timestamp": bubble.get("createdAt"),
                })

            # Tool results (file edits, terminal commands, etc.)
            tool_results = bubble.get("toolResults", [])
            for tr in tool_results:
                if isinstance(tr, dict):
                    entries.append({
                        "type": "action",
                        "tool": tr.get("toolName", tr.get("name", "unknown")),
                        "code": _safe_json(tr.get("params", tr.get("input", ""))),
                        "output": str(tr.get("result", tr.get("output", "")))[:2000],
                        "status": tr.get("status", "success"),
                        "timestamp": bubble.get("createdAt"),
                        "tool_call_id": f"tc_{bubble.get('bubbleId', '')[:8]}",
                    })

            # Tool-former data (older format)
            tool_former = bubble.get("toolFormerData")
            if isinstance(tool_former, dict) and tool_former.get("name"):
                entries.append({
                    "type": "action",
                    "tool": tool_former.get("name", "unknown"),
                    "code": _safe_json(tool_former.get("params", "")),
                    "output": str(tool_former.get("result", ""))[:2000],
                    "status": tool_former.get("status", "success"),
                    "timestamp": bubble.get("createdAt"),
                    "tool_call_id": f"tc_{bubble.get('bubbleId', '')[:8]}",
                })

            # Answer text
            if text:
                entries.append({
                    "type": "answer",
                    "text": text,
                    "timestamp": bubble.get("createdAt"),
                })

    return entries


def _extract_model_name(bubbles: List[Dict]) -> str:
    """Extract the model name from the most recent assistant bubble."""
    for b in reversed(bubbles):
        if b.get("type") == 2:
            model_info = b.get("modelInfo", {})
            if isinstance(model_info, dict) and model_info.get("modelName"):
                return model_info["modelName"]
    return "unknown"


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


def read(db_path: str, composer_id: str) -> Dict:
    """Convenience function to read a Cursor session."""
    return read_session(db_path, composer_id)


# ---------------------------------------------------------------------------
# Class-based API
# ---------------------------------------------------------------------------

class CursorReader:
    """Reads Cursor IDE sessions into AgentSON format."""

    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)

    def read(self, composer_id: str) -> Dict:
        return read_session(str(self.db_path), composer_id)

    def list_sessions(self, limit: int = 50) -> List[Dict]:
        return list_sessions(str(self.db_path), limit)
