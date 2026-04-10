# 结果溯源审计

**最后更新**：2026-04-05  
**目的**：厘清每张结果表的来源脚本、输入 artifact、输出定义、可信度，并标记已知不一致。

---

## 一、已知重大不一致

### 1.1 stress R² = 0.929 vs 0.089（同一模型，两张表）

⚠️ **2026-04-09 STATUS：paper_fixed_model_compare_*.csv 已明确作废，禁止任何引用**

| 表 | stress RMSE | stress R² | 来源 |
|---|---|---|---|
| `paper_focus_metrics_level0.csv`（canonical subdir） | 7.93 MPa | **0.929** | 训练时保存的 `test_predictions_level0.json` |
| `paper_fixed_model_compare_per_output.csv` | 27.66 MPa | **0.089** | ❌ **DEPRECATED** — 列对齐错误，output column mismatch，不能使用 |

**根本原因（已确认）**：
`run_compare_fixed_models.py` 重跑 inference 时，从 `fixed_split/test.csv` 读取测试数据后与模型输出比较。推断问题在于 **输出列对齐错误**：该脚本的 `OUTPUT_COLS` 定义与训练时不一致，导致预测值和真值配对错乱。证据：`iteration1_keff` 的 R² = -3.52×10²⁵（负无穷量级），这只可能在预测完全对应到错误目标列时出现。

**结论**：
- ✅ **`test_predictions_level0.json` 生成的结果可信**（训练脚本在同一过程内保存，列对齐有保证）
- ❌ **`paper_fixed_model_compare_*.csv` 全部作废，未来任何新分析禁止使用该脚本**

### 1.2 RMSE_mean_primary = 3.52 vs 7.77（同一模型，两张表）

| 表 | RMSE_mean_primary | 来源 | 空间 |
|---|---|---|---|
| `paper_metrics_table.csv` | **3.52** | `run_phys_levels_main.py` | 原始单位，但 5 个输出算术平均（MPa + K + mm + keff 混合） |
| `paper_fixed_model_compare_summary.csv` | **7.77** | `run_compare_fixed_models.py` | 原始单位，同样混合平均 |

**根本原因**：  
两者都是跨单位混合平均，物理上无意义。数值不同的根本原因同 1.1：`paper_fixed_model_compare` 用了错误的列对齐，因此每个输出的 RMSE 都是乱的，平均后偏大。

**结论**：  
- `paper_metrics_table.csv` RMSE_mean_primary = 3.52 是"用可信预测值计算的跨单位平均"，但本身没有物理意义，不应作为论文主要指标
- **正确的论文指标应逐输出报告**，或在标准化空间报告 NLL

---

## 二、各结果文件溯源表

### 旧体系 `experiments_phys_levels/`

