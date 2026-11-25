# ADR-005: Nightscout as a Historical Domain Integration

**Status:** Accepted for the original domain-specific integration; not a core-format dependency  
**Date:** 04 July 2026  
**Clarified:** 25 November 2026

## Context

The early AgentSON prototype included continuous-glucose-monitoring data workflows. Nightscout provided an open, self-hostable API for exchanging data from compatible systems and was selected for that prototype.

## Decision

Retain Nightscout as an optional, historical domain-specific integration example. It must not be required by AgentSON Core or treated as a clinical service.

The integration does not establish that AgentSON is a medical device, clinical decision-support system or NHS-connected service. Any future NHS FHIR work would require a separately scoped design, security review, organisational approval and testing against the relevant interfaces.

## Consequences

- The core interchange format remains domain-neutral.
- Health data is sensitive personal data and must be minimised, protected and handled under the applicable legal and organisational controls.
- Do not infer clinical meaning or recommend treatment from imported data.
- Nightscout and Libre workflows are optional adapters/examples, not evidence of universal health-data interoperability.
