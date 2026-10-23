# AgentSON core runtime: gemini
"""AgentSON Reader: gemini (Google AI Studio / Gemini export JSON)."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, List, Optional, Any


class GeminiReader:
    """Reads Gemini/AI Studio conversation exports (Google-Search_*.json)."""

    def __init__(self, path: str):
        self.path = Path(path)

    def list_sessions(self, limit: int = 50) -> List[Dict]:
        if not self.path.exists():
            return []
        with open(self.path, encoding="utf-8") as f:
            data = json.load(f)
        groups = {}
        for msg in (data if isinstance(data, list) else [])[:limit*10]:
            gid = msg.get("chatGroupId") or msg.get("id", "unknown")
            role = msg.get("role", "unknown")
            model = msg.get("displayModel") or msg.get("model", "gemini")
            groups.setdefault(gid, {"id": gid, "model": model, "messages": 0})
            groups[gid]["messages"] += 1
        return [{"id": g["id"], "model": g["model"], "messages": g["messages"]} for g in list(groups.values())[:limit]]

    def read_session(self, session_id: str) -> Optional[Dict]:
        with open(self.path, encoding="utf-8") as f:
            data = json.load(f)
        entries = []
        for msg in (data if isinstance(data, list) else []):
            gid = msg.get("chatGroupId") or msg.get("id", "")
            if gid == session_id or (not session_id and msg.get("role")):
                contents = msg.get("contents", [])
                text = " ".join(c.get("content", "") for c in contents if isinstance(c, dict))
                entries.append({
                    "tool": "gemini",
                    "session_id": gid,
                    "category": "user-message" if msg.get("role") == "user" else "model-response",
                    "evidence": text[:200],
                    "severity": "info",
                    "start": 0,
                    "end": len(text),
                    "rule": "gemini-session",
                })
        return {"session_id": session_id or "gemini-export", "tool": "gemini", "entries": entries, "source": str(self.path)}


def read(path: str, session_id: Optional[str] = None) -> Dict:
    return GeminiReader(path).read_session(session_id or "gemini-export") or {}


def list_sessions(path: str, limit: int = 50) -> List[Dict]:
    return GeminiReader(path).list_sessions(limit)
