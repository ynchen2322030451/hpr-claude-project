# run_lognormal_risk_postprocess.py
# ============================================================
# BNN 0414 后处理：对现有 D1_nominal_risk.csv 补充 Log-Normal 近似
# 的 P(exceed)。纯后处理，不触碰模型，不做 MC 采样。
#
# 与 0411 版本的差异：
#   - MODEL_IDS 更新为 BNN 4-model 列表
#   - 读取/写入路径仍走 experiment_dir("risk_propagation", <model_id>)，
#     指向 bnn0414/code/experiments_0404/experiments/risk_propagation/
#   - D1_nominal_risk.csv 的 stress_mean / stress_std 列在 BNN 下对应
#     total (epistemic+aleatoric) 汇总的样本统计量，无需改动算法
#
# 使用方式：
#   python run_lognormal_risk_postprocess.py
#
# 输出：
#   experiments_0404/experiments/risk_propagation/<model_id>/
#     D1_nominal_risk_lognormal.csv
# ============================================================

import os, sys
import numpy as np
import pandas as pd
from scipy import stats

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_CODE_ROOT = _SCRIPT_DIR
while _CODE_ROOT and not os.path.basename(_CODE_ROOT) == 'code':
    _CODE_ROOT = os.path.dirname(_CODE_ROOT)
_BNN_CONFIG_DIR = os.path.join(_CODE_ROOT, 'experiments_0404', 'config')
for _p in (_SCRIPT_DIR, _CODE_ROOT, _BNN_CONFIG_DIR,
           os.path.join(_CODE_ROOT, 'experiments_0404')):
    if _p and os.path.isdir(_p) and _p not in sys.path:
        sys.path.insert(0, _p)

try:
    from experiment_config_0404 import experiment_dir, ensure_dir
except ImportError:
    def experiment_dir(*args):
        return os.path.join(_SCRIPT_DIR, "..", "..", "experiments", *args)
    def ensure_dir(p):
        os.makedirs(p, exist_ok=True)


# BNN 4-model roster（phy-mono-ineq 已合并入 data-mono-ineq）
MODEL_IDS = ["bnn-baseline", "bnn-data-mono", "bnn-phy-mono", "bnn-data-mono-ineq"]
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
        return float(1.0 - stats.norm.cdf(threshold, loc=mu_g, scale=sigma_g))
    return float(1.0 - stats.lognorm.cdf(threshold, s=sigma_ln, scale=np.exp(mu_ln)))


def p_exceed_gaussian(mu_g: float, sigma_g: float, threshold: float) -> float:
    """Gaussian P(X > threshold)（验证用，应与 D1 中的 P_exceed 一致）"""
    return float(1.0 - stats.norm.cdf(threshold, loc=mu_g, scale=sigma_g))


def process_model(model_id: str):
    in_path = os.path.join(
        experiment_dir("risk_propagation"), model_id, "D1_nominal_risk.csv"
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
    out_dir = os.path.join(experiment_dir("risk_propagation"), model_id)
    ensure_dir(out_dir)
    out_path = os.path.join(out_dir, "D1_nominal_risk_lognormal.csv")
    # Overwrite guard at file level（脚本轻量，仅此一个 csv 产物）
    if os.path.exists(out_path):
        _rerun = os.environ.get("RERUN_TAG", "").strip()
        _force = os.environ.get("FORCE", "").strip() in ("1", "true", "yes")
        if _rerun:
            out_path = os.path.join(out_dir, f"D1_nominal_risk_lognormal.rerun_{_rerun}.csv")
            print(f"  [OVERWRITE-GUARD] RERUN_TAG={_rerun} → {out_path}")
        elif _force:
            print(f"  [OVERWRITE-GUARD] FORCE=1 覆盖 {out_path}")
        else:
            print(f"  [OVERWRITE-GUARD] 已存在 {out_path}；跳过 {model_id}（设 RERUN_TAG 或 FORCE=1 以强跑）")
            return
    out_df.to_csv(out_path, index=False)
    print(f"  [OK] {model_id}: saved → {out_path}")

    # 打印摘要（tau=131 MPa 行）
    sub = out_df[out_df["threshold_MPa"] == 131.0]
    if not sub.empty:
        print(f"       tau=131 MPa 对比（Gaussian vs LogNormal）：")
        print(sub[["sigma_k", "P_exceed_gaussian", "P_exceed_lognormal", "delta_pp"]].to_string(index=False))


def main():
    print("=== BNN Log-Normal 风险后处理 ===")
    print("说明：对 BNN 预测 stress 分布（已含 epistemic+aleatoric 总不确定度）")
    print("     用矩匹配方式拟合 Log-Normal。在大 sigma_k 区间（p5 接近 0 MPa）")
    print("     Gaussian 存在负值问题，Log-Normal 在物理上更合理（应力恒正）。\n")
    for mid in MODEL_IDS:
        print(f"--- {mid} ---")
        process_model(mid)
    print("\n完成。结果保存在各模型的 risk_propagation 目录下。")


if __name__ == "__main__":
    main()
