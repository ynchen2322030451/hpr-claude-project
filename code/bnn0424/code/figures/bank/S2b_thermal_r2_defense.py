"""S2b — Thermal R^2 defense: variance compression explains low R^2 (SI figure).

Bar chart showing iter1 vs iter2 std and RMSE for thermal outputs,
demonstrating that coupling compresses variance while absolute error improves.
"""
from __future__ import annotations

import json
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

_BNN0424   = _FIG.parents[1]
_PRED_JSON = (_BNN0424 / "code" / "models" / "bnn-phy-mono" /
              "fixed_eval" / "test_predictions_fixed.json")
_METR_CSV  = (_BNN0424 / "code" / "models" / "bnn-phy-mono" /
              "fixed_eval" / "metrics_per_output_fixed.csv")
_OUT_DIR   = _BNN0424 / "manuscript" / "0414_v4" / "figures" / "bank"

PAIRS = [
    ("Max fuel temp",      1,  9),
    ("Max monolith temp",  2,  10),
    ("Avg fuel temp",      0,  8),
    ("Monolith temp",      4,  12),
]


def load():
    with open(_PRED_JSON) as f:
        d = json.load(f)
    metr = pd.read_csv(_METR_CSV)
    return np.array(d["y_true"]), metr


def draw():
    y_true, metr = load()
    set_publication_rc()

    fig, (ax1, ax2) = plt.subplots(
        1, 2, figsize=(FIG_WIDTH_DOUBLE, FIG_WIDTH_DOUBLE * 0.38),
        constrained_layout=True,
    )

    labels = [p[0] for p in PAIRS]
    x = np.arange(len(labels))
    w = 0.35

    std1 = [y_true[:, p[1]].std() for p in PAIRS]
    std2 = [y_true[:, p[2]].std() for p in PAIRS]
    rmse1 = [metr.iloc[p[1]]["RMSE"] for p in PAIRS]
    rmse2 = [metr.iloc[p[2]]["RMSE"] for p in PAIRS]

    ax1.bar(x - w/2, std1, w, color=C["uncoupled"], label="Single-pass")
    ax1.bar(x + w/2, std2, w, color=C["coupled"], label="Coupled")
    ax1.set_ylabel("Test-set std (K)")
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels, rotation=25, ha="right", fontsize=FS["tick"])
    ax1.legend(fontsize=FS["legend"])
    finalize_axes(ax1)
    panel_label(ax1, "(a)")
    ax1.set_title("Signal variance", fontsize=FS["title"])

    ax2.bar(x - w/2, rmse1, w, color=C["uncoupled"], label="Single-pass")
    ax2.bar(x + w/2, rmse2, w, color=C["coupled"], label="Coupled")
    ax2.set_ylabel("RMSE (K)")
    ax2.set_xticks(x)
    ax2.set_xticklabels(labels, rotation=25, ha="right", fontsize=FS["tick"])
    ax2.legend(fontsize=FS["legend"])
    finalize_axes(ax2)
    panel_label(ax2, "(b)")
    ax2.set_title("Prediction error", fontsize=FS["title"])

    return fig


def main():
    fig = draw()
    written = savefig(fig, "S2b_thermal_r2_defense", _OUT_DIR)
    for w in written:
        print("wrote", w)


if __name__ == "__main__":
    main()
