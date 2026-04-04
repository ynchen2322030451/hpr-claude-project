# diag_perturbation_stress_check.py
# ============================================================
# 【诊断脚本 - 仅供内部调试，不写入论文】
#
# 背景：
#   数据集是以 material_config.py 中的 MATERIAL_MEAN_VALUES 为设计标称点，
#   在 ±3σ (≈±30% 相对扰动) 范围内 LHS 均匀采样生成的。
#   当前论文 forward UQ 直接用 meta_stats [min, max] 作为采样范围，
#   等价于全量 ±3σ。
#
# 目的：
#   1) 统计数据集 iteration2_max_global_stress > 131 MPa 的真实比例
#   2) 以 material_config.py 中的设计标称值为中心，
#      扫描不同扰动倍数 k (Uniform[nominal ± k·σ])，
#      分别计算代理预测的 P(stress > 131 MPa)，
#      与数据集实际比例对照
#
# 扰动逻辑：
#   lo_eff[j] = nominal[j] - k * sigma[j]
#   hi_eff[j] = nominal[j] + k * sigma[j]
#   k=3 约等于当前全范围（数据集边界）
#
# 运行：
#   conda run -n nn_env python diag_perturbation_stress_check.py
# ============================================================

import os
import sys
import json
import pickle

import numpy as np
import pandas as pd
import torch

# ---- 路径配置 ----
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CODE_DIR   = os.path.dirname(SCRIPT_DIR)             # code/
EXP_DIR    = os.path.join(SCRIPT_DIR, "experiments_phys_levels")
SPLIT_DIR  = os.path.join(EXP_DIR, "fixed_split")
ART_DIR    = os.path.join(EXP_DIR, "fixed_surrogate_fixed_level2")
CKPT_PATH  = os.path.join(ART_DIR, "checkpoint_level2.pt")
SCALER_PATH = os.path.join(ART_DIR, "scalers_level2.pkl")

STRESS_COL = "iteration2_max_global_stress"
THRESHOLD  = 131.0  # MPa

INPUT_COLS = [
    "E_slope", "E_intercept", "nu", "alpha_base",
    "alpha_slope", "SS316_T_ref", "SS316_k_ref", "SS316_alpha"
]
OUTPUT_COLS = [
    "iteration1_avg_fuel_temp",
    "iteration1_max_fuel_temp",
    "iteration1_max_monolith_temp",
    "iteration1_max_global_stress",
    "iteration1_monolith_new_temperature",
    "iteration1_Hcore_after",
    "iteration1_wall2",
    "iteration2_keff",
    "iteration2_avg_fuel_temp",
    "iteration2_max_fuel_temp",
    "iteration2_max_monolith_temp",
    "iteration2_max_global_stress",
    "iteration2_monolith_new_temperature",
    "iteration2_Hcore_after",
    "iteration2_wall2",
]
STRESS_IDX = OUTPUT_COLS.index(STRESS_COL)

# ---- 设计标称值 & 标准差（来自 material_config.py）----
# 注：这里直接硬编码，不依赖 material_config.py（避免导入路径问题）
# 原始定义见 code/material_config.py: MATERIAL_MEAN_VALUES / MATERIAL_STD_DEV_VALUES
DESIGN_NOMINAL = {
    "E_slope":      -7e7,       # Pa/K
    "E_intercept":   2e11,      # Pa
    "nu":            0.31,      # -
    "alpha_base":    1e-5,      # 1/K
    "alpha_slope":   5e-9,      # 1/K^2
    "SS316_T_ref":   923.15,    # K
    "SS316_k_ref":   23.2,      # W/(m·K)
    "SS316_alpha":   1/75,      # W/(m·K^2)
}
DESIGN_SIGMA = {
    "E_slope":       7e6,       # 10% relative std
    "E_intercept":   2e10,
    "nu":            0.031,
    "alpha_base":    1e-6,
    "alpha_slope":   5e-10,
    "SS316_T_ref":   92.315,
    "SS316_k_ref":   2.32,
    "SS316_alpha":   1/750,
}

# 扫描的扰动倍数 (k·σ)
# k=3 ≈ 数据集全范围（当前论文用法）
SIGMA_MULTIPLIERS = [0.5, 1.0, 1.5, 2.0, 3.0]

