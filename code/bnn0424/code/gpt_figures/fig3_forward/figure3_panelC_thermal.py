#!/usr/bin/env python3
"""
figure3_panelC_thermal.py
=========================
Panel C: Representative thermal output — max fuel temperature, coupled steady state.

Data source: forward_uq_alloutput_predictive.csv

Style: NCS palette — red/crimson accent.
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

COLOR = ncs_style.ACCENT_RED  # #A63D40  red/crimson


def normal_pdf(x, mean, std):
    return (1.0 / (std * np.sqrt(2.0 * np.pi))) * np.exp(
        -0.5 * ((x - mean) / std) ** 2)


def load_thermal_stats():
    """Load max fuel temp stats from predictive CSV."""
    pred_csv = SCRIPT_DIR / "forward_uq_alloutput_predictive.csv"
    if pred_csv.exists():
        df = pd.read_csv(pred_csv)
        row = df[df["label"] == "Max fuel temp (K)"].iloc[0]
        return (row["coupled_mean"], row["coupled_std"],
                row["decoupled_mean"], row["decoupled_std"])

    allout_csv = SCRIPT_DIR / "forward_uq_alloutput.csv"
    df = pd.read_csv(allout_csv)
    row = df[df["output"] == "max_fuel_temp"].iloc[0]
    return (row["coupled_mean"], row["coupled_std"],
            row["decoupled_mean"], row["decoupled_std"])


def plot_thermal_panel_from_stats(
    mean, std,
    xlabel="Max fuel temperature (K)",
    outfile="figure3_panelC_thermal",
):
    x = np.linspace(mean - 4 * std, mean + 4 * std, 800)
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

    # Stats text
    ax.text(
        mean + 0.9 * std, pdf.max() * 0.92,
        f"Mean = {mean:.0f} K\nStd = {std:.1f} K\n"
        f"P5 \u2013 P95 (central 90%)",
        ha="left", va="top", color=ncs_style.GRAY_900,
        fontsize=ncs_style.FONT_ANNOTATION,
    )

    ax.set_xlabel(xlabel)
    ax.set_ylabel("Probability density")
    ax.set_yticks([])

    # Panel label — bold uppercase
    ax.text(-0.08, 1.06, "C", transform=ax.transAxes,
            fontsize=ncs_style.FONT_PANEL_LABEL, fontweight="bold",
            va="bottom", ha="right", color=ncs_style.GRAY_900)

    # Grid
    ax.grid(axis="x", linestyle=(0, (3, 3)), color=ncs_style.GRAY_100,
            linewidth=ncs_style.LW_GRID, alpha=0.7)

    fig.tight_layout()
    ncs_style.save_all(fig, outfile, OUTDIR)
    return fig, ax


if __name__ == "__main__":
    c_mean, c_std, d_mean, d_std = load_thermal_stats()
    print(f"Max fuel temp (predictive): "
          f"coupled {c_mean:.1f}+/-{c_std:.1f} K, "
          f"decoupled {d_mean:.1f}+/-{d_std:.1f} K")
    plot_thermal_panel_from_stats(c_mean, c_std)
    plt.close("all")
