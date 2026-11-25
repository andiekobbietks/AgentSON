# ADR-009: AgentSON as an Open Interchange Format for AI Workflows

**Status:** Accepted as product positioning; claims narrowed 25 November 2026  
**Date:** 05 July 2026

## Context

AI coding and agent tools expose different session records and export paths. Their storage formats, available fields and permissions vary. Users and researchers may want to retain, inspect or compare records across tools, but no common interchange contract is guaranteed.

The original ADR used absolute statements about the absence of alternatives and time-sensitive market claims. Those statements are not maintained as architecture evidence.

## Decision

Position AgentSON as an open, vendor-neutral interchange format for supported AI-agent session records.

The canonical v1.2 wire format is JSONL. Readers map source data into the event vocabulary and preserve provenance where available. Destination consumers are separate adapters with their own capability and safety requirements.

AgentSON is not a replacement for OpenTelemetry, APM, SIEM, native product observability, agent runtimes or source-native export facilities. It does not guarantee access to records a vendor does not expose, complete session capture, private reasoning capture, lossless conversion or arbitrary runtime resumption.

## Consequences

- Prefer local-first processing and keep hosted services optional for core archive work.
- Preserve source identity and make mapping loss visible.
- Do not claim that AgentSON is the only solution, that no vendor exports session data, or that all AI session data can be obtained.
- Do not make market-size, valuation or competitor claims without current, attributable evidence.
- Data portability is a technical capability; legal access rights remain context-dependent.
