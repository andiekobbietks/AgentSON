# SOP-008: WhatsApp Bot Setup

**Version:** 1.0  
**Date:** 05 July 2026  
**Author:** Andrea Enning (AndieKobbieTech)

---

## Purpose

This SOP describes how to set up a WhatsApp bot that sends automated voice notes with glucose alerts and daily summaries.

---

## Prerequisites

| Item | Requirement |
|------|-------------|
| **Server** | Nightscout server (SOP-007) |
| **Software** | Python 3.12.3, Coqui TTS, whatsapp-web.js |
| **Hardware** | PC running 24/7 or cloud server |

---

## Architecture

```
Nightscout → Python Bot → Coqui TTS → WhatsApp Voice Note
                       ↓
                   Text Alert
```

---

## Procedure

### Step 1: Install Dependencies

```powershell
cd ~/Documents
python -m venv whatsapp-env
.\whatsapp-env\Scripts\Activate.ps1

pip install TTS whatsapp-web.js pywhatkit
```

### Step 2: Configure Bot

Create `whatsapp_bot.py`:
```python
from TTS.api import TTS
import json
import requests

# Load TTS model
tts = TTS(model_name="tts_models/en/ljspeech/tacotron2-DDC")

def generate_voice_alert(glucose_value, status):
    if status == "low":
        text = f"Warning: Glucose is low at {glucose_value} millimoles per liter. Please check immediately."
    elif status == "high":
        text = f"Alert: Glucose is high at {glucose_value} millimoles per liter. Consider taking action."
    else:
        text = f"Glucose is normal at {glucose_value} millimoles per liter. All good."
    
    tts.tts_to_file(text, file_path="alert.wav")
    return "alert.wav"

def send_whatsapp_message(phone_number, audio_file):
    # Use whatsapp-web.js to send
    import subprocess
    subprocess.run(["node", "send_whatsapp.js", phone_number, audio_file])
```

### Step 3: Set Up Alert Triggers

| Trigger | Condition | Action |
|---------|-----------|--------|
| **Hypo Alert** | Glucose < 4.0 | Immediate voice note |
| **Hyper Alert** | Glucose > 15.0 | Immediate voice note |
| **Daily Summary** | 8:00 AM | Summary of previous day |
| **Missed Reading** | No data for 2 hours | Alert sent |

### Step 4: Run Bot

```powershell
python whatsapp_bot.py
```

---

## Voice Note Examples

**Hypo Alert:**
> "Warning: Glucose is low at 3.5 millimoles per liter. Please check immediately."

**Hyper Alert:**
> "Alert: Glucose is high at 15.2 millimoles per liter. Consider taking action."

**Daily Summary:**
> "Good morning. Yesterday your glucose averaged 9.3 millimoles per liter. Time in range was 60 percent. You had 2 high readings in the afternoon."

---

## WhatsApp Web Setup

### Step 1: Install Node.js

Download from https://nodejs.org

### Step 2: Clone whatsapp-web.js

```powershell
git clone https://github.com/nicholasgasior/whatsapp-web.js.git
cd whatsapp-web.js
npm install
```

### Step 3: Authenticate

```powershell
node send_whatsapp.js
```

Scan QR code with mother's WhatsApp

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| QR code not appearing | Restart bot, check internet |
| Voice note not sending | Check file path, WhatsApp Web running |
| Delayed alerts | Check Nightscout connection |
