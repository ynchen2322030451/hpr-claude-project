# 问题清单

**最后更新**：2026-04-04

---

## 严重程度分级

- 🔴 **致命** — 直接影响核心结论正确性，不处理不能发表
- 🟠 **高** — 影响方法声明或关键数据，需要在论文中明确说明或修正
- 🟡 **中** — 影响表述质量或论文完整性，应在提交前解决
- 🟢 **低** — 细节问题，不影响核心结论

---

## 🔴 致命问题

| ID | 问题 | 影响范围 | 建议处理 | 状态 |
|----|------|---------|---------|------|
| F01 | 旧脚本中 `iter2_keff` 被错误列为 `ITER2_IDX` 范围内（7 元素），但 `OUT2` 有 8 个输出（含 keff）。`ITER2_IDX = range(7,15)` 实际只有 7 个 index，keff 是 index 7，但 OUT2 的 7 个非-keff 输出是 8-14。需确认各下游脚本里 ITER1/ITER2 索引是否正确。 | DELTA_PAIRS 计算、coupling analysis | 逐一检查 run_posterior*.py / run_forward*.py 里的索引用法 | ⬜ 待核实 |

---

## 🟠 高优先级问题

| ID | 问题 | 影响范围 | 建议处理 | 状态 |
|----|------|---------|---------|------|
| H01 | 论文里报告的 P(stress > 131 MPa) = 0.847 是"epistemic mean-only"（不含 aleatoric 采样），但附录里的旧结果文件有些是 predictive（含 aleatoric）。需确保正文只用 mean-only 结果，或统一说清楚用的是哪种。 | 正向传播结果表、失效概率数字 | 明确注明 mean-only，figure caption 需要区分 | ⬜ 待处理 |
| H02 | nearest-neighbor HF 验证不能说成"高保真重跑验证"，只能说"最近邻 HF case 检索"。旧文本里有地方表述过度，需逐一核查。 | 后验推断部分论文表述 | 搜索 "exact HF" / "rerun" 等词，替换为准确表述 | ⬜ 待核查 |
| H03 | `phy-mono` 模型中，`E_slope` 的物理符号方向（+1 还是 -1 对应 stress）需要确认。E_slope 是负值，更大的负值 → 高温 E 更低 → 可能降低应力，但符号在数据约定中需要确认。 | phy-mono 训练正确性 | 与导师确认，更新 `PHYSICS_PRIOR_PAIRS_RAW` | ⬜ 待核实 |
| H04 | keff 与 alpha_base/alpha_slope 的方向关系在 `PHYSICS_PRIOR_PAIRS_RAW` 中标记为 medium confidence，标注了"待核实"。若用于 phy-mono 训练，需先确认物理方向。 | phy-mono keff 方向约束 | 标记为"high confidence only"版本，暂不加入 keff 约束 | ⬜ 已临时规避（只用 high pairs） |

---

## 🟡 中等问题

| ID | 问题 | 影响范围 | 建议处理 | 状态 |
|----|------|---------|---------|------|
| M01 | repeated split 评估中，用 fixed-split 的最优超参再训练（不重跑 Optuna）。这可能低估或高估模型在不同 split 上的真实方差，因为超参可能对特定 split 有轻微过拟合。 | repeated split 结论 | 文中需说明这一假设；可做一次简单检验（1个模型重跑 Optuna on 不同 split） | ⬜ 待说明 |
| M02 | 数据集 CSV_PATH 指向服务器路径，本地无法直接访问。所有依赖原始 CSV 的脚本（如重新训练时）需要服务器可达。需要本地训练时必须先 rsync 数据。 | 本地可复现性 | 添加本地回退逻辑（已在 experiment_config_0404.py 中加了 get_csv_path()） | 🟡 已加回退，但训练仍需服务器 |
| M03 | MCMC 固定 4 个参数（E_intercept, alpha_base, alpha_slope, nu），另 4 个固定在先验均值。这个选择的物理合理性需要在论文中简单说明（为何选这 4 个而不是全部 8 个）。 | 后验推断方法描述 | 在论文方法节补充说明：这 4 个参数 Sobol 敏感度高，且与应力有显著相关 | ⬜ 待补充说明 |
| M04 | Optuna 40 trials 是否足够？目前基于经验判断。对于 8-10 维连续+离散混合空间，理论上更多 trials 更好，但资源有限。 | 所有模型超参搜索质量 | 文中注明"40 trials TPE"，或做一次 40 vs 80 trials 对比验证 | ⬜ 待核实，见 docs/repeated_split_rationale.md |

---

## 🟢 低优先级问题

| ID | 问题 | 影响范围 | 建议处理 | 状态 |
|----|------|---------|---------|------|
| L01 | 旧代码中 level1 loss（`loss_level1_shifted`）是占位符，返回 0.0。相关 level1 运行结果（若有）与 level0 等价，需要废弃或标注。 | 旧实验结果可信性 | 在 deprecated_models 里已记录，不影响新体系 | ✅ 已记录 |
| L02 | 部分旧图表使用 level0/level2 命名，需要在论文最终版替换为 baseline/regularized。 | 论文图表一致性 | 最终清稿前统一替换 | ⬜ 待清稿 |
| L03 | `run_phys_levels_main.py` 里的 bootstrap monotone pairs（level4）代码存在但未测试充分，可能有 edge case。 | level4 模型（已废弃） | 已废弃，不影响主线 | ✅ 废弃，不处理 |
