"""
AgentSON CLI — Export, search, and render agent sessions.
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def get_default_db_paths():
    """Get default database paths for each tool."""
    home = Path.home()
    return {
        "opencode": home / ".local" / "share" / "opencode" / "opencode.db",
        "minimax": home / ".minimax" / "sqlite.db",
        "antigravity": home / ".gemini" / "antigravity-ide" / "conversations"
    }


def cmd_export(args):
    """Export session(s) to AgentSON format."""
    from readers.opencode import read as read_opencode, list_sessions as list_opencode
    from readers.minimax import read as read_minimax, list_sessions as list_minimax
    from readers.antigravity import read_antigravity_session, get_antigravity_sessions
    from readers.libre import read_libre_csv
    
    db_paths = get_default_db_paths()
    
    if args.tool == "opencode":
        db_path = db_paths["opencode"]
        if not db_path.exists():
            print(f"Error: opencode database not found at {db_path}", file=sys.stderr)
            sys.exit(1)
            
        if args.all:
            sessions = list_opencode(str(db_path))
            for session in sessions:
                print(f"Exporting: {session['title']} ({session['id']})")
                data = read_opencode(str(db_path), session["id"])
                output_path = Path(args.output) / f"opencode_{session['id']}.AgentSON"
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            print(f"Exported {len(sessions)} sessions")
        else:
            if not args.session:
                print("Error: --session required when not using --all", file=sys.stderr)
                sys.exit(1)
            data = read_opencode(str(db_path), args.session)
            output_path = Path(args.output) / f"opencode_{args.session}.AgentSON"
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            print(f"Exported to {output_path}")
            
    elif args.tool == "minimax":
        db_path = db_paths["minimax"]
        if not db_path.exists():
            print(f"Error: MiniMax database not found at {db_path}", file=sys.stderr)
            sys.exit(1)
            
        if args.all:
            sessions = list_minimax(str(db_path))
            for session in sessions:
                print(f"Exporting: {session['title']} ({session['id']})")
                data = read_minimax(str(db_path), session["id"])
                output_path = Path(args.output) / f"minimax_{session['id']}.AgentSON"
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            print(f"Exported {len(sessions)} sessions")
        else:
            if not args.session:
                print("Error: --session required when not using --all", file=sys.stderr)
                sys.exit(1)
            data = read_minimax(str(db_path), args.session)
            output_path = Path(args.output) / f"minimax_{args.session}.AgentSON"
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            print(f"Exported to {output_path}")
            
    elif args.tool == "antigravity":
        db_path = db_paths["antigravity"]
        if not db_path.exists():
            print(f"Error: Antigravity IDE directory not found at {db_path}", file=sys.stderr)
            sys.exit(1)
            
        try:
            sessions = get_antigravity_sessions(str(db_path))
        except FileNotFoundError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
            
        if args.all:
            for session in sessions:
                print(f"Exporting: {session['session_id']}")
                data = read_antigravity_session(session)
                output_path = Path(args.output) / f"antigravity_{session['session_id']}.AgentSON"
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            print(f"Exported {len(sessions)} sessions")
        else:
            if not args.session:
                # Export the first session if no ID specified
                if sessions:
                    session = sessions[0]
                    print(f"Exporting: {session['session_id']}")
                    data = read_antigravity_session(session)
                    output_path = Path(args.output) / f"antigravity_{session['session_id']}.AgentSON"
                    with open(output_path, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2, ensure_ascii=False, default=str)
                    print(f"Exported to {output_path}")
                else:
                    print("Error: No sessions found", file=sys.stderr)
                    sys.exit(1)
            else:
                # Find specific session
                found = [s for s in sessions if s['session_id'] == args.session]
                if not found:
                    print(f"Error: Session {args.session} not found", file=sys.stderr)
                    sys.exit(1)
                session = found[0]
                data = read_antigravity_session(session)
                output_path = Path(args.output) / f"antigravity_{args.session}.AgentSON"
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False, default=str)
                print(f"Exported to {output_path}")
    elif args.tool == "libre":
        if not args.input:
            print("Error: --input required for libre tool (path to CSV file)", file=sys.stderr)
            sys.exit(1)
            
        csv_path = args.input
        if not Path(csv_path).exists():
            print(f"Error: CSV file not found at {csv_path}", file=sys.stderr)
            sys.exit(1)
            
        data = read_libre_csv(csv_path)
        output_path = Path(args.output) / f"libre_{Path(csv_path).stem}.AgentSON"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        print(f"Exported to {output_path}")
    else:
        print(f"Error: Unknown tool '{args.tool}'", file=sys.stderr)
        sys.exit(1)


def cmd_list(args):
    """List available sessions."""
    from readers.opencode import list_sessions as list_opencode
    from readers.minimax import list_sessions as list_minimax
    from readers.antigravity import get_antigravity_sessions
    
    db_paths = get_default_db_paths()
    
    if args.tool == "opencode":
        db_path = db_paths["opencode"]
        if not db_path.exists():
            print(f"Error: opencode database not found at {db_path}", file=sys.stderr)
            sys.exit(1)
        sessions = list_opencode(str(db_path), args.limit)
        
    elif args.tool == "minimax":
        db_path = db_paths["minimax"]
        if not db_path.exists():
            print(f"Error: MiniMax database not found at {db_path}", file=sys.stderr)
            sys.exit(1)
        sessions = list_minimax(str(db_path), args.limit)
        
    elif args.tool == "antigravity":
        db_path = db_paths["antigravity"]
        if not db_path.exists():
            print(f"Error: Antigravity IDE directory not found at {db_path}", file=sys.stderr)
            sys.exit(1)
        try:
            sessions = get_antigravity_sessions(str(db_path))
        except FileNotFoundError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print(f"Error: Unknown tool '{args.tool}'", file=sys.stderr)
        sys.exit(1)
        
    print(f"\n{'='*80}")
    print(f"Sessions from {args.tool}")
    print(f"{'='*80}\n")
    
    for s in sessions:
        if args.tool == "antigravity":
            print(f"ID:      {s['session_id']}")
            print(f"Cascade: {s.get('cascade_id', 'N/A')}")
            print(f"Type:    {s.get('trajectory_type', 'N/A')}")
            print(f"Steps:   {s.get('total_steps', 'N/A')}")
        else:
            print(f"ID:      {s['id']}")
            print(f"Title:   {s.get('title', 'N/A')}")
            print(f"Agent:   {s.get('agent', 'N/A')}")
            print(f"Model:   {s.get('model', 'N/A')}")
            print(f"Updated: {s.get('updated', 'N/A')}")
        print()


def cmd_push(args):
    """Push an AgentSON session to Supabase."""
    from cli.supabase_client import AgentSONSupabase

    try:
        client = AgentSONSupabase()
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"Pushing {args.input} to Supabase...")
    result = client.push(data)
    print(f"Pushed! Session ID: {result.get('id', 'unknown')}")


def cmd_pull(args):
    """Pull sessions from Supabase."""
    from cli.supabase_client import AgentSONSupabase

    try:
        client = AgentSONSupabase()
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    sessions = client.pull(
        search=args.search,
        tool=args.tool,
        limit=args.limit
    )

    print(f"\nFound {len(sessions)} session(s)\n")

    for session in sessions:
        session_id = session.get("id", "unknown")
        tool = session.get("tool", {}).get("id", "unknown")
        agent = session.get("agent", {}).get("name", "unknown")

        print(f"ID:    {session_id}")
        print(f"Tool:  {tool}")
        print(f"Agent: {agent}")
        print()

        if args.output:
            output_path = Path(args.output) / f"{tool}_{session_id}.AgentSON"
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(session, f, indent=2, ensure_ascii=False, default=str)
            print(f"Saved to {output_path}")


def cmd_search(args):
    """Search sessions for a term."""
    print(f"Search not yet implemented. Use: agentsong export --all and grep locally.")


def cmd_render(args):
    """Render an AgentSON file to different formats."""
    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    if args.format == "md":
        output = render_markdown(data)
    elif args.format == "html":
        output = render_html(data)
    else:
        print(f"Error: Unknown format '{args.format}'", file=sys.stderr)
        sys.exit(1)
        
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"Rendered to {args.output}")
    else:
        print(output)


def render_markdown(data: dict) -> str:
    """Render AgentSON data as Markdown."""
    lines = []
    lines.append(f"# Agent Session: {data.get('id', 'Unknown')}")
    lines.append("")
    lines.append(f"**Tool:** {data.get('tool', {}).get('name', 'Unknown')}")
    lines.append(f"**Agent:** {data.get('agent', {}).get('name', 'Unknown')}")
    lines.append(f"**Started:** {data.get('started_at', 'Unknown')}")
    lines.append(f"**Ended:** {data.get('ended_at', 'Unknown')}")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    for entry in data.get("entries", []):
        entry_type = entry.get("type")
        
        if entry_type == "user-query":
            lines.append("## User")
            lines.append("")
            lines.append(entry.get("text", entry.get("query", "")))
            lines.append("")
            
        elif entry_type == "thought":
            lines.append("### Thinking")
            lines.append("")
            lines.append(f"> {entry.get('text', '')}")
            lines.append("")
            
        elif entry_type == "action":
            lines.append("### Action")
            lines.append("")
            lines.append(f"**Tool:** {entry.get('tool', 'unknown')}")
            lines.append("")
            if entry.get("code"):
                lines.append("```")
                lines.append(entry["code"])
                lines.append("```")
                lines.append("")
            if entry.get("output"):
                lines.append("**Output:**")
                lines.append("```")
                lines.append(entry["output"])
                lines.append("```")
                lines.append("")
                
        elif entry_type == "answer":
            lines.append("### Answer")
            lines.append("")
            lines.append(entry.get("text", ""))
            lines.append("")
            
        elif entry_type == "side-effect":
            lines.append("### Side Effect")
            lines.append("")
            lines.append(f"**Action:** {entry.get('action', 'unknown')}")
            if entry.get("path"):
                lines.append(f"**Path:** {entry['path']}")
            lines.append("")
    
    lines.append("---")
    lines.append("")
    lines.append(f"*Exported by AgentSON v1*")
    
    return "\n".join(lines)


def render_html(data: dict) -> str:
    """Render AgentSON data as HTML."""
    md = render_markdown(data)
    # Simple HTML wrapping - in production, use a proper markdown parser
    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Agent Session: {data.get('id', 'Unknown')}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; line-height: 1.6; }}
        pre {{ background: #f5f5f5; padding: 12px; border-radius: 4px; overflow-x: auto; }}
        blockquote {{ border-left: 4px solid #ddd; margin: 0; padding: 0 16px; color: #666; }}
        h1, h2, h3 {{ color: #333; }}
        hr {{ border: none; border-top: 1px solid #eee; margin: 20px 0; }}
    </style>
</head>
<body>
<pre>{md}</pre>
</body>
</html>"""


