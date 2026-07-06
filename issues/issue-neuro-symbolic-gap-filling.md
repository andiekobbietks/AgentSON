# Issue: Neuro-Symbolic Gap-Filling Architecture for AgentSON Reconstruction

## Summary

Use a small language model (SLM) to propose plausible intermediate events between confirmed anchors in an AgentSON execution graph, with deterministic verification to prevent hallucination. This transforms reconstruction from "gaps visible" (forensic mode) to "gaps filled, labeled" (narrative mode).

## Research basis

The idea is validated by converging results across multiple 2025-2026 papers:

### HunterAgent (most directly relevant)

arXiv 2605.29269, May 2026 — reframes trace reconstruction as "cost-bounded heuristic graph search under partial observability." Architecture:

- **Generator** (LLM): proposes semantic hypotheses within a typed ontology
- **Verifier** (deterministic): grounds each via identifier-level collisions on surviving orthogonal telemetry
- **Cost-bounded beam search**: scores hops combining semantic divergence and temporal potential
- **Epistemic budget**: cumulative cost threshold; breach triggers graceful halt, not fabrication

Results: 86.1% F1, hallucination cut from 61.5% to 6.4%. Under 70% log wiping, precision stays >=84%.

### Parallel research supporting the approach

| Paper | Approach | Relevance to AgentSON |
|---|---|---|
| **Execution Trace Reconstruction Using Diffusion Models** (ICSE 2025) | SSSDS4 diffusion model for incomplete trace sequences | Gap-filling event sequences is a recognized problem |
| **Particle smoothing with bi-LSTM** (arXiv 1905.05570) | Bidirectional continuous-time LSTM for missing event imputation | Temporal context from both directions improves gap-filling |
| **LESR — LLM Event Sequence Reconstruction** (JSW 2025) | Two-phase LLM: generate candidates, then select optimal | Candidate generation + selection pattern |
| **Process mining LLM log repair** (CIMS 2026) | Trace similarity + LLM with reflection to reduce hallucination | Reflection/consistency checks reduce hallucination |
| **Decision Trace Reconstructor** (GitHub 2026) | Per-property reconstructability matrices | Alternative: don't fill gaps, just classify them |

### Boundary condition (important)

The **Agent Execution Record (AER)** paper (arXiv 2603.21692) proves that **reasoning provenance** cannot be faithfully reconstructed post-hoc. But AgentSON's gap-filling targets **execution events** (what commands ran, in what order, with what I/O) — which is a sequence reconstruction problem, not a reasoning reconstruction problem. The tractability boundary is documented in `issue-gdpr-compliance-model.md`.

## Architecture

```
                ┌─────────────────────────┐
                │  AgentSON Event Graph   │
                │  (confirmed + inferred) │
                └──────────┬──────────────┘
                           │ identifies gaps
                           ▼
                ┌─────────────────────────┐
                │     Gap Detector        │
                │  finds disconnected     │
                │  subgraphs + missing     │
                │  event positions         │
                └──────────┬──────────────┘
                           │ each gap
                           ▼
        ┌────────────────────────────────────┐
        │          Generator (SLM)           │
        │  proposes candidate events for gap │
        │  given: anchor_before, anchor_after,│
        │         available metadata          │
        └──────────┬─────────────────────────┘
                   │ N candidates per gap
                   ▼
        ┌────────────────────────────────────┐
        │          Verifier                   │
        │  deterministic checks per candidate:│
        │  • Temporal feasibility            │
        │  • File path existence              │
        │  • Process tree consistency         │
        │  • Session state constraints         │
        │  • Schema compliance                │
        └──────────┬─────────────────────────┘
                   │ passed / failed
                   ▼
        ┌────────────────────────────────────┐
        │    Cost-Bounded Beam Search        │
        │  score = f(semantic_cost,           │
        │           temporal_cost,            │
        │           schema_violation=∞)       │
        │  beam width W, epistemic budget B  │
        └──────────┬─────────────────────────┘
                   │ best paths
                   ▼
        ┌────────────────────────────────────┐
        │    Confidence Assignment            │
        │  • verified + high score → estimate │
        │  • verified + low score → estimate │
        │  • unverifiable → ml_generated     │
        │  • budget exceeded → gap_marker     │
        └──────────┬─────────────────────────┘
                   │
                   ▼
        ┌────────────────────────────────────┐
        │   Merged AgentSON Event Graph      │
        │  (confirmed + inferred + generated)│
        └────────────────────────────────────┘
```

## Event types suitable for gap-filling

Only **execution events** are candidates. Reasoning events are explicitly excluded per AER non-identifiability.

