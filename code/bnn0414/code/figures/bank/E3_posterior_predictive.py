"""E3 — Posterior predictive vs observed stress (main Fig 5 C).

For each of 18 benchmark cases, shows posterior-predictive stress
(mean + 90% CI) vs true observed stress. Cases sorted by true stress.
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
    add_identity_line, C, A, LW, FS, FIG_WIDTH_SINGLE,
)
from figure_io import savefig

_BNN0414  = _FIG.parents[1]
_FR_CSV   = (_BNN0414 / "code" / "experiments" / "posterior" /
             "bnn-phy-mono" / "feasible_region.csv")
_OUT_DIR  = _BNN0414 / "manuscript" / "0414_v4" / "figures" / "bank"


def load():
    fr = pd.read_csv(_FR_CSV)
    primary = fr[fr.tau_MPa == 131.0].copy()
    primary = primary.sort_values("stress_true_MPa").reset_index(drop=True)
    return primary


def draw(fig=None, ax=None):
    df = load()

    if fig is None:
        fig, ax = plt.subplots(figsize=(FIG_WIDTH_SINGLE, FIG_WIDTH_SINGLE))

    true_s = df["stress_true_MPa"].values
    pred_m = df["stress_post_mean"].values
    pred_lo = df["stress_post_p5"].values
    pred_hi = df["stress_post_p95"].values

    err_lo = pred_m - pred_lo
    err_hi = pred_hi - pred_m

    ax.errorbar(true_s, pred_m,
                yerr=[err_lo, err_hi],
                fmt="none",
                ecolor=C["eb_line"], elinewidth=LW["error"],
                capsize=0, alpha=0.6, zorder=2)

    ax.scatter(true_s, pred_m,
               s=14, alpha=0.90,
               color=C["main"], edgecolors="white",
               linewidths=0.2, zorder=3)

    pad = (true_s.max() - true_s.min()) * 0.12
    lo = min(true_s.min(), pred_lo.min()) - pad
    hi = max(true_s.max(), pred_hi.max()) + pad
    ax.set_xlim(lo, hi)
    ax.set_ylim(lo, hi)

    add_identity_line(ax)
    ax.set_aspect("equal", adjustable="box")

    ax.set_xlabel("Observed stress (MPa)")
    ax.set_ylabel("Posterior-predicted stress (MPa)")

    finalize_axes(ax)

    return fig, ax


def main():
    set_publication_rc()
    fig, ax = draw()
    panel_label(ax, "(C)")
    written = savefig(fig, "E3_posterior_predictive", _OUT_DIR)
    for w in written:
        print("wrote", w)


if __name__ == "__main__":
    main()
