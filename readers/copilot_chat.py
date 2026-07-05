"""
GitHub Copilot Chat session reader.

Reads multi-turn chat conversations and converts to AgentSON format.
Captures user queries, assistant responses, code suggestions, and outcomes.

Storage layout:
    ~/.copilot/
    ├── history.jsonl         # Chat history across all sessions
    ├── sessions/
    │   └── <session-id>.json # Individual session metadata
    └── cache/
        └── <session-hash>/   # Cache for embeddings, etc.

Entry format (internal):
    {"type": "user", "content": "...", "timestamp": "...", "sessionId": "..."}
    {"type": "assistant", "content": "...", "model": "...", "timestamp": "..."}
    {"type": "code", "language": "...", "snippet": "..."}
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Any


class CopilotChatReader:
    """Reads GitHub Copilot chat sessions and converts to AgentSON format."""

    TOOL_NAME = "copilot-chat"

    def __init__(self, config_dir: Optional[str] = None):
        """Initialize reader with optional custom config directory."""
        if config_dir:
            self.copilot_dir = Path(config_dir)
        else:
            self.copilot_dir = Path.home() / ".copilot"

    def list_sessions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """List all chat sessions from history."""
        history_file = self.copilot_dir / "history.jsonl"
        if not history_file.exists():
            return []

        sessions_by_id = {}
        session_order = []

        try:
            with open(history_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                        session_id = entry.get("sessionId", "unknown")

                        if session_id not in sessions_by_id:
                            sessions_by_id[session_id] = {
                                "sessionId": session_id,
                                "messageCount": 0,
                                "firstMessage": entry.get("content", "")[:100],
                                "timestamp": entry.get("timestamp", ""),
                            }
                            session_order.append(session_id)

                        sessions_by_id[session_id]["messageCount"] += 1
                        sessions_by_id[session_id]["timestamp"] = entry.get(
                            "timestamp", sessions_by_id[session_id]["timestamp"]
                        )
                    except json.JSONDecodeError:
                        continue
        except (OSError, IOError):
            pass

        # Return in reverse chronological order
        result = [
            sessions_by_id[sid]
            for sid in reversed(session_order)
            if sid in sessions_by_id
        ]
        return result[:limit]

    def read_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Read a single chat session and convert to AgentSON format."""
        history_file = self.copilot_dir / "history.jsonl"
        if not history_file.exists():
            return None

        entries = []
        metadata = {
            "session_id": session_id,
            "message_count": 0,
        }

        try:
            with open(history_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                        if entry.get("sessionId") == session_id:
                            entries.append(entry)
                            metadata["message_count"] += 1
                            if "first_timestamp" not in metadata:
                                metadata["first_timestamp"] = entry.get(
                                    "timestamp"
                                )
                            metadata["last_timestamp"] = entry.get("timestamp")
                    except json.JSONDecodeError:
                        continue
        except (OSError, IOError):
            return None

        if not entries:
            return None

        return self._to_agentson(entries, metadata)

    def export_session(self, session_id: str, output_dir: str) -> Optional[str]:
        """Export a chat session to .agentson file."""
        session = self.read_session(session_id)
        if not session:
            return None

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        out_file = output_path / f"copilot-chat-{session_id}.agentson"

        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(session, f, indent=2, ensure_ascii=False)

        return str(out_file)

    def _to_agentson(self, entries: List[Dict], metadata: Dict) -> Dict:
        """Convert Copilot chat entries to AgentSON format."""
        agentson_entries = []
        task = ""
        outcome = "partial"

        for entry in entries:
            entry_type = entry.get("type", "")
            timestamp = entry.get("timestamp", "")
            content = entry.get("content", "")

            if entry_type == "user":
                # User query
                if content:
                    if not task:
                        task = content[:200]
                    agentson_entries.append(
                        {
                            "type": "user-query",
                            "text": content,
                            "timestamp": timestamp,
                        }
                    )

            elif entry_type == "assistant":
                # Assistant response (can include code, explanation, etc.)
                if content:
                    agentson_entries.append(
                        {
                            "type": "answer",
                            "text": content,
                            "timestamp": timestamp,
                            "model": entry.get("model", "gpt-4"),
                        }
                    )
                outcome = "success"

            elif entry_type == "code":
                # Code suggestion/action
                language = entry.get("language", "")
                snippet = entry.get("snippet", "")
                file_path = entry.get("filePath", "")

                agentson_entries.append(
                    {
                        "type": "action",
                        "tool": f"code-{language}" if language else "code",
                        "code": snippet,
                        "path": file_path,
                        "timestamp": timestamp,
                        "status": "success",
                    }
                )

            elif entry_type == "thought":
                # Internal reasoning
                if content:
                    agentson_entries.append(
                        {
                            "type": "thought",
                            "text": content,
                            "timestamp": timestamp,
                        }
                    )

            elif entry_type == "observation":
                # Result/feedback from tool/system
                if content:
                    agentson_entries.append(
                        {
                            "type": "observation",
                            "text": content,
                            "source": entry.get("source", "system"),
                            "correlation_id": entry.get("correlation_id", ""),
                            "timestamp": timestamp,
                        }
                    )

        session_id = metadata.get("session_id", "unknown")

        return {
            "$schema": "https://agentson.dev/schema/v1.1.json",
            "id": f"copilot-chat-{session_id}",
            "task": task,
            "outcome": outcome,
            "tool": {
                "name": self.TOOL_NAME,
                "session_id": session_id,
            },
            "agent": {
                "name": "gpt-4",
                "provider": "openai",
                "variant": "copilot",
            },
            "started_at": self._timestamp_to_iso(
                metadata.get("first_timestamp")
            ),
            "ended_at": self._timestamp_to_iso(metadata.get("last_timestamp")),
            "context": {
                "platform": "github-copilot",
            },
            "entries": agentson_entries,
            "metadata": {
                "message_count": metadata.get("message_count", 0),
                "exported_at": datetime.utcnow().isoformat() + "Z",
            },
        }

    @staticmethod
    def _timestamp_to_iso(timestamp: Optional[str]) -> Optional[str]:
        """Convert timestamp to ISO 8601 if needed."""
        if not timestamp:
            return None
        # If already ISO format, return as-is
        if "T" in str(timestamp):
            return timestamp
        # Otherwise try to parse and convert
        try:
            dt = datetime.fromisoformat(str(timestamp).replace("Z", "+00:00"))
            return dt.isoformat() + "Z"
        except (ValueError, AttributeError):
            return timestamp


def read(session_id: str, config_dir: Optional[str] = None) -> Optional[Dict]:
    """Convenience function to read a Copilot chat session."""
    reader = CopilotChatReader(config_dir)
    return reader.read_session(session_id)


def list_sessions(
    config_dir: Optional[str] = None, limit: int = 50
) -> List[Dict]:
    """Convenience function to list Copilot chat sessions."""
    reader = CopilotChatReader(config_dir)
    return reader.list_sessions(limit)
