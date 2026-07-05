# SOP-001: Reading FreeStyle Libre 2 Sensor

**Version:** 1.0  
**Date:** 05 July 2026  
**Author:** Andrea Enning (AndieKobbieTech)

---

## Purpose

This SOP describes how to connect a FreeStyle Libre 2 reader to a Windows PC via USB and extract glucose data for analysis and storage.

---

## Prerequisites

| Item | Requirement |
|------|-------------|
| **Hardware** | FreeStyle Libre 2 reader with USB cable |
| **Software** | Python 3.12.3, glucometerutils, freestyle-hid |
| **Data** | Sensor must have readings stored on the reader |

---

## Setup (One-Time)

### Step 1: Create Python Virtual Environment

```powershell
cd C:\Users\LLM-Test\Documents
python -m venv libreenv
.\libreenv\Scripts\Activate.ps1
```

### Step 2: Install Dependencies

```powershell
pip install glucometerutils[fslibre2] freestyle-hid freestyle-keys hidapi construct
```

---

## Procedure

### Step 1: Connect Reader

1. Ensure FreeStyle Libre 2 reader is charged
2. Connect reader to PC via USB cable
3. Wait for Windows to recognize the device
4. Open PowerShell

### Step 2: Activate Virtual Environment

```powershell
cd C:\Users\LLM-Test\Documents
.\libreenv\Scripts\Activate.ps1
```

### Step 3: Read Sensor Data

```powershell
glucometerutils read --driver fslibre2 --output libre_data.csv
```

**Note:** If the reader is not detected, try:
- Unplugging and re-plugging the USB cable
- Closing any other applications that might be using the reader
- Ensuring the reader is unlocked

### Step 4: Verify Data

```powershell
Get-Content libre_data.csv | Select-Object -First 10
```

Expected output:
```
Timestamp,Glucose (mmol/L),,,Type,Source
"2026-06-17 12:43:44","11.11","","","CGM","(Sensor)"
...
```

---

## Output

| File | Description |
|------|-------------|
| `libre_data.csv` | Raw glucose readings with timestamps |

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Reader not detected | Check USB connection, try different port |
| Permission denied | Run PowerShell as Administrator |
| No data returned | Ensure sensor was scanned at least once |
| Wrong driver error | Use `--driver fslibre2` not `--driver libreview` |

---

## Next Steps

After reading the sensor, proceed to:
- **SOP-002**: Convert Libre Data to AgentSON
- **SOP-003**: View Glucose Data in Browser
