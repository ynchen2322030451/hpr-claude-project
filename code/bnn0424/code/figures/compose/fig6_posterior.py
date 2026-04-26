"""Figure 6 — Posterior Inference (main text, restructured).

Layout: 2 rows, 3 panels.
  Row 0: (A) Prior vs posterior marginals — 4 subplots, full width
  Row 1: (B) Joint posterior (E_intercept × α_base)  |  (C) Posterior predictive stress

Trace plots, R̂, ESS and autocorrelation are moved to Appendix E.
Core narrative = observation-conditioned distribution shift + predictive agreement.
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
from E1_prior_posterior import draw as draw_e1
from E3_posterior_predictive import draw as draw_e3
from E4_joint_posterior import draw as draw_e4

_BNN0414 = _FIG.parents[1]
_OUT_DIR = _BNN0414 / "manuscript" / "0414_v4" / "figures"


def compose():
    set_publication_rc()

    fig = plt.figure(figsize=(FIG_WIDTH_DOUBLE, 5.5))
    gs = gridspec.GridSpec(2, 1, figure=fig,
                           height_ratios=[0.8, 1.0],
                           hspace=0.45)

    # Row 0: (A) prior vs posterior marginals (4 side-by-side)
    gs_prior = gridspec.GridSpecFromSubplotSpec(1, 4, subplot_spec=gs[0],
                                                wspace=0.15)
    axes_prior = [fig.add_subplot(gs_prior[0, i]) for i in range(4)]

    # Row 1: (B) joint posterior  |  (C) posterior predictive
    gs_bottom = gridspec.GridSpecFromSubplotSpec(1, 2, subplot_spec=gs[1],
                                                 wspace=0.35)
    ax_joint = fig.add_subplot(gs_bottom[0, 0])
    ax_pred  = fig.add_subplot(gs_bottom[0, 1])

    # Draw all three panels from bank plots
    draw_e1(fig=fig, axes=axes_prior)
    draw_e4(fig=fig, ax=ax_joint)
    draw_e3(fig=fig, ax=ax_pred)

    panel_label(axes_prior[0], "(A)")
    panel_label(ax_joint,      "(B)")
    panel_label(ax_pred,       "(C)")

    written = savefig(fig, "fig6_posterior", _OUT_DIR)
    for w in written:
        print("wrote", w)


if __name__ == "__main__":
    compose()
