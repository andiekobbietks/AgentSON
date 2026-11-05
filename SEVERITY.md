# AgentSON Severity and Risk Classification Specification

**Version:** 1.0.0  
**Schema:** `spec/severity/v1.json`  
**Status:** Draft  
**Date:** 2026-11-04

---

## 1. Scope

This specification defines an AgentSON-wide vocabulary for severity, priority,
confidence, status and finding categories. It applies to:

* CLI reports and exporters (`agentson_platform`, `cli/grc_export.py`)
* Reader output and derived findings
* MCP and browser-adapter diagnostics
* Assurance and audit reporting

It does **not** modify the 12 event primitives in `spec/ontology.md`. Severity
is an assessment of evidence, not a property of raw events.

## 2. Design principles

1. **Four separate dimensions.** Severity, priority, confidence and status are
   never conflated.
2. **Stable identifiers.** Severity uses `SEV-1`..`SEV-5` machine-readable
   values; priority uses `P0`..`P4`.
3. **Categories are not severity levels.** `security` can be SEV-1 or SEV-5
   depending on impact and evidence.
4. **Evidence-derived.** An assessment references event IDs, sessions and
   offsets. It never edits the original JSONL stream.
5. **Method-visible.** Every assessment records whether it was produced by a
   deterministic rule, an established scoring model, AI-assisted classification
   or human approval.
6. **Versioned and auditable.** `schema_version` and `assessed_at` record the
   contract version and timestamp. `assessed_by` is required on every
   assessment. `rule_id` is required whenever `method` is `rule` or
   `scoring_model`, so the assessment names the rule or model that produced it.
7. **Not AI-only.** Severity must never depend exclusively on AI judgement.

## 3. Severity levels

| Identifier | Label | Meaning |
|------------|-------|---------|
| `SEV-1` | Critical | Catastrophic impact, active compromise, major data loss or system-wide failure |
| `SEV-2` | High | Significant security, integrity, availability or operational impact |
| `SEV-3` | Medium | Material defect with limited scope or a viable workaround |
| `SEV-4` | Low | Minor defect, inconvenience or non-critical degradation |
| `SEV-5` | Informational | Observation, improvement opportunity or non-impacting condition |

`level` is the stable value. `label` must match `level`.

## 4. Priority levels

| Identifier | Label | Response expectation |
|------------|-------|----------------------|
| `P0` | Emergency | Interrupt current work; immediate response |
| `P1` | High | Same sprint / same day |
| `P2` | Medium | Next sprint |
| `P3` | Low | Backlog, addressed when convenient |
| `P4` | Deferred | Track only; no planned action |

## 5. Confidence levels

| Level | Meaning |
|-------|---------|
| `confirmed` | Directly observed or reproducible |
| `inferred` | Reasoned from indirect evidence |
| `estimated` | Approximated from incomplete data |
| `ml_generated` | Produced by an ML classifier |
| `high` | Strong evidence, minor assumptions (scoring model) |
| `medium` | Some evidence, several assumptions (scoring model) |
| `low` | Weak evidence, many assumptions (scoring model) |
| `unknown` | No usable evidence |

`confirmed`, `inferred`, `estimated`, `ml_generated` and `unknown` are the
`provenance.confidence` values in `spec/ontology.md`. The assessment model keeps
all five and adds `high`/`medium`/`low` for scoring-model output.

## 6. Status lifecycle

| Status | Meaning |
|--------|---------|
| `detected` | Found by a rule, model or human review |
| `triaged` | Reviewed and routed |
| `accepted` | Risk accepted without immediate action |
| `in_progress` | Remediation active |
| `resolved` | Fix applied |
| `verified` | Fix confirmed with evidence |
| `dismissed` | Determined to be false positive or out of scope |

## 7. Categories

| Category | Evaluates | Example |
|----------|-----------|---------|
| `security` | Authentication, authorisation, exploitation | Exposed credentials |
| `privacy` | Personal data exposure | Sensitive data in logs |
| `data_integrity` | Accuracy and consistency | Corrupted event sequence |
| `availability` | Service accessibility | Agent execution failure |
| `reliability` | Repeatability and stability | Repeated tool failures |
| `correctness` | Whether an agent did the right thing | Incorrect tool selection |
| `safety` | Potential harmful outcomes | Unsafe autonomous action |
| `compliance` | Policy and regulatory requirements | Missing audit evidence |
| `supply_chain` | Dependencies and provenance | Unverified package |
| `performance` | Resource consumption and latency | Excessive inference latency |
| `compatibility` | Interoperability | Invalid MCP payload |
| `maintainability` | Technical debt and architectural quality | Duplicated validation logic |

## 8. Assessment object

A ``FindingAssessment`` is a versioned object that can be stored in a derived
index, embedded in a report, or carried as a separate assessment stream. It
does **not** modify the original `.agentson` JSONL events.

