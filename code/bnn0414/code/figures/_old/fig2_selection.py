"""Figure 2 — Predictive behaviour of the Bayesian neural surrogate.

Three-panel parity plot (stress / keff / coupled max fuel temp) showing
the BNN main model (bnn-phy-mono) on 435 held-out samples.

Phase-1 rulings enforced:
  * Only the main BNN model; no reference variant or multi-model comparison.
  * Per-panel annotation limited to R² / RMSE / PICP90 (3 lines max).
  * MPIW deferred to caption / appendix.
  * Over-coverage (PICP > 0.95) noted as conservative trade-off in caption.
  * No 131 MPa threshold line, no epistemic/aleatoric split.
  * 150 samples carry 90% predictive-interval error bars; remaining 285
    shown as scatter only to avoid visual clutter (random subsample, seed
    fixed for reproducibility).

Output: code/bnn0414/manuscript/0414_v4/figures/fig2_selection.{pdf,svg,png}
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from figure_io import savefig
from figure_style import (
    ALPHAS, COLORS, FONT_SIZES, LINEWIDTHS,
    apply_rc, clean_ax, panel_label,
)

# ── paths ──────────────────────────────────────────────────────────────────
_BNN0414   = _HERE.parents[1]
_MODEL_DIR = _BNN0414 / "code" / "models" / "bnn-phy-mono" / "fixed_eval"
_PRED_JSON = _MODEL_DIR / "test_predictions_fixed.json"
_METR_CSV  = _MODEL_DIR / "metrics_per_output_fixed.csv"
_FIG_DIR   = _BNN0414 / "manuscript" / "0414_v4" / "figures"

# ── target outputs ─────────────────────────────────────────────────────────
TARGETS = [
    {
        "col":   "iteration2_max_global_stress",
        "label": "Coupled steady-state\nmax stress (MPa)",
        "panel": "(A)",
    },
    {
        "col":   "iteration2_keff",
        "label": r"Coupled $k_\mathrm{eff}$",
        "panel": "(B)",
    },
    {
        "col":   "iteration2_max_fuel_temp",
        "label": "Coupled max\nfuel temperature (K)",
        "panel": "(C)",
    },
]

SUBSAMPLE_N   = 150
SUBSAMPLE_SEED = 42
Z90 = 1.645


def _load():
    with open(_PRED_JSON) as f:
        d = json.load(f)
    cols  = d["output_cols"]
    mu    = np.array(d["mu"])
    sigma = np.array(d["sigma"])
    y     = np.array(d["y_true"])
    metr  = pd.read_csv(_METR_CSV)
    return cols, mu, sigma, y, metr


def _annotation(metr: pd.DataFrame, col: str) -> str:
    row = metr[metr.output == col].iloc[0]
    r2   = row["R2"]
    rmse = row["RMSE"]
    picp = row["PICP"]

    if col == "iteration2_keff":
        rmse_str = f"RMSE = {rmse:.2e}"
    elif col == "iteration2_max_fuel_temp":
        rmse_str = f"RMSE = {rmse:.1f} K"
    else:
        rmse_str = f"RMSE = {rmse:.1f} MPa"

    return (
        f"$R^2$ = {r2:.3f}\n"
        f"{rmse_str}\n"
        f"PICP$_{{90}}$ = {picp:.3f}"
    )


def main() -> None:
    apply_rc()
    cols, mu, sigma, y, metr = _load()

    rng = np.random.default_rng(SUBSAMPLE_SEED)
    n = mu.shape[0]
    eb_idx = rng.choice(n, size=SUBSAMPLE_N, replace=False)
    eb_mask = np.zeros(n, dtype=bool)
    eb_mask[eb_idx] = True

    fig, axes = plt.subplots(1, 3, figsize=(7.1, 2.5), constrained_layout=True)

    for ax, tgt in zip(axes, TARGETS):
        idx = cols.index(tgt["col"])
        yt = y[:, idx]
        yp = mu[:, idx]
        ys = sigma[:, idx]

        lo = yt.min(); hi = yt.max(); pad = (hi - lo) * 0.05
        lims = (lo - pad, hi + pad)

        ax.plot(lims, lims, ls="--", lw=LINEWIDTHS["ref"],
                color=COLORS["reference_line"], zorder=1)

        ax.errorbar(
            yt[eb_mask], yp[eb_mask],
            yerr=Z90 * ys[eb_mask],
            fmt="none", ecolor=COLORS["bnn_main"], elinewidth=0.4,
            alpha=ALPHAS["band"], zorder=2, capsize=0,
        )

        ax.scatter(
            yt[~eb_mask], yp[~eb_mask],
            s=6, alpha=0.25, color=COLORS["bnn_main"],
            edgecolors="none", zorder=3,
        )
        ax.scatter(
            yt[eb_mask], yp[eb_mask],
            s=6, alpha=ALPHAS["scatter"], color=COLORS["bnn_main"],
            edgecolors="none", zorder=4,
        )

        ax.set_xlim(lims); ax.set_ylim(lims)
        ax.set_aspect("equal", adjustable="box")
        ax.set_xlabel("True")
        ax.set_ylabel("Predicted")
        ax.set_title(tgt["label"], fontsize=FONT_SIZES["axis"], pad=4)
        clean_ax(ax)
        panel_label(ax, tgt["panel"])

        ann = _annotation(metr, tgt["col"])
        ax.text(
            0.97, 0.03, ann,
            transform=ax.transAxes, fontsize=6,
            ha="right", va="bottom",
            bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#cccccc",
                      alpha=0.85, lw=0.5),
        )

    written = savefig(fig, "fig2_selection", _FIG_DIR)
    for w in written:
        print("wrote", w)


if __name__ == "__main__":
    main()
