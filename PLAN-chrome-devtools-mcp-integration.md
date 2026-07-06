# AgentSON: Abstraction Layer Above MCP

## Mental Model

```
MCP = execution interface (standard, won)
AgentSON = execution memory + coordination layer (abstraction above)
```

**Don't chase Chrome. Build the abstraction layer that survives Chrome.**

## Why This Matters

MCP has already won:
- Chrome DevTools MCP: 46k stars, Google-owned
- Azure MCP Server: 260+ tools across 50+ services
- Every major cloud provider is adopting MCP

AgentSON should sit ABOVE this ecosystem, not integrate with any specific MCP server.

## What AgentSON Provides (That MCP Doesn't)

1. **Portable execution traces** - Record all MCP tool calls in a standard format
2. **Replay capability** - Re-execute sequences across different MCP servers
3. **Cross-tool integration** - Browser + filesystem + database in one trace
4. **Provenance tracking** - Who did what, when, with what arguments
5. **Semantic routing** - Intent → adapter selection (not CDP method names)

## Architecture

```
AgentSON (L3) - Coordination + Provenance + Replay
    ↓
Semantic Agent API (L2) - browser.list-tabs, filesystem.read, database.query
    ↓
MCP Servers (L1) - Chrome DevTools, Azure, custom servers
```

## Integration Strategy

### Option 1: MCP Observability Layer (Recommended)
- Frame as "OpenTelemetry for MCP agents"
- Add `--record-agentson` flag to ANY MCP server
- Don't change MCP semantics, just observe

### Option 2: AgentSON as MCP Server
- Implement AgentSON as an MCP server itself
- Other MCP servers can write to AgentSON streams
- Enables cross-server provenance

### Option 3: AgentSON as Output Format
- Add .agentson as output format option to MCP servers
- Standardized execution trace format
- Portable across environments

## Next Steps

1. **Update PR framing** - Position as "abstraction layer above MCP", not "Chrome DevTools integration"
2. **Build MCP observability layer** - Generic tool that records ANY MCP server's tool calls
3. **Test with multiple MCP servers** - Chrome DevTools + Azure + custom servers
4. **Submit to MCP ecosystem** - Not just Chrome DevTools, but MCP as a whole

## Resources

- MCP spec: https://modelcontextprotocol.io/
- Chrome DevTools MCP: https://github.com/ChromeDevTools/chrome-devtools-mcp
- Azure MCP Server: https://github.com/Azure/azure-mcp-server
- AgentSON spec: https://github.com/andiekobbietks/AgentSON/blob/master/spec/v1.2.json
