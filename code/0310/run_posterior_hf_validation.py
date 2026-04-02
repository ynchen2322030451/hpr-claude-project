# run_posterior_hf_validation.py
# ============================================================
# Posterior-informed parameter validation against high-fidelity data.
#
# SCIENTIFIC PURPOSE (Li Dong analogy):
#   High-fidelity case (the "experiment") → MCMC calibrates 4 BNN
#   input parameters → posterior mean → find closest HF case in full
#   dataset → compare that case's TRUE HF outputs against:
#     (a) prior mean prediction (baseline)
#     (b) posterior mean prediction (via surrogate)
#     (c) nearest HF neighbor true outputs (ground-truth reference)
#
# Model:  8 inputs → 15 outputs (HeteroMLP).
# MCMC calibrates 4 params: E_intercept, alpha_base, alpha_slope, nu.
# Remaining 4 (E_slope, SS316_T_ref, SS316_k_ref, SS316_alpha) are
# fixed at their training-set mean.
#
# Outputs (all written to OUT_DIR):
#   paper_posterior_hf_validation_summary.csv
#   paper_posterior_hf_validation_per_output.csv
#   paper_posterior_hf_validation_meta.json
# ============================================================

import os
import json
import pickle
import numpy as np
import pandas as pd
import torch

from paper_experiment_config import (
    CSV_PATH,
    OUT_DIR,
    INPUT_COLS,
    OUTPUT_COLS,
    PRIMARY_OUTPUTS,
    PRIMARY_STRESS_OUTPUT,
    PRIMARY_AUXILIARY_OUTPUT,
    FIXED_CKPT_PATH,
    FIXED_SCALER_PATH,
    FIXED_SPLIT_DIR,
    SEED,
)
from run_phys_levels_main import (
    load_dataset,
    get_device,
    _to_numpy,
)

# ============================================================
# Settings
# ============================================================

RUN_TAG = "reduced_maintext"
CALIBRATION_INPUT_COLS = ["E_intercept", "alpha_base", "alpha_slope", "nu"]
FIXED_INPUT_COLS = [c for c in INPUT_COLS if c not in CALIBRATION_INPUT_COLS]

N_NEIGHBORS = 3      # number of nearest HF neighbors to report
N_CASES     = 20     # must match the calibration benchmark N_CASES

BENCHMARK_DIR = os.path.join(OUT_DIR, "benchmark_case")


# ============================================================
# Load frozen surrogate  (uses config paths → always consistent)
# ============================================================

def load_surrogate(device):
    from run_phys_levels_main import HeteroMLP

    if not os.path.exists(FIXED_CKPT_PATH):
        raise FileNotFoundError(
            f"Checkpoint not found: {FIXED_CKPT_PATH}\n"
            "Run run_train_fixed_surrogates.py first."
        )
    ckpt = torch.load(FIXED_CKPT_PATH, map_location=device)
    bp = ckpt["best_params"]
    model = HeteroMLP(
        in_dim=len(INPUT_COLS),
        out_dim=len(OUTPUT_COLS),
        width=int(bp["width"]),
        depth=int(bp["depth"]),
        dropout=float(bp["dropout"]),
    ).to(device)
    model.load_state_dict(ckpt["model_state_dict"])
    model.eval()

    if not os.path.exists(FIXED_SCALER_PATH):
        raise FileNotFoundError(f"Scalers not found: {FIXED_SCALER_PATH}")
    with open(FIXED_SCALER_PATH, "rb") as f:
        scalers = pickle.load(f)
    return model, scalers["sx"], scalers["sy"]


# ============================================================
# Surrogate forward pass
# ============================================================

def surrogate_predict(x_raw, model, sx, sy, device):
    """x_raw: (N, 8) numpy → returns mu (N, 15), sigma (N, 15)"""
    x_s = sx.transform(x_raw)
    x_t = torch.tensor(x_s, dtype=torch.float32, device=device)
    with torch.no_grad():
        mu_s, logvar_s = model(x_t)
        var_s = torch.exp(logvar_s)
    mu    = sy.inverse_transform(_to_numpy(mu_s))
    sigma = np.sqrt(_to_numpy(var_s)) * sy.scale_
    return mu, sigma


# ============================================================
# Build reference parameter vectors
# ============================================================

def build_prior_mean_vector(sx):
    """Prior mean = training-set mean for all 8 inputs."""
    return sx.mean_.copy()


def build_posterior_mean_vector(case_i, prior_mean_full):
    """
    Load posterior samples for case_i, compute posterior mean for the
    4 calibrated params; fill remaining 4 at training-set mean.
    Returns None if the posterior file is missing.
    """
    post_file = os.path.join(
        BENCHMARK_DIR,
        f"benchmark_case{case_i:03d}_posterior_samples_{RUN_TAG}.csv"
    )
    if not os.path.exists(post_file):
        return None
    post_df = pd.read_csv(post_file)

    theta = prior_mean_full.copy()
    for col in CALIBRATION_INPUT_COLS:
        if col in post_df.columns:
            theta[INPUT_COLS.index(col)] = float(post_df[col].mean())
    return theta


