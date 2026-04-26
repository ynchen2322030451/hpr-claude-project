"""I1 — Heteroscedastic vs homoscedastic noise modelling ablation.

Compares bnn-baseline (heteroscedastic) with bnn-baseline-homo (homoscedastic)
on stress calibration metrics by stress-level bin.
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
    C, LW, FS, FIG_WIDTH_DOUBLE,
)
from figure_io import savefig

_BNN0414 = _FIG.parents[1]
_DATA    = _BNN0414 / "results" / "results_v3418" / "analysis" / "near_threshold_calibration.csv"
_OUT_DIR = _BNN0414 / "manuscript" / "0414_v4" / "figures" / "bank"

_MODELS = {
    "bnn-baseline":      "Heteroscedastic",
    "bnn-baseline-homo": "Homoscedastic",
}
_MODEL_COLORS = {
    "bnn-baseline":      C["main"],
    "bnn-baseline-homo": C["reference"],
}
_BIN_ORDER = ["low (<110 MPa)", "near-threshold (110-150 MPa)", "high (>150 MPa)", "all"]
_BIN_LABELS = ["Low", "Near-threshold", "High", "All"]


def load():
    df = pd.read_csv(_DATA)
    df = df[df.model.isin(_MODELS.keys())].copy()
    return df


def draw(fig=None, axes=None):
    df = load()

    if fig is None:
        fig, axes = plt.subplots(1, 2, figsize=(FIG_WIDTH_DOUBLE, 2.8))

    for ax, metric, ylabel in zip(
        axes,
        ["MPIW", "CRPS"],
        ["MPIW (MPa)", "CRPS"],
    ):
        x = np.arange(len(_BIN_ORDER))
        w = 0.32
        for i, (model_id, label) in enumerate(_MODELS.items()):
            sub = df[df.model == model_id]
            vals = []
            for b in _BIN_ORDER:
                row = sub[sub.bin == b]
                vals.append(row[metric].values[0] if len(row) > 0 else 0)
            offset = -w / 2 + i * w
            ax.bar(x + offset, vals, w * 0.9, label=label,
                   color=_MODEL_COLORS[model_id], alpha=0.85, zorder=2)

        ax.set_xticks(x)
        ax.set_xticklabels(_BIN_LABELS, fontsize=FS["tick"])
        ax.set_ylabel(ylabel)
        ax.legend(fontsize=FS["legend"], frameon=False, loc="upper left")
        finalize_axes(ax)

    fig.suptitle(
        "Heteroscedastic vs homoscedastic noise modelling\n"
        "— stress calibration by bin",
        fontsize=FS["title"], y=1.02,
    )
    return fig, axes


def main():
    set_publication_rc()
    fig, axes = draw()
    panel_label(axes[0], "(A)")
    panel_label(axes[1], "(B)")
    written = savefig(fig, "I1_homo_ablation", _OUT_DIR)
    for w in written:
        print("wrote", w)


if __name__ == "__main__":
    main()
