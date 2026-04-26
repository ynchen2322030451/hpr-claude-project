# run_monotonicity_violation_0404.py
# ============================================================
# BNN 0414 — 单调性 + 不等式违反率（NCS revision P0-#4）
#
# LOCAL ONLY — 纯本地前向；无服务器依赖。
#
# 与既有 run_physics_consistency_0404.py 的差别：
#   - 既有脚本：梯度符号一致性（连续/无限小测试，frac_correct 可达 1.0）
#   - 本脚本：离散有限差分 counterexample rate + 不等式硬约束违反率
#            在 DESIGN_SIGMA 量级的实际扰动下，看模型是否违反单调/不等式
#
# 输入：
#   - fixed_split/test.csv
#   - 各模型 checkpoint (bnn-{baseline,data-mono,phy-mono,data-mono-ineq})
#   - PHYSICS_PRIOR_PAIRS_RAW + INEQUALITY_RULES from model_registry_0404
#
# 产出 (bnn0414/results/physics_consistency/)：
#   monotonicity_violation_rate.csv   — model × (input, output, expected_sign) ×
#                                        {violation_rate, mean_magnitude, max_magnitude}
#   inequality_violation_rate.csv     — model × rule × violation_rate
#   violation_magnitude_<model>.png   — 违反幅度分布
#
# 调用：
#   python run_monotonicity_violation_0404.py
#   MODEL_ID=bnn-data-mono-ineq python run_monotonicity_violation_0404.py
# ============================================================

import os, sys, json, logging
from datetime import datetime

import numpy as np
import pandas as pd
import torch

# ── sys.path ────────────────────────────────────────────────
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_EXPR_DIR   = os.path.dirname(_SCRIPT_DIR)
sys.path.insert(0, _EXPR_DIR)
from _path_setup import setup_paths  # noqa: E402
setup_paths()
sys.path.insert(0, os.path.join(_EXPR_DIR, "evaluation"))

from experiment_config_0404 import (
    INPUT_COLS, OUTPUT_COLS, PRIMARY_OUTPUTS,
    SEED, DEVICE, FIXED_SPLIT_DIR, DESIGN_SIGMA,
    ensure_dir,
)
from model_registry_0404 import (
    MODELS, PHYSICS_PRIOR_PAIRS_RAW, INEQUALITY_RULES,
)
from manifest_utils_0404 import write_manifest, make_experiment_manifest
from run_eval_0404 import _resolve_artifacts, _load_model, _load_scalers
from bnn_model import get_device

