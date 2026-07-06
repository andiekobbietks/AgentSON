"""
ChatGPT Importer for AgentSON.

Converts ChatGPT conversation exports (conversations.json) into AgentSON format.
ChatGPT exports use a tree structure with mapping nodes.
"""

import json
from datetime import datetime
from typing import Dict, List, Optional
import uuid


def import_chatgpt(
    export_path: str,
    output_path: Optional[str] = None,
    session_id: Optional[str] = None,
    all_branches: bool = False
) -> dict:
    """
    Import a ChatGPT conversation export into AgentSON format.
    
    Args:
        export_path: Path to conversations.json from ChatGPT export
        output_path: Optional path to write .agentson file
        session_id: Optional custom session ID
        all_branches: If True, include all branches; if False, follow main path
    
    Returns:
        AgentSON session dict
    """
    with open(export_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Handle both single conversation and array of conversations
    if isinstance(data, list):
        conversations = data
    elif isinstance(data, dict) and "conversations" in data:
        conversations = data["conversations"]
    else:
        conversations = [data]
    
    # Import first conversation (or could iterate)
    if not conversations:
        raise ValueError("No conversations found in export")
    
    conv = conversations[0]
    return _convert_conversation(
        conv, output_path, session_id, all_branches
    )


def _convert_conversation(
    conv: dict,
    output_path: Optional[str] = None,
    session_id: Optional[str] = None,
    all_branches: bool = False
) -> dict:
    """Convert a single ChatGPT conversation to AgentSON format."""
    
    title = conv.get("title", "Untitled Conversation")
    conv_id = conv.get("id", str(uuid.uuid4()))
    
    # Use provided session ID or generate from ChatGPT ID
    if session_id is None:
        session_id = f"chatgpt-{conv_id}"
    
    # Parse timestamps
    create_time = conv.get("create_time")
    update_time = conv.get("update_time")
    
    started_at = _timestamp_to_iso(create_time) if create_time else None
    ended_at = _timestamp_to_iso(update_time) if update_time else None
    
    # Extract entries from mapping
    mapping = conv.get("mapping", {})
    entries = _extract_entries(mapping, all_branches)
    
    # Determine model from messages
    model = _detect_model(mapping)
    
    # Build AgentSON document
    agentson = {
        "$schema": "https://agentson.dev/schema/v1.json",
        "id": session_id,
        "tool": {
            "name": "chatgpt",
            "version": "export",
            "session_id": conv_id
        },
        "agent": {
            "name": model,
            "provider": "openai",
            "variant": "default"
        },
        "started_at": started_at,
        "ended_at": ended_at,
        "context": {
            "working_directory": "",
            "platform": "web",
            "shell": "browser"
        },
        "title": title,
        "entries": entries,
        "metadata": {
            "total_tokens": 0,
            "cost": 0.0,
            "messages": len([e for e in entries if e["type"] in ("user-query", "answer")]),
            "parts": len(entries),
            "exported_at": datetime.utcnow().isoformat() + "Z",
            "source_format": "chatgpt-export"
        }
    }
    
    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(agentson, f, indent=2, ensure_ascii=False, default=str)

    return agentson


def _extract_entries(mapping: dict, all_branches: bool = False) -> List[dict]:
    """Extract entries from ChatGPT mapping tree."""
    entries = []
    
    if not mapping:
        return entries
    
    # Find root node
    root_id = None
    for node_id, node in mapping.items():
        if node.get("parent") is None:
            root_id = node_id
            break
    
    if root_id is None:
        # Try to find any node without parent
        for node_id, node in mapping.items():
            if node.get("parent") not in mapping:
                root_id = node_id
                break
    
    if root_id is None:
        return entries
    
    # Walk the tree
    visited = set()
    _walk_tree(mapping, root_id, entries, visited, all_branches)
    
    return entries


def _walk_tree(
    mapping: dict,
    node_id: str,
    entries: List[dict],
    visited: set,
    all_branches: bool
):
    """Recursively walk the ChatGPT mapping tree."""
    if node_id in visited:
        return
    
    visited.add(node_id)
    node = mapping.get(node_id, {})
    message = node.get("message")
    
    if message:
        entry = _message_to_entry(message)
        if entry:
            entries.append(entry)
    
    # Process children
    children = node.get("children", [])
    if all_branches:
        for child_id in children:
            _walk_tree(mapping, child_id, entries, visited, all_branches)
    elif children:
        # Follow first child (main path)
        _walk_tree(mapping, children[0], entries, visited, all_branches)


def _message_to_entry(message: dict) -> Optional[dict]:
    """Convert a ChatGPT message to an AgentSON entry."""
    role = message.get("author", {}).get("role", "unknown")
    content = message.get("content", {})
    
    # Skip system messages
    if role == "system":
        return None
    
    # Extract text content
    parts = content.get("parts", [])
    text_parts = []
    for part in parts:
        if isinstance(part, str):
            text_parts.append(part)
        elif isinstance(part, dict) and "text" in part:
            text_parts.append(part["text"])
    
    text = "\n".join(text_parts).strip()
    if not text:
        return None
    
    # Detect model from metadata
    metadata = message.get("metadata", {})
    model_slug = metadata.get("model_slug", "")
    
    timestamp = message.get("create_time")
    
    if role == "user":
        return {
            "type": "user-query",
            "text": text,
            "timestamp": int(timestamp * 1000) if timestamp else None
        }
    elif role == "assistant":
        entry = {
            "type": "answer",
            "text": text,
            "timestamp": int(timestamp * 1000) if timestamp else None
        }
        if model_slug:
            entry["model"] = model_slug
        return entry
    
    return None


def _detect_model(mapping: dict) -> str:
    """Detect the model used from ChatGPT messages."""
    for node_id, node in mapping.items():
        message = node.get("message") or {}
        metadata = message.get("metadata", {})
        model_slug = metadata.get("model_slug", "")
        if model_slug:
            return model_slug
    return "gpt-4"


def _timestamp_to_iso(timestamp: Optional[float]) -> Optional[str]:
    """Convert Unix timestamp to ISO 8601 string."""
    if timestamp is None:
        return None
    try:
        dt = datetime.utcfromtimestamp(timestamp)
        return dt.isoformat() + "Z"
    except:
        return None
