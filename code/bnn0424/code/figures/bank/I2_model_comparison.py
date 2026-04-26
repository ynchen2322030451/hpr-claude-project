"""I2 — Four-model key metrics comparison.

2x2 bar chart: Stress R², keff R², Stress MPIW, Stress CRPS
across Reference / Physics-regularized / Homoscedastic / Multi-fidelity.
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
    C, LW, FS, FIG_WIDTH_DOUBLE,
)
from figure_io import savefig

_BNN0414 = _FIG.parents[1]
_OUT_DIR = _BNN0414 / "manuscript" / "0414_v4" / "figures" / "bank"

# Hard-coded from comprehensive_comparison_v3418.txt Section 1
_MODELS = [
    ("Reference surrogate",          "#2F5AA6"),
    ("Physics-regularized",          "#3A7D7B"),
    ("Homoscedastic ablation",       "#707070"),
    ("Multi-fidelity hybrid",        "#D4853A"),
]

_DATA = {
    "Stress $R^2$":   [0.9418, 0.9438, 0.9402, 0.9417],
    "$k_{\\mathrm{eff}}$ $R^2$": [0.8445, 0.8492, 0.8327, 0.8110],
    "Stress MPIW (MPa)": [40.2, 39.4, 45.2, 47.8],
    "Stress CRPS":    [4.424, 4.350, 4.683, 4.772],
}

_PANEL_LABELS = ["(A)", "(B)", "(C)", "(D)"]


def draw(fig=None, axes=None):
    if fig is None:
        fig, axes = plt.subplots(2, 2, figsize=(FIG_WIDTH_DOUBLE, 4.5))
        axes = axes.ravel()

    x = np.arange(len(_MODELS))
    colors = [m[1] for m in _MODELS]
    labels = [m[0] for m in _MODELS]

    for ax, (metric, vals), plabel in zip(axes, _DATA.items(), _PANEL_LABELS):
        bars = ax.bar(x, vals, 0.65, color=colors, alpha=0.85, zorder=2)
        ax.set_xticks(x)
        ax.set_xticklabels(labels, fontsize=FS["tick"] - 0.5, rotation=20, ha="right")
        ax.set_ylabel(metric, fontsize=FS["axis"])

        # Value labels on bars
        for bar, v in zip(bars, vals):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                    f"{v:.3f}" if v < 1 else f"{v:.1f}",
                    ha="center", va="bottom", fontsize=FS["metric"],
                    color=C["text"])

        finalize_axes(ax)
        panel_label(ax, plabel)

    fig.subplots_adjust(hspace=0.55, wspace=0.40)
    return fig, axes


def main():
    set_publication_rc()
    fig, axes = draw()
    written = savefig(fig, "I2_model_comparison", _OUT_DIR)
    for w in written:
        print("wrote", w)


if __name__ == "__main__":
    main()
