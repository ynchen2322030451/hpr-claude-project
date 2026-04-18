"""C2 — Coupled keff distribution (secondary panel for Figure 3).

Shows the spread of k_eff under coupled steady-state conditions.
Single KDE density with rug plot.
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

KEFF_IDX = 7


def load():
    with open(_PRED_JSON) as f:
        d = json.load(f)
    return np.array(d["y_true"])


def draw(fig=None, ax=None):
    yt = load()
    k = yt[:, KEFF_IDX]

    if fig is None:
        fig, ax = plt.subplots(figsize=(FIG_WIDTH_SINGLE, 2.6))

    pad = (k.max() - k.min()) * 0.15
    xs = np.linspace(k.min() - pad, k.max() + pad, 400)

    kde = gaussian_kde(k, bw_method=0.3)
    ax.fill_between(xs, kde(xs), alpha=0.22, color=C["main"], zorder=1)
    ax.plot(xs, kde(xs), color=C["main"], lw=LW["main"], zorder=2)

    ax.plot(k, np.full_like(k, -0.003 * kde(xs).max()),
            "|", color=C["main"], alpha=0.15, ms=4, mew=0.4, zorder=0)

    ax.set_xlabel(r"$k_\mathrm{eff}$ (coupled)")
    ax.set_ylabel("Density")
    ax.set_xlim(xs[0], xs[-1])
    ax.set_ylim(bottom=kde(xs).max() * -0.05)

    finalize_axes(ax)

    add_metric_text(ax,
                    f"$\\mu$ = {k.mean():.4f}\n"
                    f"$\\sigma$ = {k.std():.4f}",
                    loc="upper right")

    return fig, ax


def main():
    set_publication_rc()
    fig, ax = draw()
    panel_label(ax, "(B)")
    written = savefig(fig, "C2_keff_distribution", _OUT_DIR)
    for w in written:
        print("wrote", w)


if __name__ == "__main__":
    main()
