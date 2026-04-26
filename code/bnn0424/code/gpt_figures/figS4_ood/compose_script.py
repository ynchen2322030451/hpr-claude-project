"""Figure S4 — OOD Calibration (SPEC Fig S4).

(A) Epistemic inflation ratio  |  (B) coverage comparison not yet — use F2.
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt

_HERE = Path(__file__).resolve().parent
_FIG  = _HERE.parent
if str(_FIG) not in sys.path:
    sys.path.insert(0, str(_FIG))

sys.path.insert(0, str(_FIG / "bank"))

from figure_style import set_publication_rc, panel_label, FIG_WIDTH_SINGLE
from figure_io import savefig
from F2_ood_epistemic import draw as draw_f2

_BNN0414 = _FIG.parents[1]
_OUT_DIR = _BNN0414 / "manuscript" / "0414_v4" / "figures"


def compose():
    set_publication_rc()
    fig, ax = draw_f2()
    panel_label(ax, "(A)")
    written = savefig(fig, "figS4_ood", _OUT_DIR)
    for w in written:
        print("wrote", w)


if __name__ == "__main__":
    compose()
