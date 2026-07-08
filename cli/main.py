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
    if args.format == "chatgpt":
        from importers.chatgpt import import_chatgpt
        
        output_dir = Path(args.output)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        result = import_chatgpt(
            args.input,
            output_path=str(output_dir / f"chatgpt_{Path(args.input).stem}.agentson"),
            all_branches=args.all_branches
        )
        print(f"Imported: {result.get('id', 'unknown')}")
        print(f"  Tool: {result.get('tool', {}).get('name', 'unknown')}")
        print(f"  Entries: {len(result.get('entries', []))}")
    else:
        print(f"Error: Unknown import format '{args.format}'", file=sys.stderr)
        sys.exit(1)


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


def main():
    parser = argparse.ArgumentParser(
        description="""
  ┌─┐┌─┐┌─┐┌┐┌┌┬┐┌─┐┌─┐┌┐┌   ┌─┐┬  ┬
  ├─┤│ ┬├┤ │││ │ └─┐│ ││││   │  │  │
  ┴ ┴└─┘└─┘┘└┘ ┴ └─┘└─┘┘└┘   └─┘┴─┘┴

Universal cross-vendor observation, provenance, and replay format for 
agent sessions sitting above MCP, CDP, and browser protocols.
""",
        formatter_class=RawDescriptionHelpFormatter,
        epilog="""
COMMON SCENARIOS:
  1. Validate log streams against canonical v1.2 schema:
     $ agentson validate examples/

  2. Redact PII (emails, API keys) from a directory of logs before sharing:
     $ agentson redact examples/ --output redacted_exports/ --all

  3. Convert structured formats (like Excel) or generate reports:
     $ agentson excel examples/
"""
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # export command
    export_parser = subparsers.add_parser("export", help="Export sessions to AgentSON format")
    export_parser.add_argument("--tool", required=True, choices=["opencode", "minimax", "antigravity", "chrome-devtools", "libre"])
    export_parser.add_argument("--session", help="Session ID to export")
    export_parser.add_argument("--all", action="store_true", help="Export all sessions")
    export_parser.add_argument("--output", default=".", help="Output directory")
    export_parser.add_argument("--input", help="Input file (required for libre tool)")
    
    # import command
    import_parser = subparsers.add_parser("import", help="Import from external formats")
    import_parser.add_argument("format", choices=["chatgpt"], help="Import format")
    import_parser.add_argument("input", help="Input file path")
    import_parser.add_argument("--output", default=".", help="Output directory")
    import_parser.add_argument("--all-branches", action="store_true", help="Include all conversation branches")
    
    # list command
    list_parser = subparsers.add_parser("list", help="List available sessions")
    list_parser.add_argument("--tool", required=True, choices=["opencode", "minimax", "antigravity"])
    list_parser.add_argument("--limit", type=int, default=50, help="Max sessions to list")
    
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
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
