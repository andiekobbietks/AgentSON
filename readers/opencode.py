"""
AgentSON reader for OpenCode SQLite session stores.

Supports the legacy 1.x tables (session/message/part) and the current
2.x tables (session_v2/session_message/session_part). Raw rows and decoded
JSON payloads are retained in source_payload/source_metadata; canonical
fields are projections and must not be treated as a lossless replacement.
"""
import json
import os
import platform
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


class OpencodeReader:
    """Read OpenCode sessions from either supported SQLite schema generation."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
        self.schema_generation = None

    def connect(self):
        """Open the database and detect its schema without modifying it."""
        # OpenCode may keep WAL files active. Read-only mode prevents the
        # exporter from mutating the user's database or creating a new DB.
        if self.db_path == ":memory:":
            self.conn = sqlite3.connect(self.db_path)
        else:
            database_uri = Path(self.db_path).resolve().as_uri() + "?mode=ro"
            self.conn = sqlite3.connect(database_uri, uri=True)
        self.conn.row_factory = sqlite3.Row
        if self._table_exists("session_v2") and self._table_exists("session_message"):
            self.schema_generation = "2.x"
        elif self._table_exists("session") and self._table_exists("message"):
            self.schema_generation = "1.x"
        else:
            raise ValueError(
                "Unsupported OpenCode database: expected session/message (1.x) "
                "or session_v2/session_message (2.x) tables"
            )

    def disconnect(self):
        if self.conn:
            self.conn.close()
            self.conn = None

    def _table_exists(self, name: str) -> bool:
        row = self.conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
            (name,),
        ).fetchone()
        return row is not None

    def _columns(self, table: str) -> List[str]:
        return [row["name"] for row in self.conn.execute("PRAGMA table_info(" + table + ")")]

    @staticmethod
    def _dict(row) -> Dict[str, Any]:
        return dict(row) if row is not None else {}

    @staticmethod
    def _json(value, default=None):
        if default is None:
            default = {}
        if isinstance(value, (dict, list)):
            return value
        if value is None or value == "":
            return default
        try:
            return json.loads(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _text_content(content) -> str:
        """Project readable text from OpenCode tool content without discarding raw blocks."""
        if isinstance(content, str):
            return content
        if not isinstance(content, list):
            return "" if content is None else str(content)
        values = []
        for item in content:
            if isinstance(item, dict):
                if isinstance(item.get("text"), str):
                    values.append(item["text"])
                elif item.get("type") in ("image", "file"):
                    values.append("[{} attachment]".format(item.get("type")))
            elif item is not None:
                values.append(str(item))
        return "\n".join(values)

    @staticmethod
    def _status(raw: str) -> str:
        return {
            "completed": "success",
            "success": "success",
            "error": "error",
            "failed": "error",
            "running": "running",
            "streaming": "running",
            "pending": "pending",
        }.get(raw, raw or "unknown")

    def list_sessions(self, limit: int = 50) -> List[Dict]:
        """List sessions from the detected schema generation."""
        if self.schema_generation == "2.x":
            rows = self.conn.execute(
                """SELECT * FROM session_v2
                   WHERE time_archived IS NULL
                   ORDER BY time_updated DESC LIMIT ?""",
                (limit,),
            ).fetchall()
            result = []
            for row in rows:
                item = self._dict(row)
                model = self._json(item.get("model"))
                result.append({
                    "id": item.get("id"),
                    "title": item.get("title"),
                    "created": item.get("time_created"),
                    "updated": item.get("time_updated"),
                    "model": model,
                    "agent": item.get("agent"),
                    "tokens_input": item.get("tokens_input", 0),
                    "tokens_output": item.get("tokens_output", 0),
                    "cost": item.get("cost", 0),
                    "parent_id": item.get("parent_id"),
                    "version": item.get("version"),
                })
            return result

        rows = self.conn.execute(
            """SELECT id, title, time_created, time_updated, model, agent,
                      tokens_input, tokens_output, cost
               FROM session ORDER BY time_updated DESC LIMIT ?""",
            (limit,),
        ).fetchall()
        return [{
            "id": row["id"], "title": row["title"],
            "created": row["time_created"], "updated": row["time_updated"],
            "model": row["model"], "agent": row["agent"],
            "tokens_input": row["tokens_input"], "tokens_output": row["tokens_output"],
            "cost": row["cost"],
        } for row in rows]

    def read_session(self, session_id: str) -> Dict:
        """Read and project a session, preserving its native records."""
        if self.schema_generation == "2.x":
            return self._read_v2(session_id)
        return self._read_v1(session_id)

    def _read_v1(self, session_id: str) -> Dict:
        session_row = self.conn.execute(
            "SELECT * FROM session WHERE id = ?", (session_id,)
        ).fetchone()
        if not session_row:
            raise ValueError("Session {} not found".format(session_id))
        session = self._dict(session_row)
        messages = self.conn.execute(
            """SELECT * FROM message WHERE session_id = ?
               ORDER BY time_created, id""", (session_id,)
        ).fetchall()
        parts = self.conn.execute(
            """SELECT * FROM part WHERE session_id = ?
               ORDER BY time_created, id""", (session_id,)
        ).fetchall()
        todos = []
        if self._table_exists("todo"):
            todos = self.conn.execute(
                "SELECT * FROM todo WHERE session_id = ? ORDER BY position",
                (session_id,),
            ).fetchall()
        return self._convert_v1(session, messages, parts, todos)

    def _read_v2(self, session_id: str) -> Dict:
        session_row = self.conn.execute(
            "SELECT * FROM session_v2 WHERE id = ?", (session_id,)
        ).fetchone()
        if not session_row:
            raise ValueError("Session {} not found".format(session_id))
        session = self._dict(session_row)
        messages = self.conn.execute(
            """SELECT * FROM session_message WHERE session_id = ?
               ORDER BY seq, time_created, id""", (session_id,)
        ).fetchall()
        parts = self.conn.execute(
            """SELECT * FROM session_part WHERE session_id = ?
               ORDER BY message_id, ordinal""", (session_id,)
        ).fetchall() if self._table_exists("session_part") else []
        inbox = self.conn.execute(
            """SELECT * FROM session_inbox WHERE session_id = ?
               ORDER BY enqueued_seq""", (session_id,)
        ).fetchall() if self._table_exists("session_inbox") else []
        return self._convert_v2(session, messages, parts, inbox)

    def _session_document(self, session: Dict, entries: List[Dict],
                          message_count: int, part_count: int,
                          schema_generation: str) -> Dict:
        model = self._json(session.get("model"))
        if not isinstance(model, dict):
            model = {"id": str(model)} if model else {}
        created = session.get("time_created")
        updated = session.get("time_updated")
        token_fields = [
            session.get("tokens_input") or 0,
            session.get("tokens_output") or 0,
            session.get("tokens_reasoning") or 0,
        ]
        total_tokens = sum(int(value or 0) for value in token_fields)
        directory = session.get("directory") or ""
        version = session.get("version") or "unknown"
        session_id = session.get("id")
        return {
            "$schema": "https://agentson.dev/schema/v1.2.json",
            "version": "1.2",
            "id": session_id,
            "title": session.get("title") or "",
            "tool": {
                "name": "opencode", "version": version,
                "session_id": session_id,
            },
            "agent": {
                "name": model.get("id") or session.get("agent") or "unknown",
                "provider": model.get("providerID") or "unknown",
                "variant": model.get("variant") or "unknown",
            },
            "started_at": self._timestamp_to_iso(created),
            "ended_at": self._timestamp_to_iso(updated),
            "context": {"working_directory": directory, "platform": platform.system().lower()},
            "entries": entries,
            "source_metadata": {
                "schema_generation": schema_generation,
                "session_row": session,
            },
            "metadata": {
                "total_tokens": total_tokens,
                "tokens_input": session.get("tokens_input") or 0,
                "tokens_output": session.get("tokens_output") or 0,
                "tokens_reasoning": session.get("tokens_reasoning") or 0,
                "tokens_cache_read": session.get("tokens_cache_read") or 0,
                "tokens_cache_write": session.get("tokens_cache_write") or 0,
                "cost": session.get("cost") or 0.0,
                "messages": message_count,
                "parts": part_count,
            },
        }

    def _convert_v1(self, session: Dict, messages, parts, todos) -> Dict:
        entries = []
        parts_by_message = {}
        for part in parts:
            parts_by_message.setdefault(part["message_id"], []).append(part)

        for msg_row in messages:
            msg = self._dict(msg_row)
            data = self._json(msg.get("data"))
            role = data.get("role", "unknown")
            entries_before_message = len(entries)
            for part_row in parts_by_message.get(msg.get("id"), []):
                part = self._dict(part_row)
                pdata = self._json(part.get("data"))
                part_type = pdata.get("type")
                base = {
                    "timestamp": part.get("time_created") or msg.get("time_created"),
                    "source_payload": {"message": msg, "message_data": data,
                                       "part": part, "part_data": pdata},
                }
                if role == "user" and part_type == "text":
                    entries.append(dict(base, type="user-query", text=pdata.get("text", "")))
                elif role == "assistant" and part_type == "text":
                    entries.append(dict(base, type="answer", text=pdata.get("text", "")))
                elif role == "assistant" and part_type == "reasoning":
                    entries.append(dict(base, type="thought", text=pdata.get("text", "")))
                elif role == "assistant" and part_type == "tool":
                    state = pdata.get("state") or {}
                    raw_status = state.get("status", "")
                    entries.append(dict(
                        base, type="action", tool=pdata.get("tool", "unknown"),
                        code=json.dumps(state.get("input", {}), ensure_ascii=False),
                        output=self._resolve_truncated_output(
                            self._text_content(state.get("content", state.get("output", "")))
                        ),
                        status=self._status(raw_status),
                        tool_call_id=pdata.get("callID"),
                    ))
                elif role == "assistant" and part_type == "tool-invocation":
                    entries.append(dict(
                        base, type="action", tool=pdata.get("toolName", "unknown"),
                        code=json.dumps(pdata.get("args", {}), ensure_ascii=False),
                        output=str(pdata.get("result", "")),
                        status="error" if pdata.get("error") else "success",
                    ))
                else:
                    entries.append(dict(
                        base, type="system-event", source="other",
                        text="Unmapped OpenCode part: {}".format(part_type or "unknown"),
                    ))
            if len(entries) == entries_before_message:
                entries.append({
                    "type": "system-event", "source": "other",
                    "timestamp": msg.get("time_created"),
                    "text": "OpenCode message contained no mapped parts (role: {})".format(role),
                    "source_payload": {"message": msg, "message_data": data},
                })

        entries.sort(key=lambda item: item.get("timestamp") or 0)
        for todo_row in todos:
            todo = self._dict(todo_row)
            entries.append({
                "type": "side-effect", "action": "todo_update",
                "text": todo.get("content", ""), "status": todo.get("status", "unknown"),
                "source_payload": {"todo": todo},
            })
        return self._session_document(session, entries, len(messages), len(parts), "1.x")

    def _convert_v2(self, session: Dict, messages, parts, inbox) -> Dict:
        entries = []
        parts_by_message = {}
        for part_row in parts:
            part = self._dict(part_row)
            parts_by_message.setdefault(part.get("message_id"), []).append(part)

        for msg_row in messages:
            msg = self._dict(msg_row)
            data = self._json(msg.get("data"))
            msg_type = msg.get("type")
            common = {
                "timestamp": msg.get("time_created"),
                "source_payload": {"message": msg, "message_data": data},
            }
            entries_before_message = len(entries)
            if msg_type == "user":
                entries.append(dict(common, type="user-query", text=data.get("text", "")))
            elif msg_type == "assistant":
                for part_row in parts_by_message.get(msg.get("id"), []):
                    part = self._dict(part_row)
                    pdata = self._json(part.get("data"))
                    ptype = part.get("type") or pdata.get("type")
                    state = pdata.get("state") or {}
                    base = {
                        "timestamp": part.get("time_created") or msg.get("time_created"),
                        "source_payload": {"message": msg, "message_data": data,
                                           "part": part, "part_data": pdata},
                    }
                    if ptype == "text":
                        entries.append(dict(base, type="answer", text=pdata.get("text", "")))
                    elif ptype == "reasoning":
                        entries.append(dict(base, type="thought", text=pdata.get("text", "")))
                    elif ptype == "tool":
                        raw_status = state.get("status", "")
                        output = self._text_content(state.get("content", state.get("output", "")))
                        if raw_status == "error" and not output:
                            output = self._text_content(state.get("error", ""))
                        entries.append(dict(
                            base, type="action", tool=pdata.get("name", "unknown"),
                            code=json.dumps(state.get("input", {}), ensure_ascii=False)
                                if isinstance(state.get("input"), dict) else str(state.get("input", "")),
                            output=self._resolve_truncated_output(output),
                            status=self._status(raw_status),
                            tool_call_id=part.get("call_id") or pdata.get("id"),
                        ))
                    else:
                        entries.append(dict(
                            base, type="system-event", source="other",
                            text="Unmapped OpenCode assistant part: {}".format(ptype or "unknown"),
                        ))
            elif msg_type == "shell":
                entries.append(dict(
                    common, type="action", tool="shell",
                    code=data.get("command", ""),
                    output=data.get("output", ""),
                    status=self._status(data.get("status", "")),
                ))
            else:
                # Preserve non-chat records (synthetic/system/skill/compaction/idle,
                # agent/model/location changes and future message types) explicitly.
                text_value = data.get("text") or data.get("summary") or data.get("description") or ""
                entries.append(dict(
                    common, type="system-event", source="other",
                    text=text_value or "OpenCode message type: {}".format(msg_type or "unknown"),
                ))
            if len(entries) == entries_before_message:
                entries.append(dict(
                    common, type="system-event", source="other",
                    text="OpenCode message contained no mapped content (type: {})".format(msg_type or "unknown"),
                ))

        for inbox_row in inbox:
            row = self._dict(inbox_row)
            entries.append({
                "type": "system-event", "source": "other",
                "timestamp": row.get("time_created"),
                "text": "OpenCode inbox item ({})".format(row.get("type", "unknown")),
                "source_payload": {"inbox": row},
            })
        entries.sort(key=lambda item: item.get("timestamp") or 0)
        timestamped = [item for item in entries if item.get("timestamp") is not None]
        untimestamped = [item for item in entries if item.get("timestamp") is None]
        timestamped.sort(key=lambda item: item.get("timestamp"))
        entries = timestamped + untimestamped
        return self._session_document(session, entries, len(messages), len(parts), "2.x")

    @staticmethod
    def _resolve_truncated_output(text) -> str:
        """Resolve OpenCode's external large-output marker when the file remains available."""
        text = str(text or "")
        marker = "Full output saved to: "
        if "...output truncated..." not in text or marker not in text:
            return text
        try:
            start = text.index(marker) + len(marker)
            end = text.index("\n", start)
            path = text[start:end].strip()
        except ValueError:
            return text
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as handle:
                return handle.read()
        except OSError:
            return text

    @staticmethod
    def _timestamp_to_iso(timestamp: Optional[int]) -> Optional[str]:
        if timestamp is None:
            return None
        try:
            return datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc).isoformat().replace("+00:00", "Z")
        except (OverflowError, OSError, TypeError, ValueError):
            return None


def read(db_path: str, session_id: str) -> Dict:
    reader = OpencodeReader(db_path)
    reader.connect()
    try:
        return reader.read_session(session_id)
    finally:
        reader.disconnect()


def list_sessions(db_path: str, limit: int = 50) -> List[Dict]:
    reader = OpencodeReader(db_path)
    reader.connect()
    try:
        return reader.list_sessions(limit)
    finally:
        reader.disconnect()
