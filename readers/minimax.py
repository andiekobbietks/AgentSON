"""
AgentSON Reader: minimax
Reads session data from Mavis (MiniMax Code) SQLite database.

Schema (verified 2026-07-08 against C:\\Users\\LLM-Test\\.mavis\\sqlite.db):

  sessions
    session_id, agent_name, session_type, version, title,
    workspace_dir, status, pid, port, session_data_dir,
    compressed, compressed_at, config_synced_hash, process_alive,
    last_active_at, framework_type, extra_data, framework_session_id,
    pinned, pinned_at, created_at, updated_at,
    effective_model, effective_model_variant

  session_messages
    id, session_id, msg_id, role, data (JSON blob), timestamp

  token_usage
    id, session_id, agent_name, framework_type, turn_id, model, ts,
    input_tokens, output_tokens, reasoning_tokens,
    cache_read_tokens, cache_write_tokens, cost_usd, raw

The `data` blob for an assistant message looks like:
  {
    "msg_id": "...", "role": "assistant", "msg_type": 2,
    "timestamp": 1783522138086,
    "thinking_content": "..." | null,
    "msg_content": "..." | null,
    "tool_calls": [
      {"tool_name": "bash", "tool_call_id": "...",
       "tool_call_status": 2,
       "tool_call_args": "<JSON string of args>",
       "tool_call_result_data": "<output string>"}
    ],
    "source": "api"
  }

User messages have `msg_content` (the raw user text) and no tool_calls.
"""

import sqlite3
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any


