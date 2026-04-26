#!/usr/bin/env python3
"""
figure_overview.py — Graphical overview / summary figure
========================================================
Single figure combining:
  - Top: Workflow flowchart (Uncertain inputs → HF sim → BNN → 3 applications)
  - Bottom: 2x2 grid of key result panels (A-D) embedded as images

Output: outputs/figure_overview.{pdf,svg,png}

Style: matches the GPT reference style with light gray workflow background,
       bold panel labels, and clean white panels.
"""

import sys
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import matplotlib.image as mpimg
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "_shared"))
import ncs_style
ncs_style.apply_style()

OUTDIR = HERE / "outputs"
OUTDIR.mkdir(parents=True, exist_ok=True)

# ── Panel image paths (pre-rendered PNGs) ──────────────────────────────
PANEL_IMAGES = {
    "A": HERE / "fig2_surrogate_selection" / "outputs" / "fig2_surrogate_selection.png",
    "B": HERE / "fig3_forward_uq" / "outputs" / "figure3_composed.png",
    "C": HERE / "fig4_sobol" / "outputs" / "figure4_full.png",
    "D": HERE / "fig5_posterior" / "outputs" / "figure5_combined.png",
}

PANEL_TITLES = {
    "A": "Predictive accuracy",
    "B": "Forward uncertainty propagation",
    "C": "Sensitivity attribution (Sobol)",
    "D": "Posterior calibration",
}


# ── Workflow box definitions ───────────────────────────────────────────
FLOW_BOXES = [
    {
        "id": "inputs",
        "title": "Uncertain inputs",
        "lines": [
            "SS316 material-property\nparameters:",
            "E slope / intercept",
            "thermal expansion\nbase / slope",
            "conductivity\nreference / slope",
        ],
        "color": "gray",
    },
    {
        "id": "hf_sim",
        "title": "Coupled high-fidelity\nsimulation\n(OpenMC + FEniCS)",
        "lines": [
            "uncoupled pass / coupled\nsteady state",
            r"temperature / stress / $k_\mathrm{eff}$"
            "\noutputs",
        ],
        "color": "gray",
    },
    {
        "id": "bnn",
        "title": "Bayesian neural\nsurrogate",
        "lines": [
            "constraint-regularized\nBNN",
            "multi-output predictive\ndistribution",
        ],
        "color": "blue",
    },
    {
        "id": "fwd_uq",
        "title": "Forward uncertainty\npropagation",
        "lines": [
            "Monte Carlo propagation",
            "response distributions",
            r"stress / $k_\mathrm{eff}$ / thermal"
            "\nfields",
        ],
        "color": "tan",
    },
    {
        "id": "sobol",
        "title": "Sensitivity attribution",
        "lines": [
            "Sobol variance\ndecomposition",
            "dominant-factor\nseparation",
        ],
        "color": "tan",
    },
    {
        "id": "posterior",
        "title": "Posterior calibration",
        "lines": [
            "observation-conditioned\nupdating",
            r"prior $\rightarrow$ posterior",
        ],
        "color": "tan",
    },
]


# ── Colors ─────────────────────────────────────────────────────────────
BOX_COLORS = {
    "gray": {"face": "#EFF2F5", "edge": "#C0C8D0", "title": "#2D3E50"},
    "blue": {"face": "#E0EBF5", "edge": "#8BAEC8", "title": "#1B3A5C"},
    "tan":  {"face": "#FDF5E6", "edge": "#D4C09E", "title": "#7A5C2E"},
}


