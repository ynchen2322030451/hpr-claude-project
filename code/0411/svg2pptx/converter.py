"""Orchestrate SVG parsing and PPTX generation.

One SVG -> one slide. Multiple SVGs -> multiple slides in one PPTX,
or separate PPTX files.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Optional

from svg2pptx.pptx_builder import PPTXBuilder
from svg2pptx.svg_parser import SVGParser

log = logging.getLogger(__name__)


class SVGtoPPTXConverter:
    """Convert matplotlib SVG figures to editable PowerPoint slides."""

    def __init__(self, verbose: bool = False):
        level = logging.DEBUG if verbose else logging.INFO
        logging.basicConfig(level=level, format="%(levelname)s: %(message)s")

    def convert_file(self, svg_path: str, output_path: Optional[str] = None) -> str:
        """Convert a single SVG to a single-slide PPTX.

        Returns the output path.
        """
        svg_path = str(Path(svg_path).resolve())
        if output_path is None:
            output_path = str(Path(svg_path).with_suffix(".pptx"))

        log.info("Converting %s -> %s", svg_path, output_path)
        parser = SVGParser(svg_path)
        width_pt, height_pt, elements = parser.parse()

        builder = PPTXBuilder(width_pt, height_pt)
        builder.new_slide()

        for elem in elements:
            builder.add_element(elem)

        builder.save(output_path)
        return output_path

    def convert_files(self, svg_paths: List[str], output_path: str,
                      one_per_slide: bool = True) -> str:
        """Convert multiple SVGs into one PPTX (one slide per SVG).

        If one_per_slide=False (not currently implemented), each SVG
        gets its own PPTX file.
        """
        if not svg_paths:
            raise ValueError("No SVG files provided")

        if not one_per_slide:
            # Separate files mode
            outputs = []
            for svg in svg_paths:
                out = self.convert_file(svg)
                outputs.append(out)
            return outputs[0]

        log.info("Converting %d SVGs into %s", len(svg_paths), output_path)

        # Parse all SVGs first to determine max dimensions
        parsed = []
        max_w, max_h = 0.0, 0.0
        for svg in svg_paths:
            parser = SVGParser(str(Path(svg).resolve()))
            w, h, elems = parser.parse()
            parsed.append((w, h, elems, Path(svg).name))
            max_w = max(max_w, w)
            max_h = max(max_h, h)

        # Use maximum dimensions for slide size
        builder = PPTXBuilder(max_w, max_h)

        for w, h, elements, name in parsed:
            log.info("  Slide: %s (%d elements)", name, len(elements))
            builder.new_slide()
            for elem in elements:
                builder.add_element(elem)

        builder.save(output_path)
        return output_path

    def convert_directory(self, dir_path: str, output_path: str,
                          pattern: str = "*.svg") -> str:
        """Convert all SVGs in a directory into one PPTX."""
        d = Path(dir_path)
        svgs = sorted(d.glob(pattern))
        if not svgs:
            raise FileNotFoundError(f"No SVG files matching {pattern} in {dir_path}")
        return self.convert_files([str(s) for s in svgs], output_path)
