"""Shared ReportLab styles, colours and flowables for the wordmark handbook.

Kept separate from the document body so the builder stays under the line-count
limit and so the cell styles are created once and reused, per the house rule.
"""
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Flowable, Paragraph, Preformatted, Spacer, Table, TableStyle,
)

# ----------------------------------------------------------------- palette
# Print-safe. The brand amber is deliberately absent from the ink set: it
# measures 1.83:1 on white and cannot carry text on paper. It appears only as
# a ground (dark ink on amber measures 9.50:1).
AMBER = colors.HexColor("#ffb000")
AMBER_DEEP = colors.HexColor("#8a5f00")
INK = colors.HexColor("#111111")
MUTED = colors.HexColor("#5a5a5a")
RULE = colors.HexColor("#c9c9c9")
SHADOW = colors.HexColor("#9a9a9a")
SHADOW_DEEP = colors.HexColor("#5c5c5c")
PAPER = colors.white
GROUND = colors.HexColor("#f4f1ea")

PAGE = A4
MARGIN = 18 * mm
CONTENT_W = PAGE[0] - 2 * MARGIN

_BASE = getSampleStyleSheet()


def _s(name, parent=None, **kw):
    return ParagraphStyle(name, parent=parent or _BASE["BodyText"], **kw)


class _Heading:
    """Lets a heading be written `H1 >> "Title"` at the call site.

    A bare ParagraphStyle cannot be shifted, and repeating the style argument
    on every heading is noise. This wrapper turns `>>` into a Paragraph and
    still passes through `para()` unchanged.
    """

    def __init__(self, style):
        self.style = style

    def __rshift__(self, text):
        return Paragraph(text, self.style)

    __rrshift__ = __rshift__

    def unwrap(self):
        return self.style


BODY = _s("Body", fontName="Times-Roman", fontSize=10, leading=14,
          spaceAfter=6, alignment=TA_LEFT, textColor=INK)
LEAD = _s("Lead", parent=BODY, fontSize=11.5, leading=16, spaceAfter=9,
          textColor=colors.HexColor("#333333"))
H1 = _Heading(_s("H1", fontName="Helvetica-Bold", fontSize=17, leading=21,
                 spaceBefore=14, spaceAfter=8, textColor=INK))
H2 = _Heading(_s("H2", fontName="Helvetica-Bold", fontSize=12.5, leading=16,
                 spaceBefore=11, spaceAfter=5, textColor=INK))
H3 = _Heading(_s("H3", fontName="Helvetica-BoldOblique", fontSize=10.5,
                 leading=14, spaceBefore=8, spaceAfter=3, textColor=MUTED))
CAPTION = _s("Caption", fontName="Helvetica-Oblique", fontSize=8, leading=11,
             spaceBefore=3, spaceAfter=10, textColor=MUTED)
CELL = _s("Cell", fontName="Times-Roman", fontSize=8.2, leading=10.5,
          spaceAfter=0, textColor=INK)
CELL_B = _s("CellB", parent=CELL, fontName="Times-Bold")
CELL_H = _s("CellH", parent=CELL, fontName="Helvetica-Bold", fontSize=8.2,
            textColor=colors.white)
MONO = _s("Mono", fontName="Courier", fontSize=8, leading=10.5,
          textColor=INK)
BULLET = _s("Bullet", parent=BODY, leftIndent=11, bulletIndent=2,
            spaceAfter=3)
QUOTE = _s("Quote", parent=BODY, fontName="Times-Italic", leftIndent=14,
           rightIndent=10, textColor=MUTED, spaceBefore=4, spaceAfter=8)

# Art sizing is computed, not guessed: Courier is 0.6 em wide, so N columns
# need N * 0.6 * size points. 65 columns is the widest face (larry3d).
ART_SIZE = 8.6
ART_LEAD = 9.3
ART_STYLE = _s("Art", fontName="Courier", fontSize=ART_SIZE, leading=ART_LEAD,
               textColor=INK, spaceBefore=2, spaceAfter=2)


# ---------------------------------------------------------------- helpers
def para(text, style=BODY) -> Paragraph:
    if isinstance(style, _Heading):
        style = style.unwrap()
    return Paragraph(text, style)


