"""E2 — Posterior 90% CI coverage per parameter (main Fig 5 B).

Dot chart: for each of 4 calibrated parameters, shows which of the
18 benchmark cases have their true value inside the 90% CI.
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
_BM_CSV  = (_BNN0414 / "code" / "experiments" / "posterior" /
            "bnn-phy-mono" / "benchmark_summary.csv")
_OUT_DIR = _BNN0414 / "manuscript" / "0414_v4" / "figures" / "bank"

PARAMS = ["E_intercept", "alpha_base", "alpha_slope", "SS316_k_ref"]
PARAM_LABELS = {
    "E_intercept":  r"$E_\mathrm{int}$",
    "alpha_base":   r"$\alpha_\mathrm{base}$",
    "alpha_slope":  r"$\alpha_\mathrm{slope}$",
    "SS316_k_ref":  r"$k_\mathrm{ref}$",
}


def load():
    return pd.read_csv(_BM_CSV)


def draw(fig=None, ax=None):
    bm = load()

    if fig is None:
        fig, ax = plt.subplots(figsize=(FIG_WIDTH_SINGLE, 2.4))

    for j, param in enumerate(PARAMS):
        sub = bm[bm.param == param].sort_values("case_idx")
        hits = sub["in_90ci"].values.astype(bool)
        n = len(hits)
        xs = np.arange(n)

        hit_mask = hits
        miss_mask = ~hits

        ax.scatter(xs[hit_mask], np.full(hit_mask.sum(), j),
                   s=16, color=C["main"], alpha=0.8,
                   edgecolors="white", linewidths=0.2, zorder=2)
        ax.scatter(xs[miss_mask], np.full(miss_mask.sum(), j),
                   s=16, marker="x", color="#CC4444", alpha=0.8,
                   linewidths=0.8, zorder=2)

        cov = hits.mean()
        ax.text(n + 0.5, j, f"{cov:.0%}", fontsize=FS["metric"],
                va="center", ha="left", color="#505050")

    ax.set_yticks(range(len(PARAMS)))
    ax.set_yticklabels([PARAM_LABELS[p] for p in PARAMS])
    ax.set_xlabel("Benchmark case index")
    ax.set_xlim(-0.5, 18.5)
    ax.set_ylim(-0.5, len(PARAMS) - 0.5)
    ax.invert_yaxis()

    ax.axvline(17.5, color="#DDDDDD", lw=0.4, zorder=0)

    finalize_axes(ax)

    return fig, ax


def main():
    set_publication_rc()
    fig, ax = draw()
    panel_label(ax, "(B)")
    written = savefig(fig, "E2_posterior_coverage", _OUT_DIR)
    for w in written:
        print("wrote", w)


if __name__ == "__main__":
    main()
