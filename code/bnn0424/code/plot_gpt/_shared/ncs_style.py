"""
NCS-style unified figure configuration.
All plot scripts import this module for consistent visual output.

Style target: Nature Computational Science / Nature Portfolio.
Palette: monochromatic blue-gray with muted accents.
"""

import matplotlib.pyplot as plt
import matplotlib as mpl

# ── Color palette (blue-gray monochrome + muted accents) ────────────────
BLUE_DARK   = "#1B3A5C"
BLUE_MID    = "#3B6B9A"
BLUE_LIGHT  = "#7BAFD4"
BLUE_PALE   = "#C5DAE9"
BLUE_WASH   = "#E8EFF5"

GRAY_900    = "#1A1A1A"
GRAY_700    = "#4A4A4A"
GRAY_500    = "#7A7A7A"
GRAY_300    = "#B0B0B0"
GRAY_100    = "#E8E8E8"
GRAY_BG     = "#F5F6F8"

ACCENT_TEAL   = "#2A7B6B"
ACCENT_ORANGE = "#C4713B"
ACCENT_RED    = "#A63D40"

PRIOR_COLOR     = GRAY_300
POSTERIOR_COLOR  = BLUE_MID
COUPLED_COLOR   = BLUE_MID
DECOUPLED_COLOR = GRAY_500
PI_COLOR        = BLUE_PALE
THRESHOLD_COLOR = ACCENT_RED

# Sobol-specific
SOBOL_STRESS_MAIN = BLUE_DARK
SOBOL_STRESS_BAND = BLUE_PALE
SOBOL_KEFF_MAIN   = ACCENT_ORANGE
SOBOL_KEFF_BAND   = "#F2D6BC"
SOBOL_MUTED       = GRAY_500

# ── Font sizes (pt, for final print at ~170mm width) ────────────────────
FONT_PANEL_LABEL = 9      # (a), (b), (c)
FONT_AXIS_LABEL  = 8
FONT_TICK_LABEL  = 7
FONT_LEGEND      = 7
FONT_ANNOTATION  = 7
FONT_METRIC      = 7      # R², RMSE, etc. (monospace)
FONT_TITLE       = 9      # subplot titles
FONT_SUPTITLE    = 11     # figure-level title (if any)

# ── Line widths ─────────────────────────────────────────────────────────
LW_MAIN     = 1.2
LW_SECONDARY = 0.8
LW_AXIS     = 0.8
LW_GRID     = 0.4
LW_ERRORBAR = 1.0
LW_WHISKER  = 0.8

# ── Marker ──────────────────────────────────────────────────────────────
MARKER_SIZE   = 12       # default scatter s=
MARKER_ALPHA  = 0.45

# ── Export ──────────────────────────────────────────────────────────────
EXPORT_DPI = 300
EXPORT_FORMATS = ("pdf", "svg", "png")


def apply_style():
    """Apply unified NCS rcParams globally."""
    mpl.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
        "font.size": FONT_TICK_LABEL,

        "axes.titlesize": FONT_TITLE,
        "axes.labelsize": FONT_AXIS_LABEL,
        "axes.linewidth": LW_AXIS,
        "axes.edgecolor": GRAY_700,
        "axes.labelcolor": GRAY_900,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.facecolor": "white",
        "axes.grid": False,

        "xtick.labelsize": FONT_TICK_LABEL,
        "ytick.labelsize": FONT_TICK_LABEL,
        "xtick.major.size": 3.5,
        "xtick.minor.size": 2.0,
        "ytick.major.size": 3.5,
        "ytick.minor.size": 2.0,
        "xtick.major.width": LW_AXIS,
        "ytick.major.width": LW_AXIS,
        "xtick.color": GRAY_700,
        "ytick.color": GRAY_700,

        "legend.fontsize": FONT_LEGEND,
        "legend.frameon": False,

        "figure.facecolor": "white",
        "figure.dpi": 150,
        "savefig.dpi": EXPORT_DPI,
        "savefig.bbox": "tight",
        "savefig.facecolor": "white",

        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "svg.fonttype": "none",

        "lines.linewidth": LW_MAIN,
        "lines.markersize": 4,
    })


def panel_label(ax, letter, x=-0.08, y=1.06):
    """Add (a)-style panel label at top-left of axes."""
    ax.text(x, y, f"({letter})", transform=ax.transAxes,
            fontsize=FONT_PANEL_LABEL, fontweight="bold",
            va="bottom", ha="right", color=GRAY_900)


def save_all(fig, stem, outdir):
    """Save figure in PDF, SVG, and PNG."""
    from pathlib import Path
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    for ext in EXPORT_FORMATS:
        fig.savefig(outdir / f"{stem}.{ext}",
                    dpi=EXPORT_DPI if ext == "png" else None)
    print(f"  Saved {stem} → {', '.join(EXPORT_FORMATS)}")


def metric_text(ax, text, x=0.04, y=0.96):
    """Add metric annotation (R², RMSE, etc.) in monospace."""
    ax.text(x, y, text, transform=ax.transAxes,
            fontsize=FONT_METRIC, va="top", ha="left",
            fontfamily="monospace", color=GRAY_900)
