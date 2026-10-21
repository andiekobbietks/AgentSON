"""Verify the handbook PDF by measurement, not by looking at it.

Extracts every text span with its bounding box and checks two things:
  1. nothing crosses the right margin (overflow),
  2. the shipped mark's rows survive as contiguous art rather than being
     reflowed by the layout engine.

Also renders selected pages to PNG so the result can be looked at.
"""
import pathlib
import pymupdf

# Derived artefact: previews are regenerated on demand and deliberately kept
# out of the repository, so they go to the system temp directory.
import tempfile

PDF = pathlib.Path(__file__).resolve().parents[2] / "docs" / "wordmark-handbook.pdf"
PNG = pathlib.Path(tempfile.gettempdir()) / "wordmark_handbook_preview"

MARGIN = 18 * 2.834645  # 18mm in points
PAGE_W = 595.2756
RIGHT_LIMIT = PAGE_W - MARGIN

doc = pymupdf.open(PDF)
print(f"pages        : {doc.page_count}")
print(f"metadata     : {doc.metadata.get('title')!r}")
print(f"right limit  : {RIGHT_LIMIT:.1f} pt (margin {MARGIN:.1f})")
print()

overflow = []
lines_by_page = {}
for pno in range(doc.page_count):
    page = doc[pno]
    blocks = page.get_text("dict")["blocks"]
    nlines = 0
    for b in blocks:
        if b.get("type") != 0:
            continue
        for line in b["lines"]:
            nlines += 1
            x0, y0, x1, y1 = line["bbox"]
            txt = "".join(s["text"] for s in line["spans"])
            if x1 > RIGHT_LIMIT + 0.5 and txt.strip():
                overflow.append((pno + 1, round(x1, 1), txt[:60]))
    lines_by_page[pno + 1] = nlines

print("lines of text per page:")
for p, n in lines_by_page.items():
    print(f"  page {p:>2}: {n:>4} lines")

print()
if overflow:
    print(f"OVERFLOW: {len(overflow)} line(s) cross the right margin")
    for p, x, t in overflow[:12]:
        print(f"  p{p} ends at {x} pt: {t!r}")
else:
    print("overflow: none — every line ends inside the right margin")

# Confirm the shipped mark's rows are present as real text, unreflowed.
print()
art = doc[2].get_text() if doc.page_count > 2 else ""
probe = "\\ \\ \\L\\ \\     __      __    ___\\ \\ ,_\\ \\,\\L\\_\\ \\ \\/\\ \\ \\ `\\\\ \\"
found_pages = []
for pno in range(doc.page_count):
    t = doc[pno].get_text()
    if probe in t.replace(" ", " ") and "L\\ \\" in t:
        found_pages.append(pno + 1)
print(f"larry3d row 3 located on page(s): {found_pages or 'not found'}")

PNG.mkdir(parents=True, exist_ok=True)
for pno in range(doc.page_count):
    pix = doc[pno].get_pixmap(dpi=100)
    out = PNG / f"page_{pno+1:02d}.png"
    pix.save(out)
print(f"rendered {doc.page_count} page previews at 100 dpi")
print(f"previews in {PNG}")
