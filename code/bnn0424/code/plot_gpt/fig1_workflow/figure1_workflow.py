"""
Figure 1 — Probabilistic analysis pipeline (workflow diagram).

6-box horizontal layout with NCS blue-gray monochrome style.
Text-only boxes, no decorative elements.

Outputs: fig1_workflow/outputs/figure1_workflow.{pdf,svg,png}
"""

import sys
from pathlib import Path

# Add _shared to sys.path for ncs_style import
_SHARED = str(Path(__file__).resolve().parent.parent / "_shared")
if _SHARED not in sys.path:
    sys.path.insert(0, _SHARED)

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import ncs_style

ncs_style.apply_style()

# ── Layout parameters ──────────────────────────────────────────────────
FIG_W, FIG_H = 13, 3.8
BOX_W = 0.138
BOX_H = 0.52
BOX_Y = 0.22
X_POSITIONS = [0.02, 0.185, 0.35, 0.515, 0.68, 0.845]

# ── Box definitions ────────────────────────────────────────────────────
BOXES = [
    {
        "title": "Uncertain inputs",
        "lines": [
            "8 SS316 material parameters",
            "E slope / intercept",
            "Thermal expansion base / slope",
            "Conductivity reference / slope",
            "Poisson's ratio",
        ],
    },
    {
        "title": "Coupled HF simulation",
        "lines": [
            "OpenMC + FEniCS",
            "Uncoupled pass",
            "Coupled steady state",
            "Temperature / stress / k_eff",
        ],
    },
    {
        "title": "Bayesian neural surrogate",
        "lines": [
            "Constraint-regularized BNN",
            "Posterior predictive distribution",
            "Predictive mean + uncertainty",
            "Multi-output surrogate layer",
        ],
    },
    {
        "title": "Forward propagation",
        "lines": [
            "Monte Carlo propagation",
            "Response distributions",
            "Coupling-induced shift",
            "Stress / k_eff / thermal outputs",
        ],
    },
    {
        "title": "Sensitivity attribution",
        "lines": [
            "Sobol variance decomposition",
            "Dominant-factor separation",
            "Stress vs k_eff pathways",
            "S1 / ST with confidence intervals",
        ],
    },
    {
        "title": "Posterior calibration",
        "lines": [
            "Observation-conditioned updating",
            "Prior to posterior shift",
            "Joint posterior structure",
            "Posterior predictive agreement",
        ],
    },
]


# ── Helper functions ───────────────────────────────────────────────────
def add_box(ax, xy, w, h, title, body_lines):
    """Draw a rounded box with title and bullet text."""
    x, y = xy
    box = FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.012,rounding_size=0.018",
        linewidth=0.9,
        edgecolor=ncs_style.GRAY_300,
        facecolor=ncs_style.BLUE_WASH,
    )
    ax.add_patch(box)

    # Title (bold, BLUE_MID)
    ax.text(
        x + 0.03 * w, y + h - 0.10 * h, title,
        fontsize=ncs_style.FONT_TITLE, fontweight="bold",
        va="top", ha="left", color=ncs_style.BLUE_MID,
    )

    # Bullet lines
    start_y = y + h - 0.28 * h
    step = 0.135 * h
    for i, line in enumerate(body_lines):
        ax.text(
            x + 0.05 * w, start_y - i * step, line,
            fontsize=ncs_style.FONT_TICK_LABEL, va="top", ha="left",
            color=ncs_style.GRAY_700,
        )


def add_arrow(ax, p1, p2):
    """Draw a simple gray straight arrow."""
    arrow = FancyArrowPatch(
        p1, p2,
        arrowstyle="-|>",
        mutation_scale=12,
        linewidth=1.2,
        color=ncs_style.GRAY_500,
        shrinkA=3, shrinkB=3,
    )
    ax.add_patch(arrow)


# ── Build figure ───────────────────────────────────────────────────────
fig = plt.figure(figsize=(FIG_W, FIG_H))
ax = plt.axes([0, 0, 1, 1])
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis("off")

# Draw boxes
for i, bdef in enumerate(BOXES):
    add_box(ax, (X_POSITIONS[i], BOX_Y), BOX_W, BOX_H,
            bdef["title"], bdef["lines"])

# Draw arrows between consecutive boxes
arrow_y = BOX_Y + BOX_H / 2
for i in range(len(BOXES) - 1):
    x1 = X_POSITIONS[i] + BOX_W + 0.004
    x2 = X_POSITIONS[i + 1] - 0.004
    add_arrow(ax, (x1, arrow_y), (x2, arrow_y))

# Bottom note
ax.text(
    0.02, 0.10,
    "The constraint-regularized Bayesian surrogate serves as a unified "
    "posterior predictive layer enabling forward uncertainty propagation, "
    "variance-based attribution, and observation-conditioned posterior updating.",
    fontsize=ncs_style.FONT_TICK_LABEL, color=ncs_style.GRAY_500,
    ha="left", va="center",
)
ax.text(
    0.02, 0.04,
    "'Uncoupled pass' denotes the first-pass response; "
    "'coupled steady state' denotes the converged coupled response.",
    fontsize=ncs_style.FONT_TICK_LABEL, color=ncs_style.GRAY_500,
    ha="left", va="center",
)

# ── Export ──────────────────────────────────────────────────────────────
OUTDIR = Path(__file__).resolve().parent / "outputs"
ncs_style.save_all(fig, "figure1_workflow", OUTDIR)
plt.close(fig)
print("Done.")
