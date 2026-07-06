# Issue: Browser Extension Architecture — Live Capture, Metadata Ingestion & AgentSON Reconciliation

## Summary

Spec the browser extension architecture for **live capture**, **metadata ingestion from active tabs**, and **reconciliation against existing issue graphs**. This extends the Claude Tag reader concept (`issue-new-readers.md`) into a general-purpose browser sensor layer that feeds structured observations into AgentSON for cross-session stitching.

## Why an extension instead of just an API listener

Existing readers (opencode, cursor, claude_code, cline, aider) work on **local files** — SQLite databases and JSON logs written to disk by the CLI tools. This works because those tools save their session history locally.

AgentSON lacks coverage for tools that only exist **inside the browser**:

| Tool | Data location | Requires | Not covered by |
|------|--------------|----------|----------------|
| **Claude Tag** | claude.ai session page DOM + Slack thread | Page scraping + Slack API | File-based readers |
| **Chrome DevTools AI** | Preferences JSON (readable) | Markdown export workaround | File-based reader exists but requires user-initiated export |
| **ChatGPT** | chat.openai.com DOM | Page scraping | Importer exists but requires Conversation JSON export |
| **Gemini** | gemini.google.com DOM | Page scraping | No reader yet |
| **Cursor** (web mode) | Cloud workspace | REST API (undocumented) | File-based reader (local only) |
| **V0 / Bolt.new** | Browser-only UI | Page scraping | No reader yet |
| **Claude.ai** (chat) | claude.ai DOM | Page scraping | Import from claude.ai export only |

A browser extension is the **only** way to capture data from these tools without requiring users to manually export conversations. It sits at the browser as the **sensor layer**:

```
Extension sits in browser
    │
    ├── claude.ai content script → scrapes session pages → AgentSON events
    ├── slack.com content script → captures Claude Tag messages → AgentSON events
    ├── chrome-devtools content script → auto-extracts AI conversations → AgentSON events
    ├── chatgpt.com content script → scrapes conversations → AgentSON events
    └── metadata collector → any page → page metadata → context tags
```

## The browser as sensor layer

The user's earlier observation: Mori Liu's Mira extension sat inside the browser and leveraged browser APIs (tabs, history, active page DOM, storage, cookies). AgentSON's extension applies the same pattern but for **metadata ingestion and trace capture** rather than virtual try-on.

**What the extension can observe:**

| Browser API | What it exposes | Use for AgentSON |
|-------------|----------------|------------------|
| `tabs` | URL, title, favicon, active state | Session context — what page was open |
| `tabs.onActivated` | Tab switches | Timeline — which pages user worked on |
| `tabs.onUpdated` | Page loads/navigations | Timeline — when context shifted |
| `scripting` / `content_scripts` | Page DOM | Full session trace from AI tools |
| `storage` (local/session) | Extension's own state | Event queue before export |
| `downloads` | Files downloaded | Side-effect tracking |
| `webNavigation` | Navigation events | Full browsing timeline |
| `cookies` (with permission) | Auth tokens for claude.ai / chatgpt.com | Reuse auth for session page scraping |

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│               Browser Extension (MV3)                     │
├──────────────────────────────────────────────────────────┤
│                                                           │
│  Content Scripts (per-domain):                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐ │
│  │claude.ai │ │slack.com │ │chatgpt   │ │chrome-       │ │
│  │scraper   │ │scraper   │ │.com      │ │devtools      │ │
│  │          │ │          │ │scraper   │ │scraper       │ │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └──────┬───────┘ │
│       │            │            │               │         │
│       ▼            ▼            ▼               ▼         │
│  ┌───────────────────────────────────────────────────┐   │
│  │            Background Service Worker               │   │
│  │                                                    │   │
│  │   Receives structured events from content scripts  │   │
│  │   Normalizes to AgentSON entry format              │   │
│  │   Tags with provenance (confirmed/live)            │   │
│  │   Queues for export                                │   │
│  └────────────┬───────────────────────────────────────┘   │
│               │                                            │
│               ▼                                            │
│  ┌───────────────────────────────────────────────────┐   │
│  │              Metadata Collector                    │   │
│  │                                                    │   │
│  │   Listens to tabs.onActivated, tabs.onUpdated      │   │
│  │   Captures page metadata (title, URL, description) │   │
│  │   Emits context events into AgentSON timeline      │   │
│  └────────────┬───────────────────────────────────────┘   │
│               │                                            │
│               ▼                                            │
│  ┌───────────────────────────────────────────────────┐   │
│  │           Reconciliation Engine                     │   │
│  │                                                    │   │
│  │   Receives new AgentSON events from extension       │   │
│  │   Queries existing issue graph (local cache)        │   │
│  │   Links via temporal + content fingerprinting       │   │
│  │   Flags new issues / artifacts for review           │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                           │
│  ┌───────────────────────────────────────────────────┐   │
│  │               Storage Layer                        │   │
│  │                                                    │   │
│  │   Local event queue (before export)                │   │
│  │   AgentSON file cache (recent N sessions)           │   │
│  │   Issue graph index (for reconciliation)           │   │
│  │   User config (active scrapers, export prefs)      │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                           │
│  ┌───────────────────────────────────────────────────┐   │
│  │               Export Pathways                      │   │
│  │                                                    │   │
│  │   → Local file (.AgentSON)                         │   │
│  │   → Pipe to agentson CLI                           │   │
│  │   → Push to Supabase (if configured)               │   │
│  │   → Download button (manual export)                │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

