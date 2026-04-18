"""D3 — First-order vs total Sobol indices (S1 solid + ST hatched).

Two subplots: stress (left) and keff (right).  Category-coloured bars
with the same palette as D1/D2.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

_HERE = Path(__file__).resolve().parent
_FIG  = _HERE.parent
if str(_FIG) not in sys.path:
    sys.path.insert(0, str(_FIG))

from figure_style import (
    set_publication_rc, finalize_axes, panel_label,
    C, LW, FS, FIG_WIDTH_DOUBLE,
)
from figure_io import savefig

_BNN0414    = _FIG.parents[1]
_SOBOL_JSON = (_BNN0414 / "code" / "experiments" / "sensitivity" /
               "bnn-phy-mono" / "sobol_full.json")
_OUT_DIR    = _BNN0414 / "manuscript" / "0414_v4" / "figures" / "bank"

OUTPUTS = [
    ("iteration2_max_global_stress", "Coupled steady-state max stress"),
    ("iteration2_keff",              r"$k_\mathrm{eff}$ (coupled)"),
]

PARAM_LABELS = {
    "E_slope": r"$E_\mathrm{slope}$",
    "E_intercept": r"$E_\mathrm{intercept}$",
    "nu": r"$\nu$",
    "alpha_base": r"$\alpha_\mathrm{base}$",
    "alpha_slope": r"$\alpha_\mathrm{slope}$",
    "SS316_T_ref": r"$T_\mathrm{ref}$",
    "SS316_k_ref": r"$k_\mathrm{ref}$",
    "SS316_alpha": r"$\alpha_\mathrm{SS316}$",
}

CATEGORY = {
    "E_slope":     "cat_elastic",
    "E_intercept": "cat_elastic",
    "nu":          "cat_elastic",
    "alpha_base":  "cat_thermal",
    "alpha_slope": "cat_thermal",
    "SS316_T_ref": "cat_conduct",
    "SS316_k_ref": "cat_conduct",
    "SS316_alpha": "cat_conduct",
}

BAR_H = 0.35


def load():
    with open(_SOBOL_JSON) as f:
        return json.load(f)


def _draw_panel(ax, data, output_key, title):
    inputs = data["inputs"]
    s1 = data["results"][output_key]["S1"]
    st = data["results"][output_key]["ST"]

    s1_mean = np.array(s1["mean"])
    s1_lo   = np.array(s1["lo"])
    s1_hi   = np.array(s1["hi"])
    st_mean = np.array(st["mean"])
    st_lo   = np.array(st["lo"])
    st_hi   = np.array(st["hi"])

    # sort by S1 descending
    order = np.argsort(s1_mean)[::-1]
    s1_mean = s1_mean[order]
    s1_lo, s1_hi = s1_lo[order], s1_hi[order]
    st_mean = st_mean[order]
    st_lo, st_hi = st_lo[order], st_hi[order]
    labels = [PARAM_LABELS.get(inputs[i], inputs[i]) for i in order]
    cats   = [CATEGORY.get(inputs[i], "ci_zero") for i in order]

    s1_spans_zero = (s1_lo <= 0) & (s1_hi >= 0)
    st_spans_zero = (st_lo <= 0) & (st_hi >= 0)

    n = len(s1_mean)
    y = np.arange(n)

    # S1 bars (upper position)
    s1_colors = [C["ci_zero"] if sz else C[cat]
                 for sz, cat in zip(s1_spans_zero, cats)]
    ax.barh(y + BAR_H / 2, s1_mean, height=BAR_H, color=s1_colors,
            alpha=0.75, edgecolor="none", zorder=2, label="$S_1$")
    ax.errorbar(s1_mean, y + BAR_H / 2,
                xerr=[s1_mean - s1_lo, s1_hi - s1_mean],
                fmt="none", ecolor="#555555", elinewidth=0.5,
                capsize=1.5, capthick=0.5, zorder=3)

    # ST bars (lower position, hatched)
    st_colors = [C["ci_zero"] if sz else C[cat]
                 for sz, cat in zip(st_spans_zero, cats)]
    ax.barh(y - BAR_H / 2, st_mean, height=BAR_H, color=st_colors,
            alpha=0.45, edgecolor="#555555", linewidth=0.3,
            hatch="///", zorder=2, label="$S_T$")
    ax.errorbar(st_mean, y - BAR_H / 2,
                xerr=[st_mean - st_lo, st_hi - st_mean],
                fmt="none", ecolor="#555555", elinewidth=0.5,
                capsize=1.5, capthick=0.5, zorder=3)

    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.set_xlabel("Sobol index")
    ax.set_title(title, fontsize=FS["title"], pad=4)
    ax.invert_yaxis()
    ax.axvline(0, color="#AAAAAA", lw=0.5, zorder=0)

    finalize_axes(ax)


def draw(fig=None, axes=None):
    data = load()
    if fig is None:
        fig, axes = plt.subplots(1, 2, figsize=(FIG_WIDTH_DOUBLE, 3.0))

    for ax, (okey, title) in zip(axes, OUTPUTS):
        _draw_panel(ax, data, okey, title)

    # shared legend: categories + S1/ST
    cat_patches = [
        mpatches.Patch(color=C["cat_elastic"], label="Elastic / structural"),
        mpatches.Patch(color=C["cat_thermal"], label="Thermal expansion"),
        mpatches.Patch(color=C["cat_conduct"], label="Conductivity"),
    ]
    s1_patch = mpatches.Patch(facecolor="#888888", alpha=0.75,
                              edgecolor="none", label="$S_1$ (first-order)")
    st_patch = mpatches.Patch(facecolor="#888888", alpha=0.45,
                              edgecolor="#555555", linewidth=0.3,
                              hatch="///", label="$S_T$ (total)")
    fig.legend(handles=cat_patches + [s1_patch, st_patch],
               fontsize=FS["legend"], frameon=False, ncol=3,
               loc="lower center", bbox_to_anchor=(0.5, -0.05),
               columnspacing=1.5, handletextpad=0.5)

    try:
        fig.tight_layout(rect=[0, 0.06, 1, 1])
    except Exception:
        pass  # skip when used inside external GridSpec
    return fig, axes


def main():
    set_publication_rc()
    fig, axes = draw()
    panel_label(axes[0], "(A)")
    panel_label(axes[1], "(B)")
    written = savefig(fig, "D3_sobol_total", _OUT_DIR)
    for w in written:
        print("wrote", w)


if __name__ == "__main__":
    main()
