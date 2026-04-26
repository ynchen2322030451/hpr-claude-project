"""H1 — MCMC trace plot for a representative posterior case (case_06).

4 rows (one per parameter), 4 overlaid chains per row.
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
    C, FS, FIG_WIDTH_DOUBLE,
)
from figure_io import savefig

_BNN0414   = _FIG.parents[1]
_CHAIN_NPZ = (_BNN0414 / "code" / "experiments_0404" / "experiments" /
              "posterior" / "bnn-phy-mono" / "diagnostics" / "chains" /
              "case_06.npz")
_OUT_DIR   = _BNN0414 / "manuscript" / "0414_v4" / "figures" / "bank"

PARAM_LABELS = {
    "E_intercept":  r"$E_\mathrm{intercept}$ (Pa)",
    "alpha_base":   r"$\alpha_\mathrm{base}$ (K$^{-1}$)",
    "alpha_slope":  r"$\alpha_\mathrm{slope}$ (K$^{-2}$)",
    "SS316_k_ref":  r"$k_\mathrm{ref}$ (W/m$\cdot$K)",
}

CHAIN_COLORS = ["#2F5AA6", "#D4853A", "#3A7D7B", "#7B6BA5"]


def load():
    d = np.load(_CHAIN_NPZ, allow_pickle=True)
    return d["chains"], list(d["param_names"])


def draw(fig=None, axes=None):
    chains, param_names = load()
    n_chains, n_iter, n_params = chains.shape

    if fig is None:
        fig, axes = plt.subplots(n_params, 1,
                                 figsize=(FIG_WIDTH_DOUBLE, 4.5),
                                 sharex=True)

    for i, (ax, pname) in enumerate(zip(axes, param_names)):
        for c in range(n_chains):
            ax.plot(chains[c, :, i], color=CHAIN_COLORS[c],
                    alpha=0.55, lw=0.35, zorder=2)
        ax.set_ylabel(PARAM_LABELS.get(pname, pname), fontsize=FS["tick"])
        finalize_axes(ax)

    axes[-1].set_xlabel("Iteration")
    axes[-1].set_xlim(0, n_iter)
    return fig, axes


def main():
    set_publication_rc()
    fig, axes = draw()
    panel_label(axes[0], "(A)")
    fig.tight_layout()
    written = savefig(fig, "H1_mcmc_trace", _OUT_DIR)
    for w in written:
        print("wrote", w)


if __name__ == "__main__":
    main()
