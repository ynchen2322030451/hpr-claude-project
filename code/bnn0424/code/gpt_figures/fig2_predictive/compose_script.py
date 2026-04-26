"""Figure 2 — Predictive behaviour (composed from B1 + B2 + B3).

Layout (2 rows, 2 cols):
  Row 0: stress parity (A) spanning left  |  keff (B) top-right
  Row 1: stress parity cont'd             |  thermal (C) bottom-right

No table — pure visual panels only.
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
from B1_stress_parity import draw as draw_b1
from B2_keff_parity import draw as draw_b2
from B3_thermal_parity import draw as draw_b3

_BNN0414 = _FIG.parents[1]
_OUT_DIR = _BNN0414 / "manuscript" / "0414_v4" / "figures"


def compose():
    set_publication_rc()

    fig = plt.figure(figsize=(FIG_WIDTH_DOUBLE, 5.0))
    gs = gridspec.GridSpec(
        2, 2, figure=fig,
        width_ratios=[1.4, 1],
        height_ratios=[1, 1],
        hspace=0.45, wspace=0.55,
    )

    ax_stress = fig.add_subplot(gs[0:2, 0])
    ax_keff   = fig.add_subplot(gs[0, 1])
    ax_temp   = fig.add_subplot(gs[1, 1])

    draw_b1(fig=fig, ax=ax_stress, show_colorbar=True)
    draw_b2(fig=fig, ax=ax_keff, show_colorbar=False)
    draw_b3(fig=fig, ax=ax_temp, show_colorbar=False)

    panel_label(ax_stress, "(A)")
    panel_label(ax_keff,   "(B)")
    panel_label(ax_temp,   "(C)")

    written = savefig(fig, "fig2_predictive", _OUT_DIR)
    for w in written:
        print("wrote", w)


if __name__ == "__main__":
    compose()
