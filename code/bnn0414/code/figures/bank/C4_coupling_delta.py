"""C4 — Coupling shift analysis (uncoupled-to-coupled delta per output).

Bar chart of predicted delta_mean with std whiskers for 4 coupled outputs.
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
    C, LW, FS, FIG_WIDTH_SINGLE,
)
from figure_io import savefig

_BNN0414    = _FIG.parents[1]
_DELTA_CSV  = (_BNN0414 / "code" / "experiments" / "risk_propagation" /
               "bnn-phy-mono" / "D3_coupling.csv")
_OUT_DIR    = _BNN0414 / "manuscript" / "0414_v4" / "figures" / "bank"

OUTPUT_LABELS = {
    "avg_fuel_temp":              "Avg. fuel temp.",
    "max_fuel_temp":              "Max. fuel temp.",
    "max_monolith_temp":          "Max. monolith temp.",
    "max_global_stress":          "Max. von Mises stress",
    "monolith_new_temperature":   "Monolith surface temp.",
    "Hcore_after":                "Core height change",
    "wall2":                      "Wall expansion",
}

PRIMARY = ["max_global_stress", "max_fuel_temp", "max_monolith_temp", "avg_fuel_temp"]


def load():
    return pd.read_csv(_DELTA_CSV)


def draw(fig=None, ax=None):
    df = load()
    df = df[df.output_short.isin(PRIMARY)].copy()

    if fig is None:
        fig, ax = plt.subplots(figsize=(FIG_WIDTH_SINGLE, 2.2))

    labels = [OUTPUT_LABELS.get(s, s) for s in df.output_short]
    y = np.arange(len(labels))
    means = df.pred_delta_mean.values
    stds  = df.pred_delta_std.values

    colors = [C["main"] if m < 0 else C["cat_thermal"] for m in means]

    ax.barh(y, means, height=0.55, color=colors, alpha=0.75,
            edgecolor="none", zorder=2)
    ax.errorbar(means, y, xerr=stds,
                fmt="none", ecolor="#555555", elinewidth=0.6,
                capsize=2, capthick=0.6, zorder=3)

    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.set_xlabel("Coupling shift (coupled - uncoupled)")
    ax.axvline(0, color="#AAAAAA", lw=0.5, zorder=0)
    ax.invert_yaxis()

    finalize_axes(ax)
    return fig, ax


def main():
    set_publication_rc()
    fig, ax = draw()
    panel_label(ax, "(A)")
    written = savefig(fig, "C4_coupling_delta", _OUT_DIR)
    for w in written:
        print("wrote", w)


if __name__ == "__main__":
    main()
