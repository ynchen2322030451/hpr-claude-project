# run_eval_0404.py
# ============================================================
# 0404 统一评估脚本
#
# 支持:
#   1) fixed split 评估（主文指标，使用冻结测试集）
#   2) repeated split 评估（稳定性检验，seeds 2026-2030）
#
# 由 run_0404.py 通过环境变量调用:
#   MODEL_ID=baseline  EVAL_MODE=fixed  python run_eval_0404.py
#   MODEL_ID=data-mono EVAL_MODE=repeat python run_eval_0404.py
#
# 也可直接修改底部 __main__ 的覆盖变量后运行。
#
# 输出:
#   experiments_0404/models/<model_id>/fixed_eval/
#     metrics_fixed.json
#     metrics_per_output_fixed.csv
#     test_predictions_fixed.json
#     eval_manifest_fixed.json
#
#   experiments_0404/models/<model_id>/repeat_eval/
#     seed_<S>/metrics.json
#     repeat_summary.json
#     repeat_summary.csv
#     eval_manifest_repeat.json
# ============================================================

import os, sys, json, pickle, logging
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd
import torch
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Resolve code roots: add config/ and legacy code/0310/ to path
_CODE_ROOT = _SCRIPT_DIR
while _CODE_ROOT and not os.path.basename(_CODE_ROOT) == 'code':
    _CODE_ROOT = os.path.dirname(_CODE_ROOT)
for _p in (_SCRIPT_DIR,
           os.path.join(_CODE_ROOT, 'config'),
           os.path.dirname(_CODE_ROOT),        # experiments_0404/
           os.path.dirname(os.path.dirname(_CODE_ROOT)),  # code/0310/
           os.environ.get('HPR_LEGACY_DIR', '')):
    if _p and os.path.isdir(_p) and _p not in sys.path:
        sys.path.insert(0, _p)
del _CODE_ROOT, _p

from experiment_config_0404 import (
    INPUT_COLS, OUTPUT_COLS, PRIMARY_OUTPUTS,
    SEED, REPEAT_SEEDS,
    FIXED_SPLIT_DIR, EXPR_ROOT_OLD,
    TEST_FRAC, VAL_FRAC,
    model_artifacts_dir, model_fixed_eval_dir,
    model_repeat_eval_dir, model_manifests_dir,
    model_logs_dir, ensure_dir,
    get_csv_path, DEVICE,
)
from model_registry_0404 import MODELS
from manifest_utils_0404 import write_manifest, make_eval_manifest
from run_phys_levels_main import (
    HeteroMLP, gaussian_nll, seed_all, get_device,
    compute_basic_metrics, compute_prob_metrics_gaussian, _to_numpy,
)

# ────────────────────────────────────────────────────────────
# 日志设置
# ────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


# ────────────────────────────────────────────────────────────
# 旧 checkpoint 目录映射（baseline/data-mono 复用旧产出）
# ────────────────────────────────────────────────────────────
_OLD_ARTIFACTS = {
    "baseline": {
        "ckpt":   os.path.join(EXPR_ROOT_OLD, "fixed_surrogate_fixed_base",  "checkpoint_level0.pt"),
        "scaler": os.path.join(EXPR_ROOT_OLD, "fixed_surrogate_fixed_base",  "scalers_level0.pkl"),
    },
    "data-mono": {
        "ckpt":   os.path.join(EXPR_ROOT_OLD, "fixed_surrogate_fixed_level2","checkpoint_level2.pt"),
        "scaler": os.path.join(EXPR_ROOT_OLD, "fixed_surrogate_fixed_level2","scalers_level2.pkl"),
    },
}


# ────────────────────────────────────────────────────────────
# 工具函数
# ────────────────────────────────────────────────────────────
def _setup_logger(log_path: str):
    fh = logging.FileHandler(log_path, mode="a", encoding="utf-8")
    fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(fh)


def _resolve_artifacts(model_id: str):
    """返回 (ckpt_path, scaler_path)，优先用新目录，不存在时回退到旧目录。"""
    new_dir = model_artifacts_dir(model_id)
    ckpt_new   = os.path.join(new_dir, f"checkpoint_{model_id}_fixed.pt")
    scaler_new  = os.path.join(new_dir, f"scalers_{model_id}_fixed.pkl")

    if os.path.exists(ckpt_new) and os.path.exists(scaler_new):
        return ckpt_new, scaler_new

    if model_id in _OLD_ARTIFACTS:
        old = _OLD_ARTIFACTS[model_id]
        if os.path.exists(old["ckpt"]) and os.path.exists(old["scaler"]):
            logger.info(f"[{model_id}] 使用旧目录 checkpoint: {old['ckpt']}")
            return old["ckpt"], old["scaler"]

    raise FileNotFoundError(
        f"[{model_id}] 找不到 checkpoint。"
        f" 期望: {ckpt_new} 或 {_OLD_ARTIFACTS.get(model_id, {}).get('ckpt', 'N/A')}"
    )


