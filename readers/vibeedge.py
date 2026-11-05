# AgentSON core runtime: vibeedge
"""
AgentSON Reader: vibeedge (VibeEdge Studio / VibeSDK)

Reads agent sessions out of VibeEdge's local Cloudflare state.

Two backends exist, and they are not interchangeable (see
vibesdk/worker/agents/core/conversation/MessageLoader.ts):

  think  -> ThinkAgent Durable Object, `assistant_messages` table.
            Each row is an AI-SDK UIMessage: {id, role, parts[]}.
            This is where real sessions live.
  phasic -> CodeGeneratorAgent Durable Object, `full_conversations`
            table: (id TEXT PRIMARY KEY, messages TEXT).

Neither VibeEdge nor the Cloudflare `agents` SDK exposes an export
endpoint for either store, which is why a direct reader is the only
route. Both are opened read-only (mode=ro) because miniflare keeps
them live while the dev server runs.

Two facts about the source that shape the mapping:

  1. `assistant_messages.session_id` is EMPTY. The Durable Object id is
     the only session identity available, so it is used as the session
     id and the missing column is recorded in the digest.
  2. Reasoning parts arrive with EMPTY text but a Google provider
     signature — the model withheld the reasoning. An empty `thought`
     would assert a fact that is not in the record, so those are
     counted instead of emitted, and the session is marked has_gaps.

Nothing here is inferred. Every part is explicitly typed by the source,
so provenance.confidence is "confirmed" throughout and
provenance.source is "export" — the value came from a platform export
rather than a live observation.
"""

from __future__ import annotations

import datetime as _dt
import glob
import json
import os
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

THINK_AGENT = "vibesdk-production-ThinkAgent"
CODEGEN_AGENT = "vibesdk-production-CodeGeneratorAgent"

# tool.name is a closed enum of 8 harnesses and VibeEdge is not among them,
# so it takes the escape hatch. Product identity lives in agent.provider,
# which is a free string.
TOOL_NAME = "other"
SCHEMA = "https://agentson.dev/schema/v1.2.json"


def _epoch_ms(raw: Any) -> Optional[int]:
    """ThinkAgent stores created_at as 'YYYY-MM-DD HH:MM:SS', not an epoch."""
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        return int(raw)
    try:
        dt = _dt.datetime.fromisoformat(str(raw).strip())
    except ValueError:
        return None
    return int(dt.replace(tzinfo=_dt.timezone.utc).timestamp() * 1000)


