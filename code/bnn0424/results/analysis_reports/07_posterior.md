# 07 — Posterior (observation-driven inference, 18 benchmark cases)

源：`experiments/posterior/<model>/{benchmark_summary.csv, feasible_region.csv, posterior_manifest.json}`。忽略 `posterior.bak_20260415_215948/`。
MCMC config：N_total=8000，burn=2000，thin=5；obs_noise_frac=0.02；calib params = {E_intercept, alpha_base, alpha_slope, SS316_k_ref}；n_mc_posterior=20。
观测 = test split 真 HF + 2% 人工噪声，**符合 CLAUDE.md 0404 posterior benchmark rule**（从 test split 抽样，6 low + 6 near + 6 high = 18 cases）。

## 聚合指标

| 模型 | n_cases | acceptance 均值 [范围] | 90CI coverage | 可行域（60 τ-rows） |
|---|---|---|---|---|
| bnn-baseline | 18 | 0.621 [0.601, 0.639] | 0.903 | 0.183 |
| bnn-data-mono | 18 | 0.631 [0.611, 0.649] | 0.889 | 0.183 |
| bnn-phy-mono | 18 | 0.604 [0.582, 0.621] | 0.917 | 0.217 |
| bnn-data-mono-ineq | 18 | **0.659** [0.646, 0.674] | 0.889 | 0.150 |

## P(σ > 131 MPa | posterior) — feasible_region.csv 按类别

> **注意**：`feasible_region.csv` 仅含 low + near 两类共 10 cases 的可行域扫描，high 6 cases 未在该表中。high-stress 的 P_exceed 需要直接查 `benchmark_summary.csv` 的 high 子集（下方单列）。

| 模型 | low (n=6)：范围（均值） | near (n=4)：范围（均值） |
|---|---|---|
| bnn-baseline | 0.680–0.998 (0.872) | 0.601–1.000 (0.811) |
| bnn-data-mono | 0.677–0.991 (0.868) | 0.612–1.000 (0.812) |
| bnn-phy-mono | 0.657–0.999 (0.879) | 0.573–1.000 (0.804) |
| bnn-data-mono-ineq | 0.672–0.963 (0.843) | 0.626–0.998 (0.821) |

## HF rerun 状态（bnn-phy-mono，54/54 完成）

**完成日期**：2026-04-16（远程 tjzs@tjzs，AMD EPYC 9654 96-core + 2× RTX 5090）
**结果文件**：`posterior/bnn-phy-mono/hf_rerun/results/posterior_hf_rerun_summary_rebuilt.csv`（54 行）
**解析方式**：post-hoc parser 从 archive/caseXXX_*/PrintOut.txt 提取（runtime parser 有 bug，读错文件）

| 指标 | stress | keff | max_fuel_temp | max_monolith_temp | wall2 |
|---|---|---|---|---|---|
| post-mean MAE | 5.65 MPa | 0.0005 | 4.50 K | 5.09 K | 0.021 cm |
| post-mean rel MAE | 4.52% | 0.05% | 0.42% | 0.49% | 0.07% |
| [5%,95%] HF 包络覆盖 | 18/18 | 17/18 | 18/18 | 18/18 | 17/18 |

**HF wall-clock**：mean 2357 s, median 2328 s, std 297 s, range 1768–3022 s
**MCMC 参数 90%-CI 覆盖**：66/72 = 0.917（18 cases × 4 params）

**post-mean stress by category**：low MAE 6.65 MPa, near MAE 6.65 MPa, high MAE 3.67 MPa

| 模型 | hf_rerun 目录 | status |
|---|---|---|
| bnn-baseline | 不存在 | — |
| bnn-data-mono | 不存在 | — |
| bnn-phy-mono | 存在 | **54/54 完成** |
| bnn-data-mono-ineq | 存在 | 只写了 inputs，未运行 |

→ 正文已在 §2.4 末尾引用 HF rerun 结果并指向附录 N。

## 与 CLAUDE.md canonical（0405）对比

| 口径 | 0405 memory (phy-mono) | bnn0414 phy-mono | 判断 |
|---|---|---|---|
| 90CI coverage | 0.875 | **0.917** | ↑ 数值更新 |
| acceptance | 0.47–0.61 | 0.582–0.621 | 上沿重叠，下沿不同 |
| high-stress P>131 | 0.63–1.0 | feasible_region 无 high —— 不可直接复核 | 需从 benchmark_summary 的 high 子集重算 |

## 写作建议

1. **主文**写 acceptance 0.58–0.67 与 90CI coverage 0.889–0.917 作为标定证据。
2. **可行域**（τ=131 MPa 下的分位）用 feasible_region 的 low + near 子集。
3. **high-stress 后验** 用 benchmark_summary 计算（不在本报告中，需要再开一步小分析），**不要引用 CLAUDE.md 的旧 0.63–1.0 数字**（来源标注已过时）。
4. HF rerun（bnn-phy-mono）已完成 54/54：主文 §2.4 末尾引用关键数字（stress MAE 5.65 MPa, [5%,95%] 覆盖 18/18），详细结果放附录 N。

## Memory 更新建议
`project_posterior_canonical.md` 应改为：
- 18 benchmark cases；acceptance 0.58–0.67（四模型区间）；
- 90CI coverage 0.89–0.92（四模型）；
- high-stress P>131 的引用来源从 feasible_region 改为 benchmark_summary；
- HF-rerun（phy-mono）已完成 54/54；不作为验证证据 → 已作为验证证据，写入 §2.4 + 附录 N。
