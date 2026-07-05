"""
AgentSON Reader: chrome-devtools
================================

Reads session data from Chrome DevTools AI Assistance Markdown exports
(Chrome 148 export format and equivalent hand-rolled exports).

Chrome DevTools stores its AI Assistance history in `Preferences`
under `devtools.preferences.ai-assistance-history-entries` (a JSON-
encoded string). When the user clicks "Export conversation", Chrome
writes a Markdown file with this structure:

    # Exported Chat from Chrome DevTools AI Assistance
    **Export Timestamp (UTC):** 2026-06-02T14:17:27.115Z
    ---
    ## User
    download me through console this video
    User attached an image
    ## AI
    ### Analyzing data
    **Data used:**
    * Element's uid is 4.
    ...
    ### Checking video source
    Get the source URL of the video element...
    **Code executed:**
    ```
    const video = document.querySelector('video.video-stream.html5-main-video');
    ```
    **Data returned:**
    ```
    {"src":"blob:https://..."}
    ```
    ### Answer
    The video on YouTube uses Media Source Extensions...
    ## User
    cool go ahead and sort it out so it sdownloaed
    ...

This reader parses that Markdown into an AgentSON document. Each `### Foo`
subsection in an AI block becomes one or more AgentSON entries:

    "### Analyzing ... + **Data used:** bullets" -> context entry
    "### Analyzing ... + **Thought:** paragraph" -> thought entry
    "### <verb>-ing ... + **Code executed:** + **Data returned:**" -> action entry
    "### Answer" -> answer entry
    "### Side Effect" -> side-effect entry

Other subsection titles (e.g. "Listing network requests", "Capturing
current video frame") fall back to `action` if they contain fenced code,
otherwise `thought`. This is content-driven classification rather than
title-driven, so new Chrome export variants work without parser changes.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional


SCHEMA_URI = "https://agentson.dev/schema/v1.1.json"

# Regex patterns
H2_RE = re.compile(r"^##\s+(?P<title>.+?)\s*$", re.MULTILINE)
H3_RE = re.compile(r"^###\s+(?P<title>.+?)\s*$", re.MULTILINE)
FENCE_RE = re.compile(r"^(?P<fence>`{3,}|~{3,})(?P<lang>\w+)?\s*$")
META_RE = re.compile(r"^\*\*(?P<key>[^*]+):\*\*\s*(?P<value>.+?)\s*$")


def _strip_fences(text: str) -> str:
    """Strip opening/closing ``` fences, return inner text."""
    lines = text.splitlines()
    if not lines:
        return ""
    if FENCE_RE.match(lines[0]):
        lines = lines[1:]
    if lines and FENCE_RE.match(lines[-1]):
        lines = lines[:-1]
    return "\n".join(lines)


def _split_into_sections(md: str) -> List[tuple[str, str]]:
    """Split markdown by H2 boundaries. Returns list of (title, body)."""
    sections: List[tuple[str, str]] = []
    matches = list(H2_RE.finditer(md))
    for i, m in enumerate(matches):
        title = m.group("title").strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(md)
        body = md[start:end].strip("\n")
        sections.append((title, body))
    return sections


def _parse_meta(header: str) -> tuple[Dict, Optional[datetime]]:
    """Extract top-of-file metadata like Export Timestamp."""
    meta: Dict = {}
    created: Optional[datetime] = None
    for line in header.splitlines():
        m = META_RE.match(line.strip())
        if not m:
            continue
        key = m.group("key").strip()
        val = m.group("value").strip()
        if key == "Export Timestamp (UTC)":
            try:
                iso = val.replace("Z", "+00:00")
                created = datetime.fromisoformat(iso)
            except ValueError:
                pass
        else:
            meta[key] = val
    return meta, created


def _parse_analyzing_body(body: str) -> Optional[Dict]:
    """Inside an AI block, a section titled 'Analyzing ...' may carry:
        **Data used:** + bulleted list          -> context
        **Thought:** + paragraph                -> thought
    """
    text = body.strip()
    if text.startswith("**Data used:**"):
        rest = text[len("**Data used:**"):].strip()
        details: List[Dict] = []
        for line in rest.splitlines():
            line = line.strip()
            if not line.startswith("*"):
                continue
            line = line.lstrip("*").strip()
            m = re.match(r"^\*\*(?P<title>[^*]+):\*\*\s*(?P<text>.+)$", line)
            if m:
                details.append({"title": m.group("title").strip(), "text": m.group("text").strip()})
            else:
                details.append({"text": line})
        if details:
            return {"type": "context", "details": details}
        return None
    if text.startswith("**Thought:**"):
        return {"type": "thought", "text": text[len("**Thought:**"):].strip()}
    if text:
        return {"type": "thought", "text": text}
    return None


def _parse_action_body(title: str, body: str) -> Optional[Dict]:
    """Parse an `### <verb> ...` section as an action."""
    entry: Dict = {"type": "action", "title": title, "tool_call_id": f"tc_{hashlib.md5(title.encode()).hexdigest()[:8]}"}
    pattern = re.compile(
        r"(?:\*\*(?P<label>[^*]+):\*\*\s*)?"
        r"(?P<fence>```[\s\S]*?```)",
        re.MULTILINE,
    )
    for m in pattern.finditer(body):
        label = (m.group("label") or "").strip().lower()
        fence_text = _strip_fences(m.group("fence"))
        if "code" in label:
            entry["code"] = fence_text
        elif "data" in label or "output" in label or "return" in label:
            entry["output"] = fence_text
        else:
            if "code" not in entry:
                entry["code"] = fence_text
            else:
                entry["output"] = (entry.get("output", "") + "\n" + fence_text).strip()
    leftover = pattern.sub("", body).strip()
    if leftover:
        entry["thought"] = leftover
    # Infer tool name from title and code content.
    title_low = title.lower()
    code = entry.get("code", "")
    code_low = code.lower()
    if "capture" in title_low or "screenshot" in title_low or "toDataURL" in code or "canvas" in code_low:
        entry["tool"] = "browser.capture"
    elif "fetch" in title_low or "request" in title_low or "network" in title_low:
        entry["tool"] = "network.fetch"
    elif "read" in title_low or "cat" in title_low or "file" in title_low or "fs.read" in code_low:
        entry["tool"] = "file.read"
    elif "querySelector" in code or "document." in code or "browser" in title_low or "element" in title_low or "video" in title_low or "image" in title_low or "checking" in title_low or "inspecting" in title_low:
        entry["tool"] = "browser.evaluate"
    elif "console" in title_low:
        entry["tool"] = "console.run"
    else:
        entry["tool"] = "console.run"
    return entry if ("code" in entry or "output" in entry or "thought" in entry) else None


