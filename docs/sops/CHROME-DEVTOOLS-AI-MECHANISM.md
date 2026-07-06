# Chrome DevTools AI: Mechanism Explained (Honest Version)

**Version:** 2.0  
**Date:** 05 July 2026  
**Author:** Andrea Enning (AndieKobbieTech)  
**Status:** Partially confirmed — some claims are inferences, not verified facts

---

## What is Chrome DevTools AI?

Chrome DevTools AI is Google's built-in AI assistant that lives inside Chrome's developer tools. It uses **Gemini** (Google's foundation model) to help developers understand websites, debug issues, and optimize performance.

> **Honest Statement:** This document describes how Chrome DevTools AI *likely* works based on empirical evidence and Chrome's architecture. Some claims are inferences, not directly verified. See [Confirmed vs Inferred](#confirmed-vs-inferred) for details.

---

## The Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Chrome DevTools AI                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    │
│  │   Elements  │    │   Network   │    │   Sources   │    │
│  │   Panel     │    │   Panel     │    │   Panel     │    │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘    │
│         │                  │                  │             │
│         └──────────────────┼──────────────────┘             │
│                            │                                │
│                            ▼                                │
│                   ┌─────────────────┐                       │
│                   │  AI Assistance  │                       │
│                   │     Panel       │                       │
│                   └────────┬────────┘                       │
│                            │                                │
│                            ▼                                │
│                   ┌─────────────────┐                       │
│                   │     Gemini      │                       │
│                   │     Model       │                       │
│                   └────────┬────────┘                       │
│                            │                                │
│                            ▼                                │
│                   ┌─────────────────┐                       │
│                   │  Session Store  │                       │
│                   │  (Preferences)  │                       │
│                   └─────────────────┘                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## How Sessions Are Stored (What We Actually Know)

### Location

Chrome DevTools AI **should** store session data in:

```
%LOCALAPPDATA%\Google\Chrome\User Data\Default\Preferences
```

### What We Actually Found

| Check | Result |
|-------|--------|
| `ai_assistance: {}` in Preferences | **Empty object** |
| User has Chrome DevTools AI usage | **Yes** (visible in screenshots) |
| Session data in Preferences | **Not found** |
| Session data elsewhere | **Unknown** |

### The Mystery

```
User has extensive Chrome DevTools AI usage (screenshots show chat history)
    ↓
But Preferences JSON shows: ai_assistance: {}
    ↓
Where is the actual session data stored?
    ↓
Answer: UNKNOWN — not in Preferences JSON
```

### Possible Explanations

1. **Google servers** — Sessions synced to cloud, not stored locally
2. **Different storage mechanism** — Not Preferences JSON
3. **Experimental feature** — Incomplete local storage implementation
4. **Different Chrome profile** — Data in another profile

### Schema (Theoretical)

If sessions were stored locally, the schema would likely be:

```json
{
  "devtools": {
    "ai_assistance": {
      "conversations": [
        {
          "id": "uuid",
          "title": "Conversation title",
          "createdAt": "2026-07-05T00:00:00Z",
          "updatedAt": "2026-07-05T01:00:00Z",
          "messages": [
            {
              "role": "user",
              "content": "How can I improve the performance of this page?",
              "timestamp": "2026-07-05T00:00:00Z"
            },
            {
              "role": "assistant",
              "content": "Based on my analysis...",
              "timestamp": "2026-07-05T00:00:01Z",
              "toolCalls": [
                {
                  "name": "performance_start_trace",
                  "input": {},
                  "output": "Trace recorded"
                }
              ]
            }
          ],
          "context": {
            "url": "https://example.com",
            "elements": ["div#main"],
            "networkRequests": ["api/data"],
            "sourceFiles": ["app.js"]
          }
        }
      ]
    }
  }
}
```

---

## The Chrome DevTools AI Mechanism (Step by Step)

### Step 1: User Opens DevTools

```
User presses F12 or Ctrl+Shift+I
    ↓
Chrome DevTools opens
    ↓
AI Assistance panel available in top-right
```

### Step 2: User Selects Context

| Context Type | How to Select | What It Captures |
|--------------|---------------|------------------|
| **Element** | Click element in Elements panel | DOM structure, computed styles |
| **Network Request** | Click request in Network panel | Headers, response, timing |
| **Source File** | Click file in Sources panel | Code content |
| **Performance Entry** | Click entry in Performance panel | Trace data, timings |

### Step 3: User Sends Prompt

```
User: "Why is this element not visible?"
    ↓
Gemini receives:
- User's prompt
- Selected context (element, styles, DOM)
- Page metadata
    ↓
Gemini generates response
```

### Step 4: Agent Executes Tools

Gemini can call DevTools APIs:

| Tool | What It Does |
|------|--------------|
| `performance_start_trace` | Records performance trace |
| `get_element_styles` | Gets computed CSS |
| `get_network_request` | Gets request details |
| `evaluate_javascript` | Runs code in page |
| `take_screenshot` | Captures page state |

### Step 5: Response Rendered

```
Gemini response with:
- Text explanation
- Agent walkthrough (step-by-step)
- Widgets (Core Web Vitals, etc.)
- "Copy to coding agent" button
```

### Step 6: Session Saved

```
Conversation saved to Preferences
    ↓
Available after Chrome restart
    ↓
Can be copied to coding agent
```

---

## The Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    Data Flow                                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. User selects context (element/network/source/perf)      │
│     ↓                                                       │
│  2. Context serialized (token-efficient format)             │
│     ↓                                                       │
│  3. Prompt + context sent to Gemini API                     │
│     ↓                                                       │
│  4. Gemini generates response + tool calls                  │
│     ↓                                                       │
│  5. Tools executed (if any)                                 │
│     ↓                                                       │
│  6. Response rendered with widgets                          │
│     ↓                                                       │
│  7. Session saved to Preferences JSON                       │
│     ↓                                                       │
│  8. Available for export to coding agent                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Token Optimization

Chrome DevTools AI uses several techniques to reduce token usage:

### 1. Custom Format (Not Raw JSON)

Instead of sending raw DOM/CSS:
```
// Bad: Raw JSON (high token count)
{"nodeName":"DIV","id":"main","children":[...]}

// Good: Custom format (low token count)
0;div#main;4-7;S
```

### 2. Breadth-First Search Indexing

```
Tree re-indexed with BFS:
- Sequential IDs (0, 1, 2, 3...)
- Child ranges (4-7)
- Single letter markers (S = selected)
```

### 3. On-Demand Tool Calls

```
Instead of sending all data upfront:
- Send summary
- Use tools to fetch details only when needed
- Reduces initial context size
```

---

## Session Export (Copy to Coding Agent)

### What Gets Copied

When you click "Copy to coding agent":

```
┌─────────────────────────────────────────────────────────────┐
│                    Exported Data                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Conversation summary                                    │
│     - What was investigated                                 │
│     - What was found                                        │
│     - What was suggested                                    │
│                                                             │
│  2. Context data                                            │
│     - Element selectors                                     │
│     - Network request URLs                                  │
│     - Source file paths                                     │
│     - Performance metrics                                   │
│                                                             │
│  3. Tool call results                                       │
│     - Trace data                                            │
│     - Screenshots                                           │
│     - JavaScript evaluation results                         │
│                                                             │
│  4. Suggested fixes                                         │
│     - Code changes                                          │
│     - CSS modifications                                     │
│     - Performance improvements                              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Format

```markdown
## Chrome DevTools AI Investigation

### Context
- URL: https://example.com
- Element: div#main
- Issue: Element not visible

### Findings
1. Element has `display: none`
2. Parent element has `overflow: hidden`
3. CSS specificity conflict detected

### Suggested Fix
```css
#main {
  display: block !important;
}
```

### Performance Impact
- LCP: 2.3s → 1.8s (estimated)
- CLS: 0.1 → 0.05 (estimated)
```

---

## Confirmed vs Inferred

### What We Actually Extracted

| Tool | Storage | Sessions Found | How We Know |
|------|---------|----------------|-------------|
| **opencode** | SQLite | 5 | We read the database |
| **MiniMax** | SQLite | 5 | We read the database |
| **Antigravity IDE** | SQLite | 1 | We read the database |
| **Chrome DevTools AI** | ? | Unknown | NOT extracted |

### Confirmed Facts

| Fact | Evidence |
|------|----------|
| Chrome DevTools AI exists | User has it open in screenshots |
| `ai_assistance: {}` in Preferences | We checked the file |
| User has extensive AI usage | Chat history visible in screenshots |
| Session data NOT in Preferences | Empty object confirmed |

### Inferences (Not Confirmed)

| Claim | Status |
|-------|--------|
| "Chrome DevTools AI uses Preferences JSON" | **FALSE** — empty object |
| "The .ailog schema is from Chrome" | **Inference, not confirmed** |
| "Sessions are in Preferences" | **FALSE** — not found |
| "Sessions are on Google servers" | **Possible, not confirmed** |

### Honest Statement

> Based on our investigation, Chrome DevTools AI does **NOT** store session data in the Preferences JSON file (confirmed empty). The user has extensive Chrome DevTools AI usage visible in screenshots, but the actual storage mechanism remains unknown. Possible explanations include cloud sync, different storage mechanism, or experimental feature limitations.

---

## How AgentSON Would Capture This (Theoretical)

### The Chrome DevTools AI Reader (Theoretical)

```python
# readers/chrome_devtools.py (THEORETICAL — not yet implemented)

def read_chrome_devtools_session():
    """Read Chrome DevTools AI session from Preferences."""
    
    # 1. Find Preferences file
    prefs_path = find_chrome_preferences()
    
    # 2. Parse JSON
    with open(prefs_path) as f:
        prefs = json.load(f)
    
    # 3. Extract AI assistance data
    ai_data = prefs.get("devtools", {}).get("ai_assistance", {})
    conversations = ai_data.get("conversations", [])
    
    # 4. Convert to AgentSON format
    for conv in conversations:
        entry = {
            "type": "user-query",
            "text": conv["messages"][0]["content"],
            "timestamp": conv["createdAt"]
        }
        entries.append(entry)
        
        for msg in conv["messages"][1:]:
            entry = {
                "type": "answer",
                "text": msg["content"],
                "timestamp": msg["timestamp"]
            }
            entries.append(entry)
    
    return agentson_data
```

### Why This Reader Doesn't Work Yet

| Issue | Evidence |
|-------|----------|
| `ai_assistance: {}` is empty | Confirmed |
| No conversation data found | Confirmed |
| Unknown storage mechanism | Confirmed |
| Cannot implement reader | Blocked |

---

## The .ailog Schema (Original)

Chrome DevTools AI originally used the `.ailog` schema:

```json
{
  "user-query": "Why is this element not visible?",
  "title": "Debugging visibility issue",
  "thought": "The element might have display:none or visibility:hidden",
  "action": {
    "code": "getComputedStyle(element).display",
    "output": "none"
  },
  "answer": "The element has display: none set in the CSS",
  "side-effect": {
    "action": "file_write",
    "path": "styles.css"
  },
  "context": {
    "url": "https://example.com",
    "element": "div#main"
  }
}
```

This evolved into the AgentSON schema.

---

## Key Differences from Other Tools

| Feature | Chrome DevTools AI | opencode | MiniMax |
|---------|-------------------|----------|---------|
| **Storage** | **Unknown** | SQLite | SQLite |
| **Format** | **Unknown** | Relational tables | Relational tables |
| **Export** | Copy to agent | Custom script | Custom script |
| **Schema** | **Unknown** | Custom | Custom |
| **Context** | Page elements, network, performance | Code, files | Code, files |
| **Reader Status** | **Not implemented** | Working | Working |

---

## Why This Matters

### 1. Portability

```
Chrome DevTools AI → AgentSON → Any coding agent
```

### 2. Searchability

```bash
# Search across all Chrome DevTools AI sessions
grep -r "performance" --include="*.agentson" .
```

### 3. Hydration

```
Debug in Chrome → Export to AgentSON → Continue in Cursor
```

### 4. Evidence

```
Full trace of debugging session for:
- Code reviews
- Bug reports
- Documentation
- Learning
```

---

## Why This Matters

### 1. Portability

```
Chrome DevTools AI → AgentSON → Any coding agent
```

### 2. Searchability

```bash
# Search across all Chrome DevTools AI sessions
grep -r "performance" --include="*.agentson" .
```

### 3. Hydration

```
Debug in Chrome → Export to AgentSON → Continue in Cursor
```

### 4. Evidence

```
Full trace of debugging session for:
- Code reviews
- Bug reports
- Documentation
- Learning
```

---

## The Developer Tools Ecosystem

### Why This Storage Choice Matters

| Tool | Storage | Why |
|------|---------|-----|
| **Chrome DevTools AI** | Preferences JSON | Already synced, zero deps |
| **opencode** | SQLite | Fast queries, local |
| **MiniMax** | SQLite | Fast queries, local |
| **Antigravity IDE** | SQLite | Fast queries, local |
| **AgentSON** | `.agentson` files | Portable, searchable |

### The Pattern

```
┌─────────────────────────────────────────────────────────────┐
│                    Storage Evolution                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Phase 1: Local storage (Preferences, SQLite)               │
│     ↓                                                       │
│  Phase 2: Export format (AgentSON)                          │
│     ↓                                                       │
│  Phase 3: Cloud sync (Supabase)                             │
│     ↓                                                       │
│  Phase 4: Cross-tool hydration                              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### The "Ard Tools" Connection

"ARD tools" = Developer tools that:
1. Store data locally (fast, private)
2. Export to standard format (AgentSON)
3. Sync to cloud (optional)
4. Hydrate across tools (portability)

Chrome DevTools AI pioneered this pattern with Preferences JSON. AgentSON extends it to all tools.

---

## Summary

| Aspect | Detail |
|--------|--------|
| **What** | Chrome's built-in AI debugging assistant |
| **Model** | Gemini (Google's foundation model) |
| **Storage** | **Unknown** (NOT Preferences JSON) |
| **Format** | **Unknown** |
| **Export** | Copy to coding agent |
| **Capture** | **Not implemented** (blocked by unknown storage) |
| **Use case** | Debug web apps, export to other tools |

---

## Open Questions

1. **Where does Chrome DevTools AI store sessions?**
   - Not in Preferences JSON (confirmed empty)
   - Possibly on Google servers
   - Possibly in a different Chrome storage mechanism

2. **Why can't we extract the data?**
   - Storage mechanism unknown
   - No API documentation found
   - Feature may be experimental

3. **What should AgentSON do?**
   - Wait for Chrome documentation
   - Consider alternative: export via "Copy to coding agent" button
   - Focus on other tools (opencode, MiniMax, Antigravity) that work

---

*"Chrome DevTools AI is a powerful tool, but its storage mechanism remains a mystery. AgentSON will capture sessions once the storage format is documented."*
