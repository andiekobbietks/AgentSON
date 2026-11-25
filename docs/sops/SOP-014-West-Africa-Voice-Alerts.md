# SOP-014: Multilingual Voice-Alert Concept

**Status:** Research concept only; not a validated language or health-alert system.  
**Last reviewed:** 25 November 2026

## Purpose

Record a research idea for accessible voice interfaces in multiple West African languages. The previous version used unvalidated translations and a Turkish language code as a proxy for Twi; those examples are withdrawn and must not be used.

## Current limitations

- No validated Twi, Ga, Ewe, Yoruba, Igbo or Hausa alert model is established by this repository.
- A multilingual TTS model's language selector does not prove accurate pronunciation, translation or clinical meaning.
- No prevalence, mobile-penetration or access statistic is maintained by this SOP.
- No WhatsApp/SMS delivery service or clinically validated alert threshold is provided here.

## Requirements before implementation

1. Work with fluent native speakers for each language and dialect.
2. Have all translations independently reviewed and tested with intended users.
3. Have any health-related wording reviewed by qualified healthcare professionals.
4. Use synthetic data in development and obtain appropriate approvals before processing real health data.
5. Provide clear failure states, consent, opt-out, delivery audit and a non-digital fallback.
6. Never present a voice message as diagnosis, treatment, medication advice or emergency response.

## Safety boundary

This concept must not be used as the sole monitoring or alerting mechanism. No user should rely on an unvalidated voice model or messaging service for urgent medical decisions.
