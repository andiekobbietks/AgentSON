# Mental Models

How I think about problems before I write code.

---

## Simplicity First

**The simplest solution that works is the best solution.**

If you can solve a problem with a 20-line Python script, don't build a microservice. If a JSON file does the job, don't reach for a database. Complexity is a cost, not a feature.

**In practice:**
- AgentSON is a JSON file, not a database
- The viewer is a single HTML file, no build step
- The CLI is a flat Python module, no framework

**The test:** Can you explain the solution to someone in 2 sentences? If not, it's too complex.

---

## Own Your Data

**Never depend on a vendor for something you can store yourself.**

If your glucose data lives in Dexcom's cloud, you don't own it. If your session history lives in OpenAI's servers, you don't own it. If the company shuts down, your data disappears.

**In practice:**
- .AgentSON files live on your machine
- Nightscout is self-hosted
- No account required for anything

**The test:** If the internet goes down for a week, can you still access everything you need?

---

## Build to Learn

**Build things to understand them, not just to use them.**

The Chrome DevTools reader exists because I wanted to understand how Chrome stores AI assistance history. The glucose reader exists because I wanted to understand how FreeStyle Libre data is structured. Building teaches better than reading documentation.

**In practice:**
- Write the parser yourself before using a library
- Read the SQLite schema yourself before using an ORM
- Understand the format before building the tool

**The test:** Can you explain how it works under the hood, not just how to use it?

---

## Constraint-Driven

**Limitations are features, not bugs.**

I have a GTX 1050 with 2GB VRAM. That means I can't run 7B models locally. That constraint drove me to fine-tuning smaller models, which led to better results on specific tasks than a general 7B model would give.

**In practice:**
- £0 build budget → everything must be free or self-hosted
- 2GB VRAM → quantized models, distillation, API fallback
- Limited time → single-file solutions, no build pipelines

**The test:** Would this solution still work on a 5-year-old laptop with no internet?

---

## One File, One Truth

**A single file should contain everything needed.**

A .AgentSON file has the schema, the entries, the metadata, the context. You don't need a database, a config file, and a log. One file. One truth.

**In practice:**
- One .AgentSON = one complete session
- One SOP = one complete procedure
- One HTML file = one complete viewer

**The test:** Can you send someone one file and have everything they need?

---

## Transparency Over Polish

**Honest documentation beats marketing.**

If something is experimental, say so. If something doesn't work yet, label it "Planned." If there's a known limitation, document it. Users trust honesty more than polish.

**In practice:**
- Status badges on every feature (Done / Planned / Experimental)
- CHANGELOG tracks what changed and why
- ADRs explain why decisions were made, not just what was decided

**The test:** Would a new contributor understand the project's state in 5 minutes?

---

## The Carer Test

**If my mother's carer can't use it, it doesn't work.**

All the technical sophistication in the world means nothing if the person who needs it can't operate it. The TV dashboard, the WhatsApp alerts, the voice notifications — they exist because the end user is a busy carer, not a developer.

**In practice:**
- TV dashboard: no login, no config, just works
- WhatsApp: send a message, get a response
- Voice alerts: no app required, just a phone call

**The test:** Can someone who has never seen the code use the tool without reading documentation?

---

*These models are not rules. They are lenses. Use them to evaluate decisions, not to constrain creativity.*
