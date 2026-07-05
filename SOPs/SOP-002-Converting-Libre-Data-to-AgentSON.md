# SOP-002: Converting Libre Data to AgentSON

**Version:** 1.0  
**Date:** 05 July 2026  
**Author:** Andrea Enning (AndieKobbieTech)

---

## Purpose

This SOP describes how to convert FreeStyle Libre 2 glucose data (CSV format) into AgentSON format for visualization, search, and sharing.

---

## Prerequisites

| Item | Requirement |
|------|-------------|
| **Input** | `libre_data.csv` (from SOP-001) |
| **Software** | Python 3.12.3, AgentSON CLI |
| **Location** | `C:\Users\LLM-Test\Documents\agentsong` |

---

## Procedure

### Step 1: Navigate to AgentSON Directory

```powershell
cd C:\Users\LLM-Test\Documents\agentsong
```

### Step 2: Export CSV to AgentSON

```powershell
python -m cli.main export --tool libre --input "C:\Users\LLM-Test\Documents\libre_data.csv" --output "C:\Users\LLM-Test\Downloads"
```

### Step 3: Verify Output

```powershell
Get-Item "C:\Users\LLM-Test\Downloads\libre_libre_data.AgentSON"
```

Expected output:
```
Name                          Length LastWriteTime
----                          ------ -------------
libre_libre_data.AgentSON     12345  05/07/2026 00:53
```

---

## Output

| File | Description |
|------|-------------|
| `libre_libre_data.AgentSON` | Glucose data in AgentSON format |

---

## What's in the AgentSON File

```json
{
  "id": "libre-libre_data",
  "tool": {"name": "FreeStyle Libre 2"},
  "entries": [
    {
      "role": "sensor",
      "type": "glucose_reading",
      "timestamp": "2026-06-17T12:43:44",
      "text": "Glucose: 11.11 mmol/L",
      "data": {"value": 11.11, "unit": "mmol/L"},
      "status": "high"
    }
  ],
  "metrics": {
    "avg_glucose": 9.33,
    "time_in_range": 60.6,
    "hypo_pct": 0.0,
    "hyper_pct": 39.4
  }
}
```

---

## Next Steps

After converting the data, proceed to:
- **SOP-003**: View Glucose Data in Browser
- **SOP-006**: Share Data with Doctors
