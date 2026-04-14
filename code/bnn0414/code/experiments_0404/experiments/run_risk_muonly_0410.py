#!/usr/bin/env python3
"""
run_risk_muonly_0410.py  (BNN 0414)
============================================================
为 bnn-data-mono-ineq 生成两套 forward UQ 风险结果：

  1. mu-only (mean_only) → 主文 canonical evidence
     使用 BNN 的 mean-weights forward (sample=False) —— 等价于
     用后验均值权重做一次确定性预测，不做 MC 采样，不加 aleatoric。
     阈值: [110, 120, 131] MPa（扩展版 ext）
     σ_k:  [0.5, 1.0, 1.5, 2.0]

  2. predictive draw（含 epistemic + aleatoric）→ 附录 supplementary
     使用 mc_predict 得到 total_var，再按 N(mu, sqrt(total_var)) 采样。
     阈值: [110, 120, 131, 169, 200] MPa
     σ_k:  [0.5, 1.0, 1.5, 2.0]

同时计算 iter1 输出的 mu-only forward UQ（两套结果都记录 iter1_stress）。

# TODO(bnn): "mu-only" 在 BNN 语境下是一种简化 —— 它丢弃了 epistemic
#            不确定度（MC 分散），只保留后验均值权重的确定性预测。
#            这与 0411 中 HeteroMLP 的 mu（唯一确定性输出）不完全等价，
#            但在 "展示 canonical central tendency" 的目的下是合理的。

输出目录：
  experiments_0404/experiments/risk_propagation_0410/bnn-data-mono-ineq/
    D1_muonly.json / .csv        ← 主文
    D1_predictive_extended.json  ← 附录
============================================================
"""

import os, sys, json, logging
from datetime import datetime

import numpy as np
import pandas as pd
import torch

# ── path setup (inline, same pattern as run_risk_propagation_0404.py) ──
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_CODE_ROOT = _SCRIPT_DIR
while _CODE_ROOT and not os.path.basename(_CODE_ROOT) == 'code':
    _CODE_ROOT = os.path.dirname(_CODE_ROOT)
_BNN_CODE_DIR = _CODE_ROOT
_BNN_CONFIG_DIR = os.path.join(_CODE_ROOT, 'experiments_0404', 'config')
_BNN_EVAL_DIR   = os.path.join(_CODE_ROOT, 'experiments_0404', 'evaluation')
_CODE_TOP = os.path.dirname(os.path.dirname(_CODE_ROOT))
_ROOT_0310 = os.path.join(_CODE_TOP, '0310')
for _p in (_SCRIPT_DIR, _BNN_CODE_DIR, _BNN_CONFIG_DIR, _BNN_EVAL_DIR,
           os.path.join(_CODE_ROOT, 'experiments_0404'),
           _ROOT_0310,
           os.environ.get('HPR_LEGACY_DIR', '')):
    if _p and os.path.isdir(_p) and _p not in sys.path:
        # [BNN0414 FIX] bnn0414 paths go to front (high prio); legacy to back.
        # Without this, HPR_LEGACY_DIR / code/0310 lands at sys.path[0] and
        # shadows bnn0414/experiment_config_0404.py with the pre-BNN version.
        _is_legacy = any(seg in _p for seg in ('/0310', 'hpr_legacy'))
        if _is_legacy:
            if _p not in sys.path:
                sys.path.append(_p)
        else:
            sys.path.insert(0, _p)

from experiment_config_0404 import (
    INPUT_COLS, OUTPUT_COLS,
    PRIMARY_STRESS_OUTPUT, PRIMARY_STRESS_THRESHOLD,
    DESIGN_NOMINAL, DESIGN_SIGMA,
    RISK_PROP_N_SAMPLES, RISK_PROP_SIGMA_K,
    BNN_N_MC_EVAL,
    SEED, DEVICE, FIXED_SPLIT_DIR,
)
from model_registry_0404 import MODELS
from run_eval_0404 import _resolve_artifacts, _load_model, _load_scalers
from manifest_utils_0404 import resolve_output_dir
from bnn_model import mc_predict, get_device, seed_all

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