N_SAMPLES = 20000
SEED      = 2026
DRAW_PRED = True   # True=预测分布采样; False=仅均值


# ============================================================
# 加载模型（从 run_phys_levels_main 复用 HeteroMLP）
# ============================================================
sys.path.insert(0, SCRIPT_DIR)
from run_phys_levels_main import HeteroMLP


# ============================================================
# 数据集真实比例
# ============================================================
def compute_dataset_proportion():
    dfs = []
    for split in ["train", "val", "test"]:
        p = os.path.join(SPLIT_DIR, f"{split}.csv")
        if os.path.exists(p):
            dfs.append(pd.read_csv(p))
    if not dfs:
        return None
    df = pd.concat(dfs, ignore_index=True)
    stress = df[STRESS_COL].dropna().values
    n_total   = len(stress)
    n_exceed  = int(np.sum(stress > THRESHOLD))
    return {
        "n_total":     n_total,
        "n_exceed":    n_exceed,
        "proportion":  n_exceed / n_total,
        "mean_MPa":    float(np.mean(stress)),
        "std_MPa":     float(np.std(stress)),
        "q05_MPa":     float(np.quantile(stress, 0.05)),
        "q50_MPa":     float(np.quantile(stress, 0.50)),
        "q95_MPa":     float(np.quantile(stress, 0.95)),
        "min_MPa":     float(np.min(stress)),
        "max_MPa":     float(np.max(stress)),
    }


# ============================================================
# 加载代理模型
# ============================================================
def load_surrogate():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    ckpt   = torch.load(CKPT_PATH, map_location="cpu")
    bp     = ckpt["best_params"]
    model  = HeteroMLP(
        in_dim=len(INPUT_COLS),
        out_dim=len(OUTPUT_COLS),
        width=int(bp["width"]),
        depth=int(bp["depth"]),
        dropout=float(bp["dropout"]),
    ).to(device)
    model.load_state_dict(ckpt["model_state_dict"], strict=False)
    model.eval()
    with open(SCALER_PATH, "rb") as f:
        scalers = pickle.load(f)
    return model, scalers["sx"], scalers["sy"], device


# ============================================================
# 以设计标称值为中心，按 k·σ 均匀采样输入
# ============================================================
def sample_inputs_nominal(k: float, n: int, rng: np.random.RandomState) -> np.ndarray:
    x = np.zeros((n, len(INPUT_COLS)), dtype=float)
    for j, col in enumerate(INPUT_COLS):
        nominal = DESIGN_NOMINAL[col]
        sigma   = DESIGN_SIGMA[col]
        lo = nominal - k * sigma
        hi = nominal + k * sigma
        x[:, j] = rng.uniform(lo, hi, size=n)
    return x


# ============================================================
# 代理预测
# ============================================================
@torch.no_grad()
def predict(model, sx, sy, x_raw: np.ndarray, device, rng: np.random.RandomState):
    x_s = sx.transform(x_raw)
    xt  = torch.tensor(x_s, dtype=torch.float32, device=device)
    mu_s, logvar_s = model(xt)
    mu_raw    = sy.inverse_transform(mu_s.cpu().numpy())
    sigma_raw = np.sqrt(np.exp(logvar_s.cpu().numpy())) * sy.scale_
    if DRAW_PRED:
        y = rng.normal(loc=mu_raw, scale=np.maximum(sigma_raw, 1e-12))
    else:
        y = mu_raw.copy()
    return y


