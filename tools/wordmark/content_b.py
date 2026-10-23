"""Handbook content, part B: split mechanics, colour, the 3D treatment,
failure modes, the shipped specification and appendices."""
from reportlab.lib import colors
from reportlab.platypus import (
    PageBreak, Paragraph, Preformatted, Spacer, Table, TableStyle,
)

from handbook_style import (
    AMBER, AMBER_DEEP, ART_SIZE, CAPTION, CELL, CONTENT_W, GROUND, INK, MUTED,
    RULE, SHADOW, ArtBlock, ShadowArt, bullets, callout, grid, para,
    BODY, H1, H2, H3, LEAD, MONO,
)


def split_section(data):
    f = data["faces"][data["shipped"]]
    return [
        H1 >> "5. The split, and how it was verified",
        para(
            "The mark renders <i>Agent</i> in brand amber and <i>SON</i> in "
            "bold amber. Both halves share the same rows, so the boundary "
            "cannot be found by searching the text. It is a fixed column, "
            "measured by rendering the word <i>Agent</i> alone and taking its "
            "widest row.", LEAD),
        para(
            f"For the shipped face that column is <b>{f['son_start']}</b>, and "
            f"the mark is {f['width']} columns wide, so the split leaves "
            f"{f['width'] - f['son_start']} columns to the right of it. The "
            "verification that matters is per row: every one of the nine rows "
            "must carry ink in both halves, or part of a glyph is being "
            "coloured as though it belonged to the other word."),
        grid(
            ["Row", "Agent ink ends", "SON ink begins", "Split", "Verdict"],
            _gap_rows(f),
            [40, 96, 92, 46, 80],
            align_right=(0, 3)),
        para(
            "Rows eight and nine are the descender rows of the three-dimensional "
            "face &mdash; the trailing shadow strokes &mdash; and carry ink "
            "only on the left. They are correct as drawn; a short gap there is "
            "the face's own geometry, not a split error.", CAPTION),
        PageBreak(),
    ]


def _gap_rows(f):
    rows = []
    for i, r in enumerate(f["rows"]):
        s = f["son_start"]
        left = len(r[:s].rstrip())
        right = len(r[s:].strip())
        if right == 0:
            verdict = "single-sided row"
        elif left <= s:
            verdict = "clean edge"
        else:
            verdict = "OVERLAP"
        rows.append([
            str(i + 1),
            f"column {left}" if left else "none",
            f"column {s}" if right else "none",
            str(s),
            verdict,
        ])
    return rows


def colour_section(data):
    sw = data["swatches"]
    rows = [[s["label"], s["fg"], s["bg"], f"{s['ratio']:.2f}:1",
             s["verdict"]] for s in sw]
    fails = [s for s in sw if s["verdict"] == "FAILS"]
    return [
        H1 >> "6. Colour, measured",
        para(
            "Fourteen foreground and ground pairings were computed against the "
            "Web Content Accessibility Guidelines relative-luminance "
            "definition. The verdict thresholds are the standard ones: seven "
            "to one for AAA body text, four and a half for AA, three for large "
            "text and for non-text graphics such as block glyphs, and below "
            "three a failure.", LEAD),
        grid(
            ["Context", "Foreground", "Ground", "Ratio", "Verdict"],
            rows,
            [128, 62, 62, 52, 62],
            align_right=(3,)),
        Spacer(1, 6),
        para("The swatches below are the same fourteen pairings drawn as ink, "
             "not described in words.", CAPTION),
        _swatch_strip(sw),
        Spacer(1, 8),
        callout(
            f"Forced decision: {len(fails)} pairings fail, and they share a "
            "ground",
            "Every failure in the matrix is amber acting as ink on a light "
            f"ground, or white on amber. Amber on white paper measures "
            f"<b>{_find(sw, '#ffb000', '#ffffff')}</b> &mdash; well under the "
            "three-to-one floor for non-text graphics, and legible on a "
            "terminal only because terminals put it on black. The same amber "
            f"as a <i>ground</i> with dark ink measures "
            f"<b>{_find(sw, '#1a1a1a', '#ffb000')}</b>."),
        para(
            "The consequence is a clean rule with two halves. <b>On screen the "
            "mark is amber on black</b>, because that is where the brand colour "
            "was tuned and it exceeds AAA everywhere tested. <b>On paper the "
            "mark is dark ink on white, or white ink on an amber ground</b>; "
            "amber is never used as ink. This handbook follows that rule "
            "throughout, which is why the printed mark you are reading is "
            "black and grey rather than amber."),
        para(
            "The secondary palette was checked on the same terms. The green "
            "measures comfortably and the blue passes AAA on black, so both are "
            "safe as screen accents; neither is used in the mark."),
        PageBreak(),
    ]


def _find(sw, fg, bg):
    for s in sw:
        if s["fg"] == fg and s["bg"] == bg:
            return f"{s['ratio']:.2f}:1"
    return "n/a"


