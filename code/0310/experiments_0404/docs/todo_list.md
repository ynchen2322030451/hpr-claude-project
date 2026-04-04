# 待办事项清单

**最后更新**：2026-04-05（会话续写）

---

## 优先级说明
- 🔴 **P0** — 影响主文，不做论文无法完成
- 🟠 **P1** — 影响主文质量，强烈建议做
- 🟡 **P2** — 附录/补充，可以做但不阻塞主文
- 🟢 **P3** — 锦上添花，有空再做

---

## 训练 & 评估

| 状态 | 优先级 | 任务 | 说明 |
|------|--------|------|------|
| ✅ 完成 | 🔴 P0 | 实现 `run_train_0404.py` | 支持5个模型，含 manifest 生成，固定旧 checkpoint 复用 |
| ⬜ 待做 | 🔴 P0 | 训练 `phy-mono` | 物理先验单调性模型，E4 要求，需在服务器运行 |
| ✅ 完成 | 🟠 P1 | 实现 `run_eval_0404.py` | fixed split + repeat split 统一评估，自动 manifest |
| ⬜ 待做 | 🟡 P2 | 训练 `phy-ineq` | 附录消融，不等式约束 |
| ⬜ 待做 | 🟡 P2 | 训练 `data-mono-ineq` | 附录完整约束版 |
| ⬜ 待做 | 🟡 P2 | repeated split 评估（5次） | baseline + data-mono，验证 split 稳定性 |

---

## 正向传播 & 风险实验

| 状态 | 优先级 | 任务 | 说明 |
|------|--------|------|------|
| ✅ 完成 | 🔴 P0 | 实现 `run_risk_propagation_0404.py` | D1+D2+D3 全部实现，含 manifest |
| ✅ 完成 | 🟠 P1 | D2: 代表性 case 扰动 | 低/近阈值/高/极端应力 case，多幅度扰动 |
| ✅ 完成 | 🟠 P1 | D3: 多物理耦合路径分析 | iter1→iter2 均值偏移、方差比、Spearman 关联 |
| ⬜ 待做 | 🟡 P2 | 风险曲线对比图（baseline vs data-mono） | 不同模型在同一扰动下的 P_fail 差异 |

---

## 物理一致性分析（E2-E3）

| 状态 | 优先级 | 任务 | 说明 |
|------|--------|------|------|
| ✅ 完成 | 🔴 P0 | 实现 `run_physics_consistency_0404.py` | autograd 梯度符号 + data Spearman 方向对比 |
| ⬜ 待做 | 🟠 P1 | 物理先验方向文档完善 | 核实 `model_registry_0404.py` 里的 medium confidence 对 |
| ⬜ 待做 | 🟠 P1 | 生成 `physics_consistency_report.md` | 运行后由结果生成，哪些方向一致/不一致 |

---

## 敏感性分析

| 状态 | 优先级 | 任务 | 说明 |
|------|--------|------|------|
| ✅ 已有 | — | Sobol S1/ST（旧结果） | `experiments_phys_levels/` 下已有，可引用 |
| ✅ 完成 | 🟠 P1 | 实现 `run_sensitivity_0404.py` | Sobol Jansen + Spearman + PRCC 全部实现 |
| ✅ 完成 | 🟠 P1 | Spearman rank correlation | run_sensitivity_0404.py 内部实现 |
| ✅ 完成 | 🟡 P2 | PRCC | run_sensitivity_0404.py 内部实现，附录用 |
| ⬜ 待做 | 🟡 P2 | Morris screening | 附录方法，与 Sobol 主效应对比 |
| ⬜ 待做 | 🟡 P2 | 方法对比报告 | 各方法结论一致性、差异分析 |

---

## 后验推断

| 状态 | 优先级 | 任务 | 说明 |
|------|--------|------|------|
| ✅ 已有 | — | MCMC 20 benchmark cases（旧结果） | 可引用旧结果 |
| ✅ 已有 | — | 10 极端应力 case 验证（旧结果） | 可引用旧结果 |
| ✅ 完成 | 🟠 P1 | 实现 `run_posterior_0404.py` | MH-MCMC benchmark + feasible region 全部实现 |
| ✅ 完成 | 🟠 P1 | 可行域分析（feasible region） | 高应力 case 后验 P(safe>α) 分析 |
| ⬜ 待做 | 🟡 P2 | 不同观测子集对比 | 仅应力 vs 多输出联合观测 |
| ⬜ 待做 | 🟡 P2 | 不同噪声水平对比 | observation quality 影响后验宽度 |

---

## OOD / 速度

| 状态 | 优先级 | 任务 | 说明 |
|------|--------|------|------|
| ✅ 已有 | — | OOD single/multi feature（旧结果） | 可引用 |
| ✅ 已有 | — | 速度对比（旧结果） | 可引用 |
| ✅ 完成 | 🟡 P2 | 实现 `run_generalization_0404.py` | 4个 OOD 特征，in-dist vs tail 对比 |
| ⬜ 待做 | 🟡 P2 | 实现 `run_speed_0404.py` | 速度对比，只跑 data-mono |

---

## 画图

| 状态 | 优先级 | 任务 | 说明 |
|------|--------|------|------|
| ✅ 完成 | 🟠 P1 | 实现 `run_figures_0404.py` — 主文图 | Fig1–5 + AppA1–A8，自动从旧规范结果回退读取 |
| ✅ 完成 | 🟡 P2 | 附录图生成 | figA1–figA8 均在 run_figures_0404.py 内实现 |

---

## 文档

| 状态 | 优先级 | 任务 | 说明 |
|------|--------|------|------|
| ✅ 完成 | — | `0404_refactor_summary.md` | 本次重构总结 |
| ✅ 完成 | — | `model_system_overview.md` | 模型体系概览 |
| ✅ 完成 | — | `issue_tracker.md` | 当前问题清单 |
| ✅ 完成 | — | `physics_prior_design.md` | 物理先验设计说明 |
| ✅ 完成 | — | `repeated_split_rationale.md` | 重复划分方案说明 |
| ✅ 完成 | — | `sensitivity_methods_comparison.md` | 敏感性方法对比 |
| ⬜ 待做 | 🟠 P1 | 核实物理先验中的 medium confidence 对 | 需与导师确认 E_slope 符号、keff 关系 |
| ⬜ 待做 | 🟡 P2 | 更新 open_questions.md（随实验进展） | 动态维护 |
