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
| **Data** | `libre_data.csv` or `.AgentSON` glucose files |
| **Hardware** | GPU recommended (or Google Colab free tier) |

---

## Procedure

### Step 1: Prepare Training Data

Convert glucose data to MedGemma format:

```python
import json

training_data = []

# Read AgentSON glucose file
with open("libre_libre_data.AgentSON", "r") as f:
    data = json.load(f)

# Convert to training format
for entry in data["entries"]:
    if entry["type"] == "glucose_reading":
        training_data.append({
            "input": f"Glucose reading at {entry['timestamp']}: {entry['data']['value']} mmol/L",
            "output": f"Status: {entry['status']}. {'Normal range.' if entry['status'] == 'normal' else 'Attention required.'}"
        })

# Save training data
with open("glucose_training_data.json", "w") as f:
    json.dump(training_data, f, indent=2)
```

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
