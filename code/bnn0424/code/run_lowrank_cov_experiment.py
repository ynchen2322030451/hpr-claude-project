#!/usr/bin/env python3
"""
Low-rank covariance BNN experiment (model_rescue: Route A)
==========================================================
Tests whether replacing diagonal Gaussian likelihood with
low-rank multivariate Gaussian improves NLL / CRPS / calibration.

Architecture:
  BayesianMLP backbone (same as bnn-phy-mono)
  + mu head (5 primary outputs)
  + diag_logvar head (5 outputs — diagonal variance)
  + factor head (5 x rank — low-rank covariance factors)

  Sigma(x) = diag(sigma^2(x)) + L(x) L(x)^T
  where L is (5, rank) predicted per sample.

Likelihood: multivariate Gaussian with low-rank + diagonal covariance.

Outputs: 5 primary coupled outputs only:
  iteration2_keff, iteration2_max_fuel_temp, iteration2_max_monolith_temp,
  iteration2_max_global_stress, iteration2_wall2

Usage:
  cd /home/tjzs/Documents/fenics_data/fenics_data/bnn0414/code
  conda activate pytorch-env
  python run_lowrank_cov_experiment.py

Results saved to:
  results_v3418/models/bnn-lowrank-cov/
"""

import os, sys, json, math, time, logging
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, TensorDataset
from sklearn.preprocessing import StandardScaler
import joblib

# ── Path setup ──
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_BNN_CODE_DIR = _SCRIPT_DIR
while _BNN_CODE_DIR and os.path.basename(_BNN_CODE_DIR) != 'code':
    _BNN_CODE_DIR = os.path.dirname(_BNN_CODE_DIR)

_BNN_CONFIG_DIR = os.path.join(_BNN_CODE_DIR, 'experiments_0404', 'config')
_ROOT_0310 = os.path.join(os.path.dirname(os.path.dirname(_BNN_CODE_DIR)), '0310')

for _p in (_SCRIPT_DIR, _BNN_CODE_DIR, _BNN_CONFIG_DIR, _ROOT_0310):
    if _p and os.path.isdir(_p) and _p not in sys.path:
        sys.path.insert(0, _p)

from experiment_config_0404 import (
    INPUT_COLS, OUTPUT_COLS, SEED, FIXED_SPLIT_DIR,
    get_csv_path, DEVICE, BNN_N_MC_EVAL,
)
from bnn_model import BayesianLinear, seed_all, get_device

# ── Constants ──
PRIMARY_5 = [
    "iteration2_keff",
    "iteration2_max_fuel_temp",
    "iteration2_max_monolith_temp",
    "iteration2_max_global_stress",
    "iteration2_wall2",
]
PRIMARY_IDX = [OUTPUT_COLS.index(c) for c in PRIMARY_5]
N_OUT = len(PRIMARY_5)
N_IN = len(INPUT_COLS)

RANK = 2
EXPERIMENT_NAME = "bnn-lowrank-cov"


# ============================================================
# Model: Low-rank covariance BNN
# ============================================================

