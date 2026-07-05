# Issue: Add "Intrinsic Before Extrinsic" design principle

## Summary

Codify a design principle that prevents the AgentSON core specification from accumulating application-specific concerns. The four intrinsic properties of an AgentSON episode are:

1. **Fidelity** — does it accurately represent what happened?
2. **Portability** — can it move between systems?
3. **Replayability** — can the execution be reconstructed?
4. **Analyzability** — can humans and software inspect it?

Everything else (fine-tuning, analytics, compliance, dashboards, archives, search, benchmarking) is an **extrinsic use** of the artifact, not a property of it.

## Proposed addition

Add to `docs/standards/` (or a new `DESIGN-PRINCIPLES.md`):

```
Design Principle — Intrinsic Before Extrinsic

AgentSON Core SHALL evolve only to improve the intrinsic properties of an execution episode:

  fidelity,
  portability,
  replayability,
  analyzability.

Applications that consume AgentSON (training, archives, dashboards, analytics,
compliance, benchmarking, etc.) are intentionally outside the core specification.
Their ability to exist is a consequence of the specification, not its purpose.
```

## Why this matters

This gives a clear test for new feature proposals:

> "Does this change improve one of the four intrinsic properties?"

- If yes → candidate for core
- If no → belongs in a downstream package, plugin, or application

## Analogies

| Standard | What it doesn't know about |
|----------|--------------------------|
| Git | Pull requests |
| PDF | E-signatures |
| OpenTelemetry | Dashboards |
| PCAP | Intrusion detection |
| **AgentSON** | Fine-tuning, analytics, compliance |

## Suggested ADR

ADR-012: Intrinsic Before Extrinsic — a constitutional rule for the AgentSON specification.

## Related

- ADR-001: Why AgentSON Exists
- ADR-004: Amber Design Tokens
- ADR-010: GDPR/EU AI Act Data Liberation
- ADR-011: Naming Change (agenson → AgentSON)
