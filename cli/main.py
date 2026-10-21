"""
AgentSON CLI — Export, search, and render agent sessions.
"""

import argparse
from argparse import RawDescriptionHelpFormatter
import json
import os
import sys
from pathlib import Path
from typing import List
from cli.help_system import WORDMARK, WORDMARK_SON_START, WORDMARK_TAGLINE

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def get_default_db_paths():
    """Get default database paths for each tool."""
    home = Path.home()
    return {
        "opencode": home / ".local" / "share" / "opencode" / "opencode.db",
        "minimax": home / ".minimax" / "sqlite.db",
        "antigravity": home / ".gemini" / "antigravity-ide" / "conversations",
        # VibeEdge stores its chats in Cloudflare Durable Object SQLite under
        # the local wrangler state dir, not in a single database file.
        "vibeedge": home / "vibeedge-studio" / "vibesdk" / ".wrangler",
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
                output_path = Path(args.output) / f"opencode_{session['id']}.agentson"
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            print(f"Exported {len(sessions)} sessions")
        else:
            if not args.session:
                print("Error: --session required when not using --all", file=sys.stderr)
                sys.exit(1)
            data = read_opencode(str(db_path), args.session)
            output_path = Path(args.output) / f"opencode_{args.session}.agentson"
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
                output_path = Path(args.output) / f"minimax_{session['id']}.agentson"
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            print(f"Exported {len(sessions)} sessions")
        else:
            if not args.session:
                print("Error: --session required when not using --all", file=sys.stderr)
                sys.exit(1)
            data = read_minimax(str(db_path), args.session)
            output_path = Path(args.output) / f"minimax_{args.session}.agentson"
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
                output_path = Path(args.output) / f"antigravity_{session['session_id']}.agentson"
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
                    output_path = Path(args.output) / f"antigravity_{session['session_id']}.agentson"
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
                output_path = Path(args.output) / f"antigravity_{args.session}.agentson"
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False, default=str)
                print(f"Exported to {output_path}")
    elif args.tool == "chrome-devtools":
        from readers.chrome_devtools import read as read_chrome, list_exports as list_chrome
        
        if not args.input:
            print("Error: --input required for chrome-devtools tool (path to directory with devtools_*.md files)", file=sys.stderr)
            sys.exit(1)
        
        input_dir = Path(args.input)
        if not input_dir.exists():
            print(f"Error: Directory not found at {input_dir}", file=sys.stderr)
            sys.exit(1)
        
        if args.all:
            sessions = list_chrome(input_dir)
            for session in sessions:
                print(f"Exporting: {session['id']}")
                data = read_chrome(session['path'])
                output_path = Path(args.output) / f"chrome_{session['id']}.agentson"
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            print(f"Exported {len(sessions)} sessions")
        else:
            if not args.session:
                print("Error: --session required when not using --all", file=sys.stderr)
                sys.exit(1)
            data = read_chrome(args.session)
            output_path = Path(args.output) / f"chrome_{args.session}.agentson"
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
        output_path = Path(args.output) / f"libre_{Path(csv_path).stem}.agentson"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        print(f"Exported to {output_path}")
    elif args.tool == "claude-code":
        from readers.claude_code import ClaudeCodeReader

        reader = ClaudeCodeReader()

        if args.all:
            sessions = reader.list_sessions()
            for session in sessions:
                sid = session.get("sessionId", session.get("id", "unknown"))
                print(f"Exporting: {sid}")
                data = reader.read_session(sid)
                if data:
                    output_path = Path(args.output) / f"claude-code_{sid}.agentson"
                    with open(output_path, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            print(f"Exported {len(sessions)} sessions")
        else:
            if not args.session:
                print("Error: --session required when not using --all", file=sys.stderr)
                sys.exit(1)
            data = reader.read_session(args.session)
            if not data:
                print(f"Error: Session {args.session} not found", file=sys.stderr)
                sys.exit(1)
            output_path = Path(args.output) / f"claude-code_{args.session}.agentson"
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            print(f"Exported to {output_path}")
    elif args.tool == "vibeedge":
        from readers.vibeedge import VibeedgeReader

        root = args.input or db_paths["vibeedge"]
        if not Path(root).exists():
            print(f"Error: VibeEdge wrangler state not found at {root}", file=sys.stderr)
            sys.exit(1)

        reader = VibeedgeReader(root)
        try:
            # Create the output dir up front: the other branches assume it
            # exists and fail with FileNotFoundError on a fresh path.
            Path(args.output).mkdir(parents=True, exist_ok=True)
            if args.all:
                sessions = reader.list_sessions()
                if not sessions:
                    print("No VibeEdge sessions found", file=sys.stderr)
                    sys.exit(1)
                for session in sessions:
                    sid = session["id"]
                    print(f"Exporting: {session['backend']}:{sid} "
                          f"({session['messages']} msgs) {session['preview']}")
                    data = reader.read_session(sid)
                    if data:
                        output_path = (Path(args.output) /
                                       f"vibeedge_{sid}.agentson")
                        with open(output_path, "w", encoding="utf-8") as f:
                            json.dump(data, f, indent=2,
                                      ensure_ascii=False, default=str)
                print(f"Exported {len(sessions)} sessions")
            else:
                if not args.session:
                    print("Error: --session required when not using --all",
                          file=sys.stderr)
                    sys.exit(1)
                data = reader.read_session(args.session)
                if not data:
                    print(f"Error: Session {args.session} not found",
                          file=sys.stderr)
                    sys.exit(1)
                output_path = (Path(args.output) /
                               f"vibeedge_{args.session}.agentson")
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False,
                              default=str)
                print(f"Exported to {output_path}")
        finally:
            reader.disconnect()
    else:
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
    elif args.tool == "chrome-devtools":
        from readers.chrome_devtools import list_exports as list_chrome
        
        if not args.input:
            print("Error: --input required for chrome-devtools tool (path to directory)", file=sys.stderr)
            sys.exit(1)
        
        input_dir = Path(args.input)
        if not input_dir.exists():
            print(f"Error: Directory not found at {input_dir}", file=sys.stderr)
            sys.exit(1)
        
        sessions = list_chrome(input_dir)
    elif args.tool == "claude-code":
        from readers.claude_code import ClaudeCodeReader

        reader = ClaudeCodeReader()
        sessions = reader.list_sessions()
    elif args.tool == "vibeedge":
        from readers.vibeedge import VibeedgeReader

        root = args.input or db_paths["vibeedge"]
        if not Path(root).exists():
            print(f"Error: VibeEdge wrangler state not found at {root}", file=sys.stderr)
            sys.exit(1)
        reader = VibeedgeReader(root)
        try:
            sessions = reader.list_sessions(args.limit)
        finally:
            reader.disconnect()
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
        elif args.tool == "claude-code":
            sid = s.get("sessionId", s.get("id", "unknown"))
            print(f"ID:      {sid}")
            print(f"Project: {s.get('project_hash', 'N/A')}")
            print(f"Path:    {s.get('fullPath', s.get('project_path', 'N/A'))}")
            print(f"Msgs:    {s.get('messageCount', 'N/A')}")
        elif args.tool == "vibeedge":
            print(f"ID:      {s['id']}")
            print(f"Backend: {s.get('backend', 'N/A')}")
            print(f"Msgs:    {s.get('messages', 'N/A')}")
            print(f"Span:    {s.get('started', 'N/A')} -> {s.get('ended', 'N/A')}")
            print(f"Preview: {s.get('preview', 'N/A')}")
        else:
            print(f"ID:      {s['id']}")
            print(f"Title:   {s.get('title', 'N/A')}")
            print(f"Agent:   {s.get('agent', 'N/A')}")
            print(f"Model:   {s.get('model', 'N/A')}")
            print(f"Updated: {s.get('updated', 'N/A')}")
        print()


