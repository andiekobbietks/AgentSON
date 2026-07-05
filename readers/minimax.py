"""
AgentSON Reader: MiniMax
Reads session data from MiniMax's SQLite database.
"""

import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional, Any


class MiniMaxReader:
    """Reads agent sessions from MiniMax's SQLite database."""
    
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
            SELECT session_id, title, agent_name, created_at, updated_at,
                   effective_model, status
            FROM sessions
            ORDER BY updated_at DESC
            LIMIT ?
        """, (limit,))
        
        sessions = []
        for row in cursor.fetchall():
            sessions.append({
                "id": row["session_id"],
                "title": row["title"],
                "agent": row["agent_name"],
                "created": row["created_at"],
                "updated": row["updated_at"],
                "model": row["effective_model"],
                "status": row["status"]
            })
        return sessions
    
    def read_session(self, session_id: str) -> Dict:
        """Read a full session and convert to AgentSON format."""
        cursor = self.conn.cursor()
        
        # Get session metadata
        cursor.execute("""
            SELECT * FROM sessions WHERE session_id = ?
        """, (session_id,))
        session = cursor.fetchone()
        
        if not session:
            raise ValueError(f"Session {session_id} not found")
            
        # Get messages
        cursor.execute("""
            SELECT id, msg_id, role, data, timestamp
            FROM session_messages
            WHERE session_id = ?
            ORDER BY timestamp
        """, (session_id,))
        messages = cursor.fetchall()
        
        # Get token usage
        cursor.execute("""
            SELECT * FROM token_usage
            WHERE session_id = ?
            ORDER BY ts
        """, (session_id,))
        token_usage = cursor.fetchall()
        
        # Convert to AgentSON format
        return self._convert_to_agentsong(
            session, messages, token_usage
        )
    
    def _convert_to_agentsong(
        self,
        session: Dict,
        messages: List[Dict],
        token_usage: List[Dict]
    ) -> Dict:
        """Convert MiniMax data to AgentSON format."""
        
        # Build entries
        entries = []
        
        for msg in messages:
            try:
                msg_data = json.loads(msg["data"]) if msg["data"] else {}
            except:
                msg_data = {}
                
            role = msg_data.get("role", msg["role"])
            
            if role == "user":
                content = msg_data.get("msg_content", "")
                if isinstance(content, list):
                    # Handle multipart content
                    text_parts = []
                    for part in content:
                        if isinstance(part, dict) and part.get("type") == "text":
                            text_parts.append(part.get("text", ""))
                    content = " ".join(text_parts)
                    
                entries.append({
                    "type": "user-query",
                    "text": content,
                    "timestamp": msg["timestamp"]
                })
                
            elif role == "assistant":
                # Extract thinking content
                thinking = msg_data.get("thinking_content", "")
                if thinking:
                    entries.append({
                        "type": "thought",
                        "text": thinking,
                        "timestamp": msg["timestamp"]
                    })
                    
                # Extract message content
                content = msg_data.get("msg_content", "")
                if content:
                    entries.append({
                        "type": "answer",
                        "text": content,
                        "timestamp": msg["timestamp"]
                    })
                    
                # Extract tool calls
                tool_calls = msg_data.get("tool_calls", [])
                for tc in tool_calls:
                    entries.append({
                        "type": "action",
                        "tool": tc.get("tool_name", "unknown"),
                        "code": tc.get("tool_call_args", ""),
                        "output": tc.get("tool_call_result_data", ""),
                        "status": "success" if tc.get("tool_call_status") == 2 else "error",
                        "timestamp": msg["timestamp"]
                    })
        
        # Calculate total tokens
        total_input = sum(t.get("input_tokens", 0) for t in token_usage)
        total_output = sum(t.get("output_tokens", 0) for t in token_usage)
        total_cost = sum(t.get("cost_usd", 0) for t in token_usage)
        
        # Sort entries by timestamp
        entries.sort(key=lambda x: x.get("timestamp") or 0)
        
        # Build AgentSON document
        agentsong = {
            "$schema": "https://agentsong.dev/schema/v1.json",
            "id": session["session_id"],
            "tool": {
                "name": "minimax",
                "version": "1.0.0",
                "session_id": session["session_id"]
            },
            "agent": {
                "name": session["effective_model"] or "unknown",
                "provider": "minimax",
                "variant": "thinking"
            },
            "started_at": self._timestamp_to_iso(session["created_at"]),
            "ended_at": self._timestamp_to_iso(session["updated_at"]),
            "context": {
                "working_directory": session["workspace_dir"] if session["workspace_dir"] else "",
                "platform": "win32",
                "shell": "powershell"
            },
            "entries": entries,
            "metadata": {
                "total_tokens": total_input + total_output,
                "cost": total_cost,
                "messages": len(messages),
                "exported_at": datetime.utcnow().isoformat() + "Z"
            }
        }
        
        return agentsong
    
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
    """Convenience function to read a MiniMax session."""
    reader = MiniMaxReader(db_path)
    reader.connect()
    try:
        return reader.read_session(session_id)
    finally:
        reader.disconnect()


def list_sessions(db_path: str, limit: int = 50) -> List[Dict]:
    """Convenience function to list MiniMax sessions."""
    reader = MiniMaxReader(db_path)
    reader.connect()
    try:
        return reader.list_sessions(limit)
    finally:
        reader.disconnect()
