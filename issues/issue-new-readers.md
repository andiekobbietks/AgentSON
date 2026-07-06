# Issue: New Reader Targets — Claude Tag (live capture) and Browser Extension

## Summary

Add Claude Tag as a reader target with a new **live capture** reader type (not file-based like all existing readers). This requires a browser extension or Slack API listener that intercepts Claude Tag's messages at the communication layer as they arrive, converting them to AgentSON in real time.

## Why Claude Tag is different from existing readers

Existing readers (cursor, cline, aider, claude_code) operate on **local files on disk** — SQLite databases, JSON files, markdown logs. Claude Tag runs in Anthropic's cloud sandbox and communicates through Slack. There is no local file to read.

| Aspect | File-based readers (cursor/cline/aider) | Claude Tag reader |
|---|---|---|
| Data location | Local disk (~/.config, ~/.claude) | Slack API stream + claude.ai |
| Capture mode | Batch (read file after session) | Live (intercept during session) |
| Data format | SQLite, JSON, Markdown | Slack message objects + HTML |
| Reasoning trace | Captured in tool logs | Partial (Slack) + session page |
| User action required | None (just point at file) | Install extension/listener |

## Claude Tag's technical architecture (what we know)

Based on Anthropic's documentation and technical analysis:

### Execution flow

```
User types @Claude in Slack channel
    ↓
Slack Events API delivers message to Anthropic
    ↓
Ephemeral sandbox created per-thread (Anthropic infra)
    ↓
Claude works: read context, run tools, generate output
    ↓
Results posted back to Slack thread:
    • Checklist (live task list, edited in-place)
    • Final reply (text, file, chart)
    • "Open session in Claude" link
    ↓
Sandbox released when thread idle
    ↓
Session link → read-only page at claude.ai with full tool-call record
```

### What's visible at each layer

| Layer | What's exposed | Capture method | Confidence |
|---|---|---|---|
| **Slack thread** | User prompts, Claude's checklist updates, final replies, file attachments | Slack Events API | `confirmed` |
| **Session page** (claude.ai) | Every tool call (name, input, output), thinking blocks, timing | Extension scrapes the page | `confirmed` |
| **Sandbox internals** | Internal planning, token-level reasoning | Not exposed | N/A — vendor internal |

### Key finding

Claude Tag does **not** stream individual tool calls into Slack in real time. Instead, it posts a **checklist** that updates in-place as work progresses. The detailed trace (every tool call with I/O) is only accessible via the "Open session in Claude" link, which opens a read-only page on claude.ai.

This means a pure Slack API listener captures:
- ✅ User prompts
- ✅ Claude's final outputs
- ✅ Checklist status updates
- ✅ File attachments

But NOT:
- ❌ Individual tool calls with inputs/outputs
- ❌ Thinking blocks
- ❌ Execution timing

