#!/usr/bin/env python3
"""Regenerate Fig A8: training / validation curves for the 5 surrogates.

Reads `0411/results/training_history/training_history_<model>_fixed.json`
and writes `0411/figures/figA8_training_curves.{pdf,svg,png}`. No retraining.

Each JSON is a list of dicts with keys: epoch, train_loss (Gaussian NLL,
unnormalised target scale) and val_nll (Gaussian NLL on the validation
split). Curves are drawn on a shared semilog-y axis so the 5 runs can be
compared directly at a glance.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
HISTORY_DIR = ROOT / "results" / "training_history"
OUT_DIR     = ROOT / "figures"
OUT_DIR.mkdir(parents=True, exist_ok=True)

MODELS = [
    ("baseline",       "Baseline",              "#808080"),
    ("data-mono",      "Data + mono",           "#1f77b4"),
    ("data-mono-ineq", "Data + mono + ineq",    "#d62728"),
    ("phy-mono",       "Phy + mono",            "#2ca02c"),
    ("phy-ineq",       "Phy + ineq",            "#9467bd"),
]


def load(model: str):
    path = HISTORY_DIR / f"training_history_{model}_fixed.json"
    with open(path) as f:
        return json.load(f)


def main() -> None:
    fig, axes = plt.subplots(1, 2, figsize=(8.6, 3.4), constrained_layout=True)
    ax_tr, ax_val = axes

    for model, label, color in MODELS:
        rows = load(model)
        epochs = [r["epoch"] for r in rows]
        tr     = [r["train_loss"] for r in rows]
        val    = [r["val_nll"]    for r in rows]
        ax_tr.plot(epochs, tr,  color=color, lw=1.4, label=label)
        ax_val.plot(epochs, val, color=color, lw=1.4, label=label)

    for ax, title, ylabel in (
        (ax_tr,  "Training loss",      "train NLL (unnormalised)"),
        (ax_val, "Validation loss",    "val NLL (standardised)"),
    ):
        ax.set_yscale("log")
        ax.set_xlabel("epoch")
        ax.set_ylabel(ylabel)
        ax.set_title(title, fontsize=10)
        ax.grid(True, which="both", alpha=0.3, lw=0.5)

    ax_val.legend(fontsize=7, loc="upper right", frameon=False)

    stem = OUT_DIR / "figA8_training_curves"
    for ext in ("pdf", "svg", "png"):
        fig.savefig(f"{stem}.{ext}", dpi=300 if ext == "png" else None,
                    bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {stem}.pdf / .svg / .png")


if __name__ == "__main__":
    main()
