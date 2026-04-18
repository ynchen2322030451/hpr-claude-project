"""Figure 1 — Prediction Accuracy & Calibration (SPEC Fig 1).

Layout: 2 rows.
  Row 0: (A) Reliability diagram  |  (B-C) PIT histograms (stress + keff)
  Row 1: (D) CRPS comparison      |  (E) ECE comparison
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
from B4_calibration_reliability import draw as draw_b4
from B6_pit_histogram import draw as draw_b6
from B7_scoring_rules import draw as draw_b7

_BNN0414 = _FIG.parents[1]
_OUT_DIR = _BNN0414 / "manuscript" / "0414_v4" / "figures"


def compose():
    set_publication_rc()

    fig = plt.figure(figsize=(FIG_WIDTH_DOUBLE, 5.6))
    gs = gridspec.GridSpec(2, 3, figure=fig,
                           width_ratios=[1, 1, 1],
                           height_ratios=[1, 1],
                           hspace=0.50, wspace=0.45)

    # Row 0: reliability (spanning col 0) + PIT histograms (cols 1-2)
    ax_rel = fig.add_subplot(gs[0, 0])
    ax_pit_stress = fig.add_subplot(gs[0, 1])
    ax_pit_keff = fig.add_subplot(gs[0, 2])

    # Row 1: scoring rules (cols 0-1 for CRPS, col 2 for ECE)
    ax_crps = fig.add_subplot(gs[1, 0:2])
    ax_ece = fig.add_subplot(gs[1, 2])

    draw_b4(fig=fig, ax=ax_rel)
    draw_b6(fig=fig, axes=[ax_pit_stress, ax_pit_keff])
    draw_b7(fig=fig, axes=[ax_crps, ax_ece])

    panel_label(ax_rel,        "(A)")
    panel_label(ax_pit_stress, "(B)")
    panel_label(ax_pit_keff,   "(C)")
    panel_label(ax_crps,       "(D)")
    panel_label(ax_ece,        "(E)")

    written = savefig(fig, "fig1_accuracy", _OUT_DIR)
    for w in written:
        print("wrote", w)


if __name__ == "__main__":
    compose()