def bullets(items, style=BULLET) -> list:
    return [Paragraph(f"&bull;&nbsp;&nbsp;{t}", style) for t in items]


def grid(header, rows, widths, align_right=()) -> Table:
    """Build a table whose every cell is a Paragraph.

    Plain strings do not wrap and overflow the column; wrapping every cell is
    the only reliable fix, so this helper is the single path to a table.
    """
    data = [[Paragraph(h, CELL_H) for h in header]]
    for r in rows:
        line = []
        for i, cell in enumerate(r):
            st = CELL_B if i == 0 else CELL
            line.append(Paragraph(str(cell), st))
        data.append(line)

    t = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2f2f2f")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("LINEBELOW", (0, 0), (-1, -1), 0.4, RULE),
        ("LINEBELOW", (0, 0), (-1, 0), 0.8, colors.HexColor("#000000")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, GROUND]),
    ]
    for col in align_right:
        style.append(("ALIGN", (col, 1), (col, -1), "RIGHT"))
    t.setStyle(TableStyle(style))
    return t


def callout(title, body_text) -> Table:
    """A bordered note. Used for measured findings that drive a decision."""
    inner = [Paragraph(title, CELL_B), Spacer(1, 2),
             Paragraph(body_text, CELL)]
    t = Table([[inner]], colWidths=[CONTENT_W], hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), GROUND),
        ("LINEBEFORE", (0, 0), (0, -1), 2.2, AMBER),
        ("BOX", (0, 0), (-1, -1), 0.4, RULE),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    return t


# ------------------------------------------------------------ flowables
class ArtBlock(Flowable):
    """Two-tone wordmark: Agent in one ink, SON in another, split by column.

    Drawn as one canvas text object per row with the two spans positioned by
    absolute x, because a monospace grid only aligns if every character sits on
    a fixed advance.
    """

    def __init__(self, rows, son_start, fg_agent, fg_son, size=ART_SIZE,
                 lead=ART_LEAD, align="LEFT", width=None):
        super().__init__()
        self.rows = rows
        self.son_start = son_start
        self.fg_agent = fg_agent
        self.fg_son = fg_son
        self.size = size
        self.lead = lead
        self.align = align
        self.charw = size * 0.6
        self.width = width or (max(len(r) for r in rows) * self.charw)
        self.height = len(rows) * lead

    def wrap(self, aw, ah):
        return self.width, self.height

    def draw(self):
        c = self.canv
        x0 = 0
        if self.align == "CENTER":
            x0 = (self.width - max(len(r) for r in self.rows) * self.charw) / 2
        c.setFont("Courier", self.size)
        for i, row in enumerate(self.rows):
            y = self.height - (i + 1) * self.lead + (self.lead - self.size) / 2
            head = row[:self.son_start]
            tail = row[self.son_start:]
            if head.strip():
                c.setFillColor(self.fg_agent)
                c.drawString(x0, y, head)
            if tail.strip():
                c.setFillColor(self.fg_son)
                c.drawString(x0 + len(head) * self.charw, y, tail)


class ShadowArt(ArtBlock):
    """Three-layer 3D treatment: far shadow, near shadow, then the face.

    A terminal cannot shade, so this effect exists only on the page. Each layer
    is drawn with the canvas translated rather than by rewriting row text, so
    the two-tone split logic is inherited unchanged. Offsets are a fraction of
    the cap height so the effect survives reduction without the layers merging.
    """

    def __init__(self, *a, deep=SHADOW_DEEP, near=SHADOW, dx=None, dy=None,
                 **kw):
        super().__init__(*a, **kw)
        self.deep, self.near = deep, near
        step = self.size * 0.11
        self.dx = dx if dx is not None else step
        self.dy = dy if dy is not None else step

    def draw(self):
        c = self.canv
        top_agent, top_son = self.fg_agent, self.fg_son
        for ox, oy, ink in ((2 * self.dx, -2 * self.dy, self.deep),
                            (self.dx, -self.dy, self.near)):
            self.fg_agent = self.fg_son = ink
            c.saveState()
            c.translate(ox, oy)
            ArtBlock.draw(self)
            c.restoreState()
        self.fg_agent, self.fg_son = top_agent, top_son
        ArtBlock.draw(self)
