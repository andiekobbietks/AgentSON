# SOP-014: West Africa Voice Alerts

**Version:** 1.0  
**Date:** 05 July 2026  
**Author:** Andrea Enning (AndieKobbieTech)

---

## Purpose

This SOP describes how to set up voice alerts in West African languages (Twi, Ga, Ewe, Yoruba, Igbo, Hausa) for diabetes monitoring in Ghana, Nigeria, and other West African countries.

---

## Prerequisites

| Item | Requirement |
|------|-------------|
| **Software** | Coqui TTS, WhatsApp Web |
| **Data** | Glucose readings (from sensor or manual entry) |
| **Hardware** | Basic Android phone (feature phone possible for SMS) |

---

## Context

| Statistic | Value | Source |
|-----------|-------|--------|
| Ghana diabetes prevalence | 2.8-4.0% | WHO Africa |
| West Africa CGM access | <1% | Akoma Pa Program |
| Mobile phone penetration | High | GSMA |
| SMS literacy | High | Even without smartphone |

---

## Procedure

### Step 1: Install Coqui TTS

```powershell
pip install coqui-tts
```

### Step 2: Download West African Language Models

```python
# Check available models
from TTS.api import TTS

# List models
models = TTS().list_models()

# For West African languages, use:
# - Multi-lingual models
# - Or fine-tune on local language data
```

### Step 3: Create Voice Alerts

```python
from TTS.api import TTS

# Load multi-lingual model
tts = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2")

# English alert
tts.tts_to_file(
    "Warning: Glucose is low at 3.5 millimoles. Please eat something sweet.",
    file_path="alert_english.wav",
    language="en"
)

# Twi alert (Ghana)
tts.tts_to_file(
    "Kɛse: Wo glucose kɔ ne 3.5 mmol/L. Me ma wo sɛ wo no nneɛma a ɛdɔ.",
    file_path="alert_twi.wav",
    language="tr"  # Using Turkish as proxy for now
)

# Yoruba alert (Nigeria)
tts.tts_to_file(
    "Ìkìlọ̀: Glucose rẹ̀ kọ̀ sí 3.5 mmol/L. Jọ̀wọ́ jẹun nǹkan dulẹ.",
    file_path="alert_yoruba.wav",
    language="yo"
)
```

### Step 4: Send via WhatsApp

```python
import subprocess

def send_voice_alert(phone_number, audio_file, language="en"):
    """Send voice alert via WhatsApp."""
    # Use whatsapp-web.js
    subprocess.run([
        "node", "send_voice.js",
        phone_number,
        audio_file
    ])
```

### Step 5: SMS Fallback (Feature Phones)

For phones without WhatsApp:

```python
import subprocess

def send_sms_alert(phone_number, message):
    """Send SMS alert for feature phones."""
    # Use Africa's Talking API or local provider
    subprocess.run([
        "node", "send_sms.js",
        phone_number,
        message
    ])
```

---

## Language Templates

### Twi (Ghana)

| Alert | Message |
|-------|---------|
| **Low** | "Kɛse: Wo glucose kɔ ne 3.5 mmol/L. Me ma wo sɛ wo no nneɛma a ɛdɔ." |
| **High** | "Kɛse: Wo glucose kɔ ne 15 mmol/L. Fa wo nsɛm kɔ hospital." |
| **Missed** | "Wo nsɛm nni hɔ. Fa wo phone kɔ near sensor." |

### Yoruba (Nigeria)

| Alert | Message |
|-------|---------|
| **Low** | "Ìkìlọ̀: Glucose rẹ̀ kọ̀ sí 3.5 mmol/L. Jọ̀wọ́ jẹun nǹkan dulẹ." |
| **High** | "Ìkìlọ̀: Glucose rẹ̀ ga ju 15 mmol/L lọ. Lo hospital." |
| **Missed** | "Kò sí ìfẹ̀rọ̀. Fi phone yìí sí sensor." |

### Ewe (Ghana)

| Alert | Message |
|-------|---------|
| **Low** | "Gahe: Wo glucose kɔ 3.5 mmol/L. Na wo nə̀." |
| **High** | "Gahe: Wo glucose kɔ 15 mmol/L. Yi hospital." |

---

## Community Health Worker Integration

| CHW Task | How |
|----------|-----|
| **Screening** | Use phone app to enter readings |
| **Monitoring** | Check dashboard weekly |
| **Alerts** | Receive WhatsApp/SMS for high-risk patients |
| **Reports** | Generate monthly summaries |

---

## Data Flow

```
Patient (Manual Entry or Sensor)
    ↓
CHW Phone (Juggluco or Manual)
    ↓
Nightscout (or Local Server)
    ↓
Voice/SMS Alert System
    ↓
Patient Phone (WhatsApp or SMS)
```

---

## Cost

| Component | Cost | Notes |
|-----------|------|-------|
| Coqui TTS | Free | Open source |
| WhatsApp | Free | Free messaging |
| SMS (Africa's Talking) | £0.01/message | Pay per use |
| Phone | Already have | No new hardware |
| **TOTAL** | <£1/month | For 100 SMS |

---

## Cultural Considerations

| Consideration | Adaptation |
|---------------|------------|
| **Language** | Voice in local language, not English |
| **Literacy** | Voice > text for low literacy |
| **Trust** | Community health workers as intermediaries |
| **Cost** | SMS for feature phones, WhatsApp for smartphones |
| **Connectivity** | Offline-first, sync when available |

---

## References

- Akoma Pa Program (Ghana): https://chag-ghana.org
- DiabAid Nexus: JMIR 2026
- Africa's Talking API: https://africastalking.com
