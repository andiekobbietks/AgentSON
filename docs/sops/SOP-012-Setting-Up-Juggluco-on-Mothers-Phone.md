# SOP-012: Setting Up Juggluco on Mother's Phone

**Version:** 1.0  
**Date:** 05 July 2026  
**Author:** Andrea Enning (AndieKobbieTech)

---

## Purpose

This SOP describes how to install and configure Juggluco on mother's phone for continuous glucose monitoring via Bluetooth.

---

## Prerequisites

| Item | Requirement |
|------|-------------|
| **Hardware** | Mother's Android phone |
| **Sensor** | New FreeStyle Libre 2 sensor (current one ended Jun 24) |
| **Internet** | WiFi or mobile data |
| **Location** | With mother (physical setup required) |

---

## Procedure

### Step 1: Install Juggluco

**On mother's phone:**

1. Open Google Play Store
2. Search "Juggluco"
3. Install "Juggluco" by Jan Rijnen
4. Open app

**OR download APK:**

1. Go to https://www.juggluco.nl
2. Download latest APK
3. Install (allow unknown sources)

### Step 2: Create Account

1. Open Juggluco
2. Tap "Settings" → "Account"
3. Create account with email
4. Verify email

### Step 3: Pair with Sensor

1. **Apply new sensor** to mother's arm (or have nurse do it)
2. Open Juggluco
3. Tap "Scan"
4. Point phone at sensor (NFC)
5. Wait for connection
6. Sensor should appear in app

### Step 4: Enable Bluetooth

1. Settings → "Bluetooth"
2. Enable "Continuous scanning"
3. Keep phone within 1 meter of sensor
4. Readings update every 5 minutes

### Step 5: Configure Cloud Upload

1. Settings → "Cloud Upload"
2. Select "Nightscout"
3. Enter server URL (from SOP-007)
4. Enter API secret
5. Enable "Upload on WiFi only" (optional)
6. Test connection

### Step 6: Set Alerts

1. Settings → "Alerts"
2. Configure:
   - Low alert: < 4.0 mmol/L
   - High alert: > 15.0 mmol/L
   - Missed reading: 2 hours
3. Enable sound/vibration

---

## Phone Placement

| Location | Bluetooth Range | Battery Impact |
|----------|-----------------|----------------|
| Same room | ✅ Best | Moderate |
| Adjacent room | ✅ Good | Low |
| Different floor | ⚠️ May disconnect | Low |
| Different building | ❌ No connection | None |

**Recommendation:** Keep phone in same room as mother, or in her pocket/bag.

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Sensor not detected | Ensure sensor is new, try again |
| Bluetooth disconnects | Keep phone closer, check battery |
| No data uploading | Check Nightscout URL, internet connection |
| Battery draining fast | Reduce scan frequency, use WiFi only |

---

## Next Steps

After setting up Juggluco, proceed to:
- **SOP-007**: Nightscout Server (receive uploads)
- **SOP-008**: WhatsApp Bot (send alerts)
- **SOP-009**: TV Dashboard (view data)