logging.basicConfig(level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger(__name__)


# ============================================================
# 配置
# ============================================================
N_TEST_SAMPLES  = int(os.environ.get("N_TEST_SAMPLES", 0))  # 0 = 全部
PERTURB_SCALE   = float(os.environ.get("PERTURB_SCALE", 1.0))  # × DESIGN_SIGMA
PERTURB_N_DIRS  = int(os.environ.get("PERTURB_N_DIRS", 1))   # 每方向扰动次数
VIOL_TOLERANCE  = float(os.environ.get("VIOL_TOLERANCE", 0.0))  # 允许的容差


# paper-facing labels
OUTPUT_PAPER_LABEL = {
    "iteration2_max_global_stress":    "Max. global stress",
    "iteration2_keff":                 r"$k_{\mathrm{eff}}$",
    "iteration2_max_fuel_temp":        "Max. fuel temp.",
    "iteration2_max_monolith_temp":    "Max. monolith temp.",
    "iteration2_wall2":                "Wall expansion",
    "iteration1_max_fuel_temp":        "Max. fuel temp. (uncoupled)",
    "iteration1_max_monolith_temp":    "Max. monolith temp. (uncoupled)",
    "iteration1_max_global_stress":    "Max. global stress (uncoupled)",
    "iteration1_avg_fuel_temp":        "Avg. fuel temp. (uncoupled)",
    "iteration2_avg_fuel_temp":        "Avg. fuel temp.",
}
MODEL_PAPER_LABEL = {
    "bnn-baseline":       "Reference surrogate",
    "bnn-data-mono":      "Data-monotone BNN",
    "bnn-phy-mono":       "Physics-regularized BNN",
    "bnn-data-mono-ineq": "Data+inequality BNN",
}


# ============================================================
# 批量 mean-weights 前向（deterministic）
# ============================================================
def predict_mean(model, sx, sy, X_raw: np.ndarray, device) -> np.ndarray:
    """BNN mean-weights 前向返回原量纲 μ。shape (N, D_out)."""
    X_s = sx.transform(X_raw)
    X_t = torch.tensor(X_s, dtype=torch.float32, device=device)
    with torch.no_grad():
        out = model(X_t, sample=False)
        mu_s = out[0] if isinstance(out, tuple) else out
    mu_s = mu_s.cpu().numpy()
    mu_raw = sy.inverse_transform(mu_s)
    return mu_raw


# ============================================================
# 单调性离散违反率
# ============================================================
def monotonicity_violation(model, sx, sy, X_test: np.ndarray, device,
                            perturb_scale: float = 1.0) -> pd.DataFrame:
    """
    对每个 (input_name, output_name, expected_sign) physics pair，在 X_test 每个样本上：
      Δμ = μ(x + δ e_i) - μ(x - δ e_i), δ = PERTURB_SCALE × DESIGN_SIGMA[input_name]
    违反 = sign(Δμ) × expected_sign < -tol
    """
    N = len(X_test)
    rows = []

    # 预先计算所有 {(name, sign)} baseline 前向，减少开销
    mu_base = predict_mean(model, sx, sy, X_test, device)

    for (inp_name, out_name, sign, conf, _) in PHYSICS_PRIOR_PAIRS_RAW:
        if inp_name not in INPUT_COLS or out_name not in OUTPUT_COLS:
            continue
        i_in  = INPUT_COLS.index(inp_name)
        i_out = OUTPUT_COLS.index(out_name)
        delta = DESIGN_SIGMA[inp_name] * perturb_scale

        X_plus  = X_test.copy(); X_plus[:,  i_in] += delta
        X_minus = X_test.copy(); X_minus[:, i_in] -= delta

        mu_plus  = predict_mean(model, sx, sy, X_plus,  device)[:, i_out]
        mu_minus = predict_mean(model, sx, sy, X_minus, device)[:, i_out]
        d_mu = mu_plus - mu_minus                                     # 预期与 sign 同号
        signed = d_mu * sign                                          # 对准预期，>0 = 一致

        # 违反：signed < -tol（考虑 tol 做数值保护）
        tol = VIOL_TOLERANCE * np.std(mu_base[:, i_out]) + 1e-12
        viol_mask = signed < -tol
        viol_rate = float(np.mean(viol_mask))

        # 违反幅度：只在违反处取绝对 |Δμ|
        if viol_mask.any():
            viol_mag = np.abs(d_mu[viol_mask])
            mean_mag = float(np.mean(viol_mag))
            max_mag  = float(np.max(viol_mag))
            rel_mag  = float(np.mean(viol_mag) / (np.std(mu_base[:, i_out]) + 1e-12))
        else:
            mean_mag = max_mag = rel_mag = 0.0

        rows.append({
            "input":            inp_name,
            "output":           out_name,
            "output_label":     OUTPUT_PAPER_LABEL.get(out_name, out_name),
            "expected_sign":    "+" if sign > 0 else "-",
            "confidence":       conf,
            "perturb_delta":    delta,
            "n_test":           N,
            "violation_rate":   viol_rate,
            "mean_viol_magnitude": mean_mag,
            "max_viol_magnitude":  max_mag,
            "viol_mag_over_output_std": rel_mag,
            "is_primary_output": out_name in PRIMARY_OUTPUTS,
        })
        logger.info(
            f"  ({inp_name}{'↑'if sign>0 else '↓'} → {out_name}): "
            f"violation_rate = {viol_rate:.3f} (n={N}, δ={delta:.3g})"
        )

    return pd.DataFrame(rows)


# ============================================================
# 不等式违反率
# ============================================================
def inequality_violation(model, sx, sy, X_test: np.ndarray, device) -> pd.DataFrame:
    """
    对每个 inequality rule，在 X_test 的 mean-weights 预测上检查是否满足。
    """
    mu = predict_mean(model, sx, sy, X_test, device)
    rows = []
    for rule in INEQUALITY_RULES:
        name = rule["name"]
        rtype = rule["type"]
        if rtype == "greater_equal":
            big = mu[:, rule["j_big"]]
            small = mu[:, rule["j_small"]]
            viol_mask = big < small
            gap = small - big                 # 正值 = 违反
        elif rtype == "nonneg":
            v = mu[:, rule["j_val"]]
            bound = float(rule.get("bound", 0.0))
            viol_mask = v < bound
            gap = bound - v
        else:
            continue

        viol_rate = float(np.mean(viol_mask))
        if viol_mask.any():
            mean_gap = float(np.mean(gap[viol_mask]))
            max_gap  = float(np.max(gap[viol_mask]))
        else:
            mean_gap = max_gap = 0.0

        rows.append({
            "rule_name":      name,
            "rule_type":      rtype,
            "n_test":         len(X_test),
            "violation_rate": viol_rate,
            "mean_gap":       mean_gap,
            "max_gap":        max_gap,
        })
        logger.info(
            f"  [{name}]: violation_rate = {viol_rate:.4f}, "
            f"mean_gap={mean_gap:.3g}, max_gap={max_gap:.3g}"
        )

    return pd.DataFrame(rows)


# ============================================================
# 作图：各模型在 primary output 上的单调性违反率条形
# ============================================================
def plot_summary(mono_df: pd.DataFrame, ineq_df: pd.DataFrame, out_dir: str):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    # 单调性：仅 primary output
    prim = mono_df[mono_df["is_primary_output"]].copy()
    if not prim.empty:
        prim["model_label"] = prim["model_id"].map(MODEL_PAPER_LABEL).fillna(prim["model_id"])
        pivot = prim.pivot_table(
            index=["input", "output_label", "expected_sign"],
            columns="model_label", values="violation_rate",
        ).fillna(0.0)
        fig, ax = plt.subplots(figsize=(10, max(4, 0.6 * len(pivot))))
        pivot.plot(kind="barh", ax=ax, width=0.8)
        ax.set_xlabel("Violation rate (discrete ±δ test)")
        ax.set_ylabel("Physics pair")
        ax.set_title("Monotonicity violation rate on test split (primary outputs)")
        ax.grid(True, axis="x", alpha=0.3)
        ax.legend(title="Model", fontsize=8)
        fig.tight_layout()
        p = os.path.join(out_dir, "monotonicity_violation_primary.png")
        fig.savefig(p, dpi=150)
        fig.savefig(p.replace(".png", ".pdf"))
        plt.close(fig)
        logger.info(f"  saved {p}")

    # 不等式
    if not ineq_df.empty:
        ineq_df = ineq_df.copy()
        ineq_df["model_label"] = ineq_df["model_id"].map(MODEL_PAPER_LABEL).fillna(ineq_df["model_id"])
        pivot = ineq_df.pivot_table(
            index="rule_name", columns="model_label", values="violation_rate",
        ).fillna(0.0)
        fig, ax = plt.subplots(figsize=(10, max(3, 0.5 * len(pivot))))
        pivot.plot(kind="barh", ax=ax, width=0.8)
        ax.set_xlabel("Inequality violation rate")
        ax.set_ylabel("Rule")
        ax.set_title("Physical inequality violation rate on test split")
        ax.grid(True, axis="x", alpha=0.3)
        ax.legend(title="Model", fontsize=8)
        fig.tight_layout()
        p = os.path.join(out_dir, "inequality_violation.png")
        fig.savefig(p, dpi=150)
        fig.savefig(p.replace(".png", ".pdf"))
        plt.close(fig)
        logger.info(f"  saved {p}")


# ============================================================
# 单模型跑完整检查
# ============================================================
def run_for_model(model_id: str, X_test: np.ndarray) -> tuple:
    logger.info(f"=== {model_id} ===")
    device = get_device(DEVICE)
    ckpt, scapath = _resolve_artifacts(model_id)
    model = _load_model(ckpt, device); model.eval()
    scalers = _load_scalers(scapath); sx, sy = scalers["sx"], scalers["sy"]

    mono = monotonicity_violation(model, sx, sy, X_test, device, PERTURB_SCALE)
    mono["model_id"] = model_id
    mono["model_label"] = MODEL_PAPER_LABEL.get(model_id, model_id)

    ineq = inequality_violation(model, sx, sy, X_test, device)
    ineq["model_id"] = model_id
    ineq["model_label"] = MODEL_PAPER_LABEL.get(model_id, model_id)

    return mono, ineq


# ============================================================
# 入口
# ============================================================
if __name__ == "__main__":
    model_id_env = os.environ.get("MODEL_ID", "all")
    model_ids = list(MODELS.keys()) if model_id_env == "all" else [model_id_env]

    # 输出目录: bnn0414/results/physics_consistency/
    _BNN_ROOT = os.path.dirname(os.path.dirname(_SCRIPT_DIR))  # experiments_0404 -> bnn0414/code
    _BNN_ROOT = os.path.dirname(_BNN_ROOT)                     # bnn0414/
    out_dir = ensure_dir(os.path.join(_BNN_ROOT, "results", "physics_consistency"))
    out_dir = os.path.abspath(out_dir)
    logger.info(f"out_dir = {out_dir}")

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    fh = logging.FileHandler(os.path.join(out_dir, f"monotonicity_{ts}.log"))
    fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(fh)

    # 加载 test split
    test_df = pd.read_csv(os.path.join(FIXED_SPLIT_DIR, "test.csv"))
    X_test = test_df[INPUT_COLS].values.astype(float)
    if N_TEST_SAMPLES > 0 and N_TEST_SAMPLES < len(X_test):
        rng = np.random.RandomState(SEED)
        idx = rng.choice(len(X_test), N_TEST_SAMPLES, replace=False)
        X_test = X_test[idx]
    logger.info(f"N test samples = {len(X_test)} | PERTURB_SCALE = {PERTURB_SCALE}")

    all_mono, all_ineq = [], []
    for mid in model_ids:
        if mid not in MODELS:
            logger.error(f"未知 MODEL_ID: {mid}"); continue
        mono, ineq = run_for_model(mid, X_test)
        all_mono.append(mono)
        all_ineq.append(ineq)

    mono_df = pd.concat(all_mono, ignore_index=True) if all_mono else pd.DataFrame()
    ineq_df = pd.concat(all_ineq, ignore_index=True) if all_ineq else pd.DataFrame()

    p_mono = os.path.join(out_dir, "monotonicity_violation_rate.csv")
    p_ineq = os.path.join(out_dir, "inequality_violation_rate.csv")
    mono_df.to_csv(p_mono, index=False)
    ineq_df.to_csv(p_ineq, index=False)
    logger.info(f"写入 {p_mono} ({len(mono_df)} 行)")
    logger.info(f"写入 {p_ineq} ({len(ineq_df)} 行)")

    plot_summary(mono_df, ineq_df, out_dir)

    # manifest
    summary = {
        "n_test":           int(len(X_test)),
        "perturb_scale":    PERTURB_SCALE,
        "n_physics_pairs":  len(PHYSICS_PRIOR_PAIRS_RAW),
        "n_ineq_rules":     len(INEQUALITY_RULES),
        "mono_viol_rate_by_model": mono_df.groupby("model_id")["violation_rate"].mean().to_dict() if not mono_df.empty else {},
        "ineq_viol_rate_by_model": ineq_df.groupby("model_id")["violation_rate"].mean().to_dict() if not ineq_df.empty else {},
        "mono_viol_rate_primary_by_model": mono_df[mono_df["is_primary_output"]].groupby("model_id")["violation_rate"].mean().to_dict() if not mono_df.empty else {},
    }
    mf = make_experiment_manifest(
        experiment_id = "monotonicity_violation",
        model_id      = ",".join(model_ids),
        input_source  = f"{FIXED_SPLIT_DIR}/test.csv",
        outputs_saved = [p_mono, p_ineq],
        key_results   = summary,
        source_script = os.path.abspath(__file__),
        extra         = {"config": {
            "PERTURB_SCALE": PERTURB_SCALE,
            "PERTURB_N_DIRS": PERTURB_N_DIRS,
            "VIOL_TOLERANCE": VIOL_TOLERANCE,
            "N_TEST_SAMPLES": N_TEST_SAMPLES,
        }},
    )
    write_manifest(os.path.join(out_dir, "monotonicity_manifest.json"), mf)

    logger.info(f"SUMMARY: {json.dumps(summary, indent=2, default=str)}")
    print("MONOTONICITY DONE — out_dir:", out_dir)
