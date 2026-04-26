#!/usr/bin/env python3
"""
figure3_compose.py
==================
Compose all three panels (a, b, c) into a single Figure 3.
Draws directly — does not depend on exported images from individual scripts.

Data sources:
  - forward_uq_alloutput_predictive.csv  (summary stats)
  - forward_uq_alloutput.csv             (fallback)

Style: NCS palette — distinct per-panel color schemes.
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

# Colors — distinct per-panel color scheme
COLOR_UNCOUPLED = ncs_style.BLUE_MID       # #3B6B9A  blue
COLOR_COUPLED   = ncs_style.ACCENT_ORANGE  # #C4713B  orange/coral
COLOR_KEFF      = ncs_style.ACCENT_TEAL    # #2A7B6B  teal/green
COLOR_THERMAL   = ncs_style.ACCENT_RED     # #A63D40  red/crimson

VIOLIN_ALPHA = 0.18
BOX_ALPHA    = 0.30
JITTER_ALPHA = 0.12


def normal_pdf(x, mean, std):
    return (1.0 / (std * np.sqrt(2.0 * np.pi))) * np.exp(
        -0.5 * ((x - mean) / std) ** 2)


# --- data loading -----------------------------------------------------------

def load_all_stats():
    pred_csv = SCRIPT_DIR / "forward_uq_alloutput_predictive.csv"
    allout_csv = SCRIPT_DIR / "forward_uq_alloutput.csv"

    if pred_csv.exists():
        df = pd.read_csv(pred_csv)
        stress = df[df["label"] == "Peak stress (MPa)"].iloc[0]
        keff = df[df["label"] == "k_eff"].iloc[0]
        thermal = df[df["label"] == "Max fuel temp (K)"].iloc[0]
    else:
        df = pd.read_csv(allout_csv)
        stress = df[df["output"] == "max_global_stress"].iloc[0]
        keff = df[df["output"] == "keff"].iloc[0]
        thermal = df[df["output"] == "max_fuel_temp"].iloc[0]

    return {
        "stress_coupled_mean": stress["coupled_mean"],
        "stress_coupled_std": stress["coupled_std"],
        "stress_decoupled_mean": stress["decoupled_mean"],
        "stress_decoupled_std": stress["decoupled_std"],
        "keff_mean": keff["coupled_mean"],
        "keff_std": keff["coupled_std"],
        "thermal_coupled_mean": thermal["coupled_mean"],
        "thermal_coupled_std": thermal["coupled_std"],
    }


# --- Panel A -----------------------------------------------------------------

def draw_panel_A(ax, uncoupled, coupled):
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
    for pos, data, color in [(1, uncoupled, COLOR_UNCOUPLED),
                              (2, coupled, COLOR_COUPLED)]:
        q5, q50, q95 = np.percentile(data, [5, 50, 95])
        for y, lab in zip([q5, q50, q95], ["P5", "P50", "P95"]):
            ax.hlines(y, pos + 0.03, pos + 0.30, color=color,
                      linestyle=(0, (4, 3)),
                      linewidth=ncs_style.LW_SECONDARY)
            ax.text(pos + 0.32, y, f"{lab} = {y:.0f} MPa", color=color,
                    va="center", ha="left",
                    fontsize=ncs_style.FONT_ANNOTATION)

    # Delta-mu arrow
    mu_u, mu_c = np.mean(uncoupled), np.mean(coupled)
    std_u, std_c = np.std(uncoupled, ddof=1), np.std(coupled, ddof=1)
    delta = mu_c - mu_u
    reduction = 1.0 - std_c / std_u

    ax.annotate("", xy=(1.5, mu_c), xytext=(1.5, mu_u),
                arrowprops=dict(arrowstyle="-|>", lw=ncs_style.LW_MAIN,
                                color=ncs_style.GRAY_900))
    ax.text(1.54, 0.5 * (mu_u + mu_c),
            f"$\\Delta\\mu$ = {delta:.0f} MPa",
            va="center", ha="left",
            fontsize=ncs_style.FONT_ANNOTATION, color=ncs_style.GRAY_900)

    q5_u = np.percentile(uncoupled, 5)
    q5_c = np.percentile(coupled, 5)
    ax.text(1.36, min(q5_u, q5_c) + 16,
            f"Spread reduced\nby ~{reduction * 100:.0f}%",
            ha="left", va="center",
            fontsize=ncs_style.FONT_ANNOTATION, color=ncs_style.GRAY_900)

    ax.set_xticks([1, 2])
    ax.set_xticklabels(["Uncoupled pass", "Coupled steady state"])
    ax.set_ylabel("Max stress (MPa)")

    # Panel label — bold uppercase
    ax.text(-0.08, 1.06, "A", transform=ax.transAxes,
            fontsize=ncs_style.FONT_PANEL_LABEL, fontweight="bold",
            va="bottom", ha="right", color=ncs_style.GRAY_900)

    # Grid
    ax.grid(axis="y", linestyle=(0, (3, 3)), color=ncs_style.GRAY_100,
            linewidth=ncs_style.LW_GRID, alpha=0.75)
    ax.set_axisbelow(True)


# --- Panel B / C (density) ---------------------------------------------------

def draw_density_panel(ax, mean, std, color, xlabel, panel_letter, fmt_text):
    x = np.linspace(mean - 4 * std, mean + 4 * std, 800)
    pdf = normal_pdf(x, mean, std)
    p5 = mean - 1.645 * std
    p95 = mean + 1.645 * std

    ax.plot(x, pdf, color=color, lw=ncs_style.LW_MAIN)
    ax.fill_between(x, pdf, color=color, alpha=VIOLIN_ALPHA)
    ax.axvline(mean, color=color, lw=ncs_style.LW_MAIN)
    ax.axvline(p5, color=color, lw=ncs_style.LW_SECONDARY,
               linestyle=(0, (3, 3)))
    ax.axvline(p95, color=color, lw=ncs_style.LW_SECONDARY,
               linestyle=(0, (3, 3)))

    ax.set_xlabel(xlabel)
    ax.set_ylabel("Probability density")
    ax.set_yticks([])

    # Panel label — bold uppercase
    ax.text(-0.08, 1.06, panel_letter.upper(), transform=ax.transAxes,
            fontsize=ncs_style.FONT_PANEL_LABEL, fontweight="bold",
            va="bottom", ha="right", color=ncs_style.GRAY_900)

    # Grid
    ax.grid(axis="x", linestyle=(0, (3, 3)), color=ncs_style.GRAY_100,
            linewidth=ncs_style.LW_GRID, alpha=0.7)

    ax.text(mean + 0.9 * std, pdf.max() * 0.92, fmt_text,
            ha="left", va="top", color=ncs_style.GRAY_900,
            fontsize=ncs_style.FONT_ANNOTATION)


# --- main --------------------------------------------------------------------

if __name__ == "__main__":
    stats = load_all_stats()

    rng = np.random.default_rng(42)
    uncoupled_stress = rng.normal(
        stats["stress_decoupled_mean"], stats["stress_decoupled_std"], 4000)
    coupled_stress = rng.normal(
        stats["stress_coupled_mean"], stats["stress_coupled_std"], 4000)

    keff_mean = stats["keff_mean"]
    keff_std = stats["keff_std"]
    thermal_mean = stats["thermal_coupled_mean"]
    thermal_std = stats["thermal_coupled_std"]

    fig = plt.figure(figsize=(13.8, 5.8))
    gs = fig.add_gridspec(1, 3, width_ratios=[2.0, 1.15, 1.15], wspace=0.30)

    axA = fig.add_subplot(gs[0, 0])
    axB = fig.add_subplot(gs[0, 1])
    axC = fig.add_subplot(gs[0, 2])

    draw_panel_A(axA, uncoupled_stress, coupled_stress)

    keff_pcm = keff_std * 1e5
    draw_density_panel(
        axB, keff_mean, keff_std, COLOR_KEFF,
        xlabel=r"$k_{\mathrm{eff}}$",
        panel_letter="b",
        fmt_text=(f"Mean = {keff_mean:.5f}\n"
                  f"Std = {keff_std:.2e} (~{keff_pcm:.0f} pcm)\n"
                  f"(approximately Gaussian)"),
    )

    draw_density_panel(
        axC, thermal_mean, thermal_std, COLOR_THERMAL,
        xlabel="Max fuel temperature (K)",
        panel_letter="c",
        fmt_text=(f"Mean = {thermal_mean:.0f} K\n"
                  f"Std = {thermal_std:.1f} K\n"
                  f"P5 \u2013 P95 (central 90%)"),
    )

    fig.tight_layout()
    ncs_style.save_all(fig, "figure3_composed", OUTDIR)
    plt.close("all")
