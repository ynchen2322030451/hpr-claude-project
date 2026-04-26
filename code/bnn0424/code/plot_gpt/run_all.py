#!/usr/bin/env python3
"""
run_all.py — One-click regeneration of all figures + PPTs.

Usage:
    python run_all.py              # rebuild everything
    python run_all.py fig3         # rebuild fig3 only
    python run_all.py fig2 fig4    # rebuild fig2 and fig4 only

Each figure folder is self-contained:
    1. Run plot script(s) → outputs/*.{pdf,svg,png}
    2. Run PPT script     → outputs/*.pptx
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

FIGURES = {
    "fig1": {
        "plot": ["fig1_workflow/figure1_workflow.py"],
        "ppt":  "fig1_workflow/figure1_to_ppt.py",
    },
    "fig2": {
        "plot": ["fig2_surrogate_selection/plot_fig2.py"],
        "ppt":  "fig2_surrogate_selection/figure2_to_ppt.py",
    },
    "fig3": {
        "plot": [
            "fig3_forward_uq/figure3_panelA_stress.py",
            "fig3_forward_uq/figure3_panelB_keff.py",
            "fig3_forward_uq/figure3_panelC_thermal.py",
            "fig3_forward_uq/figure3_compose.py",
        ],
        "ppt":  "fig3_forward_uq/figure3_to_ppt.py",
    },
    "fig4": {
        "plot": ["fig4_sobol/figure4_sobol_separation.py"],
        "ppt":  "fig4_sobol/figure4_to_ppt.py",
    },
    "fig5": {
        "plot": ["fig5_posterior/figure5_panels_demo.py"],
        "ppt":  "fig5_posterior/figure5_to_ppt.py",
    },
    "overview": {
        "plot": ["figure_overview.py"],
        "ppt":  "overview_to_ppt.py",
    },
}


def run_script(script_path: Path) -> bool:
    rel = script_path.relative_to(ROOT)
    print(f"  Running {rel} ... ", end="", flush=True)
    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=str(ROOT),
        capture_output=True, text=True,
    )
    if result.returncode == 0:
        print("OK")
        return True
    else:
        print("FAILED")
        if result.stderr:
            for line in result.stderr.strip().split("\n")[-5:]:
                print(f"    {line}")
        return False


def build_figure(name: str) -> bool:
    cfg = FIGURES[name]
    print(f"\n{'='*50}")
    print(f"  {name.upper()}")
    print(f"{'='*50}")

    ok = True
    for script in cfg["plot"]:
        if not run_script(ROOT / script):
            ok = False

    if ok and cfg.get("ppt"):
        run_script(ROOT / cfg["ppt"])

    return ok


def main():
    targets = sys.argv[1:] if len(sys.argv) > 1 else list(FIGURES.keys())

    for t in targets:
        t = t.lower().replace("figure", "fig").replace("_", "")
        if t not in FIGURES:
            print(f"Unknown figure: {t}  (available: {', '.join(FIGURES.keys())})")
            continue
        build_figure(t)

    print(f"\n{'='*50}")
    print("  DONE")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
