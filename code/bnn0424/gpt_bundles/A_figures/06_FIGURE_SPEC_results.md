# 画图规格书 — BNN Surrogate Paper Figures

> 本文档供画图对话使用。每张图给出：数据源、布局、要点、vocabulary 约束。
> 所有数据已在本地 `bnn0414/results/` 或 `bnn0414/code/` 下。
> **Figure vocabulary**: 禁用 iter2/level0/baseline/data-mono-ineq 等内部 ID，禁 CJK。

---

## 通用约定

- **主线对比**: Reference BNN (bnn-baseline) vs Physics-regularized BNN (bnn-phy-mono)
- **附录扩展**: + Data-monotone BNN, Data+inequality BNN, MC-Dropout, Deep Ensemble
- **颜色建议**: baseline=#1f77b4, phy-mono=#d62728, data-mono=#2ca02c, data-mono-ineq=#9467bd, mc-dropout=#8c564b, ensemble=#e377c2
- **字体**: sans-serif, ≥8pt for labels
- **格式**: 同时存 PDF + PNG (dpi≥300)

---

## Fig 1: Prediction Accuracy & Calibration (主文)

### 布局: 2×3 or 3-row composite

**Panel A: Reliability diagram (2 models)**
- 数据源: `results/accuracy/calibration_multi_alpha.csv`
  - columns: model_id, output, nominal_alpha, empirical_coverage
- 布局: 2 子图 (baseline vs phy-mono), 每个 5 条线 (5 primary outputs)
- X: nominal coverage (0.5–0.99), Y: empirical coverage
- 对角线虚线 = 完美校准
- 已有图可参考: `results/accuracy/reliability_bnn-baseline.png`

**Panel B: PIT histogram (2 models)**
- 数据源: `results/accuracy/pit_values.npz`
  - 加载: `np.load(path)`, keys 为 model_id, 每个是 (N_test, N_outputs) array
- 布局: 选 1-2 个关键输出 (stress + keff)
- 理想 = 均匀分布, 水平参考线 y=1
- 已有图可参考: `results/accuracy/pit_bnn-phy-mono.png`

**Panel C: Scoring rules 对比 bar chart (6 models × 2-3 metrics)**
- 数据源: `results/master_comparison_table.csv`
- 建议 grouped bar: stress 和 keff 各一组
- 指标: CRPS + ECE (或 NLL)
- 6 models: 4 BNN + MC-Dropout + Deep Ensemble

**Panel D (optional): 6-model RMSE 对比**
- 同上数据源
- per-output grouped bar
- 突出 BNN 在温度上 RMSE 几乎是外部基线一半

### 关键数值标注
- phy-mono stress ECE = 0.106 (最低)
- BNN fuel temp RMSE ≈ 4.26 vs MC-Dropout 4.50 vs Ensemble 4.49
- BNN keff R2 ≈ 0.63 vs MC-Dropout 0.86 vs Ensemble 0.83
  **注意**: keff 的 R2 外部基线反而更高！但 CRPS 和 NLL 差不多。需要决定是否展示 keff R2。

---

## Fig 2: Physics Consistency (主文)

### 布局: 1×2 or 1×3

**Panel A: Monotonicity violation rate heatmap**
- 数据源: `results/physics_consistency/monotonicity_violation_rate.csv`
- 布局: heatmap, rows = input-output pairs, cols = 4 BNN models
- 颜色: 0% = 绿/白, >0% = 红色渐变
- 只展示 primary output 的行
- 关键: 几乎全 0%, 唯一例外是 SS316_alpha→fuel_temp (~36-54%, medium confidence)
- 已有图: `results/physics_consistency/monotonicity_violation_primary.png`

**Panel B: Uncertainty decomposition stacked bar**
- 数据源: `results/uncertainty_decomposition/uncertainty_decomposition.csv`
- columns: model_id, output_label, frac_epistemic_mean
- 布局: 2 模型 (baseline, phy-mono) × 5 outputs
- 蓝 = epistemic, 橙 = aleatoric
- 已有图: `results/uncertainty_decomposition/uncertainty_decomposition_bar.png`

