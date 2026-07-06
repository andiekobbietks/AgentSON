# Draft PR: AgentSON Integration for Chrome DevTools MCP

## Summary

Adds AgentSON integration to Chrome DevTools MCP, enabling portable execution traces for browser agent actions.

## What is AgentSON?

AgentSON is a streaming format for recording agent actions, observations, and thoughts. It provides:
- Portable execution traces across different tools and environments
- Replay capability for verifying findings
- Provenance tracking for audit and debugging
- Cross-tool integration (browser + filesystem + database)

## Changes

### Option 1: Skill File
- Added `skills/agentson/SKILL.md` with instructions for agents
- Added example .agentson traces in `skills/agentson/examples/`
- No code changes required

### Option 2: --record-agentson Flag
- Added `src/tools/agentson-recorder.ts` for recording tool calls
- Added `src/agentson/` utilities for .agentson format
- Added `--record-agentson` CLI flag
- Modified tool execution to record to .agentson stream

### Option 3: --agentson-output Flag
- Added `src/agentson/` utilities for .agentson format
- Added `--agentson-output` CLI flag
- Modified tool results to include .agentson entries

## Example .agentson Stream

```json
{"type": "stream-meta", "stream_id": "chrome-devtools-2026-07-06", "agents": [{"id": "chrome-devtools", "capabilities": ["navigate", "screenshot", "evaluate"]}]}
{"type": "action", "tool": "navigate_page", "args": {"url": "https://example.com"}}
{"type": "observation", "text": "Navigated to https://example.com"}
{"type": "action", "tool": "take_screenshot", "args": {}}
{"type": "observation", "text": "Screenshot captured"}
```

## Use Cases

1. **Debugging**: Record all browser actions to trace what happened
2. **Replay**: Re-execute the same sequence to verify findings
3. **Handoff**: Share execution traces between agents
4. **Audit**: Complete provenance of browser interactions

## Testing

- [ ] Unit tests for .agentson format utilities
- [ ] Integration tests for --record-agentson flag
- [ ] Manual testing with Chrome DevTools MCP

## Documentation

- [ ] Updated README.md with new flag
- [ ] Added .agentson skill documentation
- [ ] Updated tool reference

## Related

- AgentSON repo: https://github.com/andiekobbietks/AgentSON
- AgentSON spec: https://github.com/andiekobbietks/AgentSON/blob/master/spec/v1.2.json
- AgentSON ontology: https://github.com/andiekobbietks/AgentSON/blob/master/spec/ontology.md
