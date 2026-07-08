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

**One .agentson file = one complete session.**

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

## Bug Response Procedure

**Finding a bug is not the same as fixing a bug. Do both, in this order, every time.**

1. **Prove it's real before saying it's real.** Reproduce it — run the failing case, don't just read the code and infer. A claim like "this looks like it could crash" is not a bug report until you've actually crashed it.
2. **Check if it's pre-existing.** `git stash` (or check `master` directly) and rerun. Matters for how it gets reported and whether it's something to just fix quietly or flag as a regression.
3. **Decide scope before touching code.** Is this a mechanical one-line fix, or does it reveal a design question (a missing spec field, a missing core command, a litmus-test violation)? Fix the former. Flag the latter and stop — don't unilaterally decide a spec change or scope call belongs to you.
4. **Fix it, then re-run the exact reproduction that found it.** "The code looks right now" is not verification. The same failing case from step 1 must now pass.
5. **Write or extend a real test**, using real data where available. If only synthetic data is available, say so explicitly rather than implying it's been verified against something real.
6. **Run pyrefly** on every file touched.
7. **State exactly what was tested vs. assumed.** No "should work now."
8. **CHANGELOG entry** naming the root cause, not just "fixed bug."
9. **Branch → PR.** Never push a fix directly to `master`, no matter how small.

**Rule:** If you can't point to the command that reproduced the bug and the command that proved the fix, you haven't finished — you've guessed.

**Why:** A bug "fixed" without reproduction is a bug hidden, not solved. This is the same discipline as "Test Against Real Data," applied to the moment a problem is found rather than only to the moment new code is written.

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
