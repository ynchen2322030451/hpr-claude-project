#!/usr/bin/env python3
"""
figure3_panelB_keff.py
======================
Panel B: Coupled k_eff distribution (single density curve).

Data source: forward_uq_alloutput_predictive.csv or forward_uq_alloutput.csv

Style: NCS palette — teal/green accent.
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

COLOR = ncs_style.ACCENT_TEAL  # #2A7B6B  teal/green


def normal_pdf(x, mean, std):
    return (1.0 / (std * np.sqrt(2.0 * np.pi))) * np.exp(
        -0.5 * ((x - mean) / std) ** 2)


def load_keff_stats():
    """Load k_eff stats from predictive CSV, fall back to alloutput CSV."""
    pred_csv = SCRIPT_DIR / "forward_uq_alloutput_predictive.csv"
    if pred_csv.exists():
        df = pd.read_csv(pred_csv)
        row = df[df["label"] == "k_eff"].iloc[0]
        return row["coupled_mean"], row["coupled_std"]

    allout_csv = SCRIPT_DIR / "forward_uq_alloutput.csv"
    df = pd.read_csv(allout_csv)
    row = df[df["output"] == "keff"].iloc[0]
    return row["coupled_mean"], row["coupled_std"]


def plot_keff_panel_from_stats(
    mean, std,
    outfile="figure3_panelB_keff",
):
    xlim = (mean - 4 * std, mean + 4 * std)
    x = np.linspace(xlim[0], xlim[1], 800)
    pdf = normal_pdf(x, mean, std)

    p5 = mean - 1.645 * std
    p95 = mean + 1.645 * std

    fig, ax = plt.subplots(figsize=(4.8, 5.6))
    ax.plot(x, pdf, color=COLOR, lw=ncs_style.LW_MAIN)
    ax.fill_between(x, pdf, color=COLOR, alpha=0.18)

    ax.axvline(mean, color=COLOR, lw=ncs_style.LW_MAIN)
    ax.axvline(p5, color=COLOR, lw=ncs_style.LW_SECONDARY,
               linestyle=(0, (3, 3)))
    ax.axvline(p95, color=COLOR, lw=ncs_style.LW_SECONDARY,
               linestyle=(0, (3, 3)))

    # P5-P95 span annotation
    ax.annotate(
        "", xy=(p5, pdf.max() * 0.16), xytext=(p95, pdf.max() * 0.16),
        arrowprops=dict(arrowstyle="<->", lw=ncs_style.LW_SECONDARY,
                        color=COLOR),
    )
    ax.text(
        0.5 * (p5 + p95), pdf.max() * 0.08,
        "P5 \u2013 P95\n(central 90%)",
        ha="center", va="center", color=COLOR,
        fontsize=ncs_style.FONT_ANNOTATION,
    )

    # Stats text
    std_pcm = std * 1e5
    ax.text(
        mean + 1.15 * std, pdf.max() * 0.92,
        f"Mean = {mean:.5f}\nStd = {std:.2e} (~{std_pcm:.0f} pcm)\n"
        f"(approximately Gaussian)",
        ha="left", va="top", color=ncs_style.GRAY_900,
        fontsize=ncs_style.FONT_ANNOTATION,
    )

    ax.set_xlabel(r"$k_{\mathrm{eff}}$")
    ax.set_ylabel("Probability density")
    ax.set_yticks([])

    # Panel label — bold uppercase
    ax.text(-0.08, 1.06, "B", transform=ax.transAxes,
            fontsize=ncs_style.FONT_PANEL_LABEL, fontweight="bold",
            va="bottom", ha="right", color=ncs_style.GRAY_900)

    # Grid
    ax.grid(axis="x", linestyle=(0, (3, 3)), color=ncs_style.GRAY_100,
            linewidth=ncs_style.LW_GRID, alpha=0.7)

    fig.tight_layout()
    ncs_style.save_all(fig, outfile, OUTDIR)
    return fig, ax


def plot_keff_panel_from_samples(samples, **kwargs):
    mean = float(np.mean(samples))
    std = float(np.std(samples, ddof=1))
    return plot_keff_panel_from_stats(mean, std, **kwargs)


if __name__ == "__main__":
    mean, std = load_keff_stats()
    print(f"k_eff: mean={mean:.6f}, std={std:.2e} (~{std*1e5:.0f} pcm)")
    plot_keff_panel_from_stats(mean, std)
    plt.close("all")