def draw_workflow(ax):
    """Draw the workflow flowchart on the given axes."""
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    # Light gray background
    bg = FancyBboxPatch(
        (0.01, 0.01), 0.98, 0.98,
        boxstyle="round,pad=0.015,rounding_size=0.02",
        facecolor="#F5F6F8", edgecolor="#D8DDE2",
        linewidth=0.8, zorder=0,
    )
    ax.add_patch(bg)

    # Layout: 2 rows
    # Row 1: inputs → hf_sim → fwd_uq (top)
    # Row 2: (empty) → bnn → sobol → posterior (bottom, shifted right)
    # Actually, let's use a layout closer to the reference:
    # Row 1: inputs → hf_sim → fwd_uq
    # Row 2: (under inputs) → bnn (center) → sobol → posterior (right)

    box_w = 0.20
    box_h = 0.38

    positions = {
        "inputs":    (0.03, 0.52),
        "hf_sim":    (0.28, 0.52),
        "fwd_uq":    (0.53, 0.52),
        "bnn":       (0.28, 0.08),
        "sobol":     (0.53, 0.08),
        "posterior":  (0.78, 0.52),
    }

    for box_def in FLOW_BOXES:
        bid = box_def["id"]
        x, y = positions[bid]
        cset = BOX_COLORS[box_def["color"]]

        # Box
        bx = FancyBboxPatch(
            (x, y), box_w, box_h,
            boxstyle="round,pad=0.008,rounding_size=0.015",
            facecolor=cset["face"], edgecolor=cset["edge"],
            linewidth=0.8, zorder=2,
        )
        ax.add_patch(bx)

        # Title
        ax.text(x + box_w / 2, y + box_h - 0.04, box_def["title"],
                ha="center", va="top", fontsize=6.5, fontweight="bold",
                color=cset["title"], zorder=3)

        # Body lines (bullets)
        body_y = y + box_h - 0.15
        for line in box_def["lines"]:
            ax.text(x + 0.015, body_y, f"\u2022 {line}",
                    ha="left", va="top", fontsize=5.0,
                    color="#4A4A4A", zorder=3)
            body_y -= 0.09

    # Arrows
    arrow_kw = dict(arrowstyle="-|>", mutation_scale=10, lw=1.0,
                    color="#7A8A9A", shrinkA=3, shrinkB=3)

    arrows = [
        # inputs → hf_sim
        ((0.03 + box_w + 0.005, 0.52 + box_h / 2),
         (0.28 - 0.005, 0.52 + box_h / 2)),
        # hf_sim → fwd_uq
        ((0.28 + box_w + 0.005, 0.52 + box_h / 2),
         (0.53 - 0.005, 0.52 + box_h / 2)),
        # fwd_uq → posterior
        ((0.53 + box_w + 0.005, 0.52 + box_h / 2),
         (0.78 - 0.005, 0.52 + box_h / 2)),
        # inputs → bnn (down)
        ((0.03 + box_w / 2, 0.52 - 0.005),
         (0.28 - 0.005, 0.08 + box_h / 2)),
        # hf_sim → bnn (down)
        ((0.28 + box_w / 2, 0.52 - 0.005),
         (0.28 + box_w / 2, 0.08 + box_h + 0.005)),
        # bnn → sobol
        ((0.28 + box_w + 0.005, 0.08 + box_h / 2),
         (0.53 - 0.005, 0.08 + box_h / 2)),
        # sobol → posterior (up-right)
        ((0.53 + box_w + 0.005, 0.08 + box_h / 2),
         (0.78 - 0.005, 0.52 + 0.005)),
    ]

    for p1, p2 in arrows:
        arr = FancyArrowPatch(p1, p2, **arrow_kw, zorder=1)
        ax.add_patch(arr)


def draw_panel_image(ax, img_path, label, title):
    """Draw a panel with embedded pre-rendered image."""
    if img_path.exists():
        img = mpimg.imread(str(img_path))
        ax.imshow(img, aspect="auto")
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_edgecolor("#D0D0D0")
        spine.set_linewidth(0.6)

    ax.set_title(f"({label})  {title}", fontsize=8, fontweight="bold",
                 color="#1A1A1A", loc="left", pad=6)


def main():
    # Overall figure: workflow on top, 2x2 panels below
    fig = plt.figure(figsize=(12, 16))

    # Title
    fig.text(0.5, 0.98, "Figure 1. Probabilistic analysis framework",
             ha="center", va="top", fontsize=13, fontweight="bold",
             color="#1A1A1A")

    # Workflow axes (top 30%)
    ax_wf = fig.add_axes([0.03, 0.68, 0.94, 0.28])
    draw_workflow(ax_wf)

    # 2x2 panel grid (bottom 65%)
    gs = fig.add_gridspec(
        2, 2, left=0.04, right=0.97, top=0.66, bottom=0.02,
        wspace=0.08, hspace=0.10,
    )

    panels = [("A", gs[0, 0]), ("B", gs[0, 1]),
              ("C", gs[1, 0]), ("D", gs[1, 1])]

    for label, spec in panels:
        ax = fig.add_subplot(spec)
        img_path = PANEL_IMAGES[label]
        draw_panel_image(ax, img_path, label, PANEL_TITLES[label])

    # Save
    ncs_style.save_all(fig, "figure_overview", OUTDIR)
    plt.close(fig)
    print(f"Overview figure saved to: {OUTDIR}")


if __name__ == "__main__":
    main()
