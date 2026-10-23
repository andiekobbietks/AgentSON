"""Handbook content, part A: cover, lineage, the survey, and the drawings."""
from reportlab.lib.units import mm
from reportlab.platypus import PageBreak, Preformatted, Spacer

from handbook_style import (
    AMBER, AMBER_DEEP, ART_SIZE, CAPTION, INK, MUTED, PAPER, GROUND,
    ArtBlock, ShadowArt, _s, bullets, callout, grid, para, BODY, H1, H2, H3,
    LEAD, MONO,
)

DATE = "21 October 2026"


def cover(data):
    f = data["faces"][data["shipped"]]
    return [
        Spacer(1, 26 * mm),
        para("AgentSON", _s("CoverKicker", fontName="Helvetica-Bold",
                            fontSize=11, leading=14, textColor=MUTED,
                            spaceAfter=4)),
        para("The Wordmark Handbook",
             _s("CoverTitle", fontName="Helvetica-Bold", fontSize=27,
                leading=31, textColor=INK, spaceAfter=10)),
        para("Attempts, lineage, colour and the shipped mark",
             _s("CoverSub", fontName="Times-Italic", fontSize=13, leading=17,
                textColor=MUTED, spaceAfter=16)),
        ShadowArt(f["rows"], f["son_start"], AMBER, INK, size=ART_SIZE + 1.4,
                  lead=ART_SIZE + 2.2),
        Spacer(1, 8 * mm),
        para(f"{data['brand']['tagline']}",
             _s("CoverTag", fontName="Times-Italic", fontSize=11, leading=15,
                textColor=MUTED, spaceAfter=4)),
        Spacer(1, 4 * mm),
        para(f"Compiled {DATE} &nbsp;&bull;&nbsp; shipped face: "
             f"<b>{data['shipped']}</b> &nbsp;&bull;&nbsp; "
             f"brand amber <font face='Courier'>#ffb000</font>, "
             f"ANSI index 214",
             _s("CoverMeta", fontName="Helvetica", fontSize=8.5, leading=12,
                textColor=MUTED)),
        PageBreak(),
    ]


def why(data):
    return [
        H1 >> "1. Why this handbook exists",
        para(
            "The AgentSON command line had no mark. It had a boxed heading and "
            "a table of contents, and that was the whole of its visual "
            "identity. Three separate taglines had accumulated in one file, "
            "each slightly different from the others. There was no version "
            "string at all: <font face='Courier'>--version</font> was rejected "
            "by the argument parser, and the packaging metadata still declared "
            "a version two releases behind the newest tag."),
        para(
            "This handbook records what was drawn, what was measured, what was "
            "rejected and why, so that the choice of mark is auditable rather "
            "than a matter of taste asserted once and forgotten. Where a "
            "decision rests on a number, the number was computed, and the "
            "method is stated. Where a decision rests on judgement, it is "
            "labelled as judgement."),
        callout(
            "What was actually decided",
            "One face was drawn and shipped: <b>larry3d</b>, split by fixed "
            "column so that <i>Agent</i> renders in brand amber and "
            "<i>SON</i> in bold amber. Eight faces were surveyed and measured. "
            "One colour decision was forced by measurement: the brand amber "
            "cannot be used as ink on paper."),
        para(
            "Two failure modes deserve to be recorded here rather than quietly "
            "corrected, because they are the interesting part. The first is "
            "that a missing comma turned seven art rows into one four hundred "
            "and thirteen character string. The second is that a test suite of "
            "one hundred and ninety two tests passed throughout, with the help "
            "system in a state that would crash the CLI on first use."),
        PageBreak(),
    ]


