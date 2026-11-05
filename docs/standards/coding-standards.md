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

**No unsolicited telemetry, analytics, tracking or error reporting.**

Do not collect or transmit usage/session data for the maintainer or a third party without explicit, informed user opt-in. Core archive operations must not phone home.

**Rule:** No hidden analytics, tracking pixels, beacons or background uploads. Network access required for a user-requested source integration, update check or explicitly enabled hosted feature is not telemetry by itself; it must be documented, scoped to that action and disclose what data leaves the device. Do not send session content to an external service merely because a user opened or inspected an archive.

**Why:** Users own their session data and must understand and control every external disclosure.

---

## Vendor Neutral

**The canonical model and archive must not depend on one company's API or format.**

The canonical archive must remain readable and inspectable without the originating vendor runtime or a hosted AgentSON service. Individual source adapters may depend on a source application's local database or an explicitly authorised API; those dependencies must be declared per adapter.

**Rule:** External services are optional to the core archive. Core parse, validate and inspect operations must work offline. Source-specific capture may require the source application or service and must disclose that requirement.

**Why:** Vendor lock-in is the enemy of portability. The archive must outlive any one harness or provider.

---

## Single File Output

**One canonical .agentson archive = one independently readable session record.**

The archive contains its session envelope, ordered entries and the metadata needed to interpret the recorded session. It must not depend on a hidden database, config file or service. Large or separately governed artefacts may be external references only when explicit and integrity-verifiable; the archive must report when an artefact is unavailable.

**Rule:** A recipient must be able to parse and inspect the session record from the archive alone. External infrastructure must never be a hidden dependency.

**Why:** A self-contained archive can be transferred, shared, archived and version-controlled without silently losing its meaning.

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

## Privacy-Safe Test Data

Real exports are important for reader fidelity, but raw sessions must never be committed by default. Prompts, code, file paths, tool output, URLs, account identifiers and credentials may contain personal or confidential data.

**Rule:** Keep raw real exports outside the public repository unless the data owner has explicitly approved publication and a documented review confirms that disclosure is safe. Prefer a sanitised, provenance-labelled fixture derived from a real export. Record the sanitisation method and what was changed. Synthetic fixtures remain useful for edge cases, but must be labelled synthetic and must not be presented as real-world evidence.

**Why:** Real-data coverage must not become a route for publishing secrets or personal data.

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


## Interoperability and Honest Claims

- Do not describe an adapter as cross-harness compatible merely because it can export or parse a session.
- Report semantic loss, unavailable source data, redactions and unsupported event types.
- Distinguish capture, portability, reconstruction and resumption.
- Imported session content is untrusted; inspection must not execute commands or tool calls.
- Link claims such as 'working', 'validated', 'reconstructable' or 'resumable' to the exact implementation and tests that support them.
- Treat the canonical session archive as the v1.2 JSON envelope defined by spec/v1.2.json; JSONL stream code is a separate interface until it has its own contract.
