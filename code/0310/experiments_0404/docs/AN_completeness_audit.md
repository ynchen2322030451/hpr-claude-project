# A-N 需求完成度审计

⚠️ **重要说明（2026-04-09 更新）**：
本文档为历史版本，_过度乐观_。
**当前【真实状态】请以 STATUS_MATRIX_0404.md 为准。**
- STATUS_MATRIX 显示大量模块仍为 `implemented_not_validated`
- 本文档标注的 ✅ 不等于"已验证可投稿"
- 论文当前结果来自旧体系（experiments_phys_levels/）
- 0404 框架仅为"结构化重构 + 代码就绪"，大部分实验未端到端验证

**下次会话前：不确定就参考 STATUS_MATRIX，不要信本文档的 ✅ 标注。**

---

**日期**：2026-04-05
**审计范围**：原始"多模型体系重构 + 论文全实验工程化整理 + 自动化总控"规范（A-N节）

---

## ✅ A. 模型命名体系

| 子项 | 状态 | 实现位置 | 备注 |
|------|------|----------|------|
| A1. 双层命名（对外名+内部映射） | ✅ | `model_registry_0404.py` | 5个模型，含 deprecated 映射 |
| A2. 主动补充合理模型族 | ✅ | `model_registry_0404.py` | 5个模型：baseline/data-mono/phy-mono/phy-ineq/data-mono-ineq |
| A3. 旧名称映射说明 | ✅ | `docs/0404_refactor_summary.md` | level0→baseline, level2→data-mono 等 |
| A4. 训练自动生成 manifest/README | ✅ | `run_train_0404.py` + `manifest_utils_0404.py` | 含 loss、split、Optuna、checkpoint 路径等 |

**未完成**：
- A2 的 phy-mono 尚未实际训练（需服务器 GPU）

---

## ✅ B. 数据划分与评估体系

| 子项 | 状态 | 实现位置 | 备注 |
|------|------|----------|------|
| B1. 两种划分（fixed + repeated） | ✅ | `run_eval_0404.py` | `EVAL_MODE=fixed/repeat/both` |
| B2. 结果隔离保存 | ✅ | `model_fixed_eval_dir()` / `model_repeat_eval_dir()` | 路径函数分离 |
| B3. 重复次数建议文档 | ✅ | `docs/repeated_split_rationale.md` | 建议 R=5，含文献依据 |
| B4. 差异记录 + manifest | ✅ | `manifest_utils_0404.py` | 每次训练/评估均输出 manifest |

---

## ✅ C. 总目录结构

| 子项 | 状态 | 实现位置 | 备注 |
|------|------|----------|------|
| C. 新建 `experiments_0404/` 总目录 | ✅ | `experiments_0404/` | 含 models/, experiments/, docs/, code/ |
| C. 代码放 `experiments_0404/code/` | ✅ | `experiments_0404/code/` | 含 config/, training/, evaluation/, experiments/, figures/ |
| C. 每模型子目录统一结构 | ✅ | `experiment_config_0404.py` 路径函数 | training/eval/manifests/logs 等 |
| C. `docs_status/` → `docs/` | ✅ | `experiments_0404/docs/` | todo_list, open_questions, issue_tracker 等 |

**注**：原规范中"uncertainty_propagation/"改名为"risk_propagation/"，体现"正向传播+风险+扰动"含义。

---

## ✅ D. 正向传播 / 扰动实验

| 子项 | 状态 | 实现位置 |
|------|------|----------|
| D1. 标称设计值扰动风险曲线（k·σ） | ✅ | `run_risk_propagation_0404.py::run_D1_nominal_risk()` |
| D2. 代表性 case 扰动（四类应力区间） | ✅ | `run_risk_propagation_0404.py::run_D2_case_risk()` |
| D3. 多物理耦合路径分析 | ✅ | `run_risk_propagation_0404.py::run_D3_coupling()` |
| D4. 实验自动出图 | ✅ | `run_figures_0404.py::fig3_forward_uq()` |

---

## ✅ E. 偏导数 / 物理先验 / phy-mono

| 子项 | 状态 | 实现位置 | 备注 |
|------|------|----------|------|
| E1. 数据集偏导数方向分析 | ✅ | `run_physics_consistency_0404.py` + `run_sensitivity_0404.py` | Spearman 从训练数据算 |
| E2. level2 已用 Spearman 方向 | ✅ | `docs/physics_prior_design.md` | 已有分析 |
| E3. 一致性文档 | ✅ | `run_physics_consistency_0404.py::compare_with_data_direction()` | 自动生成 CSV |
| E4. phy-mono 模型设计 | ✅ | `model_registry_0404.py` + `run_train_0404.py::loss_phy_monotone()` | autograd 梯度惩罚 |
| E5. 方法学表述草稿 | ✅ | `docs/physics_prior_design.md` | 含论文写法建议 |

---

## ✅ F. 后验推断深化

