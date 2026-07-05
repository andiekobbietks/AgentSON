# SOP-004: Exporting AI Sessions

**Version:** 1.0  
**Date:** 05 July 2026  
**Author:** Andrea Enning (AndieKobbieTech)

---

## Purpose

This SOP describes how to export AI coding sessions from various tools (opencode, MiniMax, Antigravity IDE) into AgentSON format for search, backup, and cross-tool hydration.

---

## Prerequisites

| Item | Requirement |
|------|-------------|
| **Software** | Python 3.12.3, AgentSON CLI |
| **Data** | Existing AI sessions in supported tools |
| **Location** | `~/agentson` |

---

## Supported Tools

| Tool | Database Location |
|------|-------------------|
| opencode | `~\.local\share\opencode\opencode.db` |
| MiniMax | `~\.minimax\sqlite.db` |
| Antigravity IDE | `~\.gemini\antigravity-ide\conversations\*.db` |

---

## Procedure

### Step 1: List Available Sessions

```powershell
cd ~/agentson

# List opencode sessions
python -m cli.main list --tool opencode

# List MiniMax sessions
python -m cli.main list --tool minimax

# List Antigravity sessions
python -m cli.main list --tool antigravity
```

### Step 2: Export Specific Session

```powershell
# Export specific opencode session
python -m cli.main export --tool opencode --session ses_xxx --output "~/Downloads"

# Export specific MiniMax session
python -m cli.main export --tool minimax --session xxx --output "~/Downloads"
```

### Step 3: Export All Sessions

```powershell
# Export all opencode sessions
python -m cli.main export --tool opencode --all --output "~/Downloads"

# Export all MiniMax sessions
python -m cli.main export --tool minimax --all --output "~/Downloads"
```

---

## Output

| Tool | File Pattern |
|------|--------------|
| opencode | `opencode_ses_xxx.AgentSON` |
| MiniMax | `minimax_xxx.AgentSON` |
| Antigravity | `antigravity_xxx.AgentSON` |

---

## Next Steps

After exporting, proceed to:
- **SOP-003**: View sessions in browser
- **SOP-005**: Search sessions for specific content
