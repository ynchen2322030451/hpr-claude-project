#!/usr/bin/env python3
"""
run_conformal_0404.py — Split conformal calibration for BNN surrogates
======================================================================

Phase 3 of MODEL_UPGRADE_PLAN.md (appendix-level content).

Method:
  Split conformal prediction with normalized residuals.
  - The test set (501 samples) is split 50/50 into calibration and evaluation
    subsets (seed=42).
  - Nonconformity scores on calibration subset:
        s_i = |y_true_i - mu_i| / sigma_i
  - Conformal quantile q_hat at level (1 - alpha) with finite-sample correction:
        q_hat = ceil((n_cal + 1) * (1 - alpha)) / n_cal  quantile of {s_i}
  - Conformal interval on evaluation subset:
        [mu - q_hat * sigma, mu + q_hat * sigma]
  - Compare with raw BNN 90% interval using z = 1.645.

Outputs:
  - results_v3418/analysis/conformal_calibration.csv
  - printed summary table

Does NOT retrain any model.
"""

import json
import os
import sys
import numpy as np
import pandas as pd

# ── paths ──────────────────────────────────────────────────────
RESULTS_ROOT = "/Users/yinuo/Projects/hpr-claude-project/code/bnn0414/results/results_v3418"
OUT_DIR = os.path.join(RESULTS_ROOT, "analysis")

MODEL_IDS = ["bnn-baseline", "bnn-phy-mono", "bnn-baseline-homo", "bnn-mf-hybrid"]

# From experiment_config_0404.py
PRIMARY_OUTPUTS = [
    "iteration2_keff",
    "iteration2_max_fuel_temp",
    "iteration2_max_monolith_temp",
    "iteration2_max_global_stress",
    "iteration2_wall2",
]
STRESS_COL = "iteration2_max_global_stress"
STRESS_THRESHOLD = 131.0
NEAR_THRESHOLD_LO = 110.0
NEAR_THRESHOLD_HI = 150.0

ALPHA = 0.10          # target miscoverage
Z_RAW = 1.6449       # scipy.stats.norm.ppf(0.95)
SPLIT_SEED = 42


def load_predictions(model_id: str):
    """Load test_predictions_fixed.json for a model, return (mu, sigma, y_true, output_cols).

    Also runs a sanity check: for each output, verifies that mu and y_true
    have overlapping ranges. Returns a list of flagged output names if not.
    """
    path = os.path.join(RESULTS_ROOT, "models", model_id,
                        "fixed_eval", "test_predictions_fixed.json")
    with open(path, "r") as f:
        d = json.load(f)
    mu = np.array(d["mu"])          # (n_test, n_out)
    sigma = np.array(d["sigma"])    # (n_test, n_out)
    y_true = np.array(d["y_true"]) # (n_test, n_out)
    output_cols = d["output_cols"]

    # Sanity check: detect scrambled output columns.
    # A column is "scrambled" if the mu center is far outside the y_true range,
    # indicating the model's output ordering doesn't match the label.
    # We use: |median(mu) - median(y)| > 3 * IQR(y) as the criterion.
    flagged = []
    for i, col in enumerate(output_cols):
        med_mu = np.median(mu[:, i])
        med_y = np.median(y_true[:, i])
        iqr_y = np.percentile(y_true[:, i], 75) - np.percentile(y_true[:, i], 25)
        if iqr_y < 1e-30:
            continue  # near-constant output, skip check
        if abs(med_mu - med_y) > 3.0 * iqr_y:
            flagged.append(col)

    return mu, sigma, y_true, output_cols, flagged


def conformal_quantile(scores: np.ndarray, alpha: float) -> float:
    """Compute the conformal quantile with finite-sample correction.

    q_hat = the ceil((n+1)*(1-alpha))/n -th quantile of scores.
    Guarantees marginal coverage >= 1 - alpha.
    """
    n = len(scores)
    level = np.ceil((n + 1) * (1 - alpha)) / n
    level = min(level, 1.0)  # clip at 1.0
    return float(np.quantile(scores, level))


def compute_picp_mpiw(y_true, mu, half_width):
    """Compute PICP and MPIW given half-width of interval."""
    lower = mu - half_width
    upper = mu + half_width
    covered = (y_true >= lower) & (y_true <= upper)
    picp = np.mean(covered)
    mpiw = np.mean(2.0 * half_width)
    return picp, mpiw


