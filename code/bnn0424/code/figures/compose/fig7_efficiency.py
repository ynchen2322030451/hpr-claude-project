"""Figure 7 — Computational Efficiency (SPEC Fig 4).

Layout: 1x2.
  (A) Budget-matched speedup (surrogate vs HF)
  (B) Data efficiency curve (RMSE vs training fraction)
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
from G1_speedup import draw as draw_g1
from F1_data_efficiency import draw as draw_f1

_BNN0414 = _FIG.parents[1]
_OUT_DIR = _BNN0414 / "manuscript" / "0414_v4" / "figures"


def compose():
    set_publication_rc()

    fig = plt.figure(figsize=(FIG_WIDTH_DOUBLE, 3.0))
    gs = gridspec.GridSpec(1, 2, figure=fig, wspace=0.45)

    ax_speed = fig.add_subplot(gs[0, 0])
    ax_data  = fig.add_subplot(gs[0, 1])

    draw_g1(fig=fig, ax=ax_speed)
    draw_f1(fig=fig, ax=ax_data)

    panel_label(ax_speed, "(A)")
    panel_label(ax_data,  "(B)")

    written = savefig(fig, "fig7_efficiency", _OUT_DIR)
    for w in written:
        print("wrote", w)


if __name__ == "__main__":
    compose()
