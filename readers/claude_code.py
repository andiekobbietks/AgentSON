"""
Claude Code session reader.

Reads JSONL transcript files from ~/.claude/projects/<hash>/*.jsonl
and converts them to AgentSON format.

Storage layout:
    ~/.claude/
    ├── projects/
    │   └── <hash>/
    │       ├── sessions-index.json    # Session metadata
    │       ├── <session-id>.jsonl     # Main transcripts
    │       └── agent-*.jsonl          # Subagent transcripts
    ├── history.jsonl                  # Global prompt index
    └── file-history/                  # File snapshots (pre-edit)

JSONL entry format (internal, changes between versions):
    {"type": "user", "timestamp": "...", "message": {"role": "user", "content": [...]}, "sessionId": "..."}
    {"type": "assistant", "timestamp": "...", "message": {"role": "assistant", "model": "...", "content": [...]}, "sessionId": "..."}
    {"type": "summary", ...}

Content blocks in message.content:
    {"type": "text", "text": "..."}
    {"type": "tool_use", "id": "...", "name": "...", "input": {...}}
    {"type": "tool_result", "tool_use_id": "...", "content": "..."}

Reference: https://code.claude.com/docs/en/sessions.md
"""

import json
import os
import glob
from pathlib import Path
from datetime import datetime
from typing import Optional


