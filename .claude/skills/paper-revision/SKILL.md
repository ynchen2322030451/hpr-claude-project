---
name: paper-revision
description: Edit the manuscript in rigorous academic style for the HPR surrogate paper, preserving evidence-claim separation.
---
﻿
Use this skill for manuscript restructuring, section rewriting, appendix migration, and consistency checking.
﻿
Workflow:
1. Read the relevant manuscript fragment first.
2. Identify:
- statements supported by saved tables
- statements requiring verification
- statements that belong in appendix
3. Preserve main text logic:
- model performance
- forward UQ and stress-risk
- Sobol mechanism discussion
- observation-driven posterior inference
-多物理耦合的重要性要强调
4. For threshold discussion:
- 131 MPa stays in main text
- 110/120 MPa move to appendix unless explicitly requested
﻿
Always:
- mark unsupported numbers as 【待核实】
- separate evidence from interpretation
- flag wording that overclaims engineering generality
-保证严谨的论文行文结构，可以参考nature computational science的其他期刊
-要保证数据来源于实验 并且严谨能经得起最严厉的业内专家的审视也要经得起跨行专家的提问
-提醒我所有逻辑不严谨的地方

你负责论文写作分支时，默认遵循以下规则：
	1.	论文主线固定为：
这不是一篇“新神经网络应用到 reactor”的文章，而是一篇“面向复杂安全关键多物理系统的 uncertainty-to-risk-to-feasible-region 分析框架”文章，reactor 只是强耦合高风险应用验证场景。
	2.	主文 Results 只保留四大块：
	•	Dataset and model selection
	•	Forward uncertainty propagation and stress-risk quantification
	•	Sensitivity attribution and uncertainty amplification
	•	Observation-driven posterior inference and safety-feasible region analysis
OOD、开发路径、更多模型变体默认放入 Discussion / Supplementary，除非我明确要求提升到主文。
	3.	主文模型比较默认只保留：
	•	baseline probabilistic neural model
	•	physics-regularized probabilistic neural model
不再把 Level1/4 作为主文主图主表内容。
	4.	术语必须去代码化。主文中默认使用工程表达，而不是代码字段名：
	•	iteration2_max_global_stress → second-iteration maximum global stress
	•	iteration2_keff → second-iteration effective multiplication factor
	•	Level0 / Level2 → baseline / regularized model
	•	MGX → variance-based global sensitivity analysis / Sobol analysis
	5.	语言风格要求：
	•	句子短一些，主判断明确
	•	少用过满表述，如“demonstrates / proves / confirms”，优先用“suggests / indicates / is consistent with”
	•	先写结果，再写解释，再写意义
	•	不要像内部报告，不要像代码注释，不要像学生作业
	•	保持 NCS 风格：克制、清楚、以问题和结论为中心
	6.	对于不确定、尚未冻结、需要我确认的地方，必须用【】明确标出，不允许默认编造。
	7.	旧稿默认只作为素材库，不作为主文事实来源。凡涉及输出数量、反演写法、阈值设定、模型选择等关键信息，优先以当前冻结代码、最新结果表和最新主稿为准。

When you work on the paper-writing branch, follow these default rules:
	1.	The paper must be framed as:
This is not a “new neural network applied to a reactor” paper. It is an uncertainty-to-risk-to-feasible-region framework for complex safety-critical multiphysics systems, with the reactor serving only as a representative high-risk, strongly coupled validation case.
	2.	The main-text Results should be restricted to four blocks only:
	•	Dataset and model selection
	•	Forward uncertainty propagation and stress-risk quantification
	•	Sensitivity attribution and uncertainty amplification
	•	Observation-driven posterior inference and safety-feasible region analysis
OOD, development-path comparisons, and additional model variants should go to the Discussion or Supplementary Information unless I explicitly ask to elevate them.
	3.	The main-text model comparison should default to only:
	•	baseline probabilistic neural model
	•	physics-regularized probabilistic neural model
Do not use Level1/4 as main-text figure or table content unless explicitly requested.
	4.	De-code the terminology. In the manuscript, default to engineering language rather than raw field names:
	•	iteration2_max_global_stress → second-iteration maximum global stress
	•	iteration2_keff → second-iteration effective multiplication factor
	•	Level0 / Level2 → baseline / regularized model
	•	MGX → variance-based global sensitivity analysis / Sobol analysis
	5.	Writing style requirements:
	•	shorter sentences
	•	explicit main claim per paragraph
	•	prefer “suggests / indicates / is consistent with” over “demonstrates / proves / confirms” unless the evidence is exceptionally strong
	•	write result → interpretation → significance
	•	do not sound like an internal report, code comment, or student draft
	•	keep the tone NCS-like: restrained, clear, and conclusion-driven
	6.	Any uncertain, unfrozen, or user-dependent point must be explicitly marked with 【】 rather than guessed.
	7.	Old drafts should be treated as a materials bank, not as the source of record. For output definitions, inverse formulation, threshold logic, model selection, and all core claims, always prioritize the current frozen code, latest result tables, and the latest manuscript direction.