def cmd_search(args):
    """Search AgentSON files for a term."""


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


def cmd_excel(args):
    """Export AgentSON file(s) to Excel with charts and analytics."""
    from exporters.excel import export_to_excel, export_all_to_excel
    
    # Optionally redact PII first
    input_path = args.input
    if args.redact:
        from tools.pii_redactor import PIIRedactor
        redactor = PIIRedactor(use_model=False)
        
        if args.all:
            # Redact all files to temp directory
            import tempfile
            with tempfile.TemporaryDirectory() as tmpdir:
                redact_all(args.input, tmpdir)
                export_all_to_excel(tmpdir, args.output or "exports")
        else:
            # Redact single file to temp
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.agentson', delete=False) as tmp:
                tmp_path = tmp.name
            redactor.redact_file(input_path, tmp_path)
            export_to_excel(tmp_path, args.output)
            import os
            os.unlink(tmp_path)
        return
    
    if args.all:
        export_all_to_excel(input_path, args.output or "exports")
    else:
        export_to_excel(input_path, args.output)


def cmd_redact(args):
    """Redact PII from AgentSON files."""
    from tools.pii_redactor import PIIRedactor, redact_all
    
    if args.all:
        redact_all(args.input, args.output or "examples_redacted")
    else:
        redactor = PIIRedactor(use_model=False)
        output = args.output or args.input
        stats = redactor.redact_file(args.input, output)
        
        print(f"Redacted: {stats['input_file']} -> {stats['output_file']}")
        print(f"Total redactions: {stats['total_redactions']}")
        for pii_type, count in stats["by_type"].items():
            print(f"  - {pii_type}: {count}")


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