def run_conformal_for_model(model_id: str):
    """Run split conformal for one model. Returns list of result dicts."""
    mu, sigma, y_true, output_cols, flagged = load_predictions(model_id)

    if flagged:
        print(f"  [WARNING] {model_id}: output columns with misaligned mu/y_true ranges: {flagged}")
        print(f"           This model likely has scrambled output ordering. Skipping.")
        return []
    n_test, n_out = mu.shape

    # 50/50 split of test set
    rng = np.random.default_rng(SPLIT_SEED)
    indices = np.arange(n_test)
    rng.shuffle(indices)
    n_cal = n_test // 2
    cal_idx = indices[:n_cal]
    eval_idx = indices[n_cal:]

    # Identify stress column index for near-threshold subsetting
    stress_oidx = output_cols.index(STRESS_COL)
    # Near-threshold mask on evaluation subset (based on TRUE stress values)
    stress_eval_true = y_true[eval_idx, stress_oidx]
    near_mask = (stress_eval_true >= NEAR_THRESHOLD_LO) & (stress_eval_true <= NEAR_THRESHOLD_HI)
    n_near = int(np.sum(near_mask))

    results = []

    for out_name in PRIMARY_OUTPUTS:
        oidx = output_cols.index(out_name)

        # Calibration scores (normalized residuals)
        mu_cal = mu[cal_idx, oidx]
        sigma_cal = sigma[cal_idx, oidx]
        y_cal = y_true[cal_idx, oidx]
        scores_cal = np.abs(y_cal - mu_cal) / (sigma_cal + 1e-30)

        # Conformal quantile
        q_hat = conformal_quantile(scores_cal, ALPHA)

        # Evaluation subset
        mu_eval = mu[eval_idx, oidx]
        sigma_eval = sigma[eval_idx, oidx]
        y_eval = y_true[eval_idx, oidx]

        # Raw BNN 90% interval: z = 1.645
        picp_raw, mpiw_raw = compute_picp_mpiw(y_eval, mu_eval, Z_RAW * sigma_eval)

        # Conformal-adjusted interval: q_hat * sigma
        picp_conf, mpiw_conf = compute_picp_mpiw(y_eval, mu_eval, q_hat * sigma_eval)

        row = {
            "model": model_id,
            "output": out_name,
            "subset": "all_eval",
            "n_cal": n_cal,
            "n_eval": len(eval_idx),
            "q_hat": round(q_hat, 4),
            "z_raw": Z_RAW,
            "picp_raw_90": round(picp_raw, 4),
            "mpiw_raw_90": round(mpiw_raw, 6),
            "picp_conf_90": round(picp_conf, 4),
            "mpiw_conf_90": round(mpiw_conf, 6),
            "coverage_gap_raw": round(picp_raw - 0.90, 4),
            "coverage_gap_conf": round(picp_conf - 0.90, 4),
        }
        results.append(row)

        # Near-threshold subset (stress-specific)
        if out_name == STRESS_COL and n_near > 0:
            mu_near = mu_eval[near_mask]
            sigma_near = sigma_eval[near_mask]
            y_near = y_eval[near_mask]

            picp_raw_near, mpiw_raw_near = compute_picp_mpiw(
                y_near, mu_near, Z_RAW * sigma_near)
            picp_conf_near, mpiw_conf_near = compute_picp_mpiw(
                y_near, mu_near, q_hat * sigma_near)

            row_near = {
                "model": model_id,
                "output": out_name,
                "subset": f"near_threshold_{int(NEAR_THRESHOLD_LO)}_{int(NEAR_THRESHOLD_HI)}",
                "n_cal": n_cal,
                "n_eval": n_near,
                "q_hat": round(q_hat, 4),
                "z_raw": Z_RAW,
                "picp_raw_90": round(picp_raw_near, 4),
                "mpiw_raw_90": round(mpiw_raw_near, 6),
                "picp_conf_90": round(picp_conf_near, 4),
                "mpiw_conf_90": round(mpiw_conf_near, 6),
                "coverage_gap_raw": round(picp_raw_near - 0.90, 4),
                "coverage_gap_conf": round(picp_conf_near - 0.90, 4),
            }
            results.append(row_near)

    return results


def main():
    all_results = []
    for mid in MODEL_IDS:
        pred_path = os.path.join(RESULTS_ROOT, "models", mid,
                                 "fixed_eval", "test_predictions_fixed.json")
        if not os.path.exists(pred_path):
            print(f"[SKIP] {mid}: no test_predictions_fixed.json")
            continue
        print(f"[INFO] Processing {mid} ...")
        rows = run_conformal_for_model(mid)
        all_results.extend(rows)
        print(f"       {len(rows)} rows")

    if not all_results:
        print("[ERROR] No results produced.")
        sys.exit(1)

    df = pd.DataFrame(all_results)

    # Save
    os.makedirs(OUT_DIR, exist_ok=True)
    out_path = os.path.join(OUT_DIR, "conformal_calibration.csv")
    df.to_csv(out_path, index=False)
    print(f"\n[SAVED] {out_path}")

    # ── Summary table ─────────────────────────────────────────
    print("\n" + "=" * 100)
    print("CONFORMAL CALIBRATION SUMMARY (90% target coverage)")
    print("=" * 100)

    # All-eval rows only for main table
    df_all = df[df["subset"] == "all_eval"].copy()
    df_all["output_short"] = df_all["output"].str.replace("iteration2_", "")

    pivot_cols = ["model", "output_short", "q_hat",
                  "picp_raw_90", "picp_conf_90",
                  "mpiw_raw_90", "mpiw_conf_90",
                  "coverage_gap_raw", "coverage_gap_conf"]
    print("\n--- All evaluation samples ---")
    print(df_all[pivot_cols].to_string(index=False))

    # Near-threshold stress rows
    df_near = df[df["subset"].str.startswith("near_threshold")].copy()
    if len(df_near) > 0:
        print(f"\n--- Near-threshold stress ({NEAR_THRESHOLD_LO}-{NEAR_THRESHOLD_HI} MPa) ---")
        near_cols = ["model", "n_eval", "q_hat",
                     "picp_raw_90", "picp_conf_90",
                     "mpiw_raw_90", "mpiw_conf_90",
                     "coverage_gap_raw", "coverage_gap_conf"]
        print(df_near[near_cols].to_string(index=False))

    # Key observations
    print("\n--- Key observations ---")
    for mid in df_all["model"].unique():
        sub = df_all[df_all["model"] == mid]
        avg_gap_raw = sub["coverage_gap_raw"].mean()
        avg_gap_conf = sub["coverage_gap_conf"].mean()
        q_stress = sub.loc[sub["output"].str.contains("stress"), "q_hat"].values
        q_str = f", stress q_hat={q_stress[0]:.3f}" if len(q_stress) > 0 else ""
        print(f"  {mid}: raw avg gap={avg_gap_raw:+.4f}, conformal avg gap={avg_gap_conf:+.4f}{q_str}")

    print()


if __name__ == "__main__":
    main()
