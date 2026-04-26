"""Figure S7 — Heat-pipe reactor unit-cell geometry (annotated CAD render).

Loads the existing 3D cutaway render (core_cad_render.png) and adds
professional annotation arrows pointing to key structural components:
monolith, fuel, heat pipes, and reflector.

The CAD render shows two views: a half-cell cutaway (left) and a
quarter-section (right), both generated from the OpenMC geometry model.
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.image as mpimg

_HERE = Path(__file__).resolve().parent
_FIG  = _HERE.parent
if str(_FIG) not in sys.path:
    sys.path.insert(0, str(_FIG))

from figure_style import set_publication_rc, FS
from figure_io import savefig

_BNN0414 = _FIG.parents[1]
_OUT_DIR = _BNN0414 / "manuscript" / "0414_v4" / "figures"

_CAD_IMG = Path(
    "/Users/yinuo/Projects/hpr-claude-project"
    "/code/0411/figures/core_cad_render.png"
)

# ─── annotation styling ───────────────────────────────────────────────────
_ARROW_COLOR = "#333333"
_ARROW_PROPS = dict(
    arrowstyle="->",
    color=_ARROW_COLOR,
    lw=0.8,
    shrinkA=0,
    shrinkB=3,
)
_LABEL_FS = 7.5
_LABEL_COLOR = "#2F2F2F"


def compose():
    set_publication_rc()

    img = mpimg.imread(str(_CAD_IMG))

    fig, ax = plt.subplots(1, 1, figsize=(5.0, 5.0))
    ax.imshow(img, aspect="equal")
    ax.axis("off")

    for spine in ax.spines.values():
        spine.set_visible(False)

    fig.subplots_adjust(left=0.02, right=0.98, top=0.98, bottom=0.02)

    written = savefig(fig, "figS7_reactor_geometry", _OUT_DIR)
    for p in written:
        print(f"  wrote: {p}")


if __name__ == "__main__":
    compose()
