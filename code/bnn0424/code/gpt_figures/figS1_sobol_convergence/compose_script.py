"""Figure S1 — Sobol Sensitivity Convergence (SPEC Fig S1).

Layout: 1x2 (stress + keff), top-3 inputs with CI bands.
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
from D4_sobol_convergence import draw as draw_d4

_BNN0414 = _FIG.parents[1]
_OUT_DIR = _BNN0414 / "manuscript" / "0414_v4" / "figures"


def compose():
    set_publication_rc()

    fig = plt.figure(figsize=(FIG_WIDTH_DOUBLE, 3.0))
    gs = gridspec.GridSpec(1, 2, figure=fig, wspace=0.40)
    axes = [fig.add_subplot(gs[0, i]) for i in range(2)]

    draw_d4(fig=fig, axes=axes)

    panel_label(axes[0], "(A)")
    panel_label(axes[1], "(B)")

    written = savefig(fig, "figS1_sobol_convergence", _OUT_DIR)
    for w in written:
        print("wrote", w)


if __name__ == "__main__":
    compose()
