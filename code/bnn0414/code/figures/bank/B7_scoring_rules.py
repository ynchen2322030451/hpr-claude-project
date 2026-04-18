"""B7 — Scoring rules comparison (CRPS + ECE) across 6 models.

Grouped horizontal bars for stress output. Highlights physics-reg BNN.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

_HERE = Path(__file__).resolve().parent
_FIG  = _HERE.parent
if str(_FIG) not in sys.path:
    sys.path.insert(0, str(_FIG))

from figure_style import (
    set_publication_rc, finalize_axes, panel_label,
    C, FS, FIG_WIDTH_DOUBLE,
)
from figure_io import savefig

_BNN0414   = _FIG.parents[1]
_MASTER    = _BNN0414 / "results" / "master_comparison_table.csv"
_OUT_DIR   = _BNN0414 / "manuscript" / "0414_v4" / "figures" / "bank"

MODEL_ORDER = [
    "bnn-phy-mono", "bnn-baseline", "bnn-data-mono",
    "bnn-data-mono-ineq", "mc-dropout", "deep-ensemble",
]
MODEL_LABELS = {
    "bnn-phy-mono":      "Phy-reg. BNN",
    "bnn-baseline":      "Ref. BNN",
    "bnn-data-mono":     "Data-mono BNN",
    "bnn-data-mono-ineq":"Data+ineq BNN",
    "mc-dropout":        "MC-Dropout",
    "deep-ensemble":     "Deep Ensemble",
}
MODEL_COLORS = {
    "bnn-phy-mono":       C["posterior"],
    "bnn-baseline":       C["main"],
    "bnn-data-mono":      "#5B9BD5",
    "bnn-data-mono-ineq": "#7B6BA5",
    "mc-dropout":         C["mc_dropout"],
    "deep-ensemble":      C["deep_ensemble"],
}

OUTPUT = "iteration2_max_global_stress"


def load():
    df = pd.read_csv(_MASTER)
    return df[df.output == OUTPUT]


def draw(fig=None, axes=None):
    df = load()

    if fig is None:
        fig, axes = plt.subplots(1, 2, figsize=(FIG_WIDTH_DOUBLE, 2.8))
    ax_crps, ax_ece = axes

    for ax, metric, xlabel in [
        (ax_crps, "CRPS", "CRPS (stress)"),
        (ax_ece,  "ECE",  "ECE (stress)"),
    ]:
        vals, labels, colors = [], [], []
        for mid in MODEL_ORDER:
            row = df[df.model_id == mid]
            if len(row) == 0:
                continue
            v = float(row[metric].values[0])
            vals.append(v)
            labels.append(MODEL_LABELS[mid])
            colors.append(MODEL_COLORS[mid])

        y = np.arange(len(vals))
        ax.barh(y, vals, height=0.55, color=colors, alpha=0.85,
                edgecolor="none", zorder=2)
        ax.set_yticks(y)
        ax.set_yticklabels(labels)
        ax.set_xlabel(xlabel)
        ax.invert_yaxis()
        finalize_axes(ax)

    return fig, axes


def main():
    set_publication_rc()
    fig, axes = draw()
    panel_label(axes[0], "(A)")
    panel_label(axes[1], "(B)")
    fig.tight_layout()
    written = savefig(fig, "B7_scoring_rules", _OUT_DIR)
    for w in written:
        print("wrote", w)


if __name__ == "__main__":
    main()
