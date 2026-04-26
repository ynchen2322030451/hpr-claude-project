#!/usr/bin/env python3
"""
figure3_panelA_stress.py
========================
Panel A: Max stress — uncoupled pass vs coupled steady state.
Raincloud-like: violin + box + jitter + quantile annotation.

Data source: forward_uq_alloutput_predictive.csv (summary stats)

Style: NCS palette — blue (uncoupled) + orange/coral (coupled).
"""

import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR.parent / "_shared"))
import ncs_style

ncs_style.apply_style()

OUTDIR = SCRIPT_DIR / "outputs"
OUTDIR.mkdir(exist_ok=True)

# Colors: blue (uncoupled) + orange/coral (coupled)
COLOR_UNCOUPLED = ncs_style.BLUE_MID       # #3B6B9A  blue
COLOR_COUPLED   = ncs_style.ACCENT_ORANGE  # #C4713B  orange/coral

VIOLIN_ALPHA = 0.18
BOX_ALPHA    = 0.30
JITTER_ALPHA = 0.12


def annotate_quantiles(ax, x, data, color, side="right"):
    q5, q50, q95 = np.percentile(data, [5, 50, 95])
    if side == "right":
        x0, x1, xt, ha = x + 0.03, x + 0.30, x + 0.32, "left"
    else:
        x0, x1, xt, ha = x - 0.30, x - 0.03, x - 0.32, "right"

    for y, name in zip([q5, q50, q95], ["P5", "P50", "P95"]):
        ax.hlines(y, x0, x1, color=color, linestyle=(0, (4, 3)),
                  linewidth=ncs_style.LW_SECONDARY)
        ax.text(xt, y, f"{name} = {y:.0f} MPa", color=color,
                va="center", ha=ha, fontsize=ncs_style.FONT_ANNOTATION)
    return q5, q50, q95


def load_real_data():
    """Load real forward UQ data from CSV summaries."""
    pred_csv = SCRIPT_DIR / "forward_uq_alloutput_predictive.csv"
    pred = pd.read_csv(pred_csv)
    row = pred[pred["label"] == "Peak stress (MPa)"].iloc[0]
    return {
        "coupled_mean": row["coupled_mean"],
        "coupled_std": row["coupled_std"],
        "decoupled_mean": row["decoupled_mean"],
        "decoupled_std": row["decoupled_std"],
    }


def generate_samples(stats, n=4000, seed=42):
    """Generate samples from normal approximation for visualization."""
    rng = np.random.default_rng(seed)
    uncoupled = rng.normal(stats["decoupled_mean"], stats["decoupled_std"], n)
    coupled = rng.normal(stats["coupled_mean"], stats["coupled_std"], n)
    return uncoupled, coupled


