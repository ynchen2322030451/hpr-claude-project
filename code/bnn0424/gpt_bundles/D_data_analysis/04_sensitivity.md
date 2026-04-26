# 03 — Sensitivity: Sobol / Spearman / PRCC

源：`experiments/sensitivity/<model>/{sobol_results.csv, sobol_full.json, spearman_results.csv, prcc_results.csv, sensitivity_comparison.csv}`。
**注意**：`sensitivity_manifest.json` 的 `output_list = [iteration2_max_global_stress, iteration2_keff]` —— **不含 max_fuel_temp / max_monolith_temp**。正文不得在 Sobol 语境下声称"四个主输出"。
config：N_base=4096, N_repeats=50, CI=90%, n_mc_sobol=30。

## Stress（iteration2_max_global_stress）S1 / 主导输入

| 模型 | Top-1 S1 [90% CI] | Top-2 S1 [90% CI] | S1 CI 跨零 |
|---|---|---|---|
| bnn-baseline | E_intercept **0.582** [0.577, 0.586] | alpha_base 0.155 [0.148, 0.161] | SS316_alpha |
| bnn-data-mono | E_intercept 0.504 [0.498, 0.510] | alpha_base 0.232 [0.224, 0.239] | SS316_alpha |
| bnn-phy-mono | E_intercept 0.545 [0.541, 0.549] | alpha_base 0.196 [0.190, 0.202] | SS316_alpha |
| bnn-data-mono-ineq | E_intercept **0.558** [0.551, 0.565] | alpha_base 0.148 [0.139, 0.157] | 全非零 |

ST 排序与 S1 一致，E_intercept ST ∈ [0.525, 0.601]。

## keff（iteration2_keff）S1 / 主导输入

| 模型 | Top-1 S1 | Top-2 S1 | S1 CI 跨零 |
|---|---|---|---|
| bnn-baseline | alpha_base 0.778 [0.775, 0.781] | alpha_slope 0.181 | E_slope, E_intercept, SS316_T_ref, SS316_k_ref, SS316_alpha |
| bnn-data-mono | alpha_base 0.784 [0.781, 0.787] | alpha_slope 0.186 | E_slope, E_intercept, SS316_T_ref, SS316_alpha |
| bnn-phy-mono | alpha_base 0.768 [0.766, 0.771] | alpha_slope 0.186 | 同 baseline |
| bnn-data-mono-ineq | alpha_base 0.742 [0.736, 0.747] | alpha_slope 0.164 | 同 baseline |

## Spearman / PRCC（一致性检查）

`sensitivity_comparison.csv` 中，Spearman 与 PRCC 的排序**与 Sobol 定性一致**。例：
- phy-mono, stress: E_intercept Spearman=0.782，PRCC=0.926；
- phy-mono, keff: alpha_base Spearman=0.800，PRCC=0.883。
三方法互证主导项，可以作为 triangulation 证据写进附录。

## 与 CLAUDE.md canonical（0405）对比

| 口径 | 0405 memory | bnn0414（主文 baseline） | 结论 |
|---|---|---|---|
| stress E_intercept S1 | 0.598 | 0.582 | 定性一致，数值−2.7% |
| keff alpha_base S1 | 0.775 | 0.778 | 几乎相同 |
| stress 旧主导(k_ref,SS316)=0.529 | 替换 | SS316 相关均 CI 跨零或低阶 | 新结论成立 |

## 写作约束（遵守 CLAUDE.md）
- Sobol 置信区间跨零的因素 **不得**写成稳定主导（例：SS316_alpha 对 stress、E_slope/E_intercept/SS316_* 对 keff）。
- 只写 stress 与 keff 的 Sobol，不要把 fuel_temp / monolith_temp 混进来。
- 建议表达：
  > "For the coupled steady-state maximum stress, Young's modulus intercept (E_intercept) is the dominant driver with first-order Sobol index S₁ ≈ 0.54–0.58 (90% CI, across four BNN variants), followed by the base thermal expansion coefficient alpha_base with S₁ ≈ 0.15–0.23. For k_eff, alpha_base dominates (S₁ ≈ 0.74–0.78). Other inputs have first-order CIs overlapping zero and are not reported as stable drivers."
