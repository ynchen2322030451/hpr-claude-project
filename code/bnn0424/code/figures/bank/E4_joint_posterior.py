"""E4 — Joint posterior (E_intercept × α_base) for main Fig 6 B.

Shows the compensation ridge: an increase in stiffness (E_intercept)
can be partially offset by a decrease in thermal expansion (α_base),
leaving σ ∝ E · α · ΔT approximately invariant.

Data source: 4-chain MCMC chain samples (.npz) for a representative
high-stress benchmark case.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

_HERE = Path(__file__).resolve().parent
_FIG  = _HERE.parent
if str(_FIG) not in sys.path:
    sys.path.insert(0, str(_FIG))

from figure_style import (
    set_publication_rc, finalize_axes, panel_label,
    C, A, LW, FS, FIG_WIDTH_SINGLE,
)
from figure_io import savefig

_BNN0414  = _FIG.parents[1]
_CHAIN_DIR = (_BNN0414 / "code" / "experiments" / "posterior" /
              "bnn-phy-mono" / "rerun_4chain")
_OUT_DIR   = _BNN0414 / "manuscript" / "0414_v4" / "figures" / "bank"

# Use case 12 (high-stress, ~135 MPa) — shows clear contraction
_CASE_IDX = 12


def load(case_idx: int = _CASE_IDX):
    npz = np.load(_CHAIN_DIR / f"chain_samples_case{case_idx}.npz",
                  allow_pickle=True)
    params = list(npz["params"])
    posterior = npz["posterior"]
    true_vals = npz["true_values"]
    return posterior, params, true_vals


def draw(fig=None, ax=None, case_idx: int = _CASE_IDX):
    posterior, params, true_vals = load(case_idx)

    e_idx = params.index("E_intercept")
    a_idx = params.index("alpha_base")

    e_samples = posterior[:, e_idx] / 1e9   # Pa → GPa
    a_samples = posterior[:, a_idx] * 1e6   # K⁻¹ → μK⁻¹
    e_true = true_vals[e_idx] / 1e9
    a_true = true_vals[a_idx] * 1e6

    if fig is None:
        fig, ax = plt.subplots(figsize=(FIG_WIDTH_SINGLE, FIG_WIDTH_SINGLE))

    # Hexbin density
    ax.hexbin(e_samples, a_samples,
              gridsize=30, cmap="Blues", mincnt=1,
              linewidths=0.1, edgecolors="white", alpha=0.85,
              zorder=1)

    # True value marker
    ax.plot(e_true, a_true,
            marker="*", markersize=9,
            color=C["posterior"], markeredgecolor="white",
            markeredgewidth=0.5, zorder=4,
            label="True value")

    # 2D contours (90% and 50% density)
    from scipy.stats import gaussian_kde
    xy = np.vstack([e_samples, a_samples])
    kde = gaussian_kde(xy)
    x_grid = np.linspace(e_samples.min(), e_samples.max(), 100)
    y_grid = np.linspace(a_samples.min(), a_samples.max(), 100)
    X, Y = np.meshgrid(x_grid, y_grid)
    Z = kde(np.vstack([X.ravel(), Y.ravel()])).reshape(X.shape)
    # Levels for 50% and 90% HPD
    z_flat = Z.ravel()
    z_sorted = np.sort(z_flat)[::-1]
    z_cumsum = np.cumsum(z_sorted) / z_sorted.sum()
    level_50 = z_sorted[np.searchsorted(z_cumsum, 0.50)]
    level_90 = z_sorted[np.searchsorted(z_cumsum, 0.90)]
    ax.contour(X, Y, Z, levels=[level_90, level_50],
               colors=[C["main_light"], C["main"]],
               linewidths=[LW["aux"], LW["main"]],
               linestyles=["--", "-"],
               zorder=3)

    ax.set_xlabel(r"$E_\mathrm{intercept}$ (GPa)", fontsize=FS["axis"])
    ax.set_ylabel(r"$\alpha_\mathrm{base}$ ($\mu$K$^{-1}$)", fontsize=FS["axis"])
    ax.legend(fontsize=FS["legend"], frameon=False, loc="upper right")

    finalize_axes(ax)
    return fig, ax


def main():
    set_publication_rc()
    fig, ax = draw()
    panel_label(ax, "(B)")
    fig.tight_layout()
    written = savefig(fig, "E4_joint_posterior", _OUT_DIR)
    for w in written:
        print("wrote", w)


if __name__ == "__main__":
    main()
