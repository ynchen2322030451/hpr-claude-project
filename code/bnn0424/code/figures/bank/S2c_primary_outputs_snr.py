"""S2c — Signal-to-noise profile of all five primary coupled outputs.

Shows why R^2 varies across outputs: thermal outputs have compressed variance
(low signal) despite good absolute accuracy (low RMSE), while stress and
wall expansion retain large variance (high signal).

Panel (a): Test-set std vs RMSE for each output (log scale)
Panel (b): RMSE/std ratio (= sqrt(1-R^2) proxy) — direct explanation of R^2
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

_BNN0424   = _FIG.parents[1]
_METR_CSV  = (_BNN0424 / "code" / "models" / "bnn-phy-mono" /
              "fixed_eval" / "metrics_per_output_fixed.csv")
import json
_PRED_JSON = (_BNN0424 / "code" / "models" / "bnn-phy-mono" /
              "fixed_eval" / "test_predictions_fixed.json")
_OUT_DIR   = _BNN0424 / "manuscript" / "0414_v4" / "figures" / "bank"

PRIMARY = [
    ("iteration2_max_global_stress",    "Stress",       "MPa",  11),
    ("iteration2_keff",                 r"$k_\mathrm{eff}$", "",  7),
    ("iteration2_max_fuel_temp",        "Max fuel\ntemp", "K",  9),
    ("iteration2_max_monolith_temp",    "Max monolith\ntemp", "K", 10),
    ("iteration2_wall2",                "Wall\nexpansion", "cm", 14),
]


def load():
    metr = pd.read_csv(_METR_CSV)
    with open(_PRED_JSON) as f:
        d = json.load(f)
    y_true = np.array(d["y_true"])
    return metr, y_true


def draw():
    metr, y_true = load()
    set_publication_rc()

    fig, (ax1, ax2) = plt.subplots(
        1, 2, figsize=(FIG_WIDTH_DOUBLE, FIG_WIDTH_DOUBLE * 0.40),
        constrained_layout=True,
    )

    labels = [p[1] for p in PRIMARY]
    x = np.arange(len(labels))
    w = 0.35

    stds  = [y_true[:, p[3]].std() for p in PRIMARY]
    rmses = [float(metr[metr["output"] == p[0]]["RMSE"].iloc[0]) for p in PRIMARY]
    r2s   = [float(metr[metr["output"] == p[0]]["R2"].iloc[0]) for p in PRIMARY]
    ratios = [r / s if s > 0 else 0 for r, s in zip(rmses, stds)]

    colors = [C["coupled"]] * len(PRIMARY)

    ax1.bar(x - w/2, stds, w, color=C["uncoupled"], label="Test-set std", alpha=0.85)
    ax1.bar(x + w/2, rmses, w, color=C["coupled"], label="RMSE", alpha=0.85)
    ax1.set_ylabel("Value (output units)")
    ax1.set_yscale("log")
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels, fontsize=FS["tick"] - 0.5)
    ax1.legend(fontsize=FS["legend"], loc="upper right")
    finalize_axes(ax1)
    panel_label(ax1, "(a)")
    ax1.set_title("Signal vs prediction error", fontsize=FS["title"])

    bar_colors = []
    for r in r2s:
        if r > 0.95:
            bar_colors.append(C["cat_elastic"])
        elif r > 0.75:
            bar_colors.append(C["cat_conduct"])
        else:
            bar_colors.append(C["cat_thermal"])

    bars = ax2.bar(x, ratios, 0.6, color=bar_colors, alpha=0.85)
    for i, (ratio, r2) in enumerate(zip(ratios, r2s)):
        ax2.text(i, ratio + 0.01, f"R²={r2:.3f}",
                 ha="center", va="bottom", fontsize=FS["tick"] - 0.5,
                 color=C["text"])
    ax2.set_ylabel("RMSE / std")
    ax2.set_xticks(x)
    ax2.set_xticklabels(labels, fontsize=FS["tick"] - 0.5)
    ax2.axhline(1.0, color=C["refline"], ls="--", lw=LW["ref"], alpha=0.5)
    finalize_axes(ax2)
    panel_label(ax2, "(b)")
    ax2.set_title("Normalized prediction error", fontsize=FS["title"])
    ax2.set_ylim(0, max(ratios) * 1.35)

    return fig


def main():
    fig = draw()
    written = savefig(fig, "S2c_primary_outputs_snr", _OUT_DIR)
    for w in written:
        print("wrote", w)


if __name__ == "__main__":
    main()
