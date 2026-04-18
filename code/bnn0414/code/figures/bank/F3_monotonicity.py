"""F3 — Physics-consistency heatmaps (monotonicity violation rate).

Side-by-side heatmaps for Reference surrogate (left) vs
Physics-regularized surrogate (right). Primary outputs only.
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
    C, LW, FS, FIG_WIDTH_DOUBLE,
)
from figure_io import savefig

_BNN0414  = _FIG.parents[1]
_MONO_CSV = _BNN0414 / "results" / "physics_consistency" / "monotonicity_violation_rate.csv"
_OUT_DIR  = _BNN0414 / "manuscript" / "0414_v4" / "figures" / "bank"

OUTPUT_LABELS = {
    "iteration2_max_global_stress": "Max stress",
    "iteration2_max_fuel_temp":     "Max fuel temp",
    "iteration2_max_monolith_temp": "Max monolith temp",
    "iteration2_keff":              r"$k_\mathrm{eff}$",
}

INPUT_LABELS = {
    "E_intercept": r"$E_\mathrm{intercept}$",
    "E_slope":     r"$E_\mathrm{slope}$",
    "alpha_base":  r"$\alpha_\mathrm{base}$",
    "alpha_slope": r"$\alpha_\mathrm{slope}$",
    "SS316_k_ref": r"$k_\mathrm{ref}$",
    "SS316_alpha": r"$\alpha_\mathrm{SS316}$",
}

PANELS = [
    ("bnn-baseline",  "Reference surrogate"),
    ("bnn-phy-mono",  "Physics-regularized surrogate"),
]


def load():
    df = pd.read_csv(_MONO_CSV)
    return df[df.is_primary_output == True].copy()


def _build_matrix(df, model_id, input_names, output_names):
    sub = df[df.model_id == model_id]
    mat = np.full((len(input_names), len(output_names)), np.nan)
    for i, inp in enumerate(input_names):
        for j, out in enumerate(output_names):
            row = sub[(sub["input"] == inp) & (sub.output == out)]
            if len(row):
                mat[i, j] = row.violation_rate.values[0]
    return mat


def draw(fig=None, axes=None):
    df = load()
    input_names  = sorted(df["input"].unique(),
                          key=lambda x: list(INPUT_LABELS.keys()).index(x)
                          if x in INPUT_LABELS else 99)
    output_names = sorted(df.output.unique(),
                          key=lambda x: list(OUTPUT_LABELS.keys()).index(x)
                          if x in OUTPUT_LABELS else 99)

    if fig is None:
        fig, axes = plt.subplots(1, 2, figsize=(FIG_WIDTH_DOUBLE, 3.0))

    cmap = plt.cm.RdYlGn_r  # red = high violation
    norm = mcolors.Normalize(vmin=0, vmax=0.5)

    for ax, (mid, title) in zip(axes, PANELS):
        mat = _build_matrix(df, mid, input_names, output_names)
        im = ax.imshow(mat, cmap=cmap, norm=norm, aspect="auto")

        # annotate cells
        for i in range(mat.shape[0]):
            for j in range(mat.shape[1]):
                v = mat[i, j]
                if np.isnan(v):
                    continue
                txt = f"{v:.2f}" if v > 0 else "0"
                color = "white" if v > 0.25 else "black"
                ax.text(j, i, txt, ha="center", va="center",
                        fontsize=FS["metric"], color=color)

        ax.set_xticks(np.arange(len(output_names)))
        ax.set_xticklabels([OUTPUT_LABELS.get(o, o) for o in output_names],
                           rotation=35, ha="right", fontsize=FS["tick"])
        ax.set_yticks(np.arange(len(input_names)))
        ax.set_yticklabels([INPUT_LABELS.get(n, n) for n in input_names],
                           fontsize=FS["tick"])
        ax.set_title(title, fontsize=FS["title"], pad=4)

    # shared colorbar
    fig.subplots_adjust(right=0.88, wspace=0.35)
    cbar_ax = fig.add_axes([0.90, 0.18, 0.015, 0.65])
    cb = fig.colorbar(im, cax=cbar_ax)
    cb.set_label("Violation rate", fontsize=FS["tick"])
    cb.ax.tick_params(labelsize=FS["tick"] - 1)

    return fig, axes


def main():
    set_publication_rc()
    fig, axes = draw()
    panel_label(axes[0], "(A)")
    panel_label(axes[1], "(B)")
    written = savefig(fig, "F3_monotonicity", _OUT_DIR)
    for w in written:
        print("wrote", w)


if __name__ == "__main__":
    main()
