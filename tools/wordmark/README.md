# Wordmark build

Produces `docs/wordmark-handbook.pdf` — the design record for the AgentSON
mark: what was drawn, what was measured, what was rejected and why.

## Rebuild

```
python build_handbook.py     # writes ../../docs/wordmark-handbook.pdf
python verify_pdf.py         # checks overflow by measuring text bounding boxes
```

`build_handbook.py` needs **only `reportlab`**. It reads
`handbook_data.json`, which is the frozen set of measurements, so the handbook
is reproducible without re-rendering any fonts.

## Regenerating the measurements

```
python gen_data.py           # rewrites handbook_data.json
```

This is the one step that needs **`pyfiglet`**, because it renders every face
and counts. Everything else downstream consumes the JSON and never touches the
font library. Commit the JSON alongside any change to the generator.

## Files

| File | Purpose |
|---|---|
| `gen_data.py` | Renders 8 faces, computes 14 WCAG contrast ratios, writes the JSON |
| `handbook_data.json` | Frozen measurements — the reproducibility anchor |
| `handbook_style.py` | Styles, the DRY table helper, `ArtBlock` and `ShadowArt` flowables |
| `content_a.py` | Cover, lineage, the survey, the drawings |
| `content_b.py` | Split, colour, the 3D treatment, failure modes, spec, appendices |
| `build_handbook.py` | Assembles the story, applies page furniture |
| `verify_pdf.py` | Extracts every text span and fails if any crosses the right margin |

## Two rules the code enforces

**Every table cell is a `Paragraph`.** Plain strings do not wrap and overflow
their column. This is not stylistic — the swatch strip was originally built
from plain strings, printed its markup literally, and pushed four lines past
the page edge. It was caught by `verify_pdf.py`, not by looking at it.

**Amber is never ink on paper.** `#ffb000` measures 1.83:1 against white and
fails outright; the same amber as a *ground* with dark ink measures 9.50:1.
The brand colour is therefore used on screen only, and on this page only as a
rule. The measurements are in `handbook_data.json` under `swatches`.

## Re-shipping a different face

Change `SHIPPED` in `gen_data.py`, re-run the generator, then rebuild. The
wordmark constant that ships in `cli/help_system.py` is regenerated as
Appendix B, and its backslashes **must** be escaped — the outline faces are
full of them, and an unescaped trailing backslash escapes the closing quote
and makes the module a syntax error.
