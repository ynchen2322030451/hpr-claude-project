"""E1 — Prior vs posterior marginal densities (main Fig 5 A).

Shows contraction from uniform prior to Gaussian-approximated posterior
for each of the 4 calibrated parameters, aggregated across 18 benchmark
cases (median posterior shown, with band spanning case-to-case variation).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import norm

_HERE = Path(__file__).resolve().parent
_FIG  = _HERE.parent
if str(_FIG) not in sys.path:
    sys.path.insert(0, str(_FIG))

from figure_style import (
    set_publication_rc, finalize_axes, panel_label,
    C, A, LW, FS, FIG_WIDTH_DOUBLE,
)
from figure_io import savefig

_BNN0414  = _FIG.parents[1]
# Prefer 4-chain rerun results; fall back to legacy single-chain
_BM_CSV_4CHAIN = (_BNN0414 / "code" / "experiments" / "posterior" /
                  "bnn-phy-mono" / "rerun_4chain" / "benchmark_summary.csv")
_BM_CSV_LEGACY = (_BNN0414 / "code" / "experiments_legacy" / "posterior" /
                  "bnn-phy-mono" / "benchmark_summary.csv")
_BM_CSV   = _BM_CSV_4CHAIN if _BM_CSV_4CHAIN.exists() else _BM_CSV_LEGACY
_OUT_DIR  = _BNN0414 / "manuscript" / "0414_v4" / "figures" / "bank"

PRIOR_RANGES = {
    "E_intercept":  (1.387e11, 2.592e11),
    "alpha_base":   (6.52e-6, 1.34e-5),
    "alpha_slope":  (3.44e-9, 6.52e-9),
    "SS316_k_ref":  (15.7, 29.9),
}

PARAM_LABELS = {
    "E_intercept":  r"$E_\mathrm{intercept}$ (Pa)",
    "alpha_base":   r"$\alpha_\mathrm{base}$ (K$^{-1}$)",
    "alpha_slope":  r"$\alpha_\mathrm{slope}$ (K$^{-2}$)",
    "SS316_k_ref":  r"$k_\mathrm{ref}$ (W/m$\cdot$K)",
}

PARAMS = ["E_intercept", "alpha_base", "alpha_slope", "SS316_k_ref"]


def load():
    return pd.read_csv(_BM_CSV)


def draw(fig=None, axes=None):
    bm = load()

    if fig is None:
        fig, axes = plt.subplots(1, 4, figsize=(FIG_WIDTH_DOUBLE, 2.0))

    for ax, param in zip(axes, PARAMS):
        sub = bm[bm.param == param]
        lo_prior, hi_prior = PRIOR_RANGES[param]

        xs = np.linspace(lo_prior, hi_prior, 300)
        prior_pdf = np.ones_like(xs) / (hi_prior - lo_prior)
        ax.fill_between(xs, prior_pdf, alpha=0.15, color=C["prior"], zorder=0)
        ax.plot(xs, prior_pdf, color=C["prior"], lw=LW["aux"],
                label="Prior", zorder=1)

        all_pdfs = []
        for _, row in sub.iterrows():
            pdf = norm.pdf(xs, row["post_mean"], row["post_std"])
            all_pdfs.append(pdf)
        all_pdfs = np.array(all_pdfs)

        median_pdf = np.median(all_pdfs, axis=0)
        lo_pdf = np.percentile(all_pdfs, 10, axis=0)
        hi_pdf = np.percentile(all_pdfs, 90, axis=0)

        ax.fill_between(xs, lo_pdf, hi_pdf, alpha=0.18, color=C["posterior"], zorder=2)
        ax.plot(xs, median_pdf, color=C["posterior"], lw=LW["main"],
                label="Posterior", zorder=3)

        ax.set_xlabel(PARAM_LABELS[param], fontsize=FS["tick"])
        ax.set_xlim(lo_prior, hi_prior)
        ax.set_ylim(bottom=0)
        ax.set_yticks([])
        finalize_axes(ax)
        ax.spines["left"].set_visible(False)

    axes[0].set_ylabel("Density", fontsize=FS["axis"])
    axes[-1].legend(fontsize=FS["legend"], frameon=False, loc="upper right")

    return fig, axes


def main():
    set_publication_rc()
    fig, axes = draw()
    panel_label(axes[0], "(A)")
    fig.subplots_adjust(wspace=0.15)
    written = savefig(fig, "E1_prior_posterior", _OUT_DIR)
    for w in written:
        print("wrote", w)


if __name__ == "__main__":
    main()