# ────────────────────────────────────────────────────────────
# Predictors
# ────────────────────────────────────────────────────────────
@torch.no_grad()
def _predict_mean_weights(model, X_np: np.ndarray, sx, sy, device):
    """
    确定性 forward：使用 BNN 的后验均值权重（sample=False），
    返回 (mu_orig, sigma_aleatoric_orig) —— 尺度为原始输出空间。

    此路径不做 MC 采样；sigma 仅是 heteroscedastic aleatoric 分量
    （由 logvar_head 输出），供记录但不参与 mu-only 抽样。
    """
    model.eval()
    X_scaled = sx.transform(X_np)
    x_t = torch.tensor(X_scaled, dtype=torch.float32, device=device)
    mu_scaled, logvar_scaled = model(x_t, sample=False)
    mu_np       = mu_scaled.detach().cpu().numpy()
    logvar_np   = logvar_scaled.detach().cpu().numpy()

    sy_mean  = sy.mean_[np.newaxis, :]
    sy_scale = sy.scale_[np.newaxis, :]
    mu_orig          = mu_np * sy_scale + sy_mean
    var_orig         = np.exp(logvar_np) * (sy_scale ** 2)
    sigma_aleatoric  = np.sqrt(var_orig)
    return mu_orig, sigma_aleatoric


def _predict_mc(model, X_np: np.ndarray, sx, sy, device):
    """BNN MC 预测：返回 (mu_mean, sigma_total, epistemic_std, aleatoric_std)."""
    mu_mean, mu_std, aleatoric_var, epistemic_var, total_var = mc_predict(
        model, X_np, sx, sy, device, n_mc=BNN_N_MC_EVAL
    )
    sigma_total   = np.sqrt(total_var)
    epistemic_std = np.sqrt(epistemic_var)
    aleatoric_std = np.sqrt(aleatoric_var)
    return mu_mean, sigma_total, epistemic_std, aleatoric_std


# ────────────────────────────────────────────────────────────
# D1 runner
# ────────────────────────────────────────────────────────────
def run_D1(model_id, model, sx, sy, device,
           sigma_k_list, threshold_list, draw_predictive, tag):
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

        if draw_predictive:
            # MC 路径：完整 epistemic + aleatoric
            mu, sigma_pred, epi_std, ale_std = _predict_mc(model, X_samp, sx, sy, device)
            eps = rng.standard_normal(size=mu.shape)
            y_draw = mu + sigma_pred * eps
        else:
            # mu-only 路径：后验均值权重，纯确定性
            mu, sigma_pred = _predict_mean_weights(model, X_samp, sx, sy, device)
            epi_std = np.zeros_like(mu)      # by definition under mean-weights
            ale_std = sigma_pred
            y_draw = mu

        stress_draw = y_draw[:, STRESS_IDX]
        keff_draw   = y_draw[:, KEFF_IDX]

        # iter1 stress from same samples (always mu-only for iter1 trace)
        iter1_stress = mu[:, ITER1_STRESS_IDX]

        for tau in threshold_list:
            p_exceed = float(np.mean(stress_draw > tau))
            row = {
                "sigma_k":                   k,
                "threshold_MPa":             tau,
                "P_exceed":                  p_exceed,
                "stress_mean":               float(np.mean(stress_draw)),
                "stress_std":                float(np.std(stress_draw)),
                "stress_p5":                 float(np.percentile(stress_draw, 5)),
                "stress_p50":                float(np.percentile(stress_draw, 50)),
                "stress_p95":                float(np.percentile(stress_draw, 95)),
                "stress_pred_mu_mean":       float(np.mean(mu[:, STRESS_IDX])),
                "stress_pred_sigma_mean":    float(np.mean(sigma_pred[:, STRESS_IDX])),
                "stress_pred_epistemic_mean":float(np.mean(epi_std[:, STRESS_IDX])),
                "stress_pred_aleatoric_mean":float(np.mean(ale_std[:, STRESS_IDX])),
                "keff_mean":                 float(np.mean(keff_draw)),
                "keff_std":                  float(np.std(keff_draw)),
                "iter1_stress_mean":         float(np.mean(iter1_stress)),
                "iter1_stress_std":          float(np.std(iter1_stress)),
                "sample_source":             "predictive" if draw_predictive else "mean_only",
            }
            rows.append(row)
            logger.info(
                f"  k={k:.1f}σ, τ={tau} MPa → P(exceed)={p_exceed:.4f} "
                f"(stress μ={row['stress_mean']:.1f} σ={row['stress_std']:.1f} MPa)"
            )

    meta = {
        "experiment":           f"D1_{tag}",
        "model_id":             model_id,
        "model_class":          "BayesianMLP",
        "inference_method":     "mc_sampling" if draw_predictive else "mean_weights",
        "n_mc_eval":            int(BNN_N_MC_EVAL) if draw_predictive else 0,
        "N_samples":            RISK_PROP_N_SAMPLES,
        "sigma_k_list":         sigma_k_list,
        "threshold_sweep_MPa":  threshold_list,
        "draw_predictive":      draw_predictive,
        "tag":                  tag,
        "design_nominal":       DESIGN_NOMINAL,
        "design_sigma_1sigma":  DESIGN_SIGMA,
        "artifact_origin":      "trained_in_bnn0414",
        "training_protocol":    "bnn0414_fixed",
        "rows":                 rows,
    }
    return meta, pd.DataFrame(rows)


