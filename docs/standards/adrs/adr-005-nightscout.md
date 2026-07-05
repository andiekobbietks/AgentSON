# ADR-005: Why Nightscout Over Proprietary CGM Systems

**Status:** Accepted
**Date:** 04 July 2026
**Author:** Andrea Enning

---

## Context

My mother uses a FreeStyle Libre 2 continuous glucose monitor. Abbott's proprietary system stores data in their cloud, requires their app, and charges subscription fees. For a carer on Universal Credit, this is not sustainable.

## Decision

Self-host Nightscout as the glucose data platform.

## Consequences

### Positive
- Free (runs on a £35 Raspberry Pi)
- Data stays on our hardware
- No subscription fees
- Custom alerts (WhatsApp, SMS, voice)
- Works with multiple sensors and apps (Juggluco, xDrip+)

### Negative
- Requires initial setup and maintenance
- No official support from Abbott
- Self-hosted = we handle outages

### Neutral
- Nightscout is the standard in the DIY CGM community
- Data can be exported to AgentSON for analysis
- NHS FHIR integration possible through Nightscout API
