"""Figure 6 — Posterior Inference (SPEC Fig 3).

Layout: 3 rows.
  Row 0: (A) MCMC trace plot (4 params, case_06) — full width
  Row 1: (B) Prior vs posterior marginals — 4 subplots, full width
  Row 2: (C) Rhat diagnostics  |  (D) ESS diagnostics
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

_HERE = Path(__file__).resolve().parent
_FIG  = _HERE.parent
if str(_FIG) not in sys.path:
    sys.path.insert(0, str(_FIG))

sys.path.insert(0, str(_FIG / "bank"))

from figure_style import set_publication_rc, panel_label, FIG_WIDTH_DOUBLE
from figure_io import savefig
from H1_mcmc_trace import draw as draw_h1
from E1_prior_posterior import draw as draw_e1
from H3_mcmc_diagnostics import draw as draw_h3

_BNN0414 = _FIG.parents[1]
_OUT_DIR = _BNN0414 / "manuscript" / "0414_v4" / "figures"


def compose():
    set_publication_rc()

    fig = plt.figure(figsize=(FIG_WIDTH_DOUBLE, 9.0))
    gs = gridspec.GridSpec(3, 1, figure=fig,
                           height_ratios=[1.5, 0.7, 0.8],
                           hspace=0.40)

    # Row 0: MCMC trace (4 stacked rows within)
    gs_trace = gridspec.GridSpecFromSubplotSpec(4, 1, subplot_spec=gs[0],
                                                hspace=0.25)
    axes_trace = [fig.add_subplot(gs_trace[i]) for i in range(4)]

    # Row 1: prior vs posterior marginals (4 side-by-side)
    gs_prior = gridspec.GridSpecFromSubplotSpec(1, 4, subplot_spec=gs[1],
                                                wspace=0.15)
    axes_prior = [fig.add_subplot(gs_prior[0, i]) for i in range(4)]

    # Row 2: diagnostics (rhat + ESS side by side)
    gs_diag = gridspec.GridSpecFromSubplotSpec(1, 2, subplot_spec=gs[2],
                                               wspace=0.40)
    ax_rhat = fig.add_subplot(gs_diag[0, 0])
    ax_ess = fig.add_subplot(gs_diag[0, 1])

    draw_h1(fig=fig, axes=axes_trace)
    draw_e1(fig=fig, axes=axes_prior)
    draw_h3(fig=fig, axes=[ax_rhat, ax_ess])

    panel_label(axes_trace[0], "(A)")
    panel_label(axes_prior[0], "(B)")
    panel_label(ax_rhat,       "(C)")
    panel_label(ax_ess,        "(D)")

    written = savefig(fig, "fig6_posterior", _OUT_DIR)
    for w in written:
        print("wrote", w)


if __name__ == "__main__":
    compose()
