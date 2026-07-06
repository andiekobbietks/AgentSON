"""
AgentSON Wiki Deployment Cheat Sheet v4
Proper breathing room, SOP for wiki creation, OpenCode integration
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, PageBreak
from reportlab.lib.units import inch, mm

PHI = 1.618

AMBER = HexColor("#FFB000")
WHITE = HexColor("#FFFFFF")
GRAY = HexColor("#666666")
LIGHT_GRAY = HexColor("#f8f8f8")
GREEN = HexColor("#00AA55")
RED = HexColor("#CC3333")
BLUE = HexColor("#4488CC")

def build_cheatsheet():
    doc = SimpleDocTemplate(
        "C:\\Users\\LLM-Test\\Documents\\agentsong\\wiki\\AgentSON_Wiki_Cheatsheet.pdf",
        pagesize=A4,
        rightMargin=60,
        leftMargin=60,
        topMargin=60,
        bottomMargin=60
    )

    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('Title', parent=styles['Title'], fontSize=24, textColor=AMBER, spaceAfter=24, leading=24*PHI, alignment=1)
    subtitle_style = ParagraphStyle('Subtitle', parent=styles['Normal'], fontSize=10, textColor=GRAY, spaceAfter=16, alignment=1)
    h1_style = ParagraphStyle('H1', parent=styles['Heading1'], fontSize=16, textColor=AMBER, spaceBefore=24, spaceAfter=12, leading=16*PHI)
    h2_style = ParagraphStyle('H2', parent=styles['Heading2'], fontSize=12, textColor=BLUE, spaceBefore=16, spaceAfter=8, leading=12*PHI)
    body_style = ParagraphStyle('Body', parent=styles['Normal'], fontSize=10, leading=10*PHI, spaceAfter=8)
    code_style = ParagraphStyle('Code', parent=styles['Code'], fontSize=9, backColor=LIGHT_GRAY, borderWidth=0.5, borderColor=HexColor("#dddddd"), borderPadding=8, spaceAfter=8, leading=9*PHI, fontName='Courier')
    success_style = ParagraphStyle('Success', parent=body_style, textColor=GREEN)
    fail_style = ParagraphStyle('Fail', parent=body_style, textColor=RED)
    small_style = ParagraphStyle('Small', parent=body_style, fontSize=8, textColor=GRAY)
    bold_style = ParagraphStyle('Bold', parent=body_style, fontName='Helvetica-Bold')
    cell_style = ParagraphStyle('Cell', parent=body_style, fontSize=9, leading=9*PHI, wordWrap='CJK')

    story = []

    # === PAGE 1: Title + Environment ===
    story.append(Paragraph("AgentSON Wiki Deployment<br/>Cheat Sheet", title_style))
    story.append(Paragraph("Full reproducibility record — bugs, CLI versions, exact outputs<br/>2026-07-05 | Author: Andrea Enning", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=AMBER))
    story.append(Spacer(1, 24))

    story.append(Paragraph("Environment", h1_style))
    env_data = [
        [Paragraph("<b>Component</b>", cell_style), Paragraph("<b>Value</b>", cell_style)],
        [Paragraph("OS", cell_style), Paragraph("Windows 10 (Build 19045.6456) — Italian locale", cell_style)],
        [Paragraph("Shell", cell_style), Paragraph("PowerShell 5.1 (not pwsh)", cell_style)],
        [Paragraph("Python", cell_style), Paragraph("3.12", cell_style)],
        [Paragraph("Git", cell_style), Paragraph("Latest (2026)", cell_style)],
        [Paragraph("GitHub Account", cell_style), Paragraph("andiekobbietks", cell_style)],
        [Paragraph("Repo", cell_style), Paragraph("andiekobbietks/AgentSON (public, master)", cell_style)],
        [Paragraph("Wiki Repo", cell_style), Paragraph("andiekobbietks/AgentSON.wiki.git (separate endpoint)", cell_style)],
        [Paragraph("OpenCode", cell_style), Paragraph("MiMo V2.5 Free via OpenCode", cell_style)],
        [Paragraph("OpenCode DB", cell_style), Paragraph("~/.local/share/opencode/opencode.db (1.7GB SQLite)", cell_style)],
    ]
    t = Table(env_data, colWidths=[100, 330])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), AMBER),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('GRID', (0, 0), (-1, -1), 0.5, GRAY),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, LIGHT_GRAY]),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(t)

    # === PAGE 2: What We Built + Step-by-step ===
    story.append(PageBreak())
    story.append(Paragraph("What We Built", h1_style))
    story.append(Paragraph("9 wiki pages pushed to github.com/andiekobbietks/AgentSON/wiki:", body_style))
    story.append(Spacer(1, 8))

    pages = ["Home — Landing page with 'Why This Exists' health data story",
             "Getting-Started — Install, export, search, fine-tune, view",
             "Schema — JSON Schema v1.1 reference",
             "Readers — 6 working + 27 planned tool readers",
             "ADRs — 11 Architecture Decision Records",
             "SOPs — 14 Standard Operating Procedures",
             "Coding-Standards — Non-negotiable code rules",
             "Mental-Models — How we think about problems",
             "Contributing — How to add readers, write tests, submit PRs"]
    for p in pages:
        story.append(Paragraph(f"• {p}", body_style))

    story.append(Spacer(1, 16))
    story.append(Paragraph("Step-by-Step (Exact Commands and Outputs)", h1_style))
    
    story.append(Paragraph("Step 1: Create Wiki Content Locally", h2_style))
    story.append(Paragraph("Command:", bold_style))
    story.append(Paragraph("New-Item -ItemType Directory -Path 'C:\\Users\\LLM-Test\\Documents\\agentsong\\wiki' -Force", code_style))
    story.append(Paragraph("Then created 9 markdown files using Python write() tool.", body_style))

    story.append(Paragraph("Step 2: Create Wiki on GitHub (Manual)", h2_style))
    story.append(Paragraph("Go to github.com/andiekobbietks/AgentSON/wiki → click 'Create the first page'", body_style))
    story.append(Paragraph("Result: 'Your Wiki was created.' banner appears", success_style))

    story.append(Paragraph("Step 3: Clone Wiki Repo", h2_style))
    story.append(Paragraph("Command:", bold_style))
    story.append(Paragraph("git clone https://github.com/andiekobbietks/AgentSON.wiki.git", code_style))
    story.append(Paragraph("Output:", bold_style))
    story.append(Paragraph("Cloning into 'AgentSON.wiki'...<br/>remote: Enumerating objects: 3, done.<br/>Receiving objects: 100% (3/3), done.", code_style))

    # === PAGE 3: Steps continued ===
    story.append(PageBreak())
    story.append(Paragraph("Step 4: Copy Files", h2_style))
    story.append(Paragraph("Command:", bold_style))
    story.append(Paragraph("copy agentsong\\wiki\\*.* AgentSON.wiki\\", code_style))
    story.append(Paragraph("Output:", bold_style))
    story.append(Paragraph("9 files copied: Home.md, Getting-Started.md, Schema.md, Readers.md, ADRs.md, SOPs.md, Coding-Standards.md, Mental-Models.md, Contributing.md", code_style))

    story.append(Paragraph("Step 5: Commit", h2_style))
    story.append(Paragraph("Commands:", bold_style))
    story.append(Paragraph("cd AgentSON.wiki<br/>git add .<br/>git commit -m 'Add wiki pages'", code_style))
    story.append(Paragraph("Output:", bold_style))
    story.append(Paragraph("[master 95badf9] Add wiki pages<br/>9 files changed, 996 insertions(+), 1 deletion(-)", code_style))

    story.append(Paragraph("Step 6: Push with Token in URL", h2_style))
    story.append(Paragraph("Commands:", bold_style))
    story.append(Paragraph("$token = Read-Host -Prompt 'Paste PAT' -AsSecureString<br/>$tokenPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto(<br/>    [Runtime.InteropServices.Marshal]::SecureStringToBSTR($token))<br/>git remote set-url origin<br/>    \"https://andiekobbietks:${tokenPlain}@github.com/andiekobbietks/AgentSON.wiki.git\"<br/>git push", code_style))
    story.append(Paragraph("Output:", bold_style))
    story.append(Paragraph("Enumerating objects: 13, done.<br/>Writing objects: 100% (11/11), 12.92 KiB | 2.58 MiB/s, done.<br/>To https://github.com/andiekobbietks/AgentSON.wiki.git<br/>e21356a..95badf9  master -> master", code_style))

    # === PAGE 4: Bugs ===
    story.append(PageBreak())
    story.append(Paragraph("Bugs Encountered", h1_style))
    
    bugs = [
        ("Bug 1: Fine-Grained Token Cannot Push to Wiki",
         "git push",
         "remote: Invalid username or token. Password authentication is not supported for Git operations.",
         "GitHub fine-grained tokens have separate wiki permission — must be explicitly granted. Default is deny.",
         "Use classic PAT with 'repo' scope (includes wiki)."),
        ("Bug 2: Password Authentication Deprecated",
         "git push (entered PAT as password when prompted)",
         "remote: Invalid username or token. Password authentication is not supported for Git operations.",
         "GitHub removed password auth for Git operations in 2021. PATs must be embedded in URL.",
         "Embed token in URL: https://USER:TOKEN@github.com/USER/REPO.git"),
        ("Bug 3: Cached Bad Credentials",
         "git push (after failed attempt, even with correct token)",
         "remote: Invalid username or token.",
         "Windows Credential Manager cached the failed attempt. Git uses cached creds automatically.",
         "git config --global --unset credential.helper<br/>git config --global credential.helper store"),
        ("Bug 4: Token Compromised by Sharing in Chat",
         "User pasted PAT into chat — visible to AI and potentially logged.",
         "Any entity with the token can push to all repos with 'repo' scope.",
         "Immediately delete compromised token at github.com/settings/tokens. Generate new one.",
         "Use $token = Read-Host -Prompt 'PAT' -AsSecureString (masked input)")
    ]
    
    for title, cmd, error, cause, fix in bugs:
        story.append(Paragraph(title, h2_style))
        story.append(Paragraph("Command that failed:", bold_style))
        story.append(Paragraph(cmd, code_style))
        story.append(Paragraph("Error:", bold_style))
        story.append(Paragraph(error, fail_style))
        story.append(Paragraph("Root cause:", bold_style))
        story.append(Paragraph(cause, body_style))
        story.append(Paragraph("Fix:", bold_style))
        story.append(Paragraph(fix, body_style))
        story.append(Spacer(1, 12))

    # === PAGE 5: Lessons + Obsolete + Working Method ===
    story.append(PageBreak())
    story.append(Paragraph("Lessons Learned", h1_style))
    lessons = [
        "Fine-grained tokens need explicit wiki scope — default is deny",
        "GitHub password auth is gone since 2021 — PAT must be in URL",
        "Cached creds persist across attempts — must clear credential helper",
        "Never share tokens in chat — compromised immediately",
        "Wiki is a separate git repo — different endpoint (.wiki.git suffix)",
        "Classic PAT with repo scope covers wiki — fine-grained requires extra permission",
        "Read-Host -AsSecureString masks input — prevents shoulder surfing",
        "Token in URL format: https://USER:TOKEN@github.com/USER/REPO.git",
        "ReportLab needs pip install first — not in default Python install",
        "Windows copy uses backslashes — not forward slashes like Linux/Mac",
    ]
    for i, lesson in enumerate(lessons, 1):
        story.append(Paragraph(f"{i}. {lesson}", body_style))

    story.append(Spacer(1, 16))
    story.append(Paragraph("Obsolete / Deprecated Commands", h1_style))
    obsolete = [
        "git push with password prompt → DEPRECATED 2021 → Embed PAT in URL",
        "git config credential.helper store → WORKS BUT INSECURE → Use Read-Host -AsSecureString",
        "Fine-grained token for wiki → INSUFFICIENT PERMS → Classic PAT or grant wiki scope",
    ]
    for item in obsolete:
        story.append(Paragraph(f"• {item}", body_style))

    story.append(Spacer(1, 16))
    story.append(Paragraph("The Working Method (Copy-Paste Ready)", h1_style))
    story.append(Paragraph("# 1. Generate classic PAT with repo scope at github.com/settings/tokens<br/># 2. Run these commands:", body_style))
    story.append(Paragraph("cd C:\\Users\\LLM-Test\\Documents<br/>git clone https://github.com/andiekobbietks/AgentSON.wiki.git<br/>copy agentsong\\wiki\\*.* AgentSON.wiki\\<br/>cd AgentSON.wiki<br/>git add .<br/>git commit -m 'Add wiki pages'<br/>$token = Read-Host -Prompt 'Paste PAT' -AsSecureString<br/>$tokenPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto(<br/>    [Runtime.InteropServices.Marshal]::SecureStringToBSTR($token))<br/>git remote set-url origin<br/>    \"https://andiekobbietks:${tokenPlain}@github.com/andiekobbietks/AgentSON.wiki.git\"<br/>git push", code_style))

    # === PAGE 6: File Locations + Remaining Tasks ===
    story.append(PageBreak())
    story.append(Paragraph("File Locations", h1_style))
    locations = [
        "Wiki source files: ~/Documents/agentsong/wiki/",
        "Cloned wiki repo: ~/Documents/AgentSON.wiki/",
        "Main repo: ~/Documents/agentsong/",
        "OpenCode DB: ~/.local/share/opencode/opencode.db",
        "Cheatsheet PDF: ~/Documents/agentsong/wiki/AgentSON_Wiki_Cheatsheet.pdf",
        "Session: FreeStyle Libre — ses_1069f6208ffe...XozEyNyMW6RXOO (slug: gentle-engine)",
        "Session: Current — ses_0cbd91919ffey...YUXTVAIBZXQu7 (slug: jolly-cabin)",
        "GitHub Repo: https://github.com/andiekobbietks/AgentSON",
        "GitHub Wiki: https://github.com/andiekobbietks/AgentSON/wiki",
    ]
    for loc in locations:
        story.append(Paragraph(f"• {loc}", body_style))

    story.append(Spacer(1, 16))
    story.append(Paragraph("Remaining Tasks", h1_style))
    tasks = [
        ("Wiki deployment", "DONE"),
        ("README 'Why This Exists' section", "DONE — committed locally"),
        ("Push README to remote", "TODO — needs PAT push"),
        ("Push ADR-011 + modified files", "TODO — needs PAT push"),
        ("Fix reader count (6 vs 7)", "DONE — fixed in README"),
    ]
    for task, status in tasks:
        color = GREEN if "DONE" in status else GRAY
        story.append(Paragraph(f"• {task} — <font color='{color}'>{status}</font>", body_style))

    # Footer
    story.append(Spacer(1, 24))
    story.append(HRFlowable(width="100%", thickness=2, color=AMBER))
    story.append(Spacer(1, 8))
    story.append(Paragraph("Generated by AgentSON deployment session — 2026-07-05 23:21 UTC+1<br/>Author: Andrea Enning (AndieKobbieTech) — andiekobbietks@outlook.com<br/>Model: MiMo V2.5 Free via OpenCode | License: Apache 2.0", small_style))

    doc.build(story)
    print("PDF generated: agentsong/wiki/AgentSON_Wiki_Cheatsheet.pdf")

if __name__ == "__main__":
    build_cheatsheet()
