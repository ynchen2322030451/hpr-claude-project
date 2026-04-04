# 重复划分评估方案说明

**日期**：2026-04-04

---

## 1. 为什么需要 repeated split

Fixed split 评估只反映在一个特定训练/测试划分上的性能，存在以下问题：
- 结果对这个具体划分有潜在偏差（split-dependent）
- 无法量化模型性能对数据划分的敏感度
- 某些极端情况下，一个固定 split 会系统性高估或低估

Repeated split（重复随机划分）可以提供：
- 更可靠的期望性能估计（均值）
- 性能方差估计（对比模型间的稳定性）
- 对"某个模型是否真的稳定优于另一个"的统计支持

---

## 2. 推荐方案：5次重复（R=5）

### 为什么是 5 次

**研究实践参考：**
- Raschka (2018, arXiv:1811.12808) 对中等规模数据集（n ≈ 1000-10000）建议：
  5-10 次重复随机划分或 5-fold 交叉验证，足以估计性能方差。
- Bischl et al. (2023, mlr-org) 建议：当 n > 1000 时，5x 重复已能给出稳定估计。
- 本项目 n = 2900，属于中等规模，5 次已能提供有意义的方差估计。

**工程折中：**
| 重复次数 | 训练时间（估算，每次 ~10-20min with Optuna） | 方差估计质量 |
|---------|-------------------------------------------|------------|
| 1 次（fixed only） | ~15-20 min × 2 models = ~40 min | 无方差 |
| 5 次 | ~40 min × 5 = ~200 min | 可靠 |
| 10 次 | ~400 min | 更好，但边际递减 |
| 20 次 | ~800 min | 过度，收益很小 |

结论：**5 次是在该项目规模下工程上可接受的默认方案**。

**【待核实】**：若模型训练时间超过预期（服务器繁忙/模型更复杂），可降至 3 次。
若时间允许且对稳定性非常在意，可增至 10 次。

### 随机种子

固定种子列表：`[2026, 2027, 2028, 2029, 2030]`，保证可复现性。

---

## 3. 关于超参数搜索的决定

**方案：不对每个 split 重跑 Optuna，而是复用 fixed-split 的最优超参。**

原因：
- 重跑 Optuna（40 trials × 5 splits）会将训练时间增加 5 倍
- 目的是评估 **split 稳定性**，而非 **超参-split 交叉效应**
- 固定超参时的跨 split 方差是"纯粹的 split 效应"，对于性能稳定性结论更干净

潜在局限（需在报告中说明）：
- 超参可能对 fixed split 的验证集有轻微过拟合
- 不同 split 上的最优超参可能略有不同
- 因此 repeated split 结果更应视为"固定超参下的 split 敏感性检验"

**建议论文表述**：
> "To assess split sensitivity, we retrain each model with fixed hyperparameters 
> (optimized on the primary fixed split) over five additional random splits. 
> The resulting performance variance provides an estimate of split sensitivity 
> independent of hyperparameter reoptimization."

---

## 4. 报告格式

repeated split 结果应报告：
- 均值 ± 标准差（across 5 splits）
- 每个 split 的单独结果（附录表格）
- 与 fixed split 结果的比较

如果 std 很小（< 1% relative），说明模型对 split 稳定。
如果 std 较大，说明结论对 split 敏感，需要在论文中注明。