## Content Scripts

### claude.ai scraper

Captures Claude Tag session pages and regular Claude.ai chat conversations.

```
claude.ai content script activates on:
    /session/*        → Claude Tag session read-only page
    /chat/*           → Regular Claude chat (new conversations)
    /projects/*       → Project conversations (optional)

What it extracts:

    Session metadata:
        ← URL → extract session_id from path
        ← Page title → "Claude Tag session in #channel-name"
        ← Document meta tags → model name, timing

    Tool calls (from rendered DOM):
        ← Tool call blocks → tool name, input JSON, output JSON
        ← Thinking blocks → expanded thinking text
        ← Error states → tool call failures, retries

    Conversation turns:
        ← User messages → prompt text, file attachments
        ← Assistant responses → text, code blocks
        ← Tool results → command output, file contents

    Timing:
        ← Relative timestamps on each turn → inter-event latency
        ← Session duration → from page metadata
```

**Selectors strategy** (fragile — must handle claude.ai DOM changes):

```
Primary: structured selectors with data-* attributes if available
Fallback: semantic HTML patterns (article, section, pre, code)
Last resort: full text extraction + AgentSON's content-driven classification
(from chrome_devtools.py pattern)
```

**AgentSON event mapping:**

| DOM element | AgentSON entry type | Provenance |
|-------------|--------------------|------------|
| User message text | `user-query` | `confirmed` |
| Assistant thinking block | `thought` | `confirmed` |
| Tool call block (name + input) | `action` | `confirmed` |
| Tool call output block | `observation` | `confirmed` |
| Assistant text response | `answer` | `confirmed` |
| File attachment | `side-effect` | `confirmed` |
| Error state | `observation` | `confirmed` |

### slack.com scraper

Captures Claude Tag messages in Slack web for the **message-layer** part of live capture.

```
slack.com content script monitors:
    All channel views for messages from Claude Tag bot

What it captures:
    ← Message text → user prompt or Claude response
    ← Checklist blocks → in-place updates as Claude works
    ← "Open session in Claude" links → session URL for deep scrape
    ← File attachments → file names, types, download URLs
    ← Thread structure → thread_ts linking Claude Tag messages
```

**Note:** This captures only the Slack communication layer (messages + attachments). Full tool-call detail requires the claude.ai session page scraper. The two streams are merged by thread_ts + timestamp alignment — same Strategy C (hybrid) pattern from `issue-new-readers.md`.

### chatgpt.com / gemini.google.com scrapers (future)

Same pattern as claude.ai scraper but targeting each platform's DOM structure.

### Page metadata collector (all domains)

This is the **general-purpose sensor** — not tied to AI tools.

```
Triggers on: tabs.onActivated, tabs.onUpdated (complete)

What it captures for every page:
    ← URL (full, with hash, query params)
    ← Page title (document.title)
    ← Meta description (if present)
    ← Open Graph tags (og:title, og:description, og:type)
    ← Meta keywords (if present)
    ← Content type detected (article, product, documentation, AI tool, search)
    ← Timestamp of first activation, last seen time
```

**AgentSON event mapping:**

| Metadata field | AgentSON entry | Usage |
|---------------|---------------|-------|
| URL + title | `context` event | "User was on page X" → session timeline |
| OG tags | `context.details` | Rich metadata for the context entry |
| Content type | `context.category` | "documentation", "ai-tool", "github" |
| Timestamps | Entry timestamp | Temporal anchoring for multi-source stitching |

**Why capture all pages?** The issue graph reconciliation depends on knowing the user's full context. If AgentSON only captures AI tool pages, the reconstruction pipeline loses the real-world trigger that sent the user to the AI tool in the first place.

