"""
Export Figure 1 workflow as a FULLY NATIVE editable PowerPoint.

Every element is a native PPT object:
  - 6 rounded rectangles (movable, recolorable)
  - Title + bullet text inside each box (editable font/size/color)
  - 5 arrow connectors (repositionable)
  - Bottom caption text boxes (editable)

No embedded images — 100% editable.
"""

import sys
from pathlib import Path

_SHARED = str(Path(__file__).resolve().parent.parent / "_shared")
if _SHARED not in sys.path:
    sys.path.insert(0, _SHARED)

import ppt_helper as ppt

HERE = Path(__file__).resolve().parent
OUTDIR = HERE / "outputs"
OUTDIR.mkdir(parents=True, exist_ok=True)

# ── NCS color palette ─────────────────────────────────────────────────────
BLUE_WASH   = "#E8EFF5"
BLUE_MID    = "#3B6B9A"
GRAY_300    = "#B0B0B0"
GRAY_500    = "#7A7A7A"
GRAY_700    = "#4A4A4A"
GRAY_900    = "#1A1A1A"

# ── Box definitions (same content as figure1_workflow.py) ─────────────────
BOXES = [
    {
        "title": "Uncertain inputs",
        "lines": [
            "8 SS316 material parameters",
            "E slope / intercept",
            "Thermal expansion base / slope",
            "Conductivity reference / slope",
            "Poisson\u2019s ratio",
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

# ── Layout constants (inches) ─────────────────────────────────────────────
N_BOXES = len(BOXES)
BOX_W = 1.82
BOX_H = 2.7
GAP = 0.26
TOTAL_W = N_BOXES * BOX_W + (N_BOXES - 1) * GAP
LEFT_MARGIN = (ppt.SLIDE_W - TOTAL_W) / 2
BOX_TOP = 1.55
ARROW_Y = BOX_TOP + BOX_H / 2


def main():
    prs = ppt.create_presentation()
    slide = ppt.add_blank_slide(prs)

    # ── Slide title ───────────────────────────────────────────────────────
    ppt.add_slide_title(
        slide, "Figure 1 | Probabilistic analysis pipeline",
        font_size=22, bold=True, color=GRAY_900,
        left=0.5, top=0.20, width=12.0, height=0.60)

    # ── Subtitle ──────────────────────────────────────────────────────────
    ppt.add_text_box(
        slide,
        "Coupled thermo-mechanical HPR uncertainty-to-risk workflow",
        left=0.5, top=0.72, width=12.0, height=0.40,
        font_size=13, italic=True, color=GRAY_500)

    # ── 6 workflow boxes ──────────────────────────────────────────────────
    for i, bdef in enumerate(BOXES):
        x = LEFT_MARGIN + i * (BOX_W + GAP)
        ppt.add_box_with_text(
            slide, left=x, top=BOX_TOP, width=BOX_W, height=BOX_H,
            title=bdef["title"],
            body_lines=bdef["lines"],
            fill_color=BLUE_WASH,
            border_color=GRAY_300,
            title_color=BLUE_MID,
            body_color=GRAY_700,
            title_size=12,
            body_size=9.5,
            border_width=1.0,
        )

    # ── Arrow connectors between boxes ────────────────────────────────────
    for i in range(N_BOXES - 1):
        x_start = LEFT_MARGIN + i * (BOX_W + GAP) + BOX_W + 0.02
        x_end = LEFT_MARGIN + (i + 1) * (BOX_W + GAP) - 0.02
        ppt.add_arrow(slide, x_start, ARROW_Y, x_end, ARROW_Y,
                      color=GRAY_500, width=1.5)

    # ── Bottom caption notes ──────────────────────────────────────────────
    caption_lines = [
        "The constraint-regularized Bayesian surrogate serves as a unified "
        "posterior predictive layer enabling forward uncertainty propagation, "
        "variance-based attribution, and observation-conditioned posterior "
        "updating.",
        "",
        "\u2018Uncoupled pass\u2019 denotes the first-pass response; "
        "\u2018coupled steady state\u2019 denotes the converged coupled "
        "response.",
    ]
    ppt.add_multiline_text_box(
        slide, caption_lines,
        left=0.5, top=4.60, width=12.3, height=1.2,
        font_size=9.5, color=GRAY_500)

    # ── Decorative top line ───────────────────────────────────────────────
    ppt.add_line(slide, 0.5, 1.20, 12.8, 1.20,
                 color=GRAY_300, width=0.5)

    # ── Save ──────────────────────────────────────────────────────────────
    ppt.save_pptx(prs, OUTDIR / "figure1_workflow.pptx")


if __name__ == "__main__":
    main()
    print("Done.")
