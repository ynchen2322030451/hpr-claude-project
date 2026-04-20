"""SVG transform parsing and affine matrix composition.

Handles translate(), scale(), rotate(), matrix() as used by matplotlib SVGs.
Nested <g> transforms are accumulated by composing parent * child matrices.
"""

from __future__ import annotations

import math
import re
from typing import List, Tuple

import numpy as np

_TRANSFORM_RE = re.compile(
    r"(translate|scale|rotate|matrix|skewX|skewY)\s*\(([^)]+)\)"
)
_NUM_RE = re.compile(r"[+-]?(?:\d+\.?\d*|\.\d+)(?:e[+-]?\d+)?", re.I)


class AffineTransform:
    """3x3 affine matrix: [[a c e], [b d f], [0 0 1]]."""

    __slots__ = ("m",)

    def __init__(self, matrix: np.ndarray | None = None):
        self.m: np.ndarray = matrix if matrix is not None else np.eye(3)

    @classmethod
    def identity(cls) -> AffineTransform:
        return cls()

    @classmethod
    def from_translate(cls, tx: float, ty: float = 0.0) -> AffineTransform:
        m = np.eye(3)
        m[0, 2] = tx
        m[1, 2] = ty
        return cls(m)

    @classmethod
    def from_scale(cls, sx: float, sy: float | None = None) -> AffineTransform:
        if sy is None:
            sy = sx
        m = np.eye(3)
        m[0, 0] = sx
        m[1, 1] = sy
        return cls(m)

    @classmethod
    def from_rotate(cls, deg: float) -> AffineTransform:
        r = math.radians(deg)
        c, s = math.cos(r), math.sin(r)
        m = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]], dtype=float)
        return cls(m)

    @classmethod
    def from_matrix(cls, a, b, c, d, e, f) -> AffineTransform:
        m = np.array([[a, c, e], [b, d, f], [0, 0, 1]], dtype=float)
        return cls(m)

    @classmethod
    def from_svg_string(cls, transform_str: str) -> AffineTransform:
        """Parse SVG transform attribute, e.g. 'translate(103 331) scale(0.1 -0.1)'."""
        result = cls.identity()
        for match in _TRANSFORM_RE.finditer(transform_str):
            func = match.group(1)
            nums = [float(x) for x in _NUM_RE.findall(match.group(2))]
            if func == "translate":
                tx = nums[0]
                ty = nums[1] if len(nums) > 1 else 0.0
                t = cls.from_translate(tx, ty)
            elif func == "scale":
                sx = nums[0]
                sy = nums[1] if len(nums) > 1 else sx
                t = cls.from_scale(sx, sy)
            elif func == "rotate":
                t = cls.from_rotate(nums[0])
            elif func == "matrix":
                t = cls.from_matrix(*nums[:6])
            else:
                continue
            result = result.compose(t)
        return result

    def compose(self, other: AffineTransform) -> AffineTransform:
        """self followed by other -> self @ other's matrix, i.e. apply self first."""
        return AffineTransform(self.m @ other.m)

    def then(self, other: AffineTransform) -> AffineTransform:
        """Apply self, then other: other.m @ self.m."""
        return AffineTransform(other.m @ self.m)

    def apply_point(self, x: float, y: float) -> Tuple[float, float]:
        v = self.m @ np.array([x, y, 1.0])
        return float(v[0]), float(v[1])

    def apply_points(self, pts: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        if not pts:
            return []
        arr = np.ones((len(pts), 3))
        for i, (x, y) in enumerate(pts):
            arr[i, 0] = x
            arr[i, 1] = y
        out = (self.m @ arr.T).T
        return [(float(r[0]), float(r[1])) for r in out]

    def get_scale(self) -> Tuple[float, float]:
        sx = math.sqrt(self.m[0, 0]**2 + self.m[1, 0]**2)
        sy = math.sqrt(self.m[0, 1]**2 + self.m[1, 1]**2)
        return sx, sy

    def get_rotation_deg(self) -> float:
        return math.degrees(math.atan2(self.m[1, 0], self.m[0, 0]))

    def get_translation(self) -> Tuple[float, float]:
        return float(self.m[0, 2]), float(self.m[1, 2])

    def __repr__(self) -> str:
        return f"AffineTransform({self.m.tolist()})"
