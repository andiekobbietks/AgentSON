# SOP-010: Setting Up MedGemma / HAI-DEF

**Version:** 1.0  
**Date:** 05 July 2026  
**Author:** Andrea Enning (AndieKobbieTech)

---

## Purpose

This SOP describes how to sign up for Google's Health AI Developer Foundations (HAI-DEF) and download MedGemma for glucose pattern analysis.

---

## Prerequisites

| Item | Requirement |
|------|-------------|
| **Account** | Google account |
| **Software** | Python 3.12.3, Hugging Face account |
| **Hardware** | PC with 8GB+ RAM (for 4B model) |

---

## Procedure

### Step 1: Sign Up for HAI-DEF

1. Go to https://developers.google.com/health-ai-developer-foundations
2. Click "Get Started"
3. Sign in with Google account
4. Accept Terms of Use
5. Done — no approval needed

### Step 2: Create Hugging Face Account

1. Go to https://huggingface.co
2. Sign up (free)
3. Verify email

### Step 3: Download MedGemma

```powershell
# Install Hugging Face CLI
pip install huggingface_hub

# Login
huggingface-cli login

# Download MedGemma 4B (multimodal - can analyze images)
huggingface-cli download google/medgemma-4b --local-dir ./medgemma-4b

# OR download MedGemma 27B (text only - better for clinical reasoning)
huggingface-cli download google/medgemma-27b --local-dir ./medgemma-27b
```

### Step 4: Install Dependencies

```powershell
pip install torch transformers accelerate
```

### Step 5: Test MedGemma

```python
from transformers import AutoModelForCausalLM, AutoTokenizer

model = AutoModelForCausalLM.from_pretrained("google/medgemma-4b")
tokenizer = AutoTokenizer.from_pretrained("google/medgemma-4b")

# Test with glucose question
prompt = "A patient has glucose readings of 15.2, 14.8, 16.1 mmol/L over 3 hours. What does this indicate?"
inputs = tokenizer(prompt, return_tensors="pt")
outputs = model.generate(**inputs, max_new_tokens=200)
print(tokenizer.decode(outputs[0]))
```

---

## What You Get

| Resource | Cost | Access |
|----------|------|--------|
| MedGemma 4B | Free | Hugging Face |
| MedGemma 27B | Free | Hugging Face |
| MedASR | Free | Hugging Face |
| Vertex AI free tier | Free | Google Cloud |

---

## Next Steps

After setting up MedGemma, proceed to:
- **SOP-011**: Fine-tuning MedGemma on Glucose Data
