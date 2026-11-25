# Standard Operating Procedures (SOPs)

This page indexes the legacy wiki procedures. Repository governance procedures SOP-015 and SOP-016 are maintained under the root SOPs directory; the duplicate numbering is historical and must not be used to identify them interchangeably.

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
| 012 | [Setting Up Juggluco on Android](SOP-012) | Health |
| 013 | [NHS FHIR Integration](SOP-013) | Health |
| 014 | [West Africa Voice Alerts](SOP-014) | Health/Localization |
| W-015 | [Creating GitHub Wiki (Manual + Programmatic)](SOP-015-Creating-GitHub-Wiki) | Infrastructure (legacy wiki procedure) |

---

## Repository governance SOPs

- [SOP-015: AI-Agent Repository Operating Procedure](https://github.com/andiekobbietks/AgentSON/blob/master/SOPs/SOP-015-AI-Agent-Repository-Operating-Procedure.md)
- [SOP-016: Work-In-Progress Governance](https://github.com/andiekobbietks/AgentSON/blob/master/SOPs/SOP-016-Work-In-Progress-Governance.md)

These repository procedures govern branch/PR workflow and take precedence over legacy wiki instructions about authentication or pushing. Do not embed access tokens in Git URLs, shell history or documentation.

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
agentson import --tool libre --input libre_data.csv --output session.agentson
```

---

### SOP-003: Viewing Legacy JSON Session Documents in Browser

The browser viewer reads legacy single-JSON session-envelope documents only. It does not support canonical v1.2 JSONL streams.

1. Open `docs/viewer/index.html`
2. Load a legacy JSON session-envelope document (.json or legacy JSON .agentson)
3. For canonical v1.2 JSONL archives, use: agentson render FILE --format md

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

## Wiki publishing procedure

The maintained source is [W-015: Publishing the AgentSON GitHub Wiki](SOP-015-Creating-GitHub-Wiki). It explains the distinction between docs/wiki in the main repository and the separate GitHub Wiki remote. The required sequence is: edit docs/wiki in a reviewed main-repository branch, merge the approved source, clone the separate .wiki.git repository, change into that clone, copy the approved Markdown pages, inspect the diff, commit and push to the wiki repository's configured default branch. Do not push directly to the main AgentSON master branch.
