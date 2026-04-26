"""F1 — Data-efficiency learning curves (RMSE vs training size).

Two lines: Reference surrogate (grey) and Physics-regularized (blue),
with shaded std bands.
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
    C, A, LW, FS, FIG_WIDTH_SINGLE,
)
from figure_io import savefig

_BNN0414 = _FIG.parents[1]
_DATA    = _BNN0414 / "results" / "data_efficiency" / "data_efficiency_summary.csv"
_OUT_DIR = _BNN0414 / "manuscript" / "0414_v4" / "figures" / "bank"

MODELS = [
    ("bnn-baseline",  "Reference surrogate",          C["ci_zero"], "--"),
    ("bnn-phy-mono",  "Physics-regularized surrogate", C["main"],   "-"),
]


def load():
    return pd.read_csv(_DATA)


def draw(fig=None, ax=None):
    df = load()

    if fig is None:
        fig, ax = plt.subplots(figsize=(FIG_WIDTH_SINGLE, 2.6))

    for mid, label, color, ls in MODELS:
        sub = df[df.model_id == mid].sort_values("n_train_mean")
        x = sub.n_train_mean.values
        y = sub.rmse_mean.values
        ye = sub.rmse_std.values

        ax.plot(x, y, ls, color=color, lw=LW["main"], label=label, zorder=3)
        ax.fill_between(x, y - ye, y + ye, color=color, alpha=A["band"],
                        zorder=1)

    ax.set_xlabel("Training set size")
    ax.set_ylabel("RMSE (stress, MPa)")
    ax.legend(fontsize=FS["legend"], frameon=False, loc="upper right",
              handlelength=1.5, borderpad=0.3)

    finalize_axes(ax)
    return fig, ax


def main():
    set_publication_rc()
    fig, ax = draw()
    panel_label(ax, "(A)")
    written = savefig(fig, "F1_data_efficiency", _OUT_DIR)
    for w in written:
        print("wrote", w)


if __name__ == "__main__":
    main()
