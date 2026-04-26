# run_calibration_0404.py
# ============================================================
# BNN 0414 — 多 α calibration + PIT + NLL + interval score
# NCS revision P0-#2
#
# LOCAL ONLY — 纯本地后处理，不需要服务器。
#
# 输入：
#   code/models/<model>/fixed_eval/test_predictions_fixed.json
#     字段: mu (N,D), sigma (N,D), epistemic_var, aleatoric_var, y_true
#   code/models/<model>/repeat_eval/seed_<s>/metrics.json (多 seed 聚合)
#
# 产出 (bnn0414/results/accuracy/)：
#   calibration_multi_alpha.csv — per model × per output × per α:
#     nominal_alpha, empirical_coverage, interval_score, MPIW_alpha
#   scoring_rules.csv — per model × per output:
#     CRPS, NLL, IS_90, IS_95, ECE, sharpness
#   scoring_rules_multi_seed_ci.csv — 基于 repeat_eval 5 seeds 的 bootstrap CI
#   pit_values.npz — per model × per output 的 PIT 值，供作图复用
#   reliability_<model>.png — reliability diagram
#   pit_<model>.png — PIT histogram grid
#
# 调用：
#   python run_calibration_0404.py           # 全 4 模型
#   MODEL_ID=bnn-phy-mono python run_calibration_0404.py
# ============================================================

import os, sys, json, logging
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
    OUTPUT_COLS, PRIMARY_OUTPUTS, OUTPUT_META,
    REPEAT_SEEDS, SEED,
    model_fixed_eval_dir, model_repeat_eval_dir,
    ensure_dir,
)
# EXPR_ROOT_0404 in config 实际指向 bnn0414/code/，注释不准。
# 手算到 bnn0414/ 根
_BNN_ROOT = os.path.dirname(_CODE_ROOT)  # bnn0414/
from model_registry_0404 import MODELS
from manifest_utils_0404 import write_manifest, make_experiment_manifest

