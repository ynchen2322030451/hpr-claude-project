"""Unified pdf/svg/png writer for bnn0414 figures.

One call -> three files. pptx bundling is handled separately by
`export_pptx.py` (thin driver over the legacy svg2pptx package under
/code/0411/svg2pptx/).

Figure scripts must call `savefig(fig, stem, out_dir)` instead of
matplotlib's `fig.savefig` directly so the 4-format export chain stays
consistent across the main text and appendix.
"""
from __future__ import annotations

from pathlib import Path
from typing import List, Union

import matplotlib.pyplot as plt

FORMATS = ("pdf", "svg", "png")


def savefig(
    fig,
    stem: str,
    out_dir: Union[str, Path],
    dpi_png: int = 600,
    close: bool = True,
) -> List[str]:
    """Write `fig` as pdf+svg+png into `out_dir/<stem>.{ext}`.

    Returns the list of written paths. `close=True` closes the figure
    after writing, which is the default because figures are one-shot.
    """
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    written: List[str] = []
    for ext in FORMATS:
        p = out / f"{stem}.{ext}"
        kw = {"bbox_inches": "tight"}
        if ext == "png":
            kw["dpi"] = dpi_png
        fig.savefig(p, **kw)
        written.append(str(p))
    if close:
        plt.close(fig)
    return written
