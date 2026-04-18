# bnn0414 分析摘要（for manuscript 0414_v4）

生成日期：2026-04-16
完整版见 `code/bnn0414/results/analysis_reports/00_overview.md` 及 01–07 分报告。
主对比：`Reference surrogate` (bnn-baseline) vs `Physics-regularized surrogate` (bnn-data-mono-ineq)。bnn-data-mono / bnn-phy-mono 作为附录消融。

## 一、可直接入正文的数值（已核实与文件对齐）

### 1. Accuracy（5 seeds，n_test=459）
| metric | Reference | Physics-regularized | Δ |
|---|---|---|---|
| MAE | 2.62 ± 0.13 | 2.68 ± 0.11 | +2.2% |
| R² | 0.744 ± 0.048 | 0.733 ± 0.047 | −0.011 |
| PICP | 0.976 ± 0.005 | 0.986 ± 0.003 | +0.010 |
| MPIW | 16.24 ± 0.26 | 21.14 ± 0.32 | +30.2% |
| CRPS | 1.97 ± 0.07 | 2.21 ± 0.06 | +12.3% |

### 2. Speed（bnn-baseline，CUDA，50-sample MC）
- 单样本 MC 推理：**12.9 ms**
- HF 参考：2266 s/case（3-run benchmark，AMD EPYC 9654）；54-case rerun 均值 2357 s
- **Speedup ≈ 1.76×10⁵**（单样本 MC vs HF @ 2266 s）

### 3. Sensitivity（Sobol, N=4096, 50 rep, 90% CI）
- Stress 主导：**E_intercept S₁ ∈ [0.54, 0.58]**（四模型），alpha_base S₁ ∈ [0.15, 0.23]
- keff 主导：**alpha_base S₁ ∈ [0.74, 0.78]**，alpha_slope S₁ ∈ [0.16, 0.19]
- **CI 跨零的输入不得写成稳定主导**：SS316_alpha (stress)；E_slope / E_intercept / SS316_T_ref / SS316_k_ref / SS316_alpha (keff)
- 仅对 stress 与 keff 做了 Sobol —— 不要写"四个主输出"

### 4. Risk (131 MPa, N=20000)
- Reference P>131 = **0.841**
- Physics-regularized P>131 = **0.816**（更保守 2.5 个百分点）
- σ_k=2.0 鲁棒性：Reference 0.708 vs Physics-regularized 0.725（后者衰减更慢）
- **未保存 bootstrap CI**，避免"统计显著"表述

### 5. Posterior (18 benchmark, MCMC 8000/2000/thin5)
- Acceptance 四模型均值区间：**0.58–0.67**
- 90CI coverage：**0.89–0.92**
- low/near cases P(σ>131|post)：详见 07 报告
- ✅ **HF rerun（bnn-phy-mono）54/54 完成**（2026-04-16）
  - post-mean stress MAE = 5.65 MPa (4.52% rel)
  - [5%,95%] HF 包络覆盖：stress 18/18, keff 17/18, wall₂ 17/18
  - MCMC 参数 90%-CI 覆盖 = 0.917 (66/72)
  - HF wall-clock：mean 2357 s, median 2328 s, range 1768–3022 s
  - 正文 §2.4 末尾已引用，详细内容放附录 N

### 6. Physics consistency
- 4 模型 × 10 (input, output) pairs × 435 points，frac_gradient_correct = **1.000**
- ⚠️ 不能用此指标区分 baseline 与 physics-regularized（都满分）

### 7. Generalization (OOD tail subsets)
- OOD PICP ≥ 0.98（四模型、四 OOD 特征）
- OOD MAE 比 in-dist 升高 3–12%
- ⚠️ **OOD R² > in-dist R² 不是"泛化更好"**（SST 差异所致）

## 二、与 CLAUDE.md memory 冲突点（需用户授权后更新 memory）

| memory 原值 | bnn0414 新值 | 处置 |
|---|---|---|
| Sobol stress E_intercept S₁ = 0.598 | 0.582 (baseline) / 0.558 (data-mono-ineq) | 更新 `project_sobol_canonical.md` |
| Posterior phy-mono coverage 0.875 | 0.917 | 更新 `project_posterior_canonical.md` |
| Posterior phy-mono acceptance 0.47–0.61 | 0.582–0.621 | 更新 |
| "high-stress P>131 = 0.63–1.0" | feasible_region 无 high 子集，待从 benchmark_summary 重算 | 标记待核实 |

## 三、正文建议修改位（待与用户确认后落笔）
待和用户确认后再改：
- §3（performance / accuracy）：用上面表替换旧 5-seed 数字
- §4（speed）：替换 speedup 数值
- §5（sensitivity）：用新 S₁ 区间
- §6（risk propagation）：替换 P>131 值、σ_k 扫描表
- §7（posterior）：acceptance / coverage 更新，**删除或改写任何"HF rerun 已验证"表述**
- 附录 E：放 4 模型完整消融表、4 OOD 特征完整结果、阈值扫描 110/120/131

## 四、依然缺失 / 风险项
1. ~~HF rerun 未完成~~ → phy-mono 54/54 已完成；data-mono-ineq 仅写 input，如需可后续补跑
2. run_record_20260415_235341 把 physics_consistency 与 figures 标 fail：需要看 log 判定是出图失败还是模块失败
3. feasible_region.csv 高应力类别缺失：需要补一步 high-stress 子集分析
4. 阈值风险无 bootstrap CI：可事后手算或重跑加 CI
