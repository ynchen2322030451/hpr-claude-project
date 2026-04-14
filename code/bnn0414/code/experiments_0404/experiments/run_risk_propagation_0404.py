# run_risk_propagation_0404.py
# ============================================================
# BNN 0414 风险传播实验
#
# BNN adaptation of code/0411/.../run_risk_propagation_0404.py.
#
# 关键 BNN 改动：
#   - _predict 已是 MC-averaged（从 run_eval_0404 导入）
#   - 额外保存 epistemic_std / aleatoric_std（不确定性分解）
#   - _predict_full 返回 (mu_mean, sigma_total, epistemic_var, aleatoric_var)
#   - 超越概率仍基于 mu_mean（与 HeteroMLP 版本一致）
#
# 三类实验：
#   D1. 围绕标称设计值扰动 -> P(stress > tau) vs. k*sigma 曲线
#   D2. 围绕代表性 test case 扰动 -> case-level 风险曲线
#   D3. 多物理耦合路径分析 -> iter1 vs iter2 输出关联统计
#
# 调用方式:
#   MODEL_ID=bnn-baseline RISK_EXP=D1 python run_risk_propagation_0404.py
#   MODEL_ID=bnn-data-mono RISK_EXP=all python run_risk_propagation_0404.py
#
# 输出:
#   bnn0414/code/experiments_0404/experiments/risk_propagation/<model_id>/
#     D1_nominal_risk.json   D1_nominal_risk.csv
#     D2_case_risk.json      D2_case_risk.csv
#     D3_coupling.json       D3_coupling.csv
# ============================================================

import os, sys, json, logging
from datetime import datetime

import numpy as np
import pandas as pd
import torch

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_CODE_DIR = os.path.dirname(_SCRIPT_DIR)
for _p in [
    os.path.join(_CODE_DIR, 'config'),
    os.path.dirname(_CODE_DIR),  # experiments_0404/
    os.path.dirname(os.path.dirname(_CODE_DIR)),  # bnn0414/code/
    os.path.dirname(os.path.dirname(os.path.dirname(_CODE_DIR))),  # code/0310/
    os.path.join(_CODE_DIR, 'evaluation'),
    os.environ.get('HPR_LEGACY_DIR', ''),
]:
    if _p and os.path.isdir(_p) and _p not in sys.path:
        sys.path.insert(0, _p)

from experiment_config_0404 import (
    INPUT_COLS, OUTPUT_COLS, PRIMARY_OUTPUTS, PRIMARY_STRESS_OUTPUT,
    PRIMARY_STRESS_THRESHOLD, THRESHOLD_SWEEP,
    DESIGN_NOMINAL, DESIGN_SIGMA,
    RISK_PROP_N_SAMPLES, RISK_PROP_SIGMA_K,
    RISK_PROP_CASE_SIGMA_K, RISK_PROP_CASE_CATEGORIES,
    RISK_PROP_DRAW_PRED,
    BNN_N_MC_EVAL,
    SEED, DEVICE,
    FIXED_SPLIT_DIR, EXPR_ROOT_OLD,
    model_artifacts_dir, experiment_dir, ensure_dir,
    DELTA_PAIRS, OUT1, OUT2,
)
from model_registry_0404 import MODELS
from manifest_utils_0404 import write_manifest, make_experiment_manifest
from run_eval_0404 import _resolve_artifacts, _load_model, _load_scalers, _predict, _predict_full

# ────────────────────────────────────────────────────────────
# 日志
# ────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# 主应力输出的列索引
STRESS_IDX = OUTPUT_COLS.index(PRIMARY_STRESS_OUTPUT)
KEFF_IDX   = OUTPUT_COLS.index("iteration2_keff")


