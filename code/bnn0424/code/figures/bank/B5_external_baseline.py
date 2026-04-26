"""B5 — BNN vs MC-Dropout vs Deep Ensemble (dual: R² left, RMSE right).

Left panel: R² comparison (all outputs on same 0–1 scale).
Right panel: RMSE comparison (log scale to handle 4-OOM range).
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

_BNN0414      = _FIG.parents[1]
_EXT_CSV      = _BNN0414 / "results" / "accuracy" / "external_baseline_scoring.csv"
_BNN_CSV      = _BNN0414 / "results" / "accuracy" / "repeat_eval_per_output_summary.csv"
_OUT_DIR      = _BNN0414 / "manuscript" / "0414_v4" / "figures" / "bank"

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

MODELS = [
    ("bnn-phy-mono",   "Physics-reg. BNN", C["baseline"]),
    ("mc-dropout",     "MC-Dropout",        C["mc_dropout"]),
    ("deep-ensemble",  "Deep Ensemble",     C["deep_ensemble"]),
]

BAR_H  = 0.22


def load():
    ext = pd.read_csv(_EXT_CSV)
    bnn = pd.read_csv(_BNN_CSV)
    bnn_phy = bnn[(bnn.model_id == "bnn-phy-mono") & (bnn.is_primary == True)]

    rows = []
    for _, r in bnn_phy.iterrows():
        if r.output in PRIMARY_OUTPUTS:
            rows.append({
                "model_id": "bnn-phy-mono",
                "output": r.output,
                "RMSE": r.RMSE_mean,
                "R2": r.R2_mean,
            })
    bnn_df = pd.DataFrame(rows)

    ext_sub = ext[ext.output.isin(PRIMARY_OUTPUTS)][["model_id", "output", "RMSE", "R2"]]
    combined = pd.concat([bnn_df, ext_sub], ignore_index=True)
    return combined


def draw(fig=None, axes=None):
    df = load()

    if fig is None:
        fig, axes = plt.subplots(1, 2, figsize=(FIG_WIDTH_DOUBLE, 3.0))
    ax_r2, ax_rmse = axes

    n_out = len(PRIMARY_OUTPUTS)
    n_mod = len(MODELS)
    y_base = np.arange(n_out)

    for j, (mid, mlabel, color) in enumerate(MODELS):
        offset = (j - (n_mod - 1) / 2) * BAR_H
        r2_vals, rmse_vals = [], []
        for out in PRIMARY_OUTPUTS:
            row = df[(df.model_id == mid) & (df.output == out)]
            r2_vals.append(row.R2.values[0] if len(row) else 0.0)
            rmse_vals.append(row.RMSE.values[0] if len(row) else 0.0)

        ax_r2.barh(y_base + offset, r2_vals, height=BAR_H * 0.9,
                   color=color, alpha=0.8, edgecolor="none",
                   label=mlabel, zorder=2)
        ax_rmse.barh(y_base + offset, rmse_vals, height=BAR_H * 0.9,
                     color=color, alpha=0.8, edgecolor="none",
                     zorder=2)

    ylabels = [OUTPUT_LABELS[o] for o in PRIMARY_OUTPUTS]

    ax_r2.set_yticks(y_base)
    ax_r2.set_yticklabels(ylabels)
    ax_r2.set_xlabel(r"$R^2$ (test set)")
    ax_r2.set_xlim(0.4, 1.02)
    ax_r2.invert_yaxis()

    ax_rmse.set_yticks(y_base)
    ax_rmse.set_yticklabels([])
    ax_rmse.set_xlabel("RMSE (test set)")
    ax_rmse.set_xscale("log")
    ax_rmse.invert_yaxis()

    ax_r2.legend(fontsize=FS["legend"], frameon=False, loc="lower left",
                 handlelength=1.2, borderpad=0.3)

    finalize_axes(ax_r2)
    finalize_axes(ax_rmse)
    return fig, axes


def main():
    set_publication_rc()
    fig, axes = draw()
    panel_label(axes[0], "(A)")
    panel_label(axes[1], "(B)")
    written = savefig(fig, "B5_external_baseline", _OUT_DIR)
    for w in written:
        print("wrote", w)


if __name__ == "__main__":
    main()
