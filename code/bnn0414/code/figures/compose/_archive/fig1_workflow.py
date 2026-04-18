"""Figure 1 — Probabilistic analysis pipeline of the coupled HPR workflow.

Rich workflow schematic with embedded CAD inset, neural-network icon,
mini analysis icons, and professional visual hierarchy.

Phase-1 rulings enforced:
  * Only "uncoupled pass" / "coupled steady state" on figure face.
  * No threshold gate, no feasible-region checkmark, no old-surrogate
    upgrade arrow, no "HeteroMLP", no iter1/iter2.
  * No CJK text anywhere.
  * Data flow = solid arrow; distribution flow = dashed blue arrow.
  * HF consistency = side branch, dotted grey arrow.
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.image as mpimg
import numpy as np
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

_HERE = Path(__file__).resolve().parent
_FIG = _HERE.parent
if str(_FIG) not in sys.path:
    sys.path.insert(0, str(_FIG))

from figure_style import set_publication_rc, C, FS, LW, FIG_WIDTH_DOUBLE
from figure_io import savefig

_BNN0414 = _FIG.parents[1]
_OUT_DIR = _BNN0414 / "manuscript" / "0414_v4" / "figures"
_CAD_IMG = Path("/Users/yinuo/Projects/hpr-claude-project"
                "/code/0411/figures/core_cad_render.png")

# ── colour palette ──────────────────────────────────────────────────────────
C_EPIST   = "#D6EAF8"   # light blue — epistemic inputs
C_ALEAT   = "#FADBD8"   # light pink — aleatoric inputs
C_HF      = "#FDEBD0"   # warm cream — HF solver
C_BNN     = "#D4E6F1"   # medium blue — BNN surrogate
C_OUTPUT  = "#D5F5E3"   # light green — output list
C_ANAL    = "#EBF5FB"   # pale blue — analysis boxes
C_HF_CHK  = "#F0F0F0"   # light grey — HF consistency
C_EDGE    = "#555555"
C_ARROW   = "#333333"
C_DIST    = C["main"]   # blue — probabilistic flow


# ── helper: rounded box with header bar ─────────────────────────────────────
def _box(ax, x, y, w, h, fc=C_EPIST, ec=C_EDGE, lw=0.8, radius=0.08,
         zorder=2, alpha=1.0):
    """Draw a FancyBboxPatch; return patch for reference."""
    p = FancyBboxPatch(
        (x, y), w, h,
        boxstyle=f"round,pad={radius}", fc=fc, ec=ec, lw=lw,
        zorder=zorder, alpha=alpha,
    )
    ax.add_patch(p)
    return p


def _header_box(ax, x, y, w, h, title, fc, header_fc=None):
    """Box with a coloured header strip at top."""
    _box(ax, x, y, w, h, fc=fc)
    if header_fc is None:
        # darken the fill slightly for the header
        import matplotlib.colors as mcolors
        rgb = np.array(mcolors.to_rgb(fc))
        header_fc = mcolors.to_hex(rgb * 0.85)
    # header strip (manually drawn rectangle at top)
    hh = 0.28
    ax.fill_between([x + 0.06, x + w - 0.06], y + h - hh, y + h - 0.04,
                    color=header_fc, zorder=3, alpha=0.6)
    ax.text(x + w / 2, y + h - hh / 2 - 0.02, title,
            ha="center", va="center", fontsize=FS["title"],
            fontweight="bold", color="#2F2F2F", zorder=4)


def _arrow(ax, x1, y1, x2, y2, color=C_ARROW, lw=1.2, ls="-",
           style="-|>", shrinkA=3, shrinkB=3, zorder=5):
    """Annotate-based arrow."""
    ax.annotate(
        "", xy=(x2, y2), xytext=(x1, y1),
        arrowprops=dict(arrowstyle=style, color=color, lw=lw, ls=ls,
                        shrinkA=shrinkA, shrinkB=shrinkB),
        zorder=zorder,
    )


def _bullet_list(ax, x, y, items, fontsize=6.0, dy=0.22, color="#2F2F2F"):
    """Render a left-aligned list with bullet points."""
    for i, txt in enumerate(items):
        ax.text(x, y - i * dy, txt,
                ha="left", va="center", fontsize=fontsize,
                color=color, zorder=4)


# ── mini icons ──────────────────────────────────────────────────────────────
def _draw_nn_icon(ax, cx, cy, scale=0.18):
    """Draw a tiny 3-layer neural network icon."""
    layers = [3, 5, 3]
    xs = [cx - scale, cx, cx + scale]
    positions = []
    for li, (nx, lx) in enumerate(zip(layers, xs)):
        ys = np.linspace(cy - scale * 0.7 * (nx - 1) / 2,
                         cy + scale * 0.7 * (nx - 1) / 2, nx)
        positions.append([(lx, yy) for yy in ys])
    # connections
    for l in range(len(layers) - 1):
        for (x1, y1) in positions[l]:
            for (x2, y2) in positions[l + 1]:
                ax.plot([x1, x2], [y1, y2], color="#8899BB", lw=0.3,
                        zorder=3, alpha=0.5)
    # nodes
    for layer in positions:
        for (nx, ny) in layer:
            ax.plot(nx, ny, "o", color=C["main"], markersize=2.5,
                    markeredgewidth=0.3, markeredgecolor="white", zorder=4)


def _draw_bell_curve(ax, cx, cy, w=0.25, h=0.12):
    """Tiny bell curve icon."""
    t = np.linspace(-2.5, 2.5, 50)
    pdf = np.exp(-t**2 / 2)
    ax.plot(cx + t / 5 * w, cy + pdf * h - h * 0.1,
            color=C["main"], lw=0.8, zorder=4)
    ax.fill_between(cx + t / 5 * w, cy - h * 0.1,
                    cy + pdf * h - h * 0.1,
                    color=C["main"], alpha=0.15, zorder=3)


def _draw_bar_icon(ax, cx, cy, w=0.22, h=0.10):
    """Tiny horizontal bars icon for Sobol."""
    bars_y = [cy + h * 0.6, cy, cy - h * 0.6]
    widths = [w * 0.9, w * 0.55, w * 0.35]
    for by, bw in zip(bars_y, widths):
        ax.barh(by, bw, height=h * 0.45, left=cx - w / 2,
                color=C["cat_elastic"], alpha=0.7, edgecolor="none",
                zorder=4)


def _draw_posterior_icon(ax, cx, cy, w=0.25, h=0.12):
    """Prior (wide, faded) -> posterior (narrow, dark) shift icon."""
    t = np.linspace(-3, 3, 50)
    prior = np.exp(-t**2 / 4)
    post = np.exp(-(t - 0.3)**2 / 0.6)
    ax.plot(cx + t / 6 * w, cy + prior * h * 0.6 - h * 0.1,
            color=C["prior"], lw=0.6, zorder=3, alpha=0.7)
    ax.plot(cx + t / 6 * w, cy + post * h - h * 0.1,
            color=C["posterior"], lw=0.8, zorder=4)


# ── main figure ─────────────────────────────────────────────────────────────
def main() -> None:
    set_publication_rc()

    fig, ax = plt.subplots(figsize=(FIG_WIDTH_DOUBLE, 4.0))
    ax.set_xlim(-0.2, 13.0)
    ax.set_ylim(-0.4, 4.2)
    ax.axis("off")

    # ====================================================================
    # LEFT SECTION: Input Uncertainties
    # ====================================================================
    # Outer container
    _box(ax, 0.0, 0.2, 2.55, 3.7, fc="#F4F7FC", ec="#AABBCC", lw=0.6)
    ax.text(1.275, 3.75, "Input Uncertainties",
            ha="center", va="center", fontsize=FS["title"],
            fontweight="bold", color="#2F2F2F", zorder=4)

    # Epistemic sub-box
    _box(ax, 0.12, 2.0, 2.30, 1.70, fc=C_EPIST, ec="#8AAED0", lw=0.5)
    ax.text(1.27, 3.48, "Epistemic (nuclear data)",
            ha="center", va="center", fontsize=6.5,
            fontweight="bold", color="#2F5AA6", zorder=4)
    epist_items = [
        r"$X_1$: $E_\mathrm{intercept}$",
        r"$X_2$: $E_\mathrm{slope}$",
        r"$X_3$: $\nu$",
        r"$X_4$: $\alpha_\mathrm{base}$",
        r"$X_5$: $\alpha_\mathrm{slope}$",
    ]
    _bullet_list(ax, 0.35, 3.18, epist_items, fontsize=6.0, dy=0.22)

    # Aleatoric sub-box
    _box(ax, 0.12, 0.35, 2.30, 1.45, fc=C_ALEAT, ec="#D4A0A0", lw=0.5)
    ax.text(1.27, 1.58, "Aleatoric (manufacturing)",
            ha="center", va="center", fontsize=6.5,
            fontweight="bold", color="#8B3A3A", zorder=4)
    aleat_items = [
        r"$M_1$: SS316 $k_\mathrm{ref}$",
        r"$M_2$: SS316 $T_\mathrm{ref}$",
        r"$M_3$: SS316 $\alpha$",
    ]
    _bullet_list(ax, 0.35, 1.30, aleat_items, fontsize=6.0, dy=0.22,
                 color="#5A2A2A")

    # ====================================================================
    # CENTER-LEFT: Coupled HF Solver
    # ====================================================================
    hf_x, hf_y, hf_w, hf_h = 3.2, 0.8, 2.4, 3.0
    _header_box(ax, hf_x, hf_y, hf_w, hf_h,
                "Coupled HF Solver", fc=C_HF, header_fc="#E8C98E")
    ax.text(hf_x + hf_w / 2, hf_y + hf_h - 0.50,
            "OpenMC\u2013FEniCS",
            ha="center", va="center", fontsize=6.5,
            color="#6B5B3A", style="italic", zorder=4)

    # Embed CAD render
    if _CAD_IMG.exists():
        img = mpimg.imread(str(_CAD_IMG))
        # inset axes for the image
        # position in figure coords
        img_w, img_h = 0.16, 0.32
        # Convert data coords to figure fraction for inset
        # Use ax.transData to get pixel coords, then fig.transFigure.inverted()
        p1 = ax.transData.transform((hf_x + 0.35, hf_y + 0.55))
        p2 = ax.transData.transform((hf_x + hf_w - 0.35, hf_y + hf_h - 0.65))
        inv = fig.transFigure.inverted()
        fp1 = inv.transform(p1)
        fp2 = inv.transform(p2)
        axins = fig.add_axes([fp1[0], fp1[1], fp2[0] - fp1[0],
                              fp2[1] - fp1[1]])
        axins.imshow(img)
        axins.axis("off")
        # thin border
        for spine in axins.spines.values():
            spine.set_visible(True)
            spine.set_edgecolor("#CCBBAA")
            spine.set_linewidth(0.5)

    # Sub-labels below image
    ax.text(hf_x + hf_w / 2, hf_y + 0.32,
            "Uncoupled pass  \u2192  Coupled steady state",
            ha="center", va="center", fontsize=5.5,
            color="#888888", style="italic", zorder=4)

    # Sample count
    ax.text(hf_x + hf_w / 2, hf_y + 0.10,
            r"$n \approx 2\,900$ simulations",
            ha="center", va="center", fontsize=5.5,
            color="#999999", zorder=4)

    # ====================================================================
    # CENTER: BNN Surrogate
    # ====================================================================
    bnn_x, bnn_y, bnn_w, bnn_h = 6.2, 0.8, 2.2, 3.0
    _header_box(ax, bnn_x, bnn_y, bnn_w, bnn_h,
                "BNN Surrogate", fc=C_BNN, header_fc="#9AB8D8")
    ax.text(bnn_x + bnn_w / 2, bnn_y + bnn_h - 0.48,
            "Bayesian neural network",
            ha="center", va="center", fontsize=6.0,
            color="#3A5A8A", style="italic", zorder=4)

    # NN icon
    _draw_nn_icon(ax, bnn_x + bnn_w / 2, bnn_y + bnn_h / 2 + 0.15,
                  scale=0.45)

    # predictive distribution label
    ax.text(bnn_x + bnn_w / 2, bnn_y + 0.42,
            r"$p(\mathbf{y}\,|\,\boldsymbol{\theta},\,\mathcal{D})$",
            ha="center", va="center", fontsize=7.5,
            color="#2F5AA6", zorder=4)

    # multi-output subtitle
    ax.text(bnn_x + bnn_w / 2, bnn_y + 0.12,
            "multi-output",
            ha="center", va="center", fontsize=5.5,
            color="#888888", zorder=4)

    # ====================================================================
    # CENTER-RIGHT: Outputs
    # ====================================================================
    out_x, out_y, out_w, out_h = 8.9, 1.2, 2.1, 2.3
    _box(ax, out_x, out_y, out_w, out_h, fc=C_OUTPUT, ec="#7DBB8E", lw=0.6)
    ax.text(out_x + out_w / 2, out_y + out_h - 0.15, "Outputs",
            ha="center", va="center", fontsize=FS["title"],
            fontweight="bold", color="#2A6B3A", zorder=4)

    output_items = [
        r"$\sigma_\mathrm{vM}$ (pin-by-pin stress)",
        r"$k_\mathrm{eff}$",
        "Max fuel temp",
        "Max monolith temp",
        "Wall expansion",
    ]
    _bullet_list(ax, out_x + 0.18, out_y + out_h - 0.55,
                 output_items, fontsize=5.8, dy=0.30, color="#2A4A2A")

    # ====================================================================
    # RIGHT: Analysis branches (stacked)
    # ====================================================================
    anal_x = 11.35
    anal_w = 1.55
    anal_h = 0.60
    analyses = [
        (3.35, "Forward UQ",     "MC propagation",       _draw_bell_curve,     C_ANAL,  C_DIST, "--"),
        (2.55, "Sobol sensitivity", r"$S_1, S_T$ indices", _draw_bar_icon,      C_ANAL,  C_DIST, "--"),
        (1.75, "Posterior calib.", "MH\u2013MCMC",        _draw_posterior_icon, C_ANAL,  C_DIST, "--"),
        (0.95, "HF consistency",  "Spot-check",           None,                 C_HF_CHK, "#AAAAAA", ":"),
    ]

    for (by, title, sub, icon_fn, fc, arr_c, arr_ls) in analyses:
        _box(ax, anal_x, by, anal_w, anal_h, fc=fc,
             ec="#AABBCC" if fc != C_HF_CHK else "#CCCCCC", lw=0.5)
        # title
        ty = by + anal_h - 0.17
        ax.text(anal_x + 0.38, ty, title,
                ha="left", va="center",
                fontsize=6.0, fontweight="bold",
                color="#2F2F2F" if fc != C_HF_CHK else "#999999",
                zorder=4)
        # subtitle
        ax.text(anal_x + 0.38, ty - 0.20, sub,
                ha="left", va="center", fontsize=5.2,
                color="#666666" if fc != C_HF_CHK else "#AAAAAA",
                zorder=4)
        # icon
        if icon_fn is not None:
            icon_fn(ax, anal_x + 0.18, by + anal_h / 2)

        # arrow from outputs box to analysis box
        _arrow(ax, out_x + out_w, out_y + out_h / 2,
               anal_x, by + anal_h / 2,
               color=arr_c,
               lw=0.8 if fc != C_HF_CHK else 0.5,
               ls=arr_ls)

    # ====================================================================
    # ARROWS: main data flow
    # ====================================================================
    # Inputs -> HF solver
    _arrow(ax, 2.55, 2.3, hf_x, 2.3, color=C_ARROW, lw=1.2)

    # HF solver -> BNN
    _arrow(ax, hf_x + hf_w, 2.3, bnn_x, 2.3, color=C_ARROW, lw=1.2)

    # BNN -> Outputs
    _arrow(ax, bnn_x + bnn_w, 2.3, out_x, 2.3, color=C_ARROW, lw=1.2)

    # ====================================================================
    # Flow labels on arrows
    # ====================================================================
    ax.text((2.55 + hf_x) / 2, 2.46, "8 inputs",
            ha="center", va="bottom", fontsize=5.0, color="#666666",
            zorder=4)
    ax.text((hf_x + hf_w + bnn_x) / 2, 2.46, "train",
            ha="center", va="bottom", fontsize=5.0, color="#666666",
            zorder=4)
    ax.text((bnn_x + bnn_w + out_x) / 2, 2.46, "predict",
            ha="center", va="bottom", fontsize=5.0, color="#666666",
            zorder=4)

    # ====================================================================
    # Legend for arrow types
    # ====================================================================
    leg_y = -0.15
    # solid
    ax.annotate("", xy=(7.0, leg_y), xytext=(6.4, leg_y),
                arrowprops=dict(arrowstyle="-|>", color=C_ARROW, lw=1.0))
    ax.text(7.15, leg_y, "Data flow", fontsize=5.0, va="center",
            color="#444444")
    # dashed blue
    ax.annotate("", xy=(9.0, leg_y), xytext=(8.4, leg_y),
                arrowprops=dict(arrowstyle="-|>", color=C_DIST, lw=0.8,
                                ls="--"))
    ax.text(9.15, leg_y, "Probabilistic flow", fontsize=5.0, va="center",
            color="#444444")
    # dotted grey
    ax.annotate("", xy=(11.2, leg_y), xytext=(10.6, leg_y),
                arrowprops=dict(arrowstyle="-|>", color="#AAAAAA", lw=0.6,
                                ls=":"))
    ax.text(11.35, leg_y, "Validation (optional)", fontsize=5.0,
            va="center", color="#999999")

    # ====================================================================
    # Save
    # ====================================================================
    written = savefig(fig, "fig1_workflow", _OUT_DIR)
    for w in written:
        print("wrote", w)


if __name__ == "__main__":
    main()