## Background Service Worker

The service worker is the **orchestration layer**. It receives events from all content scripts, normalizes them to AgentSON format, manages the event queue, and handles export.

### Event flow

```
Content script sends: {
    source: "claude.ai" | "slack.com" | "chatgpt.com" | "metadata",
    event_type: "user-query" | "thought" | "action" | "answer" | "context",
    payload: { ... },    // domain-specific payload
    page_url: "https://...",
    timestamp: 1712345678901
}

Service worker:
    1. Receives event → wrap in AgentSON envelope
    2. Add provenance: { source: "extension", confidence: "confirmed" }
    3. Assign session_id:
        - For AI tools: match existing session by URL pattern + 15-min inactivity timeout
        - For metadata: assign to current AI session (if one active) or create standalone
    4. Queue for export
    5. If reconciliation enabled, send to reconciliation engine
```

### Session lifecycle

```
NEW_SESSION created when:
    - User navigates to claude.ai/chat/* or claude.ai/session/*
    - User navigates to slack.com and Claude Tag message detected

SESSION_ACTIVE while:
    - Same domain with conversation-id URL pattern
    - Inactivity < 15 minutes

SESSION_CLOSED when:
    - Tab closed
    - Inactivity > 15 minutes
    - User navigates away from conversation page

SESSION_EXPORTED when:
    - Session closed → batch write to .AgentSON file
    - Or manually by user via toolbar popup
```

### Export queue management

```
Queue in chrome.storage.local:

{
    "queue": [
        {
            "id": "evt-uuid-v4",
            "session_id": "sess-abc123",
            "entry": { /* AgentSON entry */ },
            "queued_at": 1712345678901,
            "retry_count": 0
        }
    ],
    "sessions": {
        "sess-abc123": {
            "tool": "claude-ai",
            "tool_session_id": "session-uuid-from-url",
            "started_at": 1712345600000,
            "ended_at": null,
            "event_count": 0,
            "last_event_at": 1712345678901
        }
    }
}
```

**Export triggers:**
- Session closed → flush event queue to .AgentSON file
- Queue size > 50 events → flush (prevents data loss on crash)
- Manual export via popup → immediate flush
- `storage.onChanged` listener in agentson CLI → auto-ingest on write

## Reconciliation Engine

This is the **key innovation** over a simple scraper — the extension doesn't just capture events, it **reconciles them against existing issue graphs**.

### What is the issue graph?

The issue graph is a set of linked `.AgentSON` files representing known work artifacts — issues, wikis, code changes, documentation. These are stored in a local index:

```
{
    "graphs": [
        {
            "id": "issue-gdpr-compliance-model",
            "type": "issue",
            "sessions": ["sess-001", "sess-004"],
            "artifacts": ["issues/issue-gdpr-compliance-model.md"],
            "keywords": ["gdpr", "aep", "reconstruction", "provenance"],
            "domain": "agentson"
        },
        {
            "id": "issue-new-readers",
            "type": "issue",
            "sessions": ["sess-002", "sess-004"],
            "artifacts": ["issues/issue-new-readers.md"],
            "keywords": ["claude-tag", "reader", "live-capture"],
            "domain": "agentson"
        }
    ]
}
```

### Reconciliation on new events

```
New event arrives (e.g., user asks Claude about GDPR compliance):

    1. Extract keywords from event text
    2. Match against issue graph index (keyword overlap, session overlap)
    3. If match found:
        a. Link this event to the matched issue graph
        b. Append session_id to graph's session list
        c. Emit reconciliation event: {
            type: "reconciliation",
            event_id: "evt-xyz",
            linked_graph_ids: ["issue-gdpr-compliance-model"],
            match_quality: 0.85,  // cosine similarity or keyword overlap
            link_type: "continues_existing | new_reference"
        }
    4. If no match:
        a. Hold for session-end analysis
        b. If session produces new artifact → create new graph node
        c. If session references nothing known → tag as "exploratory"
```

### What this enables

| Capability | Without reconciliation | With reconciliation |
|-----------|----------------------|-------------------|
| "What work was I doing related to GDPR?" | Search across .AgentSON files | Directed graph of all GDPR sessions |
| "Did I finish the new readers issue?" | Open issue file → see VS | Auto-updates graph with session outcome |
| "What prompted this work?" | No context | Traces back through metadata events to the trigger |
| "How many sessions on this topic?" | Manual count | Count from graph metadata |

## Storage Architecture

