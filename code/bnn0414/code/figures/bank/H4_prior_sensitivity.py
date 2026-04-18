"""H4 — Prior sensitivity heatmap (coverage under 6 prior variants).

Rows = prior variants, columns = 4 calibrated parameters.
Cell color = 90% CI coverage of true value.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

_HERE = Path(__file__).resolve().parent
_FIG  = _HERE.parent
if str(_FIG) not in sys.path:
    sys.path.insert(0, str(_FIG))

from figure_style import (
    set_publication_rc, finalize_axes, panel_label,
    C, FS, FIG_WIDTH_SINGLE,
)
from figure_io import savefig

_BNN0414  = _FIG.parents[1]
_PS_CSV   = (_BNN0414 / "code" / "experiments_0404" / "experiments" /
             "posterior" / "bnn-phy-mono" / "prior_sensitivity" /
             "prior_sensitivity_summary.csv")
_OUT_DIR  = _BNN0414 / "manuscript" / "0414_v4" / "figures" / "bank"

PARAMS = ["E_intercept", "alpha_base", "alpha_slope", "SS316_k_ref"]
PARAM_LABELS = [r"$E_\mathrm{int}$", r"$\alpha_\mathrm{base}$",
                r"$\alpha_\mathrm{slope}$", r"$k_\mathrm{ref}$"]

VARIANT_ORDER = ["canonical", "diffuse", "tight", "flat",
                 "shift_pos", "shift_neg"]
VARIANT_LABELS = ["Canonical", "Diffuse", "Tight", "Flat",
                  "Shift+", "Shift\u2212"]


def load():
    return pd.read_csv(_PS_CSV)


def draw(fig=None, ax=None):
    df = load()
    df = df[df.model_id == "bnn-phy-mono"]

    if fig is None:
        fig, ax = plt.subplots(figsize=(FIG_WIDTH_SINGLE, 2.8))

    # build matrix
    mat = np.full((len(VARIANT_ORDER), len(PARAMS)), np.nan)
    for i, var in enumerate(VARIANT_ORDER):
        for j, param in enumerate(PARAMS):
            row = df[(df.prior_variant == var) & (df.param == param)]
            if len(row):
                mat[i, j] = row.coverage_90ci_true.values[0]

    cmap = mcolors.LinearSegmentedColormap.from_list(
        "cov", ["#CC4444", "#FFDD88", "#44AA66"], N=256)
    im = ax.imshow(mat, cmap=cmap, vmin=0.3, vmax=1.0, aspect="auto")

    # annotate cells
    for i in range(mat.shape[0]):
        for j in range(mat.shape[1]):
            v = mat[i, j]
            if np.isnan(v):
                continue
            color = "white" if v < 0.55 else "#2F2F2F"
            ax.text(j, i, f"{v:.0%}", ha="center", va="center",
                    fontsize=FS["metric"], fontweight="medium", color=color)

    ax.set_xticks(range(len(PARAMS)))
    ax.set_xticklabels(PARAM_LABELS, fontsize=FS["tick"])
    ax.set_yticks(range(len(VARIANT_ORDER)))
    ax.set_yticklabels(VARIANT_LABELS, fontsize=FS["tick"])

    cb = fig.colorbar(im, ax=ax, shrink=0.8, pad=0.03, aspect=20)
    cb.set_label("90% CI coverage", fontsize=FS["tick"])
    cb.ax.tick_params(labelsize=FS["tick"] - 1)

    return fig, ax


def main():
    set_publication_rc()
    fig, ax = draw()
    panel_label(ax, "(A)")
    fig.tight_layout()
    written = savefig(fig, "H4_prior_sensitivity", _OUT_DIR)
    for w in written:
        print("wrote", w)


if __name__ == "__main__":
    main()