def lineage(data):
    return [
        H1 >> "2. Lineage: how a character becomes a banner",
        para(
            "Every large letter in this document is an illusion maintained by "
            "three separate inventions stacked on top of each other. Knowing "
            "which layer does what is what lets you change a face, recolour it, "
            "or move it to a page without breaking it.",
            LEAD),

        H2 >> "2.1 The first constraint: ninety-five glyphs",
        para(
            "ASCII was standardised in 1963 and gave the terminal one hundred "
            "and twenty eight code points, of which ninety five are printable. "
            "A banner built in a terminal can therefore only be assembled from "
            "those ninety five shapes. That is a hard ceiling, and it is why "
            "early computer lettering looks the way it does: heavy, blocky, "
            "and assembled from whatever dense character was available."),
        para(
            "This constraint is not merely historical. It is the reason the "
            "<font face='Courier'>banner</font> face in the survey is built "
            "entirely from the hash character. A hash survives every code page, "
            "every font substitution and every terminal that can render ASCII "
            "at all. Faces that reach outside that set inherit whatever can go "
            "wrong outside it."),
        *bullets([
            "<b>banner</b> uses the hash character &mdash; pure ASCII, no "
            "dependency beyond a code page that contains ASCII.",
            "<b>larry3d</b>, the shipped face, uses the backslash, underscore, "
            "pipe, slash, space and grave accent &mdash; also pure ASCII, but "
            "the backslash is a live escape character in several languages, "
            "which is a property of the host language rather than of the art.",
            "Faces built from Unicode block elements add roughly two hundred "
            "glyphs of drawing material, and lose every terminal that cannot "
            "encode them.",
        ]),

        H2 >> "2.2 FIGlet and the fixed grid",
        para(
            "FIGlet appeared in 1991 and turned the craft into a solved "
            "problem. A FIGlet font is a file of glyph grids: every character "
            "is stored as the same number of rows, and rendering a word means "
            "laying those grids side by side. This machine has five hundred and "
            "seventy one such fonts installed; eight were surveyed for this "
            "mark."),
        para("A glyph for the digit two, drawn as a five row grid, looks "
             "conceptually like this:", H3),
        Preformatted(
            "  ___   \n"
            " / _ \\  \n"
            "| | | | \n"
            "| |_| | \n"
            " \\___/  \n",
            MONO),
        para(
            "Five rows is the usual minimum that still reads as a letter. The "
            "surveyed faces range from four rows (<font face='Courier'>mini"
            "</font>) to nine (<font face='Courier'>larry3d</font>), and row "
            "count is the single strongest predictor of how much vertical room "
            "a mark consumes in a terminal that is already showing content.", BODY),

        H2 >> "2.3 The two mechanics that make it fit",
        para(
            "Two details decide whether a rendered word looks correct or "
            "shambolic, and both are invisible in the output."),
        *bullets([
            "<b>The hardblank.</b> A FIGlet font reserves one character as a "
            "placeholder for the space inside a glyph. It is substituted for a "
            "real space at render time. If the font's hardblank collides with a "
            "character the art actually uses, the substitution destroys the "
            "glyph. Faces built from backslashes are the case to watch.",
            "<b>Smushing.</b> Placing grids side by side leaves gaps. FIGlet "
            "can simply pad them, or it can fuse adjacent characters where "
            "their edges are compatible. Smushing is what makes a face look "
            "tight; it is also what makes a face width unpredictable, which is "
            "why every face in this survey was measured after rendering rather "
            "than reasoned about from the font definition.",
        ]),
        callout(
            "Why the split is a column and not a string",
            "Because rows are shared. In the shipped mark, the <i>Agent</i> "
            "half and the <i>SON</i> half occupy the same rows, and two of the "
            "nine rows contain ink from only one of them. Searching the "
            "rendered text for the letter S would find several candidates and "
            "no way to choose between them. A fixed column &mdash; forty, "
            "measured from rendering <i>Agent</i> alone &mdash; is the only "
            "deterministic boundary."),

        H2 >> "2.4 From glyph grid to colour",
        para(
            "Once the grid exists, colour is a separate concern and is carried "
            "out of band. A terminal receives an escape sequence that changes "
            "the state of subsequent characters; the characters themselves are "
            "unchanged. The sequences this mark emits are the select-graphic-"
            "rendition family: one for the foreground in the two hundred and "
            "fifty six colour cube, and one for bold."),
        Preformatted(
            "  Agent   \\x1b[38;5;214m   foreground 214  (amber #ffb000)\n"
            "  SON     \\x1b[1m\\x1b[38;5;214m   bold, same foreground\n"
            "  reset   \\x1b[0m\n",
            MONO),
        para(
            "The library that renders this help system models colour as a "
            "sequence of styled spans over a single text object, and converts "
            "them to escapes at output time. That indirection is what allows "
            "the same wordmark to be emitted to a terminal and drawn to a page "
            "without being rewritten, and it is the mechanism this handbook "
            "inspected to prove the two halves were styled separately."),

        H2 >> "2.5 What changes when it becomes a page",
        para(
            "Moving the mark onto paper removes three things at once, and each "
            "removal forces a decision that the terminal never raised."),
        *bullets([
            "<b>State does not persist.</b> A terminal colour is sticky between "
            "characters. A page has no state; every element is painted "
            "explicitly. The mark is therefore drawn twice per row, once per "
            "ink, at an absolutely computed position.",
            "<b>Colour becomes ink.</b> A bright amber that reads comfortably "
            "on a black ground has no useful lightness contrast against white "
            "paper. Section six measures this and the result decides the print "
            "treatment.",
            "<b>Monospace becomes a real font.</b> Courier has a fixed advance "
            "width of six tenths of an em, which preserves the grid exactly. "
            "A proportional face would not, and would destroy the mark "
            "silently rather than obviously.",
        ]),
        PageBreak(),
    ]