def cmd_import(args):
    """Import sessions from external formats."""
    from pathlib import Path
    
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.format == "chatgpt":
        from importers.chatgpt import import_chatgpt
        
        result = import_chatgpt(
            args.input,
            output_path=str(output_dir / f"chatgpt_{Path(args.input).stem}.agentson"),
            all_branches=args.all_branches
        )
    elif args.format == "mcp":
        from importers.mcp import import_mcp
        result = import_mcp(
            args.input,
            output_path=str(output_dir / f"mcp_{Path(args.input).stem}.agentson"),
        )
    elif args.format == "a2a":
        from importers.a2a import import_a2a
        result = import_a2a(
            args.input,
            output_path=str(output_dir / f"a2a_{Path(args.input).stem}.agentson"),
        )
    elif args.format == "agntcy":
        from importers.agntcy import import_agntcy
        result = import_agntcy(
            args.input,
            output_path=str(output_dir / f"agntcy_{Path(args.input).stem}.agentson"),
        )
    else:
        print(f"Error: Unknown import format '{args.format}'", file=sys.stderr)
        sys.exit(1)

    print(f"Imported: {result.get('id', 'unknown')}")
    print(f"  Tool: {result.get('tool', {}).get('name', 'unknown')}")
    print(f"  Entries: {len(result.get('entries', []))}")


def cmd_finetune(args):
    """Export AgentSON session to fine-tuning format."""
    from exporters.finetune import export_training_data
    
    with open(args.input, "r", encoding="utf-8") as f:
        session = json.load(f)
    
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    stem = Path(args.input).stem
    output_path = str(output_dir / f"{stem}_{args.format}.jsonl")
    
    examples = export_training_data(
        session,
        format=args.format,
        output_path=output_path,
        include_thoughts=args.include_thoughts
    )
    
    print(f"Exported {len(examples)} training examples to {output_path}")
    print(f"Format: {args.format}")
    if args.format == "unsloth":
        print("Compatible with: Unsloth, LLaMA-Factory, axolotl")
    elif args.format == "olive":
        print("Compatible with: Microsoft Olive, ONNX Runtime")


