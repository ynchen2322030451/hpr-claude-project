"""G1 — Computational speedup: surrogate vs high-fidelity simulation.

Bar chart of N_samples_required and wall-clock comparison at different
target CI half-widths, with speedup annotation.  tau = 131 MPa, batch mode.
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

_BNN0414   = _FIG.parents[1]
_SPEED_CSV = _BNN0414 / "results" / "speed" / "budget_matched_risk.csv"
_OUT_DIR   = _BNN0414 / "manuscript" / "0414_v4" / "figures" / "bank"


def load():
    df = pd.read_csv(_SPEED_CSV)
    sub = df[(df.model_id == "bnn-baseline") &
             (df.surrogate_mode == "batch") &
             (df.tau_MPa == 131.0)].copy()
    return sub.sort_values("target_CI_half")


def draw(fig=None, ax=None):
    df = load()

    if fig is None:
        fig, ax = plt.subplots(figsize=(FIG_WIDTH_SINGLE, 2.6))

    ci_labels = [f"{v:.3f}" if v < 0.01 else f"{v:.2f}" if v < 0.1 else f"{v:.1f}"
                 for v in df.target_CI_half]
    # clean labels
    ci_labels = [s.rstrip("0").rstrip(".") for s in ci_labels]

    x = np.arange(len(ci_labels))
    surr_sec = df.surrogate_total_sec.values
    hf_sec   = df.HF_total_sec.values

    # side-by-side bars
    w = 0.35
    ax.bar(x - w / 2, surr_sec, w, color=C["main"], alpha=0.8,
           label="Surrogate", zorder=2)
    ax.bar(x + w / 2, hf_sec, w, color=C["ci_zero"], alpha=0.7,
           label="High-fidelity", zorder=2)

    ax.set_yscale("log")
    ax.set_xticks(x)
    ax.set_xticklabels(ci_labels)
    ax.set_xlabel("Target CI half-width")
    ax.set_ylabel("Wall-clock time (seconds)")

    # annotate speedup — single label at top
    speedup = df.speedup_HF_over_surr.values
    sp_val = speedup[0]
    ax.text(0.5, 0.95, f"Speedup: {sp_val:.1e}$\\times$",
            transform=ax.transAxes, ha="center", va="top",
            fontsize=FS["axis"], fontweight="medium", color=C["text"])

    ax.legend(fontsize=FS["legend"], frameon=False, loc="upper left",
              handlelength=1.2, borderpad=0.3)

    finalize_axes(ax)
    return fig, ax


def main():
    set_publication_rc()
    fig, ax = draw()
    panel_label(ax, "(A)")
    written = savefig(fig, "G1_speedup", _OUT_DIR)
    for w in written:
        print("wrote", w)


if __name__ == "__main__":
    main()
