# run_budget_matched_risk_0404.py
# ============================================================
# BNN 0414 — Compute-budget matched risk comparison
# NCS revision P0-#5
#
# LOCAL ONLY — 纯本地分析；无前向计算。
#
# 核心命题（NCS "enabling" 论点）：
#   在 tail risk P(σ > τ) 的 CI 半宽达到 h_target 时所需 wall-clock：
#     HF-MC:         N_HF  × t_HF   s
#     surrogate-MC:  N_surr × t_surr s
#   对同一 h_target 比较，量化 enabling 比率。
#
# 输入：
#   bnn0414/code/experiments/computational_speedup/<model>/bnn_speed_benchmark.json
#     → 取 single_sample_latency_sec 和 per_sample_batch_latency_sec
#   bnn0414/code/experiments/posterior/<model>/hf_rerun/results/progress.csv
#     → 若有真实 HF elapsed_s 统计，用之；否则 fallback 到 3600s/case 的占位
#   bnn0414/code/experiments/risk_propagation/<model>/D1_nominal_risk.csv
#     → 读参考 P_exceed 值（τ=131）
#
# 输出 (bnn0414/results/speed/)：
#   budget_matched_risk.csv   — model × target_CI_half × {N, wallclock_HF, wallclock_surr, speedup}
#   budget_matched_risk.png   — 双曲线 + 交叉点
#   hf_wallclock_source.json  — HF 时间来源声明（真实 vs 3600s fallback）
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
for _p in (_SCRIPT_DIR, _CODE_ROOT, _BNN_CONFIG_DIR):
    if _p and os.path.isdir(_p) and _p not in sys.path:
        sys.path.insert(0, _p)

from experiment_config_0404 import (
    PRIMARY_STRESS_THRESHOLD, THRESHOLD_SWEEP,
    RISK_PROP_N_SAMPLES, ensure_dir,
)
from model_registry_0404 import MODELS
from manifest_utils_0404 import write_manifest, make_experiment_manifest

