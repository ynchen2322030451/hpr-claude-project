# run_data_efficiency_0404.py
# ============================================================
# BNN 0414 — Data efficiency curve  NCS revision P1-#8
#
# 目的：
#   审稿人通常问："你们的 BNN 需要多大训练集才稳定？再给 2 倍/一半数据会怎样？"
#   本脚本在固定 hyperparameters（来自 canonical training_manifest.json 的 best_params）
#   下，对 TRAIN_FRACS 中每个 fraction 随机子采 train set 重训，
#   评估 frozen test split，产出 RMSE/NLL/CRPS vs N_train 曲线 + 多 seed CI。
#
# 关键设计：
#   - 不重做 Optuna（那样会引入额外方差）
#   - 直接用 canonical best_params + 重训 final_train
#   - 子采样在 FIXED_SPLIT 的 train_indices 上做，val/test 不变
#   - 默认只跑 bnn-baseline & bnn-phy-mono（paper 核心对比）
#
# 运行成本：fraction 数 × seed 数 × 模型数 ≈ 4 × 2 × 2 = 16 次 training
#
# 调用（服务器）：
#   MODEL_ID=bnn-phy-mono python run_data_efficiency_0404.py
#   MODEL_ID=all        python run_data_efficiency_0404.py
#
# 输出 (experiments_0404/experiments/data_efficiency/)：
#   data_efficiency_<model>.csv     — 每 frac × seed 行，含 RMSE / NLL / R2
#   data_efficiency_summary.csv
#   data_efficiency_curve.png
#   data_efficiency_manifest.json
# ============================================================

import os, sys, json, time, pickle, logging
from datetime import datetime

import numpy as np
import pandas as pd

# ── sys.path ────────────────────────────────────────────────
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_CODE_ROOT = _SCRIPT_DIR
while _CODE_ROOT and os.path.basename(_CODE_ROOT) != 'code':
    _CODE_ROOT = os.path.dirname(_CODE_ROOT)
_BNN_CONFIG_DIR = os.path.join(_CODE_ROOT, 'experiments_0404', 'config')
_CODE_TOP = os.path.dirname(os.path.dirname(_CODE_ROOT))
_ROOT_0310 = os.path.join(_CODE_TOP, '0310')
_TRAINING_DIR = os.path.join(_CODE_ROOT, 'experiments_0404', 'training')
for _p in (_SCRIPT_DIR, _CODE_ROOT, _BNN_CONFIG_DIR, _TRAINING_DIR, _ROOT_0310,
           os.environ.get('HPR_LEGACY_DIR', '')):
    if _p and os.path.isdir(_p) and _p not in sys.path:
        if any(seg in _p for seg in ('/0310', 'hpr_legacy')):
            sys.path.append(_p)
        else:
            sys.path.insert(0, _p)

from experiment_config_0404 import (
    INPUT_COLS, OUTPUT_COLS, FIXED_SPLIT_DIR, SEED, DEVICE, BNN_N_MC_EVAL,
    EXPR_ROOT_0404, experiment_dir, ensure_dir,
)
from model_registry_0404 import MODELS
from manifest_utils_0404 import make_experiment_manifest, write_manifest

MODEL_PAPER_LABEL = {
    "bnn-baseline":       "Reference surrogate",
    "bnn-data-mono":      "Data-monotone BNN",
    "bnn-phy-mono":       "Physics-regularized BNN",
    "bnn-data-mono-ineq": "Data+inequality BNN",
}

from bnn_model import seed_all, get_device, mc_predict

# 复用 canonical 的 final_train / load_fixed_split / evaluate_on_test
import run_train_0404 as rt
import torch
from sklearn.preprocessing import StandardScaler

