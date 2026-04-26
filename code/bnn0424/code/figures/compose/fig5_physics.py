"""Figure 5 — Physics Consistency (SPEC Fig 2).

Layout: 2 rows.
  Row 0: (A) Monotonicity violation heatmaps (baseline vs phy-mono)
  Row 1: (B) Uncertainty decomposition (epistemic vs aleatoric)
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

    fig = plt.figure(figsize=(FIG_WIDTH_DOUBLE, 5.8))
    gs = gridspec.GridSpec(2, 1, figure=fig,
                           height_ratios=[1.2, 1],
                           hspace=0.45)

    # Row 0: monotonicity heatmaps (two subplots inside)
    gs_mono = gridspec.GridSpecFromSubplotSpec(1, 2, subplot_spec=gs[0],
                                               wspace=0.35)
    axes_mono = [fig.add_subplot(gs_mono[0, i]) for i in range(2)]

    # Row 1: uncertainty decomposition
    ax_decomp = fig.add_subplot(gs[1])

    draw_f3(fig=fig, axes=axes_mono)
    draw_f4(fig=fig, ax=ax_decomp)

    panel_label(axes_mono[0], "(A)")
    panel_label(ax_decomp,    "(B)")

    written = savefig(fig, "fig5_physics", _OUT_DIR)
    for w in written:
        print("wrote", w)


if __name__ == "__main__":
    compose()
