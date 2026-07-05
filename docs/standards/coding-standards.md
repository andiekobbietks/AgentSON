# Coding Standards

Non-negotiable rules for how I write code.

---

## No PII in Repo

**Never commit personal file paths, names, or identifiers.**

`C:\Users\LLM-Test\Documents\...` is PII. It reveals a username, a directory structure, potentially a real name. Replace with `~/...` equivalents.

**Rule:** Before any commit, grep for `C:\Users\` and replace with `~/`. Before any push, rewrite history if PII leaked.

**Why:** A public repo with PII is a security risk and a privacy violation. Even if the data seems harmless, it builds a profile.

---

## No Telemetry

**No phone-home, no analytics, no tracking.**

Not even "anonymous usage statistics." Not even "error reporting." If the user didn't explicitly opt in, don't send data anywhere.

**Rule:** No `requests.post`, no `fetch()` to external URLs, no beacon scripts, no tracking pixels.

**Why:** The user owns their data. That includes metadata about how they use the tool.

---

## Vendor Neutral

**Never depend on one company's API or format.**

If OpenAI shuts down tomorrow, AgentSON still works. If GitHub goes down, the CLI still works. If Supabase disappears, the local files still work.

**Rule:** Every external service is optional. Every core feature works offline.

**Why:** Vendor lock-in is the enemy of portability. The whole point of AgentSON is that it works everywhere.

---

## Single File Output

**One .AgentSON file = one complete session.**

No sidecar files, no database entries, no config dependencies. One file has everything: schema, entries, metadata, context.

**Rule:** If you need a second file to understand the first file, the format is broken.

**Why:** A single file can be emailed, shared, archived, version-controlled. Multiple files create sync problems.

---

## Minimal Dependencies

**If you can do it in 20 lines, don't import a library.**

Every dependency is a liability. It can be abandoned, hacked, or become incompatible. If the standard library does the job, use it.

**Rule:** Check if `json`, `sqlite3`, `pathlib`, `hashlib`, `re`, `datetime` can solve the problem before reaching for `pip install`.

**Why:** Dependencies are trust. Every `pip install` is trusting a stranger with your code.

---

## Test Against Real Data

**Synthetic test data lies. Real data tells the truth.**

Test fixtures should come from real sessions, not hand-crafted examples. Real data has edge cases, missing fields, weird encodings. Synthetic data is always clean.

**Rule:** Every reader must have at least one test fixture from a real export.

**Why:** If it works on clean data but breaks on real data, it doesn't work.

---

## Honest Labels

**If something is experimental, say so. If something is planned, say so.**

No feature should be presented as complete when it's not. Status badges exist for a reason.

**Rule:** Use `Done`, `Planned`, `Experimental`, or `Broken` on every feature card.

**Why:** Users make decisions based on what you tell them. Lying about readiness wastes their time.

---

## Commit Messages

**Write commits for humans, not machines.**

Format: `type(scope): description`

Types:
- `feat` — new feature
- `fix` — bug fix
- `docs` — documentation only
- `refactor` — code change that neither fixes a bug nor adds a feature
- `test` — adding tests
- `chore` — maintenance

**Rule:** The commit message should explain *why*, not just *what*.

**Example:**
```
feat(readers): chrome-devtools reader - parse MD exports to AgentSON

Closes a real gap in readers/: chrome-devtools was in the tool.name
enum but had no corresponding readers/chrome_devtools.py.
```

Not:
```
add chrome devtools reader
```

---

*These standards are not suggestions. They are the price of entry.*
