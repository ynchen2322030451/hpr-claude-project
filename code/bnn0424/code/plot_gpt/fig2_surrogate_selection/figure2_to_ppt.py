#!/usr/bin/env python3
"""Export Figure 2 to PPTX with native editable elements.

Slide 1: Full composed figure (image) + native title + native panel labels
Slide 2: Editable text layer — all annotations, labels, captions as
         native text boxes that can be moved/resized/recolored.
"""

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "_shared"))
import ppt_helper as ppt

OUTDIR = HERE / "outputs"
COMPOSED = OUTDIR / "fig2_surrogate_selection.png"

# ── NCS colors ────────────────────────────────────────────────────────────
BLUE_DARK = "#1B3A5C"
GRAY_500  = "#7A7A7A"
GRAY_900  = "#1A1A1A"


def main():
    prs = ppt.create_presentation()

    # ── Slide 1: Full figure with native title + panel labels ─────────────
    slide1 = ppt.add_blank_slide(prs)
    ppt.add_slide_title(slide1,
        "Figure 2 | Posterior predictive behaviour of the selected "
        "Bayesian surrogate",
        font_size=18, color=GRAY_900)
    ppt.add_centered_image(slide1, COMPOSED, max_w=11.5, max_h=5.8,
                           y_offset=0.55)

    # Native panel labels (positioned outside image, top-left of each panel)
    ppt.add_panel_label(slide1, "A", left=0.55, top=0.90)
    ppt.add_panel_label(slide1, "B", left=6.10, top=0.90)
    ppt.add_panel_label(slide1, "C", left=6.10, top=3.50)
    ppt.add_panel_label(slide1, "D", left=1.30, top=5.10)

    # ── Slide 2: Editable text layer ─────────────────────────────────────
    slide2 = ppt.add_blank_slide(prs)
    ppt.add_slide_title(slide2,
        "Figure 2 — Editable text elements",
        font_size=16, color=GRAY_500)

    ppt.add_text_box(slide2, "Editable panel titles and annotations",
                     left=0.5, top=0.80, width=12.0, height=0.35,
                     font_size=11, italic=True, color=GRAY_500)

    # Panel titles
    y = 1.40
    for letter, title in [
        ("A", "Max global stress (parity plot)"),
        ("B", "Effective multiplication factor, k_eff (parity plot)"),
        ("C", "Max fuel temperature (parity plot)"),
        ("D", "Interval calibration across five coupled outputs"),
    ]:
        ppt.add_text_box(slide2, f"{letter}.  {title}",
                         left=0.7, top=y, width=8.0, height=0.35,
                         font_size=13, bold=True, color=BLUE_DARK)
        y += 0.50

    # Metric annotations (typical values — user can update)
    y += 0.30
    ppt.add_text_box(slide2, "Key metric annotations (editable):",
                     left=0.7, top=y, width=8.0, height=0.30,
                     font_size=11, bold=True, color=GRAY_900)
    y += 0.40
    metrics = [
        "Panel A — R\u00b2, RMSE (MPa), PICP90",
        "Panel B — R\u00b2, RMSE, PICP90",
        "Panel C — R\u00b2, RMSE (K), PICP90",
        "Panel D — PICP90 at 90% nominal level",
    ]
    ppt.add_multiline_text_box(
        slide2, metrics,
        left=0.9, top=y, width=10.0, height=1.8,
        font_size=10, color=GRAY_900, bullet=True)

    # Legend items
    y += 2.0
    ppt.add_text_box(slide2, "Legend entries (editable):",
                     left=0.7, top=y, width=8.0, height=0.30,
                     font_size=11, bold=True, color=GRAY_900)
    y += 0.35
    legend_items = [
        "90% predictive interval",
        "y = x (identity line)",
        "Physics-regularized BNN",
        "MC-Dropout",
        "Deep Ensemble",
    ]
    ppt.add_multiline_text_box(
        slide2, legend_items,
        left=0.9, top=y, width=10.0, height=1.5,
        font_size=10, color=GRAY_900, bullet=True)

    # Caption
    y += 1.8
    ppt.add_text_box(
        slide2,
        "Caption: Panels A\u2013C show parity hexbin plots for coupled "
        "steady-state max stress, k_eff, and max fuel temperature "
        "respectively, with 90% predictive intervals. Panel D compares "
        "interval calibration (PICP90) of BNN vs baselines across all "
        "five coupled outputs.",
        left=0.7, top=y, width=11.0, height=1.0,
        font_size=10, italic=True, color=GRAY_500)

    # Notes
    slide1.notes_slide.notes_text_frame.text = (
        "Figure 2: Posterior predictive behaviour.\n"
        "Panels A-C: parity hexbin, Panel D: PICP90 strip.\n"
        "All text on Slide 2 is editable — copy to this slide as needed."
    )

    ppt.save_pptx(prs, OUTDIR / "figure2_surrogate_selection.pptx")


if __name__ == "__main__":
    main()
