# v3418 Experiment Registry

> 本文件记录 v3418 数据集（n=3341, split seed=2026）上所有已完成和待补实验。
> 更新日期：2026-04-19

## 数据集信息

| 字段 | 值 |
|---|---|
| CSV | `dataset_v3_updated.csv` (服务器: `dataset_v3.csv`) |
| n_total | 3341 |
| n_train / n_val / n_test | 2339 / 501 / 501 |
| split seed | 2026 |
| rerun_tag | v3418 |

## 模型清单

| 模型 ID | 训练日期 | Checkpoint | Optuna trials | 角色 |
|---|---|---|---|---|
| bnn-baseline | 2026-04-18 | ✅ `checkpoint_bnn-baseline_fixed.pt` | best_params in manifest | 主对比基线 |
| bnn-phy-mono | 2026-04-18 | ✅ `checkpoint_bnn-phy-mono_fixed.pt` | best_params in manifest | **主模型** |
| bnn-baseline-homo | 2026-04-18 | ✅ `checkpoint_bnn-baseline-homo_fixed.pt` | best_params in manifest | 消融：同方差 |
| bnn-mf-hybrid | 2026-04-18~19 | ✅ `checkpoint_bnn-mf-hybrid_fixed.pt` | best_params in manifest | 消融：多保真 |

## 已完成实验

### Phase 1: Fixed-split 评估（精度）
| 模型 | 状态 | 输出文件 | stress R² | keff R² |
|---|---|---|---|---|
| bnn-baseline | ✅ 完成 | `models/bnn-baseline/fixed_eval/metrics_per_output_fixed.csv` | 0.9418 | 0.8445 |
| bnn-phy-mono | ✅ 完成 | `models/bnn-phy-mono/fixed_eval/metrics_per_output_fixed.csv` | 0.9438 | 0.8492 |
| bnn-baseline-homo | ✅ 完成 | `models/bnn-baseline-homo/fixed_eval/metrics_per_output_fixed.csv` | 0.9402 | 0.8327 |
| bnn-mf-hybrid | ✅ 完成 | `models/bnn-mf-hybrid/fixed_eval/metrics_per_output_fixed.csv` | 0.9417 | 0.8110 |

### Phase 2: Forward Risk Propagation
| 模型 | 状态 | 输出文件 | P>131@σ_k=1.0 |
|---|---|---|---|
| bnn-baseline | ✅ 完成 | `experiments/risk_propagation/bnn-baseline/D1_nominal_risk.json` | 0.8445 |
| bnn-phy-mono | ✅ 完成 | `experiments/risk_propagation/bnn-phy-mono/D1_nominal_risk.json` | 0.8357 |
| bnn-baseline-homo | ✅ 完成 | `experiments/risk_propagation/bnn-baseline-homo/D1_nominal_risk.json` | 0.8343 |
| bnn-mf-hybrid | ✅ 完成 | `experiments/risk_propagation/bnn-mf-hybrid/D1_nominal_risk.json` | 0.8341 |

### Phase 3: Sobol Sensitivity
| 模型 | 状态 | 输出文件 | stress E_int S₁ | keff α_base S₁ |
|---|---|---|---|---|
| bnn-baseline | ✅ 完成 | `experiments/sensitivity/bnn-baseline/sobol_results.csv` | 0.600 | 0.787 |
| bnn-phy-mono | ✅ 完成 | `experiments/sensitivity/bnn-phy-mono/sobol_results.csv` | 0.579 | 0.785 |
| bnn-mf-hybrid | ✅ 完成 | `experiments/sensitivity/bnn-mf-hybrid/sobol_results.csv` | 0.580 | 0.734 |

### Phase 5: OOD Generalization
| 模型 | 状态 | 输出文件 |
|---|---|---|
| bnn-baseline | ✅ 完成 | `experiments/generalization/bnn-baseline/ood_summary.csv` |
| bnn-phy-mono | ✅ 完成 | `experiments/generalization/bnn-phy-mono/ood_summary.csv` |
| bnn-mf-hybrid | ✅ 完成 | `experiments/generalization/bnn-mf-hybrid/ood_summary.csv` |

### Phase 6: Speed Benchmark
| 模型 | 状态 | 输出文件 | speedup (single MC) |
|---|---|---|---|
| bnn-baseline | ✅ 完成 | `experiments/computational_speedup/bnn-baseline/bnn_speed_benchmark.json` | 143,237× |
| bnn-mf-hybrid | ✅ 完成 | `experiments/computational_speedup/bnn-mf-hybrid/bnn_speed_benchmark.json` | 42,467× |