| Event type | Gap-fillable | Verifier strategy |
|---|---|---|
| `tool_call` | Yes | Check tool existed, args well-formed, output plausible |
| `command_run` | Yes | Check binary exists in PATH, output consistent |
| `file_edit` | Yes | Check file path exists, diff is valid |
| `git_operation` | Yes | Check commit hash exists in log |
| `api_request` | Partial | Check endpoint known, response format valid |
| `assistant_response` | No | Would fabricate reasoning — excluded |
| `user_prompt` | No | Would fabricate intent — excluded |
| `internal_planning` | No | Reasoning provenance — excluded per AER |

## Verifier design (key to preventing hallucination)

The verifier is the critical component. Research shows hallucination reduction comes from the **verifier, not the generator**.

### Check types (ordered by strength)

1. **Identity collision** — strongest. Does the candidate event reference a file/process/PID that exists in confirmed events? (HunterAgent pattern)
2. **Temporal constraint** — does the candidate timestamp fall within the gap's bounds? Are duration constraints satisfied?
3. **Schema compliance** — does the candidate match the AgentSON event schema? Hard prune on violation.
4. **Domain constraint** — does the candidate violate known system behavior (e.g., cannot write to a read-only path)?
5. **Consistency check** — if multiple candidates exist for the same gap, do they agree?

### Hard vs. soft constraints

```
HARD PRUNE (score = ∞, candidate discarded):
  • Schema violation (missing required field, wrong type)
  • Temporal impossibility (timestamp before anchor_before)
  • Physical impossibility (file operation on nonexistent path)

SOFT COST (added to beam search cost function):
  • Semantic divergence from training distribution
  • Temporal distance from nearest anchor
  • Low consistency with alternative hypotheses
```

## SLM training strategy

Train on existing AgentSON event sequences from all 9+ readers.

### Training data

- Source: all existing `.AgentSON` example files and user-generated exports
- Task: given a prefix and suffix context, predict the missing event in the middle
- Augmentation: randomly mask out events from complete traces to create training gaps

### Model selection criteria

| Property | Requirement | Reason |
|---|---|---|
| Size | < 1B parameters | Must run locally, user-side |
| Context window | >= 4096 tokens | Enough for gap context |
| Inference speed | < 500ms per gap | Interactive CLI use |
| Open license | Apache 2.0 or MIT | Matches AgentSON license |
| Candidates: Phi-3-mini (3.8B), TinyLlama (1.1B), Gemma-2B, Qwen2.5-1.5B, or a tiny custom transformer trained from scratch on AgentSON event sequences. | | |

### Alternative: no training needed

HunterAgent demonstrates that the generator can work via **in-context prompting** (no fine-tuning required) — the prompt includes the typed ontology and available context. This means AgentSON could ship with narrative mode using a stock SLM + prompt template, while a fine-tuned model is a future optimization.

## Cost-bounded beam search

From HunterAgent: frame a path through the gap as a sequence of hypothesized events. Each path has cumulative cost.

### Cost function

```
C(path) = sum over hops of:
    hard_prune? INF : (w1 * semantic_divergence + w2 * temporal_cost)
```

- `semantic_divergence`: cosine distance from the candidate embedding to the distribution of known events of the same type
- `temporal_cost`: log-normal CDF of inter-event latency (calibrated from known events in the same session)
- Weights `w1`, `w2` calibrated on leave-one-out reconstruction of known events

### Beam search

- Beam width W = 5 (default)
- At each hop, expand each path with top-W candidates from the generator
- Prune hard violations immediately
- Score remaining paths, keep top-W lowest cost
- Continue until path reaches the anchor_after event

### Epistemic budget

- `B_max` = 99th percentile of reconstruction cost on clean (complete) traces
- If cumulative cost of all paths exceeds `B_max` → halt, mark gap as INSUFFICIENT_EVIDENCE
- Prevents "hallucination spirals" where the SLM generates increasingly speculative events to bridge a wide gap

## Confidence assignment

After gap-filling, each generated event receives a composite confidence:

| Verifier result | Cost percentile | Assigned confidence |
|---|---|---|
| All checks passed | < 50th | `estimated` |
| All checks passed | >= 50th | `ml_generated` |
| Soft constraint violated | any | `ml_generated` |
| Budget exceeded | — | `gap_marker` (not filled) |

## CLI integration

The gap-filler is activated via `--mode narrative` in `agentson reconstruct`:

```
agentson reconstruct --slack-export ./slack --claude-export ./claude \
  --mode narrative --model phi-3-mini --temperature 0.3 \
  --output session.ason
```

### Output format for generated events

