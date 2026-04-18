"""Figure 3 — Forward-propagated response distributions under coupling.

Two-panel violin + inner-box: (A) uncoupled vs coupled max stress,
(B) coupled k_eff.  Distributions are from 435 held-out HF simulations
(same test split as Fig 2), showing the *physical* coupling effect; the
BNN subsequently enables this analysis at 20k-sample scale.

Phase-1 rulings enforced:
  * Violin + inner box, not KDE + quantile strip.
  * Median line + p5–p95 whisker + p25–p75 thick bar always visible.
  * No 131 MPa threshold line as primary visual.
  * No exceedance curve, no pass/fail language.
  * Std compression numbers NOT hard-coded — read from data at draw time.

Output: code/bnn0414/manuscript/0414_v4/figures/fig3_forward.{pdf,svg,png}
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from figure_io import savefig
from figure_style import (
    ALPHAS, COLORS, FONT_SIZES, LINEWIDTHS,
    apply_rc, clean_ax, panel_label,
)

_BNN0414   = _HERE.parents[1]
_PRED_JSON = (_BNN0414 / "code" / "models" / "bnn-phy-mono" /
              "fixed_eval" / "test_predictions_fixed.json")
_FIG_DIR   = _BNN0414 / "manuscript" / "0414_v4" / "figures"


def _load():
    with open(_PRED_JSON) as f:
        d = json.load(f)
    cols = d["output_cols"]
    yt = np.array(d["y_true"])
    return cols, yt


def _draw_violin_with_box(ax, data, pos, color, width=0.6):
    """Draw a single violin body with inner box (p25–p75) + whisker
    (p5–p95) + median dot."""
    parts = ax.violinplot(
        data, positions=[pos], widths=width, showmedians=False,
        showmeans=False, showextrema=False,
    )
    for pc in parts["bodies"]:
        pc.set_facecolor(color)
        pc.set_edgecolor(color)
        pc.set_alpha(ALPHAS["violin"])
        pc.set_linewidth(0.6)

    p5, p25, p50, p75, p95 = np.percentile(data, [5, 25, 50, 75, 95])

    bw = width * 0.18
    ax.vlines(pos, p5, p95, color=color, lw=LINEWIDTHS["aux"], zorder=5)
    ax.vlines(pos, p25, p75, color=color, lw=3.5, zorder=6)

    ax.scatter([pos], [p50], color="white", edgecolors=color,
               s=20, zorder=7, linewidths=0.8)

    return {"p5": p5, "p25": p25, "median": p50, "p75": p75, "p95": p95,
            "mean": np.mean(data), "std": np.std(data)}


def main() -> None:
    apply_rc()
    cols, yt = _load()

    stress1 = yt[:, cols.index("iteration1_max_global_stress")]
    stress2 = yt[:, cols.index("iteration2_max_global_stress")]
    keff2   = yt[:, cols.index("iteration2_keff")]

    fig = plt.figure(figsize=(5.5, 3.2))
    gs = fig.add_gridspec(1, 2, width_ratios=[3, 1.4], wspace=0.45)
    ax_s = fig.add_subplot(gs[0])
    ax_k = fig.add_subplot(gs[1])

    # ── Panel (A): stress violin ──────────────────────────────────────
    s1_stats = _draw_violin_with_box(ax_s, stress1, pos=0,
                                      color=COLORS["uncoupled"], width=0.55)
    s2_stats = _draw_violin_with_box(ax_s, stress2, pos=1,
                                      color=COLORS["coupled"], width=0.55)

    ax_s.set_xticks([0, 1])
    ax_s.set_xticklabels(["Uncoupled\npass", "Coupled\nsteady state"],
                          fontsize=FONT_SIZES["axis"])
    ax_s.set_ylabel("Max stress (MPa)")
    clean_ax(ax_s)
    panel_label(ax_s, "(A)")

    ann_a = (
        f"uncoupled: $\\mu$={s1_stats['mean']:.1f}, "
        f"$\\sigma$={s1_stats['std']:.1f} MPa\n"
        f"coupled:   $\\mu$={s2_stats['mean']:.1f}, "
        f"$\\sigma$={s2_stats['std']:.1f} MPa"
    )
    ax_s.text(0.98, 0.97, ann_a, transform=ax_s.transAxes,
              fontsize=5.5, ha="right", va="top",
              bbox=dict(boxstyle="round,pad=0.3", fc="white",
                        ec="#cccccc", alpha=0.85, lw=0.5))

    # ── Panel (B): keff violin ────────────────────────────────────────
    k_stats = _draw_violin_with_box(ax_k, keff2, pos=0,
                                     color=COLORS["coupled"], width=0.45)

    ax_k.set_xticks([0])
    ax_k.set_xticklabels(["Coupled\nsteady state"],
                          fontsize=FONT_SIZES["axis"])
    ax_k.set_ylabel(r"$k_\mathrm{eff}$")
    clean_ax(ax_k)
    panel_label(ax_k, "(B)")

    k_std_pcm = k_stats["std"] * 1e5
    ann_b = (
        f"$\\mu$={k_stats['mean']:.4f}\n"
        f"$\\sigma$={k_std_pcm:.1f} pcm"
    )
    ax_k.text(0.95, 0.97, ann_b, transform=ax_k.transAxes,
              fontsize=5.5, ha="right", va="top",
              bbox=dict(boxstyle="round,pad=0.3", fc="white",
                        ec="#cccccc", alpha=0.85, lw=0.5))

    fig.suptitle("")

    written = savefig(fig, "fig3_forward", _FIG_DIR)
    for w in written:
        print("wrote", w)

    print(f"\n--- data-derived summary ---")
    print(f"uncoupled stress: mean={s1_stats['mean']:.2f} std={s1_stats['std']:.2f}")
    print(f"coupled   stress: mean={s2_stats['mean']:.2f} std={s2_stats['std']:.2f}")
    red = (1 - s2_stats['std'] / s1_stats['std']) * 100
    print(f"std reduction: {red:.1f}%")
    print(f"coupled keff: mean={k_stats['mean']:.6f} std_pcm={k_std_pcm:.1f}")


if __name__ == "__main__":
    main()
