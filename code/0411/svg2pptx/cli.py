"""CLI for svg2pptx.

Usage:
    python -m svg2pptx input.svg -o output.pptx
    python -m svg2pptx figures/draft/fig*.svg -o all_figures.pptx
    python -m svg2pptx figures/draft/ -o all_figures.pptx
    python -m svg2pptx input.svg --separate
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="svg2pptx",
        description="Convert matplotlib SVG figures to editable PowerPoint slides. "
                    "Each SVG element becomes an independent, editable shape.",
    )
    parser.add_argument(
        "inputs", nargs="+",
        help="SVG file(s) or directory to convert",
    )
    parser.add_argument(
        "-o", "--output", default=None,
        help="Output PPTX path (default: <input>.pptx or figures.pptx for multiple)",
    )
    parser.add_argument(
        "--separate", action="store_true",
        help="Create a separate PPTX file for each input SVG",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true",
        help="Enable debug logging",
    )

    args = parser.parse_args(argv)

    from svg2pptx.converter import SVGtoPPTXConverter
    converter = SVGtoPPTXConverter(verbose=args.verbose)

    inputs = args.inputs
    # Expand directories
    expanded: list[str] = []
    for inp in inputs:
        p = Path(inp)
        if p.is_dir():
            svgs = sorted(p.glob("*.svg"))
            if not svgs:
                print(f"Warning: no SVG files found in {inp}", file=sys.stderr)
            expanded.extend(str(s) for s in svgs)
        elif p.is_file():
            expanded.append(str(p))
        else:
            # Could be a glob pattern already expanded by shell
            expanded.append(str(p))

    if not expanded:
        print("Error: no SVG files to convert", file=sys.stderr)
        sys.exit(1)

    if len(expanded) == 1 and not args.separate:
        out = args.output or str(Path(expanded[0]).with_suffix(".pptx"))
        result = converter.convert_file(expanded[0], out)
        print(f"Created: {result}")

    elif args.separate:
        for svg in expanded:
            out = str(Path(svg).with_suffix(".pptx"))
            result = converter.convert_file(svg, out)
            print(f"Created: {result}")

    else:
        out = args.output or "figures.pptx"
        result = converter.convert_files(expanded, out, one_per_slide=True)
        print(f"Created: {result}")
