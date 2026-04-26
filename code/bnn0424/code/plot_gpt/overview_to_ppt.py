"""
Export overview figure + all individual figures to a multi-slide PPTX
with native editable text elements.

Each slide has:
  - Centered image (the figure)
  - Native editable title text box
  - Native panel labels where applicable
"""

import sys
from pathlib import Path

_SHARED = str(Path(__file__).resolve().parent / "_shared")
if _SHARED not in sys.path:
    sys.path.insert(0, _SHARED)

import ppt_helper as ppt

HERE = Path(__file__).resolve().parent
OUTDIR = HERE / "outputs"

# Collect all key PNGs in presentation order
SLIDES = [
    ("Figure 1 | Probabilistic analysis framework — Overview",
     OUTDIR / "figure_overview.png",
     ["A", "B", "C", "D"]),
    ("Figure 2 | Surrogate predictive accuracy",
     HERE / "fig2_surrogate_selection" / "outputs" / "fig2_surrogate_selection.png",
     ["A", "B", "C", "D"]),
    ("Figure 3 | Forward uncertainty propagation",
     HERE / "fig3_forward_uq" / "outputs" / "figure3_composed.png",
     ["A", "B", "C"]),
    ("Figure 3A | Stress distribution",
     HERE / "fig3_forward_uq" / "outputs" / "figure3_panelA_stress.png",
     []),
    ("Figure 3B | k_eff distribution",
     HERE / "fig3_forward_uq" / "outputs" / "figure3_panelB_keff.png",
     []),
    ("Figure 3C | Thermal distribution",
     HERE / "fig3_forward_uq" / "outputs" / "figure3_panelC_thermal.png",
     []),
    ("Figure 4 | Sobol sensitivity",
     HERE / "fig4_sobol" / "outputs" / "figure4_full.png",
     ["A", "B", "C"]),
    ("Figure 4A | Stress Sobol",
     HERE / "fig4_sobol" / "outputs" / "panel_A_stress.png",
     []),
    ("Figure 4B | k_eff Sobol",
     HERE / "fig4_sobol" / "outputs" / "panel_B_keff.png",
     []),
    ("Figure 5 | Posterior calibration",
     HERE / "fig5_posterior" / "outputs" / "figure5_combined.png",
     ["A", "B", "C"]),
    ("Figure 5A | Marginals",
     HERE / "fig5_posterior" / "outputs" / "figure5_panelA.png",
     []),
    ("Figure 5B | Joint posterior",
     HERE / "fig5_posterior" / "outputs" / "figure5_panelB.png",
     []),
    ("Figure 5C | Predictive stress",
     HERE / "fig5_posterior" / "outputs" / "figure5_panelC.png",
     []),
]


def main():
    prs = ppt.create_presentation()

    for title, img_path, panel_labels in SLIDES:
        img_path = Path(img_path)
        if not img_path.exists():
            print(f"  Skipping (not found): {img_path.name}")
            continue

        slide = ppt.add_blank_slide(prs)

        # Native editable title
        ppt.add_slide_title(slide, title, font_size=18)

        # Centered image
        ppt.add_centered_image(slide, img_path,
                               max_w=12.0, max_h=6.0, y_offset=0.40)

        # Native panel labels if specified
        # Default positions spread across top of figure
        if panel_labels:
            n = len(panel_labels)
            for j, letter in enumerate(panel_labels):
                x = 0.30 + j * (12.0 / n)
                ppt.add_panel_label(slide, letter, left=x, top=0.90)

    ppt.save_pptx(prs, OUTDIR / "all_figures.pptx")


if __name__ == "__main__":
    main()
