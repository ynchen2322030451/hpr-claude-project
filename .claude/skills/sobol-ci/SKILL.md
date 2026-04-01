---
name: sobol-ci
description: Interpret Sobol sensitivity results with confidence intervals for the HPR surrogate project.
---
﻿
Use this skill for Sobol interpretation, ranking, CI-aware discussion, and manuscript writing，还有画敏感性热力图
﻿
Workflow:
1. Prefer `paper_sobol_results_with_ci.csv` and `paper_sobol_methods_ready_summary.csv`.
2. Distinguish:
- stable_positive
- crosses_zero
3. Do not over-interpret factors whose CI crosses zero.
4. For stress and keff, emphasize top stable contributors only.
5. Keep mechanistic interpretation separate from statistical evidence.
6.根据敏感性分析结果画图，可以参考我上传的旧稿子rpha文章中的敏感性热力图，其中输出名称要和论文中的统一，体现出多物理场耦合与没有耦合的对比，如果st和s1都很接近的话就解释一下为什么接近然后只保留st就好了，要svg和png两个版本的，或者你把这个留下来让画图agent做也可以
﻿
Writing rules:
- Report ST before mechanistic interpretation.
- Use “dominant contributor”, “secondary contributor”, and “not robustly interpretable”.
- Flag any statement inconsistent with the saved summary tables.
- 如果某个因素置信区间跨零，只能写成“当前证据不足以支持其为稳定主导因素”。
- 中文写作中，先写统计结果，再写物理解释，避免把相关性直接写成因果性。