**Panel C (optional): Epistemic vs aleatoric scatter**
- 已有图: `results/uncertainty_decomposition/epi_vs_ale_scatter_bnn-phy-mono.png`
- 每个 test sample 一个点, X=aleatoric std, Y=epistemic std
- 对角线 = equal contribution

---

## Fig 3: Posterior Inference (主文)

### 布局: 2×2 or composite

**Panel A: MCMC trace plot (1 representative case)**
- 数据源: chain .npz at `code/experiments_0404/experiments/posterior/bnn-phy-mono/diagnostics/chains/case_06.npz`
  - 加载: `d = np.load(path, allow_pickle=True)`; `d['chains']` shape (4, 1200, 4), `d['param_names']`
- 建议用 case_06 (near-threshold stress category)
- 4 chains 叠加, 4 参数分行
- 已有图: `results/posterior/trace_bnn-phy-mono_case06.png`

**Panel B: Rank plot (same case)**
- 已有图: `results/posterior/rank_bnn-phy-mono_case06.png`

**Panel C: Posterior contraction (prior vs posterior marginals)**
- 数据源: 同上 chain .npz
- prior = `d['param_names']` 对应的先验分布 (Normal, 从 experiment_config 获取)
- posterior = KDE of pooled chains
- 建议 2×2 子图 (4 params), 每个叠加 prior (虚线) + posterior (实线)
- **需要新画** — 现有图中没有 prior vs posterior 对比

**Panel D: Diagnostics summary**
- 数据源: `code/experiments_0404/experiments/posterior/bnn-phy-mono/diagnostics/mcmc_diagnostics.csv`
- 可做 scatter: X=case_idx, Y=rhat 或 ESS, 分参数
- 或 简洁 table

---

## Fig 4: Computational Efficiency (主文)

### 布局: 1×2

**Panel A: Budget-matched risk curve**
- 数据源: `results/speed/budget_matched_risk.csv`
- X: CI half-width (0.001–0.05, log scale)
- Y: total time (seconds, log scale)
- 两条线: HF (linear growth) vs BNN (near-zero)
- 已有图: `results/speed/budget_matched_risk.png`
- 标注 headline: "speedup ≈ 1.7×10⁸"

**Panel B: Data efficiency curve**
- 数据源: `results/data_efficiency/data_efficiency_summary.csv`
- X: training fraction (0.25, 0.5, 0.75, 1.0)
- Y: RMSE (with error bars from 2 seeds)
- 两条线: baseline vs phy-mono
- 已有图: `results/data_efficiency/data_efficiency_curve.png`

---

## Fig S1: Sobol Sensitivity Convergence (Supplementary)

- 数据源: `results/sensitivity/sobol_convergence.csv`
  - columns: model_id, output, input, N_base, S1_mean, S1_std, S1_ci_lo, S1_ci_hi
- 布局: 2×2 (2 models × 2 outputs)
- X: N_base (256–8192, log2 scale)
- Y: S₁ with error bars (ci_lo, ci_hi)
- 每个 subplot 3 lines (top-3 inputs)
- 已有图: `results/sensitivity/sobol_convergence_bnn-phy-mono_stress.png` 等

---

## Fig S2: Prior Sensitivity (Supplementary)

- 数据源: `code/experiments_0404/experiments/posterior/bnn-phy-mono/prior_sensitivity/prior_sensitivity_summary.csv`
- 布局建议: grouped bar or heatmap
  - rows = 6 prior variants (canonical, diffuse, tight, flat, shift_pos, shift_neg)
  - cols = 4 params
  - 色值 = KL divergence vs canonical, or coverage
- 关键: tight coverage 降至 50%, 其他均 ≥83%
- 已有图 (单模型): `posterior/bnn-phy-mono/prior_sensitivity/prior_sensitivity_bnn-phy-mono.png`

---

## Fig S3: Noise Sensitivity (Supplementary)

- 数据源: `code/experiments_0404/experiments/posterior/bnn-phy-mono/noise_sensitivity/noise_sensitivity_summary.csv`
- 布局: line plot
  - X: noise_frac (0.005–0.10)
  - Y: posterior std (4 lines for 4 params) 或 CI width
