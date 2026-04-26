#!/usr/bin/env python3
"""Export Figure 3 to PPTX with native editable elements.

Slide 1: Composed 3-panel figure (image) + native title + panel labels
Slide 2-4: Individual panels as images + native labels
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
    ("A", "figure3_panelA_stress", "Coupling reshapes stress distribution"),
    ("B", "figure3_panelB_keff", "Coupled k_eff distribution"),
    ("C", "figure3_panelC_thermal", "Coupled max fuel temperature distribution"),
]


def main():
    prs = ppt.create_presentation()

    # ── Slide 1: Composed figure ──────────────────────────────────────────
    slide1 = ppt.add_blank_slide(prs)
    ppt.add_slide_title(slide1,
        "Figure 3 | Coupling reshapes forward response distributions",
        font_size=18, color=GRAY_900)
    ppt.add_centered_image(slide1, OUTDIR / "figure3_composed.png",
                           max_w=12.0, max_h=5.8, y_offset=0.55)
    # Panel labels
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
            f"Figure 3{letter} | {subtitle}",
            font_size=18, color=GRAY_900)
        ppt.add_centered_image(slide, img, max_w=10.0, max_h=5.8,
                               y_offset=0.55)
        ppt.add_panel_label(slide, letter, left=0.50, top=0.90)

    # ── Slide 5: Editable text layer ──────────────────────────────────────
    slide_txt = ppt.add_blank_slide(prs)
    ppt.add_slide_title(slide_txt,
        "Figure 3 — Editable text elements",
        font_size=16, color=GRAY_500)

    y = 1.20
    for letter, _, subtitle in PANELS:
        ppt.add_text_box(slide_txt, f"{letter}.  {subtitle}",
                         left=0.7, top=y, width=10.0, height=0.35,
                         font_size=13, bold=True, color=BLUE_DARK)
        y += 0.45

    y += 0.30
    ppt.add_text_box(slide_txt, "Axis labels (editable):",
                     left=0.7, top=y, width=8.0, height=0.30,
                     font_size=11, bold=True, color=GRAY_900)
    y += 0.35
    axis_labels = [
        "Panel A x-axis: Coupled steady-state max stress (MPa)",
        "Panel A legend: Uncoupled pass / Coupled steady state / 131 MPa threshold",
        "Panel B x-axis: k_eff (coupled)",
        "Panel C x-axis: Max fuel temperature (K)",
        "All y-axes: Density",
    ]
    ppt.add_multiline_text_box(
        slide_txt, axis_labels,
        left=0.9, top=y, width=11.0, height=2.0,
        font_size=10, color=GRAY_900, bullet=True)

    y += 2.2
    ppt.add_text_box(
        slide_txt,
        "Caption: Coupling-induced forward response shift. "
        "(A) Max stress: uncoupled pass vs coupled steady state, "
        "with 131 MPa threshold. "
        "(B) Coupled k_eff. "
        "(C) Coupled max fuel temperature. "
        "All distributions from BNN predictive draw "
        "(20,000 input samples \u00d7 50 MC weight draws).",
        left=0.7, top=y, width=11.0, height=1.0,
        font_size=10, italic=True, color=GRAY_500)

    notes = (
        "Figure 3 — Forward UQ.\n"
        "Panel A: stress, Panel B: k_eff, Panel C: fuel temp.\n"
        "All text on last slide is editable."
    )
    prs.slides[0].notes_slide.notes_text_frame.text = notes

    ppt.save_pptx(prs, OUTDIR / "figure3_forward_uq.pptx")


if __name__ == "__main__":
    main()
