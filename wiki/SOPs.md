# Standard Operating Procedures (SOPs)

15 SOPs covering health data, AI sessions, infrastructure, and wiki deployment.

---

## SOP Index

| # | Title | Category |
|---|-------|----------|
| 001 | [Reading FreeStyle Libre 2 Sensor](SOP-001) | Health |
| 002 | [Converting Libre Data to AgentSON](SOP-002) | Health |
| 003 | [Viewing Glucose Data in Browser](SOP-003) | Health |
| 004 | [Exporting AI Sessions](SOP-004) | AI Sessions |
| 005 | [Searching AI Sessions](SOP-005) | AI Sessions |
| 006 | [Sharing Data with Doctors](SOP-006) | Health |
| 007 | [Setting Up Nightscout Server](SOP-007) | Infrastructure |
| 008 | [WhatsApp Bot Setup](SOP-008) | Infrastructure |
| 009 | [TV Dashboard Setup](SOP-009) | Infrastructure |
| 010 | [Setting Up MedGemma HAI-DEF](SOP-010) | Health/AI |
| 011 | [Fine-tuning MedGemma on Glucose Data](SOP-011) | Health/AI |
| 012 | [Setting Up Juggluco on Mother's Phone](SOP-012) | Health |
| 013 | [NHS FHIR Integration](SOP-013) | Health |
| 014 | [West Africa Voice Alerts](SOP-014) | Health/Localization |
| 015 | [Creating GitHub Wiki (Manual + Programmatic)](SOP-015) | Infrastructure |

---

## Health SOPs

### SOP-001: Reading FreeStyle Libre 2 Sensor

Read glucose data from FreeStyle Libre 2 continuous glucose monitor using NFC.

**Prerequisites:**
- FreeStyle Libre 2 sensor
- Android phone with NFC
- LibreLink app installed

**Steps:**
1. Open LibreLink app
2. Scan sensor with NFC
3. Export CSV from app
4. Run `agentson import --tool libre --input libre_data.csv`

---

### SOP-002: Converting Libre Data to AgentSON

Convert FreeStyle Libre 2 CSV export to AgentSON format.

```bash
# Import Libre CSV
agentson import --tool libre --input libre_data.csv --output session.AgentSON
```

---

### SOP-003: Viewing Glucose Data in Browser

View glucose data in the web viewer with trend charts.

1. Open `docs/viewer/index.html`
2. Drag and drop `.AgentSON` file
3. View trend chart and statistics

---

## AI Session SOPs

### SOP-004: Exporting AI Sessions

Export sessions from any supported tool.

```bash
# Export from opencode
agentson export --tool opencode --session ses_xxx --output ./sessions/

# Export from Claude Code
agentson export --tool claude-code --session session_xxx --output ./sessions/
```

---

### SOP-005: Searching AI Sessions

Full-text search across all exported sessions.

```bash
# Search for a keyword
agentson search "nightscout" --tool opencode

# Search across all tools
agentson search "auth bug"
```

---

## Infrastructure SOPs

### SOP-007: Setting Up Nightscout Server

Self-host Nightscout for glucose data cloud sync.

**Prerequisites:**
- Oracle Cloud Always Free tier (or any VPS)
- Docker installed

**Steps:**
1. Deploy Nightscout Docker container
2. Configure MongoDB
3. Set API secret
4. Connect LibreLink app

---

### SOP-013: NHS FHIR Integration

Share glucose data with NHS doctors via FHIR API.

**Status:** Planned — requires NHS Digital FHIR credentials

---

## Health/AI SOPs

### SOP-010: Setting Up MedGemma HAI-DEF

Set up Google's MedGemma model for glucose data analysis.

### SOP-011: Fine-tuning MedGemma on Glucose Data

Fine-tune MedGemma on personal glucose data for personalized insights.

---

## Infrastructure SOPs (Wiki)

### SOP-015: Creating GitHub Wiki (Manual + Programmatic)

Create and populate a GitHub wiki — manually via browser or programmatically via clone-and-push.

**Prerequisites:**
- GitHub account
- Git installed
- Classic PAT with `repo` scope

**Method 1: Manual (Browser)**
1. Go to `github.com/USER/REPO/wiki`
2. Click "Create the first page"
3. Edit, save, repeat

**Method 2: Clone and Push (Recommended)**
```bash
git clone https://github.com/USER/REPO.wiki.git
# Copy markdown files into cloned repo
git add . && git commit -m "Add wiki pages"
# Push with PAT embedded in URL
```

**Method 3: Programmatic with OpenCode**
1. Prompt OpenCode to generate markdown pages
2. Review locally
3. Push manually (Method 2)

**Common errors:**
- "Password authentication not supported" → Embed PAT in URL
- "Invalid username or token" → Use classic PAT, not fine-grained
- "Repository not found" → Wiki URL needs `.wiki.git` suffix