if __name__ == "__main__":
    model_id = os.environ.get("MODEL_ID", "bnn-data-mono-ineq")
    if model_id not in MODELS:
        raise ValueError(f"未知 MODEL_ID: {model_id}。可选: {list(MODELS.keys())}")

    # output dir —— 不覆盖 canonical risk_propagation
    # 与 0411 保持相同的 risk_propagation_0410 子目录命名
    from experiment_config_0404 import EXPR_ROOT_0404
    out_base = resolve_output_dir(
        os.path.join(EXPR_ROOT_0404, "experiments", "risk_propagation_0410", model_id),
        script_name=os.path.basename(__file__),
    )

    # load BNN model
    ckpt_path, scaler_path = _resolve_artifacts(model_id)
    device  = get_device(DEVICE)
    seed_all(SEED)
    model   = _load_model(ckpt_path, device)
    scalers = _load_scalers(scaler_path)
    sx, sy  = scalers["sx"], scalers["sy"]

    sigma_k_list    = RISK_PROP_SIGMA_K           # [0.5, 1.0, 1.5, 2.0]
    thresholds_main = [110.0, 120.0, 131.0]
    thresholds_ext  = [110.0, 120.0, 131.0, 169.0, 200.0]

    # ── 1. mu-only (主文 canonical evidence) ──
    meta_mu, df_mu = run_D1(model_id, model, sx, sy, device,
                            sigma_k_list, thresholds_ext,
                            draw_predictive=False, tag="muonly")
    df_mu.to_csv(os.path.join(out_base, "D1_muonly.csv"), index=False)
    with open(os.path.join(out_base, "D1_muonly.json"), "w") as f:
        json.dump(meta_mu, f, indent=2)
    logger.info(f"[mu-only] → {out_base}/D1_muonly.json")

    # ── 2. predictive draw + extended thresholds (附录) ──
    meta_pred, df_pred = run_D1(model_id, model, sx, sy, device,
                                sigma_k_list, thresholds_ext,
                                draw_predictive=True, tag="predictive_extended")
    df_pred.to_csv(os.path.join(out_base, "D1_predictive_extended.csv"), index=False)
    with open(os.path.join(out_base, "D1_predictive_extended.json"), "w") as f:
        json.dump(meta_pred, f, indent=2)
    logger.info(f"[predictive-ext] → {out_base}/D1_predictive_extended.json")

    # ── 3. Summary ──
    print("\n" + "="*72)
    print(f"SUMMARY — {model_id} forward UQ (BNN)")
    print("="*72)
    print("\n[mu-only (mean-weights), σ_k=1.0, main-text canonical]")
    for _, r in df_mu[df_mu.sigma_k == 1.0].iterrows():
        print(f"  τ={r.threshold_MPa:.0f} MPa  P_exceed={r.P_exceed:.4f}  "
              f"stress μ={r.stress_mean:.1f}±{r.stress_std:.1f}  "
              f"keff μ={r.keff_mean:.6f}±{r.keff_std:.6f}")
        print(f"    iter1_stress μ={r.iter1_stress_mean:.1f}±{r.iter1_stress_std:.1f}")

    print("\n[predictive draw (MC, total uncertainty), σ_k=1.0, appendix]")
    for _, r in df_pred[df_pred.sigma_k == 1.0].iterrows():
        print(f"  τ={r.threshold_MPa:.0f} MPa  P_exceed={r.P_exceed:.4f}  "
              f"stress μ={r.stress_mean:.1f}±{r.stress_std:.1f}  "
              f"(epi={r.stress_pred_epistemic_mean:.2f}, ale={r.stress_pred_aleatoric_mean:.2f})")
