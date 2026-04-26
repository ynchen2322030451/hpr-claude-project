from __future__ import annotations

import sys
from pathlib import Path
from typing import List, Tuple

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import FancyBboxPatch
import numpy as np

# =========================
# Figure 4: Sobol separation (NCS style)
# =========================
# Panels A+B side-by-side (Sobol bar charts),
# Panel C (dominant-factor separation summary),
# shared legend below.
#
# Recommended usage:
#   python figure4_sobol_separation.py
#
# Output structure:
#   outputs/
#       panel_A_stress.svg/png/pdf
#       panel_B_keff.svg/png/pdf
#       panel_C_summary.svg/png/pdf
#       legend_only.svg/png/pdf
#       figure4_full.svg/png/pdf

# ── Shared style ────────────────────────────────────────────────────────
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "_shared"))
import ncs_style
ncs_style.apply_style()


# -------------------------
# User-editable data section
# -------------------------
PARAM_ORDER = [
    r"$E$ intercept",
    r"$E$ slope",
    r"$\nu$",
    r"$\alpha$ base",
    r"$\alpha$ slope",
    r"$k$ reference",
    r"$T$ reference",
    r"$\alpha_{diff}$",
]

# Example values approximating the mock figure.
# Replace with your true results.
STRESS_DATA = {
    "s1": np.array([0.579, 0.053, 0.030, 0.169, 0.037, 0.030, 0.008, 0.002]),
    "st": np.array([0.85, 0.25, 0.10, 0.38, 0.17, 0.14, 0.07, 0.06]),
    "ci_low": np.array([0.46, -0.005, -0.010, 0.08, -0.01, -0.01, -0.03, -0.03]),
    "ci_high": np.array([0.72, 0.11, 0.06, 0.31, 0.08, 0.05, 0.09, 0.05]),
}

KEFF_DATA = {
    "s1": np.array([-0.001, 0.010, -0.014, 0.785, 0.179, 0.015, 0.007, 0.000]),
    "st": np.array([0.00, 0.28, 0.00, 0.94, 0.38, 0.18, 0.09, 0.00]),
    "ci_low": np.array([-0.06, -0.03, -0.06, 0.66, 0.08, -0.03, -0.03, -0.05]),
    "ci_high": np.array([0.12, 0.08, 0.09, 0.91, 0.28, 0.08, 0.07, 0.08]),
}

EXPORT_DIR = Path(__file__).resolve().parent / "outputs"


# -------------------------
# Utilities
# -------------------------
def is_ci_cross_zero(ci_low: float, ci_high: float) -> bool:
    return (ci_low <= 0.0) and (ci_high >= 0.0)


# -------------------------
# Panel A / B
# -------------------------
def draw_sobol_panel(
    ax: plt.Axes,
    params: List[str],
    s1: np.ndarray,
    st: np.ndarray,
    ci_low: np.ndarray,
    ci_high: np.ndarray,
    panel_title: str,
    main_color: str,
    band_color: str,
    xlim: Tuple[float, float] = (-0.12, 1.02),
) -> None:
    n = len(params)
    y = np.arange(n)[::-1]

    ax.set_xlim(*xlim)
    ax.set_ylim(-0.8, n - 0.2)
    ax.axvline(0.0, color=ncs_style.GRAY_300, lw=0.8, ls="--", zorder=0)

    # Background total-effect bands
    for yi, sti in zip(y, st):
        if sti > 0:
            ax.barh(yi, sti, left=0, height=0.55,
                    color=band_color, edgecolor="none", zorder=1)

    # Foreground first-order points + CI
    for yi, s1i, lo, hi in zip(y, s1, ci_low, ci_high):
        muted = is_ci_cross_zero(lo, hi)
        color = ncs_style.SOBOL_MUTED if muted else main_color
        ax.errorbar(
            x=s1i, y=yi,
            xerr=[[max(0, s1i - lo)], [max(0, hi - s1i)]],
            fmt="o", ms=5, color=color, ecolor=color,
            elinewidth=ncs_style.LW_ERRORBAR, capsize=3, zorder=3,
        )

    ax.set_yticks(y)
    ax.set_yticklabels(params)
    ax.tick_params(axis="y", length=0)
    ax.set_xlabel("Sobol index")

    # numeric S1 labels on right margin
    xr = xlim[1] - 0.02
    for yi, s1i, lo, hi in zip(y, s1, ci_low, ci_high):
        muted = is_ci_cross_zero(lo, hi)
        color = ncs_style.SOBOL_MUTED if muted else main_color
        ax.text(xr, yi, f"{s1i:.3f}", ha="right", va="center",
                color=color, fontsize=ncs_style.FONT_ANNOTATION)

    ax.text(
        xr, n - 0.15, r"$S_1$ (90% CI)",
        ha="right", va="bottom", color=main_color,
        fontsize=ncs_style.FONT_AXIS_LABEL, fontweight="bold",
    )

    # Simple bold title (replaces colored ribbon header)
    ax.set_title(panel_title, fontsize=ncs_style.FONT_TITLE,
                 fontweight="bold", color=ncs_style.GRAY_900, pad=10)