# ============================================================
# 主流程
# ============================================================
def main():
    np.random.seed(SEED)

    print("=" * 70)
    print("  诊断：以设计标称值为中心，不同扰动倍数 vs. P(stress > 131 MPa)")
    print("  [仅供内部调试，不写入论文]")
    print("=" * 70)

    # --- 设计标称值参考 ---
    print("\n[参考] material_config.py 设计标称点（k=0 对应纯标称预测）")
    print(f"  {'参数':<18} {'标称值':>18}  {'1σ':>14}  {'k=3时范围'}")
    print("  " + "-" * 65)
    for col in INPUT_COLS:
        nom = DESIGN_NOMINAL[col]
        sig = DESIGN_SIGMA[col]
        rel = abs(sig / nom) * 100
        print(f"  {col:<18} {nom:>18.4g}  ±{sig:.4g} ({rel:.0f}%)  "
              f"[{nom-3*sig:.4g}, {nom+3*sig:.4g}]")

    # --- 数据集实际比例 ---
    ds = compute_dataset_proportion()
    if ds:
        print(f"\n[数据集] 全集 stress 统计（n={ds['n_total']}）")
        print(f"  mean ± std : {ds['mean_MPa']:.2f} ± {ds['std_MPa']:.2f} MPa")
        print(f"  q05 / q50 / q95 : {ds['q05_MPa']:.2f} / {ds['q50_MPa']:.2f} / {ds['q95_MPa']:.2f} MPa")
        print(f"  P(>131 MPa) : {ds['n_exceed']}/{ds['n_total']} = {ds['proportion']:.1%}")
    else:
        print("\n[WARN] 找不到 split CSV，跳过数据集比例计算")

    # --- 加载模型 ---
    print("\n[INFO] 加载代理模型 level2 ...")
    model, sx, sy, device = load_surrogate()
    print(f"[INFO] device = {device}")

    # --- 标称点单点预测（k=0）---
    nom_x = np.array([[DESIGN_NOMINAL[c] for c in INPUT_COLS]])
    rng0  = np.random.RandomState(SEED)
    y_nom = predict(model, sx, sy, nom_x, device, rng0)
    stress_nom = float(y_nom[0, STRESS_IDX])
    print(f"\n[标称点] 代理预测 stress = {stress_nom:.2f} MPa  "
          f"({'超阈值' if stress_nom > THRESHOLD else '在阈值内'})")

    # --- 扫描 σ 倍数 ---
    print(f"\n[INFO] N={N_SAMPLES}, draw_predictive={DRAW_PRED}")
    print(f"\n{'k (×σ)':>8}  {'采样范围说明':^20}  {'stress均值':>10}  "
          f"{'stress_std':>10}  {'P(>131)':>9}  {'与数据集差':>10}")
    print("-" * 80)

    rows = []
    for k in SIGMA_MULTIPLIERS:
        rng_x = np.random.RandomState(SEED + int(k * 100) + 1)
        rng_y = np.random.RandomState(SEED + int(k * 100) + 2)

        x_samp  = sample_inputs_nominal(k, N_SAMPLES, rng_x)
        y_samp  = predict(model, sx, sy, x_samp, device, rng_y)
        stress  = y_samp[:, STRESS_IDX]

        p_fail  = float(np.mean(stress > THRESHOLD))
        s_mean  = float(np.mean(stress))
        s_std   = float(np.std(stress))
        diff_ds = (p_fail - ds["proportion"]) if ds else float("nan")

        # 相对扰动百分比（以标称值为参考，取 nu 为代表）
        rel_pct = k * 10   # 因为 std = 10% * nominal，所以 k*σ = k*10%

        label = f"±{rel_pct:.0f}% 标称值"
        diff_str = f"{diff_ds:+.1%}" if ds else "N/A"
        print(f"{k:>8.1f}  {label:^20}  {s_mean:>10.2f}  {s_std:>10.2f}  "
              f"{p_fail:>9.1%}  {diff_str:>10}")

        rows.append({
            "k_sigma":       k,
            "rel_pct":       rel_pct,
            "n_samples":     N_SAMPLES,
            "draw_pred":     DRAW_PRED,
            "stress_mean":   round(s_mean, 3),
            "stress_std":    round(s_std, 3),
            "p_exceed_131":  round(p_fail, 4),
        })

    print("-" * 80)

    # --- 参考：当前论文（全 [min,max] 范围，约 k=3）---
    print(f"\n  [当前论文 forward UQ: 全 [min,max] 均匀]  P(>131) ≈ 72.1%  (saved result)")
    if ds:
        print(f"  [数据集真实]                               P(>131) = {ds['proportion']:.1%}")

    # --- 解读提示 ---
    print("\n[解读]")
    print("  · 标称点 stress 预测值直接判断了哪个区域是'安全'的")
    print("  · k=1 (±10%) 是原数据生成时 1σ 扰动，物理意义最清晰")
    print("  · k=3 (±30%) 约等于当前论文全范围，P(>131) 应接近已保存值 72%")
    print("  · 若标称点本身 stress >> 131 MPa，则任意扰动都有高失效概率")
    print("    这是物理特性，不是代理问题")

    print("\n[DONE]\n")


if __name__ == "__main__":
    main()