| 文件 | 生成脚本 | 测试集 | 推断方式 | 输出空间 | 可信度 | 备注 |
|---|---|---|---|---|---|---|
| `fixed_surrogate_fixed_base/test_predictions_level0.json` | `run_phys_levels_main.py` | `fixed_split/test.csv`（435条） | 训练过程中保存 | 原始单位（inverse_transform） | ✅ **可信** | 列对齐有保证 |
| `fixed_surrogate_fixed_level2/test_predictions_level2.json` | `run_phys_levels_main.py` | 同上 | 同上 | 原始单位 | ✅ **可信** | 同上 |
| `fixed_surrogate_fixed_base/paper_focus_metrics_level0.csv` | `run_phys_levels_main.py` | 同上 | 从上述 JSON 计算 | 原始单位，逐输出 | ✅ **可信** | 主文指标来源 |
| `fixed_surrogate_fixed_level2/paper_focus_metrics_level2.csv` | 同上 | 同上 | 同上 | 同上 | ✅ **可信** | 同上 |
| `paper_metrics_table.csv` | `run_phys_levels_main.py` | 同上 | 从 test_predictions 计算 | 原始单位跨输出平均 | ⚠️ 数字可信，但指标无物理意义 | RMSE_mean_primary 是混合单位均值 |
| `paper_fixed_model_compare_summary.csv` | `run_compare_fixed_models.py` | `fixed_split/test.csv` | **重新运行 inference** | 原始单位 | ❌ **不可信** | 列对齐错误，所有数字作废 |
| `paper_fixed_model_compare_per_output.csv` | 同上 | 同上 | 同上 | 同上 | ❌ **不可信** | 同上 |
| `paper_fixed_model_compare_primary.csv` | 同上 | 同上 | 同上 | 同上 | ❌ **不可信** | 同上 |
| `paper_sobol_results_with_ci.csv` | `run_sobol_analysis.py` 等 | 代理模型预测 | 基于代理均值 | 标准化空间的 Sobol 指数 | ✅ **可信** | 用于主文 Sobol 图 |
| `paper_forward_uq_summary.csv` | 旧 forward UQ 脚本 | 代理预测分布 | 20k 蒙特卡洛样本 | 原始单位统计量 | ✅ **可信** | 含均值/方差/失效概率 |
| `paper_ood_multi_feature_summary.csv` | `run_ood_multi_feature.py` | OOD 划分 | 从 test_predictions 重算 | 原始单位 | ⚠️ 需核实列对齐 | 参考 1.1 的风险 |
| `paper_posterior_hf_validation_summary_reduced_maintext.csv` | `run_posterior_hf_validation.py` | HF 近邻代理 | 后验预测 | 原始单位 | ✅ **可信** | 明确标注为 nearest-neighbour proxy |
| `paper_extreme_stress_risk_assessment.csv` | `run_extreme_scenario_benchmark.py` | 高应力 case | MCMC 后验推断 | 概率 | ✅ **可信** | |

---

## 三、主文论文应使用的可信来源

| 图/表 | 应使用的文件 | 禁止使用的文件 |
|---|---|---|
| 代理精度（Table 1） | `paper_focus_metrics_level0/2.csv`（canonical subdir） | ❌ `paper_fixed_model_compare_*.csv` |
| R² / RMSE 逐输出 | `paper_metrics_per_dim_level0/2.csv`（canonical subdir） | ❌ `paper_fixed_model_compare_per_output.csv` |
| Sobol 敏感性 | `paper_sobol_results_with_ci.csv` | — |
| Forward UQ 风险曲线 | `forward_uq_*_level2.csv` | — |
| 后验推断结果 | `benchmark_case/` + `paper_posterior_hf_validation_*_maintext.csv` | — |
| OOD 泛化 | `paper_ood_multi_feature_summary.csv`（⚠️待核实列对齐） | ❌ `paper_ood_results.csv`（旧版，输出定义不明） |

---

## 四、0404 新框架 manifest 必须记录的字段

每次 eval 生成的 manifest 需包含：

```json
{
  "artifact_origin": "reused_legacy | trained_in_0404",
  "training_protocol": "legacy_fixed | 0404_fixed | 0404_repeat",
  "output_definition_version": "15col_v1",
  "inference_method": "saved_predictions | rerun_inference",
  "column_alignment_verified": true,
  "test_set": "fixed_split/test.csv",
  "n_test": 435,
  "standardized_space": false
}
```

**关键规则**：  
`inference_method = rerun_inference` 时，必须附带列对齐校验步骤（比较预测均值与已知 test_predictions JSON 的相关系数 > 0.99），否则结果不可信。

---

## 五、待确认事项

- [ ] `paper_ood_multi_feature_summary.csv` 的列对齐是否正确（参考 1.1 的风险，需检查 OOD 脚本的 OUTPUT_COLS 定义）
- [ ] `paper_metrics_table.csv` 的 RMSE_mean_primary 是否在任何论文正文中直接引用（如有，替换为逐输出指标）
- [ ] `run_compare_fixed_models.py` 是否有必要修复（列对齐问题）——或直接废弃，改用 `run_eval_0404.py` 替代
