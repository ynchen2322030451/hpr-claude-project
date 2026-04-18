"""Figure 5 — Observation-conditioned posterior shift and predictive calibration.

Three-panel layout:
  (A) Prior vs posterior marginals for 4 calibration params (Gaussian
      approximation from posterior summary stats; raw MCMC chains were
      not saved to disk).
  (B) 90% CI coverage across 18 benchmark cases: per-param dot indicating
      whether the true value falls within the posterior 90% CI.
  (C) Posterior predictive stress vs observed/true stress for the 10
      feasible-region extreme cases (these cases have stress_post_mean,
      stress_post_p5, stress_post_p95 saved).

Phase-1 rulings enforced:
  * 3 panels (MCMC diagnostics → appendix).
  * No threshold feasibility gate.
  * No pass/fail, no category-coloured stratification.
  * No "correctly identifies" language.
  * Over-coverage noted as trade-off.

Data limitation note: Panel (A) uses Gaussian approximation because raw
posterior chains were not persisted. Panel (C) uses 10 extreme cases from
feasible_region.csv rather than the 18 benchmark cases because posterior
predictive stress statistics are only available for those 10 cases.

Output: code/bnn0414/manuscript/0414_v4/figures/fig5_posterior.{pdf,svg,png}
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import norm

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from figure_io import savefig
from figure_style import (
    ALPHAS, COLORS, FONT_SIZES, LINEWIDTHS,
    apply_rc, clean_ax, panel_label,
)

_BNN0414  = _HERE.parents[1]
_POST_DIR = (_BNN0414 / "code" / "experiments" / "posterior" / "bnn-phy-mono")
_FIG_DIR  = _BNN0414 / "manuscript" / "0414_v4" / "figures"

CALIB_PARAMS = ["E_intercept", "alpha_base", "alpha_slope", "SS316_k_ref"]
PARAM_LABELS = {
    "E_intercept": r"$E_\mathrm{intercept}$",
    "alpha_base":  r"$\alpha_\mathrm{base}$",
    "alpha_slope": r"$\alpha_\mathrm{slope}$",
    "SS316_k_ref": r"$k_\mathrm{ref}$ (SS316)",
}
PARAM_UNITS = {
    "E_intercept": "Pa",
    "alpha_base":  "1/K",
    "alpha_slope": r"1/K$^2$",
    "SS316_k_ref": "W/(m·K)",
}
PRIOR_BOUNDS = {
    "E_intercept": (1.387e11, 2.592e11),
    "alpha_base":  (6.525e-6, 1.340e-5),
    "alpha_slope": (3.442e-9, 6.519e-9),
    "SS316_k_ref": (15.71, 29.93),
}

REPR_CASE = 10


def _load():
    bs = pd.read_csv(_POST_DIR / "benchmark_summary.csv")
    fr = pd.read_csv(_POST_DIR / "feasible_region.csv")
    with open(_POST_DIR / "benchmark_case_meta.json") as f:
        meta = json.load(f)
    return bs, fr, meta


def _panel_a(ax_arr, bs):
    """Prior vs posterior marginals for a representative case."""
    case = bs[bs.case_idx == REPR_CASE]
    for i, param in enumerate(CALIB_PARAMS):
        ax = ax_arr[i]
        row = case[case.param == param].iloc[0]
        lo, hi = PRIOR_BOUNDS[param]
        rng = hi - lo

        x = np.linspace(lo - 0.15 * rng, hi + 0.15 * rng, 300)
        prior_y = np.where((x >= lo) & (x <= hi), 1.0 / rng, 0.0)

        post_y = norm.pdf(x, row.post_mean, row.post_std)

        ax.fill_between(x, prior_y, alpha=0.25, color=COLORS["prior"],
                         label="Prior (uniform)", step="mid")
        ax.plot(x, post_y, color=COLORS["posterior"], lw=LINEWIDTHS["main"],
                label="Posterior (approx.)")
        ax.fill_between(x, post_y, alpha=ALPHAS["band"],
                         color=COLORS["posterior"])

        ax.axvline(row.true_value, color=COLORS["observed"], ls="--",
                    lw=LINEWIDTHS["aux"], label="True value")

        ax.set_xlabel(f"{PARAM_LABELS[param]}")
        ax.set_yticks([])
        clean_ax(ax)

        if i == 0:
            ax.legend(fontsize=5, loc="upper right", frameon=False)

    stress = case.stress_true_MPa.iloc[0]
    ax_arr[0].set_title(
        f"Case {REPR_CASE} (obs. stress {stress:.0f} MPa)",
        fontsize=FONT_SIZES["axis"], loc="left",
    )


def _panel_b(ax, bs, meta):
    """90% CI coverage dot chart across 18 benchmark cases."""
    cases = sorted(bs.case_idx.unique())
    n_cases = len(cases)

    for j, param in enumerate(CALIB_PARAMS):
        sub = bs[bs.param == param].sort_values("case_idx")
        y_pos = np.arange(n_cases) + j * 0.18 - 0.27
        hits = sub.in_90ci.values.astype(float)
        colors = [COLORS["bnn_main"] if h else "#cc3333" for h in hits]
        ax.scatter(y_pos, [j] * n_cases, c=colors, s=14, zorder=3,
                    marker="s" if j % 2 == 0 else "o",
                    edgecolors="none", alpha=0.8)

    ax.set_yticks(range(len(CALIB_PARAMS)))
    ax.set_yticklabels([PARAM_LABELS[p] for p in CALIB_PARAMS])
    ax.set_xticks(range(n_cases))
    ax.set_xticklabels([str(c) for c in cases], fontsize=5)
    ax.set_xlabel("Benchmark case index")
    ax.set_title("90% CI coverage per case", fontsize=FONT_SIZES["axis"],
                  loc="left")
    clean_ax(ax)

    total_hits = bs.in_90ci.sum()
    total = len(bs)
    cov = total_hits / total
    ax.text(0.98, 0.97,
            f"Overall: {total_hits}/{total} = {cov:.3f}",
            transform=ax.transAxes, fontsize=6, ha="right", va="top",
            bbox=dict(boxstyle="round,pad=0.3", fc="white",
                      ec="#cccccc", alpha=0.85, lw=0.5))

    import matplotlib.lines as mlines
    h_hit = mlines.Line2D([], [], color=COLORS["bnn_main"], marker="s",
                            ls="", ms=5, label="In 90% CI")
    h_miss = mlines.Line2D([], [], color="#cc3333", marker="s",
                             ls="", ms=5, label="Outside 90% CI")
    ax.legend(handles=[h_hit, h_miss], fontsize=5, loc="lower right",
               frameon=False)


def _panel_c(ax, fr):
    """Posterior predictive stress vs observed/true stress."""
    uniq = fr.drop_duplicates("case_idx").sort_values("stress_true_MPa")

    yt = uniq.stress_true_MPa.values
    yp = uniq.stress_post_mean.values
    lo = uniq.stress_post_p5.values
    hi = uniq.stress_post_p95.values

    lims = (min(yt.min(), lo.min()) - 8,
            max(yt.max(), hi.max()) + 8)
    ax.plot(lims, lims, ls="--", lw=LINEWIDTHS["ref"],
            color=COLORS["reference_line"], zorder=1)

    ax.errorbar(yt, yp, yerr=[yp - lo, hi - yp],
                fmt="o", ms=5, color=COLORS["posterior"],
                ecolor=COLORS["posterior"], elinewidth=0.8,
                capsize=2, alpha=0.85, zorder=3)

    ax.set_xlabel("Observed stress (MPa)")
    ax.set_ylabel("Posterior predictive\nstress (MPa)")
    ax.set_xlim(lims); ax.set_ylim(lims)
    ax.set_aspect("equal", adjustable="box")
    ax.set_title("Posterior predictive vs observed",
                  fontsize=FONT_SIZES["axis"], loc="left")
    clean_ax(ax)

    ax.text(0.97, 0.03,
            f"n = {len(uniq)} cases\n90% pred. interval",
            transform=ax.transAxes, fontsize=5.5,
            ha="right", va="bottom",
            bbox=dict(boxstyle="round,pad=0.3", fc="white",
                      ec="#cccccc", alpha=0.85, lw=0.5))


def main() -> None:
    apply_rc()
    bs, fr, meta = _load()

    fig = plt.figure(figsize=(7.1, 5.8))
    gs = fig.add_gridspec(2, 2, height_ratios=[1, 1.3], hspace=0.45,
                           wspace=0.40)

    gs_top = gs[0, :].subgridspec(1, 4, wspace=0.35)
    ax_marg = [fig.add_subplot(gs_top[0, i]) for i in range(4)]
    _panel_a(ax_marg, bs)
    panel_label(ax_marg[0], "(A)", loc=(-0.25, 1.12))

    ax_cov = fig.add_subplot(gs[1, 0])
    _panel_b(ax_cov, bs, meta)
    panel_label(ax_cov, "(B)")

    ax_pred = fig.add_subplot(gs[1, 1])
    _panel_c(ax_pred, fr)
    panel_label(ax_pred, "(C)")

    written = savefig(fig, "fig5_posterior", _FIG_DIR)
    for w in written:
        print("wrote", w)


if __name__ == "__main__":
    main()
