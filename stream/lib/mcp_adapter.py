#!/usr/bin/env python3
"""
AgentSON MCP Adapter
Connects to Chrome DevTools MCP server via mcp-use and emits to .agentson stream.

Usage:
    python mcp_adapter.py [output.agentson]
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

try:
    from mcp_use import MCPClient
except ImportError:
    print("Installing mcp-use...")
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "mcp-use"], check=True)
    from mcp_use import MCPClient


# Chrome DevTools MCP server config
CHROME_MCP_CONFIG = {
    "mcpServers": {
        "chrome-devtools": {
            "command": "npx",
            "args": ["-y", "chrome-devtools-mcp@latest"]
        }
    }
}

# Semantic operation mapping (Chrome DevTools MCP -> AgentSON operation)
TOOL_MAPPING = {
    # Navigation
    "navigate_page": "browser.navigate",
    "new_page": "browser.navigate",
    "select_page": "browser.select-tab",
    "close_page": "browser.close-tab",
    "list_pages": "browser.list-tabs",
    
    # Content
    "take_snapshot": "browser.extract",
    "take_screenshot": "browser.screenshot",
    "evaluate_script": "browser.evaluate",
    
    # Interaction
    "click": "browser.click",
    "hover": "browser.hover",
    "fill": "browser.type",
    "fill_form": "browser.type",
    "type_text": "browser.type",
    "press_key": "browser.key",
    "drag": "browser.drag",
    "upload_file": "browser.upload",
    
    # Network
    "list_network_requests": "browser.network",
    "get_network_request": "browser.network",
    
    # Console
    "list_console_messages": "browser.console",
    "get_console_message": "browser.console",
    
    # Performance
    "performance_start_trace": "browser.performance",
    "performance_stop_trace": "browser.performance",
    "performance_analyze_insight": "browser.performance",
    "lighthouse_audit": "browser.lighthouse",
    "take_heapsnapshot": "browser.memory",
    
    # Other
    "emulate": "browser.emulate",
    "resize_page": "browser.resize",
    "handle_dialog": "browser.dialog",
    "wait_for": "browser.wait",
}


class AgentSONMCPAdapter:
    """Connects to MCP server and emits AgentSON entries."""
    
    def __init__(self, output_path: str):
        self.output_path = Path(output_path)
        self.client = None
        self.session = None
        self.stream_id = f"mcp-export-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
    def emit(self, entry: dict):
        """Write entry to .agentson stream."""
        entry["timestamp"] = entry.get("timestamp", int(datetime.now().timestamp() * 1000))
        with open(self.output_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
            f.flush()
        print(f"  [{entry.get('type')}] {entry.get('tool', entry.get('text', '')[:50])}")
    
    def init_stream(self, tools: list):
        """Write stream-meta header."""
        tool_names = [t.name if hasattr(t, 'name') else str(t) for t in tools]
        self.emit({
            "type": "stream-meta",
            "stream_id": self.stream_id,
            "agents": [
                {"id": "mcp-client", "capabilities": ["mcp"]},
                {"id": "chrome-devtools", "capabilities": tool_names}
            ],
            "mode": "jsonl",
            "source": {
                "platform": "chrome-devtools-mcp",
                "tools": tool_names
            }
        })
    
    def map_tool(self, mcp_tool: str) -> str:
        """Map MCP tool name to semantic operation."""
        return TOOL_MAPPING.get(mcp_tool, f"mcp.{mcp_tool}")
    
    async def connect(self):
        """Connect to Chrome DevTools MCP server."""
        print("Connecting to Chrome DevTools MCP...")
        self.client = MCPClient(CHROME_MCP_CONFIG)
        await self.client.create_all_sessions()
        self.session = self.client.get_session("chrome-devtools")
        
        # List available tools
        tools = await self.session.list_tools()
        print(f"Connected. Tools available: {len(tools)}")
        for t in tools:
            print(f"  - {t.name}: {t.description[:60] if t.description else ''}")
        
        return tools
    
    async def call_tool(self, tool_name: str, args: dict) -> dict:
        """Call an MCP tool and emit to stream."""
        semantic_name = self.map_tool(tool_name)
        
        # Emit action
        self.emit({
            "type": "action",
            "agent": "mcp-client",
            "tool": semantic_name,
            "args": args,
            "source": "mcp"
        })
        
        # Call the tool
        try:
            result = await self.session.call_tool(tool_name, args)
            
            # Extract text from result
            text = ""
            if hasattr(result, "content"):
                for block in result.content:
                    if hasattr(block, "text"):
                        text = block.text
                        break
                    elif isinstance(block, dict) and "text" in block:
                        text = block["text"]
                        break
            
            # Emit observation
            self.emit({
                "type": "observation",
                "agent": "chrome-devtools",
                "source": "tool",
                "text": text[:3000] if text else str(result)[:3000]
            })
            
            return {"success": True, "text": text, "raw": result}
            
        except Exception as e:
            self.emit({
                "type": "observation",
                "agent": "chrome-devtools",
                "source": "tool",
                "text": f"Error: {str(e)}",
                "status": "error"
            })
            return {"success": False, "error": str(e)}
    
    async def close(self):
        """Close MCP connection."""
        if self.client:
            await self.client.close_all_sessions()
        print("Connection closed.")


async def interactive_mode(adapter: AgentSONMCPAdapter):
    """Interactive mode - user types tool calls."""
    tools = await adapter.connect()
    adapter.init_stream(tools)
    
    print("\n=== AgentSON MCP Adapter (Interactive Mode) ===")
    print("Commands:")
    print("  list              - List available tools")
    print("  call <tool> {args} - Call a tool")
    print("  quit              - Exit")
    print()
    
    while True:
        try:
            line = input("mcp> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        
        if not line:
            continue
        
        if line == "quit":
            break
        
        if line == "list":
            tools = await adapter.session.list_tools()
            for t in tools:
                print(f"  {t.name}: {t.description[:60] if t.description else ''}")
            continue
        
        if line.startswith("call "):
            parts = line[5:].split(" ", 1)
            tool_name = parts[0]
            args = {}
            if len(parts) > 1:
                try:
                    args = json.loads(parts[1])
                except json.JSONDecodeError:
                    args = {"input": parts[1]}
            
            await adapter.call_tool(tool_name, args)
            continue
        
        print(f"Unknown command: {line}")
    
    await adapter.close()


async def demo_mode(adapter: AgentSONMCPAdapter):
    """Demo mode - runs a sequence of tool calls."""
    tools = await adapter.connect()
    adapter.init_stream(tools)
    
    print("\n=== AgentSON MCP Adapter (Demo Mode) ===")
    
    # Demo sequence (using actual Chrome DevTools MCP tool names)
    demo_calls = [
        ("navigate_page", {"url": "https://example.com"}),
        ("take_screenshot", {}),
        ("evaluate_script", {"function": "() => document.title"}),
        ("take_snapshot", {}),
    ]
    
    for tool_name, args in demo_calls:
        print(f"\nCalling: {tool_name}")
        await adapter.call_tool(tool_name, args)
        await asyncio.sleep(0.5)
    
    # Emit completion
    adapter.emit({
        "type": "side-effect",
        "agent": "mcp-client",
        "action": "demo-complete",
        "result": {"tools_called": len(demo_calls)}
    })
    
    await adapter.close()


async def main():
    # Parse arguments
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    output = args[0] if args else "mcp_export.agentson"
    
    adapter = AgentSONMCPAdapter(output)
    
    # Check for demo mode
    if "--demo" in sys.argv:
        await demo_mode(adapter)
    else:
        await interactive_mode(adapter)


if __name__ == "__main__":
    asyncio.run(main())
