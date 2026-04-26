# Phase 1.6 — Posterior Coverage Honest Discussion

## Data Summary

| Stress category | Cases | In 90% CI | Coverage |
|----------------|-------|-----------|----------|
| Low (<120 MPa) | 6 (24 params) | 16 | 0.667 |
| Near (120–131 MPa) | 6 (24 params) | 24 | 1.000 |
| High (>131 MPa) | 6 (24 params) | 22 | 0.917 |
| **Overall** | **18 (72 params)** | **62** | **0.861** |

### Low-stress misses detail

| Case | Param | True value | Post mean | Rel bias |
|------|-------|-----------|-----------|----------|
| 0 | SS316_k_ref | 28.13 | 24.50 | -0.129 |
| 2 | E_intercept | 148.9B | 173.6B | +0.166 |
| 2 | alpha_base | 1.18e-5 | 9.05e-6 | -0.234 |
| 2 | SS316_k_ref | 19.66 | 24.10 | +0.226 |
| 3 | alpha_slope | 5.75e-9 | 4.81e-9 | -0.164 |
| 4 | E_intercept | 148.2B | 172.5B | +0.164 |
| 4 | alpha_base | 1.10e-5 | 9.14e-6 | -0.167 |
| 5 | alpha_base | 7.57e-6 | 9.51e-6 | +0.257 |

**Root cause pattern:** Misses are NOT concentrated on a single parameter. They are distributed across all 4 parameters (E_intercept: 2, alpha_base: 3, alpha_slope: 1, SS316_k_ref: 2). Cases 2 and 4 have the most misses (3 and 2 respectively) and correspond to extreme true parameter values far from the training distribution center. The posterior systematically regresses toward the prior mean for these extreme cases.

---

## EN — Results Section 2.4: Stratified Coverage Report

The 90% credible interval coverage of the posterior calibration exhibits pronounced stress-regime dependence (Table X). Across 18 benchmark cases (6 per stress category), the overall parameter-level coverage is 0.861 (62/72). However, the near-threshold regime (120–131 MPa) achieves perfect coverage (1.000), while the high-stress regime reaches 0.917, and the low-stress regime falls to 0.667.

Analysis of the 8 low-stress misses reveals that they are distributed across all four calibration parameters rather than concentrated on any single one: E_intercept (2 misses), alpha_base (3), alpha_slope (1), and SS316_k_ref (2). The two most affected cases (Cases 2 and 4) share a common feature: their true E_intercept values (~149 GPa) lie substantially below the prior mean (~200 GPa), and their true alpha_base values (~1.1–1.2 × 10⁻⁵ K⁻¹) deviate from the nominal range. In both cases, the posterior mean regresses toward the center of the prior, with relative biases exceeding 16%.

This behavior is consistent with a known property of likelihood-based inference through surrogate models: when the surrogate's predictive sensitivity to a parameter is weak — as occurs in the low-stress regime where absolute stress magnitudes are small and the output landscape is relatively flat — the posterior is dominated by the prior rather than the data. The BNN's epistemic uncertainty, while well-calibrated in the predictive space (CRPS = 4.35 MPa), does not fully compensate for the reduced Fisher information in these regions.

Importantly, this miscoverage does not compromise the framework's primary engineering objective. The near-threshold and high-stress regimes — precisely the cases where accurate posterior inference matters for structural integrity assessment — achieve 1.000 and 0.917 coverage, respectively. For the low-stress regime, the posterior correctly identifies all cases as low-risk (P(sigma > 131 MPa) < 0.05), so the practical consequence of the bias is limited.

## EN — Limitations Item

The posterior calibration coverage shows stress-regime dependence, with the low-stress category achieving 0.667 coverage versus 1.000 for near-threshold cases. This reflects the reduced sensitivity of the coupled thermo-mechanical response to input parameter variations in the low-stress regime, which limits the information content of the observations and causes the posterior to default toward the prior. Future work could address this through informative prior elicitation or augmented likelihood formulations that increase sensitivity in flat regions of the output space.

---

## CN — Results Section 2.4: Stratified Coverage Report

后验标定的90%可信区间覆盖率呈现显著的应力分区依赖性（表X）。在18个基准案例（每个应力类别6个）中，参数层面的总体覆盖率为0.861（62/72）。然而，近阈值区间（120–131 MPa）的覆盖率达到1.000，高应力区间为0.917，而低应力区间仅为0.667。

对低应力区间8次覆盖失败的分析表明，这些偏差并非集中于某一参数，而是分布在全部四个标定参数上：E_intercept（2次）、alpha_base（3次）、alpha_slope（1次）、SS316_k_ref（2次）。受影响最严重的两个案例（案例2和4）具有共同特征：其真实E_intercept值（约149 GPa）显著低于先验均值（约200 GPa），alpha_base值也偏离了标称范围。在这两个案例中，后验均值均向先验中心回归，相对偏差超过16%。

这一现象与基于代理模型的似然推断的已知性质一致：当代理模型对某参数的预测敏感度较弱时——低应力区间中绝对应力量值较小、输出景观相对平坦——后验分布会被先验主导而非被数据更新。BNN的认知不确定性虽然在预测空间中标定良好（CRPS = 4.35 MPa），但无法完全弥补这些区域中Fisher信息量的不足。

值得强调的是，这一覆盖率偏低并未影响框架的核心工程目标。近阈值和高应力区间——正是结构完整性评估中后验推断准确性至关重要的区域——分别达到了1.000和0.917的覆盖率。对于低应力区间，后验分布正确地将所有案例识别为低风险（P(sigma > 131 MPa) < 0.05），因此偏差的实际后果有限。

## CN — Limitations Item

后验标定覆盖率呈现应力分区依赖性，低应力类别覆盖率为0.667，而近阈值类别为1.000。这反映了在低应力区间，耦合热-力响应对输入参数变化的敏感度降低，限制了观测数据的信息含量，导致后验分布趋向先验。未来工作可通过信息性先验构建或增强似然函数等策略，提高输出空间平坦区域的参数敏感度。

---

## Data Sources
- `code/experiments/posterior/bnn-phy-mono/rerun_4chain/benchmark_summary.csv` — per-case, per-parameter coverage (in_90ci), bias, rhat
- `results/CANONICAL_DATA_SUMMARY.md` — overall coverage 0.861, acceptance rates 0.58–0.63
