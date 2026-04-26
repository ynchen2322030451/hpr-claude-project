#!/usr/bin/env python3
"""Regenerate training / validation curves for the 4 BNN surrogates.

Reads `bnn0414/results/training_history/training_history_<model>_fixed.json`
and writes `bnn0414/figures/figA_bnn_training_curves.{pdf,svg,png}`.

Each JSON is a list of dicts with keys: epoch, train_loss (ELBO = NLL + KL),
val_nll, and optionally kl_term. Three panels:
  (A) Training loss (ELBO)
  (B) Validation NLL
  (C) KL divergence term (BNN-specific)
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
HISTORY_DIR = ROOT / "results" / "training_history"
OUT_DIR     = ROOT / "figures"
OUT_DIR.mkdir(parents=True, exist_ok=True)

MODELS = [
    ("bnn-baseline",       "BNN Baseline",            "#808080"),
    ("bnn-data-mono",      "BNN + Data Mono",         "#1f77b4"),
    ("bnn-data-mono-ineq", "BNN + Data Mono + Ineq",  "#d62728"),
    ("bnn-phy-mono",       "BNN + Phy Mono",          "#2ca02c"),
]


def load(model: str):
    path = HISTORY_DIR / f"training_history_{model}_fixed.json"
    if not path.exists():
        print(f"  [SKIP] {path} not found")
        return None
    with open(path) as f:
        return json.load(f)


def main() -> None:
    has_kl = False
    loaded = {}
    for model, label, color in MODELS:
        rows = load(model)
        if rows is None:
            continue
        loaded[model] = rows
        if rows and "kl_term" in rows[0]:
            has_kl = True

    if not loaded:
        print("[SKIP] No training history files found. Run BNN training first.")
        return

    ncols = 3 if has_kl else 2
    fig, axes = plt.subplots(1, ncols, figsize=(4.3 * ncols, 3.4),
                             constrained_layout=True)

    for model, label, color in MODELS:
        if model not in loaded:
            continue
        rows = loaded[model]
        epochs = [r["epoch"] for r in rows]
        tr     = [r["train_loss"] for r in rows]
        val    = [r["val_nll"]    for r in rows]
        axes[0].plot(epochs, tr,  color=color, lw=1.4, label=label)
        axes[1].plot(epochs, val, color=color, lw=1.4, label=label)
        if has_kl and "kl_term" in rows[0]:
            kl = [r["kl_term"] for r in rows]
            axes[2].plot(epochs, kl, color=color, lw=1.4, label=label)

    titles = [
        ("Training loss (ELBO)", "train ELBO"),
        ("Validation NLL",       "val NLL"),
    ]
    if has_kl:
        titles.append(("KL divergence", "KL / n_train"))

    for ax, (title, ylabel) in zip(axes, titles):
        ax.set_yscale("log")
        ax.set_xlabel("epoch")
        ax.set_ylabel(ylabel)
        ax.set_title(title, fontsize=10)
        ax.grid(True, which="both", alpha=0.3, lw=0.5)

    axes[-1].legend(fontsize=7, loc="upper right", frameon=False)

    stem = OUT_DIR / "figA_bnn_training_curves"
    for ext in ("pdf", "svg", "png"):
        fig.savefig(f"{stem}.{ext}", dpi=300 if ext == "png" else None,
                    bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {stem}.pdf / .svg / .png")


if __name__ == "__main__":
    main()