def _iso(ms: Optional[int]) -> Optional[str]:
    if ms is None:
        return None
    return (_dt.datetime.fromtimestamp(ms / 1000, tz=_dt.timezone.utc)
            .strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z")


class VibeedgeReader:
    """Reads agent sessions from VibeEdge's local Cloudflare state."""

    def __init__(self, root: Optional[str] = None):
        self.root = (Path(root) if root else _default_root())
        self._conns: Dict[str, sqlite3.Connection] = {}

    # -- discovery -----------------------------------------------------

    def _do_dir(self, namespace: str) -> Optional[Path]:
        p = self.root / "state" / "v3" / "do" / namespace
        return p if p.is_dir() else None

    def _open(self, path: Path) -> sqlite3.Connection:
        key = str(path)
        if key not in self._conns:
            # mode=ro: miniflare holds these live while the dev server runs.
            uri = "file:" + path.resolve().as_posix() + "?mode=ro"
            con = sqlite3.connect(uri, uri=True)
            con.execute("PRAGMA busy_timeout=5000")
            con.row_factory = sqlite3.Row
            self._conns[key] = con
        return self._conns[key]

    def _think_files(self) -> List[Path]:
        d = self._do_dir(THINK_AGENT)
        if not d:
            return []
        return sorted(d.glob("*.sqlite"),
                      key=lambda p: -p.stat().st_size)

    # -- public API ----------------------------------------------------

    def list_sessions(self, limit: int = 50) -> List[Dict]:
        """List readable sessions from both backends."""
        out: List[Dict] = []

        for path in self._think_files():
            try:
                con = self._open(path)
                rows = con.execute(
                    "SELECT id, session_id, role, content, created_at "
                    "FROM assistant_messages ORDER BY created_at"
                ).fetchall()
            except sqlite3.Error:
                continue
            if not rows:
                continue
            do_id = path.stem
            stamps = [_epoch_ms(r["created_at"]) for r in rows]
            stamps = [s for s in stamps if s]
            preview = ""
            for r in rows:
                if r["role"] != "user":
                    continue
                try:
                    body = json.loads(r["content"] or "{}")
                except json.JSONDecodeError:
                    continue
                txt = " ".join(
                    p.get("text", "") for p in (body.get("parts") or [])
                    if isinstance(p, dict) and p.get("type") == "text"
                ).strip()
                if txt:
                    preview = txt.splitlines()[0][:60]
                    break
            out.append({
                "id": do_id,
                "backend": "think",
                "session_id_column": rows[0]["session_id"] or "",
                "messages": len(rows),
                "preview": preview,
                "started": _iso(min(stamps)) if stamps else None,
                "ended": _iso(max(stamps)) if stamps else None,
            })
            if len(out) >= limit:
                return out

        # phasic/agentic backend — present in the schema, usually empty.
        d = self._do_dir(CODEGEN_AGENT)
        if d:
            for path in sorted(d.glob("*.sqlite")):
                try:
                    con = self._open(path)
                    rows = con.execute(
                        "SELECT id, length(messages) AS n "
                        "FROM full_conversations WHERE messages IS NOT NULL"
                    ).fetchall()
                except sqlite3.Error:
                    continue
                for r in rows:
                    out.append({
                        "id": r["id"],
                        "backend": "phasic",
                        "session_id_column": r["id"],
                        "messages": 1,
                        "preview": f"full_conversations row ({r['n']} bytes)",
                        "started": None,
                        "ended": None,
                    })
                    if len(out) >= limit:
                        return out
        return out

    def read_session(self, session_id: str) -> Optional[Dict]:
        """Read one session and convert it to an AgentSON v1.2 document."""
        for path in self._think_files():
            if path.stem != session_id:
                continue
            return self._read_think(path)
        # Fall through to the phasic backend by conversation id.
        d = self._do_dir(CODEGEN_AGENT)
        if d:
            for path in sorted(d.glob("*.sqlite")):
                try:
                    con = self._open(path)
                    row = con.execute(
                        "SELECT messages FROM full_conversations "
                        "WHERE id = ?", (session_id,)
                    ).fetchone()
                except sqlite3.Error:
                    continue
                if row and row["messages"]:
                    return self._read_phasic(session_id, row["messages"])
        return None

    # -- think backend -------------------------------------------------

    def _read_think(self, path: Path) -> Optional[Dict]:
        con = self._open(path)
        try:
            rows = con.execute(
                "SELECT id, session_id, role, content, created_at "
                "FROM assistant_messages ORDER BY created_at"
            ).fetchall()
        except sqlite3.Error:
            return None
        if not rows:
            return None

        # The DO id is the only session identity; the column is empty.
        sid = path.stem
        column_populated = any(r["session_id"] for r in rows)

        entries: List[Dict] = []
        withheld_reasoning = 0
        stamps: List[int] = []

        for r in rows:
            ts = _epoch_ms(r["created_at"])
            if ts is not None:
                stamps.append(ts)
            try:
                body = json.loads(r["content"] or "{}")
            except json.JSONDecodeError:
                continue
            parts = body.get("parts") or []
            msg_id = r["id"] or sid

            for p in parts:
                if not isinstance(p, dict):
                    continue
                ptype = p.get("type")

                if ptype == "reasoning":
                    # Empty text is still evidence a step happened, but an
                    # empty `thought` would assert reasoning we do not have.
                    if not (p.get("text") or "").strip():
                        withheld_reasoning += 1
                        continue
                    entries.append({
                        "type": "thought", "text": p["text"],
                        "agent": "vibesdk-think",
                        "correlation_id": msg_id,
                        "timestamp": ts,
                        "provenance": {"confidence": "confirmed",
                                       "source": "export"},
                    })

                elif ptype == "text":
                    txt = p.get("text", "")
                    if r["role"] == "user":
                        entries.append({
                            "type": "user-query", "text": txt, "query": txt,
                            "agent": "human", "correlation_id": msg_id,
                            "timestamp": ts,
                            "provenance": {"confidence": "confirmed",
                                           "source": "export"},
                        })
                    else:
                        entries.append({
                            "type": "answer", "text": txt,
                            "agent": "vibesdk-think",
                            "correlation_id": msg_id, "timestamp": ts,
                            "provenance": {"confidence": "confirmed",
                                           "source": "export"},
                        })

                elif isinstance(ptype, str) and ptype.startswith("tool-"):
                    # One source part carries BOTH the call and its result,
                    # so it becomes two entries joined on toolCallId. That
                    # id is explicit in the source, not reconstructed.
                    tid = p.get("toolCallId")
                    name = p.get("toolName") or ptype[len("tool-"):]
                    done = (p.get("state") == "output-available")
                    entries.append({
                        "type": "action", "tool": name,
                        "args": p.get("input"),
                        "tool_call_id": tid,
                        "correlation_id": tid or msg_id,
                        "status": "success" if done else "pending",
                        "agent": "vibesdk-think", "timestamp": ts,
                        "provenance": {"confidence": "confirmed",
                                       "source": "export"},
                    })
                    raw_out = p.get("output")
                    if raw_out is not None:
                        text = (raw_out if isinstance(raw_out, str)
                                else json.dumps(raw_out, ensure_ascii=False))
                        entries.append({
                            "type": "observation", "text": text,
                            "source": "tool", "agent": name,
                            "correlation_id": tid or msg_id,
                            "timestamp": ts,
                            "provenance": {"confidence": "confirmed",
                                           "source": "export"},
                        })

        return self._build(sid, entries, len(rows),
                           withheld_reasoning, stamps, column_populated)

    # -- phasic backend ------------------------------------------------

    def _read_phasic(self, conv_id: str, blob: str) -> Optional[Dict]:
        """CodeGeneratorAgent stores OpenAI-style ConversationMessage[]."""
        try:
            msgs = json.loads(blob)
        except json.JSONDecodeError:
            return None
        if not isinstance(msgs, list):
            return None

        entries: List[Dict] = []

        def _text(content) -> str:
            if content is None:
                return ""
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                return "\n".join(
                    p.get("text", "") for p in content
                    if isinstance(p, dict) and p.get("type") == "text"
                )
            return str(content)

        for m in msgs:
            if not isinstance(m, dict):
                continue
            role = m.get("role")
            body = _text(m.get("content"))
            mid = m.get("conversationId") or conv_id

            if role == "user":
                entries.append({
                    "type": "user-query", "text": body, "query": body,
                    "agent": "human", "correlation_id": mid,
                    "provenance": {"confidence": "confirmed",
                                   "source": "export"},
                })
            elif role == "tool":
                entries.append({
                    "type": "observation", "text": body, "source": "tool",
                    "agent": m.get("name") or "tool",
                    "correlation_id": m.get("tool_call_id") or mid,
                    "provenance": {"confidence": "confirmed",
                                   "source": "export"},
                })
            elif role == "assistant":
                for tc in (m.get("tool_calls") or []):
                    fn = tc.get("function", {}) if isinstance(tc, dict) else {}
                    tid = tc.get("id")
                    entries.append({
                        "type": "action", "tool": fn.get("name") or "unknown",
                        "code": fn.get("arguments"),
                        "tool_call_id": tid,
                        "correlation_id": tid or mid,
                        "status": "success" if tid else "pending",
                        "agent": "vibesdk-think",
                        "provenance": {"confidence": "confirmed",
                                       "source": "export"},
                    })
                if body:
                    entries.append({
                        "type": "answer", "text": body,
                        "agent": "vibesdk-think", "correlation_id": mid,
                        "provenance": {"confidence": "confirmed",
                                       "source": "export"},
                    })

        return self._build(conv_id, entries, len(msgs), 0, [], True)

    # -- shared --------------------------------------------------------

    def _build(self, sid: str, entries: List[Dict], source_messages: int,
               withheld: int, stamps: List[int],
               column_populated: bool) -> Dict:
        from collections import Counter
        by_type = Counter(e["type"] for e in entries)
        by_conf = Counter(e["provenance"]["confidence"] for e in entries)

        doc: Dict[str, Any] = {
            "$schema": SCHEMA,
            "id": f"vibesdk_{sid}",
            "tool": {"name": TOOL_NAME, "version": "0.1.0",
                     "session_id": sid},
            "agent": {"name": "vibesdk-think", "provider": "vibesdk",
                      "variant": "default"},
            "context": {"platform": "win32"},
            "entries": entries,
            "digest": {
                "total_entries": len(entries),
                "by_type": dict(sorted(by_type.items())),
                "by_confidence": dict(sorted(by_conf.items())),
                # Withheld reasoning and the empty session_id column both
                # make the record incomplete, and both are schema fields,
                # so they survive the round trip here.
                "has_gaps": (withheld > 0) or (not column_populated),
            },
        }
        if stamps:
            doc["started_at"] = _iso(min(stamps))
            doc["ended_at"] = _iso(max(stamps))
        return doc

    # -- teardown ------------------------------------------------------

    def disconnect(self):
        for con in self._conns.values():
            try:
                con.close()
            except sqlite3.Error:
                pass
        self._conns.clear()


def _default_root() -> Path:
    """Default: the local miniflare state dir under a vibeedge checkout."""
    home = Path.home()
    candidates = [
        home / "vibeedge-studio" / "vibesdk" / ".wrangler",
        home / "vibesdk" / ".wrangler",
    ]
    for c in candidates:
        if c.is_dir():
            return c
    return candidates[0]


def read(db_path: str, session_id: str) -> Dict:
    """Convenience function to read one VibeEdge session."""
    reader = VibeedgeReader(db_path)
    try:
        doc = reader.read_session(session_id)
    finally:
        reader.disconnect()
    if not doc:
        raise ValueError(f"VibeEdge session {session_id} not found")
    return doc


def list_sessions(db_path: str, limit: int = 50) -> List[Dict]:
    """Convenience function to list VibeEdge sessions."""
    reader = VibeedgeReader(db_path)
    try:
        return reader.list_sessions(limit)
    finally:
        reader.disconnect()
