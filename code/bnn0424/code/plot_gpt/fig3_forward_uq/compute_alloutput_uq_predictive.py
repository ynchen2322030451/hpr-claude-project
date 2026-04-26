#!/usr/bin/env python3
"""
compute_alloutput_uq_predictive.py
===================================
Forward UQ for ALL 15 outputs using predictive draw (MC + aleatoric noise).
Matches the canonical D1 approach used for stress/keff in the main manuscript.

sigma_k=1.0, N=20000, n_mc=50
"""

import os, sys, json
import numpy as np
import pandas as pd
import torch

# ── path setup ──
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_CODE_ROOT = os.path.abspath(os.path.join(_SCRIPT_DIR, '..', '..'))
_BNN_CONFIG_DIR = os.path.join(_CODE_ROOT, 'experiments_0404', 'config')
_BNN_EVAL_DIR = os.path.join(_CODE_ROOT, 'experiments_0404', 'evaluation')
_BNN_EXPT_DIR = os.path.join(_CODE_ROOT, 'experiments_0404', 'experiments')

for _p in (_CODE_ROOT, _BNN_CONFIG_DIR, _BNN_EVAL_DIR, _BNN_EXPT_DIR,
           os.path.join(_CODE_ROOT, 'experiments_0404')):
    if _p and os.path.isdir(_p) and _p not in sys.path:
        sys.path.insert(0, _p)

from experiment_config_0404 import (
    INPUT_COLS, OUTPUT_COLS,
    DESIGN_NOMINAL, DESIGN_SIGMA,
    RISK_PROP_N_SAMPLES, SEED, DEVICE,
    BNN_N_MC_EVAL,
)
from run_eval_0404 import _resolve_artifacts, _load_model, _load_scalers
from bnn_model import mc_predict, get_device, seed_all

MODEL_ID = "bnn-phy-mono"
SIGMA_K = 1.0

# iter1/iter2 output pairs
PAIRED_OUTPUTS = [
    ("iteration1_max_fuel_temp",          "iteration2_max_fuel_temp",          "Max fuel temp (K)"),
    ("iteration1_max_monolith_temp",      "iteration2_max_monolith_temp",      "Max monolith temp (K)"),
    ("iteration1_max_global_stress",      "iteration2_max_global_stress",      "Peak stress (MPa)"),
    ("iteration1_wall2",                  "iteration2_wall2",                  "Wall expansion (mm)"),
]
KEFF_COL = "iteration2_keff"


def main():
    seed_all(SEED)
    device = get_device("cpu")

    ckpt_path, scaler_path = _resolve_artifacts(MODEL_ID)
    print(f"Loading model from {ckpt_path}")
    model = _load_model(ckpt_path, device)
    scalers = _load_scalers(scaler_path)
    sx, sy = scalers["sx"], scalers["sy"]

    nominal = np.array([DESIGN_NOMINAL[c] for c in INPUT_COLS])
    sigma_1 = np.array([DESIGN_SIGMA[c] for c in INPUT_COLS])
    rng = np.random.default_rng(SEED)
    X_samp = rng.normal(loc=nominal, scale=SIGMA_K * sigma_1,
                        size=(RISK_PROP_N_SAMPLES, len(INPUT_COLS)))
    print(f"Generated {RISK_PROP_N_SAMPLES} samples")

    # MC prediction in batches
    BATCH = 2000
    mu_all, sigma_all = [], []
    for i in range(0, len(X_samp), BATCH):
        print(f"  Batch {i//BATCH + 1}/{(len(X_samp)-1)//BATCH + 1}...")
        batch = X_samp[i:i+BATCH]
        mu_mean, mu_std, ale_var, epi_var, total_var = mc_predict(
            model, batch, sx, sy, device, n_mc=BNN_N_MC_EVAL
        )
        mu_all.append(mu_mean)
        sigma_all.append(np.sqrt(total_var))

    mu = np.concatenate(mu_all, axis=0)       # (20000, 15)
    sigma = np.concatenate(sigma_all, axis=0)  # (20000, 15)

    # Predictive draw: y = mu + sigma * eps
    eps = rng.standard_normal(size=mu.shape)
    y_draw = mu + sigma * eps

    print(f"\nPredictions shape: {y_draw.shape}")

    # Compute stats
    rows = []
    for iter1_col, iter2_col, label in PAIRED_OUTPUTS:
        i1 = OUTPUT_COLS.index(iter1_col)
        i2 = OUTPUT_COLS.index(iter2_col)
        c_mean = float(np.mean(y_draw[:, i2]))
        c_std = float(np.std(y_draw[:, i2]))
        d_mean = float(np.mean(y_draw[:, i1]))
        d_std = float(np.std(y_draw[:, i1]))
        rows.append({
            "label": label,
            "coupled_mean": c_mean,
            "coupled_std": c_std,
            "decoupled_mean": d_mean,
            "decoupled_std": d_std,
            "std_reduction_pct": (d_std - c_std) / d_std * 100 if d_std > 0 else 0,
        })

    keff_idx = OUTPUT_COLS.index(KEFF_COL)
    rows.append({
        "label": "k_eff",
        "coupled_mean": float(np.mean(y_draw[:, keff_idx])),
        "coupled_std": float(np.std(y_draw[:, keff_idx])),
        "decoupled_mean": float('nan'),
        "decoupled_std": float('nan'),
        "std_reduction_pct": float('nan'),
    })

    df = pd.DataFrame(rows)
    out_path = os.path.join(_SCRIPT_DIR, "forward_uq_alloutput_predictive.csv")
    df.to_csv(out_path, index=False)

    print("\n" + "=" * 90)
    print("FORWARD UQ ALL-OUTPUT (predictive draw, sigma_k=1.0, N=20000, n_mc=50)")
    print("=" * 90)
    print(f"  {'Output':25s} {'Coupled mean':>14s} {'Coupled s.d.':>14s} {'Decoupled mean':>16s} {'Decoupled s.d.':>16s} {'Std red.':>8s}")
    print("-" * 90)
    for _, r in df.iterrows():
        if r['label'] == 'k_eff':
            print(f"  {r['label']:25s} {r['coupled_mean']:14.6f} {r['coupled_std']:14.6f} {'~constant':>16s} {'~0':>16s}")
        else:
            print(f"  {r['label']:25s} {r['coupled_mean']:14.2f} {r['coupled_std']:14.2f} {r['decoupled_mean']:16.2f} {r['decoupled_std']:16.2f} {r['std_reduction_pct']:7.1f}%")


if __name__ == "__main__":
    main()
