"""
Figure 1 — Workflow overview (v2, visual-rich).

4-column layout matching gpt样板图:
  (A) Uncertain SS316 material-property priors — with mini distribution curves
  (B) Coupled high-fidelity simulation — OpenMC + FEniCS schematic
  (C) Unified Bayesian posterior predictive layer — BNN architecture + output densities
  (D) Downstream analyses — 3 application thumbnails

Each column is a separate subplot for easy PPT extraction.
"""
import sys
from pathlib import Path
import numpy as np
from scipy import stats

_SHARED = str(Path(__file__).resolve().parent.parent / "_shared")
if _SHARED not in sys.path:
    sys.path.insert(0, _SHARED)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle
from matplotlib.lines import Line2D
import matplotlib.gridspec as gridspec
import ncs_style

ncs_style.apply_style()

HERE = Path(__file__).resolve().parent
OUTDIR = HERE / "outputs"
OUTDIR.mkdir(exist_ok=True)

# ── Colors ──
C_BOX_BG   = "#EDF2F8"
C_BOX_EDGE = "#B8CBDC"
C_BLUE     = ncs_style.BLUE_MID
C_DARK     = ncs_style.BLUE_DARK
C_ORANGE   = ncs_style.ACCENT_ORANGE
C_TEAL     = ncs_style.ACCENT_TEAL
C_RED      = ncs_style.ACCENT_RED
C_GRAY     = ncs_style.GRAY_500
C_LGRAY    = ncs_style.GRAY_100
C_TEXT     = ncs_style.GRAY_900

# ── Input parameters for (A) ──
PARAM_GROUPS = [
    {"label": "Elasticity",
     "color": C_BLUE,
     "params": [
         (r"$E_\mathrm{intercept}$", 200, 20),
         (r"$E_\mathrm{slope}$", -70, 7),
         (r"$\nu$", 0.31, 0.031),
     ]},
    {"label": "Thermal expansion",
     "color": C_ORANGE,
     "params": [
         (r"$\alpha_\mathrm{base}$", 10, 1),
         (r"$\alpha_\mathrm{slope}$", 5, 0.5),
     ]},
    {"label": "Thermal transport",
     "color": C_TEAL,
     "params": [
         (r"$k_\mathrm{ref}$", 23.2, 2.3),
         (r"$T_\mathrm{ref}$", 923, 92),
         (r"$\alpha_\mathrm{SS316}$", 0.013, 0.001),
     ]},
]


def rounded_box(ax, xy, w, h, fc=C_BOX_BG, ec=C_BOX_EDGE, lw=0.8):
    box = FancyBboxPatch(xy, w, h,
                         boxstyle="round,pad=0.015,rounding_size=0.02",
                         facecolor=fc, edgecolor=ec, linewidth=lw, zorder=0)
    ax.add_patch(box)


def draw_mini_gaussian(ax, x0, y0, w, h, color, n_pts=80):
    x = np.linspace(-3, 3, n_pts)
    y = stats.norm.pdf(x)
    ax.plot(x0 + x / 6 * w, y0 + y / y.max() * h * 0.9,
            color=color, lw=0.9, solid_capstyle="round")
    ax.fill_between(x0 + x / 6 * w, y0, y0 + y / y.max() * h * 0.9,
                    color=color, alpha=0.15)


def connect_columns(fig, ax_from, ax_to, y_frac=0.5):
    from matplotlib.patches import FancyArrowPatch
    p1 = ax_from.transData.transform((1.0, y_frac))
    p2 = ax_to.transData.transform((0.0, y_frac))
    p1_fig = fig.transFigure.inverted().transform(p1)
    p2_fig = fig.transFigure.inverted().transform(p2)
    arrow = FancyArrowPatch(
        p1_fig, p2_fig,
        transform=fig.transFigure,
        arrowstyle="-|>", mutation_scale=14,
        lw=1.5, color=C_GRAY, shrinkA=8, shrinkB=8,
        clip_on=False)
    fig.patches.append(arrow)


# ═══════════════════════════════════════════════════════════════
# BUILD FIGURE
# ═══════════════════════════════════════════════════════════════

fig = plt.figure(figsize=(16, 5.5))

# 4 main columns + small gaps for arrows
gs = fig.add_gridspec(1, 4, width_ratios=[0.9, 1.1, 1.2, 1.0],
                      left=0.02, right=0.98, top=0.88, bottom=0.12,
                      wspace=0.08)

# ───────────────────────────────────────────────────────────────
# (A) Uncertain SS316 material-property priors
# ───────────────────────────────────────────────────────────────
ax_A = fig.add_subplot(gs[0])
ax_A.set_xlim(0, 1)
ax_A.set_ylim(0, 1)
ax_A.axis("off")