def main():
    parser = argparse.ArgumentParser(
        prog="agentsong",
        description="AgentSON — Export, search, and render agent sessions"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # export command
    export_parser = subparsers.add_parser("export", help="Export sessions to AgentSON format")
    export_parser.add_argument("--tool", required=True, choices=["opencode", "minimax", "antigravity", "chrome-devtools", "libre"])
    export_parser.add_argument("--session", help="Session ID to export")
    export_parser.add_argument("--all", action="store_true", help="Export all sessions")
    export_parser.add_argument("--output", default=".", help="Output directory")
    export_parser.add_argument("--input", help="Input file (required for libre tool)")
    
    # list command
    list_parser = subparsers.add_parser("list", help="List available sessions")
    list_parser.add_argument("--tool", required=True, choices=["opencode", "minimax", "antigravity"])
    list_parser.add_argument("--limit", type=int, default=50, help="Max sessions to list")
    
    # search command
    search_parser = subparsers.add_parser("search", help="Search sessions")
    search_parser.add_argument("--term", required=True, help="Search term")
    search_parser.add_argument("--tool", help="Filter by tool")
    
    # render command
    render_parser = subparsers.add_parser("render", help="Render AgentSON file")
    render_parser.add_argument("input", help="Input AgentSON JSON file")
    render_parser.add_argument("--format", choices=["md", "html"], default="md")
    render_parser.add_argument("--output", help="Output file")

    # push command
    push_parser = subparsers.add_parser("push", help="Push session to Supabase")
    push_parser.add_argument("input", help="Input AgentSON JSON file")

    # pull command
    pull_parser = subparsers.add_parser("pull", help="Pull sessions from Supabase")
    pull_parser.add_argument("--search", help="Full-text search query")
    pull_parser.add_argument("--tool", help="Filter by tool")
    pull_parser.add_argument("--limit", type=int, default=50, help="Max sessions to return")
    pull_parser.add_argument("--output", help="Output directory")
    
    args = parser.parse_args()
    
    if args.command == "export":
        cmd_export(args)
    elif args.command == "list":
        cmd_list(args)
    elif args.command == "search":
        cmd_search(args)
    elif args.command == "render":
        cmd_render(args)
    elif args.command == "push":
        cmd_push(args)
    elif args.command == "pull":
        cmd_pull(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
