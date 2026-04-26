"""Figure A1 — Model validation appendix (B4 + B5).

Layout: 2 rows.
  Row 0: (A) Calibration reliability diagram
  Row 1: (B) R² comparison  |  (C) RMSE comparison (log scale)
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
from B5_external_baseline import draw as draw_b5

_BNN0414 = _FIG.parents[1]
_OUT_DIR = _BNN0414 / "manuscript" / "0414_v4" / "figures"


def compose():
    set_publication_rc()

    fig = plt.figure(figsize=(FIG_WIDTH_DOUBLE, 5.6))
    gs = gridspec.GridSpec(2, 2, figure=fig,
                           width_ratios=[1, 1],
                           height_ratios=[1, 1],
                           hspace=0.50, wspace=0.40)

    # Row 0: calibration reliability (spanning both cols)
    ax_b4 = fig.add_subplot(gs[0, :])

    # Row 1: B5 dual panel (R² + RMSE)
    ax_r2   = fig.add_subplot(gs[1, 0])
    ax_rmse = fig.add_subplot(gs[1, 1])

    draw_b4(fig=fig, ax=ax_b4)
    draw_b5(fig=fig, axes=[ax_r2, ax_rmse])

    panel_label(ax_b4,   "(A)")
    panel_label(ax_r2,   "(B)")
    panel_label(ax_rmse, "(C)")

    written = savefig(fig, "figA1_model_validation", _OUT_DIR)
    for w in written:
        print("wrote", w)


if __name__ == "__main__":
    compose()
