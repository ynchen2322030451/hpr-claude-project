"""D2 — First-order Sobol indices for keff (main Fig 4 right).

Same category-colour layout as D1 but for iteration2_keff.
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
    C, LW, FS, FIG_WIDTH_SINGLE,
)
from figure_io import savefig

_BNN0414    = _FIG.parents[1]
_SOBOL_JSON = (_BNN0414 / "code" / "experiments_legacy" / "sensitivity" /
               "bnn-phy-mono" / "sobol_full.json")
_OUT_DIR    = _BNN0414 / "manuscript" / "0414_v4" / "figures" / "bank"

OUTPUT = "iteration2_keff"

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


def load():
    with open(_SOBOL_JSON) as f:
        d = json.load(f)
    inputs = d["inputs"]
    r = d["results"][OUTPUT]["S1"]
    return inputs, np.array(r["mean"]), np.array(r["lo"]), np.array(r["hi"])


def draw(fig=None, ax=None):
    inputs, mean, lo, hi = load()

    order = np.argsort(mean)[::-1]
    mean, lo, hi = mean[order], lo[order], hi[order]
    labels = [PARAM_LABELS.get(inputs[i], inputs[i]) for i in order]
    cats   = [CATEGORY.get(inputs[i], "ci_zero") for i in order]

    spans_zero = (lo <= 0) & (hi >= 0)

    if fig is None:
        fig, ax = plt.subplots(figsize=(FIG_WIDTH_SINGLE, 2.8))

    y = np.arange(len(mean))
    colors = [C["ci_zero"] if sz else C[cat] for sz, cat in zip(spans_zero, cats)]
    err_lo = mean - lo
    err_hi = hi - mean

    ax.barh(y, mean, height=0.55, color=colors, alpha=0.75,
            edgecolor="none", zorder=2)
    ax.errorbar(mean, y, xerr=[err_lo, err_hi],
                fmt="none", ecolor="#555555", elinewidth=0.6,
                capsize=2, capthick=0.6, zorder=3)

    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.set_xlabel("First-order Sobol index $S_1$")
    ax.set_title(r"$k_\mathrm{eff}$ (coupled)", fontsize=FS["title"], pad=4)
    ax.invert_yaxis()
    ax.axvline(0, color="#AAAAAA", lw=0.5, zorder=0)

    # category legend
    patches = [
        mpatches.Patch(color=C["cat_elastic"], label="Elastic / structural"),
        mpatches.Patch(color=C["cat_thermal"], label="Thermal expansion"),
        mpatches.Patch(color=C["cat_conduct"], label="Conductivity"),
    ]
    ax.legend(handles=patches, fontsize=FS["legend"], frameon=False,
              loc="lower right", handlelength=1.2, borderpad=0.3)

    finalize_axes(ax)

    return fig, ax


def main():
    set_publication_rc()
    fig, ax = draw()
    panel_label(ax, "(B)")
    written = savefig(fig, "D2_keff_sobol", _OUT_DIR)
    for w in written:
        print("wrote", w)


if __name__ == "__main__":
    main()
