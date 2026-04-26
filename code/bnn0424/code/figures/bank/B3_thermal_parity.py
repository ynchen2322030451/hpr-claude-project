"""B3 — Max fuel temperature parity plot.

Same hexbin+linear-fit+PI-band design as B1.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.ndimage import uniform_filter1d

_HERE = Path(__file__).resolve().parent
_FIG  = _HERE.parent
if str(_FIG) not in sys.path:
    sys.path.insert(0, str(_FIG))

from figure_style import (
    set_publication_rc, finalize_axes, panel_label,
    add_metric_text, C, LW, FS, FIG_WIDTH_SINGLE,
)
from figure_io import savefig

_BNN0414   = _FIG.parents[1]
_PRED_JSON = (_BNN0414 / "code" / "models" / "bnn-phy-mono" /
              "fixed_eval" / "test_predictions_fixed.json")
_METR_CSV  = (_BNN0414 / "code" / "models" / "bnn-phy-mono" /
              "fixed_eval" / "metrics_per_output_fixed.csv")
_OUT_DIR   = _BNN0414 / "manuscript" / "0414_v4" / "figures" / "bank"

TEMP_COL = "iteration2_max_fuel_temp"
TEMP_IDX = 9
Z90 = 1.645


def load():
    with open(_PRED_JSON) as f:
        d = json.load(f)
    metr = pd.read_csv(_METR_CSV)
    return (np.array(d["mu"]), np.array(d["sigma"]),
            np.array(d["y_true"]), metr)


def draw(fig=None, ax=None, show_colorbar=True):
    mu, sigma, y_true, metr = load()
    yt = y_true[:, TEMP_IDX]
    yp = mu[:, TEMP_IDX]
    ys = sigma[:, TEMP_IDX]

    row = metr[metr.output == TEMP_COL].iloc[0]
    r2   = row["R2"]
    rmse = row["RMSE"]
    picp = row["PICP"]

    if fig is None:
        fig, ax = plt.subplots(figsize=(FIG_WIDTH_SINGLE, FIG_WIDTH_SINGLE))

    pad = (yt.max() - yt.min()) * 0.08
    lo, hi = yt.min() - pad, yt.max() + pad

    order = np.argsort(yt)
    yt_s = yt[order]
    pi_lo = (yp - Z90 * ys)[order]
    pi_hi = (yp + Z90 * ys)[order]
    w = max(len(yt) // 20, 5)
    pi_lo_sm = uniform_filter1d(pi_lo, w)
    pi_hi_sm = uniform_filter1d(pi_hi, w)
    ax.fill_between(yt_s, pi_lo_sm, pi_hi_sm,
                    alpha=0.22, color=C["pi_band"],
                    label="90% predictive interval", zorder=0)

    hb = ax.hexbin(yt, yp, gridsize=30, cmap="turbo",
                   mincnt=1, linewidths=0, zorder=1)
    if show_colorbar:
        cb = fig.colorbar(hb, ax=ax, shrink=0.72, pad=0.02, aspect=25)
        cb.set_label("Point density", fontsize=FS["tick"])
        cb.ax.tick_params(labelsize=FS["tick"] - 1)

    ax.plot([lo, hi], [lo, hi], "k--", lw=LW["ref"],
            label="y = x", zorder=4)

    slope, intercept = np.polyfit(yt, yp, 1)
    xs = np.linspace(lo, hi, 100)
    ax.plot(xs, slope * xs + intercept, color=C["linear_fit"],
            lw=LW["main"], label="Linear fit", zorder=4)

    ax.set_xlim(lo, hi)
    ax.set_ylim(lo, hi)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("True max fuel temp. (K)")
    ax.set_ylabel("Predicted mean max fuel temp. (K)")

    ax.legend(fontsize=FS["legend"], frameon=False, loc="upper left",
              handlelength=1.5, borderpad=0.4, labelspacing=0.3)

    finalize_axes(ax)

    add_metric_text(ax,
                    f"$R^2$ = {r2:.3f}\n"
                    f"RMSE = {rmse:.2f} K\n"
                    f"PICP$_{{90}}$ = {picp:.1%}",
                    loc="lower right")

    return fig, ax


def main():
    set_publication_rc()
    fig, ax = draw()
    panel_label(ax, "(C)")
    written = savefig(fig, "B3_thermal_parity", _OUT_DIR)
    for w in written:
        print("wrote", w)


if __name__ == "__main__":
    main()