logging.basicConfig(level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger(__name__)


# ============================================================
# 配置
# ============================================================
ALPHA_LEVELS = [0.5, 0.68, 0.8, 0.9, 0.95, 0.99]   # nominal coverage
PIT_N_BINS   = 20
BOOTSTRAP_N  = 1000
CI_LEVEL     = 0.90

# paper-facing output name mapping（图内禁用 iter1/iter2 原名）
OUTPUT_PAPER_LABEL = {
    "iteration2_max_global_stress":    "Max. global stress",
    "iteration2_keff":                 r"$k_{\mathrm{eff}}$",
    "iteration2_max_fuel_temp":        "Max. fuel temp.",
    "iteration2_max_monolith_temp":    "Max. monolith temp.",
    "iteration2_wall2":                "Wall expansion",
}
MODEL_PAPER_LABEL = {
    "bnn-baseline":       "Reference surrogate",
    "bnn-data-mono":      "Data-monotone BNN",
    "bnn-phy-mono":       "Physics-regularized BNN",
    "bnn-data-mono-ineq": "Data+inequality BNN",
}


# ============================================================
# Scoring rules (Gaussian)
# ============================================================
def gaussian_crps(mu: np.ndarray, sigma: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Closed-form CRPS for Gaussian forecast. mu/sigma/y: same shape."""
    from scipy.stats import norm
    sigma = np.maximum(sigma, 1e-10)
    z = (y - mu) / sigma
    return sigma * (z * (2 * norm.cdf(z) - 1) + 2 * norm.pdf(z) - 1.0 / np.sqrt(np.pi))


def gaussian_nll(mu: np.ndarray, sigma: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Element-wise Gaussian negative log-likelihood."""
    sigma = np.maximum(sigma, 1e-10)
    return 0.5 * (np.log(2 * np.pi * sigma ** 2) + ((y - mu) / sigma) ** 2)


def interval_score(mu: np.ndarray, sigma: np.ndarray, y: np.ndarray, alpha: float) -> np.ndarray:
    """
    Gneiting & Raftery (2007) interval score at nominal coverage α.
    Lower is better. Uses Gaussian quantiles.
    """
    from scipy.stats import norm
    sigma = np.maximum(sigma, 1e-10)
    z = norm.ppf(0.5 + alpha / 2)
    lo = mu - z * sigma
    hi = mu + z * sigma
    width = hi - lo
    # penalty arms: use (1-α) convention (= tail mass)
    beta = 1.0 - alpha
    penalty_lo = (2.0 / beta) * np.maximum(lo - y, 0)
    penalty_hi = (2.0 / beta) * np.maximum(y - hi, 0)
    return width + penalty_lo + penalty_hi


def pit_values(mu: np.ndarray, sigma: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Probability Integral Transform under Gaussian predictive."""
    from scipy.stats import norm
    sigma = np.maximum(sigma, 1e-10)
    return norm.cdf((y - mu) / sigma)


def empirical_coverage(mu, sigma, y, alpha):
    from scipy.stats import norm
    z = norm.ppf(0.5 + alpha / 2)
    lo = mu - z * sigma
    hi = mu + z * sigma
    return float(np.mean((y >= lo) & (y <= hi)))


# ============================================================
# 加载 fixed_eval 预测
# ============================================================
def load_predictions(model_id: str) -> dict:
    p = os.path.join(model_fixed_eval_dir(model_id), "test_predictions_fixed.json")
    if not os.path.exists(p):
        raise FileNotFoundError(p)
    with open(p) as f:
        d = json.load(f)
    return {
        "mu":    np.asarray(d["mu"]),
        "sigma": np.asarray(d["sigma"]),
        "epistemic_var": np.asarray(d.get("epistemic_var", np.zeros_like(d["mu"]))),
        "aleatoric_var": np.asarray(d.get("aleatoric_var", np.zeros_like(d["mu"]))),
        "y_true": np.asarray(d["y_true"]),
        "output_cols": list(d["output_cols"]),
    }


# ============================================================
# 单模型：全输出全 α 指标
# ============================================================
def metrics_for_model(model_id: str) -> dict:
    logger.info(f"=== {model_id} ===")
    pred = load_predictions(model_id)
    mu, sig, y = pred["mu"], pred["sigma"], pred["y_true"]
    cols = pred["output_cols"]
    N, D = mu.shape

    # 逐输出逐 α
    rows_alpha = []
    for j, out in enumerate(cols):
        for alpha in ALPHA_LEVELS:
            emp = empirical_coverage(mu[:, j], sig[:, j], y[:, j], alpha)
            is_mean = float(np.mean(interval_score(mu[:, j], sig[:, j], y[:, j], alpha)))
            # MPIW at α
            from scipy.stats import norm
            z = norm.ppf(0.5 + alpha / 2)
            mpiw = float(np.mean(2 * z * sig[:, j]))
            rows_alpha.append({
                "model_id": model_id,
                "output": out,
                "output_label": OUTPUT_PAPER_LABEL.get(out, out),
                "nominal_alpha": alpha,
                "empirical_coverage": emp,
                "coverage_error": emp - alpha,
                "interval_score": is_mean,
                "MPIW_alpha": mpiw,
                "is_primary": out in PRIMARY_OUTPUTS,
            })

    # 逐输出 scoring rules（聚合 α）
    rows_scoring = []
    pit_per_out = {}
    for j, out in enumerate(cols):
        crps = float(np.mean(gaussian_crps(mu[:, j], sig[:, j], y[:, j])))
        nll  = float(np.mean(gaussian_nll(mu[:, j], sig[:, j], y[:, j])))
        is90 = float(np.mean(interval_score(mu[:, j], sig[:, j], y[:, j], 0.90)))
        is95 = float(np.mean(interval_score(mu[:, j], sig[:, j], y[:, j], 0.95)))
        sharp = float(np.mean(sig[:, j]))
        # ECE：|empirical - nominal| 在 α 网格上的均值
        alphas = np.array(ALPHA_LEVELS)
        empcov = np.array([empirical_coverage(mu[:, j], sig[:, j], y[:, j], a) for a in alphas])
        ece = float(np.mean(np.abs(empcov - alphas)))
        pit_per_out[out] = pit_values(mu[:, j], sig[:, j], y[:, j])

        rows_scoring.append({
            "model_id": model_id,
            "output": out,
            "output_label": OUTPUT_PAPER_LABEL.get(out, out),
            "CRPS": crps,
            "NLL": nll,
            "IS_90": is90,
            "IS_95": is95,
            "ECE": ece,
            "sharpness_mean_sigma": sharp,
            "is_primary": out in PRIMARY_OUTPUTS,
        })

    return {
        "alpha_rows": rows_alpha,
        "scoring_rows": rows_scoring,
        "pit": pit_per_out,
        "cols": cols,
        "N": N,
        "pred": pred,
    }


# ============================================================
# 多 seed 的 bootstrap CI（用 repeat_eval 聚合）
# ============================================================
def multi_seed_ci_for_model(model_id: str) -> pd.DataFrame:
    """从 repeat_eval/seed_*/metrics_per_output.csv 聚合 5 seed 的 per-output 指标。"""
    rows = []
    per_seed = []
    for s in REPEAT_SEEDS:
        p = os.path.join(model_repeat_eval_dir(model_id), f"seed_{s}", "metrics_per_output.csv")
        if not os.path.exists(p):
            logger.warning(f"  missing {p}")
            continue
        df = pd.read_csv(p)
        df["seed"] = s
        per_seed.append(df)
    if not per_seed:
        return pd.DataFrame()
    all_df = pd.concat(per_seed, ignore_index=True)

    # 对每 output 聚合
    from scipy.stats import t as student_t
    metrics = ["MAE", "RMSE", "R2", "PICP", "MPIW", "CRPS"]
    for out in all_df["output"].unique():
        sub = all_df[all_df["output"] == out]
        row = {"model_id": model_id, "output": out,
               "output_label": OUTPUT_PAPER_LABEL.get(out, out),
               "n_seeds": len(sub), "is_primary": out in PRIMARY_OUTPUTS}
        for m in metrics:
            if m not in sub.columns:
                continue
            vals = sub[m].values
            mean = float(np.mean(vals))
            std  = float(np.std(vals, ddof=1))
            # t-based CI (n=5, df=4)
            if len(vals) > 1:
                tcrit = student_t.ppf(0.5 + CI_LEVEL / 2, df=len(vals) - 1)
                half = tcrit * std / np.sqrt(len(vals))
                row[f"{m}_mean"]  = mean
                row[f"{m}_std"]   = std
                row[f"{m}_ci_lo"] = mean - half
                row[f"{m}_ci_hi"] = mean + half
            else:
                row[f"{m}_mean"] = mean
                row[f"{m}_std"]  = 0.0
                row[f"{m}_ci_lo"] = mean
                row[f"{m}_ci_hi"] = mean
        rows.append(row)
    return pd.DataFrame(rows)


# ============================================================
# 作图
# ============================================================
def plot_reliability(all_alpha_df: pd.DataFrame, out_dir: str):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    # 每模型一张图；每条线 = 一个 primary output
    for mid in all_alpha_df["model_id"].unique():
        sub = all_alpha_df[(all_alpha_df["model_id"] == mid)
                           & (all_alpha_df["is_primary"])]
        if sub.empty:
            continue
        fig, ax = plt.subplots(figsize=(5, 5))
        ax.plot([0, 1], [0, 1], "k--", alpha=0.6, label="Ideal")
        for out in sub["output"].unique():
            s2 = sub[sub["output"] == out].sort_values("nominal_alpha")
            ax.plot(s2["nominal_alpha"], s2["empirical_coverage"],
                    "-o", label=OUTPUT_PAPER_LABEL.get(out, out))
        ax.set_xlabel("Nominal coverage")
        ax.set_ylabel("Empirical coverage")
        ax.set_title(f"Reliability — {MODEL_PAPER_LABEL.get(mid, mid)}")
        ax.set_xlim(0, 1); ax.set_ylim(0, 1)
        ax.legend(fontsize=8, loc="lower right")
        ax.grid(True, alpha=0.3)
        fig.tight_layout()
        p = os.path.join(out_dir, f"reliability_{mid}.png")
        fig.savefig(p, dpi=150)
        fig.savefig(p.replace(".png", ".pdf"))
        plt.close(fig)
        logger.info(f"  saved {p}")


def plot_pit(pit_by_model: dict, out_dir: str):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    primary = [o for o in PRIMARY_OUTPUTS]
    for mid, pit_per_out in pit_by_model.items():
        primary_here = [o for o in primary if o in pit_per_out]
        if not primary_here:
            continue
        ncol = min(len(primary_here), 5)
        fig, axes = plt.subplots(1, ncol, figsize=(3.2 * ncol, 3.2), sharey=True)
        if ncol == 1:
            axes = [axes]
        for ax, out in zip(axes, primary_here):
            pit = pit_per_out[out]
            ax.hist(pit, bins=PIT_N_BINS, range=(0, 1),
                    density=True, edgecolor="black", alpha=0.75)
            ax.axhline(1.0, ls="--", color="red", alpha=0.7, label="Uniform")
            ax.set_xlabel("PIT")
            ax.set_title(OUTPUT_PAPER_LABEL.get(out, out), fontsize=9)
            ax.set_xlim(0, 1)
        axes[0].set_ylabel("Density")
        fig.suptitle(f"PIT — {MODEL_PAPER_LABEL.get(mid, mid)}", fontsize=11)
        fig.tight_layout()
        p = os.path.join(out_dir, f"pit_{mid}.png")
        fig.savefig(p, dpi=150)
        fig.savefig(p.replace(".png", ".pdf"))
        plt.close(fig)
        logger.info(f"  saved {p}")


# ============================================================
# 入口
# ============================================================
if __name__ == "__main__":
    model_id_env = os.environ.get("MODEL_ID", "all")
    model_ids = list(MODELS.keys()) if model_id_env == "all" else [model_id_env]

    out_dir = ensure_dir(os.path.join(_BNN_ROOT, "results", "accuracy"))
    out_dir = os.path.abspath(out_dir)
    logger.info(f"out_dir = {out_dir}")

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    fh = logging.FileHandler(os.path.join(out_dir, f"calibration_{ts}.log"))
    fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(fh)

    all_alpha = []
    all_scoring = []
    all_ci = []
    pit_by_model = {}

    for mid in model_ids:
        if mid not in MODELS:
            logger.error(f"未知 MODEL_ID: {mid}"); continue
        res = metrics_for_model(mid)
        all_alpha.extend(res["alpha_rows"])
        all_scoring.extend(res["scoring_rows"])
        pit_by_model[mid] = res["pit"]

        ci_df = multi_seed_ci_for_model(mid)
        if not ci_df.empty:
            all_ci.append(ci_df)

    df_alpha   = pd.DataFrame(all_alpha)
    df_scoring = pd.DataFrame(all_scoring)

    p_alpha   = os.path.join(out_dir, "calibration_multi_alpha.csv")
    p_scoring = os.path.join(out_dir, "scoring_rules.csv")
    df_alpha.to_csv(p_alpha, index=False)
    df_scoring.to_csv(p_scoring, index=False)
    logger.info(f"写入 {p_alpha} ({len(df_alpha)} 行)")
    logger.info(f"写入 {p_scoring} ({len(df_scoring)} 行)")

    if all_ci:
        df_ci = pd.concat(all_ci, ignore_index=True)
        p_ci = os.path.join(out_dir, "scoring_rules_multi_seed_ci.csv")
        df_ci.to_csv(p_ci, index=False)
        logger.info(f"写入 {p_ci} ({len(df_ci)} 行, 基于 {len(REPEAT_SEEDS)} seeds)")

    # PIT 值保存（供后续作图/复用）
    pit_save = {}
    for mid, pit_per_out in pit_by_model.items():
        for out, vals in pit_per_out.items():
            pit_save[f"{mid}::{out}"] = vals
    np.savez_compressed(os.path.join(out_dir, "pit_values.npz"), **pit_save)

    # 作图
    plot_reliability(df_alpha, out_dir)
    plot_pit(pit_by_model, out_dir)

    # manifest
    outputs_saved = [p_alpha, p_scoring]
    if all_ci:
        outputs_saved.append(p_ci)
    outputs_saved.append(os.path.join(out_dir, "pit_values.npz"))

    summary = {
        "alpha_levels":     ALPHA_LEVELS,
        "n_models":         len(model_ids),
        "mean_ECE":         float(df_scoring["ECE"].mean()),
        "max_ECE":          float(df_scoring["ECE"].max()),
        "mean_CRPS":        float(df_scoring["CRPS"].mean()),
        "mean_NLL":         float(df_scoring["NLL"].mean()),
        "ECE_by_model":     df_scoring.groupby("model_id")["ECE"].mean().to_dict(),
    }
    mf = make_experiment_manifest(
        experiment_id = "calibration_multi_alpha",
        model_id      = ",".join(model_ids),
        input_source  = "fixed_eval/test_predictions_fixed.json + repeat_eval/seed_*/metrics_per_output.csv",
        outputs_saved = outputs_saved,
        key_results   = summary,
        source_script = os.path.abspath(__file__),
        extra         = {"config": {
            "ALPHA_LEVELS": ALPHA_LEVELS, "PIT_N_BINS": PIT_N_BINS,
            "BOOTSTRAP_N": BOOTSTRAP_N, "CI_LEVEL": CI_LEVEL,
            "REPEAT_SEEDS": REPEAT_SEEDS,
        }},
    )
    write_manifest(os.path.join(out_dir, "calibration_manifest.json"), mf)

    logger.info(f"SUMMARY: {json.dumps(summary, indent=2)}")
    print("CALIBRATION DONE — out_dir:", out_dir)