# ============================================================
# Nearest HF neighbor search
# ============================================================

def find_nearest_hf_neighbors(theta_full, X_full, sx, k=3, exclude_indices=None):
    """
    Find k nearest rows in X_full (N×8) to theta_full (8,) in
    standardised input space. Returns (indices, distances).
    """
    X_s = sx.transform(X_full)
    q_s = sx.transform(theta_full.reshape(1, -1))[0]
    dists = np.linalg.norm(X_s - q_s, axis=1)
    if exclude_indices is not None:
        dists[list(exclude_indices)] = np.inf
    order = np.argsort(dists)
    return order[:k], dists[order[:k]]


# ============================================================
# Load case ground truth
# ============================================================

def load_case_true_x_y(case_i, df_full, idx_test):
    """Return true input (8,) and output (15,) for test case case_i."""
    row_idx = idx_test[case_i] if case_i < len(idx_test) else case_i
    row = df_full.iloc[row_idx]
    x_true = row[INPUT_COLS].to_numpy(dtype=float)
    y_true = row[OUTPUT_COLS].to_numpy(dtype=float)
    return x_true, y_true, int(row_idx)


# ============================================================
# Prediction error
# ============================================================

def prediction_error(y_pred, y_true):
    abs_err = np.abs(y_pred - y_true)
    rel_err = abs_err / (np.abs(y_true) + 1e-30)
    return abs_err, rel_err


# ============================================================
# Main
# ============================================================

