# run_physics_consistency_0404.py  (BNN 0414)
# ============================================================
# BNN 物理一致性验证脚本
#
# 功能：
#   1) 验证 bnn-phy-mono 模型：检查物理先验对的梯度方向是否满足
#   2) 对比 bnn-data-mono 的数据驱动方向与 bnn-phy-mono 的物理先验方向
#   3) 输出每个 (input, output, sign) 三元组的一致性统计
#
# BNN 适配要点：
#   - 使用 model(x, sample=False) 做 deterministic 前向（mean weights），
#     这样梯度方向检查不受 MC 随机权重采样噪声影响。
#   - BNN forward 返回 (mu, logvar)，与 HeteroMLP 一致。
#
# 调用方式:
#   MODEL_ID=bnn-phy-mono python run_physics_consistency_0404.py
#   MODEL_ID=bnn-data-mono python run_physics_consistency_0404.py
#   MODEL_ID=all python run_physics_consistency_0404.py
# ============================================================

import os, sys, json, logging
from datetime import datetime

import numpy as np
import pandas as pd
import torch

# ── 路径引导 ────────────────────────────────────────────────
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_EXPR_DIR   = os.path.dirname(_SCRIPT_DIR)                  # experiments_0404/
sys.path.insert(0, _EXPR_DIR)
from _path_setup import setup_paths  # noqa: E402
setup_paths()
sys.path.insert(0, os.path.join(_EXPR_DIR, "evaluation"))   # for run_eval_0404

from experiment_config_0404 import (
    INPUT_COLS, OUTPUT_COLS,
    SEED,
    FIXED_SPLIT_DIR,
    experiment_dir, ensure_dir,
)
from model_registry_0404 import (
    MODELS, PHYSICS_IDX_PAIRS_HIGH,
)
from manifest_utils_0404 import write_manifest, make_experiment_manifest, resolve_output_dir
from run_eval_0404 import _resolve_artifacts, _load_model, _load_scalers
from bnn_model import get_device

# ── 日志 ────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

N_GRAD_POINTS = 1000


# ────────────────────────────────────────────────────────────
# 梯度符号检验（BNN：sample=False，mean-weights 前向）
# ────────────────────────────────────────────────────────────
def check_gradient_signs(
    model, sx, sy, device,
    idx_pairs: list,
    X_eval: np.ndarray,
) -> pd.DataFrame:
    """
    对每个 (in_i, out_j, sign) pair，用 BNN mean-weights 前向
    计算 ∂μⱼ/∂xᵢ 在 X_eval 各点处的符号。
    """
    n, _ = X_eval.shape

    X_s = sx.transform(X_eval)
    X_t = torch.tensor(X_s, dtype=torch.float32, device=device)

    rows = []
    for (inp_idx, out_idx, expected_sign) in idx_pairs:
        inp_name = INPUT_COLS[inp_idx]
        out_name = OUTPUT_COLS[out_idx]

        grads = []
        for k in range(n):
            x_k = X_t[k:k+1].detach().clone().requires_grad_(True)
            # BNN deterministic forward: use mean weights (sample=False)
            out = model(x_k, sample=False)
            mu_s = out[0] if isinstance(out, tuple) else out
            mu_j = mu_s[0, out_idx]
            mu_j.backward()
            grads.append(float(x_k.grad[0, inp_idx]))

        grads = np.array(grads)
        frac_pos   = float(np.mean(grads > 0))
        frac_neg   = float(np.mean(grads < 0))
        frac_zero  = float(np.mean(grads == 0))
        mean_grad  = float(np.mean(grads))
        frac_correct = frac_pos if expected_sign > 0 else frac_neg

        rows.append({
            "input":         inp_name,
            "output":        out_name,
            "expected_sign": "+" if expected_sign > 0 else "-",
            "frac_correct":  frac_correct,
            "frac_pos":      frac_pos,
            "frac_neg":      frac_neg,
            "frac_zero":     frac_zero,
            "mean_grad":     mean_grad,
            "is_consistent": bool(frac_correct >= 0.9),
        })

        logger.info(
            f"  ({inp_name} → {out_name}, {'+'if expected_sign>0 else '-'}): "
            f"correct={frac_correct:.1%}, mean_grad={mean_grad:+.4f}"
        )

    return pd.DataFrame(rows)


# ────────────────────────────────────────────────────────────
# 与 Spearman 方向对比
# ────────────────────────────────────────────────────────────
def compare_with_data_direction(
    model_id: str,
    grad_df: pd.DataFrame,
    train_df: pd.DataFrame,
) -> pd.DataFrame:
    from scipy.stats import spearmanr

    rows = []
    for _, row in grad_df.iterrows():
        inp, out = row["input"], row["output"]
        if inp not in train_df.columns or out not in train_df.columns:
            continue
        rho, _ = spearmanr(train_df[inp].values, train_df[out].values)
        data_sign = "+" if rho >= 0 else "-"
        agrees = (data_sign == row["expected_sign"])

        rows.append({
            "input":             inp,
            "output":            out,
            "phy_sign":          row["expected_sign"],
            "data_spearman_rho": float(rho),
            "data_sign":         data_sign,
            "phy_data_agree":    agrees,
            "model_correct":     row["is_consistent"],
        })

    return pd.DataFrame(rows)


