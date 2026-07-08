"""AgentSON export CLI.

Single entry point for converting any AI-tool session into an `.agentson`
JSON document. Supports opencode, Mavis/MiniMax, claude-code, antigravity,
copilot, and any future reader that lives in `readers/`.

Usage
-----
    agentson export opencode <session_id>  [--db PATH] [--out PATH]
    agentson export minimax <session_id>   [--db PATH] [--out PATH]
    agentson list   minimax                [--db PATH] [--limit N]
    agentson list   opencode               [--db PATH] [--limit N]
    agentson import <input.agentson>       [--into {supabase,oci-autonomous}]
    agentson info   <input.agentson>

Default DB locations (Windows):
    opencode : %LOCALAPPDATA%\\..\\..\\.local\\share\\opencode\\opencode.db
               (i.e. C:\\Users\\<user>\\.local\\share\\opencode\\opencode.db)
    minimax  : %USERPROFILE%\\.mavis\\sqlite.db
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# Default DB locations — overridable via CLI / env
DEFAULT_OPENCODE_DB = Path.home() / ".local" / "share" / "opencode" / "opencode.db"
DEFAULT_MINIMAX_DB = Path.home() / ".mavis" / "sqlite.db"
DEFAULT_OUT_DIR = Path(__file__).resolve().parent / "examples"


def _resolve_db(tool: str, override: Optional[str]) -> Path:
    if override:
        return Path(override)
    if tool == "opencode":
        return DEFAULT_OPENCODE_DB
    if tool == "minimax":
        return DEFAULT_MINIMAX_DB
    raise SystemExit(f"unknown tool: {tool}")


def _default_out(tool: str, session_id: str) -> Path:
    safe_id = "".join(c if c.isalnum() or c in "-_" else "_" for c in session_id)
    return DEFAULT_OUT_DIR / f"session_{tool}_{safe_id}.agentson"


def cmd_export(args) -> int:
    db = _resolve_db(args.tool, args.db)
    if not db.exists():
        raise SystemExit(f"database not found: {db}")

    if args.tool == "opencode":
        from readers.opencode import read
    elif args.tool == "minimax":
        from readers.minimax import read
    else:
        raise SystemExit(f"reader not implemented for tool: {args.tool}")

    agentson = read(str(db), args.session_id)

    out = Path(args.out) if args.out else _default_out(args.tool, args.session_id)
    out.parent.mkdir(parents=True, exist_ok=True)

    # Enrich if requested (adds provenance, tool metadata etc.)
    if args.enrich:
        agentson = enrich(agentson)

    with out.open("w", encoding="utf-8") as f:
        json.dump(agentson, f, indent=2, ensure_ascii=False)

    entries = len(agentson.get("entries", []))
    print(f"OK  wrote {out}  ({entries} entries)")
    print(f"    tool={agentson['tool']['name']} session={agentson['id']}")
    print(f"    started_at={agentson.get('started_at')}  heartbeat={agentson.get('heartbeat')}")
    return 0


def cmd_list(args) -> int:
    db = _resolve_db(args.tool, args.db)
    if not db.exists():
        raise SystemExit(f"database not found: {db}")

    if args.tool == "opencode":
        from readers.opencode import list_sessions
    elif args.tool == "minimax":
        from readers.minimax import list_sessions
    else:
        raise SystemExit(f"reader not implemented for tool: {args.tool}")

    rows = list_sessions(str(db), limit=args.limit)
    for r in rows:
        title = (r.get("title") or "").strip()[:80]
        print(f"  {r['id']}  {r.get('status','?'):>8}  {title}")
    print(f"\n  ({len(rows)} sessions)")
    return 0


def cmd_info(args) -> int:
    path = Path(args.input)
    if not path.exists():
        raise SystemExit(f"file not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        doc = json.load(f)
    tool = doc.get("tool", {}).get("name", "?")
    sid = doc.get("id", "?")
    entries = len(doc.get("entries", []))
    by_type = doc.get("digest", {}).get("by_type", {})
    md = doc.get("metadata", {})
    print(f"  {path}")
    print(f"  tool           {tool}")
    print(f"  session        {sid}")
    print(f"  entries        {entries}  ({', '.join(f'{k}={v}' for k,v in by_type.items())})")
    print(f"  started_at     {doc.get('started_at')}")
    print(f"  heartbeat      {doc.get('heartbeat')}")
    print(f"  outcome        {doc.get('outcome')}")
    print(f"  total_tokens   {md.get('total_tokens')}")
    print(f"  cost           {md.get('cost')}")
    return 0


def cmd_import(args) -> int:
    """Dump a `.agentson` file to a SQL script (Postgres / Autonomous) or
    Supabase seed JSON. Used to re-import portable session data into a
    managed database so tools like Oracle APEX can read it."""
    path = Path(args.input)
    if not path.exists():
        raise SystemExit(f"file not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        doc = json.load(f)

    target = args.into
    if target == "supabase":
        out = path.with_suffix(".supabase.json")
        with out.open("w", encoding="utf-8") as f:
            json.dump(_to_supabase_seed(doc), f, indent=2, ensure_ascii=False)
        print(f"OK  wrote Supabase seed: {out}")
    elif target == "oci-autonomous":
        out = path.with_suffix(".sql")
        with out.open("w", encoding="utf-8") as f:
            f.write(_to_oracle_sql(doc))
        print(f"OK  wrote Oracle SQL: {out}")
    else:
        raise SystemExit(f"unknown --into target: {target}")
    return 0


# ---------- enrichment / enrichment for cross-tool portability ----------

def enrich(doc: dict) -> dict:
    """Cross-tool enrichment: ensures every entry has full provenance,
    EU AI Act Art. 50 transparency marking, and a `_enrichment` block
    listing which tool originally produced the entry.

    Used when a downstream consumer (Claude Code, Codex CLI, Mavis) needs
    to render the document regardless of which upstream tool wrote it.
    """
    tool_name = doc.get("tool", {}).get("name", "unknown")
    enriched_entries = []
    for e in doc.get("entries", []):
        # Already has provenance? Leave it.
        e.setdefault("provenance", {})
        e["provenance"].setdefault("source", _default_source(e.get("type")))
        e["provenance"].setdefault("confidence", "inferred")
        e["provenance"].setdefault("timestamp_ms", e.get("timestamp"))

        # AI Act Art. 50 transparency marking
        e.setdefault("_transparency", {})
        e["_transparency"].setdefault("ai_generated",
                                      e.get("type") in ("answer", "thought", "action"))
        e["_transparency"].setdefault("marking_scheme", "agentson-v1.2")
        e["_transparency"].setdefault("detectable", True)

        # Tool-of-origin marker — every entry knows who wrote it
        e["_origin"] = {"tool": tool_name, "schema_version": "1.2"}

        enriched_entries.append(e)
    doc["entries"] = enriched_entries

    # Top-level tool chain so consumers can render the doc accurately
    doc.setdefault("tool_chain", []).append(
        {"tool": tool_name, "exported_at": doc.get("metadata", {}).get("exported_at")}
    )

    # Recompute digest
    by_type: dict = {}
    by_conf: dict = {}
    for e in enriched_entries:
        by_type[e["type"]] = by_type.get(e["type"], 0) + 1
        c = (e.get("provenance") or {}).get("confidence", "unknown")
        by_conf[c] = by_conf.get(c, 0) + 1
    doc.setdefault("digest", {})
    doc["digest"].update(
        total_entries=len(enriched_entries),
        by_type=by_type,
        by_confidence=by_conf,
        has_gaps=False,
    )

    doc.setdefault("compliance", {})
    doc["compliance"].setdefault("jurisdiction", "uk")
    doc["compliance"].setdefault(
        "bases",
        ["uk_gdpr_art_20_portability", "uk_duaa_recognised_legitimate_interests"],
    )
    doc["compliance"]["generated_at"] = datetime.now(timezone.utc).isoformat()
    doc["compliance"].setdefault("schema_version", "1.2")

    return doc


def _default_source(entry_type: str) -> str:
    return {
        "stream-meta": "system",
        "user-query": "user",
        "answer": "other",
        "thought": "other",
        "action": "mcp",
        "observation": "mcp",
        "system-event": "system",
        "side-effect": "system",
        "handoff": "system",
        "presence": "system",
        "capabilities": "system",
        "user-feedback": "user",
    }.get(entry_type, "other")


def _to_supabase_seed(doc: dict) -> dict:
    """Map an .agentson document to a Supabase row payload (sessions + entries)."""
    base = doc.get("metadata", {}).copy()
    base["id"] = doc["id"]
    base["tool"] = doc.get("tool", {}).get("name")
    base["tool_version"] = doc.get("tool", {}).get("version")
    base["tool_session_id"] = doc.get("tool", {}).get("session_id")
    base["agent_name"] = doc.get("agent", {}).get("name")
    base["agent_provider"] = doc.get("agent", {}).get("provider")
    base["agent_variant"] = doc.get("agent", {}).get("variant")
    base["task"] = doc.get("task")
    base["outcome"] = doc.get("outcome")
    base["started_at"] = doc.get("started_at")
    base["ended_at"] = doc.get("ended_at")
    base["heartbeat"] = doc.get("heartbeat")
    base["working_directory"] = (doc.get("context") or {}).get("working_directory")
    base["platform"] = (doc.get("context") or {}).get("platform")
    base["compliance"] = doc.get("compliance")
    base["tool_chain"] = doc.get("tool_chain")
    return {
        "tables": {
            "agentson_sessions": [base],
            "agentson_entries": [
                {"session_id": doc["id"], **e} for e in doc.get("entries", [])
            ],
        }
    }


def _to_oracle_sql(doc: dict) -> str:
    """Produce a portable Oracle SQL*Plus script for the same data — runs on
    Oracle Autonomous (ATP / ADW) so APEX apps can join on session_id."""
    sid = doc["id"].replace("'", "''")
    title = (doc.get("task") or "").replace("'", "''")
    out = []
    out.append("-- Generated by agentson CLI — re-importable into Oracle Autonomous")
    out.append("BEGIN")
    out.append("  EXECUTE IMMEDIATE 'CREATE TABLE agentson_sessions (")
    out.append("    id VARCHAR2(128) PRIMARY KEY,")
    out.append("    tool VARCHAR2(64), tool_version VARCHAR2(64),")
    out.append("    tool_session_id VARCHAR2(128),")
    out.append("    agent_name VARCHAR2(128), agent_provider VARCHAR2(64),")
    out.append("    agent_variant VARCHAR2(64),")
    out.append("    title VARCHAR2(1024), outcome VARCHAR2(64),")
    out.append("    started_at TIMESTAMP WITH TIME ZONE, ended_at TIMESTAMP WITH TIME ZONE,")
    out.append("    heartbeat TIMESTAMP WITH TIME ZONE,")
    out.append("    working_directory VARCHAR2(1024), platform VARCHAR2(64)")
    out.append("  )';")
    out.append("  EXECUTE IMMEDIATE 'CREATE TABLE agentson_entries (")
    out.append("    session_id VARCHAR2(128),")
    out.append("    entry_type VARCHAR2(64),")
    out.append("    ts TIMESTAMP WITH TIME ZONE,")
    out.append("    agent VARCHAR2(64),")
    out.append("    text CLOB,")
    out.append("    payload JSON")
    out.append("  )';")
    out.append("END;")
    out.append("/")
    out.append("")
    out.append(
        f"INSERT INTO agentson_sessions (id, tool, tool_version, tool_session_id, "
        f"agent_name, agent_provider, agent_variant, title, outcome, started_at, "
        f"ended_at, heartbeat, working_directory, platform) VALUES ("
        f"'{sid}', "
        f"'{doc.get('tool',{}).get('name','')}', "
        f"'{doc.get('tool',{}).get('version','')}', "
        f"'{doc.get('tool',{}).get('session_id','')}', "
        f"'{doc.get('agent',{}).get('name','')}', "
        f"'{doc.get('agent',{}).get('provider','')}', "
        f"'{doc.get('agent',{}).get('variant','')}', "
        f"'{title}', "
        f"'{doc.get('outcome','')}', "
        f"TIMESTAMP '{doc.get('started_at','')}', "
        f"TIMESTAMP '{doc.get('ended_at','')}', "
        f"TIMESTAMP '{doc.get('heartbeat','')}', "
        f"'{(doc.get('context') or {}).get('working_directory','').replace(chr(39),chr(39)+chr(39))}', "
        f"'{(doc.get('context') or {}).get('platform','')}'"
        f");"
    )
    for e in doc.get("entries", []):
        et = (e.get("type") or "").replace("'", "''")
        ag = (e.get("agent") or "").replace("'", "''")
        tx = (e.get("text") or "").replace("'", "''")[:2000]
        ts = e.get("timestamp")
        ts_sql = f"TIMESTAMP '{datetime.fromtimestamp(ts/1000, tz=timezone.utc).isoformat()}'" if ts else "NULL"
        payload_json = json.dumps({k: v for k, v in e.items() if k != "text"}).replace("'", "''")
        out.append(
            f"INSERT INTO agentson_entries (session_id, entry_type, ts, agent, text, payload) VALUES ("
            f"'{sid}', '{et}', {ts_sql}, '{ag}', '{tx}', '{payload_json}');"
        )
    return "\n".join(out) + "\n"


# ---------- main ----------

def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="agentson", description="AgentSON export CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    pe = sub.add_parser("export", help="Export a session to .agentson")
    pe.add_argument("tool", choices=["opencode", "minimax", "claude-code", "antigravity", "copilot"])
    pe.add_argument("session_id")
    pe.add_argument("--db", help="Path to source DB (default per tool)")
    pe.add_argument("--out", help="Output .agentson file (default: examples/session_<tool>_<id>.agentson)")
    pe.add_argument("--enrich", action="store_true",
                    help="Apply cross-tool enrichment (provenance + AI Act marking)")
    pe.add_argument("--register", metavar="WORKSPACE_KEY",
                    help="Also register the export under WORKSPACE_KEY in the cross-tool registry")
    pe.set_defaults(func=cmd_export)

    pl = sub.add_parser("list", help="List available sessions in a tool's DB")
    pl.add_argument("tool", choices=["opencode", "minimax", "claude-code", "antigravity", "copilot"])
    pl.add_argument("--db", help="Path to source DB (default per tool)")
    pl.add_argument("--limit", type=int, default=20)
    pl.set_defaults(func=cmd_list)

    pi = sub.add_parser("info", help="Print summary of an .agentson file")
    pi.add_argument("input")
    pi.set_defaults(func=cmd_info)

    pimp = sub.add_parser("import", help="Re-export .agentson into a managed DB target")
    pimp.add_argument("input")
    pimp.add_argument("--into", choices=["supabase", "oci-autonomous"], required=True)
    pimp.set_defaults(func=cmd_import)

    # Delegate account / workspace / resume to the dedicated module
    sub.add_parser("account", help="Manage tool accounts (Mavis-profile style)").set_defaults(
        func=_delegate_account
    )
    sub.add_parser("workspace", help="Manage workspaces (= projects)").set_defaults(
        func=_delegate_workspace
    )
    sub.add_parser("resume", help="Find latest .agentson for a workspace").set_defaults(
        func=_delegate_resume
    )

    args = p.parse_args(argv)
    if hasattr(args, "func"):
        return args.func(args)
    p.print_help()
    return 0


def _delegate_account(_args):
    import agentson_account
    return agentson_account.main(["account"])


def _delegate_workspace(_args):
    import agentson_account
    return agentson_account.main(["workspace"])


def _delegate_resume(args):
    import agentson_account
    return agentson_account.main(["resume", args.workspace or "default"])


if __name__ == "__main__":
    sys.exit(main())