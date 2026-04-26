"""Figure A2 — Physics robustness appendix (F3 + F4).

Layout: 2 rows.
  Top row: F3 monotonicity heatmaps (spans full width, 2 sub-axes)
  Bottom row: F4 uncertainty decomposition (single axis, full width)
Panel labels (A), (B).
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

_HERE = Path(__file__).resolve().parent
_FIG  = _HERE.parent
if str(_FIG) not in sys.path:
    sys.path.insert(0, str(_FIG))

sys.path.insert(0, str(_FIG / "bank"))

from figure_style import set_publication_rc, panel_label, FIG_WIDTH_DOUBLE
from figure_io import savefig
from F3_monotonicity import draw as draw_f3
from F4_uncertainty_decomp import draw as draw_f4

_BNN0414 = _FIG.parents[1]
_OUT_DIR = _BNN0414 / "manuscript" / "0414_v4" / "figures"


def compose():
    set_publication_rc()

    fig = plt.figure(figsize=(FIG_WIDTH_DOUBLE, 5.5))
    gs = gridspec.GridSpec(2, 2, figure=fig,
                           height_ratios=[1.2, 1],
                           hspace=0.50, wspace=0.35)

    # Top row: F3 needs two axes side by side
    ax_f3_left  = fig.add_subplot(gs[0, 0])
    ax_f3_right = fig.add_subplot(gs[0, 1])

    # Bottom row: F4 spans full width
    ax_f4 = fig.add_subplot(gs[1, :])

    draw_f3(fig=fig, axes=[ax_f3_left, ax_f3_right])
    draw_f4(fig=fig, ax=ax_f4)

    panel_label(ax_f3_left, "(A)")
    panel_label(ax_f4, "(B)")

    written = savefig(fig, "figA2_physics_robustness", _OUT_DIR)
    for w in written:
        print("wrote", w)


if __name__ == "__main__":
    compose()