```
chrome.storage.local layout:

extension-config/
    active_scrapers: ["claude.ai", "slack.com", "metadata"]
    export_path: "~/agentson/captures/"          // default
    auto_export: true
    push_supabase_url: ""                        // optional
    max_cache_sessions: 20
    session_timeout_minutes: 15

event-queue/
    (Array of queued events — see above)

active-sessions/
    (Map of session_id → session metadata)

issue-graph-index/
    (Array of known graph nodes with keywords)

exported-sessions/
    (Set of session_ids already exported — prevents double-export)
```

## Export Pathways

### Local file (default)

```
Path: {export_path}/{tool}-{session_id}.AgentSON
Example: ~/agentson/captures/claude-ai-sess-abc123.AgentSON

Written when session closes or queue flushes.
File format matches AgentSON v1.1 spec exactly.
```

### Pipe to agentson CLI

```
Extension writes to a well-known path.
agentson CLI has a `--watch` flag:

    agentson watch --dir ~/agentson/captures/

Watches directory for new .AgentSON files and auto-ingests them
into the search index + Supabase.
```

### Supabase push (optional)

```
If user configures Supabase URL + anon key in extension settings:

    On session close → POST /sessions with .AgentSON document
    Requires user to authenticate (one-time OAuth flow)
    Enables cross-device search and sync
```

### Manual export (toolbar popup)

```
Extension popup shows:
    ├── Active session indicator (if capturing)
    ├── Recent sessions list (last 10)
    │   └── "Export" button per session
    ├── "Export All" button
    └── Settings (which scrapers active, export path)
```

## Manifest Structure (Chrome MV3)

```json
{
    "manifest_version": 3,
    "name": "AgentSON Capture",
    "version": "0.1.0",
    "description": "Capture AI agent session traces and metadata, convert to AgentSON format",
    "permissions": [
        "storage",
        "tabs",
        "scripting",
        "webNavigation"
    ],
    "host_permissions": [
        "https://claude.ai/*",
        "https://slack.com/*",
        "https://chatgpt.com/*"
    ],
    "content_scripts": [
        {
            "matches": ["https://claude.ai/*"],
            "js": ["content-scripts/claude-ai.js"]
        },
        {
            "matches": ["https://app.slack.com/*"],
            "js": ["content-scripts/slack.js"]
        }
    ],
    "background": {
        "service_worker": "service-worker.js",
        "type": "module"
    },
    "action": {
        "default_popup": "popup/index.html",
        "default_title": "AgentSON Capture"
    },
    "options_ui": {
        "page": "options/index.html",
        "open_in_tab": false
    }
}
```

## File Tree

```
agent-son-extension/
├── manifest.json
├── service-worker.js              # Background orchestration
├── content-scripts/
│   ├── claude-ai.js               # claude.ai session scraper
│   ├── slack.js                   # slack.com Claude Tag capture
│   └── metadata-collector.js      # General page metadata
├── lib/
│   ├── agentson-schema.js         # Schema constants + validation
│   ├── event-queue.js             # Queue management
│   ├── session-manager.js         # Session lifecycle
│   ├── reconciliation.js          # Issue graph reconciliation
│   ├── provenance.js              # Provenance tagging helpers
│   └── storage.js                 # chrome.storage.local wrapper
├── popup/
│   ├── index.html
│   ├── popup.js                   # Popup UI logic
│   └── popup.css
├── options/
│   ├── index.html
│   ├── options.js                 # Settings UI
│   └── options.css
├── tests/
│   ├── test-claude-scraper.js     # Unit tests for DOM parsing
│   ├── test-event-queue.js        # Queue management tests
│   ├── test-session-manager.js    # Session lifecycle tests
│   └── test-reconciliation.js     # Graph reconciliation tests
└── docs/
    └── ARCHITECTURE.md            # This document
```

## Permissions & Security

### Required permissions

| Permission | Why |
|------------|-----|
| `storage` | Event queue, config, session state |
| `tabs` | Monitor tab switches for metadata collection |
| `scripting` | Inject content scripts programmatically if needed |
| `webNavigation` | Track page lifecycle (onCompleted, onDOMContentLoaded) |
| Host: `*.claude.ai` | Scrape session pages |
| Host: `*.slack.com` | Capture Claude Tag messages |
| Host: `*.chatgpt.com` | Scrape conversations (future) |

### What the extension does NOT do

- No network request modification (not a proxy, not MITM)
- No cookie exfiltration (captures page content only)
- No cross-origin requests to non-configured hosts
- No telemetry — all data stays local unless user explicitly configures Supabase push
- No keylogging — captures only structured DOM elements, not input events

### Privacy model

