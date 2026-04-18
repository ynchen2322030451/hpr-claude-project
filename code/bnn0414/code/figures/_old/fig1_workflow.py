"""Figure 1 — Probabilistic analysis pipeline of the coupled HPR workflow.

Block-diagram schematic (matplotlib, no external rendering deps).

Phase-1 rulings enforced:
  * Only "uncoupled pass" / "coupled steady state" on figure face.
  * Caption-only one-sentence explanation of correspondence to first-pass
    / converged coupled response.
  * No threshold gate, no feasible-region checkmark, no old-surrogate
    upgrade arrow, no "HeteroMLP", no iter1/iter2.
  * No CJK text anywhere.
  * Data flow = solid arrow; distribution flow = dashed arrow.
  * Supplementary HF consistency check = side branch, not main path.
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from figure_io import savefig
from figure_style import COLORS, FONT_SIZES, apply_rc

_BNN0414 = _HERE.parents[1]
_FIG_DIR = _BNN0414 / "manuscript" / "0414_v4" / "figures"

# ── colour palette for workflow blocks ─────────────────────────────────────
C_INPUT   = "#D6EAF8"
C_HF      = "#FDEBD0"
C_DATASET = "#D5F5E3"
C_BNN     = "#D4E6F1"
C_ANALYSIS = "#EBF5FB"
C_HF_CHECK = "#F9E8E8"
C_EDGE    = "#444444"
C_ARROW   = "#333333"
C_DIST_ARROW = COLORS["bnn_main"]


def _box(ax, x, y, w, h, label, sub="", fc=C_INPUT, fontsize=8):
    p = FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.12", fc=fc, ec=C_EDGE, lw=1.0,
        zorder=2,
    )
    ax.add_patch(p)
    dy = 0.15 if sub else 0
    ax.text(x + w / 2, y + h / 2 + dy, label,
            ha="center", va="center", fontsize=fontsize,
            fontweight="bold", zorder=3)
    if sub:
        ax.text(x + w / 2, y + h / 2 - dy, sub,
                ha="center", va="center", fontsize=fontsize - 1.5,
                color="#555555", zorder=3)


def _arrow(ax, x1, y1, x2, y2, style="-|>", color=C_ARROW, lw=1.3,
           ls="-"):
    ax.annotate(
        "", xy=(x2, y2), xytext=(x1, y1),
        arrowprops=dict(arrowstyle=style, color=color, lw=lw, ls=ls),
        zorder=1,
    )


def main() -> None:
    apply_rc()

    fig, ax = plt.subplots(figsize=(7.2, 3.2))
    ax.set_xlim(-0.1, 12.5)
    ax.set_ylim(-0.3, 3.8)
    ax.axis("off")

    # ── Row 1: inputs → HF → dataset ──────────────────────────────────
    _box(ax, 0.0, 1.4, 2.0, 1.2,
         "8 material\nparameters",
         r"uniform priors $\theta_i$", fc=C_INPUT)

    _box(ax, 2.7, 1.6, 2.5, 0.8,
         "Coupled HF solver",
         "OpenMC\u2013FEniCS", fc=C_HF)

    # uncoupled/coupled label beneath HF box
    ax.text(3.95, 1.45, "uncoupled pass \u2192 coupled steady state",
            ha="center", va="top", fontsize=5.5, color="#777777",
            style="italic")

    _box(ax, 5.8, 1.6, 2.2, 0.8,
         "Training data",
         "n \u2248 2 900, 15 outputs", fc=C_DATASET)

    _arrow(ax, 2.0, 2.0, 2.7, 2.0)
    _arrow(ax, 5.2, 2.0, 5.8, 2.0)

    # ── Row 2: BNN surrogate ──────────────────────────────────────────
    _box(ax, 5.8, 0.0, 2.2, 1.0,
         "Bayesian neural\nsurrogate",
         r"$p(y\,|\,\theta,\mathcal{D})$", fc=C_BNN)

    _arrow(ax, 6.9, 1.6, 6.9, 1.0)

    # ── Row 3: three downstream analyses (top row, right side) ────────
    x_start = 8.7
    gap = 0.15
    bw = 2.4
    bh = 0.65

    analyses = [
        ("Forward UQ",
         "Monte Carlo propagation",
         3.0),
        (r"Sobol sensitivity $S_1, S_T$",
         "variance decomposition",
         2.1),
        ("Posterior calibration",
         "MH\u2013MCMC",
         1.2),
    ]

    for label, sub, by in analyses:
        _box(ax, x_start, by, bw, bh, label, sub, fc=C_ANALYSIS,
             fontsize=7.5)
        _arrow(ax, 8.0, 0.5, x_start, by + bh / 2,
               color=C_DIST_ARROW, ls="--", lw=1.0)

    # ── Side branch: HF consistency check ──────────────────────────────
    _box(ax, 8.7, 0.15, 2.4, 0.55,
         "HF consistency\nspot-check",
         "", fc=C_HF_CHECK, fontsize=7)
    _arrow(ax, 8.0, 0.3, 8.7, 0.42,
           color="#999999", ls=":", lw=0.8)

    written = savefig(fig, "fig1_workflow", _FIG_DIR)
    for w in written:
        print("wrote", w)


if __name__ == "__main__":
    main()
