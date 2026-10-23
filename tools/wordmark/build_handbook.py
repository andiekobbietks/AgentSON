"""Assemble the wordmark handbook PDF.

Reads the measured data produced by gen_data.py and the two content modules,
then builds the document. Page furniture (folio and running foot) is applied
here so the content modules stay about content.
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))

from reportlab.lib.units import mm
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate, Spacer

import content_a
import content_b
from handbook_style import (
    AMBER, CAPTION, CONTENT_W, INK, MARGIN, MUTED, PAGE, PAPER, para,
)

DATA = pathlib.Path(__file__).resolve().parent / "handbook_data.json"
OUT = pathlib.Path(__file__).resolve().parents[2] / "docs" / "wordmark-handbook.pdf"

TITLE = "The AgentSON Wordmark Handbook"


def furniture(canvas, doc):
    """Folio, rule and running foot. Amber appears only as a rule, never as
    ink for text -- section six measures why."""
    canvas.saveState()
    w, h = PAGE

    canvas.setStrokeColor(AMBER)
    canvas.setLineWidth(1.6)
    canvas.line(MARGIN, h - MARGIN + 7 * mm, w - MARGIN, h - MARGIN + 7 * mm)

    canvas.setFont("Helvetica", 7.2)
    canvas.setFillColor(MUTED)
    canvas.drawString(MARGIN, h - MARGIN + 9 * mm, TITLE)

    if doc.page > 1:
        canvas.setStrokeColor(AMBER)
        canvas.setLineWidth(0.9)
        canvas.line(MARGIN, MARGIN - 5 * mm, w - MARGIN, MARGIN - 5 * mm)
        canvas.setFont("Helvetica", 7.2)
        canvas.setFillColor(MUTED)
        canvas.drawString(MARGIN, MARGIN - 9 * mm,
                          "Compiled 21 October 2026  \u2022  shipped face: larry3d")
        canvas.setFont("Helvetica-Bold", 8)
        canvas.setFillColor(INK)
        canvas.drawRightString(w - MARGIN, MARGIN - 9 * mm, str(doc.page))
    canvas.restoreState()


def build():
    data = json.loads(DATA.read_text(encoding="utf-8"))

    story = []
    story += content_a.cover(data)
    story += content_a.why(data)
    story += content_a.lineage(data)
    story += content_a.survey(data)
    story += content_a.drawings(data)
    story += content_b.split_section(data)
    story += content_b.colour_section(data)
    story += content_b.three_d_section(data)
    story += content_b.failures_section(data)
    story += content_b.spec_section(data)
    story += content_b.appendices(data)

    OUT.parent.mkdir(parents=True, exist_ok=True)

    doc = BaseDocTemplate(
        str(OUT), pagesize=PAGE,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN + 10 * mm, bottomMargin=MARGIN,
        title=TITLE, author="AgentSON", subject="Wordmark design record",
        creator="reportlab",
    )
    frame = Frame(MARGIN, MARGIN, CONTENT_W, doc.height, id="body",
                  leftPadding=0, rightPadding=0, topPadding=0,
                  bottomPadding=0)
    doc.addPageTemplates([PageTemplate(id="main", frames=[frame],
                                       onPage=furniture)])
    doc.build(story)

    size = OUT.stat().st_size
    pages = doc.page
    print(f"built  : {OUT}")
    print(f"pages  : {pages}")
    print(f"bytes   : {size:,}")
    return OUT, pages, size


if __name__ == "__main__":
    build()
