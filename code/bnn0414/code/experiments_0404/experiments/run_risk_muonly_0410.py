#!/usr/bin/env python3
"""
run_risk_muonly_0410.py
============================================================
BNN 0414 -- mu-only and predictive forward UQ for bnn-data-mono-ineq.

为 bnn-data-mono-ineq 生成两套 forward UQ 风险结果：

  1. mu-only (mean_only) -> canonical evidence
     阈值: [110, 120, 131] MPa
     sigma_k:  [0.5, 1.0, 1.5, 2.0]

  2. predictive draw (含 aleatoric) -> supplementary
     阈值: [110, 120, 131, 169, 200] MPa
     sigma_k:  [0.5, 1.0, 1.5, 2.0]

同时计算 iter1 输出的 mu-only forward UQ
(用于 iter1->iter2 coupling narrative)

BNN 改动：
  - _predict 返回 (mu_mean, sigma_total)，MC-averaged
  - mu-only 模式直接用 mu_mean
  - predictive draw: y_draw = mu_mean + sigma_total * eps

输出目录：
  experiments_0404/experiments/risk_propagation_0410/bnn-data-mono-ineq/
    D1_muonly.json / .csv
    D1_predictive_extended.json / .csv
============================================================
"""

import os, sys, json, logging
from datetime import datetime

import numpy as np
import pandas as pd
import torch

# -- path setup (same pattern as other bnn0414 experiment scripts) --
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_EXPR_DIR = os.path.dirname(_SCRIPT_DIR)
_BNN_CODE = os.path.dirname(_EXPR_DIR)
_BNN_ROOT = os.path.dirname(_BNN_CODE)
_CODE_TOP = os.path.dirname(_BNN_ROOT)
for _p in (_SCRIPT_DIR,
           os.path.join(_EXPR_DIR, 'config'),
           _EXPR_DIR,
           _BNN_CODE,
           os.path.join(_CODE_TOP, '0310'),
           os.environ.get('HPR_LEGACY_DIR', '')):
    if _p and os.path.isdir(_p) and _p not in sys.path:
        sys.path.insert(0, _p)

from experiment_config_0404 import (
    INPUT_COLS, OUTPUT_COLS,
    PRIMARY_STRESS_OUTPUT, PRIMARY_STRESS_THRESHOLD,
    DESIGN_NOMINAL, DESIGN_SIGMA,
    RISK_PROP_N_SAMPLES, RISK_PROP_SIGMA_K,
    SEED, DEVICE, FIXED_SPLIT_DIR,
)
from model_registry_0404 import MODELS
from run_eval_0404 import _resolve_artifacts, _load_model, _load_scalers, _predict

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

STRESS_IDX = OUTPUT_COLS.index(PRIMARY_STRESS_OUTPUT)
KEFF_IDX   = OUTPUT_COLS.index("iteration2_keff")

# iter1 stress index
ITER1_STRESS_IDX = OUTPUT_COLS.index("iteration1_max_global_stress")
ITER1_KEFF_IDX   = None  # iter1 has no keff


def run_D1(model_id, model, sx, sy, device,
           sigma_k_list, threshold_list, draw_predictive, tag):
    """Generic D1 runner."""
    logger.info(f"[D1-{tag}][{model_id}] N={RISK_PROP_N_SAMPLES}, "
                f"draw_pred={draw_predictive}, thresholds={threshold_list}")

    nominal = np.array([DESIGN_NOMINAL[c] for c in INPUT_COLS])
    sigma_1 = np.array([DESIGN_SIGMA[c]   for c in INPUT_COLS])
    rng = np.random.default_rng(SEED)

    rows = []
    for k in sigma_k_list:
        sigma_k = k * sigma_1
        X_samp = rng.normal(loc=nominal, scale=sigma_k,
                            size=(RISK_PROP_N_SAMPLES, len(INPUT_COLS)))

        mu, sigma_pred = _predict(model, X_samp, sx, sy, device)

        if draw_predictive:
            eps = rng.standard_normal(size=mu.shape)
            y_draw = mu + sigma_pred * eps
        else:
            y_draw = mu

        stress_draw = y_draw[:, STRESS_IDX]
        keff_draw   = y_draw[:, KEFF_IDX]

        # iter1 stress from same samples (mu-only always for iter1)
        iter1_stress = mu[:, ITER1_STRESS_IDX]

        for tau in threshold_list:
            p_exceed = float(np.mean(stress_draw > tau))
            row = {
                "sigma_k":                k,
                "threshold_MPa":          tau,
                "P_exceed":               p_exceed,
                "stress_mean":            float(np.mean(stress_draw)),
                "stress_std":             float(np.std(stress_draw)),
                "stress_p5":              float(np.percentile(stress_draw, 5)),
                "stress_p50":             float(np.percentile(stress_draw, 50)),
                "stress_p95":             float(np.percentile(stress_draw, 95)),
                "stress_pred_mu_mean":    float(np.mean(mu[:, STRESS_IDX])),
                "stress_pred_sigma_mean": float(np.mean(sigma_pred[:, STRESS_IDX])),
                "keff_mean":              float(np.mean(keff_draw)),
                "keff_std":               float(np.std(keff_draw)),
                "iter1_stress_mean":      float(np.mean(iter1_stress)),
                "iter1_stress_std":       float(np.std(iter1_stress)),
                "sample_source":          "predictive" if draw_predictive else "mean_only",
            }
            rows.append(row)
            logger.info(
                f"  k={k:.1f}sigma, tau={tau} MPa -> P(exceed)={p_exceed:.4f} "
                f"(stress mu={row['stress_mean']:.1f} sigma={row['stress_std']:.1f} MPa)"
            )

    meta = {
        "experiment":   f"D1_{tag}",
        "model_id":     model_id,
        "N_samples":    RISK_PROP_N_SAMPLES,
        "sigma_k_list": sigma_k_list,
        "threshold_sweep_MPa": threshold_list,
        "draw_predictive": draw_predictive,
        "tag":           tag,
        "design_nominal": DESIGN_NOMINAL,
        "design_sigma_1sigma": DESIGN_SIGMA,
        "rows": rows,
    }
    return meta, pd.DataFrame(rows)


