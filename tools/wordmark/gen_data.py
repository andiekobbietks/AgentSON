"""Handbook data stage: render every face, and compute contrast properly.

Runs in the temp venv because it needs pyfiglet. Emits one JSON that the PDF
builder reads, so the document is assembled from measured values rather than
numbers typed into prose.

Contrast uses the WCAG 2.x relative-luminance definition:
    c = channel / 255
    c <= 0.04045 ? c/12.92 : ((c + 0.055)/1.055) ** 2.4
    L = 0.2126 R + 0.7152 G + 0.0722 B
    ratio = (Lmax + 0.05) / (Lmin + 0.05)

Thresholds used for the verdict column:
    >= 7.0   AAA body text
    >= 4.5   AA body text
    >= 3.0   AA large text / non-text UI  (block glyphs qualify here)
    <  3.0   FAILS
"""
import json
import pathlib
import pyfiglet

FACES = ["banner", "big", "doom", "standard", "slant", "ogre",
         "larry3d", "mini"]
SHIPPED = "larry3d"

# name, hex fg, hex bg -- covers terminal, editor, print and reversed cases
SWATCHES = [
    ("Terminal default dark", "#ffb000", "#000000"),
    ("GitHub dark",           "#ffb000", "#0d1117"),
    ("VS Code dark",          "#ffb000", "#1e1e1e"),
    ("Dim terminal",          "#ffb000", "#2b2b2b"),
    ("Terminal blue-black",   "#ffb000", "#1a1a2e"),
    ("Print / white paper",   "#ffb000", "#ffffff"),
    ("Off-white paper",       "#ffb000", "#fafafa"),
    ("Reversed: amber ground","#ffffff", "#ffb000"),
    ("Reversed: dark on amber","#1a1a1a","#ffb000"),
    ("Baseline black on white","#000000","#ffffff"),
    ("Baseline white on black","#ffffff","#000000"),
    ("Secondary green on dark","#a0d060","#000000"),
    ("Secondary blue on dark", "#5b9ef6", "#000000"),
    ("Muted grey on dark",     "#808080", "#000000"),
]

OUT = pathlib.Path(__file__).resolve().parents[2] / "tools" / "wordmark" \
      / "handbook_data.json"


def luminance(hexcolour: str) -> float:
    h = hexcolour.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    lin = lambda c: c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)


def contrast(fg: str, bg: str) -> float:
    a, b = luminance(fg), luminance(bg)
    hi, lo = max(a, b), min(a, b)
    return (hi + 0.05) / (lo + 0.05)


def verdict(ratio: float) -> str:
    if ratio >= 7.0:
        return "AAA"
    if ratio >= 4.5:
        return "AA"
    if ratio >= 3.0:
        return "AA-large"
    return "FAILS"


def render(face: str):
    art = pyfiglet.figlet_format("AgentSON", font=face)
    head = pyfiglet.figlet_format("Agent", font=face)
    lines = art.split("\n")
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    if not lines:
        return None
    width = max(len(l) for l in lines)
    lines = [l.ljust(width) for l in lines]
    head_lines = [l for l in head.split("\n") if l.strip()]
    return {
        "face": face,
        "rows": lines,
        "height": len(lines),
        "width": width,
        "son_start": max(len(l) for l in head_lines),
        "glyph_cells": len(lines) * width,
        "ink": sum(l.count("#") + l.count("\\") + l.count("/")
                   + l.count("_") + l.count("|") for l in lines),
    }


def main() -> None:
    faces = {}
    for f in FACES:
        got = render(f)
        if got:
            faces[f] = got

    swatches = []
    for label, fg, bg in SWATCHES:
        r = contrast(fg, bg)
        swatches.append({
            "label": label, "fg": fg, "bg": bg,
            "ratio": round(r, 2), "verdict": verdict(r),
        })

    data = {
        "faces": faces,
        "shipped": SHIPPED,
        "swatches": swatches,
        "brand": {
            "amber": "#ffb000",
            "green": "#a0d060",
            "blue": "#5b9ef6",
            "ansi_214": 214,
            "tagline": "The universal provenance format for agent sessions.",
        },
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, indent=1), encoding="utf-8")

    print(f"wrote {OUT}")
    print(f"faces: {len(faces)}")
    for k, v in faces.items():
        mark = " <== SHIPPED" if k == SHIPPED else ""
        print(f"  {k:<10} {v['height']:>2}r x {v['width']:>2}c  "
              f"son@{v['son_start']:>2}  cells={v['glyph_cells']:>4}"
              f"  ink={v['ink']:>4}{mark}")
    print()
    print("contrast matrix:")
    for s in swatches:
        flag = "  <-- FAILS" if s["verdict"] == "FAILS" else ""
        print(f"  {s['label']:<26} {s['fg']} on {s['bg']}  "
              f"{s['ratio']:>5.2f}:1  {s['verdict']}{flag}")


if __name__ == "__main__":
    main()