# -------------------------
# Legend (shared)
# -------------------------
def make_legend_handles():
    """Return legend handles using NCS palette."""
    return [
        Line2D([0], [0], color=ncs_style.SOBOL_STRESS_BAND, lw=10,
               solid_capstyle="butt", label=r"Total-effect ($S_T$)"),
        Line2D([0], [0], marker="o", color=ncs_style.SOBOL_STRESS_MAIN,
               lw=0, markersize=5, label=r"First-order ($S_1$)"),
        Line2D([0], [0], color=ncs_style.SOBOL_STRESS_MAIN, lw=ncs_style.LW_ERRORBAR,
               marker="|", markersize=6, label=r"90% CI ($S_1$)"),
        Line2D([0], [0], marker="o", color=ncs_style.SOBOL_MUTED,
               lw=0, markersize=5, label=r"$S_1$ 90% CI spans zero"),
    ]


def make_legend_only() -> plt.Figure:
    fig = plt.figure(figsize=(7.0, 0.6))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis("off")
    handles = make_legend_handles()
    leg = ax.legend(
        handles=handles, loc="center", ncol=4,
        frameon=False, handlelength=2.5, columnspacing=1.5,
    )
    return fig


# -------------------------
# Panel C: Dominant-factor separation summary
# -------------------------
def draw_panel_c(ax: plt.Axes) -> None:
    """Draw the dominant-factor separation summary as a schematic panel."""
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    # Outer rounded border
    outer = FancyBboxPatch(
        (0.01, 0.02), 0.98, 0.94,
        boxstyle="round,pad=0.015",
        facecolor="white", edgecolor=ncs_style.GRAY_300,
        linewidth=ncs_style.LW_MAIN, zorder=0,
    )
    ax.add_patch(outer)

    # ── Dashed vertical separators ──
    for xsep in [0.32, 0.68]:
        ax.plot([xsep, xsep], [0.06, 0.90], ls="--",
                color=ncs_style.GRAY_300, lw=ncs_style.LW_SECONDARY,
                zorder=1, clip_on=False)

    fs_title = ncs_style.FONT_TITLE
    fs_body = ncs_style.FONT_ANNOTATION
    fs_label = ncs_style.FONT_AXIS_LABEL

    # ── LEFT column: Stress ──
    left_cx = 0.165
    # Title box (blue)
    title_box_stress = FancyBboxPatch(
        (0.04, 0.78), 0.25, 0.14,
        boxstyle="round,pad=0.012",
        facecolor=ncs_style.BLUE_WASH, edgecolor=ncs_style.BLUE_MID,
        linewidth=ncs_style.LW_SECONDARY, zorder=2,
    )
    ax.add_patch(title_box_stress)
    ax.text(left_cx, 0.85, "Coupled maximum\nstress",
            ha="center", va="center", fontsize=fs_title,
            fontweight="bold", color=ncs_style.BLUE_DARK, zorder=3)

    # Top-2 factors
    ax.text(left_cx, 0.72, r"Top-2 dominant factors (by $S_1$):",
            ha="center", va="center", fontsize=fs_body,
            color=ncs_style.GRAY_900, fontstyle="italic", zorder=3)
    ax.text(left_cx, 0.59, r"1.  $E$ intercept  ($S_1 \approx 0.58$)",
            ha="center", va="center", fontsize=fs_body,
            color=ncs_style.BLUE_DARK, fontweight="bold", zorder=3)
    ax.text(left_cx, 0.48, r"2.  $\alpha$ base  ($S_1 \approx 0.17$)",
            ha="center", va="center", fontsize=fs_body,
            color=ncs_style.BLUE_DARK, zorder=3)

    # Pathway label
    pathway_box_stress = FancyBboxPatch(
        (0.04, 0.22), 0.25, 0.12,
        boxstyle="round,pad=0.010",
        facecolor=ncs_style.BLUE_PALE, edgecolor="none", zorder=2,
    )
    ax.add_patch(pathway_box_stress)
    ax.text(left_cx, 0.28, "Elastic-constitutive\npathway",
            ha="center", va="center", fontsize=fs_label,
            fontweight="bold", color=ncs_style.BLUE_DARK, zorder=3)

    # ── CENTER column: separation arrow ──
    center_cx = 0.50
    ax.text(center_cx, 0.72, "Distinct dominant pathways\nfor two key outputs",
            ha="center", va="center", fontsize=fs_label,
            fontweight="bold", color=ncs_style.GRAY_900, zorder=3)

    # Double arrow
    ax.annotate(
        "", xy=(0.37, 0.55), xytext=(0.63, 0.55),
        arrowprops=dict(arrowstyle="<->", color=ncs_style.GRAY_700,
                        lw=ncs_style.LW_MAIN * 1.5),
        zorder=3,
    )

    # ── RIGHT column: keff ──
    right_cx = 0.835
    # Title box (orange)
    title_box_keff = FancyBboxPatch(
        (0.71, 0.78), 0.25, 0.14,
        boxstyle="round,pad=0.012",
        facecolor="#FDF2E9", edgecolor=ncs_style.ACCENT_ORANGE,
        linewidth=ncs_style.LW_SECONDARY, zorder=2,
    )
    ax.add_patch(title_box_keff)
    ax.text(right_cx, 0.85, r"$k_\mathrm{eff}$ (coupled)",
            ha="center", va="center", fontsize=fs_title,
            fontweight="bold", color=ncs_style.ACCENT_ORANGE, zorder=3)

    # Top-2 factors
    ax.text(right_cx, 0.72, r"Top-2 dominant factors (by $S_1$):",
            ha="center", va="center", fontsize=fs_body,
            color=ncs_style.GRAY_900, fontstyle="italic", zorder=3)
    ax.text(right_cx, 0.59, r"1.  $\alpha$ base  ($S_1 \approx 0.79$)",
            ha="center", va="center", fontsize=fs_body,
            color=ncs_style.ACCENT_ORANGE, fontweight="bold", zorder=3)
    ax.text(right_cx, 0.48, r"2.  $\alpha$ slope  ($S_1 \approx 0.18$)",
            ha="center", va="center", fontsize=fs_body,
            color=ncs_style.ACCENT_ORANGE, zorder=3)

    # Pathway label
    pathway_box_keff = FancyBboxPatch(
        (0.71, 0.22), 0.25, 0.12,
        boxstyle="round,pad=0.010",
        facecolor="#F2D6BC", edgecolor="none", zorder=2,
    )
    ax.add_patch(pathway_box_keff)
    ax.text(right_cx, 0.28, "Thermal-expansion\npathway",
            ha="center", va="center", fontsize=fs_label,
            fontweight="bold", color=ncs_style.ACCENT_ORANGE, zorder=3)

    # ── Interpretation bullets (bottom band) ──
    ax.text(center_cx, 0.12,
            ("Interpretation:  Different material-property groups dominate "
             "stress vs. reactivity, confirming pathway separation."),
            ha="center", va="center", fontsize=fs_body,
            color=ncs_style.GRAY_700, fontstyle="italic", zorder=3,
            wrap=True)


