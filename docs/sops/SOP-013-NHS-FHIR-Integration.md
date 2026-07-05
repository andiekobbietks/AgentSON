# SOP-013: NHS FHIR Integration

**Version:** 1.0  
**Date:** 05 July 2026  
**Author:** Andrea Enning (AndieKobbieTech)

---

## Purpose

This SOP describes how to connect to NHS FHIR APIs for sharing glucose data with clinical systems.

---

## Prerequisites

| Item | Requirement |
|------|-------------|
| **Data** | Glucose data in AgentSON format |
| **Registration** | NHS Innovation Service (free) |
| **Approval** | May need ICB partnership |

---

## Current NHS FHIR Status

| Status | Detail |
|--------|--------|
| **Standard** | Under development (NHS 10-Year Plan) |
| **Patient-initiated** | Aligned with our project |
| **Access** | Requires NHS partnership or innovation registration |
| **Timeline** | 12-24 months to full availability |

---

## Procedure

### Step 1: Register with NHS Innovation Service

1. Go to https://www.nhsinnovationservice.nhs.uk
2. Register as innovator (free)
3. Submit project details
4. Wait for approval

### Step 2: Understand FHIR Resources

| Resource | What It Contains |
|----------|------------------|
| **Patient** | Patient demographics |
| **Observation** | Glucose readings |
| **Condition** | Diabetes diagnosis |
| **MedicationStatement** | Current medications |
| **DiagnosticReport** | Clinical reports |

### Step 3: Build FHIR Client (When Available)

```python
import requests

# FHIR base URL (when available)
FHIR_BASE = "https://fhir.nhs.uk/R4"

# Create Observation resource
observation = {
    "resourceType": "Observation",
    "status": "final",
    "category": [{
        "coding": [{
            "system": "http://terminology.hl7.org/CodeSystem/observation-category",
            "code": "laboratory"
        }]
    }],
    "code": {
        "coding": [{
            "system": "http://loinc.org",
            "code": "2345-7",
            "display": "Glucose [Mass/volume] in Serum or Plasma"
        }]
    },
    "subject": {"reference": "Patient/mother-id"},
    "valueQuantity": {
        "value": 9.33,
        "unit": "mmol/L"
    },
    "effectiveDateTime": "2026-07-05T12:00:00Z"
}

# POST to FHIR server (when available)
# response = requests.post(f"{FHIR_BASE}/Observation", json=observation)
```

### Step 4: Export FHIR Bundle

```python
def export_to_fhir(agentson_data):
    """Convert AgentSON glucose data to FHIR Bundle."""
    bundle = {
        "resourceType": "Bundle",
        "type": "collection",
        "entry": []
    }
    
    for entry in agentson_data["entries"]:
        if entry["type"] == "glucose_reading":
            fhir_obs = {
                "resourceType": "Observation",
                "status": "final",
                "code": {
                    "coding": [{
                        "system": "http://loinc.org",
                        "code": "2345-7",
                        "display": "Glucose"
                    }]
                },
                "valueQuantity": {
                    "value": entry["data"]["value"],
                    "unit": "mmol/L"
                },
                "effectiveDateTime": entry["timestamp"]
            }
            bundle["entry"].append({"resource": fhir_obs})
    
    return bundle
```

---

## What We Can Share Now

| Data | Format | How |
|------|--------|-----|
| **Glucose readings** | PDF/HTML | Email to GP |
| **Trends** | Chart image | Print for appointment |
| **AgentSON files** | JSON | Share with developers |

---

## What FHIR Will Enable

| Benefit | How |
|---------|-----|
| **Real-time sharing** | Automatic upload to clinical system |
| **GP visibility** | Doctor sees data in EMIS/SystmOne |
| **Hospital integration** | Consultant accesses during appointment |
| **Research** | Anonymised data for NHS research |

---

## Timeline

| Phase | When | What |
|-------|------|------|
| **Now** | Jul 2026 | Manual PDF/HTML reports |
| **Phase 1** | Q4 2026 | NHS Innovation Service registration |
| **Phase 2** | Q1 2027 | FHIR API access (when available) |
| **Phase 3** | Q2 2027 | Full clinical system integration |

---

## Alternative: Nightscout → NHS

Until FHIR is available:

1. **Export from Nightscout** → CSV/PDF
2. **Convert to AgentSON** → Structured data
3. **Generate report** → HTML/PDF
4. **Share with GP** → Email or in-person

---

## References

- NHS FHIR Implementation Guide: https://fhir.nhs.uk
- NHS 10-Year Plan: Digital health integration
- Patient-initiated data sharing: Under development
