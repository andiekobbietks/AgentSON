# SOP-011: Research Outline for Health-Data Model Evaluation

**Status:** Experimental research outline; not a validated training or clinical procedure.  
**Last reviewed:** 25 November 2026

## Purpose

Describe a cautious research workflow for evaluating whether structured time-series exports can be used in a model experiment. The previous version incorrectly treated a JSONL .agentson stream as one JSON object and included unsupported clinical recommendations. Those examples are withdrawn.

## Data requirements

- Use synthetic data by default.
- Use real health data only where there is a documented lawful basis, informed permission where required, data minimisation, appropriate governance and secure handling.
- Do not upload identifiable health data to a cloud notebook or model provider without explicit approval.
- Do not treat a locally processed dataset as automatically GDPR-, HIPAA- or NHS-compliant.

## Export a time series

Use the installed CLI help to confirm the command supported by the installed version. The current example is:

~~~bash
agentson timeseries ./libre_libre_data.agentson --format csv
~~~

The canonical v1.2 archive is JSONL, not a single JSON object. Do not use json.load on the whole .agentson stream. Validate the archive first and inspect the generated CSV against the original source.

## Research workflow

1. Define a research question that does not ask the model to diagnose, prescribe or recommend medication.
2. Document the provenance, units, sampling frequency, missingness and transformations of the dataset.
3. Split data by participant and time to avoid leakage between training and evaluation.
4. Compare a simple statistical baseline before attempting fine-tuning.
5. Use a model version and training method permitted by the current model licence.
6. Evaluate calibration, robustness, subgroup performance and failure cases with qualified reviewers.
7. Publish limitations and do not generalise results beyond the tested data.

## Non-clinical boundary

A model trained or evaluated with this workflow is not a medical device and must not be used for diagnosis, treatment, medication adjustment or emergency monitoring. Any clinical use would require a separate clinical-safety, regulatory, privacy and organisational assessment.

This document does not provide a validated MedGemma fine-tuning script, does not claim clinical performance and does not certify regulatory compliance.
