"""Publication-grade visual style for bnn0414 manuscript figures.

Single source of truth for every visual parameter. Bank scripts and compose
scripts import from here; per-script rcParam overrides are forbidden.

Reference: STYLE_SPEC.md in this directory.
"""
from __future__ import annotations

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

# ─── dimensions ────────────────────────────────────────────────────────────
FIG_WIDTH_DOUBLE = 7.1       # double-column, inches
FIG_WIDTH_SINGLE = 3.46      # single-column, inches

# ─── semantic colour palette ──────────────────────────────────────────────
C = {
    "main":           "#2F5AA6",
    "main_light":     "#6b82b3",
    "scatter_bg":     "#D8E2F0",
    "reference":      "#707070",
    "posterior":       "#8c3a3a",
    "prior":          "#a9b8d6",
    "coupled":        "#2F5AA6",
    "uncoupled":      "#9a8a78",
    "ci_zero":        "#b0b0b0",
    "refline":        "#8E8E8E",
    "observed":       "#222222",
    "spine":          "#4A4A4A",
    "density_bg":     "#2F5AA6",
    "eb_line":        "#B7C7E2",
    "metric_text":    "#2F2F2F",
    "text":           "#2F2F2F",
    # parity plot overlays
    "linear_fit":     "#CC3333",
    "pi_band":        "#8BB8E8",
    # Sobol category colours
    "cat_elastic":    "#3A7D7B",     # teal — elastic / structural
    "cat_thermal":    "#D4853A",     # warm orange — thermal expansion
    "cat_conduct":    "#7B6BA5",     # muted purple — conductivity
    # model comparison
    "baseline":       "#2F5AA6",
    "mc_dropout":     "#E07B39",
    "deep_ensemble":  "#3A9A5B",
}
COLORS = C

# ─── alpha presets ─────────────────────────────────────────────────────────
A = {
    "scatter_fg":  0.70,
    "scatter_bg":  0.08,
    "density_bg":  0.15,
    "band":        0.18,
    "violin":      0.50,
    "errorbar":    0.50,
}
ALPHAS = A

# ─── line widths ───────────────────────────────────────────────────────────
LW = {
    "main":   1.2,
    "aux":    0.7,
    "ref":    0.7,
    "error":  0.5,
    "spine":  0.8,
}
LINEWIDTHS = LW

# ─── scatter defaults ─────────────────────────────────────────────────────
SCATTER = {
    "s":          6,
    "alpha":      A["scatter_fg"],
    "edgecolors": "none",
    "linewidths": 0,
}

# ─── font sizes ────────────────────────────────────────────────────────────
FS = {
    "tick":    7,
    "axis":    7.5,
    "title":   8,
    "panel":   8.5,
    "legend":  6.5,
    "metric":  6,
}
FONT_SIZES = FS

# ─── spacing ───────────────────────────────────────────────────────────────
PAD = {
    "title":    6,
    "label":    4,
    "hspace":   0.40,
    "wspace":   0.35,
    "tick_len": 4,
    "tick_minor": 2,
    "tick_w":   0.8,
}


def set_publication_rc() -> None:
    """Set rcParams once at script top; never call per-axis."""
    mpl.rcParams.update({
        "font.family":          "sans-serif",
        "font.sans-serif":      ["Arial", "Helvetica", "DejaVu Sans"],
        "font.size":            FS["axis"],

        "axes.spines.top":      False,
        "axes.spines.right":    False,
        "axes.linewidth":       LW["spine"],
        "axes.edgecolor":       C["spine"],
        "axes.labelsize":       FS["axis"],
        "axes.titlesize":       FS["title"],
        "axes.titlepad":        PAD["title"],
        "axes.labelpad":        PAD["label"],
        "axes.facecolor":       "white",
        "axes.grid":            False,

        "xtick.labelsize":      FS["tick"],
        "ytick.labelsize":      FS["tick"],
        "xtick.major.size":     PAD["tick_len"],
        "ytick.major.size":     PAD["tick_len"],
        "xtick.minor.size":     PAD["tick_minor"],
        "ytick.minor.size":     PAD["tick_minor"],
        "xtick.major.width":    PAD["tick_w"],
        "ytick.major.width":    PAD["tick_w"],
        "xtick.direction":      "out",
        "ytick.direction":      "out",

        "legend.fontsize":      FS["legend"],
        "legend.frameon":       False,
        "legend.handlelength":  1.2,
        "legend.columnspacing": 1.0,
        "legend.borderpad":     0.3,

        "figure.dpi":           150,
        "figure.facecolor":     "white",
        "savefig.dpi":          600,
        "savefig.bbox":         "tight",
        "savefig.facecolor":    "white",

        "pdf.fonttype":         42,
        "ps.fonttype":          42,
        "svg.fonttype":         "none",

        "lines.linewidth":      LW["main"],
        "errorbar.capsize":     1.5,
    })

apply_rc = set_publication_rc


def finalize_axes(ax) -> None:
    """Standard cleanup for any axis."""
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    for sp in ("left", "bottom"):
        ax.spines[sp].set_linewidth(LW["spine"])
        ax.spines[sp].set_color(C["spine"])

clean_ax = finalize_axes


def panel_label(ax, text: str, x: float = -0.12, y: float = 1.02) -> None:
    """Panel tag tight to frame corner, journal style."""
    ax.text(x, y, text, transform=ax.transAxes,
            fontsize=FS["panel"], fontweight="medium",
            va="bottom", ha="left", color="#3A3A3A")


def add_identity_line(ax, **kw) -> None:
    """y = x reference line spanning current axis limits."""
    lo = min(ax.get_xlim()[0], ax.get_ylim()[0])
    hi = max(ax.get_xlim()[1], ax.get_ylim()[1])
    defaults = dict(ls="--", lw=LW["ref"], color=C["refline"], zorder=1)
    defaults.update(kw)
    ax.plot([lo, hi], [lo, hi], **defaults)
    ax.set_xlim(lo, hi)
    ax.set_ylim(lo, hi)


def add_metric_text(ax, text: str, loc: str = "upper left") -> None:
    """Plain-text metric annotation (no box). Lightweight, readable."""
    anchor = {
        "upper left":  (0.06, 0.93, "left",  "top"),
        "upper right": (0.94, 0.93, "right", "top"),
        "lower left":  (0.06, 0.06, "left",  "bottom"),
        "lower right": (0.94, 0.06, "right", "bottom"),
    }
    x, y, ha, va = anchor[loc]
    ax.text(x, y, text, transform=ax.transAxes,
            fontsize=FS["metric"], fontweight="light", ha=ha, va=va,
            color="#505050", linespacing=1.2)


def density_underlay(ax, x, y, *, gridsize: int = 25,
                     cmap: str = "Blues", alpha: float | None = None):
    """Hexbin density background for parity plots."""
    _alpha = alpha if alpha is not None else A["density_bg"]
    ax.hexbin(x, y, gridsize=gridsize, cmap=cmap, alpha=_alpha,
              mincnt=1, linewidths=0, zorder=0)
