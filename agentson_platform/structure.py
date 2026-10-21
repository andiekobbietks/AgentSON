"""AgentSON premium pipeline: structure session streams into graph / lake / CSV.

WHY: the data-collection/structuring work belongs to the tool (user's demand),
for a fee (premium gate). Free core exports JSONL; premium builds graph,
entity table, relation table, audit-log reference, and a training-module
export (TFRecord-style JSONL of entries).

Usage: agentson structure --input . --output ./structure/
Server: GET /api/graph  | POST /api/evidence (ingest GRC package)
"""
from __future__ import annotations
import json, csv, os
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

SCHEMA = "agentson.structure/v1"


def _records(fp: Path):
    """Yield the JSON records of a .agentson JSONL stream (ADR-015, v1.2)."""
    for line in open(fp, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        try:
            yield json.loads(line)
        except ValueError:
            continue


def build_graph(directory: str, limit: int = 500) -> Dict[str, Any]:
    """Build the entity/relation graph from .agentson streams.

    Only relations present in the stream are emitted. The session id comes
    from the stream-meta line; the agent ids come from the meta ``agents``
    list and from entry ``agent`` objects. Nothing is inferred.
    """
    nodes: Dict[str, Dict[str, Any]] = {}
    edges: Dict[str, Dict[str, Any]] = {}

    def add_node(node_id: str, node_type: str, source: str, **extra) -> None:
        if node_id and node_id not in nodes:
            nodes[node_id] = {"id": node_id, "label": node_id, "type": node_type, "source_file": source, **extra}

    def add_edge(src: str, dst: str, relation: str, source: str) -> None:
        if not src or not dst:
            return
        key = f"{src}->{dst}:{relation}"
        if key not in edges:
            edges[key] = {"source": src, "target": dst, "relation": relation, "source_file": source}

    for fp in sorted(Path(directory).glob("*.agentson"))[:limit]:
        session_id = None
        for rec in _records(fp):
            if rec.get("type") == "stream-meta":
                session_id = rec.get("stream_id") or rec.get("source", {}).get("sessionId")
                if session_id:
                    add_node(session_id, "session", fp.name,
                             platform=rec.get("source", {}).get("platform", "unknown"))
                for agent in rec.get("agents", []) or []:
                    if isinstance(agent, dict) and agent.get("id"):
                        add_node(agent["id"], "agent", fp.name,
                                 capabilities=agent.get("capabilities", []))
                        if session_id:
                            add_edge(session_id, agent["id"], "involves", fp.name)
                continue
            agent = rec.get("agent")
            if isinstance(agent, dict) and agent.get("id"):
                add_node(agent["id"], "agent", fp.name, provider=agent.get("provider", "unknown"))
                if session_id:
                    add_edge(session_id, agent["id"], "produced-by", fp.name)
            elif isinstance(agent, str) and agent:
                add_node(agent, "agent", fp.name)
                if session_id:
                    add_edge(session_id, agent, "produced-by", fp.name)
            entry_session = rec.get("session_id")
            if entry_session and entry_session != session_id:
                add_node(entry_session, "session", fp.name)
                if isinstance(agent, dict) and agent.get("id"):
                    add_edge(entry_session, agent["id"], "produced-by", fp.name)

    return {
        "schema": SCHEMA,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "nodes": list(nodes.values()),
        "edges": list(edges.values()),
        "node_count": len(nodes),
        "edge_count": len(edges),
        "source_directory": str(directory),
    }


def build_entities(directory: str, limit: int = 500) -> List[Dict[str, Any]]:
    entities = []
    seen = set()
    for fp in sorted(Path(directory).glob("*.agentson"))[:limit]:
        for line in open(fp, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except Exception:
                continue
            agent = rec.get("agent")
            if isinstance(agent, dict):
                aid = agent.get("id")
                if aid and aid not in seen:
                    seen.add(aid)
                    entities.append({"entity_type": "agent", "id": aid, "provider": agent.get("provider", "unknown"), "capabilities": agent.get("capabilities", []), "source": fp.name})
            sid = rec.get("stream_id") or rec.get("session_id")
            if sid and sid not in seen:
                seen.add(sid)
                entities.append({"entity_type": "session", "id": sid, "tool": rec.get("source", {}).get("platform", "unknown"), "source": fp.name})
    return entities


def build_csv(directory: str, output_dir: str) -> List[str]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    entities = build_entities(directory)
    ent_path = out / "entities.csv"
    with open(ent_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["entity_type", "id", "provider", "capabilities", "source"])
        for e in entities:
            w.writerow([e["entity_type"], e["id"], e.get("provider", ""), ";".join(str(x) for x in e.get("capabilities", [])), e.get("source", "")])
    # Relations from graph
    graph = build_graph(directory)
    rel_path = out / "relations.csv"
    with open(rel_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["source", "target", "relation", "source_file"])
        for e in graph.get("edges", []):
            w.writerow([e.get("source"), e.get("target"), e.get("relation"), e.get("source_file", "")])
    return [str(ent_path), str(rel_path)]


def build_training_export(directory: str, output_dir: str) -> str:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    out_path = out / "training_module.jsonl"
    with open(out_path, "w", encoding="utf-8") as f:
        for fp in sorted(Path(directory).glob("*.agentson")):
            for line in open(fp, encoding="utf-8"):
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except Exception:
                    continue
                if rec.get("type") in ("agent", "user-feedback", "observation", "system-event"):
                    f.write(json.dumps({"type": rec.get("type"), "agent": rec.get("agent"), "text": rec.get("text", ""), "timestamp": rec.get("timestamp")}, ensure_ascii=False) + "\n")
    return str(out_path)
