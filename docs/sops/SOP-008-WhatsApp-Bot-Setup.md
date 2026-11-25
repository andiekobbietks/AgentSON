# SOP-008: Messaging and Voice-Alert Prototype

**Status:** Conceptual prototype only; not a validated health-alert service.  
**Last reviewed:** 25 November 2026

## Purpose

Record an early concept for generating spoken messages from user-approved data. This is not an operational deployment procedure.

## Safety and privacy boundary

- Do not use this prototype for diagnosis, treatment advice, medication decisions or emergency response.
- Do not send identifiable health data through unofficial WhatsApp Web automation or unapproved third-party services.
- Any messaging integration must use a currently supported, approved provider API, explicit recipient consent, appropriate data-processing terms and access controls.
- Do not assume that a phone number or WhatsApp account is an approved clinical contact channel.
- Alert thresholds must be set by the person and their healthcare professional; the example values in older drafts are withdrawn.
- A missed message, delayed network or failed TTS conversion must never be treated as proof that the person is safe.

## Conceptual architecture

A local data processor may create a message from a reviewed event. A separately approved messaging provider may deliver that message. The provider, retention, authentication, consent, audit and failure-handling model must be assessed before any implementation.

## Requirements before implementation

1. Use synthetic test data during development.
2. Validate every message with fluent speakers for the intended language and dialect.
3. Have any health-related wording reviewed by qualified healthcare professionals.
4. Record delivery failures and provide a safe fallback that does not depend on the messaging channel.
5. Complete privacy, security and organisational review before processing real health data.

No working WhatsApp integration or clinically validated alert logic is claimed by this SOP.
