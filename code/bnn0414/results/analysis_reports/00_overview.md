# bnn0414 全量实验分析总览

**数据来源**：`tjzs@100.68.18.85:/home/tjzs/Documents/fenics_data/hpr_surrogate/hpr-claude-project/code/bnn0414/`，于 2026-04-16 同步到本地 `code/bnn0414/code/{models,experiments,_config}`。
**对比模型**：`bnn-baseline`, `bnn-data-mono`, `bnn-phy-mono`, `bnn-data-mono-ineq`
**主文轴**（按用户约定）：baseline vs data-mono-ineq；其余两个作为消融放附录。
**Posterior 版本**：最新 `experiments/posterior/`（忽略 `posterior.bak_20260415_215948/`）

---

## 一句话总结各实验
| 实验 | 结论 |
|---|---|
| Accuracy (fixed + 5 seeds) | 四模型 R² ~0.74–0.76；PICP 全部 ≥0.96（已校准）；data-mono-ineq 区间最宽、CRPS 最差，phy-mono 区间最窄且保持覆盖 |
| Speed | bnn-baseline 单样本 MC vs HF 加速 ~2.8×10⁵，批处理样本级 ~2.7×10⁸；HF 参考 3600 s/case |
| Sensitivity | 与 CLAUDE.md 0405 canonical **定性一致**：E_intercept 支配 stress，alpha_base 支配 keff；但数值有漂移（详见 03） |
| Physics consistency | 10 对 (input, output) × 435 点，全部 frac_correct = 1.0；run_record 标 fail 应为下游步失败而非本身不通过 |
| Risk propagation | 4 模型在 131 MPa 阈值下 P_exceed = 0.816–0.845；data-mono-ineq 最保守（0.816） |
| Generalization | OOD PICP 保持 0.97–0.99；OOD R² 反而略高于 in-dist（可能为子集尺寸效应），data-mono-ineq epistemic_std 最大 |
| Posterior (18 cases) | acceptance 0.58–0.67；90CI coverage 0.889–0.917；HF-rerun **phy-mono 54/54 完成**（stress MAE 5.65 MPa, [5%,95%] 覆盖 18/18）；data-mono-ineq 只写了 inputs |

---

## 主文可靠陈述（baseline vs data-mono-ineq）

1. **标定区间**：data-mono-ineq 的 PICP_mean = 0.980 vs baseline 0.969（@ fixed_eval），以更宽区间（MPIW 21.0 vs 16.3）换取更保守的覆盖。
2. **点估计**：data-mono-ineq MAE 稍差（2.876 vs 2.771），R² 略低（0.740 vs 0.758）。
3. **风险外推**：131 MPa 阈值处 baseline P_exceed = 0.841、data-mono-ineq = 0.816（保守约 2.5 个百分点）。data-mono-ineq 在 σ_k=2.0 下仍保 0.725，鲁棒性更好。
4. **后验标定**：18 cases 平均 acceptance 0.659（data-mono-ineq） vs 0.621（baseline）；90CI coverage 都在 0.89 左右。
5. **物理一致**：两者 gradient-sign 都 100% 通过。

## ⚠️ 需要与用户确认 / 不建议现在入正文的点

1. **HF rerun**：`posterior/bnn-phy-mono/hf_rerun/results/` 已完成 54/54（2026-04-16），post-hoc 解析后 summary 见 `posterior_hf_rerun_summary_rebuilt.csv`。`posterior/bnn-data-mono-ineq/hf_rerun/` 仅写了 inputs、未运行。正文 §2.4 已引用 phy-mono 结果并指向附录 N。
2. **Posterior 与旧 memory 不符**：CLAUDE.md 记录 phy-mono 0.875 coverage / 0.47–0.61 acceptance；新跑出 0.917 / 0.58–0.62。需要更新 memory（见文末）。
3. **Sobol 数值漂移**：E_intercept S1（stress）从 memory 的 0.598 → 0.504–0.582（按模型）；baseline 最接近旧值。若正文要继续引 0.598，需要改成当前值。
4. **run_record 将 physics_consistency 和 figures 标 fail**：但 CSV/JSON 实际完整。应具体查看 log 判定是否下游出图失败 —— 不影响数值结论。
5. **feasible_region.csv 仅含 low+near，无 high-stress**：CLAUDE.md 里"high-stress P(>131)=0.63–1.0"的断言**不能**从当前 `feasible_region.csv` 直接复核；需要看 `benchmark_summary.csv` 的 high 子集（已在 07 中补记）。
6. **Generalization 表 OOD R² > in-dist R²**：反直觉，通常说明 OOD 子集方差大、R² 统计性质有偏。不建议写成"OOD 泛化好"，应改为"OOD 区间仍覆盖、点估计 MAE 略升"。
7. **Sensitivity 输出只含 stress 与 keff**，无 fuel_temp / monolith_temp，不能在正文写"四个主输出的 Sobol"。

---

## 分报告索引
- `01_accuracy.md` — fixed_eval + 5-seed repeat
- `02_speed.md` — 计算加速
- `03_sensitivity.md` — Sobol / Spearman / PRCC
- `04_physics_consistency.md` — 梯度符号
- `05_risk_propagation.md` — 阈值风险 + σ_k 扫描
- `06_generalization.md` — OOD 四种
- `07_posterior.md` — 18 benchmark 后验

## Memory 更新建议（用户审阅后可执行）
- 更新 `project_sobol_canonical.md`：将 E_intercept stress S1 更新为 bnn0414 下 baseline=0.582、data-mono=0.504、phy-mono=0.545、data-mono-ineq=0.558（CI 详见 03）；alpha_base keff S1 更新为 0.742–0.784。
- 更新 `project_posterior_canonical.md`：coverage 区间扩至 0.889–0.917；acceptance 0.58–0.67；HF-rerun phy-mono 54/54 已完成。
