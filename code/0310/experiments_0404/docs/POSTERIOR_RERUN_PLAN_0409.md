# 后验推断参数重设与重跑计划

**更新日期**：2026-04-09
**原因**：Sobol canonical (0405) 敏感性排序更新，要求后验参数配置从3D改为4D
**状态**：⚠️ P0 blocking — 必须立即在服务器上执行

---

## 一、参数配置变更总结

### 旧配置（已作废）
```python
INVERSE_CALIB_PARAMS   = ["E_intercept", "alpha_base", "alpha_slope", "nu"]
INVERSE_FIXED_PARAMS   = ["E_slope", "SS316_T_ref", "SS316_k_ref", "SS316_alpha"]
```
- 接受率：0.40–0.53
- 标定维度：3D（忽略了应力第三敏感因子SS316_k_ref）
- ❌ 问题：SS316_k_ref (S₁=0.080) 是应力的第三敏感因子但被固定，削弱后验信息量

### 新配置（2026-04-09 已设置）
```python
INVERSE_CALIB_PARAMS   = ["E_intercept", "alpha_base", "alpha_slope", "SS316_k_ref"]
INVERSE_FIXED_PARAMS   = ["E_slope", "SS316_T_ref", "SS316_alpha", "nu"]
```
- 预期接受率：0.77–0.85
- 标定维度：4D
- ✅ 理由：完全对齐Sobol敏感性排序，nu (低敏感) 被移出标定

---

## 二、Sobol 敏感性排序（新canonical, 0405）

### 应力主导因子
| 参数 | S₁ | 状态 |
|---|---|---|
| E_intercept | 0.598 | 🥇 **主导** → ✅ 标定 |
| alpha_base | 0.148 | 🥈 第二  → ✅ 标定 |
| SS316_k_ref | 0.080 | 🥉 第三  → ✅ **新增标定** |
| alpha_slope | 低/零 | N/A  → ✅ 标定（keff主导） |

### keff主导因子
| 参数 | S₁ | 状态 |
|---|---|---|
| alpha_base | 0.775 | 🥇 **主导** → ✅ 标定 |
| alpha_slope | 0.177 | 🥈 第二 → ✅ 标定 |

### 应被固定的因子
| 参数 | 理由 | 状态 |
|---|---|---|
| nu | S₁ 低/0 | ❌ **从标定中移除** |
| E_slope | 不稳定 | ✅ 继续固定 |
| SS316_T_ref | 低 | ✅ 继续固定 |
| SS316_alpha | CI包含0 | ✅ 继续固定 |

---

## 三、论文中受影响的部分

### Methods （2.6 观测驱动后验标定）
- ✅ **已改** — 参数列表、接受率、论述已更新

### Results （3.4 观测驱动后验标定）
- ✅ **已改** — 案例数（18 benchmark）、范围（133–194 MPa）、接受率已更新

### 需要重新生成的表图
- TABLE 6: 极端应力后验风险更新
- FIG 5: 后验标定结果（接受率、后验均值追踪、极端案例P_exceed对比）

---

## 四、重跑清单

### **任务 1：baseline 后验推断重跑**

**命令**：
```bash
cd /Users/yinuo/Projects/hpr-claude-project/code/0310/experiments_0404/code/experiments
MODEL_ID=baseline POSTERIOR_MODE=all python run_posterior_0404.py
```

**输入**：
- 模型：`experiments_phys_levels/fixed_surrogate_fixed_base/checkpoint.pt`
- 测试集：`fixed_split/test.csv` (435条)
- 观测：calibration_pool 中的 benchmark cases + extreme stress cases

**需验证的输出**：
- `experiments/posterior/baseline/benchmark_summary.csv`
  - 接受率列：应在 0.77–0.85 范围
  - 参数列：应包含 E_intercept, alpha_base, alpha_slope, SS316_k_ref

- `experiments/posterior/baseline/feasible_region.csv`
  - 极端应力范围：应为 133–194 MPa（不是≥220 MPa）
  - P_exceed 分布

**预期结果特征**：
- ✅ 接受率：0.77–0.85（vs 旧的 0.40–0.53）
- ✅ 后验样本：1200 per case (burn_in=2000, thin=5, total=8000)
- ✅ 无 NaN 或异常后验分布

---

### **任务 2：data-mono（Level 2）后验推断重跑**

**命令**：
```bash
cd /Users/yinuo/Projects/hpr-claude-project/code/0310/experiments_0404/code/experiments
MODEL_ID=data-mono POSTERIOR_MODE=all python run_posterior_0404.py
```

