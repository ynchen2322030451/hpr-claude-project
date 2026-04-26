"""Figure B2 — Heteroscedastic vs homoscedastic ablation (Appendix).

Directly delegates to bank/I1_homo_ablation.
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
from I1_homo_ablation import draw

_BNN0414 = _FIG.parents[1]
_OUT_DIR = _BNN0414 / "manuscript" / "0414_v4" / "figures"


def compose():
    set_publication_rc()
    fig, axes = plt.subplots(1, 2, figsize=(FIG_WIDTH_DOUBLE, 2.8))
    draw(fig=fig, axes=axes)
    panel_label(axes[0], "(A)")
    panel_label(axes[1], "(B)")
    written = savefig(fig, "figB2_homo_ablation", _OUT_DIR)
    for w in written:
        print("wrote", w)


if __name__ == "__main__":
    compose()
