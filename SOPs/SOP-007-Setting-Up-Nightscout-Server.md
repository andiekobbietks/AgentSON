# SOP-007: Setting Up Nightscout Server

**Version:** 1.0  
**Date:** 05 July 2026  
**Author:** Andrea Enning (AndieKobbieTech)

---

## Purpose

This SOP describes how to set up a Nightscout server as a data backbone for continuous glucose monitoring, enabling WhatsApp alerts, TV dashboards, and NHS FHIR integration.

---

## Prerequisites

| Item | Requirement |
|------|-------------|
| **Hardware** | PC or cloud account (Azure free tier) |
| **Software** | Node.js, MongoDB (or MongoDB Atlas free tier) |
| **Data** | Juggluco app on mother's phone |

---

## Architecture

```
Mother's Phone (Juggluco) → Nightscout Server → WhatsApp Bot
                                    ↓
                              TV Dashboard
                                    ↓
                           NHS FHIR API
```

---

## Option A: Local Server (No Cloud)

### Step 1: Install Node.js

Download from https://nodejs.org (LTS version)

### Step 2: Clone Nightscout

```powershell
cd ~/Documents
git clone https://github.com/nightscout/cgm-remote-monitor.git
cd cgm-remote-monitor
```

### Step 3: Install Dependencies

```powershell
npm install
```

### Step 4: Configure Environment

Create `.env` file:
```
MONGO_CONNECTION=mongodb://localhost:27017/nightscout
API_SECRET=your-secret-here
```

### Step 5: Start Server

```powershell
npm start
```

Server runs at: `http://localhost:1337`

---

## Option B: Azure Free Tier (Recommended)

### Step 1: Create Azure Account

1. Go to https://azure.microsoft.com/free
2. Sign up for free account ($200 credit)
3. Create MongoDB Atlas free cluster

### Step 2: Deploy Nightscout

1. Go to https://nightscout.github.io
2. Click "Deploy to Azure"
3. Follow wizard

### Step 3: Configure Juggluco

1. Open Juggluco on mother's phone
2. Go to Settings → Cloud Upload
3. Enter Nightscout URL and API secret

---

## Connecting Juggluco

### Step 1: Install Juggluco

Download from https://www.juggluco.nl

### Step 2: Pair with Sensor

1. Open Juggluco
2. Tap "Scan" → point at sensor
3. Wait for connection

### Step 3: Configure Cloud Upload

1. Settings → Cloud Upload
2. Select "Nightscout"
3. Enter server URL
4. Enter API secret
5. Enable "Upload on WiFi only" (optional)

---

## Verification

```powershell
# Check server is running
Invoke-WebRequest http://localhost:1337/api/v1/status.json
```

Expected: JSON with server status

---

## Next Steps

After setting up Nightscout, proceed to:
- **SOP-008**: WhatsApp Bot Setup
- **SOP-009**: TV Dashboard Setup