class ClaudeCodeReader:
    """Reads Claude Code JSONL session files and converts to AgentSON format."""

    TOOL_NAME = "claude-code"

    # Tool names in Claude Code content blocks
    TOOL_MAP = {
        "Read": "file_read",
        "Write": "file_write",
        "Edit": "file_edit",
        "Bash": "bash",
        "Glob": "glob_search",
        "Grep": "content_search",
        "WebFetch": "web_fetch",
        "TodoWrite": "todo_write",
        "Task": "subagent",
    }

    def __init__(self, config_dir: Optional[str] = None):
        if config_dir:
            self.claude_dir = Path(config_dir)
        else:
            self.claude_dir = Path.home() / ".claude"

    def list_sessions(self) -> list[dict]:
        """List all sessions across all projects."""
        sessions = []
        projects_dir = self.claude_dir / "projects"
        if not projects_dir.exists():
            return sessions

        for project_dir in projects_dir.iterdir():
            if not project_dir.is_dir():
                continue

            index_file = project_dir / "sessions-index.json"
            if index_file.exists():
                try:
                    with open(index_file, "r", encoding="utf-8") as f:
                        index = json.load(f)
                    for entry in index.get("entries", []):
                        entry["project_path"] = str(project_dir)
                        entry["project_hash"] = project_dir.name
                        sessions.append(entry)
                except (json.JSONDecodeError, OSError):
                    continue

            # Fallback: scan JSONL files directly
            if not index_file.exists():
                for jsonl_file in project_dir.glob("*.jsonl"):
                    if jsonl_file.name.startswith("agent-"):
                        continue
                    session_id = jsonl_file.stem
                    sessions.append({
                        "sessionId": session_id,
                        "fullPath": str(jsonl_file),
                        "project_path": str(project_dir),
                        "project_hash": project_dir.name,
                        "messageCount": self._count_lines(jsonl_file),
                    })

        sessions.sort(key=lambda s: s.get("modified", s.get("created", "")), reverse=True)
        return sessions

    def read_session(self, session_id: str) -> Optional[dict]:
        """Read a single session by ID and convert to AgentSON format."""
        projects_dir = self.claude_dir / "projects"
        if not projects_dir.exists():
            return None

        # Find the JSONL file
        jsonl_path = None
        for project_dir in projects_dir.iterdir():
            if not project_dir.is_dir():
                continue
            candidate = project_dir / f"{session_id}.jsonl"
            if candidate.exists():
                jsonl_path = candidate
                break
            # Also check subdirectories
            for sub in project_dir.rglob(f"{session_id}.jsonl"):
                jsonl_path = sub
                break
            if jsonl_path:
                break

        if not jsonl_path:
            return None

        # Read the JSONL entries
        entries = []
        metadata = {
            "session_id": session_id,
            "project_hash": jsonl_path.parent.name,
            "file_path": str(jsonl_path),
        }

        with open(jsonl_path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    entries.append(obj)
                    # Extract metadata from first user message
                    if obj.get("type") == "user" and "timestamp" not in metadata:
                        metadata["timestamp"] = obj.get("timestamp", "")
                    if obj.get("type") == "assistant" and "model" not in metadata:
                        msg = obj.get("message", {})
                        metadata["model"] = msg.get("model", "unknown")
                except json.JSONDecodeError:
                    continue

        return self._to_agentson(entries, metadata)

    def export_session(self, session_id: str, output_dir: str) -> Optional[str]:
        """Export a session to .AgentSON file."""
        session = self.read_session(session_id)
        if not session:
            return None

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        out_file = output_path / f"claude-code-{session_id}.AgentSON"

        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(session, f, indent=2, ensure_ascii=False)

        return str(out_file)

    def export_all(self, output_dir: str) -> list[str]:
        """Export all sessions to .AgentSON files."""
        exported = []
        for session_info in self.list_sessions():
            session_id = session_info.get("sessionId", "")
            if session_id:
                result = self.export_session(session_id, output_dir)
                if result:
                    exported.append(result)
        return exported

    def _to_agentson(self, entries: list[dict], metadata: dict) -> dict:
        """Convert Claude Code JSONL entries to AgentSON format."""
        agentson_entries = []
        task = ""
        outcome = "partial"

        for entry in entries:
            entry_type = entry.get("type", "")
            timestamp = entry.get("timestamp", "")

            if entry_type == "user":
                # Extract user message text
                msg = entry.get("message", {})
                content = msg.get("content", [])
                text = self._extract_text(content)
                if text:
                    if not task:
                        task = text[:200]
                    agentson_entries.append({
                        "type": "user-query",
                        "text": text,
                        "timestamp": timestamp,
                    })

            elif entry_type == "assistant":
                msg = entry.get("message", {})
                content = msg.get("content", [])
                model = msg.get("model", "")

                for block in content:
                    block_type = block.get("type", "")

                    if block_type == "text":
                        text = block.get("text", "")
                        if text:
                            agentson_entries.append({
                                "type": "thought",
                                "text": text,
                                "timestamp": timestamp,
                                "model": model,
                            })

                    elif block_type == "tool_use":
                        tool_name = block.get("name", "")
                        tool_input = block.get("input", {})
                        tool_id = block.get("id", "")
                        mapped_tool = self.TOOL_MAP.get(tool_name, tool_name.lower())

                        action = {
                            "type": "action",
                            "tool": mapped_tool,
                            "tool_call_id": tool_id,
                            "timestamp": timestamp,
                        }

                        # Map tool-specific inputs
                        if tool_name == "Bash":
                            action["code"] = tool_input.get("command", "")
                        elif tool_name in ("Read", "Write", "Edit"):
                            action["path"] = tool_input.get("file_path", "")
                            if tool_name == "Write":
                                action["code"] = tool_input.get("content", "")
                            elif tool_name == "Edit":
                                action["code"] = f"old: {tool_input.get('old_string', '')}\nnew: {tool_input.get('new_string', '')}"
                        elif tool_name == "Glob":
                            action["code"] = f"pattern: {tool_input.get('pattern', '')}"
                        elif tool_name == "Grep":
                            action["code"] = f"pattern: {tool_input.get('pattern', '')}"
                        elif tool_name == "WebFetch":
                            action["code"] = f"url: {tool_input.get('url', '')}"
                        elif tool_name == "Task":
                            action["code"] = tool_input.get("prompt", "")[:500]
                            action["tool"] = "subagent"
                        else:
                            action["code"] = json.dumps(tool_input)[:500]

                        agentson_entries.append(action)

            elif entry_type == "summary":
                text = entry.get("summary", entry.get("text", ""))
                if text:
                    agentson_entries.append({
                        "type": "answer",
                        "text": text,
                        "timestamp": timestamp,
                    })
                    outcome = "success"

            elif entry_type == "tool_result":
                tool_id = entry.get("tool_use_id", "")
                content = entry.get("content", "")
                if isinstance(content, list):
                    content = self._extract_text(content)

                # Find the matching action and add observation
                for existing in reversed(agentson_entries):
                    if existing.get("type") == "action" and existing.get("tool_call_id") == tool_id:
                        agentson_entries.append({
                            "type": "observation",
                            "text": str(content)[:2000] if content else "",
                            "correlation_id": tool_id,
                            "source": "tool",
                            "timestamp": timestamp,
                        })
                        break

        # Build the AgentSON document
        session_id = metadata.get("session_id", "unknown")
        model = metadata.get("model", "unknown")

        return {
            "$schema": "https://agentson.dev/schema/v1.1.json",
            "id": f"claude-code-{session_id}",
            "task": task,
            "outcome": outcome,
            "tool": {
                "name": self.TOOL_NAME,
                "session_id": session_id,
                "project_hash": metadata.get("project_hash", ""),
            },
            "agent": {
                "name": model,
                "provider": "anthropic",
            },
            "timestamp": metadata.get("timestamp", datetime.utcnow().isoformat() + "Z"),
            "entries": agentson_entries,
        }

    def _extract_text(self, content) -> str:
        """Extract text from content blocks (list of dicts or plain string)."""
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = []
            for block in content:
                if isinstance(block, dict):
                    if block.get("type") == "text":
                        parts.append(block.get("text", ""))
                    elif block.get("type") == "tool_result":
                        result_content = block.get("content", "")
                        if isinstance(result_content, str):
                            parts.append(result_content)
                        elif isinstance(result_content, list):
                            parts.append(self._extract_text(result_content))
                elif isinstance(block, str):
                    parts.append(block)
            return "\n".join(parts)
        return str(content)

    def _count_lines(self, path: Path) -> int:
        """Count non-empty lines in a file."""
        count = 0
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        count += 1
        except OSError:
            pass
        return count
