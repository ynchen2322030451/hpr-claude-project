"""Figure E — MCMC Diagnostics (Appendix E).

Moved from main-text Fig 6 to appendix.
Layout: 3 rows.
  Row 0: (A) MCMC trace plot (4 params, representative case) — full width
  Row 1: (B) Rhat diagnostics  |  (C) ESS diagnostics

This figure contains the MCMC convergence diagnostics that support
the main-text posterior calibration results.
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
from H3_mcmc_diagnostics import draw as draw_h3

_BNN0414 = _FIG.parents[1]
_OUT_DIR = _BNN0414 / "manuscript" / "0414_v4" / "figures"


def compose():
    set_publication_rc()

    fig = plt.figure(figsize=(FIG_WIDTH_DOUBLE, 7.0))
    gs = gridspec.GridSpec(2, 1, figure=fig,
                           height_ratios=[1.5, 0.8],
                           hspace=0.40)

    # Row 0: MCMC trace (4 stacked rows within)
    gs_trace = gridspec.GridSpecFromSubplotSpec(4, 1, subplot_spec=gs[0],
                                                hspace=0.25)
    axes_trace = [fig.add_subplot(gs_trace[i]) for i in range(4)]

    # Row 1: diagnostics (rhat + ESS side by side)
    gs_diag = gridspec.GridSpecFromSubplotSpec(1, 2, subplot_spec=gs[1],
                                               wspace=0.40)
    ax_rhat = fig.add_subplot(gs_diag[0, 0])
    ax_ess = fig.add_subplot(gs_diag[0, 1])

    draw_h1(fig=fig, axes=axes_trace)
    draw_h3(fig=fig, axes=[ax_rhat, ax_ess])

    panel_label(axes_trace[0], "(A)")
    panel_label(ax_rhat,       "(B)")
    panel_label(ax_ess,        "(C)")

    written = savefig(fig, "figE_mcmc_diagnostics", _OUT_DIR)
    for w in written:
        print("wrote", w)


if __name__ == "__main__":
    compose()
