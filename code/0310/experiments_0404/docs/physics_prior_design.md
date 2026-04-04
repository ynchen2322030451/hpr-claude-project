# phy-mono 物理先验设计说明

**日期**：2026-04-04  
**对应模型**：`phy-mono`（Physics-Prior Monotone）

---

## 1. 设计动机

`data-mono` 模型的单调性约束来自训练数据的 Spearman 秩相关，这存在一个根本问题：
**数据告诉你"是什么"，但无法区分是物理规律还是数据采样偏差。**

`phy-mono` 模型的单调性方向完全由**物理分析先验指定**，不依赖数据统计。
这使得两种模型可以直接比较：
- 如果 `phy-mono ≈ data-mono`（精度相近），说明 Spearman 对确实在捕捉物理规律。
- 如果差异显著，需要追问：是数据方向有噪声，还是物理先验有错误？

---

## 2. 物理先验对（高置信度）

下表为当前纳入 `phy-mono` 主版本（high confidence）的物理单调对。

| 输入参数 | 输出量 | 方向 | 物理原因 | 置信度 |
|---------|--------|------|---------|-------|
| E_intercept | iter2_max_global_stress | +1 | 更高基础弹性模量 → 更强刚性 → 温差诱导更大热应力 | 高 |
| alpha_base | iter2_max_global_stress | +1 | 更高热膨胀系数基准 → 更大热应变 → 更大约束应力 | 高 |
| SS316_k_ref | iter2_max_global_stress | -1 | 更好导热性 → 更均匀温度场 → 更小温度梯度 → 更低应力 | 高 |
| E_intercept | iter1_max_global_stress | +1 | 同 iter2，作用于第一轮解耦预测 | 高 |
| alpha_base | iter1_max_global_stress | +1 | 同 iter2，作用于第一轮解耦预测 | 高 |
| SS316_k_ref | iter1_max_global_stress | -1 | 同 iter2 | 高 |
| SS316_k_ref | iter2_max_fuel_temp | -1 | 更好 SS316 导热 → 热管传热能力更强 → 燃料温度更低 | 高 |
| SS316_k_ref | iter1_max_fuel_temp | -1 | 同 iter2 | 高 |
| SS316_k_ref | iter2_max_monolith_temp | -1 | 更好导热 → 单石温度更低 | 高 |
| SS316_k_ref | iter1_max_monolith_temp | -1 | 同 iter2 | 高 |

---

## 3. 中等置信度对（暂不纳入主版本）

下列关系物理上合理但有一定不确定性，暂不纳入 `phy-mono` 主版本。
可用于附录消融或未来研究。

| 输入参数 | 输出量 | 方向 | 物理原因 | 不确定性来源 |
|---------|--------|------|---------|------------|
| alpha_slope | iter2_max_global_stress | +1 | 高温下热膨胀斜率更大 → 运行温度下膨胀增大 → 应力↑ | 方向依赖具体温度分布，数值效果待验证 |
| E_slope | iter2_max_global_stress | +1 | E_slope 为负值；数值更大（更接近 0）→ 高温 E 下降更慢 → 刚性更高 → 应力可能更大 | 符号约定与数据分布需要核对【待核实】 |
| SS316_alpha | iter2_max_fuel_temp | -1 | k(T) = k_ref + alpha*(T-T_ref)，alpha 更大 → 高温导热更好 → 温度更低 | 间接效应，幅度小 |
| alpha_base | iter2_keff | -1 | 高热膨胀 → 堆芯几何膨胀 → 中子泄漏增加 → keff 降低（耦合稳态中） | 实际 keff 受多因素影响，方向可能被其他效应抵消【待核实】 |
| alpha_slope | iter2_keff | -1 | 同 alpha_base，温度依赖版本 | 同上【待核实】 |

---

## 4. 与 data-mono 对的比较

当前 `data-mono` 用 Spearman 秩相关从训练数据提取单调对，top-40 对（|ρ| > 0.25）。
`phy-mono` 使用上述 10 个 high-confidence 物理对。

**预期差异：**
- 数量：data-mono 用 40 对，phy-mono 用 10 对（更稀疏）
- 覆盖：data-mono 可能包含一些物理上不那么清晰但数据统计显著的对
- 权重：data-mono 用 |ρ| 作为权重，phy-mono 用均匀权重（或手动指定）

**如果 phy-mono 精度与 data-mono 相当：**
→ 说明 Spearman 对确实在压缩的 10 个物理对附近 → 支持方法的物理解释性

**如果 phy-mono 明显更差：**
→ 说明 Spearman 捕捉到了物理分析未涵盖的额外信息
→ 可能原因：(a) 数据噪声方向有信号价值，(b) 物理对选错，(c) 权重设计问题

---

## 5. 论文写作建议（E5）

如果要在论文中写"先验知识驱动的正则化"，建议这样表述：

> "The second regularization strategy encodes expert-specified input–output monotonicity 
> relationships derived from physical reasoning, independently of training data statistics. 
> For each physically motivated pair $(x_i, y_j)$, the expected sign of the gradient 
> $\partial \mu_j / \partial x_i$ is prescribed based on material mechanics and heat transfer 
> principles (Table X). The gradient penalty penalises violations of these sign constraints 
> throughout training, providing a physical prior that is complementary to, and distinguishable 
> from, the data-derived Spearman regularization of the proposed model."

避免说：
- ❌ "proves that the data-derived monotonicity captures physics" — 过度声称
- ❌ "we use physics-informed neural networks" — 与 PINN 混淆
- ✅ "physics-prior constrained training" 或 "expert-specified monotonicity regularization"

---

## 6. 待确认事项

- [ ] 与导师确认 E_slope 在高温下的方向效应（medium confidence 里的 H03 问题）
- [ ] 确认 alpha_base → keff 方向（依赖反应堆几何构型）
- [ ] 是否把 alpha_slope 纳入 high confidence（需数值验证）