rounded_box(ax_A, (0.02, 0.02), 0.96, 0.96)
ax_A.text(0.5, 0.95, "(A) Uncertain SS316\nmaterial-property priors",
          ha="center", va="top", fontsize=8.5, fontweight="bold", color=C_DARK)

y_cursor = 0.82
for grp in PARAM_GROUPS:
    ax_A.text(0.08, y_cursor, grp["label"],
              fontsize=7, fontweight="bold", color=grp["color"], va="top")
    y_cursor -= 0.04
    for pname, pmean, pstd in grp["params"]:
        draw_mini_gaussian(ax_A, 0.12, y_cursor - 0.06, 0.30, 0.055, grp["color"])
        ax_A.text(0.48, y_cursor - 0.035, pname,
                  fontsize=6.5, color=C_TEXT, va="center")
        y_cursor -= 0.075
    y_cursor -= 0.02

ax_A.text(0.5, 0.08, "Gaussian priors, 10% CoV",
          ha="center", va="center", fontsize=6.5, color=C_GRAY, fontstyle="italic")

# ───────────────────────────────────────────────────────────────
# (B) Coupled high-fidelity simulation
# ───────────────────────────────────────────────────────────────
ax_B = fig.add_subplot(gs[1])
ax_B.set_xlim(0, 1)
ax_B.set_ylim(0, 1)
ax_B.axis("off")

rounded_box(ax_B, (0.02, 0.02), 0.96, 0.96)
ax_B.text(0.5, 0.95, "(B) Coupled high-fidelity simulation\nOpenMC + FEniCS",
          ha="center", va="top", fontsize=8.5, fontweight="bold", color=C_DARK)

# Uncoupled pass box
rounded_box(ax_B, (0.06, 0.58), 0.88, 0.28, fc="#F0F4F8", ec=C_BLUE)
ax_B.text(0.50, 0.83, "1. Uncoupled pass",
          ha="center", va="center", fontsize=7.5, fontweight="bold", color=C_BLUE)

# Two sub-boxes inside: OpenMC → FEniCS
rounded_box(ax_B, (0.10, 0.60), 0.32, 0.18, fc="#D6E6F5", ec=C_BLUE)
ax_B.text(0.26, 0.72, "OpenMC", ha="center", va="center",
          fontsize=7, fontweight="bold", color=C_DARK)
ax_B.text(0.26, 0.64, "Neutronics", ha="center", va="center",
          fontsize=6, color=C_GRAY)

ax_B.annotate("", xy=(0.58, 0.69), xytext=(0.44, 0.69),
              arrowprops=dict(arrowstyle="-|>", color=C_GRAY, lw=1.0))

rounded_box(ax_B, (0.58, 0.60), 0.32, 0.18, fc="#D6E6F5", ec=C_BLUE)
ax_B.text(0.74, 0.72, "FEniCS", ha="center", va="center",
          fontsize=7, fontweight="bold", color=C_DARK)
ax_B.text(0.74, 0.64, "Thermo-mech.", ha="center", va="center",
          fontsize=6, color=C_GRAY)

# Arrow down
ax_B.annotate("", xy=(0.50, 0.36), xytext=(0.50, 0.56),
              arrowprops=dict(arrowstyle="-|>", color=C_GRAY, lw=1.2))
ax_B.text(0.62, 0.46, "Geometry &\ntemperature\nfeedback",
          fontsize=5.5, color=C_GRAY, va="center", fontstyle="italic")

# Coupled steady state box
rounded_box(ax_B, (0.06, 0.12), 0.88, 0.22, fc="#F0F4F8", ec=C_ORANGE)
ax_B.text(0.50, 0.30, "2. Coupled steady state",
          ha="center", va="center", fontsize=7.5, fontweight="bold", color=C_ORANGE)

# Result labels with colored dots
outputs_B = [("Power", 0.15), ("Temp.", 0.35), ("Stress", 0.58), ("k_eff", 0.78)]
colors_B = [C_RED, C_ORANGE, C_BLUE, C_TEAL]
for (lbl, xp), col in zip(outputs_B, colors_B):
    ax_B.plot(xp, 0.17, "s", color=col, markersize=5, zorder=5)
    ax_B.text(xp, 0.12, lbl, ha="center", va="top", fontsize=5.5, color=col)

ax_B.text(0.50, 0.05, "n = 3,418 simulations",
          ha="center", va="center", fontsize=6.5, color=C_GRAY, fontstyle="italic")

