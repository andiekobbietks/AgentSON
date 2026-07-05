# SOP-005: Searching AI Sessions

**Version:** 1.0  
**Date:** 05 July 2026  
**Author:** Andrea Enning (AndieKobbieTech)

---

## Purpose

This SOP describes how to search across exported AgentSON sessions for specific content, code, or patterns.

---

## Prerequisites

| Item | Requirement |
|------|-------------|
| **Input** | `.AgentSON` files (from SOP-004) |
| **Software** | PowerShell or grep-compatible tool |

---

## Procedure

### Step 1: Search Single File

```powershell
# Search for specific term
Select-String -Path "~/Downloads\*.AgentSON" -Pattern "nightscout"
```

### Step 2: Search All Sessions

```powershell
# Search all AgentSON files in directory
Get-ChildItem "~/Downloads\*.AgentSON" | Select-String -Pattern "function"
```

### Step 3: Search with Context

```powershell
# Show 2 lines before and after match
Select-String -Path "~/Downloads\*.AgentSON" -Pattern "error" -Context 2,2
```

### Step 4: Search Specific Fields

```powershell
# Search for code blocks
Select-String -Path "~/Downloads\*.AgentSON" -Pattern '"code":'
```

---

## Common Searches

| Search | Pattern |
|--------|---------|
| Find errors | `error\|Error\|ERROR` |
| Find code | `"code":` |
| Find tool calls | `"tool":` |
| Find specific function | `function.*name` |
| Find file paths | `[A-Z]:\\.*\\` |

---

## Using AgentSON CLI Search

```powershell
# Future: Native search command
python -m cli.main search --term "nightscout" --tool opencode
```

---

## Tips

1. **Use quotes** for exact matches: `"exact phrase"`
2. **Use wildcards** for partial matches: `night*`
3. **Combine searches**: `error AND function`
4. **Export results**: `| Out-File search_results.txt`
