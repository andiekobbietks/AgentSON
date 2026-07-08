# AgentSON Adapter Specification

**Status:** Draft v1.0
**Date:** 06 July 2026

---

## Overview

Adapters translate between execution backends (CDP, MCP, browser-use, extensions) and the AgentSON canonical format. Each adapter:

1. Receives operations from its backend
2. Normalizes them to AgentSON primitives
3. Emits entries to the .agentson stream

---

## Adapter Interface

Every adapter MUST implement:

```javascript
class AgentSONAdapter {
  // Unique identifier for this adapter
  id: string;  // e.g., "cdp", "mcp", "browser-use", "extension"

  // Emit entry to stream
  emit(entry: AgentSONEntry): void;

  // Process incoming operation from backend
  handleOperation(op: Operation): AgentSONEntry;

  // Map backend-specific tool names to semantic operations
  mapTool(toolName: string): string;
}
```

---

## CDP Adapter Specification

### Connection

```javascript
const CDPAdapter = {
  id: 'cdp',
  
  // Connect to Chrome DevTools Protocol
  connect(url: 'http://localhost:9222') {
    // WebSocket to browser target
  },
  
  // Map CDP methods to semantic operations
  mapTool(cdpMethod: string): string {
    const mapping = {
      'Page.navigate':           'browser.navigate',
      'Runtime.evaluate':        'browser.evaluate',
      'Page.captureScreenshot':  'browser.screenshot',
      'DOM.getDocument':         'browser.extract',
      'DOM.querySelector':       'browser.extract',
      'Performance.getMetrics':  'browser.performance',
      'Target.getTargets':       'browser.list-tabs',
    };
    return mapping[cdpMethod] || cdpMethod;
  }
};
```

### Event Mapping

| CDP Method | AgentSON Action | Args |
|------------|-----------------|------|
| `Page.navigate({url})` | `{tool: "browser.navigate", args: {url}}` | URL to load |
| `Runtime.evaluate({expression})` | `{tool: "browser.evaluate", args: {expr}}` | JS expression |
| `Page.captureScreenshot({format})` | `{tool: "browser.screenshot", args: {format}}` | Image format |
| `DOM.getDocument()` | `{tool: "browser.extract", args: {selector: "body"}}` | Content selector |
| `DOM.querySelector({selector})` | `{tool: "browser.extract", args: {selector}}` | CSS selector |
| `Performance.getMetrics()` | `{tool: "browser.performance", args: {}}` | None |
| `Target.getTargets()` | `{tool: "browser.list-tabs", args: {}}` | None |

### Response Mapping

| CDP Response | AgentSON Observation |
|--------------|---------------------|
| `Page.navigate` result | `{text: "Page loaded: {title}", source: "tool"}` |
| `Runtime.evaluate` result | `{text: "{value}", source: "tool"}` |
| `Page.captureScreenshot` | `{text: "Screenshot captured", source: "tool", attachments: [{type: "image", data}]}` |
| `DOM.getDocument` | `{text: "{html}", source: "tool"}` |
| `Performance.getMetrics` | `{text: "{json metrics}", source: "tool"}` |
| `Target.getTargets` | `{text: "{json targets}", source: "tool"}` |

### Example Flow

```
1. User Query: "Extract the page title"
2. Handoff: user → chrome-nano
3. Thought: "I need to evaluate JS to get the title"
4. Action: {tool: "browser.evaluate", args: {expr: "document.title"}}
5. Observation: {text: "My Page Title", source: "tool"}
6. Handoff: chrome-nano → opencode
7. Answer: "The page title is 'My Page Title'"
```

---

## MCP Adapter Specification

### Connection

```javascript
const MCPAdapter = {
  id: 'mcp',
  
  // Connect to MCP server via stdio or HTTP
  connect(server: string) {
    // Spawn MCP server process
    // or connect to HTTP endpoint
  },
  
  // Map MCP tool names to semantic operations
  mapTool(mcpTool: string): string {
    // MCP tools are already semantic
    // Just namespace them
    return `mcp.${mcpTool}`;
  }
};
```