# ───────────────────────────────────────────────────────────────
# (C) Unified Bayesian posterior predictive layer
# ───────────────────────────────────────────────────────────────
ax_C = fig.add_subplot(gs[2])
ax_C.set_xlim(0, 1)
ax_C.set_ylim(0, 1)
ax_C.axis("off")

rounded_box(ax_C, (0.02, 0.02), 0.96, 0.96)
ax_C.text(0.5, 0.95, "(C) Unified Bayesian\nposterior predictive layer",
          ha="center", va="top", fontsize=8.5, fontweight="bold", color=C_DARK)

# BNN architecture schematic
rounded_box(ax_C, (0.06, 0.60), 0.88, 0.26, fc="#E8EFF5", ec=C_BLUE)
ax_C.text(0.50, 0.83, "Bayesian neural surrogate",
          ha="center", va="center", fontsize=7.5, fontweight="bold", color=C_DARK)
ax_C.text(0.50, 0.77, "(trained on high-fidelity data)",
          ha="center", va="center", fontsize=6, color=C_GRAY)

# Network layers: 8 → 254 → 254 → 15
layer_x = [0.15, 0.35, 0.55, 0.75]
layer_n = [4, 6, 6, 5]
layer_labels = ["Input (8)", "254", "254", "Output (15)"]
layer_colors = [C_BLUE, C_DARK, C_DARK, C_ORANGE]

for i, (lx, ln, ll, lc) in enumerate(zip(layer_x, layer_n, layer_labels, layer_colors)):
    for j in range(ln):
        yy = 0.64 + (j - (ln-1)/2) * 0.022
        circle = Circle((lx, yy), 0.008, facecolor=lc, edgecolor="white",
                        linewidth=0.3, zorder=3, transform=ax_C.transData)
        ax_C.add_patch(circle)
    ax_C.text(lx, 0.62 - ln*0.012, ll, ha="center", va="top",
              fontsize=5, color=lc)

# Connections between layers (simplified)
for i in range(len(layer_x)-1):
    for j1 in range(min(layer_n[i], 3)):
        for j2 in range(min(layer_n[i+1], 3)):
            y1 = 0.64 + (j1 - (min(layer_n[i],3)-1)/2) * 0.022
            y2 = 0.64 + (j2 - (min(layer_n[i+1],3)-1)/2) * 0.022
            ax_C.plot([layer_x[i]+0.01, layer_x[i+1]-0.01], [y1, y2],
                     color=C_LGRAY, lw=0.3, zorder=1)

# Posterior predictive distribution box
rounded_box(ax_C, (0.10, 0.28), 0.80, 0.26, fc="white", ec=C_DARK)
ax_C.text(0.50, 0.50, "Posterior predictive distribution",
          ha="center", va="center", fontsize=7, fontweight="bold", color=C_DARK)
ax_C.text(0.50, 0.44, r"$p(\mathbf{y} \mid \mathbf{x}, \mathcal{D})$",
          ha="center", va="center", fontsize=12, color=C_DARK)

# Mini output densities
out_names = [r"$\sigma$", r"$k_\mathrm{eff}$", "Max\nfuel T", "Max\nmono T", "Wall"]
out_colors = [C_BLUE, C_TEAL, C_RED, C_ORANGE, C_GRAY]
for k, (nm, oc) in enumerate(zip(out_names, out_colors)):
    xc = 0.16 + k * 0.16
    draw_mini_gaussian(ax_C, xc - 0.06, 0.30, 0.12, 0.08, oc)
    ax_C.text(xc, 0.28, nm, ha="center", va="top", fontsize=4.5, color=oc)

# Arrow from BNN to PPD
ax_C.annotate("", xy=(0.50, 0.54), xytext=(0.50, 0.60),
              arrowprops=dict(arrowstyle="-|>", color=C_DARK, lw=1.0))

ax_C.text(0.50, 0.08,
          "Predictive mean and heteroscedastic\n"
          "uncertainty for 15 scalar outputs",
          ha="center", va="center", fontsize=6, color=C_GRAY, fontstyle="italic")
ax_C.text(0.50, 0.15,
          "Trained once; reused without retraining",
          ha="center", va="center", fontsize=6.5, fontweight="bold", color=C_DARK)

# ───────────────────────────────────────────────────────────────
# (D) Downstream analyses
# ───────────────────────────────────────────────────────────────
ax_D = fig.add_subplot(gs[3])
ax_D.set_xlim(0, 1)
ax_D.set_ylim(0, 1)
ax_D.axis("off")

