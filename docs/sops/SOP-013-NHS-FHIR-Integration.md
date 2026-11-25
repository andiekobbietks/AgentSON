# SOP-013: NHS FHIR Integration — Proposed, Not Implemented

**Status:** Design note only; no working NHS FHIR integration is provided by AgentSON.  
**Last reviewed:** 25 November 2026

## Purpose

Record a possible future integration direction. This is not a procedure for connecting to NHS systems and must not be used to transmit patient data.

## Current status

- AgentSON does not provide an implemented NHS FHIR client through this SOP.
- No NHS partnership, API access, clinical-system approval or production endpoint is implied.
- Nightscout does not, by itself, provide NHS FHIR connectivity.
- The earlier timeline, access claims and code samples using placeholder patient identifiers are withdrawn.

## Requirements before any implementation

A future project would need, at minimum:

1. A defined NHS service and current implementation guide.
2. Confirmation of the organisation's eligibility, registration and access route.
3. A documented controller/processor and lawful-basis assessment.
4. Privacy impact assessment, data minimisation and retention rules.
5. Authentication, authorisation, TLS, audit logging and secret management.
6. Clinical-safety and information-governance review where applicable.
7. A validated mapping from AgentSON events to the required FHIR resources and profiles.
8. Synthetic test fixtures and approved end-to-end testing before any real data is used.

## Format mapping

AgentSON v1.2 archives are JSONL event streams. A future FHIR mapping must read the stream event-by-event, preserve provenance and explicitly report unmapped fields. The previous examples that treated .agentson as a single JSON object or used a placeholder patient identifier must not be reused.

## References

Consult current official NHS England and FHIR implementation documentation before proposing an integration. No endpoint, access timeline or approval outcome is asserted here.