class MiniMaxReader:
    """Reads agent sessions from Mavis/MiniMax SQLite database."""

    TOOL_VERSION = "1.0.0"
    SCHEMA_VERSION = "1.2"

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None

    def connect(self):
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row

    def disconnect(self):
        if self.conn:
            self.conn.close()
            self.conn = None

    # --- list / read ---

    def _table_columns(self, table: str) -> List[str]:
        cur = self.conn.cursor()
        cur.execute(f"PRAGMA table_info({table})")
        return [r[1] for r in cur.fetchall()]

    def _safe_select(self, table: str, preferred: List[str], where: str = "",
                     order_by: str = "", limit: Optional[int] = None,
                     params: tuple = ()) -> List[sqlite3.Row]:
        cols = [c for c in preferred if c in self._table_columns(table)]
        if not cols:
            return []
        cur = self.conn.cursor()
        sql = f"SELECT {', '.join(cols)} FROM {table}"
        if where:
            sql += f" WHERE {where}"
        if order_by:
            sql += f" ORDER BY {order_by}"
        if limit is not None:
            sql += " LIMIT ?"
            params = params + (limit,)
        cur.execute(sql, params)
        return cur.fetchall()

    def list_sessions(self, limit: int = 50) -> List[Dict]:
        rows = self._safe_select(
            "sessions",
            preferred=[
                "session_id", "agent_name", "title", "framework_type",
                "effective_model", "effective_model_variant",
                "status", "created_at", "updated_at", "last_active_at",
            ],
            order_by="updated_at DESC",
            limit=limit,
        )
        out = []
        for row in rows:
            d = dict(row)
            out.append(
                {
                    "id": d.get("session_id"),
                    "title": d.get("title"),
                    "agent": d.get("agent_name"),
                    "framework_type": d.get("framework_type"),
                    "model": d.get("effective_model"),
                    "model_variant": d.get("effective_model_variant"),
                    "status": d.get("status"),
                    "created": d.get("created_at"),
                    "updated": d.get("updated_at"),
                    "last_active_at": d.get("last_active_at"),
                }
            )
        return out

    def read_session(self, session_id: str) -> Dict:
        cur = self.conn.cursor()

        cur.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,))
        sess_row = cur.fetchone()
        if not sess_row:
            raise ValueError(f"Session {session_id} not found")

        msg_rows = self._safe_select(
            "session_messages",
            preferred=["msg_id", "role", "data", "timestamp"],
            where="session_id = ?",
            order_by="timestamp",
            params=(session_id,),
        )

        token_rows = self._safe_select(
            "token_usage",
            preferred=[
                "input_tokens", "output_tokens", "reasoning_tokens",
                "cache_read_tokens", "cache_write_tokens", "cost_usd", "ts",
            ],
            where="session_id = ?",
            order_by="ts",
            params=(session_id,),
        )

        peer_rows = self._safe_select(
            "session_peers",
            preferred=["parent_session_id", "agent_name", "task_tree_id", "created_at"],
            where="session_id = ?",
            order_by="created_at",
            params=(session_id,),
        )

        return self._convert_to_agentson(sess_row, msg_rows, token_rows, peer_rows)

    # --- conversion ---

    def _convert_to_agentson(
        self,
        sess: sqlite3.Row,
        msg_rows: List[sqlite3.Row],
        token_rows: List[sqlite3.Row],
        peer_rows: List[sqlite3.Row],
    ) -> Dict:
        entries: List[Dict[str, Any]] = []

        # Build stream-meta header first (timestamp = session start)
        entries.append(self._stream_meta_entry(sess, peer_rows))

        # Now process messages
        for msg in msg_rows:
            ts = msg["timestamp"]
            try:
                blob = json.loads(msg["data"]) if msg["data"] else {}
            except Exception:
                blob = {}

            role = blob.get("role") or msg["role"]
            if role == "user":
                text = blob.get("msg_content") or ""
                if text:
                    entries.append(
                        {
                            "type": "user-query",
                            "agent": "user",
                            "text": text,
                            "timestamp": ts,
                            "provenance": {
                                "confidence": "confirmed",
                                "source": "user",
                                "timestamp_ms": ts,
                            },
                            "_transparency": {
                                "ai_generated": False,
                                "detectable": False,
                            },
                        }
                    )
            elif role == "assistant":
                # 1. thinking → thought
                thinking = blob.get("thinking_content")
                if thinking:
                    entries.append(
                        {
                            "type": "thought",
                            "agent": "minimax",
                            "text": thinking,
                            "timestamp": ts,
                            "provenance": {
                                "confidence": "ml_generated",
                                "source": "other",
                                "timestamp_ms": ts,
                            },
                            "_transparency": {
                                "ai_generated": True,
                                "marking_scheme": "agentson-v1.2",
                                "detectable": True,
                            },
                        }
                    )

                # 2. tool_calls → action (+ paired observation for output)
                for tc in blob.get("tool_calls") or []:
                    args_raw = tc.get("tool_call_args", "")
                    args_obj: Dict[str, Any] = {}
                    if isinstance(args_raw, str) and args_raw:
                        try:
                            args_obj = json.loads(args_raw)
                        except Exception:
                            # keep raw under a fallback field
                            args_obj = {"_raw": args_raw}
                    elif isinstance(args_raw, dict):
                        args_obj = args_raw

                    tool_name = tc.get("tool_name", "unknown")
                    status_code = tc.get("tool_call_status")
                    status_map = {0: "pending", 1: "partial", 2: "success", 3: "error"}
                    status = status_map.get(status_code, "unknown")

                    correlation_id = tc.get("tool_call_id")

                    # Mavis tool names map onto semantic AgentSON operations where possible
                    semantic_tool = self._semantic_tool(tool_name, args_obj)

                    entries.append(
                        {
                            "type": "action",
                            "agent": "minimax",
                            "tool": semantic_tool,
                            "args": args_obj,
                            "tool_call_id": correlation_id,
                            "status": status,
                            "timestamp": ts,
                            "correlation_id": correlation_id,
                            "provenance": {
                                "confidence": "confirmed",
                                "source": "mcp",
                                "timestamp_ms": ts,
                            },
                            "_transparency": {
                                "ai_generated": True,
                                "marking_scheme": "agentson-v1.2",
                                "detectable": True,
                            },
                        }
                    )

                    output = self._resolve_truncated_output(tc.get("tool_call_result_data") or "")
                    if output:
                        entries.append(
                            {
                                "type": "observation",
                                "agent": "minimax",
                                "source": "tool",
                                "text": output,
                                "timestamp": ts,
                                "correlation_id": correlation_id,
                                "provenance": {
                                    "confidence": "confirmed",
                                    "source": "mcp",
                                    "timestamp_ms": ts,
                                },
                            }
                        )

                # 3. final answer text (if any, and only if not pure tool)
                msg_content = blob.get("msg_content")
                if msg_content and not (blob.get("tool_calls") and not msg_content):
                    entries.append(
                        {
                            "type": "answer",
                            "agent": "minimax",
                            "text": msg_content,
                            "timestamp": ts,
                            "provenance": {
                                "confidence": "ml_generated",
                                "source": "other",
                                "timestamp_ms": ts,
                            },
                            "_transparency": {
                                "ai_generated": True,
                                "marking_scheme": "agentson-v1.2",
                                "detectable": True,
                            },
                        }
                    )

        # Sort entries by timestamp (stream-meta should stay first because it's
        # the session start; keep ties stable)
        def _key(e: Dict[str, Any]):
            ts = e.get("timestamp")
            return (0 if e.get("type") == "stream-meta" else 1, ts or 0)

        entries.sort(key=_key)

        # Totals
        total_input = sum(t["input_tokens"] or 0 for t in token_rows)
        total_output = sum(t["output_tokens"] or 0 for t in token_rows)
        total_reasoning = sum(t["reasoning_tokens"] or 0 for t in token_rows)
        total_cache_read = sum(t["cache_read_tokens"] or 0 for t in token_rows)
        total_cache_write = sum(t["cache_write_tokens"] or 0 for t in token_rows)
        total_cost = sum(t["cost_usd"] or 0.0 for t in token_rows)

        # Heartbeat = max timestamp across all entries
        heartbeats = [e["timestamp"] for e in entries if e.get("timestamp")]
        last_hb = max(heartbeats) if heartbeats else sess["updated_at"]

        # Build digest
        by_type: Dict[str, int] = {}
        for e in entries:
            by_type[e["type"]] = by_type.get(e["type"], 0) + 1

        return {
            "$schema": "https://agentson.dev/schema/v1.2.json",
            "id": sess["session_id"],
            "tool": {
                "name": "minimax",
                "version": self.TOOL_VERSION,
                "session_id": sess["session_id"],
            },
            "agent": {
                "name": sess["effective_model"] or "unknown",
                "provider": "minimax",
                "variant": sess["effective_model_variant"] or "thinking",
            },
            "task": sess["title"] or None,
            "outcome": sess["status"],
            "started_at": self._ms_to_iso(sess["created_at"]),
            "ended_at": self._ms_to_iso(sess["updated_at"]),
            "heartbeat": self._ms_to_iso(last_hb),
            "context": {
                "working_directory": sess["workspace_dir"] or "",
                "platform": "win32",
                "shell": "powershell",
            },
            "entries": entries,
            "metadata": {
                "total_tokens": total_input + total_output,
                "input_tokens": total_input,
                "output_tokens": total_output,
                "reasoning_tokens": total_reasoning,
                "cache_read_tokens": total_cache_read,
                "cache_write_tokens": total_cache_write,
                "cost": total_cost,
                "messages": len(msg_rows),
                "parts": len(entries),
                "exported_at": datetime.now(timezone.utc).isoformat(),
                "framework_type": sess["framework_type"],
                "framework_session_id": sess["framework_session_id"],
                "agent_name": sess["agent_name"],
                "session_data_dir": sess["session_data_dir"],
            },
            "compliance": {
                "jurisdiction": "uk",
                "bases": ["uk_gdpr_art_20_portability"],
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "schema_version": self.SCHEMA_VERSION,
            },
            "reconstruct_mode": "live",
            "digest": {
                "total_entries": len(entries),
                "by_type": by_type,
                "by_confidence": self._by_confidence(entries),
                "has_gaps": False,
            },
        }

    # --- helpers ---

    @staticmethod
    def _stream_meta_entry(sess: sqlite3.Row, peer_rows: List[sqlite3.Row]) -> Dict[str, Any]:
        agents = [{"id": "user", "name": "user", "capabilities": ["input"]}]
        agents.append(
            {
                "id": "minimax",
                "name": sess["agent_name"] or "mavis",
                "capabilities": [
                    "bash",
                    "filesystem",
                    "search",
                    "browser",
                    "web",
                    "mcp",
                    "delegation",
                ],
            }
        )
        return {
            "type": "stream-meta",
            "stream_id": sess["session_id"],
            "mode": "single" if not peer_rows else "collab",
            "agents": agents,
            "timestamp": sess["created_at"],
            "provenance": {
                "confidence": "confirmed",
                "source": "system",
                "timestamp_ms": sess["created_at"],
            },
        }

    @staticmethod
    def _semantic_tool(tool_name: str, args_obj: Dict[str, Any]) -> str:
        """Map raw MiniMax tool names to AgentSON's semantic operation vocabulary."""
        if tool_name == "bash":
            cmd = args_obj.get("command", "") if isinstance(args_obj, dict) else ""
            if "Get-ChildItem" in cmd or cmd.startswith("ls ") or "dir " in cmd:
                return "filesystem.list"
            if "Get-Content" in cmd or "cat " in cmd:
                return "filesystem.read"
            if "Select-String" in cmd or "grep " in cmd:
                return "filesystem.search"
            if "git " in cmd:
                return "git.run"
            return "bash.execute"
        if tool_name in ("read", "Read"):
            return "filesystem.read"
        if tool_name in ("write", "Write", "edit", "Edit"):
            return "filesystem.write"
        if tool_name in ("glob", "Glob"):
            return "filesystem.list"
        if tool_name in ("grep", "Grep"):
            return "filesystem.search"
        if tool_name == "webfetch":
            return "web.fetch"
        if tool_name == "web_search":
            return "web.search"
        if tool_name == "skill":
            return "skill.invoke"
        return tool_name

    @staticmethod
    def _by_confidence(entries: List[Dict]) -> Dict[str, int]:
        out: Dict[str, int] = {}
        for e in entries:
            c = (e.get("provenance") or {}).get("confidence") or "unknown"
            out[c] = out.get(c, 0) + 1
        return out

    @staticmethod
    def _resolve_truncated_output(text) -> str:
        """Mavis/MiniMax shares the same underlying tool-execution layer as
        opencode, so large tool outputs get truncated inline with the same
        marker: "...output truncated...\n\nFull output saved to: <path>"
        This chases that reference and inlines the real content when the
        side file is still present on disk (falls back to the truncated
        preview if the side file has moved or been cleaned up)."""
        text = str(text or "")
        marker = "Full output saved to: "
        if "...output truncated..." not in text or marker not in text:
            return text
        try:
            path_start = text.index(marker) + len(marker)
            path_end = text.index("\n", path_start)
            side_path = text[path_start:path_end].strip()
        except ValueError:
            return text
        try:
            with open(side_path, "r", encoding="utf-8", errors="replace") as f:
                return f.read()
        except OSError:
            return text

    @staticmethod
    def _ms_to_iso(ts: Optional[int]) -> Optional[str]:
        if ts is None:
            return None
        try:
            dt = datetime.fromtimestamp(ts / 1000, tz=timezone.utc)
            return dt.isoformat().replace("+00:00", "Z")
        except Exception:
            return None


def read(db_path: str, session_id: str) -> Dict:
    """Read a MiniMax/Mavis session and return it in AgentSON v1.2 form."""
    reader = MiniMaxReader(db_path)
    reader.connect()
    try:
        return reader.read_session(session_id)
    finally:
        reader.disconnect()


def list_sessions(db_path: str, limit: int = 50) -> List[Dict]:
    """List MiniMax/Mavis sessions, newest first."""
    reader = MiniMaxReader(db_path)
    reader.connect()
    try:
        return reader.list_sessions(limit)
    finally:
        reader.disconnect()