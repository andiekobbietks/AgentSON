# Mental Models

How we think about problems before writing code.

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

A GTX 1050 with 2GB VRAM means no 7B models locally. That constraint drove fine-tuning smaller models, which led to better results on specific tasks than a general 7B model would give.

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

## Say What's Tested

**Never imply unearned confidence.**

If something is written but untested, say "written, untested." If it's tested against real data, say "tested against real data." If it's tested against synthetic fixtures, say "tested against synthetic fixtures."

**In practice:**
- README badges reflect actual test results
- Status labels match reality
- No aspirational claims

**The test:** Would a skeptic agree with your status label?