```json
{
  "schema_version": "agentson.severity.v1",
  "severity": {
    "level": "SEV-2",
    "label": "High",
    "category": "security"
  },
  "priority": "P1",
  "confidence": {
    "level": "confirmed",
    "score": 0.98,
    "source": "provenance.confidence"
  },
  "status": "detected",
  "impact": {
    "scope": "single_session",
    "dimensions": ["confidentiality", "integrity"],
    "description": "Agent attempted to access an unauthorised resource."
  },
  "evidence": {
    "event_ids": ["evt_001", "evt_002"],
    "session_ids": ["sess_abc123"],
    "start_offset": 142,
    "end_offset": 189,
    "excerpt": "DELETE /admin/users/..."
  },
  "method": "rule",
  "assessed_at": "2026-11-04T17:00:00Z",
  "assessed_by": "agentson_platform.classifier",
  "rule_id": "authz-failure-001",
  "rationale": "Authorisation failure followed by retry on a privileged endpoint.",
  "overrides": null
}
```

### Required fields

* `severity` (`level`, `label`, `category`)
* `priority`
* `confidence` (`level` required; `score` optional)
* `status`
* `impact` (`scope` required; `dimensions` optional)
* `evidence` (required object; `event_ids` defaults to an empty list)
* `method`
* `assessed_by` — the classifier, model or human assessor that produced the
  assessment; must be a non-empty identifier

The following fields have safe defaults and are therefore not required by the
JSON Schema:

* `schema_version` — defaults to `agentson.severity.v1`
* `assessed_at` — defaults to the current UTC timestamp; must be an
  offset-aware ISO 8601 date-time

One field is conditionally required:

* `rule_id` — required when `method` is `rule` or `scoring_model`; optional for
  `ai_assisted` and `human_approval`

### Evidence reference

`evidence.event_ids` links the assessment to the original events. `event_ids`
are preferred over offsets because sessions can be reconstructed or reindexed.
Offsets are kept for display convenience only.

### Method

Allowed values:

* `rule` — deterministic rule for known critical conditions
* `scoring_model` — established scoring model (e.g., CVSS, custom risk score)
* `ai_assisted` — AI-assisted classification for ambiguous evidence
* `human_approval` — human approval, override or risk acceptance

### Overrides

When a human overrides an assessment, `overrides` must be either absent or
`null`, or an object that contains at least `reason` and `approved_by` (both
non-empty). An empty object is not a recorded override. A non-empty `overrides`
object should contain:

```json
{
  "previous_severity": {"level": "SEV-2", "label": "High", "category": "security"},
  "reason": "Evidence shows the request was rejected before any data was accessed.",
  "approved_by": "security@example.com",
  "approved_at": "2026-11-04T18:00:00Z"
}
```

## 9. Relationship to AgentSON primitives

* An `action` with `status: error` is evidence.
* A `FindingAssessment` is an interpretation of one or more events.
* `Severity` is an assessment of that interpretation.

Example lifecycle:

1. `tool_selected` — agent selects an MCP tool.
2. `tool_called` — agent attempts execution.
3. `tool_error` — tool returns an authorisation failure.
4. `retry` — agent attempts another execution.
5. `recovery` — agent recovers.
6. `outcome` — final state recorded.

A classifier correlates these events and produces a `FindingAssessment` that
distinguishes a genuine security concern from a harmless rejected request.

## 10. Standards alignment

This specification is informed by, but does not copy, the following frameworks:

| Standard | What AgentSON borrows |
|----------|----------------------|
| CVSS | Impact/exploitability vocabulary for security findings |
| OWASP ASVS | Security requirement categories |
| NIST SP 800-61 | Incident classification and response lifecycle |
| ITIL 4 | Impact, urgency and priority separation |
| ISO/IEC 27001 | Information security risk management process |
| OWASP Top 10 for LLM Applications | AI-specific threat categories |

## 11. Migration from existing severity strings

Current code uses loose severity strings:

| Existing | Maps to | Notes |
|----------|---------|-------|
| `critical` | `SEV-1` / Critical | |
| `high` | `SEV-2` / High | |
| `medium` | `SEV-3` / Medium | |
| `low` | `SEV-4` / Low | |
| `info` / `informational` | `SEV-5` / Informational | e.g., `readers/gemini.py` |

`agentson_platform/digest.py` currently defines `SEVERITIES = ("critical",
"high", "medium", "low")`. New platform code should emit `FindingAssessment`
objects; legacy consumers can map the `level` field back to the old strings.

## 12. Versioning

* The model version is `agentson.severity.v1`.
* The JSON Schema is `spec/severity/v1.json`.
* A new version is required when a required field is added, removed or
  re-typed, or when an enum value changes meaning.
* Adding enum values is a minor change within the same major version only if
  the schema is already designed to accept them; otherwise it requires a new
  version.

## 13. Files

| File | Purpose |
|------|---------|
| `SEVERITY.md` | This specification |
| `agentson_platform/severity/v1.py` | Reference Pydantic model |
| `agentson_platform/severity/__init__.py` | Public import alias |
| `spec/severity/v1.json` | JSON Schema 2020-12 |
| `tests/test_severity.py` | Model and schema tests |
| `tests/fixtures/severity/*.json` | Valid and edge-case fixtures |
