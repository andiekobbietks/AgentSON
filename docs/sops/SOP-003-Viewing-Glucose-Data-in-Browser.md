# SOP-003: Viewing Glucose Data in Browser

**Version:** 1.0  
**Date:** 05 July 2026  
**Author:** Andrea Enning (AndieKobbieTech)

---

## Purpose

This SOP describes how to view AgentSON glucose data in a web browser using the AgentSON web viewer.

---

## Prerequisites

| Item | Requirement |
|------|-------------|
| **Input** | `.AgentSON` file (from SOP-002) |
| **Software** | Any modern web browser (Edge, Chrome, Firefox) |
| **Location** | `C:\Users\LLM-Test\Documents\agentsong\viewers\web\index.html` |

---

## Procedure

### Step 1: Open Web Viewer

**Option A: Direct File Access**
```
double-click C:\Users\LLM-Test\Documents\agentsong\viewers\web\index.html
```

**Option B: Via Browser**
1. Open Edge/Chrome
2. Press `Ctrl+O`
3. Navigate to `C:\Users\LLM-Test\Documents\agentsong\viewers\web\`
4. Select `index.html`

### Step 2: Load AgentSON File

1. Drag `.AgentSON` file from `C:\Users\LLM-Test\Downloads\` onto the viewer
2. **OR** click the drop zone and select the file

### Step 3: View Data

The viewer displays:
- **Session info**: Tool, agent, date range
- **Glucose readings**: Each reading with timestamp and status
- **Metrics**: Average glucose, time in range, hypo/hyper percentages

---

## Viewing on Mother's iPhone

### Option A: Local LAN (No Internet Required)

1. **On your PC**: Start a local server
   ```powershell
   cd C:\Users\LLM-Test\Documents\agentsong\viewers\web
   python -m http.server 8080
   ```

2. **Find your PC's IP address**
   ```powershell
   ipconfig | findstr "IPv4"
   ```

3. **On mother's iPhone**:
   - Connect to same WiFi as PC
   - Open Safari
   - Enter: `http://YOUR-PC-IP:8080`
   - Drag `.AgentSON` file onto viewer

### Option B: Free Hosting (Works Anywhere)

1. **Deploy to Vercel** (free):
   ```powershell
   cd C:\Users\LLM-Test\Documents\agentsong\viewers\web
   npx vercel
   ```

2. **Share URL with mother**
3. **On mother's iPhone**: Open URL, drag `.AgentSON` file

---

## Features

| Feature | Description |
|---------|-------------|
| **Dark mode** | Easy on the eyes |
| **Mobile responsive** | Works on iPhone/Android |
| **Drag & drop** | No file picker needed |
| **Color-coded status** | Green=normal, Yellow=high, Red=low |

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| File not loading | Check file extension is `.AgentSON` or `.json` |
| Blank screen | Refresh page, try different browser |
| Can't access from iPhone | Ensure same WiFi network, check firewall |
