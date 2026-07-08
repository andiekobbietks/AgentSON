"""
Auto-export OpenCode sessions to .agentson format.
Run this script periodically to capture new sessions.
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from readers.opencode import list_sessions, read


def export_new_sessions(output_dir: str = "examples"):
    """Export any new or updated OpenCode sessions."""
    from readers.opencode import list_sessions, read
    
    db_path = Path.home() / ".local" / "share" / "opencode" / "opencode.db"
    if not db_path.exists():
        print(f"Error: OpenCode database not found at {db_path}")
        return
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Get list of existing .agentson files
    existing_files = set(f.stem for f in output_path.glob("opencode_*.agentson"))
    
    # Get list of sessions
    sessions = list_sessions(str(db_path), limit=100)
    
    new_count = 0
    updated_count = 0
    
    for session in sessions:
        session_id = session["id"]
        agentson_file = output_path / f"opencode_{session_id}.agentson"
        
        # Check if file exists and if session is newer
        if agentson_file.exists():
            # Skip if file is newer than session update time
            file_mtime = agentson_file.stat().st_mtime * 1000  # Convert to ms
            if file_mtime > session["updated"]:
                continue
            updated_count += 1
        else:
            new_count += 1
        
        # Export session
        try:
            data = read(str(db_path), session_id)
            
            # Redact secrets
            json_str = json.dumps(data, indent=2, ensure_ascii=False, default=str)
            json_str = json_str.replace('ghp_', 'ghp_REDACTED_')
            
            with open(agentson_file, "w", encoding="utf-8") as f:
                f.write(json_str)
            
            print(f"Exported: {session.get('title', session_id)}")
        except Exception as e:
            print(f"Error exporting {session_id}: {e}")
    
    print(f"\nDone: {new_count} new, {updated_count} updated")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Auto-export OpenCode sessions")
    parser.add_argument("--output", default="examples", help="Output directory")
    args = parser.parse_args()
    
    export_new_sessions(args.output)