def _parse_side_effect_body(body: str) -> Optional[Dict]:
    """Parse an `### Side Effect` section."""
    entry: Dict = {"type": "side-effect"}
    text_lines: List[str] = []
    pattern = re.compile(
        r"(?:\*\*(?P<label>[^*]+):\*\*\s*)?"
        r"(?P<fence>```[\s\S]*?```)",
        re.MULTILINE,
    )
    last_end = 0
    for m in pattern.finditer(body):
        prose = body[last_end:m.start()].strip()
        if prose:
            text_lines.append(prose)
        label = (m.group("label") or "").strip().lower()
        fence_text = _strip_fences(m.group("fence"))
        if "code" in label:
            entry["code"] = fence_text
        elif "output" in label or "return" in label or "data" in label:
            entry["output"] = fence_text
        last_end = m.end()
    leftover = body[last_end:].strip()
    if leftover:
        text_lines.append(leftover)
    full_text = "\n\n".join(text_lines).strip()
    if full_text:
        entry["text"] = full_text
    return entry if ("text" in entry or "code" in entry or "output" in entry) else None


def _parse_answer_body(body: str) -> Dict:
    """Parse an `### Answer` section: free text."""
    text = body.strip()
    if text.startswith("### "):
        text = H3_RE.sub("", text, count=1).strip()
    return {"type": "answer", "text": text}


def _classify_section_body(title: str, body: str) -> Optional[Dict]:
    """Content-driven classification of an AI subsection."""
    low = (title or "").lower().strip()
    rest = body.strip()

    if low.startswith("answer"):
        return _parse_answer_body(rest)
    if low.startswith("side effect"):
        return _parse_side_effect_body(rest)
    if low.startswith("thought"):
        if not rest:
            return None
        return {"type": "thought", "text": rest}

    if rest.startswith("**Data used:**"):
        e = _parse_analyzing_body(rest)
        if e and e.get("details"):
            return e
        return None
    if rest.startswith("**Thought:**"):
        return {"type": "thought", "text": rest[len("**Thought:**"):].strip()}

    has_code_label = "**Code executed:**" in rest or "**Data returned:**" in rest or "**Output:**" in rest
    has_fence = "```" in rest
    if has_code_label or has_fence:
        return _parse_action_body(title, rest)

    if rest:
        return {"type": "thought", "text": f"{title}\n\n{rest}" if title else rest}
    return None


def _parse_ai_block(body: str) -> List[Dict]:
    """Parse an entire AI turn body into a list of AgentSON entries."""
    entries: List[Dict] = []
    sections = re.split(r"(?m)(?=^###\s)", body)
    for sec in sections:
        sec = sec.strip("\n")
        if not sec:
            continue
        h3 = H3_RE.match(sec)
        if not h3:
            plain = sec.strip()
            if plain:
                entries.append({"type": "thought", "text": plain})
            continue
        title = h3.group("title").strip()
        rest = sec[h3.end():].strip()
        entry = _classify_section_body(title, rest)
        if entry:
            entries.append(entry)
    return entries