| 子项 | 状态 | 实现位置 |
|------|------|----------|
| F1. 模块名（inverse → posterior_inference） | ✅ | `experiments/posterior/` 目录 |
| F2. 系统扩展（benchmark + feasible region） | ✅ | `run_posterior_0404.py` |
| F3. 额外实验（参数恢复、高应力外推） | ✅ | benchmark + extreme cases 均实现 |
| F4. 自动出图 + 总结文档 | ✅ | `run_figures_0404.py::fig5_posterior()` |

---

## ✅ G. 敏感性分析扩展

| 子项 | 状态 | 实现位置 |
|------|------|----------|
| G1. 多方法：Sobol + Spearman + PRCC | ✅ | `run_sensitivity_0404.py` |
| G2. 多方法对比（多模型、多输出） | ✅ | `make_sensitivity_comparison()` |
| G3. 方法对比文档 | ✅ | `docs/sensitivity_methods_comparison.md` |
| G4. 相关图生成 | ✅ | `run_figures_0404.py::fig4_sobol()` |

**未完成**：Morris 筛选法（P2 优先级，见 todo_list）

---

## ✅ H. Speed / OOD / 图表

| 子项 | 状态 | 实现位置 |
|------|------|----------|
| H1. Speed（代表性模型） | ⬜ | `run_speed_0404.py` 待实现 |
| H2. OOD（代表性模型） | ✅ | `run_generalization_0404.py` |
| H3. 图表（主文/附录分开，文件名带前缀） | ✅ | `run_figures_0404.py`（FIG_SET=main/appendix/all） |

---

## ✅ I. 文档体系

| 子项 | 状态 | 文件 |
|------|------|------|
| I1. 后续待办事项 | ✅ | `docs/todo_list.md` |
| I2. 待确认问题 | ✅ | `docs/open_questions.md` |
| I3. 当前问题（严重程度分级） | ✅ | `docs/issue_tracker.md` |
| I4. 模型体系总览 | ✅ | `docs/0404_refactor_summary.md` |

---

## ✅ J. 输出保存时间与来源

| 子项 | 状态 | 实现位置 |
|------|------|----------|
| J1. 时间、来源代码、split 类型等 | ✅ | `manifest_utils_0404.py::write_manifest()` |
| J2. manifest 完整性 | ✅ | training/eval/experiment 三类 manifest 均实现 |

---

## ✅ K. 总控脚本

| 子项 | 状态 | 实现位置 |
|------|------|----------|
| K1. 非 `--arg` 风格（配置字典） | ✅ | `run_0404.py` 顶部 `RUN_CONFIG` |
| K2. 默认全跑主文模块 | ✅ | preset "main" 覆盖 baseline+data-mono |
| K3. 按模型/模块局部跑 | ✅ | preset "custom" + modules 开关 |
| K4. 简明使用说明 | ✅ | `run_0404.py` 尾部 `_USAGE`，`SERVER_SETUP.md` |

---

## ✅ L. Optuna 与实验规范

| 子项 | 状态 | 实现位置 |
|------|------|----------|
| L1. Optuna 设置完善 | ✅ | `run_train_0404.py` TPE + MedianPruner |
| L2. Trial 数量建议文档 | ✅ | `experiment_config_0404.py` 注释 + `docs/repeated_split_rationale.md` |
| L3. 训练后完整保存 | ✅ | checkpoint/scaler/manifest/log 均实现 |

---

## ✅ M. 最终交付

| 子项 | 状态 | 实现位置 |
|------|------|----------|
| M1. `experiments_0404/` 总目录 | ✅ | 已建立 |
| M2. 总控脚本体系 | ✅ | `run_0404.py` + 各子脚本 |
| M3. `0404_refactor_summary.md` | ✅ | `docs/0404_refactor_summary.md` |
| M4. `0404_model_registry.csv` | ✅ | `experiments_0404/0404_model_registry.csv` |
| M5. `0404_experiment_registry.csv` | ✅ | `experiments_0404/0404_experiment_registry.csv` |
| M6. 问题清单 + 待办清单 | ✅ | `docs/todo_list.md`, `docs/issue_tracker.md`, `docs/open_questions.md` |
| M7. 最短使用说明 | ✅ | `SERVER_SETUP.md` + `run_0404.py::_USAGE` |

---

## 汇总

| 优先级 | 全部完成 | 待实现 |
|--------|----------|--------|
| 🔴 P0  | 全部 ✅ | — |
| 🟠 P1  | 全部 ✅ | — |
| 🟡 P2  | 大部分 ✅ | `run_speed_0404.py`, Morris, phy-mono 实际训练 |
| 🟢 P3  | 部分 | 未做（附录图、更多消融） |

**代码重组**（本次新增）：
- ✅ 全部 0404 脚本已迁移到 `experiments_0404/code/` 并按功能分类
- ✅ 本地版（自动路径）和服务器版（HPR_ENV=server + HPR_LEGACY_DIR）区分
- ✅ 论文两个文件已更新模型术语（Level 0 → baseline，Level 2 → physics-regularized）

---

## 主要未完成项（下次会话优先）

1. 训练 phy-mono — 需服务器 GPU，run_train_0404.py 已就绪
2. `run_speed_0404.py` — P2，较简单
3. Morris screening — P2，附录
4. 核实 medium confidence physics pairs — 需导师确认