# ────────────────────────────────────────────────────────────
# 主函数：单个模型
# ────────────────────────────────────────────────────────────
def run_physics_consistency_one(model_id: str, out_dir: str):
    ensure_dir(out_dir)
    logger.info(f"[{model_id}] === BNN 物理一致性验证 ===")

    ckpt_path, scaler_path = _resolve_artifacts(model_id)
    device  = get_device()
    model   = _load_model(ckpt_path, device)
    scalers = _load_scalers(scaler_path)
    sx, sy  = scalers["sx"], scalers["sy"]
    model.eval()

    test_df  = pd.read_csv(os.path.join(FIXED_SPLIT_DIR, "test.csv"))
    train_df = pd.read_csv(os.path.join(FIXED_SPLIT_DIR, "train.csv"))

    X_eval = test_df[INPUT_COLS].values.astype(float)

    rng = np.random.default_rng(SEED)
    if len(X_eval) > N_GRAD_POINTS:
        idx = rng.choice(len(X_eval), N_GRAD_POINTS, replace=False)
        X_eval = X_eval[idx]

    logger.info(f"[{model_id}] 梯度评估点: {len(X_eval)}")

    grad_df = check_gradient_signs(
        model, sx, sy, device,
        idx_pairs=PHYSICS_IDX_PAIRS_HIGH,
        X_eval=X_eval,
    )
    grad_csv = os.path.join(out_dir, "gradient_sign_check.csv")
    grad_df.to_csv(grad_csv, index=False)

    compare_df = compare_with_data_direction(model_id, grad_df, train_df)
    compare_csv = os.path.join(out_dir, "physics_vs_data_direction.csv")
    compare_df.to_csv(compare_csv, index=False)

    n_pairs   = len(grad_df)
    n_correct = int(grad_df["is_consistent"].sum())
    phy_data_agree = int(compare_df["phy_data_agree"].sum()) if len(compare_df) else 0
    summary = {
        "model_id":              model_id,
        "n_physics_pairs":       n_pairs,
        "n_gradient_correct":    n_correct,
        "frac_gradient_correct": float(n_correct / max(n_pairs, 1)),
        "n_phy_data_agree":      phy_data_agree,
        "frac_phy_data_agree":   float(phy_data_agree / max(len(compare_df), 1)),
        "eval_points":           len(X_eval),
        "inference_method":      "mean_weights_deterministic",
    }
    summary_path = os.path.join(out_dir, "gradient_sign_summary.json")
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)

    logger.info(
        f"[{model_id}] 梯度方向正确率: {summary['frac_gradient_correct']:.1%} "
        f"({n_correct}/{n_pairs})"
    )
    logger.info(
        f"[{model_id}] 物理-数据方向一致率: {summary['frac_phy_data_agree']:.1%}"
    )

    mf = make_experiment_manifest(
        experiment_id="physics_consistency",
        model_id=model_id,
        input_source=FIXED_SPLIT_DIR,
        outputs_saved=[grad_csv, compare_csv, summary_path],
        key_results=summary,
        source_script=__file__,
        extra={
            "n_physics_pairs_high": len(PHYSICS_IDX_PAIRS_HIGH),
            "eval_points":          len(X_eval),
            "bnn_forward_mode":     "sample=False (mean weights)",
        },
    )
    write_manifest(os.path.join(out_dir, "physics_consistency_manifest.json"), mf)
    return summary


# ────────────────────────────────────────────────────────────
# 跨模型对比
# ────────────────────────────────────────────────────────────
def make_cross_model_comparison(summaries: list, base_dir: str):
    df = pd.DataFrame(summaries)
    out = os.path.join(base_dir, "cross_model_comparison.csv")
    df.to_csv(out, index=False)
    logger.info(f"[compare] 跨模型对比 → {out}")
    return df


# ────────────────────────────────────────────────────────────
# 入口
# ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    MODEL_ID_OVERRIDE = "bnn-phy-mono"
    model_id = os.environ.get("MODEL_ID", MODEL_ID_OVERRIDE)

    base_exp_dir = experiment_dir("physics_consistency")
    ensure_dir(base_exp_dir)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    fh = logging.FileHandler(os.path.join(base_exp_dir, f"consistency_{ts}.log"))
    fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(fh)

    if model_id == "all":
        summaries = []
        for mid in MODELS:
            try:
                _resolve_artifacts(mid)
            except FileNotFoundError:
                logger.warning(f"[{mid}] checkpoint 不存在，跳过")
                continue
            out_dir = resolve_output_dir(
                os.path.join(base_exp_dir, mid),
                script_name=os.path.basename(__file__),
            )
            s = run_physics_consistency_one(mid, out_dir)
            summaries.append(s)
        if summaries:
            make_cross_model_comparison(summaries, base_exp_dir)
    else:
        if model_id not in MODELS:
            raise ValueError(f"未知 MODEL_ID: {model_id}。可选: {list(MODELS.keys())}")
        out_dir = resolve_output_dir(
            os.path.join(base_exp_dir, model_id),
            script_name=os.path.basename(__file__),
        )
        run_physics_consistency_one(model_id, out_dir)
