#!/usr/bin/env python3
"""
Master script: run all figure scripts, then generate clean (no-text) SVG versions.
Output structure:
  final_outputs/
    fig2_predictive/
      fig2_surrogate_selection.svg          (annotated)
      fig2_surrogate_selection_clean.svg    (no text)
      fig2_surrogate_selection.png
    fig3_forward/
      figure3_composed.svg / _clean.svg / .png
      figure3_panelA_stress.svg / _clean.svg / .png
      figure3_panelB_keff.svg / _clean.svg / .png
      figure3_panelC_thermal.svg / _clean.svg / .png
    fig4_sobol/
      figure4_full.svg / _clean.svg / .png
      panel_A_stress.svg / _clean.svg / .png
      panel_B_keff.svg / _clean.svg / .png
      panel_C_summary.svg / _clean.svg / .png
    fig5_posterior/
      figure5_combined.svg / _clean.svg / .png
      figure5_panelA.svg / _clean.svg / .png
      figure5_panelB.svg / _clean.svg / .png
      figure5_panelC.svg / _clean.svg / .png
"""
import subprocess
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
PYTHON = "/opt/anaconda3/envs/nn_env/bin/python"
FINAL = HERE / "final_outputs"


def run_script(script_path: Path):
    print(f"\n{'='*60}")
    print(f"Running: {script_path.name}")
    print(f"{'='*60}")
    result = subprocess.run(
        [PYTHON, str(script_path)],
        cwd=str(script_path.parent),
        capture_output=True, text=True,
    )
    if result.stdout:
        print(result.stdout.strip())
    if result.returncode != 0:
        print(f"  ERROR: {result.stderr.strip()}")
    return result.returncode == 0


def strip_text_from_svg(src: Path, dst: Path):
    """Remove all <text> elements from SVG to create clean version."""
    ET.register_namespace("", "http://www.w3.org/2000/svg")
    ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")
    tree = ET.parse(src)
    root = tree.getroot()
    ns = {"svg": "http://www.w3.org/2000/svg"}

    for text_el in root.findall(".//svg:text", ns):
        parent = root.find(f".//{{{ns['svg']}}}" + "*/..")
        # Walk tree to find parent
        pass

    # Brute-force: walk all elements, remove <text> children
    def remove_text_elements(element):
        to_remove = []
        for child in element:
            tag = child.tag
            if isinstance(tag, str):
                local = tag.split("}")[-1] if "}" in tag else tag
                if local == "text":
                    to_remove.append(child)
                else:
                    remove_text_elements(child)
        for child in to_remove:
            element.remove(child)

    remove_text_elements(root)
    tree.write(str(dst), xml_declaration=True, encoding="unicode")
    print(f"  Clean SVG: {dst.name}")


def collect_outputs(src_dir: Path, dst_dir: Path, stems: list):
    """Copy specified files from src outputs to final dir, generate clean SVGs."""
    dst_dir.mkdir(parents=True, exist_ok=True)
    out = src_dir / "outputs"
    if not out.exists():
        print(f"  WARNING: {out} does not exist")
        return

    for stem in stems:
        for ext in [".svg", ".png", ".pdf"]:
            src_file = out / f"{stem}{ext}"
            if src_file.exists():
                shutil.copy2(src_file, dst_dir / src_file.name)

        svg_src = out / f"{stem}.svg"
        if svg_src.exists():
            clean_dst = dst_dir / f"{stem}_clean.svg"
            strip_text_from_svg(svg_src, clean_dst)


def main():
    FINAL.mkdir(exist_ok=True)

    # ── Fig 2: Predictive ──
    ok2 = run_script(HERE / "fig2_predictive" / "plot_fig2.py")
    if ok2:
        collect_outputs(
            HERE / "fig2_predictive",
            FINAL / "fig2_predictive",
            ["fig2_surrogate_selection"],
        )

    # ── Fig 3: Forward UQ ──
    ok3a = run_script(HERE / "fig3_forward" / "figure3_panelA_stress.py")
    ok3b = run_script(HERE / "fig3_forward" / "figure3_panelB_keff.py")
    ok3c = run_script(HERE / "fig3_forward" / "figure3_panelC_thermal.py")
    ok3 = run_script(HERE / "fig3_forward" / "figure3_compose.py")
    if ok3a or ok3b or ok3c or ok3:
        collect_outputs(
            HERE / "fig3_forward",
            FINAL / "fig3_forward",
            ["figure3_panelA_stress", "figure3_panelB_keff",
             "figure3_panelC_thermal", "figure3_composed"],
        )

    # ── Fig 4: Sobol ──
    ok4 = run_script(HERE / "fig4_sobol" / "figure4_sobol_separation.py")
    if ok4:
        collect_outputs(
            HERE / "fig4_sobol",
            FINAL / "fig4_sobol",
            ["panel_A_stress", "panel_B_keff", "panel_C_summary",
             "legend_only", "figure4_full"],
        )

    # ── Fig 5: Posterior ──
    ok5 = run_script(HERE / "fig6_posterior" / "figure5_panels_demo.py")
    if ok5:
        collect_outputs(
            HERE / "fig6_posterior",
            FINAL / "fig5_posterior",
            ["figure5_panelA", "figure5_panelB", "figure5_panelC",
             "figure5_combined"],
        )

    # ── Fig 1: Workflow ──
    ok1 = run_script(HERE / "fig0_workflow" / "figure1_workflow.py")
    if ok1:
        collect_outputs(
            HERE / "fig0_workflow",
            FINAL / "fig1_workflow",
            ["figure1_workflow"],
        )

    # ── Summary ──
    print(f"\n{'='*60}")
    print(f"ALL DONE. Output directory: {FINAL}")
    print(f"{'='*60}")
    for d in sorted(FINAL.iterdir()):
        if d.is_dir():
            files = sorted(d.glob("*.svg"))
            print(f"\n  {d.name}/")
            for f in files:
                print(f"    {f.name}")


if __name__ == "__main__":
    main()
