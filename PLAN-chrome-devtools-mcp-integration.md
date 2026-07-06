# Chrome DevTools MCP Integration Plan

## Goal
Submit AgentSON as a standard integration to Chrome DevTools MCP (https://github.com/ChromeDevTools/chrome-devtools-mcp)

## Why
- Chrome DevTools MCP is Google-owned, 46k stars, widely adopted
- Integration would make .agentson the standard format for recording agent browser actions
- Enables portable execution traces across all Chrome DevTools MCP users

## Options

### Option 1: Add .agentson Skill (Low Effort)
Add an instruction file to `skills/` directory that teaches agents how to use Chrome DevTools and record traces.

**What to add:**
- `skills/agentson/SKILL.md` - Instructions for agents
- `skills/agentson/examples/` - Example .agentson traces

**PR title:** `feat: add AgentSON skill for recording browser action traces`

### Option 2: Add --record-agentson Flag (Medium Effort)
Add a flag that wraps all tool calls with .agentson stream entries.

**What to add:**
- `src/tools/agentson-recorder.ts` - .agentson stream recorder
- `src/agentson/` - .agentson format utilities
- `--record-agentson` CLI flag

**PR title:** `feat: add --record-agentson flag for portable execution traces`

### Option 3: Add --agentson-output Flag (Medium Effort)
Add a flag that includes .agentson-formatted entries in tool results.

**What to add:**
- `src/agentson/` - .agentson format utilities
- `--agentson-output` CLI flag
- Modify tool result format to include .agentson entries

**PR title:** `feat: add --agentson-output flag for .agentson-formatted results`

## Steps

1. [ ] Sign Google's CLA at https://cla.developers.google.com/
2. [ ] Fork https://github.com/ChromeDevTools/chrome-devtools-mcp
3. [ ] Choose integration option (1, 2, or 3)
4. [ ] Implement changes
5. [ ] Add tests
6. [ ] Update documentation
7. [ ] Submit PR with conventional commits

## Resources

- Chrome DevTools MCP repo: https://github.com/ChromeDevTools/chrome-devtools-mcp
- CONTRIBUTING.md: https://github.com/ChromeDevTools/chrome-devtools-mcp/blob/main/CONTRIBUTING.md
- Google CLA: https://cla.developers.google.com/
- AgentSON spec: https://github.com/andiekobbietks/AgentSON/blob/master/spec/v1.2.json
- AgentSON ontology: https://github.com/andiekobbietks/AgentSON/blob/master/spec/ontology.md

## Status
- [ ] CLA signed
- [ ] Fork created
- [ ] Integration implemented
- [ ] Tests passing
- [ ] Documentation updated
- [ ] PR submitted