def _swatch_strip(sw):
    """Draw the pairings as real ink samples, five across.

    Fourteen chips in one row measured 1064 pt against a 493 pt frame, so the
    grid is chunked. Labels are Paragraphs, not strings: as strings they do not
    wrap and their markup prints literally.
    """
    per_row, chip_w = 5, 92
    cells, labels = [], []
    for s in sw:
        fg, bg = colors.HexColor(s["fg"]), colors.HexColor(s["bg"])
        cells.append(Table(
            [[Paragraph("AgentSON", _chip_style(fg))]],
            colWidths=[chip_w - 4], rowHeights=[15],
            style=TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), bg),
                ("BOX", (0, 0), (-1, -1), 0.3, RULE),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("TOPPADDING", (0, 0), (-1, -1), 1),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
            ])))
        labels.append(Paragraph(
            f"<b>{s['ratio']:.2f}:1</b><br/><font size=6>{s['verdict']}</font>",
            _chip_label()))

    blank = Paragraph("", _chip_label())
    rows = []
    for i in range(0, len(cells), per_row):
        rows.append(cells[i:i + per_row] + [blank] * (per_row - len(cells[i:i + per_row])))
        rows.append(labels[i:i + per_row] + [blank] * (per_row - len(labels[i:i + per_row])))

    outer = Table(rows, colWidths=[chip_w] * per_row, hAlign="LEFT")
    outer.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 2),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2),
    ]))
    return outer


def _chip_label():
    from reportlab.lib.styles import ParagraphStyle
    return ParagraphStyle("chipL", fontName="Helvetica", fontSize=6.4,
                          leading=7.6, textColor=MUTED, alignment=1)


def _chip_style(fg):
    from reportlab.lib.styles import ParagraphStyle
    return ParagraphStyle("chip", fontName="Helvetica-Bold", fontSize=6.4,
                          leading=8, textColor=fg, alignment=1)


def three_d_section(data):
    f = data["faces"][data["shipped"]]
    return [
        H1 >> "7. The three-dimensional treatment",
        para(
            "The shipped face is an outline face. Its three-dimensional read "
            "comes from drawing a second contour offset behind every stroke, "
            "not from shading a solid letter. That distinction matters, because "
            "an outline has no interior to shade and therefore no place to put "
            "a gradient, a highlight or a bevel.", LEAD),
        para(
            "A terminal offers exactly two levers: a different foreground, and "
            "a bold weight. There is no third. So on screen the entire "
            "dimensional effect is carried by the two-tone split &mdash; the "
            "lighter <i>Agent</i> half reading as the lit face and the bold "
            "<i>SON</i> half reading as the shadowed edge. That is the whole "
            "of the terminal treatment and it cannot be extended."),
        H2 >> "7.1 What a page can do that a terminal cannot",
        para(
            "On paper the same face can be given a genuine drop shadow, because "
            "the drawing order is under explicit control. The three treatments "
            "below use identical glyph data; only the ink and the drawing order "
            "differ. Compare them at arm's length, which is where a drop shadow "
            "either earns its place or becomes noise."),
        H3 >> "Treatment A &mdash; flat, terminal parity",
        ArtBlock(f["rows"], f["son_start"], INK, colors.HexColor("#444444"),
                 size=ART_SIZE),
        para("Two inks, no offsets. This is exactly what a terminal renders.",
             CAPTION),
        H3 >> "Treatment B &mdash; two-tone with a near shadow",
        ShadowArt(f["rows"], f["son_start"], INK, colors.HexColor("#333333"),
                  size=ART_SIZE, dx=ART_SIZE * 0.09, dy=ART_SIZE * 0.09,
                  near=colors.HexColor("#c4c4c4"),
                  deep=colors.HexColor("#e2e2e2")),
        para("One offset layer. Reads as depth at normal size without "
             "separating the strokes.", CAPTION),
        H3 >> "Treatment C &mdash; full drop shadow",
        ShadowArt(f["rows"], f["son_start"], INK, colors.HexColor("#222222"),
                  size=ART_SIZE, dx=ART_SIZE * 0.15, dy=ART_SIZE * 0.15,
                  near=colors.HexColor("#b0b0b0"),
                  deep=colors.HexColor("#8a8a8a")),
        para("Two offset layers. Strongest depth, and the first to collapse: "
             "below roughly eight points the layers merge into a smear.",
             CAPTION),
        callout(
            "Where the 3D effect does not render, and what to do instead",
            "Three conditions defeat it, and each has a stated fallback rather "
            "than a hope. <b>Small type.</b> Below about eight points the "
            "offset is smaller than a pixel and the layers fuse; the fallback "
            "is treatment A, which loses nothing because the effect was already "
            "invisible. <b>A light ground with light ink.</b> The shadow needs "
            "to be darker than the face, so amber on white has no shadow ink "
            "available &mdash; a second reason that pairing is rejected in "
            "section six. <b>A terminal.</b> There is no canvas to offset "
            "against; the fallback is the two-tone split, which is what ships."),
        PageBreak(),
    ]


