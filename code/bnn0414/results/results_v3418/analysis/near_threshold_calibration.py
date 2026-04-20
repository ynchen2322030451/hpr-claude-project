"""
Near-threshold calibration analysis for heteroscedastic ablation (Phase 1.3).

Compares bnn-baseline (heteroscedastic) vs bnn-baseline-homo (homoscedastic)
and includes bnn-phy-mono and bnn-mf-hybrid for completeness.

Output: iteration2_max_global_stress (index 11)
Stress bins: low (<110), near-threshold (110-150), high (>150) MPa
Metrics: PICP@90%, MPIW, CRPS, calibration efficiency (PICP/MPIW)
"""

import json
import os
import numpy as np
import pandas as pd
from scipy import stats as sp_stats

# ── paths ──
RESULTS_ROOT = "/Users/yinuo/Projects/hpr-claude-project/code/bnn0414/results/results_v3418"
MODELS_DIR = os.path.join(RESULTS_ROOT, "models")
OUT_DIR = os.path.join(RESULTS_ROOT, "analysis")
os.makedirs(OUT_DIR, exist_ok=True)

MODEL_IDS = ["bnn-baseline", "bnn-baseline-homo", "bnn-phy-mono", "bnn-mf-hybrid"]
STRESS_IDX = 11  # iteration2_max_global_stress in OUTPUT_COLS
ALPHA = 0.10     # 90% prediction interval
Z90 = sp_stats.norm.ppf(1 - ALPHA / 2)  # ~1.6449

# ── bin definitions ──
BINS = {
    "low (<110 MPa)":        (None, 110.0),
    "near-threshold (110-150 MPa)": (110.0, 150.0),
    "high (>150 MPa)":       (150.0, None),
    "all":                   (None, None),
}


def load_predictions(model_id):
    """Load test_predictions_fixed.json and extract stress column."""
    path = os.path.join(MODELS_DIR, model_id, "fixed_eval", "test_predictions_fixed.json")
    with open(path) as f:
        d = json.load(f)

    y_true = np.array(d["y_true"])[:, STRESS_IDX]
    mu = np.array(d["mu"])[:, STRESS_IDX]
    sigma = np.array(d["sigma"])[:, STRESS_IDX]
    epi_var = np.array(d["epistemic_var"])[:, STRESS_IDX]
    ale_var = np.array(d["aleatoric_var"])[:, STRESS_IDX]

    return {
        "y_true": y_true,
        "mu": mu,
        "sigma": sigma,       # total std
        "epi_std": np.sqrt(epi_var),
        "ale_std": np.sqrt(ale_var),
        "n": len(y_true),
    }


def crps_gaussian(y_true, mu, sigma):
    """CRPS for Gaussian predictive distribution (closed form)."""
    z = (y_true - mu) / sigma
    phi = sp_stats.norm.cdf(z)
    pdf = sp_stats.norm.pdf(z)
    return np.mean(sigma * (z * (2 * phi - 1) + 2 * pdf - 1 / np.sqrt(np.pi)))


def compute_metrics(pred, lo, hi):
    """Compute calibration metrics for a stress bin."""
    y = pred["y_true"]
    mu = pred["mu"]
    sigma = pred["sigma"]

    # bin mask
    mask = np.ones(len(y), dtype=bool)
    if lo is not None:
        mask &= y >= lo
    if hi is not None:
        mask &= y < hi

    n = mask.sum()
    if n == 0:
        return {"n": 0, "PICP_90": np.nan, "MPIW": np.nan, "CRPS": np.nan, "eff": np.nan}

    y_b = y[mask]
    mu_b = mu[mask]
    sig_b = sigma[mask]

    # 90% PI
    lower = mu_b - Z90 * sig_b
    upper = mu_b + Z90 * sig_b
    widths = upper - lower
    covered = ((y_b >= lower) & (y_b <= upper)).astype(float)

    picp = covered.mean()
    mpiw = widths.mean()
    crps = crps_gaussian(y_b, mu_b, sig_b)
    eff = picp / mpiw if mpiw > 0 else np.nan

    return {
        "n": int(n),
        "PICP_90": round(picp, 4),
        "MPIW": round(mpiw, 2),
        "CRPS": round(crps, 3),
        "eff": round(eff, 5),
    }


def main():
    rows = []
    for mid in MODEL_IDS:
        pred = load_predictions(mid)
        for bname, (lo, hi) in BINS.items():
            m = compute_metrics(pred, lo, hi)
            m["model"] = mid
            m["bin"] = bname
            # also record mean aleatoric / epistemic std in this bin
            mask = np.ones(len(pred["y_true"]), dtype=bool)
            if lo is not None:
                mask &= pred["y_true"] >= lo
            if hi is not None:
                mask &= pred["y_true"] < hi
            if mask.sum() > 0:
                m["mean_ale_std"] = round(pred["ale_std"][mask].mean(), 3)
                m["mean_epi_std"] = round(pred["epi_std"][mask].mean(), 3)
            else:
                m["mean_ale_std"] = np.nan
                m["mean_epi_std"] = np.nan
            rows.append(m)

    df = pd.DataFrame(rows)
    col_order = ["model", "bin", "n", "PICP_90", "MPIW", "CRPS", "eff",
                 "mean_ale_std", "mean_epi_std"]
    df = df[col_order]

    csv_path = os.path.join(OUT_DIR, "near_threshold_calibration.csv")
    df.to_csv(csv_path, index=False)
    print(f"Saved: {csv_path}\n")

    # ── pretty print ──
    print("=" * 110)
    print("Near-threshold calibration analysis — iteration2_max_global_stress")
    print("Stress threshold: 131 MPa | 90% PI | Bins: low<110, near=110-150, high>150")
    print("=" * 110)

    for mid in MODEL_IDS:
        sub = df[df["model"] == mid]
        print(f"\n{'─'*50}")
        print(f"  {mid}")
        print(f"{'─'*50}")
        print(f"  {'bin':<32s} {'n':>4s}  {'PICP':>6s}  {'MPIW':>8s}  {'CRPS':>7s}  {'eff':>8s}  {'ale_std':>8s}  {'epi_std':>8s}")
        for _, r in sub.iterrows():
            print(f"  {r['bin']:<32s} {r['n']:4d}  {r['PICP_90']:6.4f}  {r['MPIW']:8.2f}  "
                  f"{r['CRPS']:7.3f}  {r['eff']:8.5f}  {r['mean_ale_std']:8.3f}  {r['mean_epi_std']:8.3f}")

    # ── headline comparison ──
    print("\n" + "=" * 110)
    print("HEADLINE: heteroscedastic vs homoscedastic (near-threshold bin)")
    print("=" * 110)
    for mid in ["bnn-baseline", "bnn-baseline-homo"]:
        r = df[(df["model"] == mid) & (df["bin"] == "near-threshold (110-150 MPa)")].iloc[0]
        print(f"  {mid:<22s}  PICP={r['PICP_90']:.4f}  MPIW={r['MPIW']:.2f}  CRPS={r['CRPS']:.3f}  "
              f"eff={r['eff']:.5f}  ale_std={r['mean_ale_std']:.3f}  epi_std={r['mean_epi_std']:.3f}")


if __name__ == "__main__":
    main()
