# 待确认问题清单

**最后更新**：2026-04-04  
**说明**：这些是需要进一步思考或与导师确认的问题，不是错误。

---

## 模型设计类

**Q1. 主文应该呈现几个模型？**  
现在的计划是 baseline + data-mono 作为主文，phy-mono 作为消融。  
问题：phy-mono 是否有足够的论文可写性？还是作为附录更合适？  
→ 建议先训练出来，看精度差距，再决定。

**Q2. 物理先验对的数量是否合理（目前 10 个 high confidence）？**  
data-mono 用 40 对，phy-mono 只用 10 对。这个不对称是否会让比较不公平？  
选项：(a) 把 phy-mono 也用更多对（加入 medium confidence）；  
       (b) 保持稀疏（10对），强调"高置信度先验比大量弱约束更好"；  
       (c) 同时训练两个 phy-mono 版本（high-only 和 all）  
→ 待决定。

**Q3. phy-ineq 是否真的有附录价值？**  
inequality 约束（max≥avg，stress≥0）在实际数据中几乎总是满足的。  
这个约束的主要价值可能是 OOD 时防止物理荒谬预测，而不是 in-distribution 精度。  
是否值得专门做一个模型？  
→ 待评估。

---

## 实验设计类

**Q4. risk_propagation D2（代表性 case 扰动）如何选 case？**  
选取标准：低应力（<120 MPa）、近阈值（125-135 MPa）、超阈值（>140 MPa）、极端（>180 MPa）。  
从 test split 选还是从训练集？从多少 case？每类选几个？  
→ 初步方案：各类从 test 集随机选 3 个，共约 12 个 case。

**Q5. posterior_inference 的可行域分析如何定义？**  
"可行域"可以是：(a) P(stress < 131 | posterior) > 0.9 的参数区间；  
               (b) 后验 credible interval 在 stress < 131 的投影；  
               (c) 2D 切片（某两个参数 pair）。  
→ 建议先做 (c)（最直观），再看是否需要 (a)。

**Q6. 多物理耦合路径分析（D3）应聚焦哪些输出对？**  
候选：stress_iter1 → stress_iter2；keff_iter1 → keff_iter2；temp_iter1 → temp_iter2。  
还是应该分析"输入 → 中间变量 → 最终应力"的传递链？  
→ 先做简单的 iter1 vs iter2 统计（均值偏移、方差比），再看是否需要更深的路径分析。

---

## 写作类

**Q7. Sobol CI 跨零的因素应如何在正文呈现？**  
现有约定是"不得写成稳定主导因素"。  
但如果多个因素的 CI 都跨零，如何写结论？  
是否需要做更大 N 的 Sobol 来缩小 CI？  
→ 建议：正文只报告 CI 不跨零的因素；跨零的放附录，说明"证据不足"。

**Q8. P(>131) = 0.847 的表述是否会引起审稿人质疑？**  
现在已有参考文献支撑（原始设计应力可达 169 MPa），但审稿人可能仍觉得"太高"。  
是否需要补充额外的物理解释或图表？  
→ 建议：在图 caption 或正文加一句说明标称设计的应力范围，引用 Zhang et al. 2025。

**Q9. 论文定位是"不确定性量化框架"还是"概率代理模型"？**  
这影响摘要重点和 Introduction 叙事。  
当前倾向：框架（framework），reactor 只是验证场景。  
→ 已在 CLAUDE.md 里定义。但需要确认 Introduction 写法是否与此一致。