def _load_model(ckpt_path: str, device) -> HeteroMLP:
    state = torch.load(ckpt_path, map_location=device)
    bp = state["best_params"]
    model = HeteroMLP(
        in_dim=len(INPUT_COLS),
        out_dim=len(OUTPUT_COLS),
        width=int(bp["width"]),
        depth=int(bp["depth"]),
        dropout=float(bp.get("dropout", 0.0)),
    ).to(device)
    model.load_state_dict(state["model_state_dict"])
    model.eval()
    return model


def _load_scalers(scaler_path: str):
    with open(scaler_path, "rb") as f:
        return pickle.load(f)


def _load_fixed_split() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """从冻结 split CSV 读取 train/val/test。"""
    train_df = pd.read_csv(os.path.join(FIXED_SPLIT_DIR, "train.csv"))
    val_df   = pd.read_csv(os.path.join(FIXED_SPLIT_DIR, "val.csv"))
    test_df  = pd.read_csv(os.path.join(FIXED_SPLIT_DIR, "test.csv"))
    return train_df, val_df, test_df


def _make_random_split(df: pd.DataFrame, seed: int):
    """按给定 seed 做随机 train/val/test 划分，不覆盖冻结 split。"""
    train_val, test = train_test_split(df, test_size=TEST_FRAC, random_state=seed)
    train, val = train_test_split(train_val, test_size=VAL_FRAC, random_state=seed)
    return train, val, test


def _predict(model, X_np: np.ndarray, sx: StandardScaler, sy: StandardScaler, device):
    """
    返回 mu_orig, sigma_orig（原始量纲）
    """
    X_scaled = sx.transform(X_np)
    X_t = torch.tensor(X_scaled, dtype=torch.float32, device=device)
    with torch.no_grad():
        mu_s_t, logvar_s_t = model(X_t)
    mu_s     = mu_s_t.cpu().numpy()
    logvar_s = logvar_s_t.cpu().numpy()

    # 反标准化 mu
    mu_orig = sy.inverse_transform(mu_s)
    # 反标准化 sigma（标准化空间的 std * 原始 std）
    sigma_s = np.exp(0.5 * logvar_s)
    sigma_orig = sigma_s * sy.scale_

    return mu_orig, sigma_orig


def _compute_all_metrics(y_true: np.ndarray, mu: np.ndarray, sigma: np.ndarray) -> dict:
    basic = compute_basic_metrics(y_true, mu)         # MAE, RMSE, R2 (per-output)
    prob  = compute_prob_metrics_gaussian(y_true, mu, sigma)  # PICP, MPIW, CRPS (per-output)
    return {**basic, **prob}


def _metrics_to_records(metrics: dict, output_cols: list[str]) -> list[dict]:
    """将 per-output 向量 metrics 转成行记录列表，供 DataFrame / JSON 用。"""
    records = []
    n = len(output_cols)
    for j, col in enumerate(output_cols):
        row = {"output": col}
        for k, v in metrics.items():
            if hasattr(v, "__len__") and len(v) == n:
                row[k] = float(v[j])
        records.append(row)
    return records


def _metrics_overall(metrics: dict) -> dict:
    """对所有 per-output 指标取均值，得到 overall 标量汇总。"""
    out = {}
    for k, v in metrics.items():
        if hasattr(v, "__len__"):
            out[k + "_mean"] = float(np.mean(v))
        else:
            out[k] = float(v)
    return out


