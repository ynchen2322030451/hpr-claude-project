# HPR Surrogate 0404 重构总结

**日期**：2026-04-04  
**作者**：Yinuo Chen  
**状态**：架构已落地，训练脚本待接入

---

## 1. 重构动机

旧体系（`experiments_phys_levels/`）存在以下问题：
- 命名 level0/level2 对外无法解释模型区别
- 正向传播只有全范围均匀采样，缺少围绕设计值的扰动实验
- 逆问题模块不够系统（缺少可行域分析）
- 敏感性分析只有 Sobol，缺乏方法间对比
- 物理先验单调性模型（phy-mono）未实现
- 目录结构混乱，模型产出与实验产出混在一起

---

## 2. 新模型命名体系

| 模型 ID | 全称 | Loss 组成 | 来源 | 论文角色 |
|---------|------|-----------|------|---------|
| `baseline` | Heteroscedastic Baseline | NLL | Level 0 / fixed_base | 主文对照基线 |
| `data-mono` | Data-Monotone Regularized | NLL + Spearman | Level 2 / fixed_level2 | 主文提出方法 |
| `phy-mono` | Physics-Prior Monotone | NLL + 物理先验 | 新增（E4） | 消融/对照 |
| `phy-ineq` | Physics-Inequality Constrained | NLL + 不等式 | Level 3 partial | 附录消融 |
| `data-mono-ineq` | Data-Monotone + Inequality | NLL + Spearman + 不等式 | Level 3 complete | 附录完整版 |

### 原始 level 映射

| 原始名称 | 新名称 | 说明 |
|----------|--------|------|
| level0 / fixed_base | `baseline` | 纯数据基线 |
| level2 / fixed_level2 | `data-mono` | 数据推导单调性 |
| level1 | — | 废弃（loss 返回 0.0） |
| level3 | `phy-ineq` + `data-mono-ineq` | 分拆成两个模型 |
| level4 | — | 废弃（过度复杂，含 bootstrap + variance floor + delta head） |
| remain_delta | — | 废弃（实验性 delta head，未进入论文） |
| oldmain | — | 废弃（split 未冻结，结果不可复现） |

---

## 3. 新目录结构

```
experiments_0404/
├── _config/                   ← 配置、日志、运行记录
├── _shared/fixed_split/       ← 复用旧 fixed split（70/15/15）
│
├── models/                    ← 每个模型独立目录
│   ├── baseline/
│   │   ├── artifacts/         ← checkpoint, scaler, best_params
│   │   ├── fixed_eval/        ← fixed split 评估结果
│   │   ├── repeat_eval/       ← repeated split 评估结果
│   │   ├── manifests/         ← 训练 manifest（JSON）
│   │   └── logs/              ← 训练日志
│   ├── data-mono/
│   ├── phy-mono/
│   ├── phy-ineq/
│   └── data-mono-ineq/
│
├── experiments/               ← 按实验类型组织的下游分析
│   ├── risk_propagation/      ← 正向传播 + 风险曲线 + 扰动实验
│   │   ├── nominal_perturbation/
│   │   ├── case_perturbation/
│   │   ├── coupling_analysis/
│   │   └── figures/
│   ├── sensitivity/           ← Sobol + rank corr + Morris
│   ├── posterior_inference/   ← MCMC 后验 + 可行域
│   ├── generalization/        ← OOD 泛化
│   ├── computational_speedup/ ← 速度对比
│   └── physics_consistency/   ← 物理先验一致性
│
├── figures/
│   ├── main_text/
│   └── appendix/
│
├── docs/                      ← 本文件所在目录
│
├── 0404_model_registry.csv    ← 模型注册表
└── 0404_experiment_registry.csv ← 实验注册表
```

**原 `forward_uq/`** → 重命名为 `risk_propagation/`，更清楚地体现"正向传播 + 风险量化 + 扰动实验"含义。

---

## 4. 新增实验模块

### 4.1 risk_propagation（正向传播扩展）
相比旧 forward_uq 新增：
- **D1**：围绕设计标称值的多σ扰动（k=0.5/1/2/3），生成 risk curve
- **D2**：围绕代表性 case（低/近阈值/高应力）的扰动实验
- **D3**：多物理耦合深入分析（iter1→iter2 均值偏移、方差压缩路径、各输出放大因子）

### 4.2 sensitivity（敏感性分析扩展）
相比旧 Sobol-only 新增：
- Spearman rank correlation（快速、直觉可读）
- PRCC（Partial Rank Correlation Coefficient，适合单调非线性）
- Morris screening（附录，与 Sobol 主效应对比）

### 4.3 posterior_inference（后验推断扩展）
相比旧逆问题新增：
- 可行域分析（哪些参数组合使 stress < 131 MPa 的后验概率 > 某阈值）
- 不同观测组合（仅观测 stress vs 多输出联合观测）
- 不同噪声水平对比

### 4.4 physics_consistency（新增）
- 数据集中输入-输出 Spearman 相关方向
- 物理先验指定方向
- 两者一致性对比表
- 不一致处的可能原因分析

### 4.5 phy-mono 模型（新增，E4 要求）
- 单调性方向由物理分析指定（不依赖数据相关性）
- 高置信度物理对（定义在 `model_registry_0404.py:PHYSICS_PRIOR_PAIRS_HIGH`）
- 用途：与 data-mono 对比，验证"数据推导的单调性是否与物理一致"

---

## 5. 运行方式（最短版）

```bash
cd /Users/yinuo/Projects/hpr-claude-project/code/0310

# 1. 默认全跑主线（baseline + data-mono + 主文实验）
python run_0404.py

# 2. 跑附录模型
# 修改 run_0404.py 中 RUN_CONFIG["preset"] = "appendix"
python run_0404.py

# 3. 只跑某个模型训练
# 修改 RUN_CONFIG["preset"] = "custom"
# RUN_CONFIG["custom_models"] = ["phy-mono"]
# RUN_CONFIG["modules"]["train"] = True（其他全 False）
python run_0404.py

# 4. 只重画图
# RUN_CONFIG["modules"] 只开 "figures_main": True
python run_0404.py
```

---

## 6. 与旧结果的关系

- 旧 `experiments_phys_levels/` **不删除**，保持只读
- `baseline` 对应 `fixed_surrogate_fixed_base/`（已有 checkpoint，可直接复用）
- `data-mono` 对应 `fixed_surrogate_fixed_level2/`（已有 checkpoint，可直接复用）
- 训练脚本 `run_train_0404.py` 会先检查旧目录的 checkpoint，如存在则链接而非重训

---

## 7. 下一步任务（按优先级）

1. **[紧急]** 实现 `run_train_0404.py`（支持5个模型的训练逻辑）
2. **[重要]** 实现 `run_eval_0404.py`（统一评估 + manifest 生成）
3. **[重要]** 实现 `run_risk_propagation_0404.py`（D1/D2/D3 三类实验）
4. **[重要]** 实现 `run_physics_consistency_0404.py`（物理一致性分析文档）
5. **[中等]** 实现 `run_sensitivity_0404.py`（Sobol 扩展 + rank corr + Morris）
6. **[中等]** 实现 `run_posterior_0404.py`（后验推断 + 可行域）
7. **[低优]** 实现 `run_generalization_0404.py` / `run_speed_0404.py`
8. **[低优]** 实现 `run_figures_0404.py`（统一画图入口）

详见 `docs/todo_list.md`。
