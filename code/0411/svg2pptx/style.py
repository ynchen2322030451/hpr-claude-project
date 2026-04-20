"""Parse SVG inline style attributes and map to python-pptx fill/line properties."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

from pptx.dml.color import RGBColor
from pptx.oxml.ns import qn
from pptx.util import Pt as PptxPt, Emu
from lxml import etree

from svg2pptx.units import pt_to_emu


@dataclass
class ElementStyle:
    fill: Optional[str] = None  # hex '#rrggbb' or 'none'
    fill_opacity: float = 1.0
    stroke: Optional[str] = None
    stroke_width: float = 1.0
    stroke_opacity: float = 1.0
    opacity: float = 1.0
    font_size: Optional[float] = None  # pt
    font_family: Optional[str] = None
    font_weight: Optional[str] = None
    stroke_linejoin: Optional[str] = None
    stroke_linecap: Optional[str] = None


_STYLE_SPLITTER = re.compile(r"\s*;\s*")
_KV_SPLITTER = re.compile(r"\s*:\s*")


def parse_style(style_str: str, attrs: Optional[dict] = None) -> ElementStyle:
    """Parse inline CSS style string + element attributes into ElementStyle.

    Priority: style attribute > presentation attributes.
    """
    props: dict[str, str] = {}

    # presentation attributes first (lower priority)
    if attrs:
        for key in ("fill", "stroke", "stroke-width", "fill-opacity",
                     "stroke-opacity", "opacity", "font-size", "font-family",
                     "font-weight", "stroke-linejoin", "stroke-linecap"):
            if key in attrs:
                props[key] = attrs[key]

    # inline style (higher priority)
    if style_str:
        for part in _STYLE_SPLITTER.split(style_str.strip()):
            if not part:
                continue
            kv = _KV_SPLITTER.split(part, 1)
            if len(kv) == 2:
                props[kv[0].strip()] = kv[1].strip()

    es = ElementStyle()
    if "fill" in props:
        es.fill = props["fill"].strip()
    if "fill-opacity" in props:
        es.fill_opacity = float(props["fill-opacity"])
    if "stroke" in props:
        es.stroke = props["stroke"].strip()
    if "stroke-width" in props:
        es.stroke_width = float(props["stroke-width"])
    if "stroke-opacity" in props:
        es.stroke_opacity = float(props["stroke-opacity"])
    if "opacity" in props:
        es.opacity = float(props["opacity"])
    if "font-size" in props:
        es.font_size = float(props["font-size"].replace("px", "").replace("pt", ""))
    if "font-family" in props:
        es.font_family = props["font-family"]
    if "font-weight" in props:
        es.font_weight = props["font-weight"]
    if "stroke-linejoin" in props:
        es.stroke_linejoin = props["stroke-linejoin"]
    if "stroke-linecap" in props:
        es.stroke_linecap = props["stroke-linecap"]

    return es


def merge_style(parent: ElementStyle, child: ElementStyle) -> ElementStyle:
    """Inherit style from parent where child has no explicit value."""
    merged = ElementStyle()
    merged.fill = child.fill if child.fill is not None else parent.fill
    merged.fill_opacity = child.fill_opacity if child.fill_opacity != 1.0 else parent.fill_opacity
    merged.stroke = child.stroke if child.stroke is not None else parent.stroke
    merged.stroke_width = child.stroke_width
    merged.stroke_opacity = child.stroke_opacity
    merged.opacity = child.opacity * parent.opacity
    merged.font_size = child.font_size or parent.font_size
    merged.font_family = child.font_family or parent.font_family
    merged.font_weight = child.font_weight or parent.font_weight
    return merged


def hex_to_rgb(hex_color: str) -> RGBColor:
    """Convert '#aed9e0' -> RGBColor."""
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = h[0]*2 + h[1]*2 + h[2]*2
    return RGBColor(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def _is_visible_color(c: Optional[str]) -> bool:
    return c is not None and c.lower() != "none"


def apply_fill(shape, style: ElementStyle) -> None:
    """Apply fill color and opacity to a python-pptx shape."""
    if not _is_visible_color(style.fill):
        shape.fill.background()  # transparent
        return

    shape.fill.solid()
    rgb = hex_to_rgb(style.fill)
    shape.fill.fore_color.rgb = rgb

    alpha = style.fill_opacity * style.opacity
    if alpha < 0.999:
        _set_fill_alpha(shape, alpha)


def apply_line(shape, style: ElementStyle) -> None:
    """Apply stroke to a shape's line property."""
    ln = shape.line
    if not _is_visible_color(style.stroke):
        ln.fill.background()
        return

    ln.color.rgb = hex_to_rgb(style.stroke)
    ln.width = pt_to_emu(style.stroke_width)

    alpha = style.stroke_opacity * style.opacity
    if alpha < 0.999:
        _set_line_alpha(shape, alpha)


def _set_fill_alpha(shape, alpha: float) -> None:
    """Set fill transparency via OPC XML manipulation."""
    sp = shape._element
    spPr = sp.find(qn("p:spPr"))
    if spPr is None:
        return
    solid = spPr.find(qn("a:solidFill"))
    if solid is None:
        return
    color_elem = solid[0] if len(solid) else None
    if color_elem is None:
        return
    for existing in color_elem.findall(qn("a:alpha")):
        color_elem.remove(existing)
    alpha_elem = etree.SubElement(color_elem, qn("a:alpha"))
    alpha_elem.set("val", str(int(alpha * 100000)))


def _set_line_alpha(shape, alpha: float) -> None:
    """Set line transparency via OPC XML manipulation."""
    sp = shape._element
    spPr = sp.find(qn("p:spPr"))
    if spPr is None:
        return
    ln = spPr.find(qn("a:ln"))
    if ln is None:
        return
    solid = ln.find(qn("a:solidFill"))
    if solid is None:
        return
    color_elem = solid[0] if len(solid) else None
    if color_elem is None:
        return
    for existing in color_elem.findall(qn("a:alpha")):
        color_elem.remove(existing)
    alpha_elem = etree.SubElement(color_elem, qn("a:alpha"))
    alpha_elem.set("val", str(int(alpha * 100000)))