def plot_stress_panel(uncoupled, coupled, outfile="figure3_panelA_stress"):
    fig, ax = plt.subplots(figsize=(7.6, 5.8))
    positions = [1, 2]
    colors = [COLOR_UNCOUPLED, COLOR_COUPLED]

    # Violin
    vp = ax.violinplot(
        [uncoupled, coupled], positions=positions, widths=0.42,
        showmeans=False, showmedians=False, showextrema=False,
    )
    for body, c in zip(vp["bodies"], colors):
        body.set_facecolor(c)
        body.set_edgecolor(c)
        body.set_alpha(VIOLIN_ALPHA)
        body.set_linewidth(ncs_style.LW_MAIN)

    # Boxplot
    bp = ax.boxplot(
        [uncoupled, coupled], positions=positions, widths=0.14,
        patch_artist=True, showfliers=False,
        medianprops=dict(linewidth=ncs_style.LW_MAIN),
        whiskerprops=dict(linewidth=ncs_style.LW_WHISKER),
        capprops=dict(linewidth=ncs_style.LW_WHISKER),
    )
    for patch, c in zip(bp["boxes"], colors):
        patch.set_facecolor(c)
        patch.set_alpha(BOX_ALPHA)
        patch.set_edgecolor(c)
        patch.set_linewidth(ncs_style.LW_MAIN)
    for i, c in enumerate(colors):
        bp["whiskers"][2 * i].set_color(c)
        bp["whiskers"][2 * i + 1].set_color(c)
        bp["caps"][2 * i].set_color(c)
        bp["caps"][2 * i + 1].set_color(c)
        bp["medians"][i].set_color(c)

    # Jitter scatter
    rng = np.random.default_rng(7)
    j1 = rng.normal(1.0 - 0.18, 0.035, len(uncoupled))
    j2 = rng.normal(2.0 - 0.18, 0.035, len(coupled))
    ax.scatter(j1, uncoupled, s=8, alpha=JITTER_ALPHA,
               color=COLOR_UNCOUPLED, edgecolors="none")
    ax.scatter(j2, coupled, s=8, alpha=JITTER_ALPHA,
               color=COLOR_COUPLED, edgecolors="none")

    # Quantile annotations
    annotate_quantiles(ax, 1, uncoupled, COLOR_UNCOUPLED, side="right")
    annotate_quantiles(ax, 2, coupled, COLOR_COUPLED, side="right")

    # Delta-mu arrow
    mu_u, mu_c = np.mean(uncoupled), np.mean(coupled)
    std_u, std_c = np.std(uncoupled, ddof=1), np.std(coupled, ddof=1)
    delta_mu = mu_c - mu_u
    spread_reduction = 1.0 - std_c / std_u

    ax.annotate(
        "", xy=(1.5, mu_c), xytext=(1.5, mu_u),
        arrowprops=dict(arrowstyle="-|>", lw=ncs_style.LW_MAIN,
                        color=ncs_style.GRAY_900),
    )
    ax.text(1.54, 0.5 * (mu_u + mu_c),
            f"$\\Delta\\mu$ = {delta_mu:.0f} MPa",
            va="center", ha="left",
            fontsize=ncs_style.FONT_ANNOTATION, color=ncs_style.GRAY_900)

    # Spread reduction
    q5_u = np.percentile(uncoupled, 5)
    q5_c = np.percentile(coupled, 5)
    ax.annotate(
        "", xy=(1.35, q5_c), xytext=(1.35, q5_u),
        arrowprops=dict(arrowstyle="<->", lw=ncs_style.LW_SECONDARY,
                        color=ncs_style.GRAY_900),
    )
    ax.text(1.38, 0.5 * (q5_u + q5_c),
            f"Spread reduced\nby ~{spread_reduction * 100:.0f}%",
            va="center", ha="left",
            fontsize=ncs_style.FONT_ANNOTATION, color=ncs_style.GRAY_900)

    ax.set_xticks(positions)
    ax.set_xticklabels(["Uncoupled pass", "Coupled steady state"])
    ax.set_ylabel("Max stress (MPa)")

    # Panel label — bold uppercase
    ax.text(-0.08, 1.06, "A", transform=ax.transAxes,
            fontsize=ncs_style.FONT_PANEL_LABEL, fontweight="bold",
            va="bottom", ha="right", color=ncs_style.GRAY_900)

    # Grid
    ax.grid(axis="y", linestyle=(0, (3, 3)), color=ncs_style.GRAY_100,
            linewidth=ncs_style.LW_GRID, alpha=0.8)
    ax.set_axisbelow(True)

    y_min = min(np.min(uncoupled), np.min(coupled))
    y_max = max(np.max(uncoupled), np.max(coupled))
    pad = 0.08 * (y_max - y_min)
    ax.set_ylim(y_min - pad, y_max + pad)

    fig.tight_layout()
    ncs_style.save_all(fig, outfile, OUTDIR)
    return fig, ax


if __name__ == "__main__":
    stats = load_real_data()
    print(f"Stress stats (predictive): "
          f"uncoupled {stats['decoupled_mean']:.1f}+/-{stats['decoupled_std']:.1f}, "
          f"coupled {stats['coupled_mean']:.1f}+/-{stats['coupled_std']:.1f}")

    uncoupled, coupled = generate_samples(stats)
    plot_stress_panel(uncoupled, coupled)
    plt.close("all")
