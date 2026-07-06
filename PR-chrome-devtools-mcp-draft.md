# Draft PR: AgentSON - Abstraction Layer Above MCP

## Summary

Adds `--record-agentson` flag to Chrome DevTools MCP, enabling portable execution traces for browser agent actions. This is an **observability layer** (like OpenTelemetry), not a control layer.

**Don't chase Chrome. Build the abstraction layer that survives Chrome.**

## Mental Model

```
MCP = execution interface (standard, won)
AgentSON = execution memory + coordination layer (abstraction above)
```

## What is AgentSON?

AgentSON is a streaming format for recording agent actions, observations, and thoughts. It provides:
- Portable execution traces across different tools and environments
- Replay capability for verifying findings
- Provenance tracking for audit and debugging
- Cross-tool integration (browser + filesystem + database)

## Why This Matters

MCP has already won:
- Chrome DevTools MCP: 46k stars, Google-owned
- Azure MCP Server: 260+ tools across 50+ services
- Every major cloud provider is adopting MCP

AgentSON should sit ABOVE this ecosystem, not integrate with any specific MCP server.

## Changes

### Added: `--record-agentson` Flag

When enabled, all tool calls are recorded to an .agentson stream:

```json
{"type": "stream-meta", "stream_id": "chrome-devtools-2026-07-06", "agents": [{"id": "chrome-devtools", "capabilities": ["navigate", "screenshot", "evaluate"]}]}
{"type": "action", "tool": "navigate_page", "args": {"url": "https://example.com"}}
{"type": "observation", "text": "Navigated to https://example.com"}
{"type": "action", "tool": "take_screenshot", "args": {}}
{"type": "observation", "text": "Screenshot captured"}
```

### Implementation

- Added `src/tools/agentson-recorder.ts` - .agentson stream recorder
- Added `src/agentson/` - .agentson format utilities
- Added `--record-agentson` CLI flag
- Modified tool execution to record to .agentson stream

## Use Cases

1. **Debugging**: Record all browser actions to trace what happened
2. **Replay**: Re-execute the same sequence to verify findings
3. **Handoff**: Share execution traces between agents
4. **Audit**: Complete provenance of browser interactions

## Positioning

This is "OpenTelemetry for MCP agents" - an observability layer that sits above MCP:

```
Chrome MCP = execution interface (Google owns this)
Azure MCP = execution interface (Microsoft owns this)
AgentSON = execution memory + coordination layer (community owns this)
```

## Testing

- [ ] Unit tests for .agentson format utilities
- [ ] Integration tests for --record-agentson flag
- [ ] Manual testing with Chrome DevTools MCP

## Documentation

- [ ] Updated README.md with new flag
- [ ] Added .agentson observability documentation
- [ ] Updated tool reference

## Related

- AgentSON repo: https://github.com/andiekobbietks/AgentSON
- AgentSON spec: https://github.com/andiekobbietks/AgentSON/blob/master/spec/v1.2.json
- AgentSON ontology: https://github.com/andiekobbietks/AgentSON/blob/master/spec/ontology.md

## CLA

- [ ] Google CLA signed at https://cla.developers.google.com/
