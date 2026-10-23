"""
AgentSON Reader: aider
======================

Reads session data from Aider's chat history Markdown file.

Aider stores its chat history as a Markdown file at:
  <git_root>/.aider.chat.history.md

Format:
  # Chat History

  ## [Timestamp]

  ### User
  [User message content]

  ### Assistant
  [Assistant response with code blocks, diffs, etc.]

The Markdown file is an append-only log. Each session is delimited by
a `## [ISO timestamp]` heading. Within each session, `### User` and
### Assistant` headings separate messages.

Code blocks in assistant messages represent file edits (diffs) or
terminal commands. Aider uses a special format for code edits:
  <<<<<<< SEARCH
  [original code]
  =======
  [new code]
  >>>>>>> REPLACE

When --restore-chat-history is used, the Markdown is parsed back into
the conversation context. Otherwise it serves as a human-readable log.
"""
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


SCHEMA_URI = "https://agentson.dev/schema/v1.1.json"

# Regex patterns
SESSION_RE = re.compile(r"^## \[(.+?)\]\s*$", re.MULTILINE)
ROLE_RE = re.compile(r"^### (User|Assistant)\s*$", re.MULTILINE)
DIFF_RE = re.compile(r"<<<<<<< SEARCH\n(.*?)=======\n(.*?)>>>>>>> REPLACE", re.DOTALL)


def _parse_timestamp(ts_str: str) -> Optional[datetime]:
    """Parse various timestamp formats from Aider chat history."""
    ts_str = ts_str.strip()
    # Try ISO format
    try:
        return datetime.fromisoformat(ts_str)
    except ValueError:
        pass
    # Try common formats
    for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S"]:
        try:
            return datetime.strptime(ts_str, fmt)
        except ValueError:
            continue
    return None


def _split_sessions(md: str) -> List[Tuple[str, str]]:
    """Split Markdown chat history into (timestamp_str, session_body) tuples."""
    sessions: List[Tuple[str, str]] = []
    matches = list(SESSION_RE.finditer(md))

    for i, m in enumerate(matches):
        ts_str = m.group(1)
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(md)
        body = md[start:end].strip()
        if body:
            sessions.append((ts_str, body))

    return sessions


def _parse_session_body(body: str) -> List[Dict]:
    """Parse a session body into AgentSON entries."""
    entries: List[Dict] = []
    sections = ROLE_RE.split(body)

    # sections[0] is content before first ### (usually empty)
    # sections[1] is "User" or "Assistant"
    # sections[2] is the content
    # etc.
    i = 1
    while i < len(sections) - 1:
        role = sections[i].strip()
        content = sections[i + 1].strip()
        i += 2

        if not content:
            continue

        if role == "User":
            # Check for file context additions
            if content.startswith("/add ") or content.startswith("/drop "):
                entries.append({
                    "type": "side-effect",
                    "action": "file_context",
                    "text": content,
                })
            else:
                entries.append({"type": "user-query", "text": content})

        elif role == "Assistant":
            # Split into thinking, code blocks, and text
            _parse_assistant_message(content, entries)

    return entries


def _parse_assistant_message(content: str, entries: List[Dict]) -> None:
    """Parse an assistant message into thought/action/answer entries."""
    # Check for SEARCH/REPLACE diffs (file edits)
    diffs = list(DIFF_RE.finditer(content))
    if diffs:
        for d in diffs:
            entries.append({
                "type": "action",
                "tool": "file.edit",
                "code": f"<<<<<<< SEARCH\n{d.group(1)}=======\n{d.group(2)}>>>>>>> REPLACE",
                "status": "success",
            })
        # Get text outside diffs
        remaining = DIFF_RE.sub("", content).strip()
        if remaining:
            _parse_text_or_code(remaining, entries)
        return

    _parse_text_or_code(content, entries)


def _parse_text_or_code(text: str, entries: List[Dict]) -> None:
    """Parse text that may contain code blocks into entries."""
    # Split by code fences
    parts = re.split(r"```[\s\S]*?```", text)

    # Check if there are code blocks
    has_code = "```" in text

    if has_code:
        # Extract code blocks
        code_blocks = re.findall(r"```(?:\w+)?\n([\s\S]*?)```", text)
        for code in code_blocks:
            code = code.strip()
            if not code:
                continue
            # Infer tool from code content
            tool = _infer_tool(code)
            entries.append({
                "type": "action",
                "tool": tool,
                "code": code,
                "status": "success",
            })

        # Get text outside code blocks
        text_outside = re.sub(r"```(?:\w+)?\n[\s\S]*?```", "", text).strip()
        if text_outside:
            entries.append({"type": "answer", "text": text_outside})
    else:
        # Pure text — could be thinking or answer
        if text.startswith("Ok,") or text.startswith("OK,") or text.startswith("Sure"):
            entries.append({"type": "answer", "text": text})
        elif len(text) < 200 and not text.endswith("."):
            # Short text that looks like acknowledgment
            entries.append({"type": "answer", "text": text})
        else:
            entries.append({"type": "answer", "text": text})