- 第二 panel: acceptance rate vs noise_frac
- 已有图 (单模型): `posterior/bnn-phy-mono/noise_sensitivity/noise_sensitivity_bnn-phy-mono.png`

---

## Fig S4: OOD Calibration (Supplementary)

- 数据源: `results/ood/ood_calibration_comparison.csv`
- Panel A: epistemic inflation bar (4 models × 4 OOD features)
  - 已有图: `results/ood/ood_epistemic_ratio.png`
- Panel B: PICP in-dist vs OOD (2 models)
  - 已有图: `results/ood/ood_coverage_comparison.png`

---

## Fig S5: External Baseline Calibration (Supplementary)

- 数据源: `results/accuracy/external_baseline_calibration.csv`
- Panel A: reliability diagrams for MC-Dropout + Deep Ensemble
  - 已有图: `results/accuracy/reliability_mc-dropout.png`, `reliability_deep-ensemble.png`
- Panel B: PIT histograms
  - 已有图: `results/accuracy/pit_mc-dropout.png`, `pit_deep-ensemble.png`

---

## Table 1: Master Comparison Table (主文)

- 数据源: `results/master_comparison_table.csv`
- 6 models × 5 outputs × (RMSE, R2, CRPS, ECE, PICP)
- BNN 行用 mean±std (5-seed), 外部基线无 CI
- 加粗每列最优值
- 推荐分两个 sub-table: 上半 point prediction (RMSE, R2), 下半 UQ metrics (CRPS, ECE, PICP)

---

## Table 2: MCMC Diagnostics Summary (主文或 Supplementary)

- 数据源: `code/experiments_0404/experiments/posterior/{model}/diagnostics/mcmc_diagnostics.csv`
- 汇总: per model, report mean/max rhat, min/mean ESS, mean accept rate
- 4 models × 18 cases each

---

## 文件路径索引

```
results/
├── master_comparison_table.csv          ← Table 1 数据源
├── accuracy/
│   ├── calibration_multi_alpha.csv      ← Fig 1A
│   ├── pit_values.npz                   ← Fig 1B
│   ├── scoring_rules.csv                ← Fig 1C
│   ├── repeat_eval_*.csv                ← Table 1
│   ├── external_baseline_*.csv          ← Table 1, Fig S5
│   ├── reliability_*.png                ← Fig 1A reference
│   └── pit_*.png                        ← Fig 1B reference
├── physics_consistency/
│   ├── monotonicity_violation_rate.csv  ← Fig 2A
│   └── inequality_violation_rate.csv    ← Fig 2A
├── uncertainty_decomposition/
│   ├── uncertainty_decomposition.csv    ← Fig 2B
│   └── *.png                            ← Fig 2B/C reference
├── speed/
│   ├── budget_matched_risk.csv          ← Fig 4A
│   └── budget_matched_risk.png          ← Fig 4A reference
├── data_efficiency/
│   ├── data_efficiency_summary.csv      ← Fig 4B
│   └── data_efficiency_curve.png        ← Fig 4B reference
├── sensitivity/
│   ├── sobol_convergence.csv            ← Fig S1
│   └── sobol_convergence_*.png          ← Fig S1 reference
├── ood/
│   ├── ood_calibration_comparison.csv   ← Fig S4
│   └── *.png                            ← Fig S4 reference
├── posterior/
│   ├── trace_*.png                      ← Fig 3A reference
│   └── rank_*.png                       ← Fig 3B reference
└── EXPERIMENT_CONCLUSIONS_OVERVIEW.md
    EXPERIMENT_DETAILS.md

code/experiments_0404/experiments/posterior/
├── bnn-phy-mono/
│   ├── diagnostics/
│   │   ├── mcmc_diagnostics.csv         ← Table 2, Fig 3D
│   │   └── chains/case_*.npz           ← Fig 3A/B/C raw data
│   ├── prior_sensitivity/
│   │   └── prior_sensitivity_summary.csv ← Fig S2
│   └── noise_sensitivity/
│       └── noise_sensitivity_summary.csv ← Fig S3
└── bnn-baseline/diagnostics/...
```
