"""P0 smoke test for the bnn0414 figure export pipeline.

Purpose: confirm the 4-format export chain (pdf/svg/png + pptx) is wired
up end to end BEFORE any real main-text figure is drawn. Produces a
throwaway placeholder figure under .../figures/_smoke/ and verifies every
expected output file exists with non-zero size.

Run:
    python code/bnn0414/code/figures/smoke_test.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from figure_io import FORMATS, savefig
from figure_style import COLORS, LINEWIDTHS, apply_rc, clean_ax, panel_label
from export_pptx import batch as pptx_batch

OUT_DIR = _HERE.parents[1] / "manuscript" / "0414_v4" / "figures" / "_smoke"


def _placeholder_figure():
    x = np.linspace(0.0, 1.0, 100)
    fig, ax = plt.subplots(figsize=(3.4, 2.2))
    ax.plot(x, x ** 2, color=COLORS["bnn_main"], lw=LINEWIDTHS["main"],
            label="placeholder")
    ax.plot(x, x,       color=COLORS["reference_line"],
            lw=LINEWIDTHS["ref"], ls="--", label="y = x")
    ax.set_xlabel("x"); ax.set_ylabel("y")
    ax.legend(loc="upper left")
    clean_ax(ax)
    panel_label(ax, "(A)")
    return fig


def main() -> None:
    apply_rc()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    fig = _placeholder_figure()
    written = savefig(fig, "smoke", OUT_DIR)

    missing = []
    for ext in FORMATS:
        p = OUT_DIR / f"smoke.{ext}"
        if not p.exists() or p.stat().st_size == 0:
            missing.append(str(p))
    if missing:
        raise SystemExit("missing/empty outputs: " + "; ".join(missing))
    for w in written:
        print("wrote", w, "(", Path(w).stat().st_size, "bytes )")

    pptx_path = OUT_DIR / "smoke.pptx"
    pptx_batch(str(OUT_DIR), str(pptx_path), pattern="smoke.svg")
    if not pptx_path.exists() or pptx_path.stat().st_size == 0:
        raise SystemExit(f"pptx missing/empty: {pptx_path}")
    print("wrote", pptx_path, "(", pptx_path.stat().st_size, "bytes )")

    print("P0 smoke test OK")


if __name__ == "__main__":
    main()
