"""B6 — PIT histogram for calibration assessment.

Two subplots: stress and keff PIT distributions for bnn-phy-mono.
Ideal = uniform distribution (horizontal line at y=1).
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

_BNN0414  = _FIG.parents[1]
_PIT_NPZ  = _BNN0414 / "results" / "accuracy" / "pit_values.npz"
_OUT_DIR  = _BNN0414 / "manuscript" / "0414_v4" / "figures" / "bank"

PANELS = [
    ("bnn-phy-mono::iteration2_max_global_stress", "Max stress"),
    ("bnn-phy-mono::iteration2_keff",              r"$k_\mathrm{eff}$"),
]


def load():
    return np.load(_PIT_NPZ)


def draw(fig=None, axes=None):
    pit = load()

    if fig is None:
        fig, axes = plt.subplots(1, 2, figsize=(FIG_WIDTH_DOUBLE, 2.4))

    for ax, (key, title) in zip(axes, PANELS):
        vals = pit[key]
        n_bins = 20
        ax.hist(vals, bins=n_bins, range=(0, 1), density=True,
                color=C["main"], alpha=0.7, edgecolor="white",
                linewidth=0.4, zorder=2)
        ax.axhline(1.0, color=C["refline"], ls="--", lw=0.7, zorder=1)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, None)
        ax.set_xlabel("PIT value")
        ax.set_title(title, fontsize=FS["title"], pad=4)
        finalize_axes(ax)

    axes[0].set_ylabel("Density")
    return fig, axes


def main():
    set_publication_rc()
    fig, axes = draw()
    panel_label(axes[0], "(A)")
    panel_label(axes[1], "(B)")
    fig.tight_layout()
    written = savefig(fig, "B6_pit_histogram", _OUT_DIR)
    for w in written:
        print("wrote", w)


if __name__ == "__main__":
    main()