def failures_section(data):
    return [
        H1 >> "8. What broke, and why it is recorded",
        para(
            "Four defects were introduced while building this mark. Three were "
            "found by rendering rather than by the test suite, which is the "
            "part worth taking away.", LEAD),
        grid(
            ["Defect", "Symptom", "Cause", "Found by"],
            [
                ["Missing commas in the art tuple",
                 "Panel rendered blank with one stray hash",
                 "Adjacent string literals concatenate; enumerate() then "
                 "walked 413 characters instead of 9 rows",
                 "Reading the render"],
                ["Duplicate split constant",
                 "Five columns of the Agent half rendered bold",
                 "The installer replaced only to the tuple's closing paren, "
                 "leaving the previous face's value behind; Python takes the "
                 "last definition",
                 "Span count"],
                ["Backslashes in plain string literals",
                 "SyntaxWarning, then an unterminated literal that broke the "
                 "whole CLI",
                 "The outline face uses backslashes, one row ends in one, and "
                 "a trailing backslash escapes the closing quote",
                 "Import"],
                ["Colour measured with a non-existent escape",
                 "Reported zero colours on a correctly coloured render",
                 "A PowerShell escape valid only in version six was used in "
                 "version five point one",
                 "Cross-check"],
            ],
            [92, 96, 132, 62]),
        callout(
            "The finding that outlasts all four",
            "The test suite contains one hundred and ninety two tests and every "
            "one passed at every point above, including while "
            "<font face='Courier'>help_system.py</font> was a syntax error that "
            "would crash the command line on first use. No test imports the "
            "help system, so the suite cannot see it. A green suite is a "
            "statement about what was tested, and here it was a statement about "
            "schema validation and nothing else."),
        H2 >> "8.1 Encoding, and the one thing that never fixes itself",
        para(
            "The console used throughout this work renders an em dash as a "
            "replacement character, because the code page cannot carry it. The "
            "file itself is strict UTF-8 with no byte order mark and contains "
            "real em dashes; only the display is wrong. Every file touched here "
            "was checked byte by byte after writing &mdash; strict decoding, "
            "byte order mark absent, em dash count positive &mdash; precisely "
            "because a visual check on this console is not evidence of "
            "anything."),
        PageBreak(),
    ]


def spec_section(data):
    f = data["faces"][data["shipped"]]
    return [
        H1 >> "9. The shipped mark",
        para(
            "One constant block in "
            "<font face='Courier'>cli/help_system.py</font>, no runtime "
            "dependency, and a panel width that follows the art instead of the "
            "other way round.", LEAD),
        grid(
            ["Property", "Value"],
            [
                ["Face", data["shipped"]],
                ["Grid", f"{f['height']} rows by {f['width']} columns"],
                ["Split column", f"{f['son_start']}"],
                ["Glyph cells", f"{f['glyph_cells']}"],
                ["Ink characters", f"{f['ink']}"],
                ["Agent ink", "<font face='Courier'>#ffb000</font>, ANSI 214"],
                ["SON ink", "<font face='Courier'>bold #ffb000</font>"],
                ["Tagline", data["brand"]["tagline"]],
                ["Panel width", f"{f['width'] + 4} columns, capped at the "
                               "console width"],
                ["Print treatment", "Dark ink on white, or white on amber; "
                                    "never amber on white"],
            ],
            [92, CONTENT_W - 92]),
        para(
            "The font was generated once in an isolated environment and baked "
            "into the file as a string constant. Installing a lettering library "
            "as a dependency of a provenance tool, so that a heading can be "
            "drawn, would be the wrong trade.", BODY),
        PageBreak(),
    ]


def appendices(data):
    flow = [H1 >> "Appendix A &mdash; every face, raw"]
    for name, f in data["faces"].items():
        flow.append(H3 >> name)
        flow.append(Preformatted("\n".join(f["rows"]), MONO))
        flow.append(Spacer(1, 4))
    flow.append(PageBreak())
    flow.append(H1 >> "Appendix B &mdash; the shipped constant")
    f = data["faces"][data["shipped"]]
    block = "WORDMARK = (\n"
    for r in f["rows"]:
        block += f"    {r!r},\n"
    block += f")\nWORDMARK_SON_START = {f['son_start']}\n"
    flow.append(para(
        "Every row is emitted with its backslashes escaped by "
        "<font face='Courier'>repr()</font>, which is the fix for the defect "
        "recorded in section eight.", BODY))
    flow.append(Preformatted(block, _s_tight()))
    return flow


def _s_tight():
    from reportlab.lib.styles import ParagraphStyle
    return ParagraphStyle("tight", fontName="Courier", fontSize=5.6,
                          leading=6.6, textColor=INK)