# ────────────────────────────────────────────────────────────
# D1: 标称设计值扰动风险分析
# ────────────────────────────────────────────────────────────
def run_D1_nominal_risk(model_id: str, model, sx, sy, device, out_dir: str):
    """
    围绕设计标称值，以 k*sigma (k in RISK_PROP_SIGMA_K) 为标准差采样，
    计算 P(stress > tau) 对每个 tau in THRESHOLD_SWEEP，并记录风险曲线。
    BNN 版本额外保存 epistemic/aleatoric 不确定性分解。
    """
    logger.info(f"[D1][{model_id}] 标称设计值风险分析，N={RISK_PROP_N_SAMPLES}")

    nominal = np.array([DESIGN_NOMINAL[c] for c in INPUT_COLS])
    sigma_1 = np.array([DESIGN_SIGMA[c]   for c in INPUT_COLS])

    rng = np.random.default_rng(SEED)
    rows = []

    for k in RISK_PROP_SIGMA_K:
        sigma_k = k * sigma_1
        X_samp  = rng.normal(loc=nominal, scale=sigma_k, size=(RISK_PROP_N_SAMPLES, len(INPUT_COLS)))

        # BNN MC-averaged prediction with uncertainty decomposition
        mu, sigma_pred, epistemic_var, aleatoric_var = _predict_full(
            model, X_samp, sx, sy, device
        )

        if RISK_PROP_DRAW_PRED:
            # 从预测分布采样（mu + sigma*eps）-> 更完整的 UQ
            eps = rng.standard_normal(size=mu.shape)
            y_draw = mu + sigma_pred * eps
        else:
            y_draw = mu

        stress_draw = y_draw[:, STRESS_IDX]

        # BNN-specific: epistemic/aleatoric std for stress output
        epi_std_stress = float(np.mean(np.sqrt(epistemic_var[:, STRESS_IDX])))
        ale_std_stress = float(np.mean(np.sqrt(aleatoric_var[:, STRESS_IDX])))

        for tau in THRESHOLD_SWEEP:
            p_exceed = float(np.mean(stress_draw > tau))
            row = {
                "sigma_k":           k,
                "threshold_MPa":     tau,
                "P_exceed":          p_exceed,
                "stress_mean":       float(np.mean(stress_draw)),
                "stress_std":        float(np.std(stress_draw)),
                "stress_p5":         float(np.percentile(stress_draw, 5)),
                "stress_p50":        float(np.percentile(stress_draw, 50)),
                "stress_p95":        float(np.percentile(stress_draw, 95)),
                "stress_pred_mu_mean":    float(np.mean(mu[:, STRESS_IDX])),
                "stress_pred_sigma_mean": float(np.mean(sigma_pred[:, STRESS_IDX])),
                "stress_epistemic_std":   epi_std_stress,
                "stress_aleatoric_std":   ale_std_stress,
                "keff_mean":         float(np.mean(y_draw[:, KEFF_IDX])),
                "keff_std":          float(np.std(y_draw[:, KEFF_IDX])),
                "sample_source":     "predictive" if RISK_PROP_DRAW_PRED else "mean_only",
                "n_mc_eval":         BNN_N_MC_EVAL,
            }
            rows.append(row)
            logger.info(
                f"  k={k:.1f}sigma, tau={tau} MPa -> P(exceed)={p_exceed:.3f} "
                f"(stress mu={row['stress_mean']:.1f} MPa, epi_std={epi_std_stress:.2f}, ale_std={ale_std_stress:.2f})"
            )

    df = pd.DataFrame(rows)
    csv_path  = os.path.join(out_dir, "D1_nominal_risk.csv")
    json_path = os.path.join(out_dir, "D1_nominal_risk.json")
    df.to_csv(csv_path, index=False)

    meta = {
        "experiment":   "D1_nominal_risk",
        "model_id":     model_id,
        "model_type":   "BNN",
        "N_samples":    RISK_PROP_N_SAMPLES,
        "sigma_k_list": RISK_PROP_SIGMA_K,
        "threshold_sweep_MPa": THRESHOLD_SWEEP,
        "draw_predictive": RISK_PROP_DRAW_PRED,
        "n_mc_eval":    BNN_N_MC_EVAL,
        "design_nominal": DESIGN_NOMINAL,
        "design_sigma_1sigma": DESIGN_SIGMA,
        "rows": rows,
    }
    with open(json_path, "w") as f:
        json.dump(meta, f, indent=2)

    logger.info(f"[D1][{model_id}] results -> {csv_path}")
    return meta


# ────────────────────────────────────────────────────────────
# D2: 代表性 case 扰动风险分析
# ────────────────────────────────────────────────────────────
def _select_representative_cases(test_df: pd.DataFrame, n_per_cat: int = 3):
    """
    从 test split 按 iteration2_max_global_stress 分位选代表性 case。
    类别: low_stress / near_threshold / above_threshold / extreme_stress
    注意: 此处使用 test_df 里已有的输出列（真实值），而非预测。
    """
    stress_col = PRIMARY_STRESS_OUTPUT
    if stress_col not in test_df.columns:
        logger.warning(f"test_df 中无 {stress_col}，D2 无法运行")
        return {}

    s = test_df[stress_col].values
    tau = PRIMARY_STRESS_THRESHOLD

    categories = {
        "low_stress":       test_df[s < 0.92 * tau],            # <120 MPa
        "near_threshold":   test_df[(s >= 0.92*tau) & (s < tau)],  # 120-131 MPa
        "above_threshold":  test_df[(s >= tau) & (s < 1.37*tau)],  # 131-180 MPa
        "extreme_stress":   test_df[s >= 1.37 * tau],            # >180 MPa
    }

    selected = {}
    for cat, subset in categories.items():
        if len(subset) == 0:
            logger.warning(f"[D2] category {cat} has no samples")
            continue
        n = min(n_per_cat, len(subset))
        selected[cat] = subset.sample(n=n, random_state=SEED).reset_index(drop=True)
        logger.info(f"[D2] {cat}: {len(subset)} candidates, selected {n}")

    return selected