# ────────────────────────────────────────────────────────────
# 主评估函数
# ────────────────────────────────────────────────────────────
def eval_fixed(model_id: str, force: bool = False):
    """在冻结 fixed split 测试集上评估模型，输出到 fixed_eval/。"""
    out_dir = ensure_dir(model_fixed_eval_dir(model_id))
    manifest_path = os.path.join(out_dir, "eval_manifest_fixed.json")

    if not force and os.path.exists(manifest_path):
        logger.info(f"[{model_id}] fixed_eval 已存在，跳过（force=False）")
        return

    log_dir = ensure_dir(model_logs_dir(model_id))
    _setup_logger(os.path.join(log_dir, f"eval_fixed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"))

    logger.info(f"[{model_id}] === 开始 fixed split 评估 ===")

    # 加载模型和 scaler
    ckpt_path, scaler_path = _resolve_artifacts(model_id)
    device = get_device()
    model   = _load_model(ckpt_path, device)
    scalers = _load_scalers(scaler_path)
    sx: StandardScaler = scalers["sx"]
    sy: StandardScaler = scalers["sy"]

    # 加载测试集
    _, _, test_df = _load_fixed_split()
    X_test = test_df[INPUT_COLS].values
    Y_test = test_df[OUTPUT_COLS].values
    n_test = len(test_df)
    logger.info(f"[{model_id}] test size = {n_test}")

    # 预测
    mu, sigma = _predict(model, X_test, sx, sy, device)

    # 指标
    metrics = _compute_all_metrics(Y_test, mu, sigma)
    overall = _metrics_overall(metrics)
    per_output = _metrics_to_records(metrics, OUTPUT_COLS)

    # 保存 predictions JSON（mu + sigma，每个样本）
    pred_path = os.path.join(out_dir, "test_predictions_fixed.json")
    pred_dict = {
        "output_cols": OUTPUT_COLS,
        "n_test":      n_test,
        "mu":          mu.tolist(),
        "sigma":       sigma.tolist(),
        "y_true":      Y_test.tolist(),
    }
    with open(pred_path, "w") as f:
        json.dump(pred_dict, f)
    logger.info(f"[{model_id}] predictions saved → {pred_path}")

    # 保存 per-output CSV
    per_out_path = os.path.join(out_dir, "metrics_per_output_fixed.csv")
    pd.DataFrame(per_output).to_csv(per_out_path, index=False)

    # 保存 overall JSON
    overall_path = os.path.join(out_dir, "metrics_fixed.json")
    with open(overall_path, "w") as f:
        json.dump(overall, f, indent=2)

    logger.info(f"[{model_id}] overall metrics: {overall}")

    # 写 manifest
    m = make_eval_manifest(
        model_id    = model_id,
        split_type  = "fixed",
        split_seed  = SEED,
        metrics_overall   = overall,
        metrics_per_output= per_output,
        ckpt_path   = ckpt_path,
        scaler_path = scaler_path,
        source_script = __file__,
        extra = {
            "n_test":     n_test,
            "output_cols": OUTPUT_COLS,
            "pred_path":   pred_path,
        },
    )
    mf_dir = ensure_dir(model_manifests_dir(model_id))
    write_manifest(os.path.join(mf_dir, "eval_manifest_fixed.json"), m)
    write_manifest(manifest_path, m)
    logger.info(f"[{model_id}] fixed_eval 完成")


def eval_repeat(model_id: str, force: bool = False):
    """
    对 5 个重复随机 split 分别评估，输出到 repeat_eval/。
    不重跑 Optuna，复用 fixed split 最优超参（fixed_eval 须已存在）。
    """
    base_out = ensure_dir(model_repeat_eval_dir(model_id))
    summary_path = os.path.join(base_out, "repeat_summary.json")

    if not force and os.path.exists(summary_path):
        logger.info(f"[{model_id}] repeat_eval 已存在，跳过（force=False）")
        return

    log_dir = ensure_dir(model_logs_dir(model_id))
    _setup_logger(os.path.join(log_dir, f"eval_repeat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"))

    logger.info(f"[{model_id}] === 开始 repeat split 评估 ({len(REPEAT_SEEDS)} seeds) ===")

    # 加载模型和 scaler（使用 fixed split 训练的模型，固定超参）
    ckpt_path, scaler_path = _resolve_artifacts(model_id)
    device = get_device()
    model   = _load_model(ckpt_path, device)
    scalers = _load_scalers(scaler_path)
    sx: StandardScaler = scalers["sx"]
    sy: StandardScaler = scalers["sy"]

    # 需要完整数据集来做 repeat split
    csv_path = get_csv_path()
    if csv_path is None:
        logger.error(
            "repeat_eval 需要完整 CSV 数据集，但 get_csv_path() 返回 None。"
            " 请在服务器上运行，或设置 CSV_PATH_LOCAL。"
        )
        return

    df_full = pd.read_csv(csv_path)
    logger.info(f"[{model_id}] 全量数据集: {len(df_full)} 行")

    all_seed_results = []

    for seed in REPEAT_SEEDS:
        seed_all(seed)
        seed_dir = ensure_dir(os.path.join(base_out, f"seed_{seed}"))

        logger.info(f"[{model_id}] seed={seed} 划分 + 评估")
        _, _, test_df = _make_random_split(df_full, seed)

        X_test = test_df[INPUT_COLS].values
        Y_test = test_df[OUTPUT_COLS].values
        n_test = len(test_df)

        mu, sigma = _predict(model, X_test, sx, sy, device)
        metrics   = _compute_all_metrics(Y_test, mu, sigma)
        overall   = _metrics_overall(metrics)
        per_output= _metrics_to_records(metrics, OUTPUT_COLS)

        # 保存单 seed 结果
        with open(os.path.join(seed_dir, "metrics.json"), "w") as f:
            json.dump({"seed": seed, "n_test": n_test, **overall}, f, indent=2)
        pd.DataFrame(per_output).to_csv(
            os.path.join(seed_dir, "metrics_per_output.csv"), index=False
        )

        all_seed_results.append({"seed": seed, "n_test": n_test, **overall})
        logger.info(f"[{model_id}] seed={seed} → NLL_mean={overall.get('CRPS_mean', 'N/A'):.4f}")

    # 跨 seed 汇总（均值 ± 标准差）
    summary_df = pd.DataFrame(all_seed_results)
    numeric_cols = [c for c in summary_df.columns if c not in ("seed",)]
    summary_stats = {}
    for col in numeric_cols:
        vals = summary_df[col].values
        summary_stats[col] = {
            "mean":  float(np.mean(vals)),
            "std":   float(np.std(vals, ddof=1)),
            "min":   float(np.min(vals)),
            "max":   float(np.max(vals)),
        }

    summary_full = {
        "model_id":     model_id,
        "repeat_seeds": REPEAT_SEEDS,
        "n_repeats":    len(REPEAT_SEEDS),
        "per_seed":     all_seed_results,
        "summary":      summary_stats,
    }

    with open(summary_path, "w") as f:
        json.dump(summary_full, f, indent=2)
    summary_df.to_csv(os.path.join(base_out, "repeat_summary.csv"), index=False)

    logger.info(
        f"[{model_id}] repeat_eval 完成. "
        f"RMSE_mean: mean={summary_stats.get('RMSE_mean', {}).get('mean', 'N/A'):.4f}"
    )

    # manifest
    mf_dir = ensure_dir(model_manifests_dir(model_id))
    m = make_eval_manifest(
        model_id     = model_id,
        split_type   = "repeat",
        split_seed   = -1,   # 多个 seed，用 -1 表示
        metrics_overall   = summary_stats,
        metrics_per_output= [],
        ckpt_path    = ckpt_path,
        scaler_path  = scaler_path,
        source_script= __file__,
        extra = {
            "repeat_seeds": REPEAT_SEEDS,
            "n_repeats":    len(REPEAT_SEEDS),
            "summary_path": summary_path,
        },
    )
    write_manifest(os.path.join(mf_dir, "eval_manifest_repeat.json"), m)


