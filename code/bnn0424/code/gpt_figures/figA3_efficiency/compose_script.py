"""Figure A3 — Efficiency appendix (F1 + F2 + G1).

Layout: 1x3, equal width.
  (A) Data efficiency learning curves
  (B) OOD epistemic uncertainty ratio
  (C) Computational speedup
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
from F1_data_efficiency import draw as draw_f1
from F2_ood_epistemic import draw as draw_f2
from G1_speedup import draw as draw_g1

_BNN0414 = _FIG.parents[1]
_OUT_DIR = _BNN0414 / "manuscript" / "0414_v4" / "figures"


def compose():
    set_publication_rc()

    fig = plt.figure(figsize=(FIG_WIDTH_DOUBLE, 2.8))
    gs = gridspec.GridSpec(1, 3, figure=fig, wspace=0.55)

    ax_f1 = fig.add_subplot(gs[0, 0])
    ax_f2 = fig.add_subplot(gs[0, 1])
    ax_g1 = fig.add_subplot(gs[0, 2])

    draw_f1(fig=fig, ax=ax_f1)
    draw_f2(fig=fig, ax=ax_f2)
    draw_g1(fig=fig, ax=ax_g1)

    panel_label(ax_f1, "(A)")
    panel_label(ax_f2, "(B)")
    panel_label(ax_g1, "(C)")

    written = savefig(fig, "figA3_efficiency", _OUT_DIR)
    for w in written:
        print("wrote", w)


if __name__ == "__main__":
    compose()
