# run_generalization_0404.py
# ============================================================
# BNN 0414 OOD 泛化实验（基于 0411 版本改写）
#
# 与 0411 的差异：
#   - 模型：BayesianMLP 替代 HeteroMLP
#   - 预测：mc_predict() 返回 mu_mean 与 (epistemic, aleatoric, total) var
#   - sigma = sqrt(total_var) 用于概率指标（PICP/MPIW/CRPS）
#   - per-output CSV 增加 epistemic_std_mean / aleatoric_std_mean 两列
#
# 方法：
#   对多个输入特征，按特征值分位数分割（中间 80% in-dist，头尾 20% OOD），
#   用已训练的 BNN surrogate 直接 MC 评估（不重训）。
#
# OOD 特征：E_intercept, alpha_base, nu, alpha_slope（参考 Sobol 主效应）
#
# 调用方式：
#   MODEL_ID=bnn-baseline  python run_generalization_0404.py
#   MODEL_ID=bnn-data-mono python run_generalization_0404.py
#
# 输出：
#   experiments_0404/experiments/generalization/<model_id>/
#     ood_summary.csv
#     ood_per_output.csv
#     generalization_manifest.json
# ============================================================

import os, sys, json, logging
from datetime import datetime

import numpy as np
import pandas as pd
import torch

# ── path setup (inline walk-up, same as run_risk_propagation_0404.py) ──
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
    INPUT_COLS, OUTPUT_COLS, PRIMARY_OUTPUTS,
    PRIMARY_STRESS_OUTPUT, PRIMARY_AUXILIARY_OUTPUT,
    SEED, DEVICE, FIXED_SPLIT_DIR,
    OOD_FEATURE, OOD_KEEP_MIDDLE_RATIO,
    BNN_N_MC_EVAL,
    experiment_dir, ensure_dir,
    get_csv_path,
)
from model_registry_0404 import MODELS
from manifest_utils_0404 import write_manifest, make_experiment_manifest, resolve_output_dir
# Reuse BNN loaders from run_eval_0404 (BNN-specific _predict returns
# mu + sigma_total; we use _predict_full to also retrieve epistemic/aleatoric)
from run_eval_0404 import (
    _resolve_artifacts, _load_model, _load_scalers,
    _predict, _predict_full,
)
from bnn_model import get_device, seed_all
# Pure-numpy metric helpers
from run_phys_levels_main import (
    compute_basic_metrics, compute_prob_metrics_gaussian,
)

# ────────────────────────────────────────────────────────────
# 日志
# ────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# OOD 特征集（主要是 stress 的 Sobol 主效应贡献者）
OOD_FEATURES = ["E_intercept", "alpha_base", "nu", "alpha_slope"]
KEEP_MIDDLE_RATIO = OOD_KEEP_MIDDLE_RATIO   # 0.80


# ────────────────────────────────────────────────────────────
# OOD 数据分割
# ────────────────────────────────────────────────────────────
def make_ood_split(X: np.ndarray, Y: np.ndarray, feature: str, ratio: float = 0.80):
    """
    按 feature 的分位数分割：
      in-distribution = 中间 ratio；OOD = 头尾各 (1-ratio)/2
    返回 (X_in, Y_in, X_ood, Y_ood, lo, hi)
    """
    feat_idx = INPUT_COLS.index(feature)
    x_feat   = X[:, feat_idx]

    q_lo = (1.0 - ratio) / 2.0
    q_hi = 1.0 - q_lo
    lo = float(np.quantile(x_feat, q_lo))
    hi = float(np.quantile(x_feat, q_hi))

    in_mask  = (x_feat >= lo) & (x_feat <= hi)
    ood_mask = ~in_mask

    return X[in_mask], Y[in_mask], X[ood_mask], Y[ood_mask], lo, hi


