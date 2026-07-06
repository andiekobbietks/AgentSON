# SOP-015: Creating a GitHub Wiki (Manual + Programmatic)

**Version:** 1.0
**Date:** 2026-07-05
**Author:** Andrea Enning (AndieKobbieTech)

---

## Overview

This SOP covers creating and populating a GitHub wiki — both manually and programmatically using OpenCode.

---

## Prerequisites

- GitHub account
- Git installed
- OpenCode installed (for programmatic method)
- Classic Personal Access Token (PAT) with `repo` scope

---

## Method 1: Manual (Browser)

### Step 1: Create Wiki on GitHub

1. Go to `github.com/your-username/your-repo/wiki`
2. Click **"Create the first page"**
3. Edit the default Home page
4. Click **"Save Page"**
5. Verify: banner says "Your Wiki was created."

### Step 2: Add Pages

1. Click **"New page"** (top right)
2. Enter page name (e.g., `Getting-Started`)
3. Paste markdown content
4. Click **"Save Page"**
5. Repeat for each page

### Limitations

- No version control for wiki content
- No CI/CD pipeline
- No local editing
- No bulk operations

---

## Method 2: Clone and Push (Recommended)

### Step 1: Clone Wiki Repo

```bash
git clone https://github.com/your-username/your-repo.wiki.git
```

**Expected output:**
```
Cloning into 'your-repo.wiki'...
remote: Enumerating objects: 3, done.
remote: Counting objects: 100% (3/3), done.
Receiving objects: 100% (3/3), done.
```

### Step 2: Add Content

```bash
cd your-repo.wiki
# Copy your markdown files here
copy path\to\your\files\*.md .
```

### Step 3: Commit

```bash
git add .
git commit -m "Add wiki pages"
```

**Expected output:**
```
[main xxxxxxx] Add wiki pages
 X files changed, Y insertions(+)
```

### Step 4: Push with PAT

```powershell
# PowerShell — masked input
$token = Read-Host -Prompt "Paste PAT" -AsSecureString
$tokenPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
    [Runtime.InteropServices.Marshal]::SecureStringToBSTR($token)
)
git remote set-url origin "https://your-username:${tokenPlain}@github.com/your-username/your-repo.wiki.git"
git push
```

**Expected output:**
```
Enumerating objects: 13, done.
Writing objects: 100% (11/11), done.
To https://github.com/your-username/your-repo.wiki.git
   abc1234..def5678  main -> main
```

---

## Method 3: Programmatic with OpenCode

### What OpenCode Can Do

OpenCode is a free, open-source AI coding assistant. With the right prompts, it can:

1. Generate markdown content for wiki pages
2. Create files locally using the write() tool
3. Run git commands via bash tool
4. Generate PDFs using Python (reportlab)
5. Query SQLite databases for session data

### What OpenCode Cannot Do (Free Tier)

- Cannot authenticate to GitHub (no token handling)
- Cannot push to remote repos directly
- Cannot access browser-based workflows
- Limited to local file operations

### Workflow: OpenCode + Manual Push

**Step 1: Generate content with OpenCode**

Prompt: "Create a wiki page for [topic] in markdown format. Include: title, overview, step-by-step instructions, expected outputs, common errors, and fixes."

OpenCode will use the write() tool to create the file locally.

**Step 2: Review and edit locally**

```bash
cd C:\Users\your-username\Documents\your-repo\wiki
# Review the generated files
notepad Getting-Started.md
```

**Step 3: Push manually**

Follow Method 2 above.

### OpenCode Free Tier Limitations

| Feature | Free Tier | Paid Tier |
|---------|-----------|-----------|
| Model | MiMo V2.5 Free | GPT-4, Claude |
| Sessions | Unlimited | Unlimited |
| File writes | Yes | Yes |
| Git operations | Yes (local) | Yes (local) |
| GitHub auth | No | No |
| Token handling | No (security) | No (security) |

### OpenCode Prompts for Wiki Generation

**Generate a getting started page:**
```
Create a getting-started.md wiki page for [project name]. Include:
- Installation steps with exact commands
- Expected output for each command
- Common errors and fixes
- Version requirements
```

**Generate an API reference:**
```
Create an api-reference.md wiki page for [project name]. Include:
- All public functions/methods
- Parameters and return types
- Usage examples
- Error codes
```

**Generate a troubleshooting guide:**
```
Create a troubleshooting.md wiki page for [project name]. Include:
- Top 5 common errors
- Exact error messages
- Step-by-step fixes
- Prevention tips
```

---

## Token Management

### Creating a Classic PAT

1. Go to `github.com/settings/tokens`
2. Click **"Generate new token"** → **"Generate new token (classic)"**
3. Note: name it (e.g., `wiki-push`)
4. Expiration: 30 days
5. Scopes: check **`repo`** (only)
6. Click **"Generate token"**
7. Copy immediately (won't see again)

### Token Security Rules

- NEVER share tokens in chat/email
- Use `Read-Host -AsSecureString` for masked input
- Delete compromised tokens immediately
- Use minimal scopes (repo only for wiki)

### Clearing Cached Credentials

If git keeps failing after token change:

```bash
git config --global --unset credential.helper
git config --global credential.helper store
```

---

## Troubleshooting

### Error: "Password authentication is not supported"

**Cause:** GitHub deprecated password auth for git in 2021.
**Fix:** Embed PAT in URL: `https://USER:TOKEN@github.com/USER/REPO.wiki.git`

### Error: "Invalid username or token"

**Cause:** Fine-grained token lacks wiki permission, or cached bad creds.
**Fix:** Use classic PAT with `repo` scope. Clear credential helper.

### Error: "remote: Repository not found"

**Cause:** Wrong wiki URL.
**Fix:** Wiki URL format: `https://github.com/USER/REPO.wiki.git` (note `.wiki.git` suffix)

---

## References

- [GitHub Wiki Documentation](https://docs.github.com/en/communities/documenting-your-project-with-wikis)
- [GDPR Article 20 — Right to Data Portability](https://gdpr-info.eu/art-20-gdpr/)
- [ICO — Your Right to Data Portability](https://ico.org.uk/for-the-public/your-right-to-data-portability/)
- [OpenCode Documentation](https://opencode.ai)
