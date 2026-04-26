import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import matplotlib as mpl

# -----------------------------
# Global publication style
# -----------------------------
mpl.rcParams.update({
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "font.family": "DejaVu Sans",
    "font.size": 9,
    "axes.linewidth": 0.8,
    "savefig.bbox": "tight",
})

# -----------------------------
# Helper functions
# -----------------------------
def add_box(ax, xy, w, h, title, body_lines=None,
            fc="#F7F8FA", ec="#C9CED6", lw=1.0,
            title_size=10, body_size=8):
    x, y = xy
    box = FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.015,rounding_size=0.02",
        linewidth=lw, edgecolor=ec, facecolor=fc
    )
    ax.add_patch(box)

    ax.text(x + 0.03*w, y + h - 0.16*h, title,
            fontsize=title_size, fontweight="bold",
            va="top", ha="left", color="#1F2937")

    if body_lines:
        start_y = y + h - 0.33*h
        step = 0.12*h
        for i, line in enumerate(body_lines):
            ax.text(x + 0.05*w, start_y - i*step, line,
                    fontsize=body_size, va="top", ha="left",
                    color="#374151")

def add_arrow(ax, p1, p2, color="#8A8A8A", lw=1.6):
    arrow = FancyArrowPatch(
        p1, p2,
        arrowstyle="-|>",
        mutation_scale=14,
        linewidth=lw,
        color=color,
        shrinkA=4, shrinkB=4
    )
    ax.add_patch(arrow)

def add_small_distribution(ax, center, width=0.08, height=0.06,
                           color="#8FB3E8"):
    cx, cy = center
    xs = [cx - width/2, cx - width/4, cx, cx + width/4, cx + width/2]
    ys = [cy, cy + height*0.3, cy + height, cy + height*0.35, cy]
    ax.fill(xs, ys, color=color, alpha=0.9)
    ax.plot(xs, ys, color="#4B6FAE", lw=1.0)

def add_small_bars(ax, origin, values, w=0.012, gap=0.01,
                   color="#6E92C9"):
    x0, y0 = origin
    for i, v in enumerate(values):
        ax.add_patch(plt.Rectangle((x0 + i*(w+gap), y0), w, v,
                                   facecolor=color, edgecolor="none"))

# -----------------------------
# Figure canvas
# -----------------------------
fig = plt.figure(figsize=(13, 4.8))
ax = plt.axes([0, 0, 1, 1])
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis("off")

# -----------------------------
# Title
# -----------------------------
ax.text(0.02, 0.96, "Figure 1. Probabilistic analysis pipeline",
        fontsize=14, fontweight="bold", ha="left", va="top", color="#111827")
ax.text(0.02, 0.915,
        "Constraint-regularized Bayesian surrogate for forward propagation, sensitivity attribution, and posterior calibration",
        fontsize=9.5, ha="left", va="top", color="#4B5563")

# -----------------------------
# Main boxes
# -----------------------------
box_y = 0.28
box_h = 0.50
box_w = 0.145

x_positions = [0.03, 0.20, 0.37, 0.54, 0.71, 0.88]

add_box(
    ax, (x_positions[0], box_y), box_w, box_h,
    "Uncertain inputs",
    [
        "8 SS316 material-property parameters",
        "E slope / intercept",
        "thermal expansion base / slope",
        "conductivity reference / slope",
        "Poisson's ratio"
    ],
    fc="#FAFAF8"
)

add_box(
    ax, (x_positions[1], box_y), box_w, box_h,
    "Coupled high-fidelity simulation",
    [
        "OpenMC + FEniCS",
        "uncoupled pass",
        "coupled steady state",
        "temperature / stress / k_eff outputs"
    ],
    fc="#F7FAFC"
)

add_box(
    ax, (x_positions[2], box_y), box_w, box_h,
    "Bayesian neural surrogate",
    [
        "constraint-regularized BNN",
        "posterior predictive distribution",
        "predictive mean + uncertainty",
        "multi-output surrogate layer"
    ],
    fc="#F5F8FF"
)

add_box(
    ax, (x_positions[3], box_y), box_w, box_h,
    "Forward propagation",
    [
        "Monte Carlo propagation",
        "response distributions",
        "coupling-induced shift",
        "stress / k_eff / thermal outputs"
    ],
    fc="#FAFBF7"
)

add_box(
    ax, (x_positions[4], box_y), box_w, box_h,
    "Sensitivity attribution",
    [
        "Sobol variance decomposition",
        "dominant-factor separation",
        "stress vs k_eff pathways",
        "S1 / ST with confidence intervals"
    ],
    fc="#FBFAF5"
)

