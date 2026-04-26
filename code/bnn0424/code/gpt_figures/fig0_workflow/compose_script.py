"""Figure 0 — Workflow schematic for the BNN surrogate paper.

Horizontal flow: Input Uncertainties → Coupled HF Solver → BNN Surrogate
→ Outputs → Analysis branches.

No embedded raster images. Pure vector diagram using FancyBboxPatch and
matplotlib annotate arrows.
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

_HERE = Path(__file__).resolve().parent
_FIG  = _HERE.parent
if str(_FIG) not in sys.path:
    sys.path.insert(0, str(_FIG))

from figure_style import set_publication_rc, FIG_WIDTH_DOUBLE
from figure_io import savefig

_BNN0414 = _FIG.parents[1]
_OUT_DIR = _BNN0414 / "manuscript" / "0414_v4" / "figures"

# ─── colour palette ─────────────────────────────────────────────────────────
_PAL = {
    "epistemic_bg":   "#E8EEF6",  "epistemic_bd":   "#7B9FCC",
    "aleatoric_bg":   "#F6E8E8",  "aleatoric_bd":   "#CC7B7B",
    "hf_bg":          "#FDF2E0",  "hf_bd":          "#D4A85C",
    "bnn_bg":         "#E0EDF6",  "bnn_bd":         "#6B9BC4",
    "output_bg":      "#E4F2E4",  "output_bd":      "#6BAA6B",
    "analysis_bg":    "#F0F4FA",  "analysis_bd":    "#A0B4CC",
}

# ─── font sizes (all ≥ 6pt) ─────────────────────────────────────────────────
_FS_TITLE = 7.5
_FS_BODY  = 6.5
_FS_NOTE  = 6.0
_FS_ARROW = 6.0

# ─── helpers ─────────────────────────────────────────────────────────────────

def _box(ax, xy, w, h, bg, bd, lw=0.8, rounding=0.02):
    """Draw a FancyBboxPatch and return it."""
    patch = FancyBboxPatch(
        xy, w, h,
        boxstyle=f"round,pad={rounding}",
        facecolor=bg, edgecolor=bd, linewidth=lw,
        transform=ax.transData, zorder=2,
    )
    ax.add_patch(patch)
    return patch


def _txt(ax, x, y, text, *, fs=_FS_BODY, weight="normal", ha="center",
         va="center", color="#2F2F2F", **kw):
    ax.text(x, y, text, fontsize=fs, fontweight=weight,
            ha=ha, va=va, color=color, zorder=5, **kw)


def _arrow_solid(ax, x0, y0, x1, y1, *, label="", color="black", lw=1.0):
    """Solid data-flow arrow."""
    ax.annotate(
        "", xy=(x1, y1), xytext=(x0, y0),
        arrowprops=dict(
            arrowstyle="-|>", color=color, lw=lw,
            shrinkA=2, shrinkB=2,
        ),
        zorder=3,
    )
    if label:
        mx, my = 0.5 * (x0 + x1), 0.5 * (y0 + y1)
        _txt(ax, mx, my + 0.035, label, fs=_FS_ARROW, style="italic",
             color="#404040")


def _arrow_dashed(ax, x0, y0, x1, y1, *, color="#2F5AA6", lw=0.8):
    """Dashed probabilistic-flow arrow."""
    ax.annotate(
        "", xy=(x1, y1), xytext=(x0, y0),
        arrowprops=dict(
            arrowstyle="-|>", color=color, lw=lw,
            linestyle="dashed", shrinkA=2, shrinkB=2,
        ),
        zorder=3,
    )


def _arrow_dotted(ax, x0, y0, x1, y1, *, color="#888888", lw=0.7):
    """Dotted validation arrow."""
    ax.annotate(
        "", xy=(x1, y1), xytext=(x0, y0),
        arrowprops=dict(
            arrowstyle="-|>", color=color, lw=lw,
            linestyle="dotted", shrinkA=2, shrinkB=2,
        ),
        zorder=3,
    )


# ─── main compose ───────────────────────────────────────────────────────────

def compose():
    set_publication_rc()

    fig, ax = plt.subplots(1, 1, figsize=(FIG_WIDTH_DOUBLE, 3.2))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    # ── column x-anchors (left edge of each box) ────────────────────────────
    x_inp = 0.01        # input uncertainties
    w_inp = 0.16
    x_hf  = 0.22        # HF solver
    w_hf  = 0.17
    x_bnn = 0.44        # BNN surrogate
    w_bnn = 0.17
    x_out = 0.66        # outputs
    w_out = 0.13
    x_ana = 0.83        # analysis
    w_ana = 0.155

    # ── vertical anchors ────────────────────────────────────────────────────
    # Inputs: two sub-boxes stacked inside an outer frame
    y_inp_top = 0.88
    y_inp_bot = 0.22
    h_epi = 0.32
    h_ale = 0.22
    y_epi = y_inp_top - h_epi          # 0.56
    y_ale = y_inp_bot                   # 0.22
    gap_sub = 0.02

    # HF, BNN, Outputs: centered vertically
    y_mid_bot = 0.30
    h_mid     = 0.48

    # Analysis: four small boxes stacked
    h_ana_box = 0.115
    ana_gap   = 0.035
    y_ana_top = 0.85

    # ====================================================================
    # 1. INPUT UNCERTAINTIES — outer frame + two sub-boxes
    # ====================================================================
    _box(ax, (x_inp - 0.005, y_inp_bot - 0.01), w_inp + 0.01,
         y_inp_top - y_inp_bot + 0.02,
         bg="white", bd="#B0B0B0", lw=0.5, rounding=0.015)
    _txt(ax, x_inp + w_inp / 2, y_inp_top + 0.03,
         "Input Uncertainties", fs=_FS_TITLE, weight="bold")

    # Structural mechanics sub-box
    _box(ax, (x_inp, y_epi), w_inp, h_epi,
         bg=_PAL["epistemic_bg"], bd=_PAL["epistemic_bd"])
    _txt(ax, x_inp + w_inp / 2, y_epi + h_epi - 0.04,
         "Structural mechanics", fs=_FS_NOTE, weight="medium")
    epi_lines = [
        r"$E_\mathrm{intercept}$, $E_\mathrm{slope}$, $\nu$",
    ]
    for i, line in enumerate(epi_lines):
        _txt(ax, x_inp + w_inp / 2, y_epi + h_epi - 0.09 - i * 0.045,
             line, fs=_FS_NOTE, ha="center")

    # Thermal deformation / transport sub-box
    _box(ax, (x_inp, y_ale), w_inp, h_ale,
         bg=_PAL["aleatoric_bg"], bd=_PAL["aleatoric_bd"])
    _txt(ax, x_inp + w_inp / 2, y_ale + h_ale - 0.04,
         "Thermal deform. / transport", fs=_FS_NOTE, weight="medium")
    ale_lines = [
        r"$\alpha_\mathrm{base}$, $\alpha_\mathrm{slope}$",
        r"$k_\mathrm{ref}$, $T_\mathrm{ref}$, $k_\mathrm{slope}$",
    ]
    for i, line in enumerate(ale_lines):
        _txt(ax, x_inp + w_inp / 2, y_ale + h_ale - 0.09 - i * 0.045,
             line, fs=_FS_NOTE, ha="center")

    # ====================================================================
    # 2. COUPLED HF SOLVER
    # ====================================================================
    _box(ax, (x_hf, y_mid_bot), w_hf, h_mid,
         bg=_PAL["hf_bg"], bd=_PAL["hf_bd"])
    _txt(ax, x_hf + w_hf / 2, y_mid_bot + h_mid - 0.06,
         "Coupled HF Solver", fs=_FS_TITLE, weight="bold")
    _txt(ax, x_hf + w_hf / 2, y_mid_bot + h_mid - 0.13,
         "OpenMC\u2013FEniCS", fs=_FS_BODY, color="#555555")
    _txt(ax, x_hf + w_hf / 2, y_mid_bot + h_mid - 0.22,
         "Uncoupled pass", fs=_FS_NOTE, color="#666666")
    _txt(ax, x_hf + w_hf / 2, y_mid_bot + h_mid - 0.28,
         r"$\downarrow$", fs=_FS_NOTE, color="#666666")
    _txt(ax, x_hf + w_hf / 2, y_mid_bot + h_mid - 0.34,
         "Coupled steady state", fs=_FS_NOTE, color="#666666")
    _txt(ax, x_hf + w_hf / 2, y_mid_bot + 0.05,
         r"$n = 3{,}418$ simulations", fs=_FS_NOTE,
         color="#777777", style="italic")

    # ====================================================================
    # 3. BNN SURROGATE
    # ====================================================================
    _box(ax, (x_bnn, y_mid_bot), w_bnn, h_mid,
         bg=_PAL["bnn_bg"], bd=_PAL["bnn_bd"])
    _txt(ax, x_bnn + w_bnn / 2, y_mid_bot + h_mid - 0.06,
         "BNN Surrogate", fs=_FS_TITLE, weight="bold")
    _txt(ax, x_bnn + w_bnn / 2, y_mid_bot + h_mid - 0.13,
         "Bayesian neural network", fs=_FS_BODY, color="#555555")
    _txt(ax, x_bnn + w_bnn / 2, y_mid_bot + h_mid / 2 - 0.01,
         r"$p(\mathbf{y} \mid \boldsymbol{\theta}, \mathcal{D})$",
         fs=8.5, color="#2F5AA6")
    _txt(ax, x_bnn + w_bnn / 2, y_mid_bot + 0.05,
         "multi-output", fs=_FS_NOTE, color="#777777", style="italic")

    # ====================================================================
    # 4. OUTPUTS
    # ====================================================================
    _box(ax, (x_out, y_mid_bot), w_out, h_mid,
         bg=_PAL["output_bg"], bd=_PAL["output_bd"])
    _txt(ax, x_out + w_out / 2, y_mid_bot + h_mid - 0.06,
         "Outputs", fs=_FS_TITLE, weight="bold")
    out_lines = [
        r"$\sigma_\mathrm{vM}$ (max stress)",
        r"$k_\mathrm{eff}$",
        "Max fuel temp",
        "Max monolith temp",
        "Wall expansion",
    ]
    for i, line in enumerate(out_lines):
        _txt(ax, x_out + w_out / 2,
             y_mid_bot + h_mid - 0.15 - i * 0.065,
             line, fs=_FS_NOTE)

    # ====================================================================
    # 5. ANALYSIS BRANCHES
    # ====================================================================
    analysis_items = [
        ("Forward UQ", "MC propagation"),
        ("Sobol Sensitivity", r"$S_1$, $S_T$ indices"),
        ("Posterior Calibration", "MH\u2013MCMC"),
        ("HF Consistency", "Spot-check"),
    ]
    ana_ys = []
    for i, (title, subtitle) in enumerate(analysis_items):
        y_a = y_ana_top - i * (h_ana_box + ana_gap)
        ana_ys.append(y_a)
        _box(ax, (x_ana, y_a), w_ana, h_ana_box,
             bg=_PAL["analysis_bg"], bd=_PAL["analysis_bd"])
        _txt(ax, x_ana + w_ana / 2, y_a + h_ana_box / 2 + 0.015,
             title, fs=_FS_NOTE + 0.5, weight="medium")
        _txt(ax, x_ana + w_ana / 2, y_a + h_ana_box / 2 - 0.025,
             subtitle, fs=_FS_NOTE, color="#666666")

    # ====================================================================
    # ARROWS — data flow (solid black)
    # ====================================================================
    # Input → HF
    y_arrow = y_mid_bot + h_mid / 2
    _arrow_solid(ax, x_inp + w_inp, y_arrow, x_hf, y_arrow,
                 label="8 inputs")
    # HF → BNN
    _arrow_solid(ax, x_hf + w_hf, y_arrow, x_bnn, y_arrow,
                 label="train")
    # BNN → Outputs
    _arrow_solid(ax, x_bnn + w_bnn, y_arrow, x_out, y_arrow,
                 label="predict")

    # ====================================================================
    # ARROWS — probabilistic flow (dashed blue) FROM BNN to analysis boxes
    # The BNN posterior predictive distribution is the shared object on
    # which all three analyses operate — arrows should radiate from BNN.
    # ====================================================================
    x_bnn_right = x_bnn + w_bnn
    for i in range(3):
        y_a_mid = ana_ys[i] + h_ana_box / 2
        _arrow_dashed(ax, x_bnn_right, y_arrow, x_ana, y_a_mid)

    # ====================================================================
    # ARROW — validation flow (dotted gray) to HF Consistency
    # This one originates from the Outputs column (HF spot-check)
    # ====================================================================
    x_out_right = x_out + w_out
    y_hf_con_mid = ana_ys[3] + h_ana_box / 2
    _arrow_dotted(ax, x_out_right, y_arrow, x_ana, y_hf_con_mid)

    # ====================================================================
    # LEGEND at bottom
    # ====================================================================
    legend_y = 0.08
    legend_items = [
        (0.22, "Data flow",          dict(color="black", lw=1.0, ls="-")),
        (0.44, "Probabilistic flow", dict(color="#2F5AA6", lw=0.8, ls="--")),
        (0.66, "Validation",         dict(color="#888888", lw=0.7, ls=":")),
    ]
    for lx, label_text, style_kw in legend_items:
        ax.plot([lx, lx + 0.07], [legend_y, legend_y],
                **style_kw, zorder=4, clip_on=False)
        # arrowhead
        ax.annotate(
            "", xy=(lx + 0.07, legend_y), xytext=(lx + 0.06, legend_y),
            arrowprops=dict(
                arrowstyle="-|>",
                color=style_kw["color"],
                lw=style_kw["lw"],
            ),
            zorder=4,
        )
        _txt(ax, lx + 0.08, legend_y, label_text,
             fs=_FS_NOTE, ha="left", va="center", color="#555555")

    fig.subplots_adjust(left=0.01, right=0.99, top=0.96, bottom=0.02)

    written = savefig(fig, "fig0_workflow", _OUT_DIR)
    for p in written:
        print(f"  wrote: {p}")


if __name__ == "__main__":
    compose()
