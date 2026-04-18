"""Figure 5 — Posterior inference (composed from E1 + E2 + E3 + summary).

Layout (3 logical rows):
  Row 0: prior/posterior marginals (A) — 4 parameter subplots spanning full width
  Row 1: coverage dot chart (B) left, posterior-predictive parity (C) right
  Row 2: posterior summary table (D) — acceptance rate, contraction, coverage
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

_HERE = Path(__file__).resolve().parent
_FIG  = _HERE.parent
if str(_FIG) not in sys.path:
    sys.path.insert(0, str(_FIG))

sys.path.insert(0, str(_FIG / "bank"))

from figure_style import set_publication_rc, panel_label, FIG_WIDTH_DOUBLE, C, FS
from figure_io import savefig
from E1_prior_posterior import draw as draw_e1, PRIOR_RANGES
from E2_posterior_coverage import draw as draw_e2
from E3_posterior_predictive import draw as draw_e3

_BNN0414 = _FIG.parents[1]
_OUT_DIR = _BNN0414 / "manuscript" / "0414_v4" / "figures"
_BM_CSV  = (_BNN0414 / "code" / "experiments" / "posterior" /
            "bnn-phy-mono" / "benchmark_summary.csv")

PARAM_LABELS = {
    "E_intercept":  r"$E_\mathrm{intercept}$",
    "alpha_base":   r"$\alpha_\mathrm{base}$",
    "alpha_slope":  r"$\alpha_\mathrm{slope}$",
    "SS316_k_ref":  r"$k_\mathrm{ref}$",
}


def _build_summary_table():
    """Build posterior summary: acceptance, contraction, 90CI coverage."""
    bm = pd.read_csv(_BM_CSV)
    rows = []
    for param in ["E_intercept", "alpha_base", "alpha_slope", "SS316_k_ref"]:
        sub = bm[bm.param == param]
        accept_mean = sub.accept_rate.mean()
        coverage    = sub.in_90ci.mean()
        # contraction = 1 - (mean post_std / prior half-width)
        lo, hi = PRIOR_RANGES[param]
        prior_hw = (hi - lo) / 2
        mean_std = sub.post_std.mean()
        contraction = 1.0 - (mean_std / prior_hw)
        rows.append([
            PARAM_LABELS[param],
            f"{accept_mean:.3f}",
            f"{contraction:.1%}",
            f"{coverage:.0%}",
        ])
    return rows


def compose():
    set_publication_rc()

    fig = plt.figure(figsize=(FIG_WIDTH_DOUBLE, 6.8))
    gs = gridspec.GridSpec(
        3, 2, figure=fig,
        width_ratios=[1.2, 1],
        height_ratios=[1, 1.3, 0.28],
        hspace=0.55, wspace=0.45,
    )

    # Row 0: prior/posterior marginals (A)
    gs_top = gridspec.GridSpecFromSubplotSpec(1, 4, subplot_spec=gs[0, :],
                                              wspace=0.15)
    axes_top = [fig.add_subplot(gs_top[0, i]) for i in range(4)]

    # Row 1: coverage (B) + predictive parity (C)
    ax_cov  = fig.add_subplot(gs[1, 0])
    ax_pred = fig.add_subplot(gs[1, 1])

    # Row 2: summary table (D)
    ax_table = fig.add_subplot(gs[2, :])
    ax_table.axis("off")

    draw_e1(fig=fig, axes=axes_top)
    draw_e2(fig=fig, ax=ax_cov)
    draw_e3(fig=fig, ax=ax_pred)

    panel_label(axes_top[0], "(A)")
    panel_label(ax_cov,      "(B)")
    panel_label(ax_pred,     "(C)")

    # --- summary table -------------------------------------------------------
    col_labels = ["Parameter", "Accept. rate", "Contraction", r"90% CI cov."]
    cell_data  = _build_summary_table()

    table = ax_table.table(
        cellText=cell_data,
        colLabels=col_labels,
        loc="center",
        cellLoc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(FS["legend"])
    table.scale(1.0, 1.15)

    header_color = C["posterior"]
    for j in range(len(col_labels)):
        cell = table[0, j]
        cell.set_facecolor(header_color)
        cell.set_text_props(color="white", fontweight="bold")
        cell.set_edgecolor("white")

    row_colors = ["#F2F2F2", "#FFFFFF"]
    for i in range(1, len(cell_data) + 1):
        bg = row_colors[(i - 1) % 2]
        for j in range(len(col_labels)):
            cell = table[i, j]
            cell.set_facecolor(bg)
            cell.set_edgecolor("#DDDDDD")
            cell.set_text_props(color=C["text"])

    for i in range(len(cell_data) + 1):
        table[i, 0].set_text_props(ha="left")
        table[i, 0]._loc = "left"

    written = savefig(fig, "fig5_posterior", _OUT_DIR)
    for w in written:
        print("wrote", w)


if __name__ == "__main__":
    compose()