# ────────────────────────────────────────────────────────────
# 指标聚合
# ────────────────────────────────────────────────────────────
def _overall(metrics: dict) -> dict:
    out = {}
    for k, v in metrics.items():
        if hasattr(v, "__len__"):
            out[k + "_mean"] = float(np.mean(v))
        else:
            out[k] = float(v)
    return out


# ────────────────────────────────────────────────────────────
# 主实验
# ────────────────────────────────────────────────────────────
def run_generalization(model_id: str, model, sx, sy, device, out_dir: str):
    # 需要完整数据集（用于 OOD 分割）
    csv_path = get_csv_path()
    if csv_path is None:
        # 回退：从 fixed_split 合并 train+val+test
        logger.warning("CSV 路径不可达，从 fixed_split 合并 train+val+test 作为全集")
        dfs = [pd.read_csv(os.path.join(FIXED_SPLIT_DIR, f"{s}.csv"))
               for s in ("train", "val", "test")]
        df_full = pd.concat(dfs, ignore_index=True)
    else:
        df_full = pd.read_csv(csv_path)

    X_full = df_full[INPUT_COLS].values.astype(float)
    Y_full = df_full[OUTPUT_COLS].values.astype(float)
    logger.info(f"[{model_id}] OOD 全集: {len(df_full)} 行 (n_mc={BNN_N_MC_EVAL})")

    summary_rows  = []
    per_out_rows  = []

    for feat in OOD_FEATURES:
        if feat not in INPUT_COLS:
            logger.warning(f"  [SKIP] OOD feature {feat} 不在 INPUT_COLS")
            continue

        X_in, Y_in, X_ood, Y_ood, lo, hi = make_ood_split(
            X_full, Y_full, feat, KEEP_MIDDLE_RATIO
        )
        logger.info(
            f"  [{feat}] in={len(X_in)}, ood={len(X_ood)}, "
            f"split=[{lo:.4g}, {hi:.4g}]"
        )

        for split_name, X_s, Y_s in [("in_dist", X_in, Y_in), ("ood", X_ood, Y_ood)]:
            if len(X_s) == 0:
                logger.warning(f"  [{feat}][{split_name}] 空集，跳过")
                continue

            # BNN MC 预测 + 不确定度分解
            mu, sigma, epi_var, ale_var = _predict_full(model, sx, sy, X_s, device)
            epi_std = np.sqrt(epi_var)
            ale_std = np.sqrt(ale_var)

            basic = compute_basic_metrics(Y_s, mu)
            prob  = compute_prob_metrics_gaussian(Y_s, mu, sigma)
            metrics = {**basic, **prob}
            overall = _overall(metrics)

            summary_rows.append({
                "model_id":              model_id,
                "ood_feature":           feat,
                "split":                 split_name,
                "n":                     len(X_s),
                "feat_lo":               lo,
                "feat_hi":               hi,
                "epistemic_std_mean":    float(np.mean(epi_std)),
                "aleatoric_std_mean":    float(np.mean(ale_std)),
                **overall,
            })

            # per-output
            n_out = len(OUTPUT_COLS)
            for j, col in enumerate(OUTPUT_COLS):
                row = {
                    "model_id":           model_id,
                    "ood_feature":        feat,
                    "split":              split_name,
                    "output":             col,
                    "epistemic_std_mean": float(np.mean(epi_std[:, j])),
                    "aleatoric_std_mean": float(np.mean(ale_std[:, j])),
                }
                for k, v in metrics.items():
                    if hasattr(v, "__len__") and len(v) == n_out:
                        row[k] = float(v[j])
                per_out_rows.append(row)

    df_summary = pd.DataFrame(summary_rows)
    df_per_out = pd.DataFrame(per_out_rows)

    summary_csv = os.path.join(out_dir, "ood_summary.csv")
    per_out_csv = os.path.join(out_dir, "ood_per_output.csv")
    df_summary.to_csv(summary_csv, index=False)
    df_per_out.to_csv(per_out_csv, index=False)

    # 简要日志：每个 feature 的 R² 对比
    for feat in OOD_FEATURES:
        sub = df_summary[df_summary["ood_feature"] == feat]
        if len(sub) < 2:
            continue
        r2_in  = sub[sub["split"] == "in_dist"]["R2_mean"].values
        r2_ood = sub[sub["split"] == "ood"]["R2_mean"].values
        if len(r2_in) and len(r2_ood):
            logger.info(
                f"  [{feat}] R²: in={float(r2_in[0]):.3f}, "
                f"ood={float(r2_ood[0]):.3f}, "
                f"Δ={float(r2_ood[0]-r2_in[0]):+.3f}"
            )

    logger.info(f"[{model_id}] OOD → {summary_csv}")
    return df_summary, df_per_out


