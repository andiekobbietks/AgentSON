"""
Antigravity IDE SQLite reader for AgentSON.

This reader extracts session data from Antigravity IDE's SQLite database.
The database uses protobuf-encoded binary fields, but we can extract
useful information from the structured fields and embedded JSON.

Usage:
    from readers.antigravity import read_antigravity_session, get_antigravity_sessions

    sessions = get_antigravity_sessions()
    data = read_antigravity_session(sessions[0])
"""

import sqlite3
import json
import os
import re
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

# Default Antigravity IDE path
DEFAULT_DB_PATH = os.path.expanduser(
    r"~\.gemini\antigravity-ide\conversations"
)


def get_antigravity_sessions(db_path: Optional[str] = None) -> List[Dict]:
    """Get all Antigravity IDE sessions from SQLite database."""
    if db_path is None:
        db_path = DEFAULT_DB_PATH

    # Find the conversation database file
    db_files = []
    for f in os.listdir(db_path):
        if f.endswith('.db'):
            db_files.append(os.path.join(db_path, f))

    if not db_files:
        raise FileNotFoundError(f"No .db files found in {db_path}")

    # Use the most recent one
    db_path = max(db_files, key=os.path.getmtime)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get trajectory metadata
    cursor.execute("SELECT trajectory_id, cascade_id, trajectory_type FROM trajectory_meta")
    traj = cursor.fetchone()

    # Get step count
    cursor.execute("SELECT COUNT(*) FROM steps")
    total_steps = cursor.fetchone()[0]

    # Get step types
    cursor.execute("""
        SELECT step_type, COUNT(*) as cnt
        FROM steps
        GROUP BY step_type
        ORDER BY cnt DESC
    """)
    step_types = cursor.fetchall()

    conn.close()

    return [{
        "session_id": traj[0] if traj else "unknown",
        "cascade_id": traj[1] if traj else None,
        "trajectory_type": traj[2] if traj else None,
        "total_steps": total_steps,
        "step_types": {str(s[0]): s[1] for s in step_types},
        "db_path": db_path
    }]


def _extract_text_from_payload(payload: bytes) -> Optional[str]:
    """Try to extract text from protobuf binary payload."""
    if not payload:
        return None

    # Try to find embedded JSON strings
    text = payload.decode('utf-8', errors='ignore')

    # Look for JSON objects
    json_match = re.search(r'\{[^{}]{10,}\}', text)
    if json_match:
        try:
            return json.loads(json_match.group())
        except:
            pass

    # Look for readable text segments
    readable = re.findall(r'[\x20-\x7E]{20,}', text)
    if readable:
        return ' '.join(readable[:3])

    return None


def _extract_json_from_payload(payload: bytes) -> Optional[Dict]:
    """Try to extract JSON from protobuf binary payload."""
    if not payload:
        return None

    text = payload.decode('utf-8', errors='ignore')

    # Look for JSON objects
    json_match = re.search(r'\{[^{}]{20,}(?:\{[^{}]*\}[^{}]*)*\}', text)
    if json_match:
        try:
            return json.loads(json_match.group())
        except:
            pass

    return None


def read_antigravity_session(session: Dict) -> Dict:
    """Read an Antigravity IDE session and return normalized data."""
    db_path = session["db_path"]

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get all steps
    cursor.execute("""
        SELECT idx, step_type, status, has_subtrajectory,
               step_payload, step_format
        FROM steps
        ORDER BY idx
    """)
    steps = cursor.fetchall()

    # Get trajectory metadata blob
    cursor.execute("SELECT id, data FROM trajectory_metadata_blob")
    meta_blobs = cursor.fetchall()

    # Get gen metadata
    cursor.execute("SELECT idx, data FROM gen_metadata")
    gen_meta = cursor.fetchall()

    conn.close()

    entries = []
    total_tokens = 0
    cost = 0.0

    for step in steps:
        idx, step_type, status, has_sub, payload, fmt = step

        # Create entry
        entry = {
            "role": "assistant" if step_type in [14, 15, 23] else "tool",
            "type": step_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata": {
                "status": status,
                "has_subtrajectory": has_sub,
                "format": fmt
            }
        }

        # Try to extract content from payload
        if payload:
            json_data = _extract_json_from_payload(payload)
            if json_data:
                entry["text"] = json.dumps(json_data, indent=2)
                if "CommandLine" in json_data:
                    entry["code"] = json_data["CommandLine"]
                    entry["role"] = "assistant"
                elif "DirectoryPath" in json_data:
                    entry["code"] = f"list_dir({json_data['DirectoryPath']})"
                    entry["role"] = "tool"
            else:
                text = _extract_text_from_payload(payload)
                if text:
                    if isinstance(text, dict):
                        entry["text"] = json.dumps(text)
                    else:
                        entry["text"] = text

        # Add type-specific role mapping
        if step_type == 9:
            entry["role"] = "assistant"  # list_dir
        elif step_type == 21:
            entry["role"] = "assistant"  # run_command
        elif step_type == 98:
            entry["role"] = "assistant"  # Unknown
        elif step_type == 99:
            entry["role"] = "assistant"  # Unknown

        entries.append(entry)

    return {
        "version": "1.0.0",
        "id": session["session_id"],
        "tool": {
            "id": "antigravity",
            "name": "Antigravity IDE",
            "version": "1.0.0"
        },
        "agent": {
            "id": "gemini",
            "name": "Gemini",
            "model": "gemini-2.0-flash"
        },
        "variant": {
            "id": "antigravity",
            "name": "Antigravity IDE",
            "version": "1.0.0"
        },
        "started_at": datetime.now(timezone.utc).isoformat(),
        "ended_at": datetime.now(timezone.utc).isoformat(),
        "entries": entries,
        "metrics": {
            "total_tokens": total_tokens,
            "cost": cost,
            "total_turns": len(entries),
            "total_tool_calls": sum(1 for e in entries if e.get("role") == "tool")
        }
    }


def _step_type_to_role(step_type: int) -> str:
    """Map Antigravity step type to AgentSON role."""
    role_map = {
        9: "assistant",    # list_dir
        14: "assistant",   # Unknown
        15: "assistant",   # Unknown
        21: "assistant",   # run_command
        23: "assistant",   # Unknown
        98: "assistant",   # Unknown
        99: "assistant",   # Unknown
    }
    return role_map.get(step_type, "assistant")


if __name__ == "__main__":
    # Demo: read and print session
    import sys

    sessions = get_antigravity_sessions()
    if not sessions:
        print("No sessions found!")
        sys.exit(1)

    print(f"Found {len(sessions)} session(s)")
    session = sessions[0]
    print(f"\nSession: {session['session_id']}")
    print(f"Total steps: {session['total_steps']}")
    print(f"Step types: {session['step_types']}")
    print(f"DB path: {session['db_path']}")

    data = read_antigravity_session(session)
    print(f"\nEntries: {len(data['entries'])}")
    print(f"First entry: {json.dumps(data['entries'][0], indent=2)[:500]}")