rounded_box(ax_D, (0.02, 0.02), 0.96, 0.96)
ax_D.text(0.5, 0.95, "(D) Downstream analyses\n(three applications)",
          ha="center", va="top", fontsize=8.5, fontweight="bold", color=C_DARK)

# Three analysis boxes stacked vertically
analyses = [
    {"title": "1. Forward uncertainty\n    propagation",
     "detail": "Monte Carlo through surrogate\nOutput distributions",
     "color": C_BLUE, "y": 0.68},
    {"title": "2. Sobol sensitivity\n    attribution",
     "detail": "Variance-based decomposition\nDominant-factor separation",
     "color": C_ORANGE, "y": 0.42},
    {"title": "3. Observation-conditioned\n    posterior calibration",
     "detail": "MCMC updating\nPrior → Posterior",
     "color": C_TEAL, "y": 0.16},
]

for an in analyses:
    y0 = an["y"]
    rounded_box(ax_D, (0.06, y0), 0.88, 0.22, fc="white", ec=an["color"])
    ax_D.text(0.12, y0 + 0.18, an["title"],
              fontsize=7, fontweight="bold", color=an["color"], va="top")

    # Mini visualization thumbnail
    xv = 0.72
    if an["color"] == C_BLUE:  # forward UQ: density curve
        draw_mini_gaussian(ax_D, xv, y0 + 0.03, 0.18, 0.10, C_BLUE)
        ax_D.axvline(x=xv + 0.12, ymin=(y0+0.03)/1, ymax=(y0+0.13)/1,
                     color=C_RED, ls="--", lw=0.6)
    elif an["color"] == C_ORANGE:  # Sobol: mini bars
        bar_vals = [0.58, 0.17, 0.065, 0.05]
        for bi, bv in enumerate(bar_vals):
            by = y0 + 0.14 - bi * 0.028
            ax_D.barh(by, bv * 0.28, left=xv, height=0.020,
                     color=C_ORANGE, alpha=0.6 + bi*0.1, edgecolor="none")
    elif an["color"] == C_TEAL:  # Posterior: prior→posterior
        x_pr = np.linspace(-3, 3, 60)
        y_pr = stats.norm.pdf(x_pr, 0, 1.5)
        y_po = stats.norm.pdf(x_pr, 0.3, 0.6)
        xoff, yoff = xv, y0 + 0.03
        ax_D.fill_between(xoff + x_pr/20, yoff, yoff + y_pr/y_pr.max()*0.10,
                          color=C_GRAY, alpha=0.2)
        ax_D.plot(xoff + x_pr/20, yoff + y_pr/y_pr.max()*0.10,
                  color=C_GRAY, lw=0.6)
        ax_D.fill_between(xoff + x_pr/20, yoff, yoff + y_po/y_po.max()*0.10,
                          color=C_TEAL, alpha=0.25)
        ax_D.plot(xoff + x_pr/20, yoff + y_po/y_po.max()*0.10,
                  color=C_TEAL, lw=0.9)

# ── Inter-column arrows ──
for ax_from, ax_to in [(ax_A, ax_B), (ax_B, ax_C), (ax_C, ax_D)]:
    connect_columns(fig, ax_from, ax_to, y_frac=0.5)

# ── Bottom caption ──
fig.text(0.50, 0.03,
         "A single posterior predictive distribution, trained from coupled "
         "high-fidelity simulations, enables coherent\n"
         "forward uncertainty propagation, variance-based sensitivity "
         "attribution, and observation-conditioned posterior updating "
         "without retraining.",
         ha="center", va="center", fontsize=7, color=C_GRAY, fontstyle="italic")


# ═══════════════════════════════════════════════════════════════
# SAVE: annotated + clean
# ═══════════════════════════════════════════════════════════════
ncs_style.save_all(fig, "figure1_workflow_v2", OUTDIR)

# Individual column panels
for i, (ax_obj, name) in enumerate([
    (ax_A, "fig1_panelA_inputs"),
    (ax_B, "fig1_panelB_simulation"),
    (ax_C, "fig1_panelC_bnn"),
    (ax_D, "fig1_panelD_downstream"),
]):
    extent = ax_obj.get_tightbbox(fig.canvas.get_renderer())
    if extent is not None:
        extent_expanded = extent.expanded(1.05, 1.05)
        for fmt in ["svg", "png", "pdf"]:
            fig.savefig(OUTDIR / f"{name}.{fmt}",
                        bbox_inches=extent_expanded.transformed(fig.dpi_scale_trans.inverted()),
                        dpi=300 if fmt == "png" else None)
        print(f"  Saved {name}")

plt.close(fig)
print("Done.")
