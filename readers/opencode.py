"""
AgentSON Reader: opencode
Reads session data from opencode's SQLite database.
"""

import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional, Any


class OpencodeReader:
    """Reads agent sessions from opencode's SQLite database."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
        
    def connect(self):
        """Connect to the SQLite database."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        
    def disconnect(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            
    def list_sessions(self, limit: int = 50) -> List[Dict]:
        """List available sessions."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, title, time_created, time_updated, model, agent,
                   tokens_input, tokens_output, cost
            FROM session
            ORDER BY time_updated DESC
            LIMIT ?
        """, (limit,))
        
        sessions = []
        for row in cursor.fetchall():
            sessions.append({
                "id": row["id"],
                "title": row["title"],
                "created": row["time_created"],
                "updated": row["time_updated"],
                "model": row["model"],
                "agent": row["agent"],
                "tokens_input": row["tokens_input"],
                "tokens_output": row["tokens_output"],
                "cost": row["cost"]
            })
        return sessions
    
    def read_session(self, session_id: str) -> Dict:
        """Read a full session and convert to AgentSON format."""
        cursor = self.conn.cursor()
        
        # Get session metadata
        cursor.execute("""
            SELECT * FROM session WHERE id = ?
        """, (session_id,))
        session = cursor.fetchone()
        
        if not session:
            raise ValueError(f"Session {session_id} not found")
            
        # Get messages
        cursor.execute("""
            SELECT id, time_created, time_updated, data
            FROM message
            WHERE session_id = ?
            ORDER BY time_created
        """, (session_id,))
        messages = cursor.fetchall()
        
        # Get parts
        cursor.execute("""
            SELECT id, message_id, time_created, time_updated, data
            FROM part
            WHERE session_id = ?
            ORDER BY time_created
        """, (session_id,))
        parts = cursor.fetchall()
        
        # Get todos
        cursor.execute("""
            SELECT content, status, priority, position
            FROM todo
            WHERE session_id = ?
            ORDER BY position
        """, (session_id,))
        todos = cursor.fetchall()
        
        # Convert to AgentSON format
        return self._convert_to_agentson(
            session, messages, parts, todos
        )
    
    def _convert_to_agentson(
        self,
        session: Dict,
        messages: List[Dict],
        parts: List[Dict],
        todos: List[Dict]
    ) -> Dict:
        """Convert opencode data to AgentSON format."""
        
        # Parse model info
        try:
            model_info = json.loads(session["model"]) if session["model"] else {}
        except:
            model_info = {"id": "unknown"}
            
        # Build entries
        entries = []
        
        # Process messages and parts
        for msg in messages:
            try:
                msg_data = json.loads(msg["data"]) if msg["data"] else {}
            except:
                msg_data = {}
                
            role = msg_data.get("role", "unknown")
            
            if role == "user":
                # Extract user query from parts
                user_parts = [p for p in parts if p["message_id"] == msg["id"]]
                for part in user_parts:
                    try:
                        part_data = json.loads(part["data"]) if part["data"] else {}
                    except:
                        part_data = {}
                        
                    if part_data.get("type") == "text":
                        entries.append({
                            "type": "user-query",
                            "text": part_data.get("text", ""),
                            "timestamp": msg["time_created"]
                        })
                        
            elif role == "assistant":
                # Extract thinking and answer from parts
                assistant_parts = [p for p in parts if p["message_id"] == msg["id"]]
                for part in assistant_parts:
                    try:
                        part_data = json.loads(part["data"]) if part["data"] else {}
                    except:
                        part_data = {}
                        
                    part_type = part_data.get("type", "")
                    
                    if part_type == "text":
                        entries.append({
                            "type": "answer",
                            "text": part_data.get("text", ""),
                            "timestamp": msg["time_created"]
                        })
                    elif part_type == "reasoning":
                        # Real opencode sessions emit standalone reasoning
                        # parts (verified against a live message/parts
                        # export, not just synthetic fixtures).
                        entries.append({
                            "type": "thought",
                            "text": part_data.get("text", ""),
                            "timestamp": (part_data.get("time") or {}).get("start", msg["time_created"])
                        })
                    elif part_type == "tool":
                        # Current opencode schema: tool name at top level,
                        # input/output/status nested under "state".
                        state = part_data.get("state", {}) or {}
                        status_raw = state.get("status", "")
                        entries.append({
                            "type": "action",
                            "tool": part_data.get("tool", "unknown"),
                            "code": json.dumps(state.get("input", {})),
                            "output": str(state.get("output", "")),
                            "status": "success" if status_raw == "completed" else (status_raw or "unknown"),
                            "timestamp": (state.get("time") or {}).get("start", msg["time_created"])
                        })
                    elif part_type == "tool-invocation":
                        # Older opencode schema shape, kept as a fallback
                        # for exports predating the "tool" part type.
                        entries.append({
                            "type": "action",
                            "tool": part_data.get("toolName", "unknown"),
                            "code": json.dumps(part_data.get("args", {})),
                            "output": str(part_data.get("result", "")),
                            "status": "success" if not part_data.get("error") else "error",
                            "timestamp": msg["time_created"]
                        })
                        
        # Add todos as side-effects
        for todo in todos:
            entries.append({
                "type": "side-effect",
                "action": "todo_update",
                "text": todo["content"],
                "status": todo["status"],
                "timestamp": None
            })
        
        # Sort entries by timestamp
        entries.sort(key=lambda x: x.get("timestamp") or 0)
        
        # Build AgentSON document
        agentson = {
            "$schema": "https://agentson.dev/schema/v1.json",
            "id": session["id"],
            "tool": {
                "name": "opencode",
                "version": "0.0.13",
                "session_id": session["id"]
            },
            "agent": {
                "name": model_info.get("id", "unknown"),
                "provider": model_info.get("providerID", "opencode"),
                "variant": model_info.get("variant", "high")
            },
            "started_at": self._timestamp_to_iso(session["time_created"]),
            "ended_at": self._timestamp_to_iso(session["time_updated"]),
            "context": {
                "working_directory": session["directory"] if session["directory"] else "",
                "platform": "win32",
                "shell": "powershell"
            },
            "entries": entries,
            "metadata": {
                "total_tokens": (session["tokens_input"] or 0) + (session["tokens_output"] or 0),
                "cost": session["cost"] or 0.0,
                "messages": len(messages),
                "parts": len(parts),
                "exported_at": datetime.utcnow().isoformat() + "Z"
            }
        }
        
        return agentson
    
    def _timestamp_to_iso(self, timestamp: Optional[int]) -> Optional[str]:
        """Convert millisecond timestamp to ISO 8601 string."""
        if timestamp is None:
            return None
        try:
            dt = datetime.utcfromtimestamp(timestamp / 1000)
            return dt.isoformat() + "Z"
        except:
            return None


def read(db_path: str, session_id: str) -> Dict:
    """Convenience function to read an opencode session."""
    reader = OpencodeReader(db_path)
    reader.connect()
    try:
        return reader.read_session(session_id)
    finally:
        reader.disconnect()


def list_sessions(db_path: str, limit: int = 50) -> List[Dict]:
    """Convenience function to list opencode sessions."""
    reader = OpencodeReader(db_path)
    reader.connect()
    try:
        return reader.list_sessions(limit)
    finally:
        reader.disconnect()