def cmd_validate(args):
    """Validate AgentSON file(s) against v1.2 schema."""
    import glob as globmod
    from jsonschema import Draft202012Validator
    
    schema_path = Path(__file__).parent.parent / "spec" / "v1.2.json"
    entries_path = Path(__file__).parent.parent / "spec" / "v1.2-entries.json"
    
    with open(entries_path, "r", encoding="utf-8") as f:
        entry_schema = json.load(f)
    
    entry_validator = Draft202012Validator(entry_schema)
    
    search_dir = Path(args.input)
    
    if search_dir.is_file():
        files = [search_dir]
    else:
        files = []
        for ext in ["*.agentson", "*.AgentSON"]:
            pattern = str(search_dir / "**" / ext)
            files += [Path(p) for p in globmod.glob(pattern, recursive=True)]
    
    if not files:
        print(f"No .agentson files found in {search_dir}")
        return
    
    total = 0
    passed = 0
    failed = 0
    errors_by_type = {}
    
    def validate_entry(entry):
        """Validate a single entry against the flattened entry schema."""
        errors = list(entry_validator.iter_errors(entry))
        return [e.message for e in errors]
    
    for filepath in files:
        total += 1
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read().strip()
            
            lines = [l.strip() for l in content.split("\n") if l.strip()]
            
            # Detect format
            is_jsonl = False
            if len(lines) > 1:
                try:
                    json.loads(lines[0])
                    json.loads(lines[1])
                    is_jsonl = True
                except json.JSONDecodeError:
                    pass
            
            if is_jsonl:
                entries = [json.loads(l) for l in lines]
                
                if entries[0].get("type") != "stream-meta":
                    print(f"  WARN {filepath.name}: First entry is not stream-meta")
                
                entry_errors = []
                for i, entry in enumerate(entries):
                    errors = validate_entry(entry)
                    for msg in errors:
                        entry_errors.append((i + 1, msg))
                
                if entry_errors:
                    print(f"  FAIL {filepath.name}: {len(entry_errors)} validation error(s)")
                    for line_num, msg in entry_errors[:3]:
                        print(f"    Entry {line_num}: {msg[:100]}")
                    if len(entry_errors) > 3:
                        print(f"    ... and {len(entry_errors) - 3} more")
                    failed += 1
                    errors_by_type["schema"] = errors_by_type.get("schema", 0) + 1
                else:
                    print(f"  PASS {filepath.name} ({len(entries)} entries, JSONL)")
                    passed += 1
            else:
                data = json.loads(content)
                
                top_errors = []
                for field in ["id", "tool", "entries"]:
                    if field not in data:
                        top_errors.append(f"Missing required field: {field}")
                
                if top_errors:
                    print(f"  FAIL {filepath.name}: {'; '.join(top_errors)}")
                    failed += 1
                    errors_by_type["schema"] = errors_by_type.get("schema", 0) + 1
                    continue
                
                entries = data.get("entries", [])
                entry_errors = []
                for i, entry in enumerate(entries):
                    errors = validate_entry(entry)
                    for msg in errors:
                        entry_errors.append((i + 1, msg))
                
                if entry_errors:
                    print(f"  FAIL {filepath.name}: {len(entry_errors)} validation error(s)")
                    for line_num, msg in entry_errors[:3]:
                        print(f"    Entry {line_num}: {msg[:100]}")
                    if len(entry_errors) > 3:
                        print(f"    ... and {len(entry_errors) - 3} more")
                    failed += 1
                    errors_by_type["schema"] = errors_by_type.get("schema", 0) + 1
                else:
                    print(f"  PASS {filepath.name} ({len(entries)} entries, JSON)")
                    passed += 1
                    
        except json.JSONDecodeError as e:
            print(f"  FAIL {filepath.name}: Invalid JSON — {e}")
            failed += 1
            errors_by_type["json_parse"] = errors_by_type.get("json_parse", 0) + 1
        except Exception as e:
            print(f"  FAIL {filepath.name}: {e}")
            failed += 1
            errors_by_type["other"] = errors_by_type.get("other", 0) + 1
    
    print(f"\n{'='*60}")
    print(f"Results: {passed}/{total} passed, {failed} failed")
    if errors_by_type:
        print(f"Errors by type: {errors_by_type}")
    
    if failed > 0:
        sys.exit(1)


def cmd_search(args):
    """Search AgentSON files for a term."""
    import glob as globmod
    
    search_dir = Path(args.dir)
    pattern = str(search_dir / "**" / "*.agentson")
    files = globmod.glob(pattern, recursive=True)
    
    if not files:
        print(f"No .agentson files found in {search_dir}")
        return
    
    term = args.term.lower()
    results = []
    
    for filepath in files:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            matches = _search_session(data, term)
            if matches:
                results.append({
                    "file": str(filepath),
                    "session_id": data.get("id", "unknown"),
                    "tool": data.get("tool", {}).get("name", "unknown"),
                    "matches": matches
                })
        except Exception as e:
            print(f"Warning: Could not read {filepath}: {e}", file=sys.stderr)
    
    if not results:
        print(f"No matches for '{args.term}'")
        return
    
    print(f"\nFound {len(results)} file(s) matching '{args.term}':\n")
    
    for result in results:
        print(f"File: {result['file']}")
        print(f"  Session: {result['session_id']}")
        print(f"  Tool: {result['tool']}")
        print(f"  Matches: {len(result['matches'])}")
        for match in result['matches'][:3]:  # Show first 3
            print(f"    - [{match['type']}] {match['text'][:80]}...")
        if len(result['matches']) > 3:
            print(f"    ... and {len(result['matches']) - 3} more")
        print()


def _search_session(data: dict, term: str) -> List[dict]:
    """Search a session for a term."""
    matches = []
    
    for entry in data.get("entries", []):
        text = entry.get("text", "") or entry.get("query", "") or entry.get("code", "") or ""
        if term in text.lower():
            matches.append({
                "type": entry.get("type", "unknown"),
                "text": text[:200]
            })
    
    # Also search title
    title = data.get("title", "")
    if term in title.lower():
        matches.insert(0, {"type": "title", "text": title})
    
    return matches


