# run_posterior_predictive_check_0404.py
# ============================================================
# BNN 0414 — Posterior Predictive Check (PPC)  NCS revision P1-#6
#
# 目的：
#   canonical run_posterior_0404.py 只存 θ 的后验统计量，不存
#   posterior-predictive of observables y。审稿人会要求直接检验
#   p(y_obs | D) 的后验预测分布是否覆盖真值/观测。
#
# 本脚本消费 run_posterior_diagnostics_0404.py 产出的 chain .npz
# （位于 experiments_0404/experiments/posterior/<model>/diagnostics/chains/），
# 从每个 chain 中随机抽 M draws，forward 经 surrogate，形成 y 的后验
# 预测样本，然后：
#   - 计算 y 的 posterior-predictive mean / std / 90% CI
#   - 检查 y_obs_noisy 是否落入 90% CI（case-level coverage）
#   - 计算 PIT_y = P(Y_pred <= y_obs) 在各输出上
#   - 输出 posterior-predictive RMSE = |mean(Y_pred) - y_true|
#
# 需要 torch → 服务器端运行（与 #3/#4 相同部署方式）。
#
# 调用：
#   MODEL_ID=bnn-phy-mono python run_posterior_predictive_check_0404.py
#   MODEL_ID=all        python run_posterior_predictive_check_0404.py
#
# 输出 (experiments_0404/experiments/posterior/<model>/ppc/)：
#   ppc_per_case.csv      — case × output 的 pred_mean/std/p5/p95 + y_obs + in_90ci + PIT
#   ppc_summary.csv       — 每模型跨 case 的 coverage_90 / PIT KS / RMSE
#   pit_y_<model>.png     — PIT 直方图 per output
#   ppc_coverage_<model>.png — 覆盖率柱状图
#   ppc_manifest.json
# ============================================================

import os, sys, json, glob, logging
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
for _p in (_SCRIPT_DIR, _CODE_ROOT, _BNN_CONFIG_DIR, _ROOT_0310,
           os.environ.get('HPR_LEGACY_DIR', '')):
    if _p and os.path.isdir(_p) and _p not in sys.path:
        if any(seg in _p for seg in ('/0310', 'hpr_legacy')):
            sys.path.append(_p)
        else:
            sys.path.insert(0, _p)

from experiment_config_0404 import (
    INPUT_COLS, OUTPUT_COLS, INVERSE_CALIB_PARAMS, PRIMARY_OUTPUTS,
    SEED, DEVICE, experiment_dir, ensure_dir,
)
from model_registry_0404 import MODELS
from manifest_utils_0404 import make_experiment_manifest, write_manifest

import run_posterior_0404 as rp
from bnn_model import get_device, seed_all, mc_predict

