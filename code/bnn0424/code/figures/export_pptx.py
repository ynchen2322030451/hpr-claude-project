"""Thin driver: bundle a directory of SVGs into editable PPT slides.

This module does NOT reimplement SVG->PPTX conversion. It forwards to the
legacy svg2pptx package living at /code/0411/svg2pptx/. Per the Phase-1
ruling, we reference the legacy package in place rather than copying a
local fork; modification of legacy sources is not allowed unless a
compatibility bug forces it.

CLI:
    python code/bnn0414/code/figures/export_pptx.py \
        <svg_dir> <out_pptx> [--pattern fig*.svg]

Programmatic:
    from export_pptx import batch
    batch("code/bnn0414/manuscript/0414_v4/figures",
          "code/bnn0414/manuscript/0414_v4/figures/figures_main.pptx",
          pattern="fig*.svg")
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List

_LEGACY_ROOT = Path(__file__).resolve().parents[3] / "0411"
if str(_LEGACY_ROOT) not in sys.path:
    sys.path.insert(0, str(_LEGACY_ROOT))

try:
    from svg2pptx.converter import SVGtoPPTXConverter  # type: ignore
except ImportError as exc:
    raise SystemExit(
        f"Failed to import legacy svg2pptx from {_LEGACY_ROOT}: {exc}"
    )


def batch(svg_dir: str, out_pptx: str, pattern: str = "*.svg") -> str:
    svgs: List[Path] = sorted(Path(svg_dir).glob(pattern))
    if not svgs:
        raise SystemExit(f"No SVGs matching {pattern!r} under {svg_dir}")
    conv = SVGtoPPTXConverter()
    conv.convert_files([str(s) for s in svgs], out_pptx, one_per_slide=True)
    print(f"wrote {out_pptx}  ({len(svgs)} slides)")
    return out_pptx


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("svg_dir")
    ap.add_argument("out_pptx")
    ap.add_argument("--pattern", default="*.svg")
    args = ap.parse_args()
    batch(args.svg_dir, args.out_pptx, pattern=args.pattern)


if __name__ == "__main__":
    main()