Those require **session page scraping** — either via browser extension (intercepting the user's claude.ai session) or via the session link.

## Proposed reader architecture: two capture strategies

### Strategy A: Slack Events API listener (lightweight)

A listener that connects to Slack's Events API for the workspace, capturing messages from the Claude Tag bot user in real time.

```
Slack Events API → message_callback events
    ↓
Filter by bot_id matching Claude Tag
    ↓
Parse message structure (blocks, attachments, files)
    ↓
Convert to AgentSON events (event_type: message / response / file_attachment)
    ↓
Timestamp and provenance-tag
    ↓
Append to session.ason
```

**Pros:** No user install required beyond OAuth. Works for all channels. Lightweight.
**Cons:** No tool-call-level detail. No thinking blocks. No execution trace.

### Strategy B: Browser extension + session page scraper (full)

A browser extension that:
1. Watches Slack web for Claude Tag messages
2. Detects "Open session in Claude" links
3. Opens the session page in a headless context (or user's browser session)
4. Parses the tool-call trace from the rendered page
5. Converts everything to AgentSON events

```
Browser extension watches Slack web
    ↓
Detects Claude Tag message with session link
    ↓
Opens session link (uses existing auth cookies from claude.ai)
    ↓
Parses the session page DOM for:
    • Tool calls (name, input, output, timing)
    • Thinking blocks
    • Error states
    • File operations
    ↓
Converts to AgentSON events with confirmed provenance
    ↓
Merges with Slack-message events via thread_id matching
```

**Pros:** Full tool-call-level detail. Complete execution trace. `confirmed` confidence.
**Cons:** Requires browser extension install. Depends on claude.ai page structure (fragile). Only works when user has claude.ai session active.

### Strategy C: Hybrid (recommended)

Use both together: Slack API listener for real-time message capture, browser extension for deep session scraping when a session link is detected.

```
Slack listener captures live messages
    ↓
When session link detected in thread
    ↓
Extension scrapes session page for full trace
    ↓
Both streams merged by thread_id + timestamp alignment
    ↓
Output: AgentSON with confirmed events from both sources
```

## Why this requires a browser extension (not just an API)

The session page on claude.ai is described as "read-only" and authenticated behind the user's claude.ai session. There is no documented API to retrieve session trace data programmatically.

A browser extension can:
- Leverage the user's existing claude.ai authentication (cookies)
- Parse the rendered session page for tool-call data
- Export to AgentSON format locally

This is the same pattern as the existing Cursor reader (which reads a local SQLite database that has no export API) — we're extracting data the vendor stores but doesn't expose via API.

## Comparison: Claude Tag reader vs. existing readers

| Reader | Data source | Resolution | Capture timing | Install complexity |
|---|---|---|---|---|
| Cursor | state.vscdb (SQLite) | Full tool calls | Post-hoc | None (file path) |
| Cline | api_conversation_history.json | Full tool calls | Post-hoc | None (file path) |
| Aider | .aider.chat.history.md | Messages only | Post-hoc | None (file path) |
| Claude Code | ~/.claude/projects/*.jsonl | Full tool calls | Post-hoc | None (file path) |
| **Claude Tag (Slack only)** | Slack Events API | Messages only | Live | OAuth setup |
| **Claude Tag (extension)** | claude.ai session page | Full tool calls | Live | Browser extension install |
| **Claude Tag (hybrid)** | Both | Full trace | Live | Both |

## Relationship to GDPR compliance model

Live capture via listener/extension is architecturally significant:

```
Forensic mode (post-hoc stitching of exports):
    GDPR Art. 15/20 → export artifacts → AgentSON reconstruction
    Gaps are explicit. No reasoning trace.

Narrative mode (post-hoc + SLM gap-filling):
    Forensic output + SLM proposes missing events
    Generated events labeled with confidence=ml_generated.

Live capture mode (contemporaneous intercept):
    No GDPR claim needed — user captures at the communication layer
    All events are confirmed. Reasoning intact.
    This is what AER prescribes as the only faithful method.
```

Live capture **sidesteps** the AER non-identifiability proof because capture happens at execution time, not post-hoc. This is the strongest mode for Claude Tag integration.

## Implementation considerations

### Extension permissions needed
- Host permission: `*.slack.com` (read channel messages)
- Host permission: `*.claude.ai` (read session page)
- Storage: local event queue before export
- No network request modification needed (read-only)

### Slack API listener permissions
- `channels:history` — read channel messages
- `groups:history` — read private channel messages (opt-in)
- `users:read` — map user IDs to names
- Events: `message.channels`, `message.groups`, `message.im`

### Session page parsing (fragile)
- claude.ai session page structure may change without notice
- Mitigation: use structured selectors + fallback to text extraction
- Consider contributing to Anthropic's feedback loop asking for structured export

## Open questions

1. **Session link format** — what URL pattern does "Open session in Claude" use? (Unknown until we see one)
2. **Session page structure** — is tool-call data rendered as structured HTML or as free-text markdown?
3. **Auth cookie lifetime** — do claude.ai session cookies survive for the duration of a Claude Tag session?
4. **Rate limits** — Slack Events API has rate limits; how many concurrent Claude Tag sessions can a workspace sustain?
5. **Slack bot token scope** — does the Claude Tag bot have a unique bot_id that's stable across workspaces?

## Immediate next step

The fastest path to validating this approach: build a CLI tool that takes a session URL from the user (they paste the "Open session in Claude" link) and scrapes the page. This works today without any extension — just requires the user to be logged into claude.ai. If that works, the extension is a convenience layer on top.

```
agentson import claude-tag --session-url "https://claude.ai/session/..."
```

## Sources

1. How Claude Tag works — official Anthropic documentation: https://claude.com/docs/claude-tag/concepts/how-it-works
2. How agent identity works: https://claude.com/docs/claude-tag/concepts/agent-identity
3. Security and data handling: https://claude.com/docs/claude-tag/concepts/security-and-data
4. Introducing Claude Tag (Anthropic blog): https://www.anthropic.com/news/introducing-claude-tag
5. Claude Tag per-thread sandbox architecture (Medium technical analysis): https://medium.com/@computeleap/claude-tag-how-the-per-thread-sandbox-works-agentconn-blog-fd4edc8db0c8
6. Claude Tag enterprise access model analysis: https://therouter.ai/news/claude-tag-enterprise-agent-access-model/
7. Slack Block Kit message format: https://api.slack.com/block-kit
8. Slack Events API: https://api.slack.com/events-api
9. AgentSON GDPR compliance model: issues/issue-gdpr-compliance-model.md
