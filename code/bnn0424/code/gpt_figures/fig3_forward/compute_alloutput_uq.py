#!/usr/bin/env python3
"""
compute_alloutput_uq.py
=======================
Compute forward UQ statistics for ALL 15 outputs (coupled iter2 + decoupled iter1)
using the bnn-phy-mono model with 20,000 normal samples at sigma_k=1.0.

Output: forward_uq_alloutput.csv with columns:
  output, coupled_mean, coupled_std, decoupled_mean, decoupled_std

This provides the data needed for Table 2 (main text) and Supplementary Fig. S8.
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
SIGMA_K = 1.0  # 1-sigma nominal

# iter1/iter2 output pairs (7 paired outputs)
PAIRED_OUTPUTS = [
    ("iteration1_avg_fuel_temp",          "iteration2_avg_fuel_temp",          "avg_fuel_temp"),
    ("iteration1_max_fuel_temp",          "iteration2_max_fuel_temp",          "max_fuel_temp"),
    ("iteration1_max_monolith_temp",      "iteration2_max_monolith_temp",      "max_monolith_temp"),
    ("iteration1_max_global_stress",      "iteration2_max_global_stress",      "max_global_stress"),
    ("iteration1_monolith_new_temperature","iteration2_monolith_new_temperature","monolith_new_temp"),
    ("iteration1_Hcore_after",            "iteration2_Hcore_after",            "Hcore_after"),
    ("iteration1_wall2",                  "iteration2_wall2",                  "wall2"),
]

# keff is iter2-only (no iter1 counterpart)
KEFF_COL = "iteration2_keff"


def main():
    seed_all(SEED)
    device = get_device("cpu")  # local inference, no CUDA needed

    # Load model
    ckpt_path, scaler_path = _resolve_artifacts(MODEL_ID)
    print(f"Loading model from {ckpt_path}")
    model = _load_model(ckpt_path, device)
    scalers = _load_scalers(scaler_path)
    sx, sy = scalers["sx"], scalers["sy"]

    # Generate 20,000 samples at sigma_k=1.0
    nominal = np.array([DESIGN_NOMINAL[c] for c in INPUT_COLS])
    sigma_1 = np.array([DESIGN_SIGMA[c] for c in INPUT_COLS])
    rng = np.random.default_rng(SEED)
    X_samp = rng.normal(loc=nominal, scale=SIGMA_K * sigma_1,
                        size=(RISK_PROP_N_SAMPLES, len(INPUT_COLS)))
    print(f"Generated {RISK_PROP_N_SAMPLES} samples, shape={X_samp.shape}")

    # Predict using mean-weights (deterministic forward, sample=False)
    model.eval()
    with torch.no_grad():
        X_scaled = sx.transform(X_samp)
        x_t = torch.tensor(X_scaled, dtype=torch.float32, device=device)
        # Process in batches to avoid memory issues
        BATCH = 5000
        mu_all = []
        for i in range(0, len(x_t), BATCH):
            batch = x_t[i:i+BATCH]
            mu_scaled, _ = model(batch, sample=False)
            mu_np = mu_scaled.cpu().numpy()
            mu_all.append(mu_np)
        mu_scaled_all = np.concatenate(mu_all, axis=0)

    # Unscale to original space
    sy_mean = sy.mean_[np.newaxis, :]
    sy_scale = sy.scale_[np.newaxis, :]
    mu_orig = mu_scaled_all * sy_scale + sy_mean
    print(f"Predictions shape: {mu_orig.shape}")

    # Compute statistics for all outputs
    rows = []

    # Paired outputs (iter1 = decoupled, iter2 = coupled)
    for iter1_col, iter2_col, short_name in PAIRED_OUTPUTS:
        i1 = OUTPUT_COLS.index(iter1_col)
        i2 = OUTPUT_COLS.index(iter2_col)
        rows.append({
            "output": short_name,
            "iter2_col": iter2_col,
            "iter1_col": iter1_col,
            "coupled_mean": float(np.mean(mu_orig[:, i2])),
            "coupled_std": float(np.std(mu_orig[:, i2])),
            "decoupled_mean": float(np.mean(mu_orig[:, i1])),
            "decoupled_std": float(np.std(mu_orig[:, i1])),
            "delta_mean": float(np.mean(mu_orig[:, i2] - mu_orig[:, i1])),
            "std_ratio": float(np.std(mu_orig[:, i2]) / np.std(mu_orig[:, i1])) if np.std(mu_orig[:, i1]) > 0 else np.nan,
        })

    # keff (iter2 only; decoupled keff is ~constant)
    keff_idx = OUTPUT_COLS.index(KEFF_COL)
    rows.append({
        "output": "keff",
        "iter2_col": KEFF_COL,
        "iter1_col": "N/A",
        "coupled_mean": float(np.mean(mu_orig[:, keff_idx])),
        "coupled_std": float(np.std(mu_orig[:, keff_idx])),
        "decoupled_mean": np.nan,  # no iter1 keff
        "decoupled_std": np.nan,
        "delta_mean": np.nan,
        "std_ratio": np.nan,
    })

    df = pd.DataFrame(rows)
    out_path = os.path.join(_SCRIPT_DIR, "forward_uq_alloutput.csv")
    df.to_csv(out_path, index=False)
    print(f"\nSaved to {out_path}")
    print("\n" + "=" * 80)
    print("FORWARD UQ ALL-OUTPUT SUMMARY (sigma_k=1.0, N=20000, mean-weights)")
    print("=" * 80)
    for _, r in df.iterrows():
        if r['output'] == 'keff':
            print(f"  {r['output']:20s}  coupled: {r['coupled_mean']:.6f} ± {r['coupled_std']:.6f}  (no decoupled)")
        else:
            print(f"  {r['output']:20s}  coupled: {r['coupled_mean']:.2f} ± {r['coupled_std']:.2f}  "
                  f"decoupled: {r['decoupled_mean']:.2f} ± {r['decoupled_std']:.2f}  "
                  f"std_ratio: {r['std_ratio']:.3f}")


if __name__ == "__main__":
    main()