def cmd_grc_export(args) -> None:
    from cli.licensing import require_premium
    from cli.grc_export import build_evidence, write_evidence
    from cli.barcode import platform_upgrade_url
    from datetime import datetime, timezone
    from pathlib import Path
    import os

    if not require_premium("grc-export"):
        # Print barcode pointing at upgrade when premium absent
        try:
            from cli.barcode import render_text
            print(render_text(platform_upgrade_url()))
        except Exception:
            pass
        return

    digest_path = args.digest
    out = args.output or f"grc_evidence_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
    package = build_evidence(digest_path=digest_path)
    if getattr(args, "secure", False):
        from cli.signing import sign_package
        package = sign_package(package)
    write_evidence(package, out, args.format)
    print(f"GRC evidence exported: {out}  (secure={getattr(args, 'secure', False)})")
    if args.post:
        import urllib.request, time
        data = json.dumps(package).encode("utf-8")
        for attempt in range(1, 4):
            req = urllib.request.Request(
                args.post, data=data,
                headers={"Content-Type": "application/json", "X-AgentSON-Secure": str(getattr(args,"secure",False))},
                method="POST",
            )
            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    print(f"POSTed to {args.post}: HTTP {resp.status} (attempt {attempt})")
                    break
            except Exception as e:
                print(f"POST to {args.post} failed (attempt {attempt}/3): {e}")
                if attempt < 3:
                    time.sleep(2 ** attempt)  # 2s, 4s backoff
            else:
                break


def _display_banner() -> None:
    """The AgentSON ASCII wordmark + version, shown on CLI startup."""
    ver = '0.1.0'
    art_lines = WORDMARK
    # Print art (AgentSON wordmark + PLATFORM subtitle in same larry3d face)
    for line in art_lines:
        print(line)
    # Platform subtitle — same face, baked constant, no pyfiglet at runtime
    try:
        from cli.help_system import WORDMARK_PLATFORM
        for pline in WORDMARK_PLATFORM:
            print(pline)
    except Exception:
        pass
    # Print a clean PLATFORM subtitle in the same larry3d face
    try:
        import pyfiglet
        platform_art = pyfiglet.figlet_format("PLATFORM", font="larry3d")
        for line in platform_art.rstrip().splitlines()[:7]:
            print(line)
    except Exception:
        pass  # pyfiglet not in core dependencies; art baked in when available
    # Print version line
    print(f'-{ver}-')
    # Premium tagline (matches Option A — Enterprise Compliance & Audit)
    print()
    print("  AgentSON Platform  —  Enterprise Compliance & Audit")