# ────────────────────────────────────────────────────────────
# 多模型对比
# ────────────────────────────────────────────────────────────
def make_ood_comparison(model_ids: list, base_dir: str):
    """合并多个模型的 ood_summary 做横向对比。"""
    dfs = []
    for mid in model_ids:
        p = os.path.join(base_dir, mid, "ood_summary.csv")
        if os.path.exists(p):
            dfs.append(pd.read_csv(p))
    if not dfs:
        return
    df = pd.concat(dfs, ignore_index=True)
    df.to_csv(os.path.join(base_dir, "ood_comparison.csv"), index=False)
    logger.info(f"[compare] OOD 对比 → {os.path.join(base_dir, 'ood_comparison.csv')}")


# ────────────────────────────────────────────────────────────
# 入口
# ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    MODEL_ID_OVERRIDE = "bnn-baseline"

    model_id = os.environ.get("MODEL_ID", MODEL_ID_OVERRIDE)
    force    = os.environ.get("OOD_FORCE", "0") == "1"

    if model_id not in MODELS:
        raise ValueError(f"未知 MODEL_ID: {model_id}。可选: {list(MODELS.keys())}")

    base_exp = experiment_dir("generalization")
    out_dir  = resolve_output_dir(
        os.path.join(base_exp, model_id),
        script_name=os.path.basename(__file__),
    )

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    fh = logging.FileHandler(os.path.join(out_dir, f"ood_{ts}.log"))
    fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(fh)

    logger.info(f"generalization_0404 (BNN) | model={model_id}")

    ckpt_path, scaler_path = _resolve_artifacts(model_id)
    device = get_device(DEVICE)
    seed_all(SEED)
    model  = _load_model(ckpt_path, device)
    scalers= _load_scalers(scaler_path)
    sx, sy = scalers["sx"], scalers["sy"]
    model.eval()

    df_sum, df_per = run_generalization(model_id, model, sx, sy, device, out_dir)

    mf = make_experiment_manifest(
        experiment_id = "generalization_ood",
        model_id      = model_id,
        input_source  = "full_dataset",
        outputs_saved = [
            os.path.join(out_dir, "ood_summary.csv"),
            os.path.join(out_dir, "ood_per_output.csv"),
        ],
        key_results = {
            "n_ood_features":     len(OOD_FEATURES),
            "keep_middle_ratio":  KEEP_MIDDLE_RATIO,
            "R2_mean_in_dist":    float(df_sum[df_sum["split"]=="in_dist"]["R2_mean"].mean()),
            "R2_mean_ood":        float(df_sum[df_sum["split"]=="ood"]["R2_mean"].mean()),
            "n_mc_eval":          int(BNN_N_MC_EVAL),
        },
        source_script = __file__,
        extra = {
            "ood_features":     OOD_FEATURES,
            "model_class":      "BayesianMLP",
            "inference_method": "mc_sampling",
            "artifact_origin":  "trained_in_bnn0414",
            "training_protocol":"bnn0414_fixed",
        },
    )
    write_manifest(os.path.join(out_dir, "generalization_manifest.json"), mf)
    logger.info(f"[{model_id}] generalization 完成")
