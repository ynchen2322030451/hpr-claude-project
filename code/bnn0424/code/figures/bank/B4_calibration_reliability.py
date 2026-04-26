"""B4 — Reliability diagram for stress (nominal vs empirical coverage).

Physics-regularized BNN (blue) vs reference surrogate (grey) with
y = x perfect-calibration reference line.
"""
from __future__ import annotations

import sys
from pathlib import Path

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

_BNN0414  = _FIG.parents[1]
_CAL_CSV  = (_BNN0414 / "results" / "accuracy" /
             "calibration_multi_alpha.csv")
_OUT_DIR  = _BNN0414 / "manuscript" / "0414_v4" / "figures" / "bank"

OUTPUT = "iteration2_max_global_stress"


def load():
    df = pd.read_csv(_CAL_CSV)
    df = df[df.output == OUTPUT]
    phy  = df[df.model_id == "bnn-phy-mono"].sort_values("nominal_alpha")
    base = df[df.model_id == "bnn-baseline"].sort_values("nominal_alpha")
    return phy, base


def draw(fig=None, ax=None):
    phy, base = load()

    if fig is None:
        fig, ax = plt.subplots(figsize=(FIG_WIDTH_SINGLE, FIG_WIDTH_SINGLE))

    # perfect calibration reference
    ax.plot([0, 1], [0, 1], "--", color=C["refline"], lw=LW["ref"],
            zorder=1, label="Perfect calibration")

    # baseline (grey)
    ax.plot(base.nominal_alpha, base.empirical_coverage,
            "o-", color=C["ci_zero"], ms=4, lw=LW["main"],
            label="Reference surrogate", zorder=2)

    # phy-mono (blue)
    ax.plot(phy.nominal_alpha, phy.empirical_coverage,
            "s-", color=C["main"], ms=4, lw=LW["main"],
            label="Physics-regularized surrogate", zorder=3)

    ax.set_xlabel("Nominal coverage")
    ax.set_ylabel("Empirical coverage")
    ax.set_xlim(0.4, 1.02)
    ax.set_ylim(0.4, 1.02)
    ax.set_aspect("equal", adjustable="box")

    ax.legend(fontsize=FS["legend"], frameon=False, loc="upper left",
              handlelength=1.5, borderpad=0.4, labelspacing=0.3)

    finalize_axes(ax)
    return fig, ax


def main():
    set_publication_rc()
    fig, ax = draw()
    panel_label(ax, "(A)")
    written = savefig(fig, "B4_calibration_reliability", _OUT_DIR)
    for w in written:
        print("wrote", w)


if __name__ == "__main__":
    main()
