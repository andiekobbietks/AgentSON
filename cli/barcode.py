"""
Barcode generation for AgentSON.

WHY: the mobile/remote pairing flow needs a scannable code printed in the CLI.
A phone camera reads a QR natively, so prefer the ``qrcode`` library; fall back
to Code 128 patterns when it is absent (the free core ships zero runtime deps,
so the Core Package Registry deliberately omits qrcode).
"""

from __future__ import annotations

import io
from typing import List, Optional

try:  # optional — only used when a phone scanner is nearby
    import qrcode
except ImportError:  # pragma: no cover
    qrcode = None

from typing import List, Optional

# Code 128 pattern table, values 0..106. Each entry is 6 bar/space widths
# (bar, space, bar, space, bar, space) except the stop pattern (2331112).
# Index 0 = space, 1..95 = ASCII 33..127, 96..106 = FNC/shift/start/stop.
_C128_PATTERNS = [
    "212222", "222122", "222221", "121223", "121322", "131222", "122213",
    "122312", "132212", "221213", "221312", "231212", "112232", "122132",
    "122231", "113222", "123122", "123221", "223211", "221132", "221231",
    "213212", "223112", "312131", "311222", "321122", "321221", "312212",
    "322112", "322211", "212123", "212321", "232121", "111323", "131123",
    "131321", "112313", "132113", "132311", "211313", "231113", "231311",
    "112133", "112331", "132131", "113123", "113321", "133121", "313121",
    "211331", "231131", "213113", "213311", "213131", "311123", "311321",
    "331121", "312113", "312311", "332111", "314111", "221411", "431111",
    "111224", "111422", "121124", "121421", "141122", "141221", "112214",
    "112412", "122114", "122411", "142112", "142211", "241211", "221114",
    "413111", "241112", "134111", "111242", "121142", "121241", "114212",
    "124112", "124211", "411212", "421112", "421211", "212141", "214121",
    "412121", "111143", "111341", "131141", "114113", "114311", "411113",
    "411311", "113141", "114131", "311141", "411131", "211412", "211214",
    "211232", "2331112",
]

_START_B = 104
_STOP = 106


def _pattern(value: int) -> str:
    return _C128_PATTERNS[value]


def encode128(data: str) -> str:
    """Return the full Code 128-B bar pattern string for ``data``."""
    if not data:
        raise ValueError("barcode data must not be empty")
    for ch in data:
        if not (32 <= ord(ch) <= 127):
            raise ValueError(
                "character %r is outside Code 128 subset B (ASCII 32..127)" % ch
            )

    values = [_START_B]
    values.extend(ord(ch) - 32 for ch in data)

    checksum = _START_B
    for i, v in enumerate(values[1:], start=1):
        checksum += i * v
    checksum %= 103

    parts = [_pattern(_START_B)]
    for v in values[1:]:
        parts.append(_pattern(v))
    parts.append(_pattern(checksum))
    parts.append(_pattern(_STOP))
    return "".join(parts)


def _modules(data: str) -> List[bool]:
    """Bar pattern as a list of booleans, True where a bar is drawn."""
    widths = encode128(data)
    modules: List[bool] = []
    for i, w in enumerate(widths):
        modules.extend([i % 2 == 0] * int(w))
    return modules


def render_png(
    data: str,
    path: str,
    module_width: int = 3,
    height: int = 120,
    quiet_zones: int = 10,
) -> str:
    """Write ``data`` as a Code 128 PNG at ``path``. Returns the path.

    WHY Pillow only: adding a QR library would push a new dependency into a
    core deliberately kept at 16 packages / 16 MB.
    """
    from PIL import Image, ImageDraw

    modules = _modules(data)
    quiet = quiet_zones * module_width
    width = len(modules) * module_width + quiet * 2
    img = Image.new("L", (width, height + 20), 255)
    draw = ImageDraw.Draw(img)

    for idx, filled in enumerate(modules):
        if not filled:
            continue
        x0 = quiet + idx * module_width
        draw.rectangle([x0, 0, x0 + module_width - 1, height], fill=0)

    img.save(path, "PNG")
    return path


def render_text(data: str) -> str:
    """Return a monospace text barcode for terminals.

    The bars are a faithful Code 128 rendering; scanning them needs a camera
    pointed at the screen, and the URL is printed underneath for copy-paste.
    """
    modules = _modules(data)
    rows = ["", "", ""]
    for filled in modules:
        ch = "#" if filled else " "
        for r in range(3):
            rows[r] += ch
    return "\n".join(rows)


def render_qr_png(data: str, path: str, scale: int = 6) -> Optional[str]:
    """Write ``data`` as a QR PNG at ``path``. Returns the path, or None when
    the optional ``qrcode`` dependency is not installed."""
    if qrcode is None:
        return None
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=scale,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(path, "PNG")
    return path


def render_qr_ascii(data: str) -> Optional[str]:
    """Render a QR code as ASCII art (2 chars per module). None if unavailable."""
    if qrcode is None:
        return None
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=1,
        border=2,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    try:
        from PIL import Image
    except ImportError:
        return None
    if not hasattr(img, "convert"):
        img = img.convert("1")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    small = Image.open(buf).convert("1")
    w, h = small.size
    pixels = small.load()
    # Black module (0) = filled; white (255) = empty
    out = []
    for y in range(h):
        row = []
        for x in range(w):
            row.append("██" if pixels[x, y] < 128 else "  ")
        out.append("".join(row))
    return "\n".join(out)


def platform_upgrade_url(base: Optional[str] = None) -> str:
    """The URL the barcode points at: the premium tier landing page."""
    root = (base or "https://agentson.dev").rstrip("/")
    return f"{root}/platform/upgrade"