### Phase 7: Posterior Calibration (MCMC)
| 模型 | 状态 | 输出文件 | acceptance | 90CI coverage |
|---|---|---|---|---|
| bnn-baseline | ✅ 完成 | `experiments/posterior/bnn-baseline/benchmark_summary.csv` | 0.566–0.631 | 0.875 |
| bnn-phy-mono | ✅ 完成 | `experiments/posterior/bnn-phy-mono/benchmark_summary.csv` | 0.580–0.640 | 0.861 |
| bnn-mf-hybrid | ✅ 完成 | `experiments/posterior/bnn-mf-hybrid/benchmark_summary.csv` | — | 0.861 |

### Small-sample Data Efficiency
| 模型 | 状态 | fractions | 输出文件 |
|---|---|---|---|
| bnn-baseline | ✅ 完成 | 0.2, 0.4, 0.6 | `experiments/small_sample/bnn-baseline/frac_*/metrics.json` |
| bnn-mf-hybrid | ✅ 完成 | 0.2, 0.4, 0.6 | `experiments/small_sample/bnn-mf-hybrid/frac_*/metrics.json` |

### Analysis (post-processing)
| 分析 | 状态 | 输出文件 |
|---|---|---|
| Comprehensive comparison | ✅ 完成 | `analysis/comprehensive_comparison_v3418.txt` |
| Conformal calibration | ✅ 完成 | `analysis/conformal_calibration.csv` |
| Near-threshold calibration | ✅ 完成 | `analysis/near_threshold_calibration.csv` |

---

## 补充实验（2026-04-19 完成）

### P1: 5-seed 重复评估 ✅
- **完成日期**：2026-04-19
- **模型**：bnn-baseline, bnn-phy-mono, bnn-data-mono, bnn-data-mono-ineq (各 5 seeds: 2026–2030)
- **输出**：`models/<model_id>/repeat_eval/repeat_summary.csv`
- **汇总**：`results/accuracy/repeat_eval_global_summary.csv`
- **关键结果**：

| 模型 | RMSE (mean±std) | R² (mean±std) | CRPS (mean±std) | PICP (mean±std) |
|---|---|---|---|---|
| bnn-baseline | 3.42±0.14 | 0.744±0.048 | 1.97±0.07 | 0.976±0.005 |
| bnn-phy-mono | 3.41±0.13 | 0.747±0.050 | 1.92±0.07 | 0.970±0.006 |
| bnn-data-mono | 3.43±0.12 | 0.746±0.049 | 2.01±0.06 | 0.976±0.006 |
| bnn-data-mono-ineq | 3.53±0.11 | 0.733±0.047 | 2.21±0.06 | 0.986±0.003 |

- **注意**：使用现有 checkpoint 在不同 split 上评估（非重新训练），因 overwrite guard 阻止了重新训练

### P2: External baselines ✅
- **完成日期**：2026-04-19
- **模型**：mc-dropout, deep-ensemble（在 v3418 split 上训练+评估）
- **输出**：`models/mc-dropout/`, `models/deep-ensemble/`, `models/external_baselines_summary.json`
- **UQ scoring**：`results/accuracy/external_baseline_scoring.csv`
- **关键结果（stress）**：

| 模型 | stress RMSE | stress R² | stress CRPS | keff R² |
|---|---|---|---|---|
| MC-Dropout | 7.66 | 0.934 | 4.52 | 0.856 |
| Deep Ensemble | 7.64 | 0.934 | 4.50 | 0.828 |
| BNN-baseline | 7.18 | 0.942 | 4.35 | 0.845 |
| BNN-phy-mono | 7.06 | 0.944 | 4.24 | 0.849 |

### P3: Physics consistency ✅
- **完成日期**：2026-04-19
- **输出（单调性）**：`results/physics_consistency/monotonicity_violation_rate.csv`
- **输出（梯度一致性）**：`results_v3418/experiments/physics_consistency/bnn-phy-mono/`
- **关键结果**：4 模型 monotonicity + inequality violation rates 已计算

### P4: Uncertainty decomposition ✅
- **完成日期**：2026-04-19
- **模型**：bnn-baseline, bnn-phy-mono, bnn-data-mono, bnn-data-mono-ineq
- **输出**：`results/uncertainty_decomposition/uncertainty_decomposition.csv`
- **关键结果（stress epistemic fraction）**：

| 模型 | frac_epistemic (stress) |
|---|---|
| bnn-baseline | 0.300 |
| bnn-phy-mono | 0.314 |
| bnn-data-mono | 0.343 |
| bnn-data-mono-ineq | 0.285 |

### P5: Calibration scoring rules ❌ 部分失败
- **状态**：因 bnn-data-mono 缺少 test_predictions_fixed.json 而报错
- **已有替代**：conformal calibration 已完成（analysis/conformal_calibration.csv）

### 仍可选补充
| 实验 | 优先级 | 状态 |
|---|---|---|
| bnn-phy-mono speed benchmark | 低 | ❌ 架构同 baseline，可引用 |
| bnn-phy-mono small-sample | 低 | ❌ 附录内容 |
| P5 calibration fix (skip missing models) | 低 | ❌ 有 conformal 替代 |