class BayesianMLP_LowRankCov(nn.Module):
    """
    BNN with low-rank + diagonal covariance output head.

    Predicts:
      mu(x)      : (batch, n_out) — mean
      diag_lv(x) : (batch, n_out) — log diagonal variance
      L(x)       : (batch, n_out, rank) — low-rank factors

    Covariance: Sigma = diag(exp(diag_lv)) + L @ L^T
    """

    def __init__(self, in_dim, out_dim, width, depth, rank=2,
                 prior_sigma=1.0):
        super().__init__()
        self.out_dim = out_dim
        self.rank = rank

        layers = nn.ModuleList()
        d = in_dim
        for _ in range(depth):
            layers.append(BayesianLinear(d, width, prior_sigma=prior_sigma))
            d = width
        self.backbone = layers
        self.act = nn.SiLU()

        self.mu_head = BayesianLinear(d, out_dim, prior_sigma=prior_sigma)
        self.diag_head = BayesianLinear(d, out_dim, prior_sigma=prior_sigma)
        self.factor_head = BayesianLinear(d, out_dim * rank, prior_sigma=prior_sigma)

    def forward(self, x, sample=True):
        z = x
        for layer in self.backbone:
            z = self.act(layer(z, sample=sample))

        mu = self.mu_head(z, sample=sample)
        diag_lv = self.diag_head(z, sample=sample).clamp(-20, 5)
        L_flat = self.factor_head(z, sample=sample)
        L = L_flat.view(-1, self.out_dim, self.rank) * 0.1

        return mu, diag_lv, L

    def kl_divergence(self):
        kl = torch.tensor(0.0, device=next(self.parameters()).device)
        for layer in self.backbone:
            kl = kl + layer.kl_divergence()
        kl = kl + self.mu_head.kl_divergence()
        kl = kl + self.diag_head.kl_divergence()
        kl = kl + self.factor_head.kl_divergence()
        return kl


# ============================================================
# Loss: Multivariate Gaussian NLL with low-rank covariance
# ============================================================

def mv_nll_lowrank(y, mu, diag_lv, L, eps=1e-6):
    """
    Negative log-likelihood of N(mu, diag(d) + L L^T).

    Uses Woodbury identity for efficient computation:
      Sigma^{-1} = D^{-1} - D^{-1} L (I + L^T D^{-1} L)^{-1} L^T D^{-1}
      log|Sigma| = log|D| + log|I + L^T D^{-1} L|

    y, mu: (batch, n)
    diag_lv: (batch, n)
    L: (batch, n, r)
    """
    batch, n = y.shape
    r = L.shape[2]

    d = torch.exp(diag_lv).clamp(min=eps)  # (batch, n)
    d_inv = 1.0 / d  # (batch, n)

    residual = y - mu  # (batch, n)

    # M = I_r + L^T D^{-1} L  — (batch, r, r)
    # L^T D^{-1}: (batch, r, n) * (batch, n) -> use einsum
    Lt_Dinv = L.transpose(1, 2) * d_inv.unsqueeze(1)  # (batch, r, n)
    M = torch.eye(r, device=y.device).unsqueeze(0) + torch.bmm(Lt_Dinv, L)  # (batch, r, r)

    # Cholesky of M for stable inverse and log-det
    try:
        chol_M = torch.linalg.cholesky(M)
    except RuntimeError:
        M = M + eps * torch.eye(r, device=y.device).unsqueeze(0)
        chol_M = torch.linalg.cholesky(M)

    # log|Sigma| = sum log(d) + 2 * sum log(diag(chol_M))
    log_det_D = diag_lv.sum(dim=1)  # (batch,)
    log_det_M = 2.0 * torch.log(torch.diagonal(chol_M, dim1=1, dim2=2) + eps).sum(dim=1)
    log_det = log_det_D + log_det_M  # (batch,)

    # quadratic form: r^T Sigma^{-1} r
    # = r^T D^{-1} r - r^T D^{-1} L M^{-1} L^T D^{-1} r
    Dinv_r = d_inv * residual  # (batch, n)
    quad_diag = (residual * Dinv_r).sum(dim=1)  # (batch,)

    # v = L^T D^{-1} r — (batch, r)
    v = torch.bmm(Lt_Dinv, residual.unsqueeze(2)).squeeze(2)  # (batch, r)
    # solve M w = v
    w = torch.cholesky_solve(v.unsqueeze(2), chol_M).squeeze(2)  # (batch, r)
    quad_correction = (v * w).sum(dim=1)  # (batch,)

    quad = quad_diag - quad_correction  # (batch,)

    nll = 0.5 * (n * math.log(2 * math.pi) + log_det + quad)
    return nll.mean()


# ============================================================
# Diagonal-only baseline for fair comparison
# ============================================================

def diag_nll(y, mu, diag_lv, eps=1e-8):
    d = torch.exp(diag_lv).clamp(min=eps)
    return 0.5 * (math.log(2 * math.pi) + diag_lv + (y - mu)**2 / d).mean()


