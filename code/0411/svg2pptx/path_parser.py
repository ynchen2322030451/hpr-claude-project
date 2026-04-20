"""Parse SVG path `d` attribute into segments.

Handles M/m, L/l, H/h, V/v, C/c, Q/q, Z/z as used by matplotlib.
All relative commands are converted to absolute coordinates.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Tuple

_TOKEN_RE = re.compile(
    r"([MmLlHhVvCcQqSsTtAaZz])|([+-]?(?:\d+\.?\d*|\.\d+)(?:e[+-]?\d+)?)",
    re.I,
)


class CmdType(Enum):
    MOVE = "M"
    LINE = "L"
    CUBIC = "C"
    QUAD = "Q"
    CLOSE = "Z"


@dataclass
class PathSegment:
    cmd: CmdType
    points: List[Tuple[float, float]]  # absolute coords


def parse_path(d: str) -> List[PathSegment]:
    """Parse SVG path d-string into list of PathSegments (absolute coords)."""
    tokens = _TOKEN_RE.findall(d)
    segments: List[PathSegment] = []
    cx, cy = 0.0, 0.0  # current point
    sx, sy = 0.0, 0.0  # subpath start

    i = 0

    def _next_num() -> float:
        nonlocal i
        while i < len(tokens):
            cmd_tok, num_tok = tokens[i]
            if num_tok:
                i += 1
                return float(num_tok)
            break
        raise ValueError(f"Expected number at token {i}")

    def _has_num() -> bool:
        return i < len(tokens) and bool(tokens[i][1])

    while i < len(tokens):
        cmd_tok, num_tok = tokens[i]
        if cmd_tok:
            cmd = cmd_tok
            i += 1
        elif num_tok:
            # implicit repeat of previous command
            pass
        else:
            i += 1
            continue

        if cmd in ("M", "m"):
            x, y = _next_num(), _next_num()
            if cmd == "m":
                x += cx; y += cy
            cx, cy = x, y
            sx, sy = x, y
            segments.append(PathSegment(CmdType.MOVE, [(cx, cy)]))
            # subsequent coordinate pairs are implicit LineTo
            while _has_num():
                x, y = _next_num(), _next_num()
                if cmd == "m":
                    x += cx; y += cy
                cx, cy = x, y
                segments.append(PathSegment(CmdType.LINE, [(cx, cy)]))

        elif cmd in ("L", "l"):
            while _has_num():
                x, y = _next_num(), _next_num()
                if cmd == "l":
                    x += cx; y += cy
                cx, cy = x, y
                segments.append(PathSegment(CmdType.LINE, [(cx, cy)]))

        elif cmd in ("H", "h"):
            while _has_num():
                x = _next_num()
                if cmd == "h":
                    x += cx
                cx = x
                segments.append(PathSegment(CmdType.LINE, [(cx, cy)]))

        elif cmd in ("V", "v"):
            while _has_num():
                y = _next_num()
                if cmd == "v":
                    y += cy
                cy = y
                segments.append(PathSegment(CmdType.LINE, [(cx, cy)]))

        elif cmd in ("C", "c"):
            while _has_num():
                x1, y1 = _next_num(), _next_num()
                x2, y2 = _next_num(), _next_num()
                x, y = _next_num(), _next_num()
                if cmd == "c":
                    x1 += cx; y1 += cy
                    x2 += cx; y2 += cy
                    x += cx; y += cy
                segments.append(PathSegment(CmdType.CUBIC, [(x1, y1), (x2, y2), (x, y)]))
                cx, cy = x, y

        elif cmd in ("Q", "q"):
            while _has_num():
                x1, y1 = _next_num(), _next_num()
                x, y = _next_num(), _next_num()
                if cmd == "q":
                    x1 += cx; y1 += cy
                    x += cx; y += cy
                # convert quadratic to cubic for uniformity
                cx1 = cx + 2.0/3.0 * (x1 - cx)
                cy1 = cy + 2.0/3.0 * (y1 - cy)
                cx2 = x + 2.0/3.0 * (x1 - x)
                cy2 = y + 2.0/3.0 * (y1 - y)
                segments.append(PathSegment(CmdType.CUBIC, [(cx1, cy1), (cx2, cy2), (x, y)]))
                cx, cy = x, y

        elif cmd in ("Z", "z"):
            segments.append(PathSegment(CmdType.CLOSE, []))
            cx, cy = sx, sy

        else:
            i += 1

    return segments


def is_rect_path(segments: List[PathSegment]) -> bool:
    """Detect M-L-L-L-Z or M-L-L-L-L-Z rectangle pattern."""
    cmds = [s.cmd for s in segments]
    if cmds == [CmdType.MOVE, CmdType.LINE, CmdType.LINE, CmdType.LINE, CmdType.CLOSE]:
        return _points_form_rect(segments)
    if cmds == [CmdType.MOVE, CmdType.LINE, CmdType.LINE, CmdType.LINE, CmdType.LINE, CmdType.CLOSE]:
        return _points_form_rect(segments)
    return False


def _points_form_rect(segments: List[PathSegment]) -> bool:
    """Check that all line segments are axis-aligned (horizontal or vertical)."""
    pts = []
    for s in segments:
        if s.cmd in (CmdType.MOVE, CmdType.LINE):
            pts.extend(s.points)
    if len(pts) < 4:
        return False
    for i in range(len(pts) - 1):
        dx = abs(pts[i+1][0] - pts[i][0])
        dy = abs(pts[i+1][1] - pts[i][1])
        if dx > 0.01 and dy > 0.01:
            return False
    return True


def rect_from_path(segments: List[PathSegment]) -> Tuple[float, float, float, float]:
    """Extract (x, y, width, height) from a rectangular path."""
    pts = []
    for s in segments:
        if s.cmd in (CmdType.MOVE, CmdType.LINE):
            pts.extend(s.points)
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    x0, x1 = min(xs), max(xs)
    y0, y1 = min(ys), max(ys)
    return x0, y0, x1 - x0, y1 - y0


def linearize_cubic(p0: Tuple[float, float], p1: Tuple[float, float],
                    p2: Tuple[float, float], p3: Tuple[float, float],
                    tolerance: float = 0.5) -> List[Tuple[float, float]]:
    """Adaptively subdivide cubic Bezier into line segments.

    Returns list of points (excluding p0) that approximate the curve.
    tolerance is in the same coordinate units (pt).
    """
    # flatness test: max distance from control points to chord
    dx = p3[0] - p0[0]
    dy = p3[1] - p0[1]
    d2 = max(
        abs((p1[0] - p3[0]) * dy - (p1[1] - p3[1]) * dx),
        abs((p2[0] - p3[0]) * dy - (p2[1] - p3[1]) * dx),
    )
    chord_len_sq = dx * dx + dy * dy
    if chord_len_sq < 1e-10 or d2 * d2 <= tolerance * tolerance * chord_len_sq:
        return [p3]

    # de Casteljau subdivision at t=0.5
    m01 = _mid(p0, p1)
    m12 = _mid(p1, p2)
    m23 = _mid(p2, p3)
    m012 = _mid(m01, m12)
    m123 = _mid(m12, m23)
    m0123 = _mid(m012, m123)

    left = linearize_cubic(p0, m01, m012, m0123, tolerance)
    right = linearize_cubic(m0123, m123, m23, p3, tolerance)
    return left + right


def _mid(a: Tuple[float, float], b: Tuple[float, float]) -> Tuple[float, float]:
    return ((a[0] + b[0]) * 0.5, (a[1] + b[1]) * 0.5)