def parse_markdown(md_text: str, source_filename: Optional[str] = None) -> Dict:
    """
    Convert a Chrome DevTools AI Markdown export to an AgentSON document.

    The returned document conforms to AgentSON spec v1.1 (with task, outcome,
    and observation entries supported when present in the source). It is
    backward-compatible with v1.0 readers.
    """
    first_h2 = H2_RE.search(md_text)
    header = md_text[: first_h2.start()] if first_h2 else md_text
    body = md_text[first_h2.start():] if first_h2 else md_text
    meta, created = _parse_meta(header)

    entries: List[Dict] = []
    sections = _split_into_sections(body)

    slug = "session"
    if source_filename:
        slug = Path(source_filename).stem
        if slug.startswith("devtools_"):
            slug = slug[len("devtools_"):]

    first_user_query = ""
    for title, sec_body in sections:
        if title.strip().lower() == "user":
            text = sec_body.strip()
            att = []
            if "User attached an image" in text:
                att.append({"kind": "image", "note": "User attached an image"})
                text = text.replace("User attached an image", "").strip()
            entry: Dict = {"type": "user-query", "text": text}
            if att:
                entry["attachments"] = att
            if not first_user_query:
                first_user_query = text
            entries.append(entry)
        elif title.strip().lower() == "ai":
            entries.extend(_parse_ai_block(sec_body))
        else:
            entries.append({"type": "side-effect", "text": f"{title}\n\n{sec_body.strip()}"})

    aid = f"{slug}-{created.strftime('%Y%m%d')}" if created else slug
    doc: Dict = {
        "$schema": SCHEMA_URI,
        "id": aid,
        "title": first_user_query[:120] if first_user_query else slug,
        "tool": {
            "name": "chrome-devtools",
            "version": "148-or-export",
            "session_id": aid,
        },
        "agent": {"name": "chrome-devtools-ai", "provider": "google", "variant": "high"},
        "entries": entries,
    }
    # v1.1 trajectory fields
    if first_user_query:
        doc["task"] = first_user_query[:200]
    answers = sum(1 for e in entries if e.get("type") == "answer")
    # Outcome = state of the session at end-of-file:
    # - last entry is an answer -> success (the agent delivered)
    # - 0 answers -> aborted (user spoke but agent didn't answer)
    # - last entry is a user-query with no following answer -> partial
    # - otherwise -> partial
    if answers == 0:
        doc["outcome"] = "aborted"
    elif entries and entries[-1].get("type") == "answer":
        doc["outcome"] = "success"
    else:
        doc["outcome"] = "partial"
    if created:
        doc["started_at"] = created.isoformat()
        doc["ended_at"] = created.isoformat()
    if "url" in meta:
        doc.setdefault("context", {})["url"] = meta["url"]
    doc["metadata"] = {
        "exported_at": datetime.utcnow().isoformat() + "Z",
        "source_filename": source_filename or "",
        "users": sum(1 for e in entries if e.get("type") == "user-query"),
        "answers": answers,
    }
    return doc


# ---------------------------------------------------------------------------
# Reader class + convenience functions
# ---------------------------------------------------------------------------

class ChromeDevtoolsReader:
    """Reads Chrome DevTools AI Assistance Markdown exports into AgentSON."""

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def read(self) -> Dict:
        """Read the Markdown file and return an AgentSON document."""
        text = self.path.read_text(encoding="utf-8")
        return parse_markdown(text, source_filename=self.path.name)

    @staticmethod
    def read_dir(dir_path: str | Path, pattern: str = "devtools_*.md") -> List[Dict]:
        """Read all matching Markdown files in a directory."""
        p = Path(dir_path)
        out: List[Dict] = []
        for md in sorted(p.glob(pattern)):
            text = md.read_text(encoding="utf-8")
            out.append(parse_markdown(text, source_filename=md.name))
        return out


def read(file_path: str | Path) -> Dict:
    """Convenience function to read a single Chrome DevTools MD export."""
    return ChromeDevtoolsReader(file_path).read()


def read_dir(dir_path: str | Path, pattern: str = "devtools_*.md") -> List[Dict]:
    """Convenience function to read all devtools_*.md files in a directory."""
    return ChromeDevtoolsReader.read_dir(dir_path, pattern)


def list_exports(dir_path: str | Path, pattern: str = "devtools_*.md") -> List[Dict]:
    """List Chrome DevTools export files in a directory, with metadata only."""
    p = Path(dir_path)
    out: List[Dict] = []
    for md in sorted(p.glob(pattern)):
        text = md.read_text(encoding="utf-8")
        doc = parse_markdown(text, source_filename=md.name)
        out.append({
            "path": str(md),
            "id": doc["id"],
            "title": doc.get("title", ""),
            "started_at": doc.get("started_at"),
            "outcome": doc.get("outcome"),
            "users": doc.get("metadata", {}).get("users", 0),
            "answers": doc.get("metadata", {}).get("answers", 0),
        })
    return out