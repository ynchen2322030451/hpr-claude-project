"""I3 — Small-sample data efficiency: stress R² vs training fraction.

Line plot comparing Reference surrogate and Multi-fidelity hybrid
at 20%, 40%, 60%, 100% training data.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

_HERE = Path(__file__).resolve().parent
_FIG  = _HERE.parent
if str(_FIG) not in sys.path:
    sys.path.insert(0, str(_FIG))

from figure_style import (
    set_publication_rc, finalize_axes, panel_label,
    C, LW, FS, FIG_WIDTH_SINGLE,
)
from figure_io import savefig

_BNN0414 = _FIG.parents[1]
_OUT_DIR = _BNN0414 / "manuscript" / "0414_v4" / "figures" / "bank"

# Data from comprehensive_comparison_v3418.txt Section 7
_FRACTIONS = [0.2, 0.4, 0.6, 1.0]
_LABELS = ["20%", "40%", "60%", "100%"]

_LINES = {
    "Reference surrogate":    {"r2": [0.928, 0.939, 0.946, 0.942], "color": C["main"],      "marker": "o"},
    "Multi-fidelity hybrid":  {"r2": [0.911, 0.935, 0.939, 0.942], "color": C["cat_thermal"], "marker": "s"},
}


def draw(fig=None, ax=None):
    if fig is None:
        fig, ax = plt.subplots(figsize=(FIG_WIDTH_SINGLE, 2.8))

    for label, d in _LINES.items():
        ax.plot(_FRACTIONS, d["r2"], marker=d["marker"], color=d["color"],
                lw=LW["main"], markersize=5, label=label, zorder=3)

    ax.set_xticks(_FRACTIONS)
    ax.set_xticklabels(_LABELS)
    ax.set_xlabel("Training fraction")
    ax.set_ylabel("Stress $R^2$")
    ax.set_title("Data efficiency: stress $R^2$ vs training fraction",
                 fontsize=FS["title"])
    ax.legend(fontsize=FS["legend"], frameon=False, loc="lower right")
    ax.set_ylim(0.905, 0.950)
    finalize_axes(ax)
    return fig, ax


def main():
    set_publication_rc()
    fig, ax = draw()
    panel_label(ax, "(A)")
    written = savefig(fig, "I3_small_sample", _OUT_DIR)
    for w in written:
        print("wrote", w)


if __name__ == "__main__":
    main()
