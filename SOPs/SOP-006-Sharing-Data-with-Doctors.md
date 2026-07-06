# SOP-006: Sharing Data with Doctors

**Version:** 1.0  
**Date:** 05 July 2026  
**Author:** Andrea Enning (AndieKobbieTech)

---

## Purpose

This SOP describes how to export and share glucose data and AI session insights with healthcare professionals (GPs, consultants, diabetes nurses).

---

## Prerequisites

| Item | Requirement |
|------|-------------|
| **Input** | `.agentson` file with glucose data |
| **Software** | AgentSON CLI, web browser |
| **Output** | HTML report or PDF |

---

## Procedure

### Step 1: Generate HTML Report

```powershell
cd ~/agentson

# Render glucose data as HTML
python -m cli.main render "~/Downloads/libre_libre_data.agentson" --format html --output "~/Downloads/glucose_report.html"
```

### Step 2: Open Report in Browser

```powershell
Start-Process "~/Downloads/glucose_report.html"
```

### Step 3: Print to PDF (Optional)

1. Press `Ctrl+P` in browser
2. Select "Microsoft Print to PDF"
3. Save as `glucose_report.pdf`

### Step 4: Share with Doctor

**Option A: Email**
1. Attach PDF to email
2. Send to practice email (check with reception)

**Option B: Patient Access**
1. Upload to NHS App (if available)
2. Share during appointment

**Option C: In-Person**
1. Bring printed report to appointment
2. Bring phone/laptop with web viewer loaded

---

## What to Share

| Data | Why |
|------|-----|
| **Time in Range** | Shows how often glucose is in target zone |
| **Average Glucose** | Overall control indicator |
| **Hypo/Hyper %** | Safety concerns |
| **Trends** | Patterns over time |

---

## NHS FHIR Integration (Future)

When available, this will allow:
- Automatic sharing with clinical systems
- Real-time data access for doctors
- Integration with NHS App

See SOP-007 for Nightscout setup which enables FHIR connectivity.

---

## Tips for Appointments

1. **Bring printed report** — doctors appreciate paper
2. **Highlight concerns** — mark specific dates/times
3. **Ask questions** — "Is this pattern concerning?"
4. **Request sensor replacement** — if running low