# -------------------------
# Full figure: A+B side-by-side, panel C below, shared legend at bottom
# -------------------------
def make_full_figure() -> plt.Figure:
    fig = plt.figure(figsize=(7.0, 5.8))

    gs = fig.add_gridspec(
        nrows=3, ncols=2,
        height_ratios=[1.0, 0.38, 0.06],
        width_ratios=[1, 1],
        hspace=0.40, wspace=0.50,
    )

    # Panel A — stress
    axA = fig.add_subplot(gs[0, 0])
    draw_sobol_panel(
        axA, PARAM_ORDER,
        STRESS_DATA["s1"], STRESS_DATA["st"],
        STRESS_DATA["ci_low"], STRESS_DATA["ci_high"],
        panel_title="Coupled steady-state max stress",
        main_color=ncs_style.SOBOL_STRESS_MAIN,
        band_color=ncs_style.SOBOL_STRESS_BAND,
    )
    ncs_style.panel_label(axA, "A")

    # Panel B — keff
    axB = fig.add_subplot(gs[0, 1])
    draw_sobol_panel(
        axB, PARAM_ORDER,
        KEFF_DATA["s1"], KEFF_DATA["st"],
        KEFF_DATA["ci_low"], KEFF_DATA["ci_high"],
        panel_title=r"$k_\mathrm{eff}$ (coupled)",
        main_color=ncs_style.SOBOL_KEFF_MAIN,
        band_color=ncs_style.SOBOL_KEFF_BAND,
    )
    ncs_style.panel_label(axB, "B")

    # Panel C — dominant-factor separation summary
    axC = fig.add_subplot(gs[1, :])
    draw_panel_c(axC)
    ncs_style.panel_label(axC, "C", x=-0.03, y=1.04)

    # Shared legend below all panels
    ax_leg = fig.add_subplot(gs[2, :])
    ax_leg.axis("off")
    handles = make_legend_handles()
    ax_leg.legend(
        handles=handles, loc="center", ncol=4,
        frameon=False, handlelength=2.5, columnspacing=1.5,
    )

    return fig


