"""B8 — External baseline reliability diagrams (MC-Dropout + Deep Ensemble).

Two subplots: each shows 5 output calibration curves.
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
_CAL_CSV   = _BNN0414 / "results" / "accuracy" / "external_baseline_calibration.csv"
_OUT_DIR   = _BNN0414 / "manuscript" / "0414_v4" / "figures" / "bank"

PRIMARY_OUTPUTS = [
    "iteration2_max_global_stress",
    "iteration2_keff",
    "iteration2_max_fuel_temp",
    "iteration2_max_monolith_temp",
    "iteration2_wall2",
]
OUTPUT_LABELS = {
    "iteration2_keff":              r"$k_\mathrm{eff}$",
    "iteration2_max_fuel_temp":     "Max fuel temp",
    "iteration2_max_monolith_temp": "Max monolith temp",
    "iteration2_max_global_stress": "Max stress",
    "iteration2_wall2":             "Wall expansion",
}
OUTPUT_COLORS = ["#2F5AA6", "#D4853A", "#3A7D7B", "#7B6BA5", "#CC6677"]

MODELS = [
    ("mc-dropout",    "MC-Dropout"),
    ("deep-ensemble", "Deep Ensemble"),
]


def load():
    return pd.read_csv(_CAL_CSV)


def draw(fig=None, axes=None):
    df = load()

    if fig is None:
        fig, axes = plt.subplots(1, 2, figsize=(FIG_WIDTH_DOUBLE, 3.0))

    for ax, (mid, mtitle) in zip(axes, MODELS):
        sub = df[df.model_id == mid]

        # perfect calibration line
        ax.plot([0, 1], [0, 1], "--", color=C["refline"], lw=0.7, zorder=0,
                label="Perfect")

        for k, out in enumerate(PRIMARY_OUTPUTS):
            s = sub[sub.output == out].sort_values("nominal_alpha")
            if len(s) == 0:
                continue
            ax.plot(s.nominal_alpha, s.empirical_coverage, "o-",
                    color=OUTPUT_COLORS[k], markersize=3, lw=0.9,
                    label=OUTPUT_LABELS[out], zorder=2)

        ax.set_xlabel("Nominal coverage")
        ax.set_ylabel("Empirical coverage")
        ax.set_title(mtitle, fontsize=FS["title"], pad=4)
        ax.set_xlim(0.45, 1.02)
        ax.set_ylim(0.45, 1.05)
        ax.set_aspect("equal", adjustable="box")
        finalize_axes(ax)

    axes[0].legend(fontsize=FS["legend"] - 0.5, frameon=False,
                   loc="upper left", handlelength=1.2)

    return fig, axes


def main():
    set_publication_rc()
    fig, axes = draw()
    panel_label(axes[0], "(A)")
    panel_label(axes[1], "(B)")
    fig.tight_layout()
    written = savefig(fig, "B8_external_baseline_calib", _OUT_DIR)
    for w in written:
        print("wrote", w)


if __name__ == "__main__":
    main()