def survey(data):
    faces = data["faces"]
    rows = []
    for name, f in faces.items():
        ink_pct = 100.0 * f["ink"] / f["glyph_cells"]
        shipped = " &mdash; shipped" if name == data["shipped"] else ""
        rows.append([
            f"<b>{name}</b>{shipped}",
            f"{f['height']}", f"{f['width']}", f"{f['son_start']}",
            f"{f['glyph_cells']}", f"{f['ink']}", f"{ink_pct:.1f}%",
        ])
    return [
        H1 >> "3. The survey, measured",
        para(
            "Eight faces were rendered and measured rather than eyeballed. Ink "
            "is the count of non-space glyph characters; ink density is ink as "
            "a percentage of the total cell area, which is a workable proxy for "
            "visual weight. All figures were produced by rendering each face "
            "and counting, not estimated.", LEAD),
        grid(
            ["Face", "Rows", "Cols", "SON at", "Cells", "Ink", "Density"],
            rows,
            [118, 40, 40, 46, 46, 40, 52],
            align_right=(1, 2, 3, 4, 5, 6)),
        para(
            "Read the density column as weight. The three solid faces &mdash; "
            "<font face='Courier'>banner</font>, "
            "<font face='Courier'>doom</font> and "
            "<font face='Courier'>ogre</font> &mdash; carry the most ink per "
            "cell and read heaviest at small sizes. The outline faces carry "
            "less ink per cell but occupy more columns, because an outline must "
            "draw both edges of every stroke.", CAPTION),
        callout(
            "The measurement that mattered",
            "The shipped face, <b>larry3d</b>, is the largest in every "
            "dimension: nine rows, sixty five columns, five hundred and eighty "
            "five cells and two hundred and sixty six ink characters. That is "
            "roughly twice the area of the smallest face surveyed. It was "
            "chosen anyway, which is a judgement: distinctiveness was weighted "
            "above compactness, and the cost is stated here so it is visible."),
        PageBreak(),
    ]


def drawings(data):
    flow = [
        H1 >> "4. The drawings",
        para(
            "Each face is drawn with the production treatment: the "
            "<i>Agent</i> half in brand amber, the <i>SON</i> half in bold "
            "amber, split at the measured column, over the shared tagline. The "
            "shipped face is marked. Faces are shown at the same point size, so "
            "relative width is honest.", LEAD),
    ]
    for name, f in data["faces"].items():
        tag = " &nbsp;&mdash;&nbsp; <b>SHIPPED</b>" if name == data["shipped"] else ""
        flow.append(H3 >> f"{name}{tag}")
        flow.append(ArtBlock(f["rows"], f["son_start"], AMBER, INK))
        flow.append(para(
            f"{f['height']} rows &times; {f['width']} columns &nbsp;&bull;&nbsp; "
            f"split at column {f['son_start']} &nbsp;&bull;&nbsp; "
            f"{f['ink']} ink characters", CAPTION))
    flow.append(PageBreak())
    return flow
