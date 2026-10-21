"""Tool path registry — where each of the eight tools keeps its sessions.

Path resolution is reused, never restated. Four tools are owned by
``cli.main.get_default_db_paths()``; the reader classes own their own
directories. Copying those literals here would create a second source of
truth that drifts the first time a path changes.

``detect`` is deliberately pure filesystem: it opens no database, touches
no reader, and performs no network I/O. That is what keeps
``agentson platform detect`` safe to run anywhere.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass(frozen=True)
class ToolInfo:
    """One tool: its CLI name, its parser, and where its data lives."""

    tool: str
    """CLI name, exactly as passed to ``agentson list --tool``."""

    reader: str
    """Module or class that parses this tool's sessions."""

    path: Optional[Path]
    """Resolved data location, or None when the tool has no default path.

    None rather than ``Path("")``: an empty Path resolves to ``.``, which
    exists, and would be reported as present when it means "unknown".
    """

    path_kind: str = "directory"
    """One of sqlite | directory | csv | manual."""

    note: str = ""
    """Why a path is absent, or anything a reader needs to know."""

    @property
    def present(self) -> bool:
        return self.path is not None and self.path.exists()

    def as_dict(self) -> dict:
        return {
            "tool": self.tool,
            "reader": self.reader,
            "path": str(self.path) if self.path is not None else None,
            "path_kind": self.path_kind,
            "present": self.present,
            "note": self.note,
        }


def _default_paths() -> Dict[str, Path]:
    """The four database-backed tools, from their single owner.

    Imported lazily so that ``import agentson_platform`` does not pull in
    the CLI's argparse surface.
    """
    from cli.main import get_default_db_paths

    return get_default_db_paths()


def get_registry(tool_filter: Optional[List[str]] = None) -> Dict[str, ToolInfo]:
    """Build the registry for all eight tools, or just ``tool_filter``.

    Reader directories are resolved by constructing the readers, the same
    way ``cmd_list`` reaches them -- not by repeating their paths.
    """
    from readers.claude_code import ClaudeCodeReader
    from readers.copilot_chat import CopilotChatReader
    from readers.vibeedge import _default_root

    db = _default_paths()

    tools = [
        ToolInfo(
            tool="opencode",
            reader="readers.opencode:list_sessions",
            path=db["opencode"],
            path_kind="sqlite",
            note="OpenCode session database",
        ),
        ToolInfo(
            tool="minimax",
            reader="readers.minimax:list_sessions",
            path=db["minimax"],
            path_kind="sqlite",
            note="MiniMax session database",
        ),
        ToolInfo(
            tool="antigravity",
            reader="readers.antigravity:get_antigravity_sessions",
            path=db["antigravity"],
            path_kind="directory",
            note="Antigravity IDE conversation exports",
        ),
        ToolInfo(
            tool="vibeedge",
            reader="readers.vibeedge:VibeedgeReader",
            path=_default_root(),
            path_kind="directory",
            note="VibeEdge wrangler state; chats live in Durable Object SQLite, "
            "not a single file",
        ),
        ToolInfo(
            tool="claude-code",
            reader="readers.claude_code:ClaudeCodeReader",
            path=ClaudeCodeReader().claude_dir,
            path_kind="directory",
            note="Claude Code config directory",
        ),
        ToolInfo(
            tool="copilot-chat",
            reader="readers.copilot_chat:CopilotChatReader",
            path=CopilotChatReader().copilot_dir,
            path_kind="directory",
            note="GitHub Copilot chat directory",
        ),
        ToolInfo(
            tool="chrome-devtools",
            reader="readers.chrome_devtools:list_exports",
            path=None,
            path_kind="manual",
            note="No default location; export requires --input <dir>",
        ),
        ToolInfo(
            tool="libre",
            reader="readers.libre:read_libre_csv",
            path=None,
            path_kind="csv",
            note="Takes an explicit CSV path; not an AI coding tool",
        ),
    ]

    if tool_filter:
        wanted = set(tool_filter)
        known = {t.tool for t in tools}
        unknown = sorted(wanted - known)
        if unknown:
            raise ValueError(
                "unknown tool(s): %s (known: %s)"
                % (", ".join(unknown), ", ".join(sorted(known)))
            )
        tools = [t for t in tools if t.tool in wanted]

    return {t.tool: t for t in tools}


def detect_all() -> List[dict]:
    """Inventory of every tool and its data path.

    Return shape is the contract with ``agentson platform detect``, which
    JSON-encodes this directly -- every value must stay JSON-serialisable.
    """
    return [info.as_dict() for info in get_registry().values()]


def present_tools(tool_filter: Optional[List[str]] = None) -> List[ToolInfo]:
    """Registry entries whose data location actually exists on disk."""
    return [t for t in get_registry(tool_filter).values() if t.present]