def main():
    np.random.seed(SEED)
    device = get_device()

    # --- Load dataset ---
    df_full = load_dataset()
    X_full  = df_full[INPUT_COLS].to_numpy(dtype=float)
    Y_full  = df_full[OUTPUT_COLS].to_numpy(dtype=float)

    # --- Load frozen split ---
    idx_test = pd.read_csv(
        os.path.join(FIXED_SPLIT_DIR, "test_indices.csv")
    )["index"].to_numpy(dtype=int)
    idx_train = pd.read_csv(
        os.path.join(FIXED_SPLIT_DIR, "train_indices.csv")
    )["index"].to_numpy(dtype=int)

    # --- Load surrogate ---
    model, sx, sy = load_surrogate(device)
    prior_mean_full = sx.mean_.copy()

    print(f"[INFO] Dataset: n={len(df_full)}, test={len(idx_test)}, "
          f"train={len(idx_train)}")
    print(f"[INFO] Calibration params : {CALIBRATION_INPUT_COLS}")
    print(f"[INFO] Fixed params (mean): {FIXED_INPUT_COLS}")
    print(f"[INFO] Processing {N_CASES} cases  (RUN_TAG={RUN_TAG})\n")

    # --- Output indices ---
    stress_idx = OUTPUT_COLS.index(PRIMARY_STRESS_OUTPUT)
    keff_idx   = OUTPUT_COLS.index(PRIMARY_AUXILIARY_OUTPUT)
    pri_idx    = [OUTPUT_COLS.index(c) for c in PRIMARY_OUTPUTS]

    # --- Prior mean prediction (same for every case) ---
    mu_prior, sigma_prior = surrogate_predict(
        prior_mean_full.reshape(1, -1), model, sx, sy, device
    )
    mu_prior, sigma_prior = mu_prior[0], sigma_prior[0]

    summary_rows    = []
    per_output_rows = []
    n_skipped = 0

    for case_i in range(N_CASES):
        # 1) Ground-truth HF outputs
        x_true, y_true, global_idx = load_case_true_x_y(case_i, df_full, idx_test)
        true_stress = float(y_true[stress_idx])
        true_keff   = float(y_true[keff_idx])

        # 2) Posterior mean prediction
        theta_post = build_posterior_mean_vector(case_i, prior_mean_full)
        if theta_post is None:
            print(f"  [SKIP] Case {case_i:02d}: no posterior file found.")
            n_skipped += 1
            continue

        mu_post, sigma_post = surrogate_predict(
            theta_post.reshape(1, -1), model, sx, sy, device
        )
        mu_post, sigma_post = mu_post[0], sigma_post[0]

        # 3) Nearest HF neighbors to posterior mean
        #    (exclude the test case itself to avoid trivial match)
        nbr_indices, nbr_dists = find_nearest_hf_neighbors(
            theta_post, X_full, sx, k=N_NEIGHBORS,
            exclude_indices={global_idx}
        )
        nbr_y = Y_full[nbr_indices[0]]
        nbr_x = X_full[nbr_indices[0]]

        # 4) Prediction errors for all three predictors
        err_prior_abs, _ = prediction_error(mu_prior, y_true)
        err_post_abs,  _ = prediction_error(mu_post,  y_true)
        err_nbr_abs,   _ = prediction_error(nbr_y,    y_true)

        pri_mae_prior = float(np.mean([err_prior_abs[i] for i in pri_idx]))
        pri_mae_post  = float(np.mean([err_post_abs[i]  for i in pri_idx]))
        pri_mae_nbr   = float(np.mean([err_nbr_abs[i]   for i in pri_idx]))
        improvement   = pri_mae_prior - pri_mae_post   # positive = better

        # 5) Summary row
        summary_rows.append({
            "case_i":            case_i,
            "global_idx":        global_idx,
            "true_stress_MPa":   true_stress,
            "true_keff":         true_keff,

            # Posterior mean parameters (4 calibrated)
            **{f"post_mean_{c}": float(theta_post[INPUT_COLS.index(c)])
               for c in CALIBRATION_INPUT_COLS},

            # MAE comparison
            "pri_mae_prior":     pri_mae_prior,
            "pri_mae_post":      pri_mae_post,
            "pri_mae_nbr":       pri_mae_nbr,
            "pri_improvement":   improvement,

            # Stress-specific
            "stress_err_prior":  float(err_prior_abs[stress_idx]),
            "stress_err_post":   float(err_post_abs[stress_idx]),
            "stress_err_nbr":    float(err_nbr_abs[stress_idx]),
            "stress_pred_prior": float(mu_prior[stress_idx]),
            "stress_pred_post":  float(mu_post[stress_idx]),
            "stress_nbr_true":   float(nbr_y[stress_idx]),

            # Nearest-neighbor info
            "nbr_global_idx":    int(nbr_indices[0]),
            "nbr_dist_scaled":   float(nbr_dists[0]),
        })

        # 6) Per-output rows (primary outputs only)
        for c in PRIMARY_OUTPUTS:
            j = OUTPUT_COLS.index(c)
            per_output_rows.append({
                "case_i":      case_i,
                "output":      c,
                "true_val":    float(y_true[j]),
                "pred_prior":  float(mu_prior[j]),
                "pred_post":   float(mu_post[j]),
                "pred_nbr":    float(nbr_y[j]),
                "err_prior":   float(err_prior_abs[j]),
                "err_post":    float(err_post_abs[j]),
                "err_nbr":     float(err_nbr_abs[j]),
                "sigma_prior": float(sigma_prior[j]),
                "sigma_post":  float(sigma_post[j]),
            })

        print(f"  Case {case_i:02d}: stress={true_stress:.1f} MPa  "
              f"mae_prior={pri_mae_prior:.3f}  mae_post={pri_mae_post:.3f}  "
              f"nbr_dist={nbr_dists[0]:.3f}  improved={improvement > 0}")

    # ---- Save outputs ----
    if not summary_rows:
        print("\n[WARNING] No cases processed. Check BENCHMARK_DIR and RUN_TAG.")
        return

    df_summary = pd.DataFrame(summary_rows)
    df_per_out = pd.DataFrame(per_output_rows)

    df_summary.to_csv(
        os.path.join(OUT_DIR, "paper_posterior_hf_validation_summary.csv"),
        index=False, encoding="utf-8-sig"
    )
    df_per_out.to_csv(
        os.path.join(OUT_DIR, "paper_posterior_hf_validation_per_output.csv"),
        index=False, encoding="utf-8-sig"
    )

    # ---- Aggregate statistics ----
    n_improved = int((df_summary["pri_improvement"] > 0).sum())
    meta = {
        "run_tag":             RUN_TAG,
        "n_cases_attempted":   N_CASES,
        "n_cases_processed":   len(df_summary),
        "n_cases_skipped":     n_skipped,
        "calibration_params":  CALIBRATION_INPUT_COLS,
        "fixed_params":        FIXED_INPUT_COLS,
        "n_improved":          n_improved,
        "pct_improved":        float(n_improved / len(df_summary) * 100),
        "mean_pri_mae_prior":  float(df_summary["pri_mae_prior"].mean()),
        "mean_pri_mae_post":   float(df_summary["pri_mae_post"].mean()),
        "mean_pri_mae_nbr":    float(df_summary["pri_mae_nbr"].mean()),
        "mean_improvement":    float(df_summary["pri_improvement"].mean()),
        "mean_stress_err_prior": float(df_summary["stress_err_prior"].mean()),
        "mean_stress_err_post":  float(df_summary["stress_err_post"].mean()),
        "mean_nbr_dist":       float(df_summary["nbr_dist_scaled"].mean()),
    }
    with open(
        os.path.join(OUT_DIR, "paper_posterior_hf_validation_meta.json"),
        "w", encoding="utf-8"
    ) as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)

    # ---- Print summary ----
    print(f"\n{'='*58}")
    print(f"  POSTERIOR HF VALIDATION COMPLETE")
    print(f"  Cases processed : {len(df_summary)} / {N_CASES}")
    print(f"  Cases improved  : {n_improved}/{len(df_summary)} "
          f"({meta['pct_improved']:.0f}%)")
    print(f"  Mean primary MAE: prior={meta['mean_pri_mae_prior']:.3f}  "
          f"→  post={meta['mean_pri_mae_post']:.3f}")
    print(f"  Mean stress MAE : prior={meta['mean_stress_err_prior']:.2f}  "
          f"→  post={meta['mean_stress_err_post']:.2f} MPa")
    print(f"  Mean nbr dist   : {meta['mean_nbr_dist']:.3f} (std-space)")
    print(f"{'='*58}")
    print(f"Saved to: {OUT_DIR}/paper_posterior_hf_validation_*.csv/json")


if __name__ == "__main__":
    main()