### Event Mapping

| MCP Method | AgentSON Action | Args |
|------------|-----------------|------|
| `tools/list` | `{tool: "mcp.list-tools", args: {}}` | None |
| `tools/call({name, args})` | `{tool: "mcp.{name}", args}` | Tool-specific |
| `resources/read({uri})` | `{tool: "mcp.read-resource", args: {uri}}` | Resource URI |

### Response Mapping

| MCP Response | AgentSON Observation |
|--------------|---------------------|
| `tools/list` result | `{text: "{json tools}", source: "tool"}` |
| `tools/call` result | `{text: "{content}", source: "tool"}` |
| `resources/read` result | `{text: "{resource content}", source: "tool"}` |

### Example Flow

```
1. User Query: "List available MCP tools"
2. Handoff: user → mcp-agent
3. Thought: "Query MCP server for tool list"
4. Action: {tool: "mcp.list-tools", args: {}}
5. Observation: {text: "[{name: 'navigate', ...}]", source: "tool"}
6. Handoff: mcp-agent → opencode
7. Answer: "Available tools: navigate, click, type, ..."
```

---

## browser-use Adapter Specification

### Connection

```javascript
const BrowserUseAdapter = {
  id: 'browser-use',
  
  // Connect to browser-use daemon
  connect(daemonUrl: string) {
    // HTTP or WebSocket to browser-use
  },
  
  // Map browser-use commands to semantic operations
  mapTool(command: string): string {
    const mapping = {
      'navigate': 'browser.navigate',
      'click': 'browser.click',
      'type': 'browser.type',
      'state': 'browser.snapshot',
    };
    return mapping[command] || command;
  }
};
```

### Event Mapping

| browser-use Command | AgentSON Action | Args |
|---------------------|-----------------|------|
| `navigate(url)` | `{tool: "browser.navigate", args: {url}}` | URL |
| `click(index)` | `{tool: "browser.click", args: {index}}` | Element index |
| `type(index, text)` | `{tool: "browser.type", args: {index, text}}` | Input text |
| `state()` | `{tool: "browser.snapshot", args: {}}` | None |

### Response Mapping

| browser-use Response | AgentSON Observation |
|----------------------|---------------------|
| `navigate` result | `{text: "Navigated to {url}", source: "tool"}` |
| `click` result | `{text: "Clicked element {index}", source: "tool"}` |
| `type` result | `{text: "Typed '{text}' into element {index}", source: "tool"}` |
| `state` result | `{text: "{json state}", source: "tool"}` |

---

## Extension Adapter Specification

### Connection

```javascript
const ExtensionAdapter = {
  id: 'extension',
  
  // Connect via Chrome extension messaging
  connect(extensionId: string) {
    // chrome.runtime.sendMessage
    // chrome.tabs.executeScript
  },
  
  // Extension messages are already semantic
  mapTool(messageType: string): string {
    return `extension.${messageType}`;
  }
};
```

### Event Mapping

| Extension Event | AgentSON Primitive | Source |
|-----------------|-------------------|--------|
| `chrome.runtime.sendMessage` | `observation` | `extension` |
| `chrome.tabs.executeScript` | `action` | `extension` |
| DOM mutation observer | `observation` | `extension` |

---

## Validation

Each adapter MUST validate:

1. Every `action` has a valid `tool` name
2. Every `observation` has a `source` field
3. Handoffs reference valid agent IDs
4. No orphaned actions (action without observation)

---

## Implementation Checklist

- [x] CDP adapter (`chrome_agent.js`) - 7 semantic operations
- [ ] MCP adapter - connect to Chrome DevTools MCP server
- [ ] browser-use adapter - connect to browser-use daemon
- [ ] Extension adapter - connect via Chrome messaging
- [ ] Validation CLI tool
- [ ] Replay engine
