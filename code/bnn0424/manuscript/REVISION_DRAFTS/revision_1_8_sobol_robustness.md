# Phase 1.8 — Sobol Robustness: Cross-Method Validation

> Data source: server `experiments/sensitivity/bnn-phy-mono/{spearman,prcc}_results.csv`
> Sobol source: `CANONICAL_DATA_SUMMARY.md §5a-5b`

## Cross-method sensitivity ranking comparison

### Stress (iteration2_max_global_stress)

| Rank | Sobol S₁ | Spearman |ρ| | PRCC |r| |
|------|----------|----------|------|
| 1 | E_intercept (0.579) | E_intercept (0.782) | E_intercept (0.926) |
| 2 | alpha_base (0.169) | alpha_base (0.293) | alpha_base (0.728) |
| 3 | nu (0.065) | E_slope (0.203) | E_slope (0.566) |
| 4 | SS316_k_ref (0.051) | alpha_slope (0.193) | nu (0.562) |
| 5 | E_slope (0.050) | nu (0.180) | SS316_k_ref (0.554) |

### keff (iteration2_keff)

| Rank | Sobol S₁ | Spearman |ρ| | PRCC |r| |
|------|----------|----------|------|
| 1 | alpha_base (0.785) | alpha_base (0.800) | alpha_base (0.883) |
| 2 | alpha_slope (0.179) | alpha_slope (0.417) | alpha_slope (0.708) |
| 3 | nu (0.028) | E_slope (0.067) | nu (0.190) |

### Key findings

1. **Top-2 ranking identical across all three methods** for both stress and keff
2. **E_intercept dominates stress** in all methods (Sobol S₁=0.58, Spearman=0.78, PRCC=0.93)
3. **alpha_base dominates keff** in all methods (Sobol S₁=0.79, Spearman=0.80, PRCC=0.88)
4. **SS316_alpha negligible** in all methods (Sobol CI spans zero, Spearman p>0.05)

## Draft SI paragraph (EN)

**Supplementary Note: Sensitivity ranking robustness**

To verify that the Sobol-based sensitivity rankings are not artefacts of the surrogate
model, we compared the variance-based Sobol first-order indices with two nonparametric
rank-based methods — Spearman rank correlation and partial rank correlation coefficients
(PRCC) — evaluated on the training data (Supplementary Table SX). For stress, all three
methods identify E_intercept as the dominant contributor (Sobol S₁ = 0.58, Spearman
|ρ| = 0.78, PRCC |r| = 0.93) and alpha_base as the second contributor (Sobol S₁ = 0.17,
Spearman |ρ| = 0.29, PRCC |r| = 0.73). For k_eff, all three methods identify alpha_base
as dominant (Sobol S₁ = 0.79, Spearman |ρ| = 0.80, PRCC |r| = 0.88) and alpha_slope as
second (Sobol S₁ = 0.18, Spearman |ρ| = 0.42, PRCC |r| = 0.71). The top-two rankings
are identical across all three methods for both outputs, supporting the conclusion that the
dominant-factor separation between stress and k_eff reflects genuine parametric sensitivity
rather than surrogate-specific artefacts. The Sobol analysis additionally provides
higher-order interaction quantification (total-order minus first-order gap) that rank-based
methods cannot supply.

## Draft SI paragraph (CN)

**补充说明：敏感性排序稳健性验证**

为验证基于方差的 Sobol 敏感性排序并非代理模型的伪影，我们将 Sobol 一阶指数与两种
非参数秩相关方法——Spearman 秩相关和偏秩相关系数（PRCC）——进行了对比，后两者直接
在训练数据上计算（补充表 SX）。对于应力，三种方法均识别 E_intercept 为主导因素
（Sobol S₁ = 0.58，Spearman |ρ| = 0.78，PRCC |r| = 0.93），alpha_base 为次要
因素（Sobol S₁ = 0.17，Spearman |ρ| = 0.29，PRCC |r| = 0.73）。对于 k_eff，三
种方法均识别 alpha_base 为主导（Sobol S₁ = 0.79，Spearman |ρ| = 0.80，PRCC
|r| = 0.88），alpha_slope 为次要（Sobol S₁ = 0.18，Spearman |ρ| = 0.42，PRCC
|r| = 0.71）。两个输出量的前两位排序在三种方法间完全一致，表明应力与 k_eff 之间
主导因素的分离反映了真实的参数敏感性结构，而非特定代理模型的偏差。Sobol 分析还能提
供秩相关方法无法给出的高阶交互量化信息（总阶与一阶指数之差）。

## One-sentence summary for main text

"The dominant-factor rankings are robust to the choice of sensitivity method: Spearman
rank correlation and partial rank correlation coefficients reproduce the same top-two
parameter rankings for both stress and k_eff (Supplementary Table SX)."

## Data Sources
- `code/experiments/sensitivity/bnn-phy-mono/spearman_results.csv` — Spearman rank correlations
- `code/experiments/sensitivity/bnn-phy-mono/prcc_results.csv` — PRCC values
- `code/gpt_figures/fig4_sobol/sobol_indices_summary.csv` — Sobol S₁ values
- `results/CANONICAL_DATA_SUMMARY.md` — canonical Sobol values