logging.basicConfig(level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger(__name__)


# ============================================================
# 路径
# ============================================================
_BNN_ROOT = os.path.dirname(_CODE_ROOT)  # bnn0414/
SPEEDUP_DIR_TPL  = os.path.join(_BNN_ROOT, "code", "experiments", "computational_speedup", "{}")
HFRER_DIR_TPL    = os.path.join(_BNN_ROOT, "code", "experiments", "posterior", "{}", "hf_rerun", "results")
RISKPROP_DIR_TPL = os.path.join(_BNN_ROOT, "code", "experiments", "risk_propagation", "{}")

MODEL_PAPER_LABEL = {
    "bnn-baseline":       "Reference surrogate",
    "bnn-data-mono":      "Data-monotone BNN",
    "bnn-phy-mono":       "Physics-regularized BNN",
    "bnn-data-mono-ineq": "Data+inequality BNN",
}

# 目标 CI 半宽网格（P(σ>τ) 的 ±h）
TARGET_CI_HALF = [0.001, 0.002, 0.005, 0.01, 0.02, 0.05]

# HF canonical time: 2266s (use_time_mean from 0411/results/speed/hf_runtime_final.json,
# 3-run benchmark on AMD EPYC 9654 + RTX 5090). The old 3600s was a placeholder.
HF_CANONICAL_SEC = 2266.0
HF_FALLBACK_SEC = HF_CANONICAL_SEC


# ============================================================
# 时间来源聚合
# ============================================================
def load_surrogate_latency(model_id: str, fallback_model: str = "bnn-baseline") -> dict:
    """
    优先读本 model 的 bnn_speed_benchmark.json。
    若缺失，回退到 fallback_model（同架构 → per-sample latency 应近似相同），
    并在返回 dict 中标记 latency_source='fallback_<model>'.
    """
    p = os.path.join(SPEEDUP_DIR_TPL.format(model_id), "bnn_speed_benchmark.json")
    latency_source = model_id
    if not os.path.exists(p):
        p = os.path.join(SPEEDUP_DIR_TPL.format(fallback_model), "bnn_speed_benchmark.json")
        latency_source = f"fallback_{fallback_model}"
        if not os.path.exists(p):
            return {}
    with open(p) as f:
        d = json.load(f)
    return {
        "single_sample_latency_sec": d.get("single_sample_latency_sec"),
        "per_sample_batch_latency_sec": d.get("per_sample_batch_latency_sec"),
        "n_mc_eval": d.get("n_mc_eval"),
        "batch_size": d.get("batch_size"),
        "latency_source": latency_source,
    }


def load_hf_wallclock(models: list) -> dict:
    """
    尝试从 hf_rerun/results/progress.csv 聚合真实 HF 时间。
    忽略 status=='dry-run'/'queued'/'failed' 的行；只用 success 且 elapsed_s>0 的。
    返回：
      {source: "measured" or "fallback", mean_sec, std_sec, n_cases, raw_rows}
    """
    all_elapsed = []
    for mid in models:
        p = os.path.join(HFRER_DIR_TPL.format(mid), "progress.csv")
        if not os.path.exists(p):
            continue
        df = pd.read_csv(p)
        success_mask = df["status"].astype(str).str.lower().isin(
            ["success", "done", "ok", "completed"]
        ) & (df["elapsed_s"] > 0)
        good = df[success_mask]
        if len(good) > 0:
            all_elapsed.extend(good["elapsed_s"].tolist())

    if len(all_elapsed) >= 3:
        arr = np.array(all_elapsed, dtype=float)
        return {
            "source":    "measured",
            "mean_sec":  float(arr.mean()),
            "std_sec":   float(arr.std()),
            "median_sec":float(np.median(arr)),
            "n_cases":   int(len(arr)),
            "raw_min_sec":  float(arr.min()),
            "raw_max_sec":  float(arr.max()),
        }
    return {
        "source":   "fallback",
        "mean_sec": HF_FALLBACK_SEC,
        "std_sec":  0.0,
        "median_sec": HF_FALLBACK_SEC,
        "n_cases":  0,
        "note":     f"No completed HF runs found; using canonical {HF_FALLBACK_SEC}s from hf_runtime_final.json (3-run benchmark).",
    }


def load_reference_p_exceed(model_id: str, tau: float, sigma_k: float = 1.0) -> float:
    """从 D1_nominal_risk.csv 读 P_exceed 用于 CI 估计."""
    p = os.path.join(RISKPROP_DIR_TPL.format(model_id), "D1_nominal_risk.csv")
    if not os.path.exists(p):
        logger.warning(f"  risk_propagation CSV 缺失: {p}")
        return 0.5  # fallback 最坏情况
    df = pd.read_csv(p)
    q = df[(np.isclose(df["threshold_MPa"], tau)) & (np.isclose(df["sigma_k"], sigma_k))]
    if len(q) == 0:
        logger.warning(f"  no match for tau={tau}, sigma_k={sigma_k} in {p}")
        return 0.5
    return float(q["P_exceed"].iloc[0])


# ============================================================
# 核心：计算 N 和 wall-clock
# ============================================================
def samples_for_ci_half(p: float, h: float) -> int:
    """
    Wald CI 半宽 h = z * sqrt(p(1-p)/N)，z=1.96 (95% CI).
    N = (1.96^2) * p(1-p) / h^2. 至少 1.
    """
    z = 1.96
    var = max(p * (1 - p), 1e-4)  # 避免 0
    N = (z ** 2) * var / (h ** 2)
    return max(int(np.ceil(N)), 1)


def wallclock_for_N(N: int, per_sample_sec: float) -> float:
    return N * per_sample_sec


# ============================================================
# 单模型分析
# ============================================================
def analyze_model(model_id: str, hf_wallclock: dict, tau: float = None) -> pd.DataFrame:
    if tau is None:
        tau = PRIMARY_STRESS_THRESHOLD

    lat = load_surrogate_latency(model_id)
    if not lat:
        logger.warning(f"[{model_id}] 无 speed benchmark；跳过")
        return pd.DataFrame()

    p_ref = load_reference_p_exceed(model_id, tau)
    logger.info(f"[{model_id}] reference P(σ>{tau})={p_ref:.4f}, "
                f"surrogate per-sample = {lat['per_sample_batch_latency_sec']:.2e} s (batch), "
                f"{lat['single_sample_latency_sec']:.2e} s (single), "
                f"latency_source={lat.get('latency_source', model_id)}")

    rows = []
    # 用两档 surrogate 时间都算：batch 路径（保守下界）与 single-sample（上界）
    for mode, per_sample in [
        ("batch", lat["per_sample_batch_latency_sec"]),
        ("single_mc", lat["single_sample_latency_sec"]),
    ]:
        for h in TARGET_CI_HALF:
            N = samples_for_ci_half(p_ref, h)
            t_surr = wallclock_for_N(N, per_sample)
            t_hf   = wallclock_for_N(N, hf_wallclock["mean_sec"])
            rows.append({
                "model_id":           model_id,
                "model_label":        MODEL_PAPER_LABEL.get(model_id, model_id),
                "tau_MPa":            tau,
                "p_exceed_ref":       p_ref,
                "target_CI_half":     h,
                "N_samples_required": N,
                "surrogate_mode":     mode,
                "surrogate_sec_per_sample":  per_sample,
                "surrogate_total_sec":       t_surr,
                "surrogate_total_hours":     t_surr / 3600,
                "HF_sec_per_case":           hf_wallclock["mean_sec"],
                "HF_total_sec":              t_hf,
                "HF_total_hours":            t_hf / 3600,
                "HF_total_days":             t_hf / 86400,
                "speedup_HF_over_surr":      t_hf / max(t_surr, 1e-12),
                "hf_source":                 hf_wallclock["source"],
                "surrogate_latency_source":  lat.get("latency_source", model_id),
            })
    return pd.DataFrame(rows)


# ============================================================
# 作图
# ============================================================
def plot_budget_curves(df: pd.DataFrame, out_dir: str):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    # 只画 batch 模式的曲线（surrogate 的实际可达下界）
    sub = df[df["surrogate_mode"] == "batch"].copy()
    if sub.empty:
        return

    fig, ax = plt.subplots(figsize=(6.5, 5))

    # surrogate 每模型一条
    for mid in sub["model_id"].unique():
        s = sub[sub["model_id"] == mid].sort_values("target_CI_half")
        ax.plot(s["target_CI_half"], s["surrogate_total_sec"],
                "-o", markersize=4, label=MODEL_PAPER_LABEL.get(mid, mid))

    # HF 曲线（所有模型共用 HF 时间，取第一个）
    s0 = sub[sub["model_id"] == sub["model_id"].iloc[0]].sort_values("target_CI_half")
    ax.plot(s0["target_CI_half"], s0["HF_total_sec"],
            "k--", linewidth=2, label="HF Monte Carlo")

    # 水平参考：1 hour, 1 day, 30 days
    for sec, label in [(3600, "1 hour"), (86400, "1 day"),
                        (86400 * 30, "1 month"), (86400 * 365, "1 year")]:
        ax.axhline(sec, color="gray", linestyle=":", alpha=0.5, linewidth=0.8)
        ax.text(min(TARGET_CI_HALF) * 0.8, sec, label,
                fontsize=7, color="gray", va="bottom")

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel(r"Target CI half-width on $P(\sigma > 131\,\mathrm{MPa})$")
    ax.set_ylabel("Wall-clock time (s)")
    ax.set_title("Budget-matched risk estimation: HF-MC vs surrogate-MC")
    ax.legend(fontsize=8, loc="upper right")
    ax.grid(True, which="both", alpha=0.3)
    fig.tight_layout()
    p = os.path.join(out_dir, "budget_matched_risk.png")
    fig.savefig(p, dpi=150)
    fig.savefig(p.replace(".png", ".pdf"))
    plt.close(fig)
    logger.info(f"  saved {p}")


# ============================================================
# 入口
# ============================================================
if __name__ == "__main__":
    model_ids = list(MODELS.keys())
    out_dir = ensure_dir(os.path.join(_BNN_ROOT, "results", "speed"))
    out_dir = os.path.abspath(out_dir)
    logger.info(f"out_dir = {out_dir}")

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    fh = logging.FileHandler(os.path.join(out_dir, f"budget_matched_{ts}.log"))
    fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(fh)

    hf_wc = load_hf_wallclock(model_ids)
    logger.info(f"HF wall-clock source = {hf_wc}")

    with open(os.path.join(out_dir, "hf_wallclock_source.json"), "w") as f:
        json.dump(hf_wc, f, indent=2)

    all_rows = []
    for mid in model_ids:
        df = analyze_model(mid, hf_wc)
        if not df.empty:
            all_rows.append(df)

    if not all_rows:
        logger.error("无可用数据；退出")
        sys.exit(1)

    out_df = pd.concat(all_rows, ignore_index=True)
    p_csv = os.path.join(out_dir, "budget_matched_risk.csv")
    out_df.to_csv(p_csv, index=False)
    logger.info(f"写入 {p_csv} ({len(out_df)} 行)")

    plot_budget_curves(out_df, out_dir)

    # 关键摘要
    summary_row = out_df[(out_df["surrogate_mode"] == "batch")
                          & (out_df["target_CI_half"] == 0.005)
                          & (out_df["model_id"] == "bnn-phy-mono")].iloc[0].to_dict() \
        if len(out_df[(out_df["surrogate_mode"] == "batch")
                       & (out_df["target_CI_half"] == 0.005)
                       & (out_df["model_id"] == "bnn-phy-mono")]) > 0 else {}

    summary = {
        "tau_MPa": float(PRIMARY_STRESS_THRESHOLD),
        "n_models": len(model_ids),
        "n_target_CI_points": len(TARGET_CI_HALF),
        "hf_time_source": hf_wc["source"],
        "hf_time_mean_sec": hf_wc["mean_sec"],
        "headline_at_CI_0.005_phy_mono": summary_row,
        "WARNING": (
            f"HF wall-clock = {hf_wc['mean_sec']:.0f}s; source='{hf_wc['source']}'. "
            "Canonical benchmark = 2266s (3-run mean, hf_runtime_final.json). "
            "若 hf_rerun 的 progress.csv 有 ≥3 条 success 记录，将自动切为 'measured' 来源。"
            if hf_wc["source"] == "fallback" else "HF wall-clock 来自真实 rerun 测量"
        ),
    }

    mf = make_experiment_manifest(
        experiment_id = "budget_matched_risk",
        model_id      = ",".join(model_ids),
        input_source  = "bnn_speed_benchmark.json + hf_rerun/progress.csv + D1_nominal_risk.csv",
        outputs_saved = [p_csv, os.path.join(out_dir, "budget_matched_risk.png")],
        key_results   = summary,
        source_script = os.path.abspath(__file__),
        extra         = {"target_CI_half": TARGET_CI_HALF,
                         "hf_fallback_sec": HF_FALLBACK_SEC},
    )
    write_manifest(os.path.join(out_dir, "budget_matched_manifest.json"), mf)

    logger.info(f"SUMMARY: {json.dumps(summary, indent=2, default=str)}")
    print("BUDGET-MATCHED DONE — out_dir:", out_dir)
