"""Parse matplotlib SVG into a flat list of drawable elements.

Walks the SVG DOM depth-first, accumulates transforms from <g> groups,
resolves <use>/<defs> references, and extracts style attributes.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Union
from xml.etree import ElementTree as ET

from svg2pptx.path_parser import (
    CmdType, PathSegment, is_rect_path, parse_path, rect_from_path,
)
from svg2pptx.style import ElementStyle, parse_style, merge_style
from svg2pptx.text_reconstruct import ReconstructedText, is_text_group, reconstruct_text
from svg2pptx.transform import AffineTransform
from svg2pptx.units import parse_length

log = logging.getLogger(__name__)

SVG_NS = "http://www.w3.org/2000/svg"
XLINK_NS = "http://www.w3.org/1999/xlink"


# ── Drawable element types ──────────────────────────────────────────────────

@dataclass
class SVGRect:
    x: float
    y: float
    width: float
    height: float
    style: ElementStyle


@dataclass
class SVGPath:
    segments: List[PathSegment]
    style: ElementStyle


@dataclass
class SVGText:
    info: ReconstructedText


DrawableElement = Union[SVGRect, SVGPath, SVGText]


# ── Parser ──────────────────────────────────────────────────────────────────

class SVGParser:
    """Parse a matplotlib SVG file into drawable elements."""

    def __init__(self, svg_path: str):
        # Register namespaces to avoid ns0/ns1 prefixes in output
        ET.register_namespace("", SVG_NS)
        ET.register_namespace("xlink", XLINK_NS)
        self.tree = ET.parse(svg_path)
        self.root = self.tree.getroot()
        self.defs: Dict[str, ET.Element] = {}
        self.width_pt: float = 0.0
        self.height_pt: float = 0.0

    def parse(self) -> Tuple[float, float, List[DrawableElement]]:
        """Main entry. Returns (width_pt, height_pt, elements)."""
        self._parse_dimensions()
        self._collect_defs(self.root)
        elements = self._walk(self.root, AffineTransform.identity(), ElementStyle())
        log.info("Parsed %d drawable elements (%.0f x %.0f pt)",
                 len(elements), self.width_pt, self.height_pt)
        return self.width_pt, self.height_pt, elements

    def _parse_dimensions(self) -> None:
        w = self.root.get("width", "")
        h = self.root.get("height", "")
        if w and h:
            self.width_pt = parse_length(w)
            self.height_pt = parse_length(h)
        else:
            vb = self.root.get("viewBox", "")
            if vb:
                parts = vb.split()
                self.width_pt = float(parts[2])
                self.height_pt = float(parts[3])

    def _collect_defs(self, root: ET.Element) -> None:
        """Recursively collect all elements with id into defs lookup."""
        for elem in root.iter():
            eid = elem.get("id")
            if eid:
                self.defs[eid] = elem
        # Also explicitly walk <defs> sections
        for defs_elem in root.iter(f"{{{SVG_NS}}}defs"):
            for child in defs_elem:
                eid = child.get("id")
                if eid:
                    self.defs[eid] = child

    def _walk(self, elem: ET.Element, tf: AffineTransform,
              parent_style: ElementStyle) -> List[DrawableElement]:
        """Recursively walk DOM, yielding drawable elements."""
        results: List[DrawableElement] = []
        tag = _local_tag(elem)

        # Skip metadata, defs (processed separately), clipPath definitions
        if tag in ("metadata", "defs", "clipPath", "style", "title", "desc"):
            return results

        # Accumulate transform
        tf_str = elem.get("transform", "")
        if tf_str:
            local_tf = AffineTransform.from_svg_string(tf_str)
            tf = tf.compose(local_tf)

        # Parse style
        style = parse_style(elem.get("style", ""), dict(elem.attrib))
        style = merge_style(parent_style, style)

        # Handle text groups specially
        if tag == "g" and is_text_group(elem):
            try:
                text_info = reconstruct_text(elem, tf)
                if text_info:
                    results.append(SVGText(info=text_info))
            except Exception as e:
                log.debug("Failed to reconstruct text from %s: %s", elem.get("id"), e)
            return results  # don't recurse into text group children

        # Handle specific element types
        if tag == "rect":
            r = self._parse_rect(elem, tf, style)
            if r:
                results.append(r)

        elif tag == "path":
            p = self._parse_path_element(elem, tf, style)
            if p:
                results.append(p)

        elif tag == "use":
            u = self._resolve_use(elem, tf, style)
            if u:
                results.append(u)

        elif tag == "line":
            ln = self._parse_line(elem, tf, style)
            if ln:
                results.append(ln)

        elif tag == "circle":
            c = self._parse_circle(elem, tf, style)
            if c:
                results.append(c)

        elif tag == "ellipse":
            e = self._parse_ellipse(elem, tf, style)
            if e:
                results.append(e)

        elif tag == "polygon":
            pg = self._parse_polygon(elem, tf, style)
            if pg:
                results.append(pg)

        # Recurse into children (for <g>, <svg>, etc.)
        if tag in ("g", "svg"):
            for child in elem:
                results.extend(self._walk(child, tf, style))

        return results

    def _parse_rect(self, elem: ET.Element, tf: AffineTransform,
                    style: ElementStyle) -> Optional[SVGRect]:
        x = float(elem.get("x", "0"))
        y = float(elem.get("y", "0"))
        w = float(elem.get("width", "0"))
        h = float(elem.get("height", "0"))
        if w <= 0 or h <= 0:
            return None
        # Transform corners
        p0 = tf.apply_point(x, y)
        p1 = tf.apply_point(x + w, y + h)
        rx = min(p0[0], p1[0])
        ry = min(p0[1], p1[1])
        rw = abs(p1[0] - p0[0])
        rh = abs(p1[1] - p0[1])
        return SVGRect(rx, ry, rw, rh, style)

    def _parse_path_element(self, elem: ET.Element, tf: AffineTransform,
                            style: ElementStyle) -> Optional[DrawableElement]:
        d = elem.get("d", "")
        if not d.strip():
            return None

        try:
            segments = parse_path(d)
        except Exception as e:
            log.debug("Failed to parse path: %s", e)
            return None

        if not segments:
            return None

        # Apply transform to all points
        transformed = _transform_segments(segments, tf)

        # Detect rectangles for more efficient PPTX mapping
        if is_rect_path(transformed):
            x, y, w, h = rect_from_path(transformed)
            if w > 0.1 and h > 0.1:
                return SVGRect(x, y, w, h, style)

        return SVGPath(transformed, style)

    def _resolve_use(self, use_elem: ET.Element, tf: AffineTransform,
                     style: ElementStyle) -> Optional[DrawableElement]:
        href = use_elem.get(f"{{{XLINK_NS}}}href", use_elem.get("href", ""))
        ref_id = href.lstrip("#")
        if not ref_id or ref_id not in self.defs:
            log.debug("Unresolved <use> ref: %s", href)
            return None

        # Parse <use> style (may override def style)
        use_style = parse_style(use_elem.get("style", ""), dict(use_elem.attrib))
        merged = merge_style(style, use_style)

        # Position offset from <use x="..." y="...">
        ux = float(use_elem.get("x", "0"))
        uy = float(use_elem.get("y", "0"))
        use_tf = tf.compose(AffineTransform.from_translate(ux, uy))

        # Resolve the referenced element
        ref = self.defs[ref_id]
        ref_tag = _local_tag(ref)

        if ref_tag == "path":
            d = ref.get("d", "")
            if not d:
                return None
            # Ref element may have its own transform (e.g. scale(0.015625) on glyph paths)
            ref_tf_str = ref.get("transform", "")
            if ref_tf_str:
                ref_tf = AffineTransform.from_svg_string(ref_tf_str)
                use_tf = use_tf.compose(ref_tf)
            try:
                segments = parse_path(d)
                transformed = _transform_segments(segments, use_tf)
                if is_rect_path(transformed):
                    x, y, w, h = rect_from_path(transformed)
                    if w > 0.1 and h > 0.1:
                        return SVGRect(x, y, w, h, merged)
                return SVGPath(transformed, merged)
            except Exception as e:
                log.debug("Failed to parse <use> path: %s", e)
                return None

        return None

    def _parse_line(self, elem: ET.Element, tf: AffineTransform,
                    style: ElementStyle) -> Optional[SVGPath]:
        x1 = float(elem.get("x1", "0"))
        y1 = float(elem.get("y1", "0"))
        x2 = float(elem.get("x2", "0"))
        y2 = float(elem.get("y2", "0"))
        p1 = tf.apply_point(x1, y1)
        p2 = tf.apply_point(x2, y2)
        return SVGPath([
            PathSegment(CmdType.MOVE, [p1]),
            PathSegment(CmdType.LINE, [p2]),
        ], style)

    def _parse_circle(self, elem: ET.Element, tf: AffineTransform,
                      style: ElementStyle) -> Optional[SVGPath]:
        cx = float(elem.get("cx", "0"))
        cy = float(elem.get("cy", "0"))
        r = float(elem.get("r", "0"))
        if r <= 0:
            return None
        # Approximate circle as 4 cubic beziers
        k = 0.5522847498  # magic number for cubic approx of quarter circle
        segments = [
            PathSegment(CmdType.MOVE, [tf.apply_point(cx + r, cy)]),
            PathSegment(CmdType.CUBIC, [
                tf.apply_point(cx + r, cy + k*r),
                tf.apply_point(cx + k*r, cy + r),
                tf.apply_point(cx, cy + r),
            ]),
            PathSegment(CmdType.CUBIC, [
                tf.apply_point(cx - k*r, cy + r),
                tf.apply_point(cx - r, cy + k*r),
                tf.apply_point(cx - r, cy),
            ]),
            PathSegment(CmdType.CUBIC, [
                tf.apply_point(cx - r, cy - k*r),
                tf.apply_point(cx - k*r, cy - r),
                tf.apply_point(cx, cy - r),
            ]),
            PathSegment(CmdType.CUBIC, [
                tf.apply_point(cx + k*r, cy - r),
                tf.apply_point(cx + r, cy - k*r),
                tf.apply_point(cx + r, cy),
            ]),
            PathSegment(CmdType.CLOSE, []),
        ]
        return SVGPath(segments, style)

    def _parse_ellipse(self, elem: ET.Element, tf: AffineTransform,
                       style: ElementStyle) -> Optional[SVGPath]:
        cx = float(elem.get("cx", "0"))
        cy = float(elem.get("cy", "0"))
        rx = float(elem.get("rx", "0"))
        ry = float(elem.get("ry", "0"))
        if rx <= 0 or ry <= 0:
            return None
        k = 0.5522847498
        segments = [
            PathSegment(CmdType.MOVE, [tf.apply_point(cx + rx, cy)]),
            PathSegment(CmdType.CUBIC, [
                tf.apply_point(cx + rx, cy + k*ry),
                tf.apply_point(cx + k*rx, cy + ry),
                tf.apply_point(cx, cy + ry),
            ]),
            PathSegment(CmdType.CUBIC, [
                tf.apply_point(cx - k*rx, cy + ry),
                tf.apply_point(cx - rx, cy + k*ry),
                tf.apply_point(cx - rx, cy),
            ]),
            PathSegment(CmdType.CUBIC, [
                tf.apply_point(cx - rx, cy - k*ry),
                tf.apply_point(cx - k*rx, cy - ry),
                tf.apply_point(cx, cy - ry),
            ]),
            PathSegment(CmdType.CUBIC, [
                tf.apply_point(cx + k*rx, cy - ry),
                tf.apply_point(cx + rx, cy - k*ry),
                tf.apply_point(cx + rx, cy),
            ]),
            PathSegment(CmdType.CLOSE, []),
        ]
        return SVGPath(segments, style)

    def _parse_polygon(self, elem: ET.Element, tf: AffineTransform,
                       style: ElementStyle) -> Optional[SVGPath]:
        points_str = elem.get("points", "")
        if not points_str:
            return None
        import re
        nums = [float(x) for x in re.findall(r"[+-]?[\d.]+(?:e[+-]?\d+)?", points_str)]
        if len(nums) < 4:
            return None
        pts = [(nums[i], nums[i+1]) for i in range(0, len(nums) - 1, 2)]
        tpts = [tf.apply_point(x, y) for x, y in pts]
        segments = [PathSegment(CmdType.MOVE, [tpts[0]])]
        for p in tpts[1:]:
            segments.append(PathSegment(CmdType.LINE, [p]))
        segments.append(PathSegment(CmdType.CLOSE, []))
        return SVGPath(segments, style)


# ── Helpers ─────────────────────────────────────────────────────────────────

def _local_tag(elem: ET.Element) -> str:
    tag = elem.tag
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def _transform_segments(segments: List[PathSegment],
                        tf: AffineTransform) -> List[PathSegment]:
    out = []
    for seg in segments:
        if seg.points:
            new_pts = tf.apply_points(seg.points)
        else:
            new_pts = []
        out.append(PathSegment(seg.cmd, new_pts))
    return out
