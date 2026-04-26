"""F2 — OOD epistemic uncertainty ratio by shifted feature.

Grouped bars showing how epistemic uncertainty grows under distribution
shift for the physics-regularized BNN, with a reference line at 1.0.
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

_BNN0414 = _FIG.parents[1]
_OOD_CSV = _BNN0414 / "results" / "ood" / "ood_calibration_comparison.csv"
_OUT_DIR = _BNN0414 / "manuscript" / "0414_v4" / "figures" / "bank"

FEATURE_LABELS = {
    "E_intercept": r"$E_\mathrm{intercept}$",
    "alpha_base":  r"$\alpha_\mathrm{base}$",
    "nu":          r"$\nu$",
    "alpha_slope": r"$\alpha_\mathrm{slope}$",
}


def load():
    df = pd.read_csv(_OOD_CSV)
    return df[df.model_id == "bnn-phy-mono"].copy()


def draw(fig=None, ax=None):
    df = load()

    if fig is None:
        fig, ax = plt.subplots(figsize=(FIG_WIDTH_SINGLE, 2.6))

    features = df.ood_feature.values
    labels = [FEATURE_LABELS.get(f, f) for f in features]
    ratios = df.epistemic_ratio.values

    y = np.arange(len(features))
    colors = [C["main"] if r > 1.0 else C["ci_zero"] for r in ratios]

    ax.barh(y, ratios, height=0.55, color=colors, alpha=0.75,
            edgecolor="none", zorder=2)
    ax.axvline(1.0, color=C["refline"], lw=LW["ref"], ls="--", zorder=1,
               label="In-distribution baseline")

    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.set_xlabel("Epistemic uncertainty ratio (OOD / in-distribution)")
    ax.invert_yaxis()

    ax.legend(fontsize=FS["legend"], frameon=False, loc="lower right",
              handlelength=1.5, borderpad=0.3)

    finalize_axes(ax)
    return fig, ax


def main():
    set_publication_rc()
    fig, ax = draw()
    panel_label(ax, "(A)")
    written = savefig(fig, "F2_ood_epistemic", _OUT_DIR)
    for w in written:
        print("wrote", w)


if __name__ == "__main__":
    main()
