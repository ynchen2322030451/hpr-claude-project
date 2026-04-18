"""H2 — MCMC rank histogram for convergence diagnostics (case_06).

2x2 subplots, one per parameter. 4 chains per subplot.
Uniform rank distribution = good mixing.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import rankdata

_HERE = Path(__file__).resolve().parent
_FIG  = _HERE.parent
if str(_FIG) not in sys.path:
    sys.path.insert(0, str(_FIG))

from figure_style import (
    set_publication_rc, finalize_axes, panel_label,
    C, FS, FIG_WIDTH_DOUBLE,
)
from figure_io import savefig

_BNN0414   = _FIG.parents[1]
_CHAIN_NPZ = (_BNN0414 / "code" / "experiments_0404" / "experiments" /
              "posterior" / "bnn-phy-mono" / "diagnostics" / "chains" /
              "case_06.npz")
_OUT_DIR   = _BNN0414 / "manuscript" / "0414_v4" / "figures" / "bank"

PARAM_LABELS = {
    "E_intercept":  r"$E_\mathrm{intercept}$",
    "alpha_base":   r"$\alpha_\mathrm{base}$",
    "alpha_slope":  r"$\alpha_\mathrm{slope}$",
    "SS316_k_ref":  r"$k_\mathrm{ref}$",
}

CHAIN_COLORS = ["#2F5AA6", "#D4853A", "#3A7D7B", "#7B6BA5"]


def load():
    d = np.load(_CHAIN_NPZ, allow_pickle=True)
    return d["chains"], list(d["param_names"])


def draw(fig=None, axes=None):
    chains, param_names = load()
    n_chains, n_iter, n_params = chains.shape

    if fig is None:
        fig, axes = plt.subplots(2, 2, figsize=(FIG_WIDTH_DOUBLE, 3.6))
    axes_flat = axes.flat if hasattr(axes, 'flat') else axes

    n_bins = 20
    for i, (ax, pname) in enumerate(zip(axes_flat, param_names)):
        # pool all chains, compute global ranks
        pooled = chains[:, :, i].ravel()
        ranks = rankdata(pooled)
        # split back
        per_chain = ranks.reshape(n_chains, n_iter)
        ref_height = n_iter  # expected count per bin per chain

        for c in range(n_chains):
            ax.hist(per_chain[c], bins=n_bins,
                    range=(0.5, n_chains * n_iter + 0.5),
                    color=CHAIN_COLORS[c], alpha=0.45,
                    edgecolor="none", zorder=2,
                    label=f"Chain {c+1}" if i == 0 else None)
        ax.axhline(ref_height, color=C["refline"], ls="--", lw=0.6, zorder=1)
        ax.set_title(PARAM_LABELS.get(pname, pname),
                     fontsize=FS["title"], pad=3)
        ax.set_xlabel("Rank" if i >= 2 else "")
        finalize_axes(ax)

    if hasattr(axes, 'flat'):
        axes.flat[0].legend(fontsize=FS["legend"], frameon=False,
                            loc="upper right", ncol=2)
    return fig, axes


def main():
    set_publication_rc()
    fig, axes = draw()
    panel_label(axes.flat[0], "(A)")
    fig.tight_layout()
    written = savefig(fig, "H2_mcmc_rank", _OUT_DIR)
    for w in written:
        print("wrote", w)


if __name__ == "__main__":
    main()
