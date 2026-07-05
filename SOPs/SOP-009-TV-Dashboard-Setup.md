# SOP-009: TV Dashboard Setup

**Version:** 1.0  
**Date:** 05 July 2026  
**Author:** Andrea Enning (AndieKobbieTech)

---

## Purpose

This SOP describes how to set up a Samsung Smart TV dashboard that displays real-time glucose data, alerts, and daily summaries.

---

## Prerequisites

| Item | Requirement |
|------|-------------|
| **Hardware** | Samsung 55" Smart TV, PC on same network |
| **Software** | Web browser on TV |
| **Data** | Nightscout server (SOP-007) |

---

## Architecture

```
PC (Nightscout) → TV Browser → Glucose Dashboard
         ↓
    Voice Alerts (via TV speakers)
```

---

## Procedure

### Step 1: Create Dashboard HTML

Create `tv_dashboard.html`:
```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta http-equiv="refresh" content="300"> <!-- Refresh every 5 minutes -->
    <title>Glucose Dashboard</title>
    <style>
        body { 
            font-family: Arial; 
            background: #1a1a2e; 
            color: white; 
            text-align: center;
            padding: 50px;
        }
        .glucose { font-size: 120px; }
        .status { font-size: 40px; }
        .time { font-size: 30px; color: #888; }
        .normal { color: #00ff00; }
        .high { color: #ffff00; }
        .low { color: #ff0000; }
    </style>
</head>
<body>
    <div class="time" id="time"></div>
    <div class="glucose" id="glucose">--</div>
    <div class="status" id="status">Loading...</div>
    <script>
        async function update() {
            const res = await fetch('http://YOUR-PC-IP:1337/api/v1/entries.json?count=1');
            const data = await res.json();
            if (data.length > 0) {
                const bg = data[0].sgv / 18;
                document.getElementById('glucose').textContent = bg.toFixed(1);
                document.getElementById('glucose').className = 'glucose ' + 
                    (bg < 4 ? 'low' : bg > 10 ? 'high' : 'normal');
                document.getElementById('status').textContent = 
                    bg < 4 ? '⚠️ LOW' : bg > 10 ? '⚠️ HIGH' : '✅ Normal';
            }
            document.getElementById('time').textContent = new Date().toLocaleTimeString();
        }
        update();
        setInterval(update, 60000);
    </script>
</body>
</html>
```

### Step 2: Host Dashboard

```powershell
cd ~/agentson/viewers/web
python -m http.server 8080
```

### Step 3: Find PC's IP

```powershell
ipconfig | findstr "IPv4"
```

### Step 4: Open on TV

1. Turn on Samsung TV
2. Open built-in web browser
3. Enter: `http://YOUR-PC-IP:8080/tv_dashboard.html`
4. Bookmark for easy access

---

## TV Browser Tips

| Tip | How |
|-----|-----|
| **Full screen** | Press F11 or TV's full screen button |
| **Auto-refresh** | HTML refreshes every 5 minutes |
| **Font size** | Adjust CSS for TV viewing distance |
| **Color coding** | Green=normal, Yellow=high, Red=low |

---

## Voice Alerts via TV

If TV has Alexa or built-in speakers:

1. **Enable screen reader** in TV settings
2. **Use text-to-speech** for critical alerts
3. **Play audio files** via TV's media player

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| TV can't connect | Check same WiFi network |
| Dashboard not loading | Check PC IP, firewall settings |
| Data not updating | Check Nightscout server running |
| Font too small | Increase CSS font-size |
