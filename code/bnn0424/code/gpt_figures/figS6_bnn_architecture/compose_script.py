"""Figure S6 — BNN architecture diagram.

Detailed view of the Bayesian Neural Network with:
- input layer (epistemic / aleatoric colour coding)
- hidden layers with weight-distribution visualisation
- output layer with uncertainty indicators
- physics regularisation annotation (monotonicity constraints)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib.lines import Line2D

_HERE = Path(__file__).resolve().parent
_FIG  = _HERE.parent
if str(_FIG) not in sys.path:
    sys.path.insert(0, str(_FIG))

from figure_style import set_publication_rc, C, FS, FIG_WIDTH_DOUBLE
from figure_io import savefig

_BNN0414 = _FIG.parents[1]
_OUT_DIR = _BNN0414 / "manuscript" / "0414_v4" / "figures"

# ─── colours ──────────────────────────────────────────────────────────────────
_C = {
    "epistemic":    "#3A7D7B",
    "aleatoric":    "#D4853A",
    "hidden":       "#2F5AA6",
    "output":       "#8c3a3a",
    "conn":         "#8BA3CC",
    "phys_box":     "#5A8A5A",
    "phys_bg":      "#E8F0E8",
    "gauss_fill":   "#2F5AA6",
    "dist_out":     "#8c3a3a",
    "text":         "#2F2F2F",
}

# ─── font sizes (all >= 6 pt) ────────────────────────────────────────────────
_FS = {
    "node_label":   5.8,
    "layer_title":  7.0,
    "gauss_label":  5.0,
    "phys_title":   6.5,
    "phys_body":    5.5,
    "output_dist":  5.0,
    "category":     5.8,
}

# ─── network layout ──────────────────────────────────────────────────────────
# x positions for each layer column
_X_INPUT  = 0.15
_X_H1     = 0.32
_X_H2     = 0.47
_X_H3     = 0.62
_X_OUTPUT = 0.80

# Input parameters — order: epistemic then aleatoric
_INPUTS_EPIST = [
    r"$E_\mathrm{intercept}$",
    r"$E_\mathrm{slope}$",
    r"$\nu$",
    r"$\alpha_\mathrm{base}$",
    r"$\alpha_\mathrm{slope}$",
]
_INPUTS_ALEAT = [
    r"$k_\mathrm{ref}$",
    r"$T_\mathrm{ref}$",
    r"$\alpha_\mathrm{SS316}$",
]
_INPUTS = _INPUTS_EPIST + _INPUTS_ALEAT

_OUTPUTS = [
    r"$\sigma_\mathrm{vM}^{\max}$",
    r"$k_\mathrm{eff}$",
    r"$T_\mathrm{fuel}^{\max}$",
    r"$T_\mathrm{mono}^{\max}$",
    r"$\Delta w$",
]

_OUTPUT_LONG = [
    "Max stress",
    "Criticality",
    "Max fuel temp",
    "Max mono. temp",
    "Wall expansion",
]

_N_HIDDEN = [7, 6, 7]   # nodes per hidden layer


def _y_positions(n: int, y_center: float = 0.52, spread: float = 0.60) -> np.ndarray:
    """Return evenly-spaced y positions centred on y_center."""
    return np.linspace(y_center + spread / 2,
                       y_center - spread / 2, n)


def _draw_node(ax, x, y, radius, color, edgecolor=None, alpha=1.0, lw=0.6):
    """Draw a single network node as a filled circle."""
    ec = edgecolor or color
    circle = plt.Circle((x, y), radius, fc=color, ec=ec,
                         lw=lw, alpha=alpha, zorder=5)
    ax.add_patch(circle)
    return circle


def _draw_gaussian(ax, cx, cy, w=0.015, h=0.012, color="#2F5AA6",
                   alpha=0.70):
    """Draw a tiny bell curve centred at (cx, cy)."""
    t = np.linspace(-2.5, 2.5, 60)
    g = np.exp(-0.5 * t ** 2)
    xs = cx + t * (w / 5)
    ys = cy + g * h - h * 0.1
    ax.fill_between(xs, cy - h * 0.1, ys, color=color, alpha=alpha,
                    zorder=8, linewidth=0)
    ax.plot(xs, ys, color=color, lw=0.5, alpha=min(1.0, alpha + 0.2),
            zorder=9)


def _draw_connections(ax, x_from, y_from, x_to, y_to,
                      color="#8BA3CC", alpha=0.12, lw=0.35):
    """Draw all-to-all connections between two layers."""
    for yf in y_from:
        for yt in y_to:
            ax.plot([x_from, x_to], [yf, yt],
                    color=color, alpha=alpha, lw=lw, zorder=1,
                    solid_capstyle="round")


def _draw_weight_distributions(ax, x_from, y_from, x_to, y_to,
                                indices, color="#2F5AA6"):
    """Draw small Gaussians on selected connections to show weight uncertainty.

    indices: list of (i_from, i_to) pairs to annotate.
    """
    for i_f, i_t in indices:
        yf, yt = y_from[i_f], y_to[i_t]
        # midpoint of connection
        mx = (x_from + x_to) / 2
        my = (yf + yt) / 2
        _draw_gaussian(ax, mx, my, w=0.018, h=0.012, color=color, alpha=0.75)


def build_figure():
    set_publication_rc()

    fig, ax = plt.subplots(figsize=(FIG_WIDTH_DOUBLE, 4.5))
    ax.set_xlim(-0.06, 1.04)
    ax.set_ylim(-0.08, 1.0)
    ax.set_aspect("auto")
    ax.axis("off")

    # --- node positions -------------------------------------------------------
    r_in  = 0.015
    r_hid = 0.012
    r_out = 0.015

    y_in  = _y_positions(len(_INPUTS), y_center=0.50, spread=0.68)
    y_h1  = _y_positions(_N_HIDDEN[0], y_center=0.50, spread=0.56)
    y_h2  = _y_positions(_N_HIDDEN[1], y_center=0.50, spread=0.46)
    y_h3  = _y_positions(_N_HIDDEN[2], y_center=0.50, spread=0.56)
    y_out = _y_positions(len(_OUTPUTS), y_center=0.50, spread=0.52)

    xs = [_X_INPUT, _X_H1, _X_H2, _X_H3, _X_OUTPUT]
    ys = [y_in, y_h1, y_h2, y_h3, y_out]

    # --- connections (draw first, behind nodes) --------------------------------
    conn_alpha = 0.10
    conn_lw    = 0.30
    for k in range(len(xs) - 1):
        _draw_connections(ax, xs[k], ys[k], xs[k + 1], ys[k + 1],
                          color=_C["conn"], alpha=conn_alpha, lw=conn_lw)

    # --- weight-distribution annotations on H1→H2 connections -----------------
    _gauss_pairs = [(1, 1), (3, 3), (5, 4)]
    _draw_weight_distributions(ax, _X_H1, y_h1, _X_H2, y_h2,
                                _gauss_pairs, color=_C["gauss_fill"])

    # small label for the Gaussians
    mid_x = (_X_H1 + _X_H2) / 2
    ax.annotate(
        r"$w_{ij} \sim \mathcal{N}(\mu, \sigma^2)$",
        xy=(mid_x, y_h1[-1] - 0.035),
        fontsize=_FS["gauss_label"], color=_C["text"],
        ha="center", va="top", style="italic",
    )

    # --- draw nodes -----------------------------------------------------------
    # Input layer
    n_epist = len(_INPUTS_EPIST)
    for i, (label, y) in enumerate(zip(_INPUTS, y_in)):
        col = _C["epistemic"] if i < n_epist else _C["aleatoric"]
        _draw_node(ax, _X_INPUT, y, r_in, col, alpha=0.85)
        ax.text(_X_INPUT - 0.025, y, label,
                fontsize=_FS["node_label"], ha="right", va="center",
                color=_C["text"])

    # Hidden layers
    for hx, hy_arr, n in zip([_X_H1, _X_H2, _X_H3], [y_h1, y_h2, y_h3],
                              _N_HIDDEN):
        for y in hy_arr:
            _draw_node(ax, hx, y, r_hid, _C["hidden"], alpha=0.70)

    # Output layer
    for i, (y, sym, desc) in enumerate(zip(y_out, _OUTPUTS, _OUTPUT_LONG)):
        _draw_node(ax, _X_OUTPUT, y, r_out, _C["output"], alpha=0.85)
        # symbol label to the right
        ax.text(_X_OUTPUT + 0.025, y + 0.008, sym,
                fontsize=_FS["node_label"], ha="left", va="center",
                color=_C["output"], fontweight="medium")
        # description below symbol
        ax.text(_X_OUTPUT + 0.025, y - 0.014, desc,
                fontsize=_FS["output_dist"] - 0.3, ha="left", va="center",
                color="#666666")

    # --- output distributions (small bell curves to the right of outputs) -----
    for y in y_out:
        _draw_gaussian(ax, _X_OUTPUT + 0.14, y, w=0.016, h=0.010,
                       color=_C["dist_out"], alpha=0.55)
    # mu +/- sigma label
    ax.text(_X_OUTPUT + 0.14, y_out[-1] - 0.045,
            r"$\hat{y} = \mu \pm \sigma$",
            fontsize=_FS["output_dist"], ha="center", va="top",
            color=_C["output"], style="italic")

    # --- layer titles ---------------------------------------------------------
    y_title = 0.94
    for lx, label in [(_X_INPUT, "Input\nparameters"),
                       ((_X_H1 + _X_H3) / 2, "Hidden layers\n(Bayesian)"),
                       (_X_OUTPUT, "Output\nquantities")]:
        ax.text(lx, y_title, label, fontsize=_FS["layer_title"],
                ha="center", va="top", color=_C["text"],
                fontweight="medium", linespacing=1.25)

    # Probabilistic predictions label
    ax.text(_X_OUTPUT + 0.14, y_title, "Predictive\ndistribution",
            fontsize=_FS["layer_title"] - 0.5, ha="center", va="top",
            color=_C["output"], fontweight="medium", linespacing=1.25)

    # --- input category legends (epistemic / aleatoric) -----------------------
    # place legend in the bottom-right corner
    y_leg = -0.04
    x_leg = 0.75
    for label, col, dy in [("Epistemic (nuclear data)", _C["epistemic"], 0.0),
                            ("Aleatoric (manufacturing)", _C["aleatoric"], -0.035)]:
        dot = plt.Circle((x_leg, y_leg + dy), 0.006, fc=col, ec=col,
                          lw=0.4, zorder=10)
        ax.add_patch(dot)
        ax.text(x_leg + 0.012, y_leg + dy, label,
                fontsize=_FS["category"], ha="left", va="center",
                color=col, fontweight="medium", zorder=10)


    # --- physics regularisation box -------------------------------------------
    phys_x = 0.28
    phys_y = -0.06
    phys_w = 0.40
    phys_h = 0.12

    phys_box = FancyBboxPatch(
        (phys_x, phys_y), phys_w, phys_h,
        boxstyle="round,pad=0.012",
        fc=_C["phys_bg"], ec=_C["phys_box"],
        lw=0.8, ls="--", zorder=4, alpha=0.85,
    )
    ax.add_patch(phys_box)

    # title inside box
    ax.text(phys_x + phys_w / 2, phys_y + phys_h - 0.018,
            "Physics-informed regularisation",
            fontsize=_FS["phys_title"], ha="center", va="top",
            color=_C["phys_box"], fontweight="bold")

    # constraint equation
    ax.text(phys_x + phys_w / 2, phys_y + phys_h / 2 - 0.012,
            r"Monotonicity: $\frac{\partial \hat{y}_j}{\partial x_i} \geq 0$"
            "  for specified $(i,j)$ pairs",
            fontsize=_FS["phys_body"], ha="center", va="center",
            color=_C["text"])

    # Arrow from physics box up to hidden layer region
    arr_start_x = phys_x + phys_w / 2
    arr_start_y = phys_y + phys_h
    arr_end_y   = y_h3[-1] - 0.025

    ax.annotate(
        "", xy=(arr_start_x, arr_end_y),
        xytext=(arr_start_x, arr_start_y + 0.005),
        arrowprops=dict(
            arrowstyle="-|>",
            color=_C["phys_box"],
            lw=0.8,
            ls="--",
            mutation_scale=8,
        ),
        zorder=6,
    )

    # Small label on arrow
    ax.text(arr_start_x + 0.015, (arr_start_y + arr_end_y) / 2,
            r"$\mathcal{L}_\mathrm{phys}$",
            fontsize=_FS["gauss_label"], color=_C["phys_box"],
            ha="left", va="center", style="italic")

    return fig


def main():
    fig = build_figure()
    written = savefig(fig, "figS6_bnn_architecture", _OUT_DIR)
    for p in written:
        print(f"  wrote {p}")


if __name__ == "__main__":
    main()
