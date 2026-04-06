# run_lognormal_risk_postprocess.py
# ============================================================
# 后处理：在现有 Gaussian 风险曲线基础上，额外计算
# Log-Normal 近似的 P(exceed) 作为补充参考
#
# 不需要重训练，直接读取 D1_nominal_risk.csv 中的
# stress_mean, stress_std，拟合 Log-Normal 后计算超阈值概率
#
# 使用方式：
#   python run_lognormal_risk_postprocess.py
#
# 输出：
#   experiments/risk_propagation/<model_id>/D1_nominal_risk_lognormal.csv
# ============================================================

import os, sys
import numpy as np
import pandas as pd
from scipy import stats

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_SCRIPT_DIR, ".."))

try:
    from config.experiment_config_0404 import experiment_dir, ensure_dir
except ImportError:
    def experiment_dir(*args):
        return os.path.join(_SCRIPT_DIR, "..", "..", "experiments", *args)
    def ensure_dir(p):
        os.makedirs(p, exist_ok=True)


MODEL_IDS = ["baseline", "data-mono", "phy-mono"]
THRESHOLDS = [110.0, 120.0, 131.0]


def gaussian_to_lognormal_params(mu_g: float, sigma_g: float):
    """
    将 Gaussian(mu_g, sigma_g) 矩匹配到 LogNormal(mu_ln, sigma_ln)，
    使得两者均值和方差相同。

    LogNormal 参数（对数空间）：
        sigma_ln² = ln(1 + (sigma_g / mu_g)²)
        mu_ln     = ln(mu_g) - 0.5 * sigma_ln²
    """
    if mu_g <= 0 or sigma_g <= 0:
        return None, None
    sigma_ln_sq = np.log(1.0 + (sigma_g / mu_g) ** 2)
    mu_ln = np.log(mu_g) - 0.5 * sigma_ln_sq
    return mu_ln, float(np.sqrt(sigma_ln_sq))


def p_exceed_lognormal(mu_g: float, sigma_g: float, threshold: float) -> float:
    """
    用矩匹配的 LogNormal 计算 P(X > threshold)。
    若 mu_g <= 0 则回退到 Gaussian。
    """
    mu_ln, sigma_ln = gaussian_to_lognormal_params(mu_g, sigma_g)
    if mu_ln is None:
        # 回退到 Gaussian
        return float(1.0 - stats.norm.cdf(threshold, loc=mu_g, scale=sigma_g))
    return float(1.0 - stats.lognorm.cdf(threshold, s=sigma_ln, scale=np.exp(mu_ln)))


def p_exceed_gaussian(mu_g: float, sigma_g: float, threshold: float) -> float:
    """Gaussian P(X > threshold)（验证用，应与 D1 中的 P_exceed 一致）"""
    return float(1.0 - stats.norm.cdf(threshold, loc=mu_g, scale=sigma_g))


def process_model(model_id: str):
    in_path = os.path.join(
        experiment_dir("risk_propagation", model_id), "D1_nominal_risk.csv"
    )
    if not os.path.isfile(in_path):
        print(f"  [SKIP] {model_id}: {in_path} not found")
        return

    df = pd.read_csv(in_path)

    results = []
    for _, row in df.iterrows():
        mu_g    = float(row["stress_mean"])
        sigma_g = float(row["stress_std"])
        tau     = float(row["threshold_MPa"])
        sigma_k = float(row["sigma_k"])

        p_gauss  = p_exceed_gaussian(mu_g, sigma_g, tau)
        p_logn   = p_exceed_lognormal(mu_g, sigma_g, tau)

        results.append({
            "sigma_k":            sigma_k,
            "threshold_MPa":      tau,
            "stress_mean":        mu_g,
            "stress_std":         sigma_g,
            "P_exceed_gaussian":  p_gauss,
            "P_exceed_lognormal": p_logn,
            "delta_pp":           round((p_logn - p_gauss) * 100, 4),  # 百分点差
        })

    out_df  = pd.DataFrame(results)
    out_dir = experiment_dir("risk_propagation", model_id)
    ensure_dir(out_dir)
    out_path = os.path.join(out_dir, "D1_nominal_risk_lognormal.csv")
    out_df.to_csv(out_path, index=False)
    print(f"  [OK] {model_id}: saved → {out_path}")

    # 打印摘要（tau=131 MPa 行）
    sub = out_df[out_df["threshold_MPa"] == 131.0]
    if not sub.empty:
        print(f"       tau=131 MPa 对比（Gaussian vs LogNormal）：")
        print(sub[["sigma_k", "P_exceed_gaussian", "P_exceed_lognormal", "delta_pp"]].to_string(index=False))


def main():
    print("=== Log-Normal 风险后处理 ===")
    print("说明：对 stress 预测分布用矩匹配方式拟合 Log-Normal，")
    print("     在大 sigma_k 区间（p5 接近 0 MPa）Gaussian 存在负值问题，")
    print("     Log-Normal 在物理上更合理（应力恒正）。\n")
    for mid in MODEL_IDS:
        print(f"--- {mid} ---")
        process_model(mid)
    print("\n完成。结果保存在各模型的 risk_propagation 目录下。")


if __name__ == "__main__":
    main()
