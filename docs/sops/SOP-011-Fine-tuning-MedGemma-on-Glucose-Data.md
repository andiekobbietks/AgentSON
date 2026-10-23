# SOP-011: Fine-tuning MedGemma on Glucose Data

**Version:** 1.0  
**Date:** 05 July 2026  
**Author:** Andrea Enning (AndieKobbieTech)

---

## Purpose

This SOP describes how to fine-tune MedGemma on glucose data to create a custom model for predicting glucose patterns and generating clinical insights.

---

## Prerequisites

| Item | Requirement |
|------|-------------|
| **Software** | Python 3.12.3, MedGemma (SOP-010) |
| **Data** | `libre_data.csv` or `.agentson` glucose files |
| **Hardware** | GPU recommended (or Google Colab free tier) |

---

## Procedure

### Step 1: Prepare Training Data

Convert glucose data to MedGemma format:

```python
import json
from datetime import datetime, timezone

training_data = []

# Read AgentSON glucose file (v1.2: readings are `observation` entries)
with open("libre_libre_data.agentson", "r", encoding="utf-8") as f:
    data = json.load(f)

# Convert to training format.
# v1.2 uses `type: "observation"` for sensor readings (not
# "glucose_reading"). Filter on source + numeric value instead.
for entry in data.get("entries", []):
    d = entry.get("data") or {}
    if entry.get("source") != "sensor":
        continue
    if not isinstance(d.get("value"), (int, float)):
        continue

    # Timestamp is integer ms in v1.2; render as ISO for the prompt.
    ts_ms = entry.get("timestamp")
    if isinstance(ts_ms, (int, float)):
        ts_iso = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc).isoformat()
    else:
        ts_iso = str(ts_ms)

    labels = entry.get("labels") or {}
    status = entry.get("status", "unknown")
    reading_type = d.get("reading_type", "CGM")
    provenance = entry.get("provenance") or {}

    training_data.append({
        "input": (
            f"Glucose reading at {ts_iso}: {d['value']} {d.get('unit', 'mmol/L')} "
            f"(source: {reading_type}, provenance: {provenance.get('confidence', 'unknown')})"
        ),
        "output": (
            f"Status: {status}. "
            f"Pattern: {labels.get('pattern', 'unlabelled')}. "
            f"Hypo risk (2h): {labels.get('hypo_risk_2h', 'unknown')}. "
            + ("Normal range." if status == "normal" else "Attention required.")
        ),
    })

# Save training data
with open("glucose_training_data.json", "w", encoding="utf-8") as f:
    json.dump(training_data, f, indent=2)
```

> **Note:** for time-series foundation models (GlucoFM, Chronos-2, GluFormer, ...),
> export a flat series instead with:
> `agentson timeseries libre_libre_data.agentson --format csv`

### Step 2: Fine-tune with LoRA

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import LoraConfig, get_peft_model

# Load base model
model = AutoModelForCausalLM.from_pretrained("google/medgemma-4b")
tokenizer = AutoTokenizer.from_pretrained("google/medgemma-4b")

# Configure LoRA
lora_config = LoraConfig(
    r=16,
    lora_alpha=32,
    target_modules=["q_proj", "v_proj"],
    lora_dropout=0.1,
    bias="none",
    task_type="CAUSAL_LM"
)

# Apply LoRA
model = get_peft_model(model, lora_config)

# Train on glucose data
# (Use Hugging Face Trainer or custom training loop)
```

### Step 3: Test Fine-tuned Model

```python
# Test with new glucose data
prompt = "Patient glucose at 08:00: 4.2 mmol/L, 12:00: 8.5 mmol/L, 16:00: 12.3 mmol/L. Analyze pattern."

# Model should respond with:
# "Glucose is rising throughout the day. Pattern suggests post-meal spikes.
#  Consider adjusting meal timing or medication. Monitor for hyperglycemia."
```

### Step 4: Export Model

```python
# Save fine-tuned model
model.save_pretrained("./medgemma-glucose-finetuned")
tokenizer.save_pretrained("./medgemma-glucose-finetuned")
```

---

## Use Cases

| Use Case | Input | Output |
|----------|-------|--------|
| **Pattern detection** | Glucose history | Trend analysis |
| **Hypo prediction** | Current readings | Risk assessment |
| **Meal impact** | Pre/post meal readings | Food recommendations |
| **Medication adjustment** | Glucose + medication log | Dosage suggestions |

---

## Important Notes

| Note | Detail |
|------|--------|
| **Not for diagnosis** | Model provides insights, not medical advice |
| **Validation required** | Test thoroughly before clinical use |
| **HIPAA compliant** | Keep data local, don't upload to cloud |
| **NHS approval** | May need MHRA approval for clinical use |

---

## Next Steps

After fine-tuning, proceed to:
- **SOP-008**: WhatsApp Bot Setup (integrate model)
- **SOP-009**: TV Dashboard Setup (display predictions)