# ────────────────────────────────────────────────────────────
# 对比汇总：多个模型 fixed_eval 结果合并为一个 comparison CSV
# ────────────────────────────────────────────────────────────
def make_comparison_table(model_ids: list[str], out_path: str):
    """
    从各模型的 metrics_fixed.json 汇总成一张比较表。
    只汇总已完成的 fixed_eval。
    """
    from experiment_config_0404 import model_fixed_eval_dir

    rows = []
    for mid in model_ids:
        mpath = os.path.join(model_fixed_eval_dir(mid), "metrics_fixed.json")
        if not os.path.exists(mpath):
            logger.warning(f"[compare] {mid} 无 fixed_eval metrics，跳过")
            continue
        with open(mpath) as f:
            d = json.load(f)
        d["model_id"] = mid
        rows.append(d)

    if not rows:
        logger.warning("[compare] 无可汇总结果")
        return

    df = pd.DataFrame(rows)
    # 把 model_id 放第一列
    cols = ["model_id"] + [c for c in df.columns if c != "model_id"]
    df = df[cols]
    df.to_csv(out_path, index=False)
    logger.info(f"[compare] 对比表 → {out_path}")
    return df


# ────────────────────────────────────────────────────────────
# 入口
# ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # 由 run_0404.py 通过环境变量传入；或直接修改下方覆盖值
    MODEL_ID_OVERRIDE = "baseline"   # 直接运行时修改这里
    EVAL_MODE_OVERRIDE = "fixed"     # "fixed" | "repeat" | "both" | "compare"

    model_id  = os.environ.get("MODEL_ID",   MODEL_ID_OVERRIDE)
    eval_mode = os.environ.get("EVAL_MODE",  EVAL_MODE_OVERRIDE)
    force     = os.environ.get("EVAL_FORCE", "0") == "1"

    if model_id not in MODELS:
        raise ValueError(f"未知 MODEL_ID: {model_id}。可选: {list(MODELS.keys())}")

    logger.info(f"eval_0404 | model={model_id} | mode={eval_mode} | force={force}")

    if eval_mode in ("fixed", "both"):
        eval_fixed(model_id, force=force)

    if eval_mode in ("repeat", "both"):
        eval_repeat(model_id, force=force)

    if eval_mode == "compare":
        from experiment_config_0404 import EXPR_ROOT_0404
        # 对比所有已评估的模型
        all_ids = list(MODELS.keys())
        out_csv = os.path.join(EXPR_ROOT_0404, "comparison_fixed_eval.csv")
        make_comparison_table(all_ids, out_csv)
