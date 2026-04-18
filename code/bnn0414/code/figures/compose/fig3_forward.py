"""Figure 3 — Forward UQ distributions (composed from C1 + C2 + C3 + C4).

Layout: 2x2 grid.
  (A) C1 stress coupling KDE          (B) C2 keff distribution
  (C) C4 coupling delta bar chart     (D) C3 risk exceedance curves
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
from C1_stress_coupling import draw as draw_c1
from C2_keff_distribution import draw as draw_c2
from C3_risk_curve import draw as draw_c3
from C4_coupling_delta import draw as draw_c4

_BNN0414 = _FIG.parents[1]
_OUT_DIR = _BNN0414 / "manuscript" / "0414_v4" / "figures"


def compose():
    set_publication_rc()

    fig = plt.figure(figsize=(FIG_WIDTH_DOUBLE, 5.0))
    gs = gridspec.GridSpec(2, 2, figure=fig,
                           width_ratios=[1.2, 1],
                           height_ratios=[1, 1],
                           hspace=0.45, wspace=0.42)

    ax_a = fig.add_subplot(gs[0, 0])
    ax_b = fig.add_subplot(gs[0, 1])
    ax_c = fig.add_subplot(gs[1, 0])
    ax_d = fig.add_subplot(gs[1, 1])

    draw_c1(fig=fig, ax=ax_a)
    draw_c2(fig=fig, ax=ax_b)
    draw_c4(fig=fig, ax=ax_c)
    draw_c3(fig=fig, ax=ax_d)

    panel_label(ax_a, "(A)")
    panel_label(ax_b, "(B)")
    panel_label(ax_c, "(C)")
    panel_label(ax_d, "(D)")

    written = savefig(fig, "fig3_forward", _OUT_DIR)
    for w in written:
        print("wrote", w)


if __name__ == "__main__":
    compose()
