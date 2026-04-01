---
name: inverse-benchmark
description: Handle reduced/full inverse benchmark, posterior contraction, and feasible-region analysis for the HPR surrogate project.
---
﻿
Use this skill when working on inverse UQ, posterior inference, feasible-region plots, or reduced-vs-full comparisons.
﻿
Workflow:
1. Check whether the request concerns:
- reduced main-text benchmark
- full vs reduced comparison
- contraction summary
- 2D feasible region export
2. Prefer existing saved result tables before rerunning.
3. When comparing methods, report:
- parameter recovery
- observable fit
- computational cost
4. If discussing engineering implications, separate:
- posterior-informed refinement
- safety-feasible-region screening
﻿
Do not:
- present inverse results as design truth without caveat
- mix demo thresholds with formal engineering standards unless sourced
- silently rerun MCMC or benchmark workflows without explicit permission
﻿
Writing rules:
- 先写结果表中能直接支撑的事实，再写解释。
- reduced vs full 的比较只能写成“在当前 benchmark 下”的判断，或者其他的结果不够硬的小发现，请说明但不能写成普遍结论。
- 如果某个参数恢复性或 observable fit 没有在现有 summary tables 中核对，标注为“待核实”。
- 如果正文只需要主线结果，优先使用 main-text reduced benchmark，不主动扩展到附录型细节。
-尽量参考我上传的李冬的博士论文 贝叶斯修正参数等方法。