def _infer_tool(code: str) -> str:
    """Infer the tool from code content."""
    low = code.lower()
    if "git" in low:
        return "bash"
    if "import" in low or "def " in low or "class " in low:
        return "code_edit"
    if any(cmd in low for cmd in ["npm", "pip", "yarn", "cargo", "go "]):
        return "bash"
    return "code_edit"


def list_sessions(repo_dir: str, limit: int = 50) -> List[Dict]:
    """List Aider sessions from the chat history file."""
    aider_file = Path(repo_dir) / ".aider.chat.history.md"
    if not aider_file.exists():
        raise FileNotFoundError(f"Aider chat history not found: {aider_file}")

    text = aider_file.read_text(encoding="utf-8")
    raw_sessions = _split_sessions(text)

    sessions = []
    for ts_str, body in raw_sessions[:limit]:
        dt = _parse_timestamp(ts_str)
        entries = _parse_session_body(body)
        user_queries = [e for e in entries if e["type"] == "user-query"]
        first_query = user_queries[0]["text"] if user_queries else ""

        sessions.append({
            "id": f"aider-{dt.strftime('%Y%m%d%H%M%S')}" if dt else f"aider-{ts_str}",
            "title": first_query[:100] if first_query else "Aider session",
            "created": dt.isoformat() + "Z" if dt else "",
            "entries_count": len(entries),
        })

    return sessions


def read_session(repo_dir: str, session_id: Optional[str] = None) -> Dict:
    """Read an Aider session and convert to AgentSON format."""
    aider_file = Path(repo_dir) / ".aider.chat.history.md"
    if not aider_file.exists():
        raise FileNotFoundError(f"Aider chat history not found: {aider_file}")

    text = aider_file.read_text(encoding="utf-8")
    raw_sessions = _split_sessions(text)

    if not raw_sessions:
        raise ValueError("No sessions found in Aider chat history")

    # Find specific session or use the last one
    if session_id:
        for ts_str, body in raw_sessions:
            dt = _parse_timestamp(ts_str)
            sid = f"aider-{dt.strftime('%Y%m%d%H%M%S')}" if dt else ""
            if sid == session_id:
                break
        else:
            raise ValueError(f"Session {session_id} not found")
    else:
        ts_str, body = raw_sessions[-1]

    dt = _parse_timestamp(ts_str)
    entries = _parse_session_body(body)

    # Build document
    first_user = next((e for e in entries if e["type"] == "user-query"), None)
    title = first_user["text"][:100] if first_user else "Aider session"

    doc = {
        "$schema": SCHEMA_URI,
        "id": f"aider-{dt.strftime('%Y%m%d%H%M%S')}" if dt else f"aider-{ts_str}",
        "title": title,
        "tool": {
            "name": "aider",
            "version": "latest",
            "session_id": f"aider-{dt.strftime('%Y%m%d%H%M%S')}" if dt else ts_str,
        },
        "agent": {
            "name": "aider",
            "provider": "paul-gauthier",
            "variant": "act",
        },
        "entries": entries,
    }

    # v1.1 trajectory fields
    if first_user:
        doc["task"] = first_user["text"][:200]

    answers = sum(1 for e in entries if e["type"] == "answer")
    actions = sum(1 for e in entries if e["type"] == "action")
    if answers == 0 and actions == 0:
        doc["outcome"] = "aborted"
    elif entries and entries[-1]["type"] == "answer":
        doc["outcome"] = "success"
    else:
        doc["outcome"] = "partial"

    if dt:
        doc["started_at"] = dt.isoformat() + "Z"

    doc["metadata"] = {
        "exported_at": datetime.utcnow().isoformat() + "Z",
        "source": "aider",
        "entries_count": len(entries),
    }

    return doc


def read(repo_dir: str, session_id: Optional[str] = None) -> Dict:
    """Convenience function to read an Aider session."""
    return read_session(repo_dir, session_id)


# ---------------------------------------------------------------------------
# Class-based API
# ---------------------------------------------------------------------------

class AiderReader:
    """Reads Aider chat history into AgentSON format."""

    def __init__(self, repo_dir: str | Path):
        self.repo_dir = Path(repo_dir)

    def read(self, session_id: Optional[str] = None) -> Dict:
        return read_session(str(self.repo_dir), session_id)

    def list_sessions(self, limit: int = 50) -> List[Dict]:
        return list_sessions(str(self.repo_dir), limit)
