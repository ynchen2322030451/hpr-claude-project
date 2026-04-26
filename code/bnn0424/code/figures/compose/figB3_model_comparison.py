"""Figure B3 — Four-model key metrics comparison (Appendix).

Directly delegates to bank/I2_model_comparison.
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

from figure_style import set_publication_rc, FIG_WIDTH_DOUBLE
from figure_io import savefig
from I2_model_comparison import draw

_BNN0414 = _FIG.parents[1]
_OUT_DIR = _BNN0414 / "manuscript" / "0414_v4" / "figures"


def compose():
    set_publication_rc()
    fig, axes = plt.subplots(2, 2, figsize=(FIG_WIDTH_DOUBLE, 4.5))
    draw(fig=fig, axes=axes.ravel())
    written = savefig(fig, "figB3_model_comparison", _OUT_DIR)
    for w in written:
        print("wrote", w)


if __name__ == "__main__":
    compose()
