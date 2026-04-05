---
name: paper-revision
description: Edit the manuscript in rigorous NCS-style academic writing for the HPR surrogate paper. Handles section rewriting, bilingual drafting, structure adjustment, evidence checking, and terminology unification.
---

## 职责边界（不越界）

本 skill 负责：论文草稿写作、修改、润色、结构调整、术语统一、证据检查。

不负责：
- 运行代码/分析（→ forward-uq / inverse-benchmark / sobol-ci）
- 审图表数字一致性（→ figure-audit）
- 代码修改（→ code-safe-edit）

---

## 必须遵守的约束（非可选）

参考 `.claude/schemas/evidence-policy.md`（所有规则强制）：
1. 事实 / 解释 / 推测 分开表达
2. 未核实数字写【待核实】，不猜
3. 近邻 HF 检索 ≠ HF 重跑验证
4. Sobol CI 跨零 → 不写"主导因素"
5. P(σ > threshold) 必须注明 k·σ 扰动倍数（主文用 k=1.0）
6. 比较必须给基准

参考 `.claude/styles/ncs-style-profile.md`（风格约束）：
- 短句，主判断明确，先结论后括号引图
- Results 不混 Discussion
- 禁用过强动词：demonstrates→suggests，proves→indicates
- 无宣传性语言

---

## 子任务分类

### A. 写新段落/重写某节
1. 读当前稿件相关段落
2. 读术语表 + 风格规范
3. 确认有文件支撑的数字，未确认标【待核实】
4. 产出：中英双语（自然段交替）

### B. 结构调整（主文/附录）
主文固定四块：
1. Dataset and model selection
2. Forward uncertainty propagation and stress-risk
3. Sensitivity attribution
4. Posterior inference and safety-feasible region

移附录：110/120 MPa 扫描 / repeated split 细节 / 消融对比 / OOD 细节

### C. 术语统一
对照 `.claude/styles/ncs-style-profile.md` 术语表扫描全稿。
输出：不一致项列表 + 建议替换。

### D. 证据-结论检查
对每个量化声明核对来源文件。
输出三栏表：原句 | 支撑文件 | OK / 【待核实】

---

## 本项目固定规则

- 131 MPa 留主文；110/120 MPa 仅附录
- P(stress > 131) 主文报告 k=1.0σ，表格展示完整风险曲线
- 主文模型名：baseline / physics-regularized（不用 Level 0/2 / data-mono）
- 中英双语，中文不做英文直译

---

## 输出格式

```
## 正文
[中英文双语，自然段交替]

## 证据状态
| 声明 | 支撑文件 | 状态 |
|------|---------|------|
| ...  | ...     | OK / 【待核实】 |

## 待核实清单
- 【待核实】：问题描述 → 需核对的文件名
```
