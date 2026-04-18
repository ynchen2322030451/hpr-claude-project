"""Figure S5 — External Baseline Calibration (SPEC Fig S5).

Reliability diagrams for MC-Dropout and Deep Ensemble.
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

from figure_style import set_publication_rc, panel_label, FIG_WIDTH_DOUBLE
from figure_io import savefig
from B8_external_baseline_calib import draw as draw_b8

_BNN0414 = _FIG.parents[1]
_OUT_DIR = _BNN0414 / "manuscript" / "0414_v4" / "figures"


def compose():
    set_publication_rc()
    fig, axes = draw_b8()
    panel_label(axes[0], "(A)")
    panel_label(axes[1], "(B)")
    written = savefig(fig, "figS5_external_calib", _OUT_DIR)
    for w in written:
        print("wrote", w)


if __name__ == "__main__":
    compose()