# ============================================================
# Data loading
# ============================================================

def load_data(device):
    split_dir = os.environ.get("HPR_FIXED_SPLIT_DIR", FIXED_SPLIT_DIR)
    train_csv = os.path.join(split_dir, "train.csv")
    val_csv = os.path.join(split_dir, "val.csv")
    test_csv = os.path.join(split_dir, "test.csv")

    if os.path.exists(train_csv):
        df_train = pd.read_csv(train_csv)
        df_val = pd.read_csv(val_csv)
        df_test = pd.read_csv(test_csv)
    else:
        csv_path = get_csv_path()
        if csv_path is None:
            raise FileNotFoundError("Cannot find dataset or split CSVs")
        df = pd.read_csv(csv_path)
        train_idx = np.load(os.path.join(split_dir, "train_idx.npy"))
        val_idx = np.load(os.path.join(split_dir, "val_idx.npy"))
        test_idx = np.load(os.path.join(split_dir, "test_idx.npy"))
        df_train = df.iloc[train_idx]
        df_val = df.iloc[val_idx]
        df_test = df.iloc[test_idx]

    avail_output_cols = [c for c in OUTPUT_COLS if c in df_train.columns]
    avail_primary = [c for c in PRIMARY_5 if c in df_train.columns]
    primary_idx_in_avail = [avail_output_cols.index(c) for c in avail_primary]

    X_train = df_train[INPUT_COLS].values.astype(np.float32)
    X_val = df_val[INPUT_COLS].values.astype(np.float32)
    X_test = df_test[INPUT_COLS].values.astype(np.float32)

    Y_train = df_train[avail_primary].values.astype(np.float32)
    Y_val = df_val[avail_primary].values.astype(np.float32)
    Y_test_raw = df_test[avail_primary].values.astype(np.float32)

    scaler_X = StandardScaler().fit(X_train)
    scaler_Y = StandardScaler().fit(Y_train)

    X_train_s = scaler_X.transform(X_train)
    X_val_s = scaler_X.transform(X_val)
    X_test_s = scaler_X.transform(X_test)
    Y_train_s = scaler_Y.transform(Y_train)
    Y_val_s = scaler_Y.transform(Y_val)
    Y_test_s = scaler_Y.transform(Y_test_raw)

    to_t = lambda a: torch.tensor(a, dtype=torch.float32, device=device)

    return {
        "X_train": to_t(X_train_s), "Y_train": to_t(Y_train_s),
        "X_val": to_t(X_val_s), "Y_val": to_t(Y_val_s),
        "X_test": to_t(X_test_s), "Y_test": to_t(Y_test_s),
        "scaler_X": scaler_X, "scaler_Y": scaler_Y,
        "n_train": len(X_train), "n_val": len(X_val), "n_test": len(X_test),
        "Y_test_raw": Y_test_raw,
    }


# ============================================================
# Training loop
# ============================================================

