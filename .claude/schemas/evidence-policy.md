# 证据政策（Evidence Policy）

所有写作、编辑、审查模块必须遵守本政策。

---

## 四类陈述的区分

| 类别 | 定义 | 写法示例 | 标记 |
|------|------|---------|------|
| **事实** | 直接来自保存的文件（CSV/JSON/图） | "The R² of σ_max is 0.929 (Table 1)." | 无需标记 |
| **解释** | 作者对事实的机制性解读 | "This suggests that the monotonicity constraint..." | "suggests", "indicates" |
| **推测** | 合理但未验证的推断 | "This may be attributable to..." | "may", "possibly" |
| **待核实** | 需要但尚未确认的数字或来源 | — | 【待核实】 |

---

## 强制规则

1. **不允许把推测写成事实**
   - ✗ "The regularization prevents overfitting."
   - ✓ "The lower test NLL suggests that regularization may reduce overfitting."

2. **不允许引用未在文件中出现的数字**
   - 任何未在 CSV/JSON/图中核对的数字 → 【待核实】
   - 不允许在论文中使用"代理记忆"中的数字

3. **不允许把近邻 HF 检索描述为 HF 重跑验证**
   - ✗ "validated against high-fidelity simulations"
   - ✓ "compared against nearest-neighbor high-fidelity proxy outputs"

4. **比较必须指明基准**
   - ✗ "improves performance"
   - ✓ "reduces RMSE by 12% relative to the baseline model"

5. **Sobol CI 跨零不得写为主导因素**
   - ✗ "E_slope is a dominant contributor"（若 CI 跨零）
   - ✓ "Current evidence is insufficient to establish E_slope as a stable contributor"

6. **P(stress > threshold) 必须注明扰动幅度**
   - ✗ "stress exceedance probability is 84.7%"
   - ✓ "under 1σ material uncertainty, stress exceedance probability is X%"

---

## 待核实标记规则

- 用 【待核实】 标记，不用 (TBD), (?), [check]
- 标记必须包含：问题所在 + 需要什么文件来核实
- 例：【待核实：需核对 paper_focus_metrics_level2.csv 中 keff 的 PICP90 值】

---

## 论文各节的证据要求

| 章节 | 允许的陈述类型 | 禁止 |
|------|--------------|------|
| Abstract | 事实 + 极少量解释 | 推测、宣传性语言 |
| Introduction | 背景事实 + 他人工作（需引用） | 本文未做的工作 |
| Methods | 实现细节（事实） | 解释机制（→ Discussion） |
| Results | 事实 + 直接观察 | 机制解释、意义讨论 |
| Discussion | 解释 + 推测（清晰标注） + 局限性 | 新事实（→ Results） |
| Conclusion | 事实性总结 + 有限推广 | 夸大普适性 |
