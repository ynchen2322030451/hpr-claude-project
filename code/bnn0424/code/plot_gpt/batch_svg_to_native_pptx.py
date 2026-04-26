#!/usr/bin/env python3
"""Batch convert all Fig 1-5 SVGs to fully-native-shape PPTX files.

Each SVG element (rect, path, circle, text) becomes an independent,
draggable PPT shape. clipPath clipping is applied to prevent lines
from extending beyond axes boundaries.

Fig 0 (geometry) is handled separately by geometry_to_pptx.py since
its SVGs are raster-embedded (PyVista GL2PS output).
"""
import sys
import os
from pathlib import Path

# Add svg2pptx to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "0411"))

from svg2pptx.converter import SVGtoPPTXConverter

BASE = Path(__file__).resolve().parent

# (svg_path, output_pptx_name) — relative to each fig's outputs/ dir
FIGURES = [
    # Fig 1 — workflow
    ("fig1_workflow/outputs/figure1_workflow.svg",
     "fig1_workflow/outputs/figure1_workflow_native.pptx"),

    # Fig 2 — surrogate selection
    ("fig2_surrogate_selection/outputs/fig2_surrogate_selection.svg",
     "fig2_surrogate_selection/outputs/fig2_surrogate_native.pptx"),

    # Fig 3 — forward UQ (composed + individual panels)
    ("fig3_forward_uq/outputs/figure3_composed.svg",
     "fig3_forward_uq/outputs/figure3_composed_native.pptx"),
    ("fig3_forward_uq/outputs/figure3_panelA_stress.svg",
     "fig3_forward_uq/outputs/figure3_panelA_native.pptx"),
    ("fig3_forward_uq/outputs/figure3_panelB_keff.svg",
     "fig3_forward_uq/outputs/figure3_panelB_native.pptx"),
    ("fig3_forward_uq/outputs/figure3_panelC_thermal.svg",
     "fig3_forward_uq/outputs/figure3_panelC_native.pptx"),

    # Fig 4 — Sobol (full + individual panels)
    ("fig4_sobol/outputs/figure4_full.svg",
     "fig4_sobol/outputs/figure4_full_native.pptx"),
    ("fig4_sobol/outputs/panel_A_stress.svg",
     "fig4_sobol/outputs/panel_A_native.pptx"),
    ("fig4_sobol/outputs/panel_B_keff.svg",
     "fig4_sobol/outputs/panel_B_native.pptx"),
    ("fig4_sobol/outputs/panel_C_summary.svg",
     "fig4_sobol/outputs/panel_C_native.pptx"),

    # Fig 5 — posterior (combined + individual panels)
    ("fig5_posterior/outputs/figure5_combined.svg",
     "fig5_posterior/outputs/figure5_combined_native.pptx"),
    ("fig5_posterior/outputs/figure5_panelA.svg",
     "fig5_posterior/outputs/figure5_panelA_native.pptx"),
    ("fig5_posterior/outputs/figure5_panelB.svg",
     "fig5_posterior/outputs/figure5_panelB_native.pptx"),
    ("fig5_posterior/outputs/figure5_panelC.svg",
     "fig5_posterior/outputs/figure5_panelC_native.pptx"),
]


def main():
    conv = SVGtoPPTXConverter(verbose=True)
    print("Converting Fig 1-5 SVGs to native-shape PPTX (with clipPath support)...")
    print("=" * 70)

    ok, fail = 0, 0
    for svg_rel, out_rel in FIGURES:
        svg_path = BASE / svg_rel
        out_path = BASE / out_rel

        if not svg_path.exists():
            print(f"  [skip] {svg_rel} (SVG not found)")
            continue

        try:
            conv.convert_file(str(svg_path), str(out_path))
            ok += 1
            print(f"  [ok]   {svg_rel}")
            print(f"         → {out_path.name}")
        except Exception as e:
            print(f"  [FAIL] {svg_rel}: {e}")
            fail += 1

    print("=" * 70)
    print(f"Done: {ok} ok, {fail} failed")


if __name__ == "__main__":
    main()