```json
{
  "event_id": "evt-gap-003",
  "event_type": "tool_call",
  "source": "ml_generated",
  "provenance": {
    "confidence": "ml_generated",
    "generation_model": "phi-3-mini-4k-instruct",
    "generation_strategy": "generator_verifier_beam_search",
    "generation_context": {
      "anchor_before": "evt-012",
      "anchor_after": "evt-017",
      "verification_checks_passed": ["temporal", "schema", "domain"],
      "verification_checks_failed": [],
      "beam_cost": 0.42,
      "alternatives_considered": 3,
      "temperature": 0.3
    },
    "verifier": {
      "temporal_feasible": true,
      "file_path_exists": true,
      "schema_compliant": true,
      "domain_constraints_satisfied": true,
      "consistency_score": 0.87
    }
  },
  "timestamp": "2026-07-06T14:25:00Z",
  "timestamp_bounds": {
    "earliest_possible": "2026-07-06T14:24:30Z",
    "latest_possible": "2026-07-06T14:25:30Z"
  },
  "actor": "assistant",
  "content": "npm run build",
  "inferred_context": {
    "working_directory": "/home/user/project",
    "linked_session_id": "sess-004"
  }
}
```

## Relationship to existing documents

| Document | Relationship |
|---|---|
| `issue-gdpr-compliance-model.md` | Provides the compliance framework this architecture fits into. Gap-filling only applies in `--mode narrative`, which is not the default — forensic mode is the default for compliance use cases. |
| ADR-012 | Gap-filling is an extrinsic application (narrative mode), not a core spec concern. The core remains pure reconstruction. |
| ADR-010 | Gap-filling does not affect GDPR value prop — the legal right is about export, not about generated gap content. |

## Implementation roadmap

### Phase 1: Context-only gap marking (no ML)
- Detect gaps in the event graph
- Emit explicit `gap_marker` events with metadata about what is missing
- Ship in next release

### Phase 2: Simple heuristic gap-filling
- Fill trivial gaps (single missing event, fully determined by context)
- Rule-based only (e.g., "if before was git add and after was git commit, fill git commit -m")
- Confidence: `estimated`

### Phase 3: SLM gap-filling (opt-in)
- Integrate with `llama.cpp` / ONNX Runtime for local inference
- Generator–Verifier architecture as designed above
- Confidence: `ml_generated`
- Requires user to download a model (no bundled models)

### Phase 4: Distilled AgentSON-specific model
- Fine-tune a small transformer on AgentSON event sequences
- Reduced size, faster inference
- Can be bundled or auto-downloaded

## Risks and mitigations

| Risk | Likelihood | Mitigation |
|---|---|---|
| User treats generated events as fact | Medium | `ml_generated` label visible in all output formats. Forensic mode is default. |
| Hallucination creates plausible-sounding false events | Low with verifier | Verifier hard-prunes schema violations. Epistemic budget halts on uncertainty. |
| Model size makes CLI unwieldy | Medium | Start with stock models via `llama.cpp`. Phase 4 distills to tiny model. |
| Legal risk from generated content | Low | Narrative mode is opt-in, labeled, and explicitly not GDPR-compliance mode. |

## Open questions

1. **Beam width calibration** — what is the right W for typical AgentSON gap sizes (1-5 missing events)?
2. **Model selection** — Phi-3-mini vs TinyLlama vs custom tiny transformer — which gives best accuracy/size tradeoff?
3. **Training data sufficiency** — do existing AgentSON examples contain enough event sequence diversity to train a useful model?
4. **Threshold for epistemic budget** — should B_max be user-configurable or calibrated automatically per-session?

## Sources

1. HunterAgent — Neuro-symbolic trace reconstruction. arXiv 2605.29269. https://arxiv.org/abs/2605.29269
2. AER — Reasoning provenance non-identifiability. arXiv 2603.21692. https://arxiv.org/abs/2603.21692
3. Execution Trace Reconstruction Using Diffusion Models. ICSE 2025. https://doi.org/10.1109/icse55347.2025.00063
4. Particle smoothing for missing event imputation. arXiv 1905.05570. https://ar5iv.labs.arxiv.org/html/1905.05570
5. LESR — LLM-based Event Sequence Reconstruction. JSW 2025. https://doi.org/10.17706/jsw.20.2.95-109
6. Process mining LLM log repair. CIMS 2026. http://www.cims-journal.cn/EN/10.13196/j.cims.2025.BPM16
7. Decision Trace Reconstructor. GitHub 2026. https://github.com/governance-evidence/decision-trace-reconstructor
8. Evidence Tracing Survey. arXiv 2606.04990. https://arxiv.org/html/2606.04990v4
9. GDPR compliance model — AgentSON reconstruction layer. `issues/issue-gdpr-compliance-model.md`
