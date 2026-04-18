"""Figure A4 — Sobol index detail appendix (D3).

D3 draws S1 vs ST dual panel with its own 2 axes.
Panel labels are applied here for consistency with other compose figures.
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
from D3_sobol_total import draw as draw_d3

_BNN0414 = _FIG.parents[1]
_OUT_DIR = _BNN0414 / "manuscript" / "0414_v4" / "figures"


def compose():
    set_publication_rc()

    fig = plt.figure(figsize=(FIG_WIDTH_DOUBLE, 3.2))
    gs = gridspec.GridSpec(1, 2, figure=fig, wspace=0.45)

    ax_left  = fig.add_subplot(gs[0, 0])
    ax_right = fig.add_subplot(gs[0, 1])

    draw_d3(fig=fig, axes=[ax_left, ax_right])

    # Panel labels handled by D3 internally — but the user spec says
    # "panel labels handled by D3 internally", so we skip adding them here.

    written = savefig(fig, "figA4_sobol_detail", _OUT_DIR)
    for w in written:
        print("wrote", w)


if __name__ == "__main__":
    compose()
