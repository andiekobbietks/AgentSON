# AgentSON core runtime: crawler
"""Crawl every detected tool and read its sessions into text.

Three reader shapes exist, and each is handled once:

* ``opencode`` / ``minimax`` / ``vibeedge`` -- identical module-level
  contract: ``list_sessions(db, limit)`` and ``read(db, sid)``. One branch
  covers all three. The module-level VibeEdge pair is preferred over the
  class form because it disconnects in a ``finally``, so a crawler that
  loops over many sessions cannot leak a connection.
* ``antigravity`` -- its read takes the **session dict**, not an id.
* ``claude-code`` / ``copilot-chat`` -- reader classes with
  ``read_session(sid)``.

Failures are recorded per tool in ``ToolSummary.error`` and surfaced in
the report. They are never swallowed: a scan that silently skips a tool
reports a total nobody can trust.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from .digest import ToolSummary
from .tool_registry import get_registry

# The CLI exposes no --limit for scan, so this is the only bound. High
# enough to read a real history, low enough that one corrupt store cannot
# run away with the process.
DEFAULT_LIMIT = 1000

# Prose-carrying entry fields -- the same list redact_agentson() walks, so
# classification and redaction read identical text out of a session.
TEXT_FIELDS = ("text", "code", "output", "query", "content", "title")

# Tools whose reader exposes the shared module-level contract.
_DB_TOOLS = ("opencode", "minimax", "vibeedge")


@dataclass
class SessionDoc:
    """One session, flattened to the text a classifier can run over."""

    tool: str
    session_id: str
    texts: List[str] = field(default_factory=list)
    entry_count: int = 0
    reader_messages: Optional[int] = None

    @property
    def blob(self) -> str:
        return "\n".join(t for t in self.texts if t)


def _session_id_of(summary: dict) -> str:
    """Every key the readers use for a session id."""
    for key in ("session_id", "sessionId", "id", "sid"):
        value = summary.get(key)
        if value:
            return str(value)
    return ""


def _as_int(value) -> Optional[int]:
    """Reader-reported counts are only trusted when they parse as an int."""
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def extract_text(doc: dict) -> Tuple[List[str], int]:
    """Pull prose out of an agentson-shaped session.

    Returns ``(texts, message_count)``. Args values are included because
    a tool call's arguments routinely carry paths, keys and URLs, which
    are exactly what the rules are looking for.
    """
    entries = doc.get("entries") or []
    texts: List[str] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        for name in TEXT_FIELDS:
            value = entry.get(name)
            if isinstance(value, str) and value:
                texts.append(value)
        args = entry.get("args")
        if isinstance(args, dict):
            for value in args.values():
                if isinstance(value, str) and value:
                    texts.append(value)
    return texts, len(entries)


def _crawl_shared(tool: str, path, limit: int) -> List[SessionDoc]:
    """opencode, minimax, vibeedge -- one branch for all three."""
    import importlib

    module = importlib.import_module("readers.%s" % tool)
    docs: List[SessionDoc] = []
    for summary in module.list_sessions(str(path), limit) or []:
        sid = _session_id_of(summary)
        if not sid:
            continue
        texts, entry_count = extract_text(module.read(str(path), sid))
        docs.append(
            SessionDoc(
                tool=tool,
                session_id=sid,
                texts=texts,
                entry_count=entry_count,
                reader_messages=_as_int(summary.get("messages")),
            )
        )
    return docs


def _crawl_antigravity(path) -> List[SessionDoc]:
    from readers.antigravity import (
        get_antigravity_sessions,
        read_antigravity_session,
    )

    docs: List[SessionDoc] = []
    for summary in get_antigravity_sessions(str(path)) or []:
        doc = read_antigravity_session(summary)  # takes the dict, not an id
        texts, entry_count = extract_text(doc or {})
        docs.append(
            SessionDoc(
                tool="antigravity",
                session_id=_session_id_of(doc or summary),
                texts=texts,
                entry_count=entry_count,
                reader_messages=_as_int(summary.get("messages")),
            )
        )
    return docs


def _crawl_claude_code(limit: int) -> List[SessionDoc]:
    from readers.claude_code import ClaudeCodeReader

    reader = ClaudeCodeReader()
    docs: List[SessionDoc] = []
    for summary in reader.list_sessions()[:limit]:
        sid = _session_id_of(summary)
        if not sid:
            continue
        doc = reader.read_session(sid) or {}
        texts, entry_count = extract_text(doc)
        docs.append(
            SessionDoc(
                tool="claude-code",
                session_id=sid,
                texts=texts,
                entry_count=entry_count,
                reader_messages=_as_int(summary.get("messages")),
            )
        )
    return docs


def _crawl_copilot_chat(limit: int) -> List[SessionDoc]:
    from readers.copilot_chat import CopilotChatReader

    reader = CopilotChatReader()
    docs: List[SessionDoc] = []
    for summary in reader.list_sessions(limit):
        sid = _session_id_of(summary)
        if not sid:
            continue
        doc = reader.read_session(sid) or {}
        texts, entry_count = extract_text(doc)
        docs.append(
            SessionDoc(
                tool="copilot-chat",
                session_id=sid,
                texts=texts,
                entry_count=entry_count,
                reader_messages=_as_int(summary.get("messages")),
            )
        )
    return docs


_HANDLERS = {
    "antigravity": lambda path, limit: _crawl_antigravity(path),
    "claude-code": lambda path, limit: _crawl_claude_code(limit),
    "copilot-chat": lambda path, limit: _crawl_copilot_chat(limit),
}


def crawl(
    tool_filter: Optional[List[str]] = None,
    limit: int = DEFAULT_LIMIT,
) -> Tuple[List[SessionDoc], List[ToolSummary], Dict[str, str]]:
    """Crawl every present tool.

    Returns ``(docs, summaries, skipped)``. ``skipped`` maps each tool not
    crawled to why -- absent from this machine, or needing an explicit
    path the CLI did not supply.
    """
    registry = get_registry(tool_filter)
    docs: List[SessionDoc] = []
    summaries: List[ToolSummary] = []
    skipped: Dict[str, str] = {}

    for tool, info in registry.items():
        if not info.present:
            # A tool with no default path is "not supplied", not "absent" --
            # the registry's note says which. Printing "no data at None"
            # would read as a bug rather than a missing --input.
            skipped[tool] = (
                info.note if info.path is None else "no data at %s" % info.path
            )
            continue
        if tool in ("chrome-devtools", "libre"):
            skipped[tool] = info.note
            continue

        summary = ToolSummary(tool=tool)
        try:
            if tool in _DB_TOOLS:
                tool_docs = _crawl_shared(tool, info.path, limit)
            else:
                tool_docs = _HANDLERS[tool](info.path, limit)
        except Exception as exc:  # recorded, reported, never hidden
            summary.error = "%s: %s" % (type(exc).__name__, exc)
            summaries.append(summary)
            continue

        docs.extend(tool_docs)
        summary.sessions = len(tool_docs)
        summary.entries = sum(d.entry_count for d in tool_docs)
        summary.messages = sum(
            d.reader_messages for d in tool_docs if d.reader_messages is not None
        )
        summaries.append(summary)

    return docs, summaries, skipped