**输入**：
- 模型：`experiments_phys_levels/fixed_surrogate_fixed_level2/checkpoint.pt`
- 其他同 Task 1

**需验证的输出**：
- `experiments/posterior/data-mono/benchmark_summary.csv`
- `experiments/posterior/data-mono/feasible_region.csv`

**预期结果特征**：
- 应与 baseline 结果在接受率、后验统计上可比（允许±0.05接受率差异）

---

## 五、验证检查清单

执行完重跑后，按以下清单逐项检查：

### 接受率检查
```python
# 预期：每个模型、每个案例的接受率应在 [0.77, 0.85] 区间
# 如果大部分 < 0.70 或 > 0.90，说明 MCMC 参数需调整
baseline_rates_: should be in [0.77, 0.85]
data_mono_rates_: should be in [0.77, 0.85]
```

### 参数对账
```python
# 新后验应包含 SS316_k_ref 的后验分布（不再是固定值）
# nu 应消失（被固定）
posterior params in baseline_summary.csv:
✓ E_intercept
✓ alpha_base
✓ alpha_slope
✓ SS316_k_ref
✗ nu (should NOT exist in calib_params)
```

### 风险曲线检查
```python
# 极端应力案例（133–194 MPa 范围）的 P_exceed
# 应与论文中描述一致：
#   - ≥177 MPa: P_exceed ≥ 0.99
#   - 150–177 MPa: P_exceed = 0.96–0.97
#   - 133–137 MPa: P_exceed = 0.62–0.81
```

### Convergence 检查
```python
# R-hat 统计量：应 < 1.01（已实现在脚本中）
# trace plot：烧入期后无方向漂移
# 需手工检查输出日志中的 R-hat 值
```

---

## 六、post-run 操作清单

重跑完成后：

### 1. 生成新表格和图
```
run_figures_0404.py::TABLE6_posterior_risk()  → TABLE 6
run_figures_0404.py::FIG5_posterior()         → FIG 5
```

### 2. 更新 manifest
```
posterior_manifest_baseline.json (calib_params, acceptance_rates, etc.)
posterior_manifest_data_mono.json
```

### 3. 生成对账报告
```
对账内容：
- 新旧接受率对比表
- benchmark case count 变化（20 → 18）
- 极端应力范围变化（≥220 → 133–194）
- P_exceed 预期vs实际对比
```

### 4. 更新论文 Results 图表
- TABLE 6 插入最新数据
- FIG 5 替换为新的图表

---

## 七、时间表与依赖

| 阶段 | 任务 | 依赖 | 预计时间 | 状态 |
|---|---|---|---|---|
| P0 | baseline MCMC | 参数配置✅ | 2-3 hours | pending |
| P0 | data-mono MCMC | baseline✅ | 2-3 hours | pending |
| P1 | 验证接受率、收敛性 | 两个MCMC✅ | 0.5 hour | pending |
| P1 | 生成新TABLE6/FIG5 | 验证✅ | 1 hour | pending |
| P1 | 更新论文数字 | 图表✅ | 0.5 hour | pending |

**总预计**：5-7 小时（服务器连续运行）

---

## 八、风险提示

⚠️ **关键风险**：
1. 若接受率仍然 < 0.70，说明 proposal_scale 或似然函数需调整
2. 若 SS316_k_ref 的后验无法探索到合理范围（全是边界值），检查先验设置
3. 若极端应力 P_exceed 仍然接近 1.0（所有案例），检查观测噪声设置 σ_obs

⚠️ **不可回退**：
- 旧的接受率 0.40–0.53 不能再写进论文（已改为 0.77–0.85）
- 旧的极端应力描述（≥220 MPa）不能再用（已改为 133–194 MPa）
- ν 不能再出现在标定参数列表中

---

## 九、成功标准

✅ 任务完成判定：
1. baseline + data-mono 两个模型都完成 MCMC 采样
2. 接受率均在 0.75–0.87 范围（允许5%偏差）
3. 所有案例收敛性检查通过（R-hat < 1.01）
4. 新 TABLE 6 / FIG 5 已生成
5. 论文图表已替换为新结果
6. 论文文本（Methods 2.6 + Results 3.4）与新结果一致

---

**下一步**：
1. 确认服务器可用性和计算资源
2. 在远程服务器上执行 Task 1 和 Task 2
3. 完成本 checklist 的所有验证项
4. 三天内向课题组报告完成状态
