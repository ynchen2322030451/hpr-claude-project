"""H3 — MCMC diagnostics scatter: Rhat and ESS across 18 cases.

Left: split-rank Rhat per case per parameter.
Right: total ESS per case per parameter.
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

_BNN0414  = _FIG.parents[1]
_DIAG_CSV = (_BNN0414 / "code" / "experiments_0404" / "experiments" /
             "posterior" / "bnn-phy-mono" / "diagnostics" /
             "mcmc_diagnostics.csv")
_OUT_DIR  = _BNN0414 / "manuscript" / "0414_v4" / "figures" / "bank"

PARAMS = ["E_intercept", "alpha_base", "alpha_slope", "SS316_k_ref"]
PARAM_LABELS = {
    "E_intercept":  r"$E_\mathrm{int}$",
    "alpha_base":   r"$\alpha_\mathrm{base}$",
    "alpha_slope":  r"$\alpha_\mathrm{slope}$",
    "SS316_k_ref":  r"$k_\mathrm{ref}$",
}
PARAM_COLORS = {
    "E_intercept":  C["cat_elastic"],
    "alpha_base":   C["cat_thermal"],
    "alpha_slope":  C["cat_thermal"],
    "SS316_k_ref":  C["cat_conduct"],
}
PARAM_MARKERS = {
    "E_intercept": "o",
    "alpha_base":  "s",
    "alpha_slope": "^",
    "SS316_k_ref": "D",
}


def load():
    return pd.read_csv(_DIAG_CSV)


def draw(fig=None, axes=None):
    df = load()

    if fig is None:
        fig, axes = plt.subplots(1, 2, figsize=(FIG_WIDTH_DOUBLE, 2.6))
    ax_rhat, ax_ess = axes

    for param in PARAMS:
        sub = df[df.param == param].sort_values("case_idx")
        color = PARAM_COLORS[param]
        marker = PARAM_MARKERS[param]
        label = PARAM_LABELS[param]

        ax_rhat.scatter(sub.case_idx, sub.rhat_split_rank,
                        s=14, color=color, marker=marker,
                        alpha=0.8, edgecolors="white", linewidths=0.2,
                        label=label, zorder=2)
        ax_ess.scatter(sub.case_idx, sub.ESS_total,
                       s=14, color=color, marker=marker,
                       alpha=0.8, edgecolors="white", linewidths=0.2,
                       zorder=2)

    # threshold lines
    ax_rhat.axhline(1.01, color="#CC4444", ls="--", lw=0.6, alpha=0.7,
                    zorder=1)
    ax_rhat.set_ylabel(r"$\hat{R}$ (split-rank)")
    ax_rhat.set_xlabel("Case index")

    ax_ess.axhline(100, color="#CC4444", ls="--", lw=0.6, alpha=0.7,
                   zorder=1)
    ax_ess.set_ylabel("ESS (total)")
    ax_ess.set_xlabel("Case index")

    ax_rhat.legend(fontsize=FS["legend"], frameon=False, ncol=2,
                   loc="upper right")

    finalize_axes(ax_rhat)
    finalize_axes(ax_ess)
    return fig, axes


def main():
    set_publication_rc()
    fig, axes = draw()
    panel_label(axes[0], "(A)")
    panel_label(axes[1], "(B)")
    fig.tight_layout()
    written = savefig(fig, "H3_mcmc_diagnostics", _OUT_DIR)
    for w in written:
        print("wrote", w)


if __name__ == "__main__":
    main()
