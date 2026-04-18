"""F4 — Epistemic vs aleatoric uncertainty decomposition.

Stacked horizontal bar chart for the physics-regularized BNN,
showing fractional epistemic vs aleatoric variance per output.
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

_BNN0414  = _FIG.parents[1]
_UNC_CSV  = (_BNN0414 / "results" / "uncertainty_decomposition" /
             "uncertainty_decomposition.csv")
_OUT_DIR  = _BNN0414 / "manuscript" / "0414_v4" / "figures" / "bank"

OUTPUT_ORDER = [
    "iteration2_keff",
    "iteration2_max_fuel_temp",
    "iteration2_max_monolith_temp",
    "iteration2_max_global_stress",
    "iteration2_wall2",
]

OUTPUT_LABELS = {
    "iteration2_keff":              r"$k_\mathrm{eff}$",
    "iteration2_max_fuel_temp":     "Max fuel temp",
    "iteration2_max_monolith_temp": "Max monolith temp",
    "iteration2_max_global_stress": "Max stress",
    "iteration2_wall2":             "Wall temp",
}


def load():
    df = pd.read_csv(_UNC_CSV)
    return df[df.model_id == "bnn-phy-mono"].copy()


def draw(fig=None, ax=None):
    df = load()

    # reorder
    df = df.set_index("output").loc[OUTPUT_ORDER].reset_index()

    if fig is None:
        fig, ax = plt.subplots(figsize=(FIG_WIDTH_SINGLE, 2.6))

    labels = [OUTPUT_LABELS.get(o, o) for o in df.output]
    frac_epi = df.frac_epistemic_mean.values
    frac_ale = 1.0 - frac_epi

    y = np.arange(len(labels))

    ax.barh(y, frac_epi, height=0.55, color=C["main"], alpha=0.8,
            edgecolor="none", label="Epistemic", zorder=2)
    ax.barh(y, frac_ale, height=0.55, left=frac_epi, color=C["ci_zero"],
            alpha=0.6, edgecolor="none", label="Aleatoric", zorder=2)

    # annotate percentages
    for i in range(len(y)):
        if frac_epi[i] > 0.08:
            ax.text(frac_epi[i] / 2, y[i], f"{frac_epi[i]:.0%}",
                    ha="center", va="center", fontsize=FS["metric"],
                    color="white", fontweight="medium")

    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.set_xlabel("Variance fraction")
    ax.set_xlim(0, 1)
    ax.invert_yaxis()

    ax.legend(fontsize=FS["legend"], frameon=False, loc="lower right",
              handlelength=1.2, borderpad=0.3)

    finalize_axes(ax)
    return fig, ax


def main():
    set_publication_rc()
    fig, ax = draw()
    panel_label(ax, "(A)")
    written = savefig(fig, "F4_uncertainty_decomp", _OUT_DIR)
    for w in written:
        print("wrote", w)


if __name__ == "__main__":
    main()
