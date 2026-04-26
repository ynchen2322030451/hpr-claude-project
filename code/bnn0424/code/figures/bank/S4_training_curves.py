"""S4 — Training curves for physics-regularized and reference BNNs (SI Fig. S4).

2x1 layout: (a) Training loss vs epoch, (b) Validation RMSE vs epoch.
Both models shown on each panel for direct comparison.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt

_HERE = Path(__file__).resolve().parent
_FIG  = _HERE.parent
if str(_FIG) not in sys.path:
    sys.path.insert(0, str(_FIG))

from figure_style import (
    set_publication_rc, finalize_axes, panel_label,
    C, LW, FS, FIG_WIDTH_DOUBLE,
)
from figure_io import savefig

_BNN0424 = _FIG.parents[1]
_HIST_PHY = (_BNN0424 / "code" / "models" / "bnn-phy-mono" /
             "artifacts" / "training_history_bnn-phy-mono_fixed.json")
_HIST_REF = (_BNN0424 / "code" / "models" / "bnn-baseline" /
             "artifacts" / "training_history_bnn-baseline_fixed.json")
_OUT_DIR  = _BNN0424 / "manuscript" / "0414_v4" / "figures" / "bank"


def load(path):
    with open(path) as f:
        rows = json.load(f)
    epochs = [r["epoch"] for r in rows]
    loss   = [r["train_loss"] for r in rows]
    rmse   = [r["val_rmse"] for r in rows]
    return epochs, loss, rmse


def draw():
    ep_phy, loss_phy, rmse_phy = load(_HIST_PHY)
    ep_ref, loss_ref, rmse_ref = load(_HIST_REF)

    set_publication_rc()
    fig, (ax_loss, ax_rmse) = plt.subplots(
        1, 2, figsize=(FIG_WIDTH_DOUBLE, FIG_WIDTH_DOUBLE * 0.38),
        constrained_layout=True,
    )

    ax_loss.plot(ep_phy, loss_phy, color=C["main"], lw=LW["main"],
                 label="Physics-regularized")
    ax_loss.plot(ep_ref, loss_ref, color=C["reference"], lw=LW["main"],
                 ls="--", label="Reference")
    ax_loss.set_xlabel("Epoch")
    ax_loss.set_ylabel("Training loss")
    ax_loss.legend(fontsize=FS["legend"], loc="upper right")
    finalize_axes(ax_loss)
    panel_label(ax_loss, "(a)")

    ax_rmse.plot(ep_phy, rmse_phy, color=C["main"], lw=LW["main"],
                 label="Physics-regularized")
    ax_rmse.plot(ep_ref, rmse_ref, color=C["reference"], lw=LW["main"],
                 ls="--", label="Reference")
    ax_rmse.set_xlabel("Epoch")
    ax_rmse.set_ylabel("Validation RMSE")
    ax_rmse.legend(fontsize=FS["legend"], loc="upper right")
    finalize_axes(ax_rmse)
    panel_label(ax_rmse, "(b)")

    return fig


def main():
    fig = draw()
    written = savefig(fig, "S4_training_curves", _OUT_DIR)
    for w in written:
        print("wrote", w)


if __name__ == "__main__":
    main()