def run_D2_case_risk(model_id: str, model, sx, sy, device, out_dir: str):
    """
    对各代表性 case 的输入值为中心，以 k*sigma 扰动，
    计算局部 P(stress > tau) 分布。
    BNN 版本额外保存 epistemic/aleatoric 不确定性。
    """
    logger.info(f"[D2][{model_id}] case-level risk analysis")

    test_df = pd.read_csv(os.path.join(FIXED_SPLIT_DIR, "test.csv"))
    rng = np.random.default_rng(SEED + 1)

    sigma_1 = np.array([DESIGN_SIGMA[c] for c in INPUT_COLS])
    tau = PRIMARY_STRESS_THRESHOLD

    case_groups = _select_representative_cases(test_df, n_per_cat=3)
    if not case_groups:
        logger.warning("[D2] no representative cases, skipping")
        return {}

    rows = []
    for cat, subset in case_groups.items():
        for ci in range(len(subset)):
            case_row = subset.iloc[ci]
            x_center = case_row[INPUT_COLS].values.astype(float)
            y_true_stress = float(case_row[PRIMARY_STRESS_OUTPUT]) if PRIMARY_STRESS_OUTPUT in case_row else np.nan

            for k in RISK_PROP_CASE_SIGMA_K:
                X_samp = rng.normal(
                    loc   = x_center,
                    scale = k * sigma_1,
                    size  = (RISK_PROP_N_SAMPLES, len(INPUT_COLS)),
                )
                mu, sigma_pred, epistemic_var, aleatoric_var = _predict_full(
                    model, X_samp, sx, sy, device
                )

                if RISK_PROP_DRAW_PRED:
                    eps    = rng.standard_normal(size=mu.shape)
                    y_draw = mu + sigma_pred * eps
                else:
                    y_draw = mu

                stress_draw = y_draw[:, STRESS_IDX]

                row = {
                    "category":          cat,
                    "case_idx":          ci,
                    "sigma_k":           k,
                    "y_true_stress":     y_true_stress,
                    "P_exceed_131":      float(np.mean(stress_draw > tau)),
                    "stress_mean":       float(np.mean(stress_draw)),
                    "stress_std":        float(np.std(stress_draw)),
                    "stress_p5":         float(np.percentile(stress_draw, 5)),
                    "stress_p95":        float(np.percentile(stress_draw, 95)),
                    "stress_epistemic_std":  float(np.mean(np.sqrt(epistemic_var[:, STRESS_IDX]))),
                    "stress_aleatoric_std":  float(np.mean(np.sqrt(aleatoric_var[:, STRESS_IDX]))),
                }
                rows.append(row)

    df = pd.DataFrame(rows)
    csv_path  = os.path.join(out_dir, "D2_case_risk.csv")
    json_path = os.path.join(out_dir, "D2_case_risk.json")
    df.to_csv(csv_path, index=False)

    meta = {
        "experiment":     "D2_case_risk",
        "model_id":       model_id,
        "model_type":     "BNN",
        "sigma_k_list":   RISK_PROP_CASE_SIGMA_K,
        "N_samples":      RISK_PROP_N_SAMPLES,
        "primary_threshold_MPa": tau,
        "n_mc_eval":      BNN_N_MC_EVAL,
        "rows": rows,
    }
    with open(json_path, "w") as f:
        json.dump(meta, f, indent=2)

    logger.info(f"[D2][{model_id}] results -> {csv_path} ({len(rows)} rows)")
    return meta


