# ADR-002: Why a Portable JSONL Stream Is the Interchange Layer

**Status:** Accepted; wording clarified 25 November 2026  
**Date:** 04 July 2026

## Context

Agent tools commonly use local databases, JSON files, logs or product-specific APIs to store session activity. Replacing those source stores is not AgentSON's purpose. A portable interchange representation should be readable without requiring the original vendor database or a hosted AgentSON service.

The original title, "JSON files over SQLite", could be read as a recommendation to replace source databases with JSON documents. That is not the architecture decision.

## Decision

Use a versioned JSON-based event stream as the interchange boundary, while allowing source readers to extract from SQLite and other source-native stores.

The canonical v1.2 wire representation is JSONL: one event per line, with stream-meta first, using the .agentson extension. Individual events are validated against spec/v1.2-entries.json. The JSON session envelope in spec/v1.2.json remains a supported materialised/document representation.

AgentSON does not require vendors or users to replace their internal databases.

## Consequences

- Source databases remain source-of-truth stores for their applications.
- Readers are version-specific adapters and must document access and fidelity limits.
- Exported streams can be inspected and validated independently of the source database.
- A portable file does not imply complete capture or lossless conversion.
- Core archive validation and inspection should remain usable locally; optional network integrations may require connectivity.