def main():
    parser = argparse.ArgumentParser(
        description="""
AgentSON — Universal provenance for agent sessions.

Run 'agentson guide' for the interactive encyclopedia.
Run 'agentson help <topic>' for deep dives on any adapter, reader, or command.
""",
        formatter_class=RawDescriptionHelpFormatter,
        epilog="""
EXPLORE:
  agentson guide             Interactive encyclopedia (TUI)
  agentson help <topic>      Deep dive on any topic (e.g. mcp, a2a, agntcy)
  agentson help --onboard    Re-run first-run onboarding

SCENARIOS:
  1. Validate log streams against canonical v1.2 schema:
     $ agentson validate examples/

  2. Redact PII (emails, API keys) from a directory of logs before sharing:
     $ agentson redact examples/ --output redacted_exports/ --all

  3. Convert structured formats (like Excel) or generate reports:
     $ agentson excel examples/

TOPICS:
  agentson  mcp  a2a  agntcy  chatgpt  opencode
  chrome-devtools  claude-code  libre  validate  redact  publish  runbook
"""
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # export command
    export_parser = subparsers.add_parser("export", help="Export sessions to AgentSON format")
    export_parser.add_argument("--tool", required=True, choices=["opencode", "minimax", "antigravity", "chrome-devtools", "libre", "claude-code", "vibeedge"])
    export_parser.add_argument("--session", help="Session ID to export")
    export_parser.add_argument("--all", action="store_true", help="Export all sessions")
    export_parser.add_argument("--output", default=".", help="Output directory")
    export_parser.add_argument("--input", help="Input file (required for libre tool)")
    
    # import command
    import_parser = subparsers.add_parser("import", help="Import from external formats")
    import_parser.add_argument("format", choices=["chatgpt", "mcp", "a2a", "agntcy"], help="Import format. See 'agentson help <format>' for background.")
    import_parser.add_argument("input", help="Input file path")
    import_parser.add_argument("--output", default=".", help="Output directory")
    import_parser.add_argument("--all-branches", action="store_true", help="Include all conversation branches")
    
    # list command
    list_parser = subparsers.add_parser("list", help="List available sessions")
    list_parser.add_argument("--tool", required=True, choices=["opencode", "minimax", "antigravity", "claude-code", "vibeedge"])
    list_parser.add_argument("--limit", type=int, default=50, help="Max sessions to list")
    # cmd_list reads args.input for chrome-devtools and vibeedge; without this
    # flag the attribute was missing and those branches raised AttributeError.
    list_parser.add_argument("--input", help="Input directory (chrome-devtools exports, vibeedge wrangler state)")
    
    # search command
    search_parser = subparsers.add_parser("search", help="Search AgentSON files")
    search_parser.add_argument("term", help="Search term")
    search_parser.add_argument("--dir", default=".", help="Directory to search")
    
    # finetune command
    finetune_parser = subparsers.add_parser("finetune", help="Export to fine-tuning format")
    finetune_parser.add_argument("input", help="Input AgentSON file")
    finetune_parser.add_argument("--format", choices=["unsloth", "olive"], default="unsloth", help="Training format")
    finetune_parser.add_argument("--output", default=".", help="Output directory")
    finetune_parser.add_argument("--include-thoughts", action="store_true", default=True, help="Include thought entries")
    finetune_parser.add_argument("--no-thoughts", dest="include_thoughts", action="store_false", help="Exclude thought entries")
    
    # render command
    render_parser = subparsers.add_parser("render", help="Render AgentSON file")
    render_parser.add_argument("input", help="Input AgentSON JSON file")
    render_parser.add_argument("--format", choices=["md", "html"], default="md")
    render_parser.add_argument("--output", help="Output file")
    
    # excel command
    excel_parser = subparsers.add_parser("excel", help="Export to Excel with charts and analytics")
    excel_parser.add_argument("input", help="Input .agentson file or directory")
    excel_parser.add_argument("--output", help="Output .xlsx file or directory")
    excel_parser.add_argument("--all", action="store_true", help="Export all .agentson files in directory")
    excel_parser.add_argument("--redact", action="store_true", help="Redact PII before export")
    
    # validate command
    validate_parser = subparsers.add_parser("validate", help="Validate .agentson file(s) against v1.2 schema")
    validate_parser.add_argument("input", help="Input .agentson file or directory")

    # redact command
    redact_parser = subparsers.add_parser("redact", help="Redact PII from AgentSON files")
    redact_parser.add_argument("input", help="Input .agentson file or directory")
    redact_parser.add_argument("--output", help="Output .agentson file or directory")
    redact_parser.add_argument("--all", action="store_true", help="Process all .agentson files in directory")

    # publish command
    publish_parser = subparsers.add_parser("publish", help="Publish AgentSON session to Docker Hub or LXD Hub")
    publish_parser.add_argument("input", help="Input .agentson file")
    publish_parser.add_argument("--registry", choices=["docker", "lxd"], default="docker", help="Target registry")
    publish_parser.add_argument("--tag", help="Image tag or alias (auto-generated if omitted)")
    publish_parser.add_argument("--push", action="store_true", help="Push to remote registry after building")

    # reconstruct command
    recon_parser = subparsers.add_parser("reconstruct", help="Reconstruct session from partial sources with provenance & compliance")
    recon_parser.add_argument("--input", help="Input .agentson file")
    recon_parser.add_argument("--source", dest="sources", action="append", default=[], help="Source file or directory (repeatable)")
    recon_parser.add_argument("--mode", choices=["forensic", "narrative", "live"], default="forensic", help="Reconstruction mode")
    recon_parser.add_argument("--jurisdiction", choices=["eu", "uk", "dual"], default="dual", help="Compliance jurisdiction")
    recon_parser.add_argument("--output", help="Output file")
    recon_parser.add_argument("--format", choices=["json", "jsonl", "summary"], default="json", help="Output format")
    recon_parser.add_argument("--model", help="SLM model for narrative gap-filling")
    recon_parser.add_argument("--temperature", type=float, default=0.3, help="Generation temperature (narrative mode)")
    recon_parser.add_argument("--budget", type=float, default=1.0, help="Epistemic budget (narrative mode)")
    recon_parser.add_argument("--max-gap-ms", type=int, default=300000, help="Max gap before marker (ms)")
    recon_parser.add_argument("--no-ai-act-marks", action="store_true", help="Skip EU AI Act Art. 50(2) marking")
    recon_parser.add_argument("--strict", action="store_true", help="Fail on zero entries or missing sources")

    # browser command (agentson_mcp — chrome-devtools-mcp via mcp-use)
    browser_parser = subparsers.add_parser(
        "browser", help="NOT IMPLEMENTED — planned MCP capture (agentson_mcp, see ADR-022)"
    )
    browser_sub = browser_parser.add_subparsers(dest="browser_command", help="Browser sub-command")
    grab_p = browser_sub.add_parser("grab", help="NOT IMPLEMENTED — navigate to a URL and capture page state")
    grab_p.add_argument("--url", required=True, help="URL to navigate to")
    grab_p.add_argument("--out", help="Output .md path (default: ./devtools_<slug>.md)")
    grab_p.add_argument("--attach", help="Attach to existing Chrome at this URL (e.g. http://127.0.0.1:9222)")
    grab_p.add_argument("--no-headless", action="store_true", help="Run Chrome with a visible window")
    tabs_p = browser_sub.add_parser("tabs", help="NOT IMPLEMENTED — list open browser tabs")
    tabs_p.add_argument("--attach", help="Attach to existing Chrome at this URL")
    tools_p = browser_sub.add_parser("list-tools", help="NOT IMPLEMENTED — list MCP server tools")
    tools_p.add_argument("--attach", help="Attach to existing Chrome at this URL")

    # grc-export command (premium — GRC evidence package)
    grc_parser = subparsers.add_parser("grc-export", help="Export GRC evidence package (AgentSON Platform)")
    grc_parser.add_argument("--digest", help="Path to report.json or digest JSON")
    grc_parser.add_argument("--output", help="Output evidence JSON (default: grc_evidence_<timestamp>.json)")
    grc_parser.add_argument("--format", choices=["json"], default="json")
    grc_parser.add_argument("--post", help="POST URL for platform ingestion (optional)")
    grc_parser.add_argument("--secure", action="store_true", help="Sign the evidence package with a local ECDSA P-256 key (premium)")

    # platform command (Data Rights Intelligence Platform)
    platform_parser = subparsers.add_parser("platform", help="Data Rights Intelligence Platform — scan, analyze, report")
    platform_sub = platform_parser.add_subparsers(dest="platform_command", help="Platform sub-command")
    scan_p = platform_sub.add_parser("scan", help="Detect tools, crawl sessions, analyze, write report")
    scan_p.add_argument("--output", help="Base output directory")
    scan_p.add_argument("--tool", action="append", dest="tools", help="Only scan this tool (repeatable)")
    scan_p.add_argument("--slm", action="store_true", help="Try to use a local SLM for classification")
    scan_p.add_argument("--model", help="SLM model name")
    detect_p = platform_sub.add_parser("detect", help="List installed AI tools and their data locations")
    serve_p = platform_sub.add_parser("serve", help="Local preview server (AgentSON Platform dashboard)")
    serve_p.add_argument("--port", type=int, default=8080, help="Port")
    serve_p.add_argument("--scan-dir", help="Scan folder with report.json (default: latest found)")
    license_p = platform_sub.add_parser("license", help="Generate a local dev licence key (premium test only)")
    license_p.add_argument("--dev", action="store_true", help="Write a dev licence covering all premium features")

    # watch command (adoption monitor — forks, stars, watchers, clone trend)
    from cli.watch import build_parser as build_watch_parser
    build_watch_parser(subparsers)

    # help / guide command (encyclopedia)
    for name in ("help", "guide"):
        hp = subparsers.add_parser(name, help="Show interactive encyclopedia or topic deep-dive")
        hp.add_argument("topic", nargs="?", default=None, help="Topic to explore (e.g. mcp, a2a, validate)")
        hp.add_argument("--onboard", action="store_true", help="Re-run first-run onboarding")

    _display_banner()
    args = parser.parse_args()
    
    if args.command == "export":
        cmd_export(args)
    elif args.command == "import":
        cmd_import(args)
    elif args.command == "list":
        cmd_list(args)
    elif args.command == "search":
        cmd_search(args)
    elif args.command == "finetune":
        cmd_finetune(args)
    elif args.command == "render":
        cmd_render(args)
    elif args.command == "excel":
        cmd_excel(args)
    elif args.command == "validate":
        cmd_validate(args)
    elif args.command == "redact":
        cmd_redact(args)
    elif args.command == "publish":
        cmd_publish(args)
    elif args.command == "reconstruct":
        from cli.reconstruct import cmd_reconstruct
        cmd_reconstruct(args)
    elif args.command == "browser":
        cmd_browser(args)
    elif args.command == "watch":
        from cli.watch import cmd_watch
        cmd_watch(args)
    elif args.command == "grc-export":
        cmd_grc_export(args)
    elif args.command == "platform":
        if args.platform_command == "scan":
            from agentson_platform.scan import run_scan
            run_scan(
                output_dir=args.output,
                tool_filter=args.tools,
                use_slm=args.slm,
                slm_model=args.model,
            )
        elif args.platform_command == "detect":
            from agentson_platform.tool_registry import detect_all
            import json as _json
            print(_json.dumps(detect_all(), indent=2))
        elif args.platform_command == "serve":
            from agentson_platform.server import serve
            serve(port=args.port, scan_dir=args.scan_dir)
        elif args.platform_command == "license":
            if args.dev:
                import json
                from cli.licensing import LICENSE_PATH
                lic = {"tier":"platform","features":["grc-export","structure","audit-log"],"revoked":False,"dev":True}
                LICENSE_PATH.parent.mkdir(parents=True, exist_ok=True)
                LICENSE_PATH.write_text(json.dumps(lic, indent=2), encoding="utf-8")
                print("Dev licence written:", LICENSE_PATH)
                print("Features:", lic["features"])
            else:
                print("Usage: agentson platform license --dev")
        else:
            print("Usage: agentson platform <scan|detect|serve|license>")
            print("  serve   --port 8080  [--scan-dir DIR]  (local preview server)")
            print("  license --dev                          (write local dev licence)")
    elif args.command in ("help", "guide"):
        from cli.help_system import show_help_page, show_encyclopedia, show_onboarding, mark_onboarded
        if args.onboard:
            show_onboarding()
            mark_onboarded()
        elif args.topic:
            show_help_page(args.topic)
        else:
            show_encyclopedia()
    else:
        try:
            from cli.help_system import show_encyclopedia
            show_encyclopedia()
        except ImportError:
            parser.print_help()


def cmd_browser(args):
    """Browser capture -- NOT IMPLEMENTED.

    The original design (ADR-022/023) drove chrome-devtools-mcp via a
    companion package `agentson_mcp` providing MCPBrowser and
    AIModeExporter. That package was never written: it is listed in
    pyproject packaging includes but does not exist in this repo or in
    site-packages, so this command has always raised ImportError.

    The planned replacement is `agentson capture`, which reads each
    vendor's own conversation API using the user's own session token
    rather than rendering the page. DOM capture loses the tool
    invocations that the API retains -- see the SaveAI adapter survey.
    """
    try:
        from agentson_mcp.client import MCPBrowser  # noqa: F401
    except ImportError:
        print(
            "Error: `agentson browser` is not implemented.\n"
            "\n"
            "  The CLI imports `agentson_mcp.client.MCPBrowser`, which does\n"
            "  not exist in this repository. See ADR-022 / ADR-023.\n"
            "\n"
            "  Not implemented: grab, tabs, list-tools.\n"
            "\n"
            "  Planned replacement: `agentson capture` (vendor API capture).\n"
            "  Until then use a reader:  agentson export --tool <name>",
            file=sys.stderr,
        )
        sys.exit(1)


def cmd_publish(args):
    """Publish AgentSON session to Docker Hub or LXD Hub."""
    from tools.distribute import publish

    result = publish(
        session_path=args.input,
        registry=args.registry,
        tag=args.tag,
        push=args.push,
    )

    if result.get("success"):
        print(f"Published: {result.get('tag') or result.get('alias', 'unknown')}")
        print(f"  Session: {result.get('session_id', 'unknown')}")
        if result.get("pushed"):
            print(f"  Pushed: yes")
    else:
        print(f"Error: {result.get('error', 'unknown')}")
        if result.get("step"):
            print(f"  Step: {result['step']}")
        sys.exit(1)


if __name__ == "__main__":
    main()