if __name__ == "__main__":
    model_id = "bnn-data-mono-ineq"

    # output dir
    out_base = os.path.join(
        _EXPR_DIR, "experiments", "risk_propagation_0410", model_id
    )
    out_base = os.path.normpath(out_base)
    os.makedirs(out_base, exist_ok=True)

    # load model
    ckpt_path, scaler_path = _resolve_artifacts(model_id)
    device = torch.device(DEVICE if torch.cuda.is_available() else "cpu")
    model   = _load_model(ckpt_path, device)
    scalers = _load_scalers(scaler_path)
    sx, sy  = scalers["sx"], scalers["sy"]

    sigma_k_list = RISK_PROP_SIGMA_K  # [0.5, 1.0, 1.5, 2.0]
    thresholds_main  = [110.0, 120.0, 131.0]
    thresholds_ext   = [110.0, 120.0, 131.0, 169.0, 200.0]

    # -- 1. mu-only --
    meta_mu, df_mu = run_D1(model_id, model, sx, sy, device,
                            sigma_k_list, thresholds_ext,
                            draw_predictive=False, tag="muonly")
    df_mu.to_csv(os.path.join(out_base, "D1_muonly.csv"), index=False)
    with open(os.path.join(out_base, "D1_muonly.json"), "w") as f:
        json.dump(meta_mu, f, indent=2)
    logger.info(f"[mu-only] -> {out_base}/D1_muonly.json")

    # -- 2. predictive draw + extended thresholds --
    meta_pred, df_pred = run_D1(model_id, model, sx, sy, device,
                                sigma_k_list, thresholds_ext,
                                draw_predictive=True, tag="predictive_extended")
    df_pred.to_csv(os.path.join(out_base, "D1_predictive_extended.csv"), index=False)
    with open(os.path.join(out_base, "D1_predictive_extended.json"), "w") as f:
        json.dump(meta_pred, f, indent=2)
    logger.info(f"[predictive-ext] -> {out_base}/D1_predictive_extended.json")

    # -- 3. Summary --
    print("\n" + "="*72)
    print(f"SUMMARY -- {model_id} forward UQ")
    print("="*72)
    print("\n[mu-only, sigma_k=1.0, canonical]")
    for _, r in df_mu[df_mu.sigma_k == 1.0].iterrows():
        print(f"  tau={r.threshold_MPa:.0f} MPa  P_exceed={r.P_exceed:.4f}  "
              f"stress mu={r.stress_mean:.1f}+/-{r.stress_std:.1f}  "
              f"keff mu={r.keff_mean:.6f}+/-{r.keff_std:.6f}")
        print(f"    iter1_stress mu={r.iter1_stress_mean:.1f}+/-{r.iter1_stress_std:.1f}")

    print("\n[predictive draw, sigma_k=1.0, supplementary]")
    for _, r in df_pred[df_pred.sigma_k == 1.0].iterrows():
        print(f"  tau={r.threshold_MPa:.0f} MPa  P_exceed={r.P_exceed:.4f}  "
              f"stress mu={r.stress_mean:.1f}+/-{r.stress_std:.1f}")
