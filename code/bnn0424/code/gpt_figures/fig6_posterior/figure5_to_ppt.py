#!/usr/bin/env python3
"""Export Figure 5 to PPTX with native editable elements.

Slide 1: Full combined figure (image) + native title + panel labels
Slide 2-4: Individual panels A/B/C as images
Slide 5: Editable text layer with all annotations/captions
"""

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "_shared"))
import ppt_helper as ppt

OUTDIR = HERE / "outputs"

BLUE_DARK = "#1B3A5C"
GRAY_500  = "#7A7A7A"
GRAY_900  = "#1A1A1A"

PANELS = [
    ("A", "figure5_panelA",  "Marginal posterior distributions"),
    ("B", "figure5_panelB",  "Joint posterior (E intercept vs \u03b1_base)"),
    ("C", "figure5_panelC",  "Posterior predictive stress agreement"),
]


def main():
    prs = ppt.create_presentation()

    # ── Slide 1: Combined figure ──────────────────────────────────────────
    combined = OUTDIR / "figure5_combined.png"
    slide1 = ppt.add_blank_slide(prs)
    ppt.add_slide_title(slide1,
        "Figure 5 | Observation-conditioned posterior calibration",
        font_size=18, color=GRAY_900)
    ppt.add_centered_image(slide1, combined, max_w=12.0, max_h=5.8,
                           y_offset=0.55)
    ppt.add_panel_label(slide1, "A", left=0.30, top=0.90)
    ppt.add_panel_label(slide1, "B", left=4.50, top=0.90)
    ppt.add_panel_label(slide1, "C", left=8.80, top=0.90)

    # ── Slides 2-4: Individual panels ─────────────────────────────────────
    for letter, stem, subtitle in PANELS:
        img = OUTDIR / f"{stem}.png"
        if not img.exists():
            continue
        slide = ppt.add_blank_slide(prs)
        ppt.add_slide_title(slide,
            f"Figure 5{letter} | {subtitle}",
            font_size=18, color=GRAY_900)
        ppt.add_centered_image(slide, img, max_w=10.0, max_h=5.8,
                               y_offset=0.55)
        ppt.add_panel_label(slide, letter, left=0.50, top=0.90)

    # ── Slide 5: Editable text layer ──────────────────────────────────────
    slide_txt = ppt.add_blank_slide(prs)
    ppt.add_slide_title(slide_txt,
        "Figure 5 — Editable text elements",
        font_size=16, color=GRAY_500)

    y = 1.20
    for letter, _, subtitle in PANELS:
        ppt.add_text_box(slide_txt, f"{letter}.  {subtitle}",
                         left=0.7, top=y, width=10.0, height=0.35,
                         font_size=13, bold=True, color=BLUE_DARK)
        y += 0.45

    y += 0.30
    ppt.add_text_box(slide_txt, "Key annotations (editable):",
                     left=0.7, top=y, width=8.0, height=0.30,
                     font_size=11, bold=True, color=GRAY_900)
    y += 0.35
    annotations = [
        "Panel A: Prior (gray) vs Posterior (blue) KDE densities",
        "  Parameters: E_intercept (GPa), \u03b1_base (\u00d710\u207b\u2076 K\u207b\u00b9), "
        "\u03b1_slope (\u00d710\u207b\u2079 K\u207b\u00b2), SS316_k_ref (W/m\u00b7K)",
        "Panel B: 2D KDE contours for joint posterior",
        "  E_intercept vs \u03b1_base, showing prior \u2192 posterior contraction",
        "Panel C: Posterior predictive stress vs observed (18 benchmark cases)",
        "  Background bands: Low / Near-threshold / High stress categories",
        "  131 MPa threshold line",
    ]
    ppt.add_multiline_text_box(
        slide_txt, annotations,
        left=0.9, top=y, width=11.0, height=2.5,
        font_size=10, color=GRAY_900, bullet=True)

    y += 2.8
    ppt.add_text_box(slide_txt, "Benchmark statistics (editable):",
                     left=0.7, top=y, width=8.0, height=0.30,
                     font_size=11, bold=True, color=GRAY_900)
    y += 0.35
    stats = [
        "18 test-split benchmark cases (6 low / 6 near / 6 high stress)",
        "Acceptance rate: 0.58\u20130.67 across cases",
        "90% CI coverage: 0.89\u20130.92",
        "Posterior predictive stress tracks observations within \u00b110 MPa",
    ]
    ppt.add_multiline_text_box(
        slide_txt, stats,
        left=0.9, top=y, width=11.0, height=1.5,
        font_size=10, color=GRAY_900, bullet=True)

    notes = (
        "Figure 5: Posterior calibration.\n"
        "Panel A: marginals, Panel B: joint, Panel C: predictive.\n"
        "All text on last slide is editable."
    )
    prs.slides[0].notes_slide.notes_text_frame.text = notes

    ppt.save_pptx(prs, OUTDIR / "figure5_posterior.pptx")


if __name__ == "__main__":
    main()
