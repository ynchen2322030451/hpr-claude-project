"""Figure 4 — Sobol sensitivity analysis (composed from D3 S1+ST dual panel).

Layout: 2-column S1 vs ST bars for stress (A) and keff (B), with category
legend and S1/ST legend at bottom. Uses D3 for maximum information density.
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

    fig = plt.figure(figsize=(FIG_WIDTH_DOUBLE, 3.5))
    gs = gridspec.GridSpec(1, 2, figure=fig,
                           width_ratios=[1, 1],
                           wspace=0.50)

    axes = [fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[0, 1])]

    draw_d3(fig=fig, axes=axes)

    panel_label(axes[0], "(A)")
    panel_label(axes[1], "(B)")

    written = savefig(fig, "fig4_sobol", _OUT_DIR)
    for w in written:
        print("wrote", w)


if __name__ == "__main__":
    compose()