logging.basicConfig(level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger(__name__)

# ============================================================
# 配置
# ============================================================
PPC_N_DRAWS = int(os.environ.get("PPC_N_DRAWS", 500))  # 每 case 抽多少后验 θ 前向
PPC_N_MC    = int(os.environ.get("PPC_N_MC", 20))      # 每个 θ 的 BNN MC 采样数
ALPHA_CI    = 0.90

# paper-facing labels
OUTPUT_PAPER_LABEL = {
    "iteration2_max_global_stress": "Max. global stress",
    "iteration2_keff":              r"$k_{\mathrm{eff}}$",
    "iteration2_max_fuel_temp":     "Max. fuel temp.",
    "iteration2_max_monolith_temp": "Max. monolith temp.",
    "iteration2_wall2":             "Wall expansion",
}
MODEL_PAPER_LABEL = {
    "bnn-baseline":       "Reference surrogate",
    "bnn-data-mono":      "Data-monotone BNN",
    "bnn-phy-mono":       "Physics-regularized BNN",
    "bnn-data-mono-ineq": "Data+inequality BNN",
}


# ────────────────────────────────────────────────────────────
# PPC 核心：从 chain.npz + surrogate 生成 y_pred 样本
# ────────────────────────────────────────────────────────────
def _predict_theta(model, sx, sy, x_full, device, n_mc):
    """对单个 θ 返回一次 surrogate 预测（mu_raw, sigma_raw）全输出。"""
    mu_mean, _, aleatoric_var, epistemic_var, total_var = mc_predict(
        model, x_full.reshape(1, -1), sx, sy, device, n_mc=n_mc
    )
    return mu_mean.flatten(), np.sqrt(total_var).flatten()


def posterior_predictive_samples(
    chains: np.ndarray, x_true: np.ndarray,
    model, sx, sy, device, rng: np.random.RandomState,
    n_draws: int, n_mc: int,
):
    """
    chains: (n_chains, n_per_chain, n_params)
    返回 y_pred_samples: (n_draws, n_out)  — 每 draw 抽一次后验 θ，
                         forward 经 surrogate 取 (mu_hat)，再加一次
                         aleatoric+epistemic 扰动 sigma_hat * eps 模拟
                         predictive distribution。
    """
    n_chains, n_per, n_params = chains.shape
    total = n_chains * n_per
    pooled = chains.reshape(total, n_params)
    draw_idx = rng.choice(total, size=n_draws, replace=(n_draws > total))

    n_out = len(OUTPUT_COLS)
    y_samples = np.zeros((n_draws, n_out), float)

    for di, k in enumerate(draw_idx):
        theta = pooled[k]
        x_full = x_true.copy()
        for pi, c in enumerate(INVERSE_CALIB_PARAMS):
            x_full[INPUT_COLS.index(c)] = theta[pi]
        mu, sig = _predict_theta(model, sx, sy, x_full, device, n_mc)
        eps = rng.normal(0.0, 1.0, size=n_out)
        y_samples[di] = mu + sig * eps
    return y_samples


def pit_gaussian_like(y_obs: float, y_samples: np.ndarray) -> float:
    """用 ECDF(y_obs) 计算 PIT；避免 0/1 极值用 0.5/(N+1) 平滑。"""
    n = len(y_samples)
    rank = float(np.sum(y_samples <= y_obs))
    return (rank + 0.5) / (n + 1.0)


# ────────────────────────────────────────────────────────────
# 主流程
# ────────────────────────────────────────────────────────────
def run_ppc_for_model(model_id: str):
    chains_dir = os.path.join(experiment_dir("posterior"), model_id,
                              "diagnostics", "chains")
    npz_files = sorted(glob.glob(os.path.join(chains_dir, "case_*.npz")))
    if not npz_files:
        logger.error(f"[{model_id}] 缺 chain .npz；先跑 run_posterior_diagnostics_0404.py")
        return None

    logger.info(f"[{model_id}] 找到 {len(npz_files)} 个 chain 文件")

    device = get_device(DEVICE)
    seed_all(SEED)
    ckpt, scapath = rp._resolve_artifacts(model_id)
    model = rp._load_model(ckpt, device)
    scalers = rp._load_scalers(scapath)
    sx, sy = scalers["sx"], scalers["sy"]
    model.eval()

    out_dir = ensure_dir(os.path.join(experiment_dir("posterior"),
                                       model_id, "ppc"))

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    fh = logging.FileHandler(os.path.join(out_dir, f"ppc_{ts}.log"))
    fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(fh)

    obs_idx = [OUTPUT_COLS.index(c) for c in rp.OBS_COLS]

    per_case_rows = []
    pit_store = {c: [] for c in OUTPUT_COLS}  # 跨 case 聚合 PIT

    for ci, npz_path in enumerate(npz_files):
        z = np.load(npz_path, allow_pickle=True)
        chains = z["chains"]           # (n_chains, n_per, n_params)
        y_obs_noisy = z["y_obs_noisy"]  # (n_obs,)
        x_true = z["x_true"]           # (n_in,)
        # y_true (all OUTPUT_COLS) 要从 test.csv 恢复 — npz 没存
        row_idx = int(z["row_idx"])
        cat = str(z["category"])

        rng = np.random.RandomState(SEED + 2000 + ci)
        y_samples = posterior_predictive_samples(
            chains, x_true, model, sx, sy, device, rng,
            n_draws=PPC_N_DRAWS, n_mc=PPC_N_MC,
        )

        # 需要 y_true 全输出 → 从 fixed_split test.csv 拿
        if not hasattr(run_ppc_for_model, "_test_df"):
            from experiment_config_0404 import FIXED_SPLIT_DIR
            run_ppc_for_model._test_df = pd.read_csv(
                os.path.join(FIXED_SPLIT_DIR, "test.csv"))
        test_df = run_ppc_for_model._test_df
        y_true_all = test_df.iloc[row_idx][OUTPUT_COLS].values.astype(float)

        # 每输出：mean / std / p5 / p95 + PIT(y_true) + in_90ci
        for oi, col in enumerate(OUTPUT_COLS):
            y_pred_col = y_samples[:, oi]
            mu_pred = float(np.mean(y_pred_col))
            sd_pred = float(np.std(y_pred_col))
            p5 = float(np.percentile(y_pred_col, 5))
            p95 = float(np.percentile(y_pred_col, 95))
            y_true = float(y_true_all[oi])

            # 观测可用时用观测；否则用 y_true
            if col in rp.OBS_COLS:
                obs_loc = rp.OBS_COLS.index(col)
                y_obs_val = float(y_obs_noisy[obs_loc])
            else:
                y_obs_val = None

            pit_t = pit_gaussian_like(y_true, y_pred_col)
            pit_store[col].append(pit_t)

            per_case_rows.append({
                "case_idx": ci,
                "row_idx": row_idx,
                "category": cat,
                "output": col,
                "paper_label": OUTPUT_PAPER_LABEL.get(col, col),
                "is_observed": col in rp.OBS_COLS,
                "pred_mean": mu_pred,
                "pred_std": sd_pred,
                "pred_p5": p5,
                "pred_p95": p95,
                "y_true": y_true,
                "y_obs_noisy": y_obs_val,
                "pit_true": pit_t,
                "in_90ci_true": bool(p5 <= y_true <= p95),
                "in_90ci_obs": bool(y_obs_val is not None
                                    and p5 <= y_obs_val <= p95),
                "abs_error_mean": abs(mu_pred - y_true),
                "z_true": (y_true - mu_pred) / max(sd_pred, 1e-12),
            })

        logger.info(f"  case {ci+1}/{len(npz_files)}: done")

    df = pd.DataFrame(per_case_rows)
    df.to_csv(os.path.join(out_dir, "ppc_per_case.csv"), index=False)
    logger.info(f"[{model_id}] ppc_per_case.csv 写入 ({len(df)} 行)")

    # 跨 case 的聚合
    summary_rows = []
    for col in OUTPUT_COLS:
        sub = df[df["output"] == col]
        pits = np.array(pit_store[col])
        # KS against Uniform[0,1]
        from scipy.stats import kstest
        ks_stat, ks_p = kstest(pits, "uniform")
        summary_rows.append({
            "model_id": model_id,
            "output": col,
            "paper_label": OUTPUT_PAPER_LABEL.get(col, col),
            "n_cases": len(sub),
            "is_observed": col in rp.OBS_COLS,
            "coverage_90ci_true": float(sub["in_90ci_true"].mean()),
            "coverage_90ci_obs": float(sub["in_90ci_obs"].mean())
                if sub["y_obs_noisy"].notna().any() else np.nan,
            "RMSE_post_mean_vs_true": float(np.sqrt((sub["abs_error_mean"] ** 2).mean())),
            "mean_pred_std": float(sub["pred_std"].mean()),
            "pit_mean": float(pits.mean()),
            "pit_std": float(pits.std()),
            "pit_ks_stat": float(ks_stat),
            "pit_ks_pvalue": float(ks_p),
        })
    sdf = pd.DataFrame(summary_rows)
    sdf.to_csv(os.path.join(out_dir, "ppc_summary.csv"), index=False)
    logger.info(f"[{model_id}] ppc_summary.csv 写入 ({len(sdf)} 行)")

    # ── 图：PIT 直方图 per output ────────────────────────────
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        n_out = len(OUTPUT_COLS)
        cols = 3
        rows = int(np.ceil(n_out / cols))
        fig, axes = plt.subplots(rows, cols, figsize=(4 * cols, 3 * rows))
        axes = np.atleast_1d(axes).flatten()
        for oi, col in enumerate(OUTPUT_COLS):
            ax = axes[oi]
            ax.hist(pit_store[col], bins=10, range=(0, 1),
                    edgecolor="black", alpha=0.7)
            ax.axhline(len(pit_store[col]) / 10.0, color="red",
                       linestyle="--", lw=1, label="Uniform")
            ax.set_title(OUTPUT_PAPER_LABEL.get(col, col), fontsize=9)
            ax.set_xlabel("PIT")
            ax.set_ylabel("count")
            ax.legend(fontsize=7)
        for k in range(n_out, len(axes)):
            axes[k].axis("off")
        fig.suptitle(f"PPC PIT — {MODEL_PAPER_LABEL.get(model_id, model_id)}",
                     fontsize=11)
        fig.tight_layout()
        fig.savefig(os.path.join(out_dir, f"pit_y_{model_id}.png"), dpi=150)
        plt.close(fig)

        # coverage bar
        fig, ax = plt.subplots(figsize=(6, 3.5))
        labels = [OUTPUT_PAPER_LABEL.get(c, c) for c in OUTPUT_COLS]
        cov_true = [sdf[sdf["output"] == c]["coverage_90ci_true"].iloc[0]
                    for c in OUTPUT_COLS]
        xs = np.arange(len(labels))
        ax.bar(xs, cov_true, color="#4477aa", alpha=0.85)
        ax.axhline(0.9, color="red", linestyle="--", lw=1, label="Nominal 0.90")
        ax.set_xticks(xs)
        ax.set_xticklabels(labels, rotation=20, ha="right", fontsize=8)
        ax.set_ylabel("Empirical 90%-CI coverage")
        ax.set_ylim(0, 1.05)
        ax.set_title(f"PPC coverage — {MODEL_PAPER_LABEL.get(model_id, model_id)}",
                     fontsize=10)
        ax.legend(fontsize=8)
        fig.tight_layout()
        fig.savefig(os.path.join(out_dir, f"ppc_coverage_{model_id}.png"), dpi=150)
        plt.close(fig)
    except Exception as e:
        logger.warning(f"[{model_id}] 绘图失败 (non-fatal): {e}")

    summary_header = {
        "model_id": model_id,
        "n_cases": len(npz_files),
        "n_outputs": len(OUTPUT_COLS),
        "n_draws_per_case": PPC_N_DRAWS,
        "n_mc_per_theta": PPC_N_MC,
        "coverage_90_primary_stress": float(
            sdf[sdf["output"] == "iteration2_max_global_stress"]
                ["coverage_90ci_true"].iloc[0]),
        "mean_pit_primary_stress": float(
            sdf[sdf["output"] == "iteration2_max_global_stress"]
                ["pit_mean"].iloc[0]),
    }

    mf = make_experiment_manifest(
        experiment_id="posterior_ppc",
        model_id=model_id,
        input_source=chains_dir,
        outputs_saved=[os.path.join(out_dir, "ppc_per_case.csv"),
                       os.path.join(out_dir, "ppc_summary.csv")],
        key_results=summary_header,
        source_script=os.path.abspath(__file__),
        extra={"ALPHA_CI": ALPHA_CI},
    )
    write_manifest(os.path.join(out_dir, "ppc_manifest.json"), mf)
    logger.info(f"[{model_id}] SUMMARY: {json.dumps(summary_header, indent=2)}")
    logger.removeHandler(fh)
    return summary_header


if __name__ == "__main__":
    model_id_env = os.environ.get("MODEL_ID", "all")
    model_ids = list(MODELS.keys()) if model_id_env == "all" else [model_id_env]

    all_summaries = {}
    for mid in model_ids:
        if mid not in MODELS:
            logger.error(f"未知 MODEL_ID: {mid}")
            continue
        logger.info("=" * 60)
        logger.info(f"PPC — {mid}")
        logger.info("=" * 60)
        s = run_ppc_for_model(mid)
        if s is not None:
            all_summaries[mid] = s

    if all_summaries:
        all_out = os.path.join(experiment_dir("posterior"), "ppc_all_models.json")
        with open(all_out, "w") as f:
            json.dump(all_summaries, f, indent=2)
        logger.info(f"Cross-model PPC summary -> {all_out}")
    logger.info("PPC DONE")