logging.basicConfig(level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger(__name__)

# ============================================================
# 配置
# ============================================================
TRAIN_FRACS = [float(x) for x in os.environ.get(
    "TRAIN_FRACS", "0.25,0.5,0.75,1.0").split(",")]
DE_SEEDS = [int(x) for x in os.environ.get(
    "DE_SEEDS", "2026,2027").split(",")]
# 只跑核心对比（除非用户 override）
DEFAULT_MODEL_SET = os.environ.get("DE_MODEL_SET", "core")  # core | all
MODEL_SET_MAP = {
    "core": ["bnn-baseline", "bnn-phy-mono"],
    "all":  list(MODELS.keys()),
}


def _load_best_params(model_id: str) -> dict:
    """从 canonical training_manifest_fixed.json 拿 best_params。"""
    mf_path = os.path.join(
        EXPR_ROOT_0404, "models", model_id, "manifests",
        f"training_manifest_{model_id}_fixed.json",
    )
    # 如果 EXPR_ROOT_0404 不是 code/，兜底用 _CODE_ROOT
    if not os.path.exists(mf_path):
        mf_path = os.path.join(
            _CODE_ROOT, "models", model_id, "manifests",
            f"training_manifest_{model_id}_fixed.json",
        )
    if not os.path.exists(mf_path):
        raise FileNotFoundError(f"training_manifest not found: {mf_path}")
    with open(mf_path) as f:
        mf = json.load(f)
    return mf["best_params"]


def _dataset_csv_or_fixed_split():
    """加载 full_df 供 load_fixed_split 使用。
    优先从 fixed_split CSVs 拼接（保证无 NaN），
    仅在 fixed_split 不存在时才 fallback 到 get_csv_path()。"""
    dfs = []
    for k in ("train", "val", "test"):
        p = os.path.join(FIXED_SPLIT_DIR, f"{k}.csv")
        if os.path.exists(p):
            dfs.append(pd.read_csv(p))
    if dfs:
        return pd.concat(dfs, ignore_index=True)
    csv_path = rt.get_csv_path()
    if csv_path and os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        df = df.dropna(subset=OUTPUT_COLS)
        return df
    raise FileNotFoundError("无法加载数据集（fixed_split CSV 或 get_csv_path()）")


def _subsample_train(X_tr, Y_tr, frac, seed):
    """按 frac 随机 down-sample train set。seed 控制可复现。"""
    n = len(X_tr)
    n_keep = max(16, int(round(n * frac)))
    rng = np.random.RandomState(seed)
    idx = rng.choice(n, size=n_keep, replace=False)
    return X_tr[idx], Y_tr[idx], idx


def _evaluate(model, sx, sy, X_test, Y_test, device):
    mu_mean, _, aleatoric_var, epistemic_var, total_var = mc_predict(
        model, X_test, sx, sy, device, n_mc=BNN_N_MC_EVAL)
    sigma = np.sqrt(total_var)
    rmse = float(np.sqrt(np.mean((mu_mean - Y_test) ** 2)))
    rmse_per_out = np.sqrt(np.mean((mu_mean - Y_test) ** 2, axis=0))
    # Gaussian NLL (per point, averaged)
    var = np.maximum(total_var, 1e-12)
    nll = 0.5 * ((Y_test - mu_mean) ** 2 / var + np.log(2 * np.pi * var))
    nll_mean = float(nll.mean())
    # R2 per output
    ss_res = np.sum((Y_test - mu_mean) ** 2, axis=0)
    ss_tot = np.sum((Y_test - Y_test.mean(axis=0)) ** 2, axis=0) + 1e-12
    r2_per_out = 1.0 - ss_res / ss_tot
    return {
        "rmse_mean": rmse,
        "rmse_per_out": rmse_per_out.tolist(),
        "nll_mean": nll_mean,
        "r2_mean": float(r2_per_out.mean()),
        "r2_per_out": r2_per_out.tolist(),
    }


def run_for_model(model_id: str):
    logger.info(f"[{model_id}] data efficiency: fracs={TRAIN_FRACS}, seeds={DE_SEEDS}")
    best_params = _load_best_params(model_id)
    logger.info(f"  best_params loaded (epochs={best_params.get('epochs')}, "
                f"width={best_params.get('width')})")

    device = get_device(DEVICE)

    # 完整 split
    full_df = _dataset_csv_or_fixed_split()
    X_tr, Y_tr, X_val, Y_val, X_test, Y_test, s_seed = rt.load_fixed_split(
        full_df, logger)
    logger.info(f"  canonical split: train={len(X_tr)} val={len(X_val)} test={len(X_test)}")

    out_dir = ensure_dir(os.path.join(_CODE_ROOT, "..", "results", "data_efficiency"))
    out_dir = os.path.abspath(out_dir)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    fh = logging.FileHandler(os.path.join(out_dir, f"data_eff_{model_id}_{ts}.log"))
    fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(fh)

    rows = []
    for frac in TRAIN_FRACS:
        for sd in DE_SEEDS:
            seed_all(sd)
            X_sub, Y_sub, idx = _subsample_train(X_tr, Y_tr, frac, sd)

            sx = StandardScaler().fit(X_sub)
            sy_ = StandardScaler().fit(Y_sub)
            scalers = {"sx": sx, "sy_": sy_}

            t0 = time.time()
            model, best_val, history = rt.final_train(
                model_id, best_params,
                X_sub, Y_sub, X_val, Y_val,
                device, scalers, logger,
            )
            t_train = time.time() - t0

            metrics = _evaluate(model, sx, sy_, X_test, Y_test, device)
            metrics.update({
                "model_id": model_id,
                "train_frac": frac,
                "n_train": len(X_sub),
                "seed": sd,
                "train_time_sec": t_train,
                "val_rmse_best": best_val,
            })
            rows.append(metrics)
            logger.info(f"  frac={frac:.2f} seed={sd} n={len(X_sub)} "
                        f"RMSE={metrics['rmse_mean']:.4f} NLL={metrics['nll_mean']:.4f} "
                        f"R2={metrics['r2_mean']:.4f} ({t_train:.0f}s)")

            # free GPU
            del model
            if hasattr(torch.cuda, "empty_cache"):
                try:
                    torch.cuda.empty_cache()
                except Exception:
                    pass

    df = pd.DataFrame(rows)
    csv_out = os.path.join(out_dir, f"data_efficiency_{model_id}.csv")
    df.drop(columns=["rmse_per_out", "r2_per_out"]).to_csv(csv_out, index=False)
    logger.info(f"[{model_id}] 写入 {csv_out} ({len(df)} 行)")

    logger.removeHandler(fh)
    return df


def _aggregate_and_plot(all_df, out_dir):
    # summary: per model × per frac — mean ± std (over seeds)
    agg = all_df.groupby(["model_id", "train_frac"]).agg(
        n_train_mean=("n_train", "mean"),
        rmse_mean=("rmse_mean", "mean"),
        rmse_std=("rmse_mean", "std"),
        nll_mean=("nll_mean", "mean"),
        nll_std=("nll_mean", "std"),
        r2_mean=("r2_mean", "mean"),
        r2_std=("r2_mean", "std"),
        n_seeds=("seed", "nunique"),
    ).reset_index()
    agg.to_csv(os.path.join(out_dir, "data_efficiency_summary.csv"), index=False)
    logger.info(f"summary 写入 ({len(agg)} 行)")

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, axes = plt.subplots(1, 3, figsize=(12, 3.8))
        models = agg["model_id"].unique().tolist()
        colors = {m: c for m, c in zip(models,
                  ["#4477aa", "#cc6677", "#117733", "#882255"])}
        for metric, ax, ylabel in [
            ("rmse", axes[0], "Test RMSE (orig scale)"),
            ("nll",  axes[1], "Test NLL"),
            ("r2",   axes[2], r"Test $R^2$"),
        ]:
            for m in models:
                sub = agg[agg["model_id"] == m].sort_values("train_frac")
                y = sub[f"{metric}_mean"]
                yerr = sub[f"{metric}_std"].fillna(0.0)
                ax.errorbar(sub["n_train_mean"], y, yerr=yerr,
                            marker="o", capsize=3, label=MODEL_PAPER_LABEL.get(m, m), color=colors.get(m))
            ax.set_xlabel("N_train")
            ax.set_ylabel(ylabel)
            ax.set_xscale("log")
            ax.grid(True, which="both", alpha=0.3)
            ax.legend(fontsize=8)
        fig.suptitle("Data efficiency (surrogate test metrics vs N_train)",
                     fontsize=11)
        fig.tight_layout()
        fig.savefig(os.path.join(out_dir, "data_efficiency_curve.png"), dpi=150)
        plt.close(fig)
    except Exception as e:
        logger.warning(f"绘图失败 (non-fatal): {e}")

    return agg


if __name__ == "__main__":
    model_id_env = os.environ.get("MODEL_ID", "")
    if model_id_env and model_id_env != "all":
        model_ids = [model_id_env]
    else:
        model_ids = MODEL_SET_MAP.get(DEFAULT_MODEL_SET, MODEL_SET_MAP["core"])
        if model_id_env == "all":
            model_ids = list(MODELS.keys())

    out_dir = ensure_dir(os.path.join(_CODE_ROOT, "..", "results", "data_efficiency"))
    out_dir = os.path.abspath(out_dir)

    all_rows = []
    for mid in model_ids:
        if mid not in MODELS:
            logger.error(f"unknown MODEL_ID: {mid}")
            continue
        logger.info("=" * 60)
        logger.info(f"DATA EFFICIENCY — {mid}")
        logger.info("=" * 60)
        try:
            df_m = run_for_model(mid)
            all_rows.append(df_m)
        except Exception as e:
            logger.exception(f"[{mid}] failed: {e}")

    if all_rows:
        all_df = pd.concat(all_rows, ignore_index=True)
        all_df.drop(columns=["rmse_per_out", "r2_per_out"], errors="ignore").to_csv(
            os.path.join(out_dir, "data_efficiency_all.csv"), index=False)
        agg = _aggregate_and_plot(all_df, out_dir)

        mf = make_experiment_manifest(
            experiment_id="data_efficiency",
            model_id="multi",
            input_source=FIXED_SPLIT_DIR,
            outputs_saved=[
                os.path.join(out_dir, "data_efficiency_all.csv"),
                os.path.join(out_dir, "data_efficiency_summary.csv"),
                os.path.join(out_dir, "data_efficiency_curve.png"),
            ],
            key_results={
                "model_ids": sorted(all_df["model_id"].unique().tolist()),
                "train_fracs": TRAIN_FRACS,
                "seeds": DE_SEEDS,
                "min_rmse": float(agg["rmse_mean"].min()),
                "max_rmse": float(agg["rmse_mean"].max()),
            },
            source_script=os.path.abspath(__file__),
            extra={
                "note": "Fixed hyperparameters from canonical training_manifest; "
                        "no Optuna re-tuning per frac.",
            },
        )
        write_manifest(os.path.join(out_dir, "data_efficiency_manifest.json"), mf)
    logger.info("DATA EFFICIENCY DONE")
