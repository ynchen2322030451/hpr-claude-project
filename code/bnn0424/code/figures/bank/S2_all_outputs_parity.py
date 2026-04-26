"""S2 — Parity plots for all 15 BNN outputs (SI Fig. S2).

5x3 grid. Top two rows: 8 coupled (iter2) outputs.
Bottom ~2.3 rows: 7 single-pass (iter1) outputs.
Each panel: scatter, y=x reference, R^2 + RMSE annotation.
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
    add_metric_text, C, LW, FS, FIG_WIDTH_DOUBLE, SCATTER,
)
from figure_io import savefig

_BNN0424   = _FIG.parents[1]
_PRED_JSON = (_BNN0424 / "code" / "models" / "bnn-phy-mono" /
              "fixed_eval" / "test_predictions_fixed.json")
_METR_CSV  = (_BNN0424 / "code" / "models" / "bnn-phy-mono" /
              "fixed_eval" / "metrics_per_output_fixed.csv")
_OUT_DIR   = _BNN0424 / "manuscript" / "0414_v4" / "figures" / "bank"

Z90 = 1.645

PANELS = [
    # (col_index, short_label, unit)
    # --- Row 0: coupled primary ---
    (11, "Coupled peak stress",       "MPa"),
    (7,  r"Coupled $k_\mathrm{eff}$", ""),
    (14, "Coupled wall thickness",    "cm"),
    # --- Row 1: coupled thermal ---
    (9,  "Coupled max fuel temp",     "K"),
    (10, "Coupled max monolith temp", "K"),
    (8,  "Coupled avg fuel temp",     "K"),
    # --- Row 2: coupled other ---
    (12, "Coupled monolith temp",     "K"),
    (13, r"Coupled $H_\mathrm{core}$","cm"),
    # --- Row 3-4: single-pass ---
    (3,  "Single-pass peak stress",       "MPa"),
    (1,  "Single-pass max fuel temp",     "K"),
    (2,  "Single-pass max monolith temp", "K"),
    (0,  "Single-pass avg fuel temp",     "K"),
    (4,  "Single-pass monolith temp",     "K"),
    (5,  r"Single-pass $H_\mathrm{core}$","cm"),
    (6,  "Single-pass wall thickness",    "cm"),
]

assert len(PANELS) == 15


def load():
    with open(_PRED_JSON) as f:
        d = json.load(f)
    metr = pd.read_csv(_METR_CSV)
    cols = d["output_cols"]
    return (np.array(d["mu"]), np.array(d["sigma"]),
            np.array(d["y_true"]), metr, cols)


def draw():
    mu, sigma, y_true, metr, cols = load()
    nrows, ncols = 5, 3

    set_publication_rc()
    fig, axes = plt.subplots(nrows, ncols,
                             figsize=(FIG_WIDTH_DOUBLE, FIG_WIDTH_DOUBLE * 1.35),
                             constrained_layout=True)
    axes_flat = axes.ravel()

    for i, (cidx, label, unit) in enumerate(PANELS):
        ax = axes_flat[i]
        col_name = cols[cidx]

        yt = y_true[:, cidx]
        yp = mu[:, cidx]

        row = metr[metr.output == col_name].iloc[0]
        r2   = row["R2"]
        rmse = row["RMSE"]

        pad = (yt.max() - yt.min()) * 0.08
        lo, hi = yt.min() - pad, yt.max() + pad

        ax.scatter(yt, yp, s=SCATTER["s"] * 0.6, alpha=0.45,
                   color=C["main"], edgecolors="none", zorder=1, rasterized=True)

        ax.plot([lo, hi], [lo, hi], "k--", lw=LW["ref"], zorder=3)

        ax.set_xlim(lo, hi)
        ax.set_ylim(lo, hi)
        ax.set_aspect("equal", adjustable="box")

        unit_str = f" ({unit})" if unit else ""
        ax.set_title(label, fontsize=FS["legend"] + 0.5, pad=3)

        if i % ncols == 0:
            ax.set_ylabel(f"Predicted{unit_str}", fontsize=FS["tick"])
        if i >= (nrows - 1) * ncols:
            ax.set_xlabel(f"True{unit_str}", fontsize=FS["tick"])

        add_metric_text(ax,
                        f"$R^2$={r2:.3f}\nRMSE={rmse:.2g}",
                        loc="upper left")

        panel_label(ax, f"({chr(97 + i)})", x=-0.08, y=1.04)
        finalize_axes(ax)

    return fig


def main():
    fig = draw()
    written = savefig(fig, "S2_all_outputs_parity", _OUT_DIR)
    for w in written:
        print("wrote", w)


if __name__ == "__main__":
    main()
