"""C1 — Coupled vs uncoupled stress distribution (main Fig 3 dominant).

Shows how thermo-mechanical coupling compresses the stress distribution.
Two overlaid KDE densities: uncoupled (iter1) vs coupled (iter2).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import gaussian_kde

_HERE = Path(__file__).resolve().parent
_FIG  = _HERE.parent
if str(_FIG) not in sys.path:
    sys.path.insert(0, str(_FIG))

from figure_style import (
    set_publication_rc, finalize_axes, panel_label,
    add_metric_text, C, A, LW, FS, FIG_WIDTH_SINGLE,
)
from figure_io import savefig

_BNN0414   = _FIG.parents[1]
_PRED_JSON = (_BNN0414 / "code" / "models" / "bnn-phy-mono" /
              "fixed_eval" / "test_predictions_fixed.json")
_OUT_DIR   = _BNN0414 / "manuscript" / "0414_v4" / "figures" / "bank"

STRESS_ITER1_IDX = 3
STRESS_ITER2_IDX = 11


def load():
    with open(_PRED_JSON) as f:
        d = json.load(f)
    return np.array(d["y_true"])


def draw(fig=None, ax=None):
    yt = load()
    s1 = yt[:, STRESS_ITER1_IDX]
    s2 = yt[:, STRESS_ITER2_IDX]

    if fig is None:
        fig, ax = plt.subplots(figsize=(FIG_WIDTH_SINGLE, 2.6))

    xmin = min(s1.min(), s2.min()) - 10
    xmax = max(s1.max(), s2.max()) + 10
    xs = np.linspace(xmin, xmax, 400)

    kde1 = gaussian_kde(s1, bw_method=0.25)
    kde2 = gaussian_kde(s2, bw_method=0.25)

    ax.fill_between(xs, kde1(xs), alpha=0.20, color=C["uncoupled"], zorder=1)
    ax.plot(xs, kde1(xs), color=C["uncoupled"], lw=LW["main"],
            label="Uncoupled pass", zorder=2)

    ax.fill_between(xs, kde2(xs), alpha=0.25, color=C["main"], zorder=3)
    ax.plot(xs, kde2(xs), color=C["main"], lw=LW["main"],
            label="Coupled steady state", zorder=4)

    ax.set_xlabel("Max stress (MPa)")
    ax.set_ylabel("Density")
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(bottom=0)

    ax.legend(fontsize=FS["legend"], frameon=False, loc="upper right")

    finalize_axes(ax)

    delta_mu = s2.mean() - s1.mean()
    add_metric_text(ax,
                    f"$\\Delta\\mu$ = {delta_mu:.1f} MPa",
                    loc="upper left")

    return fig, ax


def main():
    set_publication_rc()
    fig, ax = draw()
    panel_label(ax, "(A)")
    written = savefig(fig, "C1_stress_coupling", _OUT_DIR)
    for w in written:
        print("wrote", w)


if __name__ == "__main__":
    main()
