"""H5 — Noise sensitivity: posterior width and acceptance vs observation noise.

Left: normalized CI half-width vs noise fraction (4 parameter lines).
Right: acceptance rate vs noise fraction.
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
_NS_CSV   = (_BNN0414 / "code" / "experiments_0404" / "experiments" /
             "posterior" / "bnn-phy-mono" / "noise_sensitivity" /
             "noise_sensitivity_summary.csv")
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
    df = pd.read_csv(_NS_CSV)
    return df[df.model_id == "bnn-phy-mono"]


def draw(fig=None, axes=None):
    df = load()

    if fig is None:
        fig, axes = plt.subplots(1, 2, figsize=(FIG_WIDTH_DOUBLE, 2.6))
    ax_ci, ax_acc = axes

    for param in PARAMS:
        sub = df[df.param == param].sort_values("noise_frac")
        color = PARAM_COLORS[param]
        marker = PARAM_MARKERS[param]
        label = PARAM_LABELS[param]

        # normalize CI width to value at canonical noise (0.02)
        ref_row = sub[sub.noise_frac == 0.02]
        ref_val = ref_row.mean_ci90_half_width.values[0] if len(ref_row) else 1.0
        normed = sub.mean_ci90_half_width / ref_val

        ax_ci.plot(sub.noise_frac, normed, marker=marker, color=color,
                   markersize=4, lw=1.0, label=label, zorder=2)

    ax_ci.set_xlabel("Observation noise fraction")
    ax_ci.set_ylabel("Normalized CI half-width")
    ax_ci.legend(fontsize=FS["legend"], frameon=False, loc="upper left")
    finalize_axes(ax_ci)

    # acceptance rate (same for all params in a case, take first param)
    acc = df[df.param == PARAMS[0]].sort_values("noise_frac")
    ax_acc.plot(acc.noise_frac, acc.mean_accept_rate, "o-",
                color=C["main"], markersize=4, lw=1.0, zorder=2)
    ax_acc.set_xlabel("Observation noise fraction")
    ax_acc.set_ylabel("Mean acceptance rate")
    finalize_axes(ax_acc)

    return fig, axes


def main():
    set_publication_rc()
    fig, axes = draw()
    panel_label(axes[0], "(A)")
    panel_label(axes[1], "(B)")
    fig.tight_layout()
    written = savefig(fig, "H5_noise_sensitivity", _OUT_DIR)
    for w in written:
        print("wrote", w)


if __name__ == "__main__":
    main()
