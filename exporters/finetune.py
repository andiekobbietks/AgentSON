"""
Fine-tuning exporters for AgentSON.

Converts AgentSON sessions into training formats:
- Unsloth (ShareGPT): conversation pairs for fine-tuning LLaMA/Mistral
- Olive (chat-messages): structured chat for Microsoft Olive pipeline
"""

import json
from typing import Dict, List, Optional


def to_unsloth_examples(
    session: dict,
    min_rating: Optional[int] = None,
    include_thoughts: bool = True
) -> List[dict]:
    """
    Convert AgentSON session to Unsloth/ShareGPT training examples.
    
    Each example is a conversation with "conversations" key containing
    alternating human/gpt turns.
    
    Output format:
    {
        "conversations": [
            {"from": "human", "value": "user question"},
            {"from": "gpt", "value": "assistant response"},
            ...
        ],
        "source": "agentson",
        "session_id": "xxx",
        "tool": "opencode"
    }
    """
    entries = session.get("entries", [])
    if not entries:
        return []
    
    examples = []
    current_conversation = []
    current_human = None
    
    for entry in entries:
        entry_type = entry.get("type")
        
        if entry_type == "user-query":
            # Start a new conversation turn
            if current_human is not None and current_conversation:
                # Save previous conversation
                examples.append(_build_unsloth_example(
                    current_conversation, session
                ))
                current_conversation = []
            
            current_human = entry.get("text", entry.get("query", ""))
            current_conversation.append({
                "from": "human",
                "value": current_human
            })
            
        elif entry_type == "answer":
            if current_human is not None:
                current_conversation.append({
                    "from": "gpt",
                    "value": entry.get("text", "")
                })
                current_human = None
                
        elif entry_type == "thought" and include_thoughts:
            # Include thoughts as part of the gpt response context
            if current_conversation and current_conversation[-1]["from"] == "gpt":
                thought = entry.get("text", "")
                current_conversation[-1]["value"] = (
                    f"<thinking>\n{thought}\n</thinking>\n\n"
                    + current_conversation[-1]["value"]
                )
                
        elif entry_type == "action":
            # Include tool use in gpt response
            if current_human is not None:
                tool_name = entry.get("tool", "unknown")
                code = entry.get("code", "")
                output = entry.get("output", "")
                
                action_text = f"[Used {tool_name}]\n```json\n{code}\n```\nOutput:\n```\n{output}\n```"
                
                if current_conversation and current_conversation[-1]["from"] == "gpt":
                    current_conversation[-1]["value"] += f"\n\n{action_text}"
                else:
                    current_conversation.append({
                        "from": "gpt",
                        "value": action_text
                    })
                    current_human = None
    
    # Save last conversation
    if current_conversation:
        examples.append(_build_unsloth_example(current_conversation, session))
    
    return examples


def _build_unsloth_example(conversations: List[dict], session: dict) -> dict:
    """Build a single Unsloth training example."""
    return {
        "conversations": conversations,
        "source": "agentson",
        "session_id": session.get("id", "unknown"),
        "tool": session.get("tool", {}).get("name", "unknown"),
        "agent": session.get("agent", {}).get("name", "unknown")
    }


def to_olive_examples(
    session: dict,
    min_rating: Optional[int] = None
) -> List[dict]:
    """
    Convert AgentSON session to Microsoft Olive chat-messages format.
    
    Output format per example:
    {
        "messages": [
            {"role": "system", "content": "You are a helpful assistant..."},
            {"role": "user", "content": "user question"},
            {"role": "assistant", "content": "assistant response"}
        ],
        "source": "agentson",
        "session_id": "xxx"
    }
    """
    entries = session.get("entries", [])
    if not entries:
        return []
    
    examples = []
    messages = [
        {
            "role": "system",
            "content": (
                f"You are an AI coding assistant. "
                f"Tool: {session.get('tool', {}).get('name', 'unknown')}. "
                f"Model: {session.get('agent', {}).get('name', 'unknown')}."
            )
        }
    ]
    
    for entry in entries:
        entry_type = entry.get("type")
        
        if entry_type == "user-query":
            messages.append({
                "role": "user",
                "content": entry.get("text", entry.get("query", ""))
            })
            
        elif entry_type == "answer":
            messages.append({
                "role": "assistant",
                "content": entry.get("text", "")
            })
            
        elif entry_type == "action":
            # Append tool use to last assistant message or create new one
            tool_name = entry.get("tool", "unknown")
            code = entry.get("code", "")
            output = entry.get("output", "")
            
            tool_msg = f"[Tool: {tool_name}]\nInput: ```json\n{code}\n```\nOutput: ```\n{output}\n```"
            
            if messages and messages[-1]["role"] == "assistant":
                messages[-1]["content"] += f"\n\n{tool_msg}"
            else:
                messages.append({
                    "role": "assistant",
                    "content": tool_msg
                })
        
        # Flush on alternating user/assistant pairs
        if (len(messages) >= 3 and 
            messages[-2]["role"] == "user" and 
            messages[-1]["role"] == "assistant"):
            examples.append({
                "messages": messages.copy(),
                "source": "agentson",
                "session_id": session.get("id", "unknown")
            })
            # Keep system message for next conversation
            messages = [messages[0]]
    
    # Save last conversation if it has user + assistant
    if (len(messages) >= 3 and 
        messages[-2]["role"] == "user" and 
        messages[-1]["role"] == "assistant"):
        examples.append({
            "messages": messages,
            "source": "agentson",
            "session_id": session.get("id", "unknown")
        })
    
    return examples


def export_training_data(
    session: dict,
    format: str = "unsloth",
    output_path: Optional[str] = None,
    min_rating: Optional[int] = None,
    include_thoughts: bool = True
) -> List[dict]:
    """
    Export AgentSON session to training data format.
    
    Args:
        session: AgentSON session dict
        format: "unsloth" or "olive"
        output_path: Optional path to write JSONL file
        min_rating: Optional minimum quality rating filter
        include_thoughts: Whether to include thought entries (Unsloth only)
    
    Returns:
        List of training examples
    """
    if format == "unsloth":
        examples = to_unsloth_examples(session, min_rating, include_thoughts)
    elif format == "olive":
        examples = to_olive_examples(session, min_rating)
    else:
        raise ValueError(f"Unknown format: {format}. Use 'unsloth' or 'olive'.")
    
    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            for example in examples:
                f.write(json.dumps(example, ensure_ascii=False) + "\n")
    
    return examples
