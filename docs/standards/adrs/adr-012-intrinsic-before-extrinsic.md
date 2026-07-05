# ADR-012: Intrinsic Before Extrinsic

**Status:** Proposed
**Date:** 05 July 2026
**Author:** Andrea Enning

---

## Context

As AgentSON grows, there is a risk of accumulating application-specific concerns into the core specification. Features like fine-tuning export, analytics, compliance, and dashboards are valuable — but they are **uses** of the artifact, not **properties** of it.

Without a clear boundary, the specification could become a kitchen sink that tries to serve every use case, diluting its focus and making it harder to implement.

## Decision

AgentSON Core SHALL evolve only to improve the **intrinsic properties** of an execution episode:

1. **Fidelity** — does it accurately represent what happened?
2. **Portability** — can it move between systems?
3. **Replayability** — can the execution be reconstructed?
4. **Analyzability** — can humans and software inspect it?

Applications that consume AgentSON (training, archives, dashboards, analytics, compliance, benchmarking, etc.) are intentionally **outside** the core specification. Their ability to exist is a consequence of the specification, not its purpose.

## The Architecture

```
                    AgentSON Core

         Fidelity
             │
         Portability
             │
        Replayability
             │
        Analyzability
             │
             ▼

        Stable Execution Record

             ▼

        Everything Else

    • Fine-tuning
    • Compliance
    • Search
    • Replay UI
    • Archives
    • Benchmarks
    • Analytics
```

Every downstream application depends on the core. The core depends on none of them.

## Test for New Features

When proposing a new feature, ask:

> "Does this change improve one of the four intrinsic properties?"

- **If yes** → candidate for the core
- **If no** → belongs in a downstream package, plugin, or application

## Analogies

| Standard | What it doesn't know about |
|----------|--------------------------|
| Git | Pull requests |
| PDF | E-signatures |
| OpenTelemetry | Dashboards |
| PCAP | Intrusion detection |
| **AgentSON** | Fine-tuning, analytics, compliance |

## Consequences

### Positive
- Clean separation of concerns
- Specification stays focused and minimal
- Downstream tools can innovate freely
- Easy to evaluate new feature proposals

### Negative
- Some features that could be in the spec will live in packages
- Users need to assemble their own toolchain

### Neutral
- The boundary is explicit and documented
- Can be revisited if the ecosystem demands convergence
