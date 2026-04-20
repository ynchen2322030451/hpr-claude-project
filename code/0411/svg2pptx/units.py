"""Unit conversion between SVG units and python-pptx EMU.

matplotlib SVGs use pt for width/height, viewBox coords are unitless (= pt at 72 dpi).
python-pptx uses EMU (English Metric Units): 1 pt = 12700 EMU, 1 inch = 914400 EMU.
"""

import re

PT_TO_EMU = 12700
IN_TO_EMU = 914400
CM_TO_EMU = 360000
MM_TO_EMU = 36000
PX_TO_EMU = 12700  # at 72 dpi (matplotlib default)

_LENGTH_RE = re.compile(r"^\s*([+-]?[\d.]+(?:e[+-]?\d+)?)\s*(pt|px|in|cm|mm)?\s*$", re.I)

_UNIT_TO_PT = {
    None: 1.0,
    "": 1.0,
    "pt": 1.0,
    "px": 1.0,  # matplotlib 72 dpi
    "in": 72.0,
    "cm": 72.0 / 2.54,
    "mm": 72.0 / 25.4,
}


def parse_length(value: str) -> float:
    """Parse SVG length string to pt. E.g. '784.885625pt' -> 784.885625."""
    m = _LENGTH_RE.match(value)
    if not m:
        raise ValueError(f"Cannot parse SVG length: {value!r}")
    num = float(m.group(1))
    unit = m.group(2)
    return num * _UNIT_TO_PT.get(unit.lower() if unit else None, 1.0)


def pt_to_emu(pt: float) -> int:
    return round(pt * PT_TO_EMU)
