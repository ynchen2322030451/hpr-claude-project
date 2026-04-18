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
    h_px, w_px = img.shape[:2]

    fig, ax = plt.subplots(1, 1, figsize=(5.0, 5.0))
    ax.imshow(img, aspect="equal")
    ax.axis("off")

    # ── annotation targets (in pixel coordinates of the image) ─────────
    # The left half-cell occupies roughly x=[50, 520], y=[0, 860]
    # The right quarter-section occupies roughly x=[560, 760], y=[30, 860]
    #
    # Annotations point to the left (larger) view for clarity.

    # Image is ~3907 x 3576 px.
    # Left half-cell: x ~ [200, 2100], y ~ [0, 3500]
    # Right quarter:  x ~ [2300, 3100], y ~ [100, 3500]
    annotations = [
        {
            "label": "Heat pipes",
            "xy": (1200, 220),          # top of half-cell, heat pipe caps
            "xytext": (2700, -100),     # text above-right
        },
        {
            "label": r"Fuel (UO$_2$)",
            "xy": (900, 1700),          # pink fuel region, mid-body left
            "xytext": (-250, 1700),     # text to the left
        },
        {
            "label": "Monolith (SS316)",
            "xy": (350, 1300),          # outer gold/brown shell, left edge
            "xytext": (-250, 1000),     # text to the left
        },
        {
            "label": "Reflector",
            "xy": (1200, 2900),         # dark teal region at bottom
            "xytext": (2700, 3100),     # text to the right, near bottom
        },
    ]

    for ann in annotations:
        ax.annotate(
            ann["label"],
            xy=ann["xy"],
            xytext=ann["xytext"],
            fontsize=_LABEL_FS,
            fontweight="medium",
            color=_LABEL_COLOR,
            arrowprops=_ARROW_PROPS,
            va="center",
            ha="left" if ann["xytext"][0] > ann["xy"][0] else "right",
        )

    # Thin border around image for publication polish
    for spine in ax.spines.values():
        spine.set_visible(False)

    fig.subplots_adjust(left=0.02, right=0.98, top=0.98, bottom=0.02)

    written = savefig(fig, "figS7_reactor_geometry", _OUT_DIR)
    for p in written:
        print(f"  wrote: {p}")


if __name__ == "__main__":
    compose()
