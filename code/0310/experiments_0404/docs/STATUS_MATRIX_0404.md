# 0404 体系完成状态矩阵

**最后更新**：2026-04-05  
**状态定义**：

| 状态标签 | 含义 |
|---|---|
| `scaffolded` | 框架已搭，代码文件存在，**未本地运行验证** |
| `implemented_not_validated` | 实现完整，但**从未端到端运行过**，输出文件未落盘 |
| `validated_local` | 本地 smoke test 通过，输出文件已落盘并人工确认 |
| `validated_server` | 服务器上完整跑通，结果已与旧结果对账 |
| `reused_legacy` | 使用旧 `experiments_phys_levels/` 结果，**未在 0404 框架下重跑** |

---

## 模型状态

| 模型 ID | artifact 状态 | checkpoint 来源 | 训练框架 | 备注 |
|---|---|---|---|---|
| baseline | `reused_legacy` | `fixed_surrogate_fixed_base/` | 旧 `run_phys_levels_main.py` | 0404 体系中复用，未重训 |
| data-mono | `reused_legacy` | `fixed_surrogate_fixed_level2/` | 旧 `run_phys_levels_main.py` | 0404 体系中复用，未重训 |
| phy-mono | `scaffolded` | — | — | autograd 梯度惩罚 loss 已实现，**未训练** |
| phy-ineq | `scaffolded` | — | — | 不等式约束，仅设计未实现 |
| data-mono-ineq | `scaffolded` | — | — | 仅注册，未实现 |

---

## 训练 & 评估模块

| 模块 | 脚本 | 状态 | 输出是否落盘 | 备注 |
|---|---|---|---|---|
| 训练（baseline/data-mono 复用） | `run_train_0404.py` | `reused_legacy` | ✅（旧目录） | 0404 框架会复制 artifact，不重训 |
| 训练（phy-mono） | `run_train_0404.py` | `implemented_not_validated` | ❌ | 需服务器 GPU |
| 评估 fixed split | `run_eval_0404.py` | `implemented_not_validated` | ❌ | 脚本已写，**未本地运行验证** |
| 评估 repeated split | `run_eval_0404.py` | `implemented_not_validated` | ❌ | 待 fixed split 完成后做 |

---

## 实验模块

| 模块 | 脚本 | 状态 | 旧结果可用 | 备注 |
|---|---|---|---|---|
| risk propagation D1（标称扰动） | `run_risk_propagation_0404.py` | `implemented_not_validated` | ✅（旧 forward_uq CSV） | 脚本重写，**未验证输出** |
| risk propagation D2（代表 case） | `run_risk_propagation_0404.py` | `implemented_not_validated` | 部分 | **未验证** |
| risk propagation D3（耦合分析） | `run_risk_propagation_0404.py` | `implemented_not_validated` | ❌ | **未验证** |
| Sobol 敏感性 | `run_sensitivity_0404.py` | `implemented_not_validated` | ✅（`paper_sobol_results_with_ci.csv`） | 脚本重写，**未验证** |
| Spearman / PRCC | `run_sensitivity_0404.py` | `implemented_not_validated` | 部分 | **未验证** |
| Morris 筛选 | `run_sensitivity_0404.py` | `scaffolded` | ❌ | 附录，低优先级 |
| 后验推断 benchmark（20 case） | `run_posterior_0404.py` | `implemented_not_validated` | ✅（`benchmark_case/`） | 脚本重写，**未验证** |
| 后验推断 extreme stress（10 case） | `run_posterior_0404.py` | `implemented_not_validated` | ✅（`paper_extreme_stress_*.csv`） | **未验证** |
| 后验可行域分析 | `run_posterior_0404.py` | `implemented_not_validated` | ❌ | **未验证** |
| 物理先验一致性 | `run_physics_consistency_0404.py` | `implemented_not_validated` | ❌ | **未验证** |
| OOD 泛化 | `run_generalization_0404.py` | `implemented_not_validated` | ✅（`paper_ood_*.csv`） | **未验证** |
| 计算速度对比 | `run_speed_0404.py` | `scaffolded` | ✅（`paper_speedup_benchmark.json`） | 脚本**未实现** |

---

## 画图模块

| 模块 | 脚本 | 状态 | 备注 |
|---|---|---|---|
| 主文图（Fig1–5） | `run_figures_0404.py` | `implemented_not_validated` | 逻辑来自旧 `make_figures.py`，**未运行验证** |
| 附录图（FigA1–A8） | `run_figures_0404.py` | `implemented_not_validated` | 同上 |

---

## 文档 & 配置

| 文件 | 状态 | 备注 |
|---|---|---|
| `experiment_config_0404.py` | `validated_local` | 路径、参数均已核对 |
| `model_registry_0404.py` | `validated_local` | 5 模型定义，physics pairs 部分待导师核实 |
| `manifest_utils_0404.py` | `implemented_not_validated` | 逻辑正确，未实际生成过 manifest |
| `AN_completeness_audit.md` | — | ⚠️ 历史版本过于乐观，以本文件为准 |

---

## 第一批必跑闭环（服务器任务）

按老师建议，先只验证最小闭环：

```
baseline + data-mono
  → eval_fixed
  → risk D1（标称风险曲线）
  → sensitivity（Sobol only）
  → posterior benchmark（20 case）
```

其他全部推迟到闭环验通后再做。