add_box(
    ax, (x_positions[5]-0.02, box_y), box_w, box_h,
    "Posterior calibration",
    [
        "observation-conditioned updating",
        "prior → posterior shift",
        "joint posterior structure",
        "posterior predictive agreement"
    ],
    fc="#FFF8F7"
)

# -----------------------------
# Arrows
# -----------------------------
for i in range(5):
    x1 = x_positions[i] + box_w
    x2 = (x_positions[i+1] if i < 4 else x_positions[5]-0.02)
    add_arrow(ax, (x1 + 0.01, 0.53), (x2 - 0.01, 0.53))

# -----------------------------
# Minimal visual cues
# -----------------------------
# Inputs: mini distributions
for yy in [0.60, 0.53, 0.46]:
    add_small_distribution(ax, (x_positions[0] + 0.07, yy), width=0.04, height=0.025, color="#D9C58D")

# HF block: uncoupled / coupled tiny curves
ax.plot([x_positions[1]+0.03, x_positions[1]+0.10, x_positions[1]+0.13],
        [0.43, 0.39, 0.34], color="#7A9BC9", lw=1.2)
ax.plot([x_positions[1]+0.03, x_positions[1]+0.10, x_positions[1]+0.13],
        [0.36, 0.40, 0.44], color="#6E8E63", lw=1.2)
ax.text(x_positions[1]+0.03, 0.31, "uncoupled pass → coupled steady state",
        fontsize=7.5, color="#4B5563")

# BNN block: tiny network sketch
for x in [x_positions[2]+0.035, x_positions[2]+0.075, x_positions[2]+0.115]:
    for y in [0.40, 0.48, 0.56]:
        ax.plot(x, y, 'o', ms=3.2, color="#5A78B3")
for y1 in [0.40, 0.48, 0.56]:
    for y2 in [0.40, 0.48, 0.56]:
        ax.plot([x_positions[2]+0.035, x_positions[2]+0.075], [y1, y2],
                color="#C8D4EA", lw=0.6)
        ax.plot([x_positions[2]+0.075, x_positions[2]+0.115], [y1, y2],
                color="#C8D4EA", lw=0.6)

# Forward block: mini distribution
add_small_distribution(ax, (x_positions[3]+0.08, 0.42), width=0.08, height=0.05, color="#A8C0EB")

# Sobol block: mini bars
add_small_bars(ax, (x_positions[4]+0.04, 0.38), [0.10, 0.07, 0.045, 0.03], w=0.015, gap=0.01)

# Posterior block: mini contours
theta = [i/100 for i in range(101)]
# just an abstract ellipse-like contour
for s, alpha in zip([0.045, 0.032, 0.020], [0.15, 0.22, 0.35]):
    xs = [x_positions[5]+0.05 + s*1.4 for _ in range(1)]  # placeholder to keep style simple
# draw simple nested ellipses using parametric form
import numpy as np
cx, cy = x_positions[5]+0.07, 0.42
for a, b, al in [(0.050, 0.030, 0.15), (0.036, 0.022, 0.22), (0.024, 0.014, 0.32)]:
    t = np.linspace(0, 2*np.pi, 200)
    x = cx + a*np.cos(t)
    y = cy + b*np.sin(t)
    ax.fill(x, y, color="#C98E8A", alpha=al, edgecolor="none")

# -----------------------------
# Bottom note
# -----------------------------
ax.text(
    0.02, 0.12,
    "Primary role of the surrogate: a unified posterior predictive layer enabling forward uncertainty propagation, "
    "variance-based attribution, and observation-conditioned posterior updating.",
    fontsize=8.3, color="#4B5563", ha="left", va="center"
)

ax.text(
    0.02, 0.06,
    "Note: 'uncoupled pass' denotes the first-pass response; 'coupled steady state' denotes the converged coupled response.",
    fontsize=7.8, color="#6B7280", ha="left", va="center"
)

# -----------------------------
# Save outputs
# -----------------------------
from pathlib import Path
OUTDIR = Path(__file__).resolve().parent.parent / "fig1_workflow" / "outputs"
OUTDIR.mkdir(exist_ok=True)
fig.savefig(OUTDIR / "figure1_workflow.svg")
fig.savefig(OUTDIR / "figure1_workflow.pdf")
fig.savefig(OUTDIR / "figure1_workflow.png", dpi=600)
plt.close(fig)