# ────────────────────────────────────────────────────────────
# D3: 多物理耦合路径分析
# ────────────────────────────────────────────────────────────
def run_D3_coupling(model_id: str, model, sx, sy, device, out_dir: str):
    """
    分析 iter1 -> iter2 输出对之间的统计关联：
      - 均值偏移（iter2 - iter1）
      - 方差比（sigma^2_iter2 / sigma^2_iter1）
      - Spearman 秩相关（mu_iter1 vs mu_iter2）
    在 test split 上计算。
    """
    from scipy.stats import spearmanr

    logger.info(f"[D3][{model_id}] multi-physics coupling analysis")

    test_df = pd.read_csv(os.path.join(FIXED_SPLIT_DIR, "test.csv"))
    X_test  = test_df[INPUT_COLS].values

    mu, sigma_pred = _predict(model, X_test, sx, sy, device)

    rows = []
    for out1_name, out2_name in DELTA_PAIRS:
        if out1_name not in OUTPUT_COLS or out2_name not in OUTPUT_COLS:
            continue
        i1 = OUTPUT_COLS.index(out1_name)
        i2 = OUTPUT_COLS.index(out2_name)

        mu1, mu2 = mu[:, i1], mu[:, i2]
        s1, s2   = sigma_pred[:, i1], sigma_pred[:, i2]

        delta_mean   = float(np.mean(mu2 - mu1))
        delta_std    = float(np.std(mu2 - mu1))
        var_ratio    = float(np.mean(s2**2) / (np.mean(s1**2) + 1e-30))
        rho, p_rho   = spearmanr(mu1, mu2)

        # 真实值（若存在）
        if out1_name in test_df.columns and out2_name in test_df.columns:
            y1_true, y2_true = test_df[out1_name].values, test_df[out2_name].values
            delta_mean_true  = float(np.mean(y2_true - y1_true))
            rho_true, _      = spearmanr(y1_true, y2_true)
        else:
            delta_mean_true = np.nan
            rho_true        = np.nan

        short1 = out1_name.replace("iteration1_", "")
        short2 = out2_name.replace("iteration2_", "")
        rows.append({
            "iter1_output":        out1_name,
            "iter2_output":        out2_name,
            "output_short":        short1,
            "pred_delta_mean":     delta_mean,
            "pred_delta_std":      delta_std,
            "pred_var_ratio_2to1": var_ratio,
            "pred_spearman_rho":   float(rho),
            "pred_spearman_p":     float(p_rho),
            "true_delta_mean":     delta_mean_true,
            "true_spearman_rho":   float(rho_true) if not np.isnan(rho_true) else None,
        })
        logger.info(
            f"  {short1}: delta={delta_mean:+.2f} (+/-{delta_std:.2f}), "
            f"var_ratio={var_ratio:.3f}, rho={rho:.3f}"
        )

    df = pd.DataFrame(rows)
    csv_path  = os.path.join(out_dir, "D3_coupling.csv")
    json_path = os.path.join(out_dir, "D3_coupling.json")
    df.to_csv(csv_path, index=False)

    meta = {
        "experiment": "D3_coupling",
        "model_id":   model_id,
        "model_type": "BNN",
        "n_test":     len(test_df),
        "n_mc_eval":  BNN_N_MC_EVAL,
        "rows": rows,
    }
    with open(json_path, "w") as f:
        json.dump(meta, f, indent=2)

    logger.info(f"[D3][{model_id}] results -> {csv_path}")
    return meta


# ────────────────────────────────────────────────────────────
# 入口
# ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    MODEL_ID_OVERRIDE  = "bnn-baseline"
    RISK_EXP_OVERRIDE  = "all"   # "D1" | "D2" | "D3" | "all"

    model_id = os.environ.get("MODEL_ID",   MODEL_ID_OVERRIDE)
    risk_exp = os.environ.get("RISK_EXP",   RISK_EXP_OVERRIDE)
    force    = os.environ.get("RISK_FORCE", "0") == "1"

    if model_id not in MODELS:
        raise ValueError(f"Unknown MODEL_ID: {model_id}. Available: {list(MODELS.keys())}")

    # 输出目录
    exp_base = ensure_dir(
        os.path.join(experiment_dir("risk_propagation"), model_id)
    )

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = os.path.join(exp_base, f"risk_{ts}.log")
    fh = logging.FileHandler(log_path)
    fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(fh)

    logger.info(f"risk_propagation_0404 (BNN) | model={model_id} | exp={risk_exp}")

    # 加载模型
    ckpt_path, scaler_path = _resolve_artifacts(model_id)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model   = _load_model(ckpt_path, device)
    scalers = _load_scalers(scaler_path)
    sx, sy  = scalers["sx"], scalers["sy"]

    results = {}

    if risk_exp in ("D1", "all"):
        results["D1"] = run_D1_nominal_risk(model_id, model, sx, sy, device, exp_base)

    if risk_exp in ("D2", "all"):
        results["D2"] = run_D2_case_risk(model_id, model, sx, sy, device, exp_base)

    if risk_exp in ("D3", "all"):
        results["D3"] = run_D3_coupling(model_id, model, sx, sy, device, exp_base)

    # 汇总 manifest
    mf = make_experiment_manifest(
        experiment_id = f"risk_propagation_{risk_exp}",
        model_id      = model_id,
        input_source  = FIXED_SPLIT_DIR,
        outputs_saved = [
            os.path.join(exp_base, f)
            for f in ["D1_nominal_risk.csv", "D2_case_risk.csv", "D3_coupling.csv"]
            if os.path.exists(os.path.join(exp_base, f))
        ],
        key_results = {k: v.get("rows", [])[:2] if isinstance(v, dict) else str(v)
                       for k, v in results.items()},
        source_script = __file__,
        extra = {"risk_exp": risk_exp, "model_type": "BNN", "n_mc_eval": BNN_N_MC_EVAL},
    )
    write_manifest(os.path.join(exp_base, "risk_manifest.json"), mf)
    logger.info(f"[{model_id}] risk_propagation done")