def train_one_model(data, config, device, use_lowrank=True):
    n_train = data["n_train"]

    if use_lowrank:
        model = BayesianMLP_LowRankCov(
            N_IN, N_OUT, config["width"], config["depth"],
            rank=config.get("rank", RANK),
            prior_sigma=config["prior_sigma"],
        ).to(device)
    else:
        from bnn_model import BayesianMLP
        model = BayesianMLP(
            N_IN, N_OUT, config["width"], config["depth"],
            prior_sigma=config["prior_sigma"],
        ).to(device)

    optimizer = torch.optim.Adam(model.parameters(), lr=config["lr"])
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
        optimizer, T_max=config["epochs"], eta_min=1e-6)

    ds = TensorDataset(data["X_train"], data["Y_train"])
    loader = DataLoader(ds, batch_size=config["batch"], shuffle=True, drop_last=False)

    best_val = float("inf")
    best_state = None
    patience_counter = 0

    for epoch in range(1, config["epochs"] + 1):
        model.train()
        epoch_loss = 0.0
        for xb, yb in loader:
            optimizer.zero_grad()

            if use_lowrank:
                mu, diag_lv, L = model(xb, sample=True)
                nll = mv_nll_lowrank(yb, mu, diag_lv, L)
            else:
                mu, logvar = model(xb, sample=True)
                nll = diag_nll(yb, mu, logvar)

            kl = model.kl_divergence()
            loss = nll + config["kl_weight"] * kl / n_train
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), config.get("clip", 5.0))
            optimizer.step()
            epoch_loss += loss.item() * xb.shape[0]

        scheduler.step()
        epoch_loss /= n_train

        # Validation
        model.eval()
        with torch.no_grad():
            if use_lowrank:
                mu_v, dlv_v, L_v = model(data["X_val"], sample=False)
                val_nll = mv_nll_lowrank(data["Y_val"], mu_v, dlv_v, L_v).item()
            else:
                mu_v, lv_v = model(data["X_val"], sample=False)
                val_nll = diag_nll(data["Y_val"], mu_v, lv_v).item()

        if val_nll < best_val - 1e-6:
            best_val = val_nll
            best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}
            patience_counter = 0
        else:
            patience_counter += 1

        if epoch % 20 == 0 or epoch == 1:
            print(f"  Epoch {epoch:4d} | train_loss={epoch_loss:.4f} | val_nll={val_nll:.4f} | best={best_val:.4f} | pat={patience_counter}")

        if patience_counter >= config.get("patience", 40):
            print(f"  Early stopping at epoch {epoch}")
            break

    model.load_state_dict(best_state)
    model.to(device)
    return model, best_val


# ============================================================
# Evaluation
# ============================================================