# -------------------------
# Export wrappers
# -------------------------
def export_panel_A() -> None:
    fig, ax = plt.subplots(figsize=(3.5, 3.2))
    draw_sobol_panel(
        ax, PARAM_ORDER,
        STRESS_DATA["s1"], STRESS_DATA["st"],
        STRESS_DATA["ci_low"], STRESS_DATA["ci_high"],
        panel_title="Coupled steady-state max stress",
        main_color=ncs_style.SOBOL_STRESS_MAIN,
        band_color=ncs_style.SOBOL_STRESS_BAND,
    )
    ncs_style.panel_label(ax, "A")
    ncs_style.save_all(fig, "panel_A_stress", EXPORT_DIR)
    plt.close(fig)


def export_panel_B() -> None:
    fig, ax = plt.subplots(figsize=(3.5, 3.2))
    draw_sobol_panel(
        ax, PARAM_ORDER,
        KEFF_DATA["s1"], KEFF_DATA["st"],
        KEFF_DATA["ci_low"], KEFF_DATA["ci_high"],
        panel_title=r"$k_\mathrm{eff}$ (coupled)",
        main_color=ncs_style.SOBOL_KEFF_MAIN,
        band_color=ncs_style.SOBOL_KEFF_BAND,
    )
    ncs_style.panel_label(ax, "B")
    ncs_style.save_all(fig, "panel_B_keff", EXPORT_DIR)
    plt.close(fig)


def export_panel_C() -> None:
    fig, ax = plt.subplots(figsize=(7.0, 2.2))
    draw_panel_c(ax)
    ncs_style.panel_label(ax, "c", x=-0.03, y=1.04)
    ncs_style.save_all(fig, "panel_C_summary", EXPORT_DIR)
    plt.close(fig)


def export_legend_only() -> None:
    fig = make_legend_only()
    ncs_style.save_all(fig, "legend_only", EXPORT_DIR)
    plt.close(fig)


def export_full_figure() -> None:
    fig = make_full_figure()
    ncs_style.save_all(fig, "figure4_full", EXPORT_DIR)
    plt.close(fig)


# -------------------------
# Main
# -------------------------
def main() -> None:
    export_panel_A()
    export_panel_B()
    export_panel_C()
    export_legend_only()
    export_full_figure()
    print(f"Exported files to: {EXPORT_DIR.resolve()}")


if __name__ == "__main__":
    main()
