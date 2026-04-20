"""Reconstruct editable text from matplotlib's glyph-path SVG output.

matplotlib (svg.fonttype='path', the default) renders text as:
  <defs><path id="DejaVuSans-XX" .../></defs>
  <g id="text_N">
    <g transform="translate(x y) scale(0.1 -0.1)">
      <use xlink:href="#DejaVuSans-XX" x="0"/>
      <use xlink:href="#DejaVuSans-XX" x="63.4"/>
    </g>
  </g>

The hex suffix XX is the Unicode codepoint: 30 -> '0', 2e -> '.', etc.
'Bold' in the ID means font-weight bold.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional
from xml.etree.ElementTree import Element

from svg2pptx.transform import AffineTransform

SVG_NS = "http://www.w3.org/2000/svg"
XLINK_NS = "http://www.w3.org/1999/xlink"

# Match glyph ID patterns: DejaVuSans-XX, DejaVuSans-Bold-XX, STIXGeneral-XX
_GLYPH_RE = re.compile(r"#?(\w+?)-([0-9a-fA-F]+)$")
_BOLD_RE = re.compile(r"Bold", re.I)
_ITALIC_RE = re.compile(r"Italic|Oblique", re.I)


@dataclass
class ReconstructedText:
    text: str
    x: float  # position in SVG viewBox coords (pt)
    y: float
    font_size: float  # pt
    font_family: str
    bold: bool
    italic: bool
    rotation: float  # degrees (0 or -90 typically)
    color: str  # hex


def extract_codepoint(href: str) -> Optional[str]:
    """'#DejaVuSans-30' -> '0', '#DejaVuSans-Bold-2e' -> '.'."""
    m = _GLYPH_RE.search(href)
    if not m:
        return None
    hex_str = m.group(2)
    try:
        return chr(int(hex_str, 16))
    except (ValueError, OverflowError):
        return None


def is_text_group(g_elem: Element) -> bool:
    """Check if <g id="text_N"> contains glyph <use> references."""
    gid = g_elem.get("id", "")
    if not gid.startswith("text_"):
        return False
    # look for nested <use> with xlink:href matching glyph pattern
    for use in g_elem.iter(f"{{{SVG_NS}}}use"):
        href = use.get(f"{{{XLINK_NS}}}href", use.get("href", ""))
        if _GLYPH_RE.search(href):
            return True
    return False


def reconstruct_text(g_elem: Element, parent_tf: AffineTransform) -> Optional[ReconstructedText]:
    """Extract full text string and formatting from a matplotlib text group.

    g_elem is the <g id="text_N"> element.
    parent_tf is the accumulated transform from all ancestor <g> groups.
    """
    # Find the inner <g> with the transform (translate + scale)
    inner_g = None
    for child in g_elem:
        tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
        if tag == "g" and child.get("transform"):
            inner_g = child
            break

    if inner_g is None:
        # Try direct <use> children
        inner_g = g_elem

    # Parse inner transform
    inner_tf_str = inner_g.get("transform", "")
    inner_tf = AffineTransform.from_svg_string(inner_tf_str) if inner_tf_str else AffineTransform.identity()

    # Compose with parent
    full_tf = parent_tf.compose(inner_tf)

    # Collect <use> elements and reconstruct text
    chars = []
    font_id = ""
    for use in inner_g.iter(f"{{{SVG_NS}}}use"):
        href = use.get(f"{{{XLINK_NS}}}href", use.get("href", ""))
        ch = extract_codepoint(href)
        if ch is not None:
            chars.append(ch)
            if not font_id:
                # extract font family name from first glyph
                m = _GLYPH_RE.search(href)
                if m:
                    font_id = m.group(1)

    if not chars:
        return None

    text = "".join(chars)

    # Determine position: the translation part of full_tf gives the baseline origin
    tx, ty = full_tf.get_translation()
    sx, sy = full_tf.get_scale()
    rot = full_tf.get_rotation_deg()

    # Font size: matplotlib uses scale(0.1 -0.1) with glyphs at 10x design size
    # The effective font size ≈ abs(sy) * 100 (empirically calibrated for DejaVuSans)
    # More precisely: matplotlib sets font size = rcParams['font.size'] and uses
    # scale(fs/100, -fs/100) where fs is in pt, so font_size = abs(sy) * 100
    font_size = abs(sy) * 100.0
    if font_size < 1.0:
        font_size = 10.0  # fallback

    # Font properties
    bold = bool(_BOLD_RE.search(font_id))
    italic = bool(_ITALIC_RE.search(font_id))

    # Map matplotlib font names to common names
    family = _map_font_family(font_id)

    # Color: check style on <use> or parent <g>
    color = _extract_text_color(g_elem, inner_g)

    # Rotation: normalize to useful values
    # matplotlib y-axis labels use rotate(-90) -> rot ≈ -90 or 270
    if abs(rot) > 179:
        rot = 0.0  # flip from scale(-1) is not a visual rotation
    if rot < 0:
        rot = rot + 360.0 if rot < -180 else rot

    return ReconstructedText(
        text=text, x=tx, y=ty,
        font_size=font_size, font_family=family,
        bold=bold, italic=italic,
        rotation=rot, color=color,
    )


def _map_font_family(font_id: str) -> str:
    """Map matplotlib glyph font ID to a standard font name."""
    fid = font_id.lower().replace("-", "").replace("_", "")
    if "dejavusans" in fid:
        return "Arial"
    if "stixgeneral" in fid:
        return "Times New Roman"
    if "cmr" in fid or "cmmi" in fid:
        return "Times New Roman"
    return "Arial"


def _extract_text_color(outer_g: Element, inner_g: Element) -> str:
    """Try to find fill color from text group elements."""
    for elem in (outer_g, inner_g):
        style = elem.get("style", "")
        if "fill:" in style:
            for part in style.split(";"):
                if "fill" in part and ":" in part:
                    val = part.split(":")[1].strip()
                    if val.startswith("#"):
                        return val
        fill = elem.get("fill", "")
        if fill.startswith("#"):
            return fill

    # check <use> elements
    for use in inner_g.iter(f"{{{SVG_NS}}}use"):
        style = use.get("style", "")
        if "fill:" in style:
            for part in style.split(";"):
                if "fill" in part and ":" in part:
                    val = part.split(":")[1].strip()
                    if val.startswith("#"):
                        return val

    return "#000000"  # default black
