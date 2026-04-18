"""C3 — Stress exceedance probability vs input variability (sigma_k).

Line plot with 3 threshold levels (110, 120, 131 MPa).
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
_RISK_CSV = (_BNN0414 / "code" / "experiments" / "risk_propagation" /
             "bnn-phy-mono" / "D1_nominal_risk.csv")
_OUT_DIR  = _BNN0414 / "manuscript" / "0414_v4" / "figures" / "bank"

THRESHOLDS = [110.0, 120.0, 131.0]
THRESH_STYLES = {
    110.0: {"color": "#7B6BA5", "ls": "--", "label": "110 MPa"},
    120.0: {"color": "#D4853A", "ls": "-.",  "label": "120 MPa"},
    131.0: {"color": "#2F5AA6", "ls": "-",  "label": "131 MPa (design limit)"},
}


def load():
    return pd.read_csv(_RISK_CSV)


def draw(fig=None, ax=None):
    df = load()

    if fig is None:
        fig, ax = plt.subplots(figsize=(FIG_WIDTH_SINGLE, 2.6))

    for tau in THRESHOLDS:
        sub = df[df.threshold_MPa == tau].sort_values("sigma_k")
        sty = THRESH_STYLES[tau]
        ax.plot(sub.sigma_k, sub.P_exceed, sty["ls"],
                color=sty["color"], lw=LW["main"], label=sty["label"],
                zorder=3)

    ax.set_xlabel(r"Input variability $\sigma_k$")
    ax.set_ylabel(r"$P(\sigma > \tau)$")
    ax.set_title("Stress exceedance probability", fontsize=FS["title"], pad=4)
    ax.set_xticks([0.5, 1.0, 1.5, 2.0])

    ax.legend(fontsize=FS["legend"], frameon=False, loc="lower right",
              handlelength=1.5, borderpad=0.3)

    finalize_axes(ax)
    return fig, ax


def main():
    set_publication_rc()
    fig, ax = draw()
    panel_label(ax, "(A)")
    written = savefig(fig, "C3_risk_curve", _OUT_DIR)
    for w in written:
        print("wrote", w)


if __name__ == "__main__":
    main()
