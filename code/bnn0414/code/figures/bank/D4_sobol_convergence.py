"""D4 — Sobol S1 convergence with sample size.

Two subplots: stress (left) and keff (right). Top-3 inputs with CI bands.
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

_BNN0414    = _FIG.parents[1]
_CONV_CSV   = _BNN0414 / "results" / "sensitivity" / "sobol_convergence.csv"
_OUT_DIR    = _BNN0414 / "manuscript" / "0414_v4" / "figures" / "bank"

OUTPUTS = [
    ("iteration2_max_global_stress", "Coupled steady-state max stress"),
    ("iteration2_keff",              r"$k_\mathrm{eff}$ (coupled)"),
]

PARAM_LABELS = {
    "E_slope":     r"$E_\mathrm{slope}$",
    "E_intercept": r"$E_\mathrm{intercept}$",
    "nu":          r"$\nu$",
    "alpha_base":  r"$\alpha_\mathrm{base}$",
    "alpha_slope": r"$\alpha_\mathrm{slope}$",
    "SS316_T_ref": r"$T_\mathrm{ref}$",
    "SS316_k_ref": r"$k_\mathrm{ref}$",
    "SS316_alpha": r"$\alpha_\mathrm{SS316}$",
}

CATEGORY_COLORS = {
    "E_slope": C["cat_elastic"], "E_intercept": C["cat_elastic"],
    "nu": C["cat_elastic"],
    "alpha_base": C["cat_thermal"], "alpha_slope": C["cat_thermal"],
    "SS316_T_ref": C["cat_conduct"], "SS316_k_ref": C["cat_conduct"],
    "SS316_alpha": C["cat_conduct"],
}


def load():
    df = pd.read_csv(_CONV_CSV)
    return df[df.model_id == "bnn-phy-mono"]


def draw(fig=None, axes=None):
    df = load()

    if fig is None:
        fig, axes = plt.subplots(1, 2, figsize=(FIG_WIDTH_DOUBLE, 2.8))

    for ax, (out_key, title) in zip(axes, OUTPUTS):
        sub = df[df.output == out_key]
        # find top-3 inputs by final S1
        max_n = sub.N_base.max()
        final = sub[sub.N_base == max_n].sort_values("S1_mean",
                                                      ascending=False)
        top3 = final.head(3)["input"].values

        for inp in top3:
            s = sub[sub.input == inp].sort_values("N_base")
            color = CATEGORY_COLORS.get(inp, "#888888")
            label = PARAM_LABELS.get(inp, inp)
            ax.plot(s.N_base, s.S1_mean, "o-", color=color,
                    markersize=3, lw=1.0, label=label, zorder=2)
            ax.fill_between(s.N_base, s.S1_ci_lo, s.S1_ci_hi,
                            color=color, alpha=0.15, zorder=1)

        ax.set_xscale("log", base=2)
        ax.set_xlabel(r"$N_\mathrm{base}$")
        ax.set_title(title, fontsize=FS["title"], pad=4)
        ax.legend(fontsize=FS["legend"], frameon=False, loc="upper left")
        finalize_axes(ax)

    axes[0].set_ylabel(r"$S_1$")
    return fig, axes


def main():
    set_publication_rc()
    fig, axes = draw()
    panel_label(axes[0], "(A)")
    panel_label(axes[1], "(B)")
    fig.tight_layout()
    written = savefig(fig, "D4_sobol_convergence", _OUT_DIR)
    for w in written:
        print("wrote", w)


if __name__ == "__main__":
    main()