```
All captured data is:

1. LOCAL by default — stored in chrome.storage.local
2. USER-CONTROLLED — viewable and deletable from popup
3. FILE-BASED — exported as .AgentSON files user owns
4. OPTIONAL CLOUD — only if user configures Supabase URL
5. TRANSPARENT — popup shows active capture indicator
```

## Relationship to Existing Readers

| Reader | Data source | Mode | Extension overlap |
|--------|------------|------|-------------------|
| `chrome_devtools.py` | Markdown export files | Post-hoc | Extension auto-captures DevTools AI without export button |
| `claude_code.py` | Local JSONL files | Post-hoc | Extension captures claude.ai (web), not Claude Code (CLI) |
| `chrome_devtools.py` (current) | User must manually export | Post-hoc | Extension makes this seamless |
| `claude-ai` (no reader yet) | claude.ai DOM | — | Extension is the reader |

The extension does **not** replace existing file-based readers. It fills the gap for tools that have **no local files to read**:

```
File-based readers (existing):
    opencode.db → opencode.py
    minimax.sqlite → minimax.py
    ~/.claude/*.jsonl → claude_code.py
    state.vscdb → cursor.py (planned)

Browser-based readers (extension):
    claude.ai DOM → content-scripts/claude-ai.js
    slack.com DOM → content-scripts/slack.js
    chatgpt.com DOM → content-scripts/chatgpt.js (future)
```

## Implementation Phases

### Phase 1: metadata collector + basic export (1-2 weeks)

```
Files:
    manifest.json
    service-worker.js (basic: event pass-through)
    lib/event-queue.js
    lib/session-manager.js
    lib/agentson-schema.js
    lib/storage.js
    content-scripts/metadata-collector.js
    popup/ (basic: session list + export button)

Deliverable:
    Extension captures page metadata on tab activation
    Groups into coarse sessions based on URL domain + timing
    Exports to .AgentSON files on session close
    Popup shows active sessions
```

### Phase 2: claude.ai scraper (2-3 weeks)

```
Add:
    content-scripts/claude-ai.js
    lib/reconciliation.js
    lib/provenance.js

Deliverable:
    Captures Claude Tag session pages with full tool-call detail
    Captures regular Claude.ai conversations
    Reconciliation against local issue graph index
    Session scraper for "Open session in Claude" links
```

### Phase 3: slack.com scraper + hybrid merge (1-2 weeks)

```
Add:
    content-scripts/slack.js

Deliverable:
    Captures Claude Tag messages in Slack web
    Detects "Open session in Claude" links
    Merges Slack stream + claude.ai scrape via thread_ts + timestamp
    Full three-layer capture: message → session page → AgentSON
```

### Phase 4: chrome.devtools extension + supabase (2-3 weeks)

```
Add:
    Extension auto-capture for Chrome DevTools AI (DevTools panel)
    Optional Supabase push from extension
    Cross-device sync (Supabase pull)

Deliverable:
    All browser-based AI tools captured automatically
    Cloud sync for multi-device workflow
    agentson CLI watch mode for auto-ingest
```

## Open Questions

1. **claude.ai DOM stability** — how often does Anthropic change session page structure? Mitigation: structured selectors with automated CI tests that ping daily.

2. **Session page auth** — does the extension need to handle claude.ai login state? If user isn't logged in when they click "Open session in Claude," the page shows a login wall.

3. **Multi-tab Claude sessions** — user may have multiple Claude tabs open. How does the session manager assign events? By URL session_id if available, otherwise by URL fingerprint + active tab context.

4. **Slack workspace routing** — Claude Tag sessions are per-Slack-workspace. Does the extension need to handle multiple workspace accounts?

5. **Rate limits** — claude.ai may rate-limit rapid page scraping. Mitigation: respect Retry-After headers, use exponential backoff, queue scrape requests.

6. **chrome.devtools.panels** — Chrome DevTools AI has its own panel that the user interacts with. Can an extension register a DevTools panel to auto-extract before the user even clicks "Export"?

## Immediate Next Step

Build the metadata collector first (Phase 1). It requires no AI-tool-specific DOM parsing, is unlikely to break, and immediately proves the concept:

```
1. Create extension with manifest.json, background service worker
2. Listen for tabs.onActivated → capture URL + title + timestamp
3. Store events in queue
4. On session timeout (15 min inactivity), flush to .AgentSON file
5. Test on real browsing session
```

This also generates the first "browser timeline" .AgentSON files that are the foundation for the reconciliation engine — knowing what pages the user was on provides the context anchors for stitching AI tool events.