def evaluate(model, data, device, scaler_Y, use_lowrank=True, n_mc=50):
    model.eval()
    X_test = data["X_test"]
    Y_test = data["Y_test"]
    Y_test_raw = data["Y_test_raw"]
    n_test = X_test.shape[0]

    mus_all = []
    vars_all = []

    with torch.no_grad():
        for _ in range(n_mc):
            if use_lowrank:
                mu, dlv, L = model(X_test, sample=True)
                diag_var = torch.exp(dlv)
                cov_correction = torch.bmm(L, L.transpose(1, 2))
                total_var = diag_var + torch.diagonal(cov_correction, dim1=1, dim2=2)
            else:
                mu, logvar = model(X_test, sample=True)
                total_var = torch.exp(logvar)
            mus_all.append(mu.cpu().numpy())
            vars_all.append(total_var.cpu().numpy())

    mus_all = np.array(mus_all)  # (n_mc, n_test, n_out)
    vars_all = np.array(vars_all)

    # Predictive mean and variance (law of total variance)
    pred_mean = mus_all.mean(axis=0)  # (n_test, n_out)
    epistemic_var = mus_all.var(axis=0)
    aleatoric_var = vars_all.mean(axis=0)
    total_pred_var = epistemic_var + aleatoric_var
    pred_std = np.sqrt(total_pred_var)

    # Convert back to physical space
    pred_mean_phys = scaler_Y.inverse_transform(pred_mean)
    pred_std_phys = pred_std * scaler_Y.scale_

    # Metrics in physical space
    y_true = Y_test_raw
    residuals = y_true - pred_mean_phys

    per_output = {}
    for j, name in enumerate(PRIMARY_5):
        r = residuals[:, j]
        mae = np.abs(r).mean()
        rmse = np.sqrt((r**2).mean())
        ss_res = (r**2).sum()
        ss_tot = ((y_true[:, j] - y_true[:, j].mean())**2).sum()
        r2 = 1 - ss_res / max(ss_tot, 1e-12)

        # PICP and MPIW (90%)
        z90 = 1.645
        lo = pred_mean_phys[:, j] - z90 * pred_std_phys[:, j]
        hi = pred_mean_phys[:, j] + z90 * pred_std_phys[:, j]
        in_interval = ((y_true[:, j] >= lo) & (y_true[:, j] <= hi)).mean()
        interval_width = (hi - lo).mean()

        # CRPS (Gaussian approximation)
        s = pred_std_phys[:, j]
        z = (y_true[:, j] - pred_mean_phys[:, j]) / (s + 1e-12)
        from scipy.stats import norm
        crps_vals = s * (z * (2 * norm.cdf(z) - 1) + 2 * norm.pdf(z) - 1 / math.sqrt(math.pi))
        crps = crps_vals.mean()

        per_output[name] = {
            "MAE": float(mae), "RMSE": float(rmse), "R2": float(r2),
            "PICP90": float(in_interval), "MPIW90": float(interval_width),
            "CRPS": float(crps),
        }

    # Compute NLL on test set (normalised space)
    model.eval()
    with torch.no_grad():
        if use_lowrank:
            mu_t, dlv_t, L_t = model(X_test, sample=False)
            test_nll = mv_nll_lowrank(Y_test, mu_t, dlv_t, L_t).item()
        else:
            mu_t, lv_t = model(X_test, sample=False)
            test_nll = diag_nll(Y_test, mu_t, lv_t).item()

    # Means across outputs
    mean_metrics = {
        "MAE_mean": np.mean([v["MAE"] for v in per_output.values()]),
        "RMSE_mean": np.mean([v["RMSE"] for v in per_output.values()]),
        "R2_mean": np.mean([v["R2"] for v in per_output.values()]),
        "CRPS_mean": np.mean([v["CRPS"] for v in per_output.values()]),
        "PICP_mean": np.mean([v["PICP90"] for v in per_output.values()]),
        "MPIW_mean": np.mean([v["MPIW90"] for v in per_output.values()]),
        "test_NLL": test_nll,
    }

    # Energy score (multivariate proper scoring rule)
    # ES = E||Y - X|| - 0.5 E||X - X'||
    # where X, X' are independent draws from predictive
    n_es_mc = min(n_mc, 50)
    y_true_norm = Y_test.cpu().numpy()
    es_term1 = 0.0
    es_term2 = 0.0
    for i in range(n_es_mc):
        diff = y_true_norm - mus_all[i]
        es_term1 += np.sqrt((diff**2).sum(axis=1)).mean()
    es_term1 /= n_es_mc
    for i in range(0, n_es_mc - 1, 2):
        diff = mus_all[i] - mus_all[i+1]
        es_term2 += np.sqrt((diff**2).sum(axis=1)).mean()
    es_term2 /= max(n_es_mc // 2, 1)
    energy_score = es_term1 - 0.5 * es_term2
    mean_metrics["energy_score"] = float(energy_score)

    return per_output, mean_metrics


# ============================================================
# Main
# ============================================================

def main():
    seed_all(SEED)
    device = get_device(DEVICE)
    print(f"Device: {device}")

    # Output directory
    _BNN_ROOT = os.path.dirname(_BNN_CODE_DIR)  # bnn0414/
    out_dir = os.path.join(_BNN_ROOT, "results_v3418", "models", EXPERIMENT_NAME)
    os.makedirs(out_dir, exist_ok=True)
    print(f"Output dir: {out_dir}")

    # Load data
    print("Loading data...")
    data = load_data(device)
    print(f"  Train: {data['n_train']}, Val: {data['n_val']}, Test: {data['n_test']}")

    # Save scalers
    joblib.dump(data["scaler_X"], os.path.join(out_dir, "scaler_X.joblib"))
    joblib.dump(data["scaler_Y"], os.path.join(out_dir, "scaler_Y.joblib"))

    # ── Hyperparameter configs ──
    # Use similar HPs to bnn-phy-mono (from Optuna best)
    configs = [
        {"name": "lowrank_r2_w128_d4", "width": 128, "depth": 4, "rank": 2,
         "lr": 3e-4, "kl_weight": 0.01, "prior_sigma": 0.5,
         "batch": 64, "epochs": 300, "patience": 40, "clip": 3.0},
        {"name": "lowrank_r2_w192_d3", "width": 192, "depth": 3, "rank": 2,
         "lr": 5e-4, "kl_weight": 0.005, "prior_sigma": 0.8,
         "batch": 64, "epochs": 300, "patience": 40, "clip": 3.0},
        {"name": "lowrank_r3_w128_d4", "width": 128, "depth": 4, "rank": 3,
         "lr": 3e-4, "kl_weight": 0.01, "prior_sigma": 0.5,
         "batch": 64, "epochs": 300, "patience": 40, "clip": 3.0},
        {"name": "diag_w128_d4_5out", "width": 128, "depth": 4, "rank": 0,
         "lr": 3e-4, "kl_weight": 0.01, "prior_sigma": 0.5,
         "batch": 64, "epochs": 300, "patience": 40, "clip": 3.0},
    ]

    all_results = {}

    for cfg in configs:
        use_lr = cfg["rank"] > 0
        tag = cfg["name"]
        print(f"\n{'='*60}")
        print(f"Training: {tag} (lowrank={use_lr}, rank={cfg['rank']})")
        print(f"{'='*60}")

        t0 = time.time()
        model, best_val = train_one_model(data, cfg, device, use_lowrank=use_lr)
        train_time = time.time() - t0
        print(f"  Training time: {train_time:.1f}s, best_val_nll: {best_val:.4f}")

        print("  Evaluating...")
        per_output, mean_metrics = evaluate(model, data, device,
                                            data["scaler_Y"],
                                            use_lowrank=use_lr, n_mc=50)

        result = {
            "config": cfg,
            "train_time_s": train_time,
            "best_val_nll": best_val,
            "per_output": per_output,
            "mean_metrics": mean_metrics,
        }
        all_results[tag] = result

        # Save per-config
        cfg_dir = os.path.join(out_dir, tag)
        os.makedirs(cfg_dir, exist_ok=True)
        torch.save(model.state_dict(), os.path.join(cfg_dir, "model.pt"))
        with open(os.path.join(cfg_dir, "metrics.json"), "w") as f:
            json.dump(result, f, indent=2, default=str)

        # Print summary
        print(f"\n  --- {tag} Results ---")
        for k, v in mean_metrics.items():
            print(f"    {k}: {v:.4f}")
        print(f"  Per-output:")
        for name, m in per_output.items():
            print(f"    {name}: R2={m['R2']:.4f} RMSE={m['RMSE']:.2f} "
                  f"CRPS={m['CRPS']:.3f} PICP90={m['PICP90']:.3f} MPIW90={m['MPIW90']:.2f}")

    # ── Save comparison table ──
    print(f"\n{'='*60}")
    print("COMPARISON SUMMARY")
    print(f"{'='*60}")

    rows = []
    for tag, r in all_results.items():
        m = r["mean_metrics"]
        rows.append({
            "model": tag,
            "MAE": m["MAE_mean"],
            "RMSE": m["RMSE_mean"],
            "R2": m["R2_mean"],
            "CRPS": m["CRPS_mean"],
            "NLL": m["test_NLL"],
            "PICP90": m["PICP_mean"],
            "MPIW90": m["MPIW_mean"],
            "energy_score": m["energy_score"],
            "train_time": r["train_time_s"],
        })

    df_compare = pd.DataFrame(rows)
    print(df_compare.to_string(index=False))
    df_compare.to_csv(os.path.join(out_dir, "comparison_summary.csv"), index=False)

    with open(os.path.join(out_dir, "all_results.json"), "w") as f:
        json.dump(all_results, f, indent=2, default=str)

    print(f"\nResults saved to {out_dir}")
    print("\nReference (bnn-phy-mono, 15-output): MAE=2.767, RMSE=3.582, CRPS=2.048")
    print("Note: above reference is 15-output mean; this experiment uses 5 primary outputs only.")
    print("For fair comparison, check per-output stress/keff/temp metrics against canonical values.")


if __name__ == "__main__":
    main()
