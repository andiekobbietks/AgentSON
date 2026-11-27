# AgentSON Project Charter

**Status:** Public project boundary and continuation guide  
**Canonical format:** See the versioned schemas under `spec/`  
**Implementation status:** Alpha; capabilities must be verified against the code and tests in this repository.

## Purpose

AgentSON is an open, vendor-neutral project for capturing, preserving, validating and exchanging structured records of AI-agent execution activity.

Its central concern is portability of operational history across tools and runtimes. The project should preserve source provenance and make transformations explicit rather than implying that every producer exposes the same information.

## Current scope

- Import and read supported agent-session sources.
- Represent supported records using the versioned AgentSON schema.
- Validate records and preserve relevant metadata.
- Provide local inspection, search and export capabilities where implemented.
- Document known limitations, data handling and compatibility.

A feature is implemented only when its code, tests and documentation demonstrate that it works. Roadmap entries, diagrams and examples are not evidence of implementation.

## Non-goals and boundaries

AgentSON is not, by itself:

- an agent runtime, orchestration platform or model provider;
- an identity provider or authorisation system;
- proof that an agent's output is correct or safe;
- a guarantee of complete capture from every runtime;
- a compliance certification or substitute for legal advice;
- a replacement for OpenTelemetry, MCP, A2A, ITSM or platform-native observability;
- a central service that users must depend on.

Integrations should complement established standards and tools. New protocol or schema surface area should be introduced only where a documented interoperability gap cannot be addressed adequately by an existing standard.

## Design principles

1. **Portability:** records should remain usable outside the system that produced them.
2. **Provenance:** preserve source identifiers and distinguish observed facts from inferred or transformed data.
3. **Explicit loss:** document information that cannot be captured, represented or safely exported.
4. **Versioning:** make schema evolution deliberate and test compatibility.
5. **Privacy:** collect and publish the minimum data necessary; treat prompts, outputs, paths, tokens and tool results as potentially sensitive.
6. **Security:** do not treat a valid signature, schema validation or successful import as proof of trustworthy behaviour.
7. **Interoperability:** prefer adapters to unnecessary replacement standards.
8. **Reproducibility:** connect claims to tests, examples, source references or clearly marked hypotheses.

## How to continue the project

Before implementing a significant change:

1. Read the current schema, ontology, relevant ADRs and tests.
2. Check open issues and the strategic roadmap.
3. Identify the user problem and the existing standards or formats involved.
4. Record material architectural decisions as ADRs.
5. Add fixtures and tests for both valid and invalid cases.
6. Update documentation and the changelog.
7. State what is implemented, experimental, proposed or deferred.

## Public disclosure boundary

This repository documents AgentSON's own purpose, format, implementation and evidence. Broader research into federated developer infrastructure and future products is maintained separately. Do not add unpublished architecture, credentials, private deployment details, customer information or speculative commercial plans here without an explicit project decision.

## Status vocabulary

- **Implemented:** present in the repository and covered by relevant tests.
- **Experimental:** present but unstable, incomplete or insufficiently validated.
- **Proposed:** design or roadmap only; not implemented.
- **Deferred:** intentionally postponed.
- **Deprecated:** retained for compatibility but not recommended for new use.

When uncertain, use the more conservative status.
