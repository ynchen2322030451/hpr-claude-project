# GPT Upload Bundles

每个文件夹 ≤ 25 个文件，适合一次性上传到 ChatGPT 对话中。
文件名前缀编号方便排序阅读。

---

## A_figures/ — 画图任务 (140K, 25 files)

**用途**: 让 GPT 帮你生成/修改论文出版级图表（matplotlib → PDF/SVG/PPTX）

**包含**:
- NCS 样式规范 (`ncs_style.py`, `figure_style.py`, `STYLE_SPEC.md`)
- 图表规格说明 (`manuscript_spec.txt` × 6 张主图)
- 已有 compose 脚本示例 (`compose_fig2/3/4/6.py`)
- 绘图用数据 CSV（metrics, sobol, posterior, forward UQ 等）
- 实验配置（output 名称、阈值定义）

**建议 prompt**: "请根据 manuscript_spec 和 ncs_style 生成 fig4_sobol 的完整 matplotlib 代码，数据见 22_data_sobol.csv"

---

## B_paper_polish/ — 论文润色任务 (604K, 25 files)

**用途**: 让 GPT 帮你润色/改写/翻译论文正文、SI、rebuttal letter

**包含**:
- 英文稿 + 双语稿（正文 + SI，共 4 个 txt）
- intro/abstract LaTeX 源文件
- 核心贡献定位 (`CORE_CONTRIBUTION.md`)
- NCS 修改计划 + TODO (`NCS_REVISION_PLAN.md`, `NCS_TODO.md`)
- 逐条修改回复草稿（revision_1_4 到 revision_3_2，共 7 个）
- 证据链 + BNN 决策记录
- 文献库 (`LITERATURE_BANK.md`)
- 数据支撑摘要

**建议 prompt**: "请根据 NCS_REVISION_PLAN 和 revision_1_6_coverage.md 的审稿意见，重写 manuscript_en.txt 中 Section 3.4 的 posterior coverage 段落"

---

## C_experiment_logic/ — 实验逻辑完善任务 (476K, 25 files)

**用途**: 让 GPT 帮你审查/优化/扩展实验代码逻辑

**包含**:
- BNN 模型核心代码 (`bnn_model.py`, `bnn_multifidelity.py`)
- 实验配置 + 模型注册表 (`experiment_config.py`, `model_registry.py`)
- 主流水线入口 (`run_0404_main.py`)
- 训练/评估脚本
- 关键实验脚本 × 9（posterior, sensitivity, risk, calibration, speed, monotonicity, external baselines, sobol convergence, uncertainty decomposition）
- HF 仿真代码 (`fenics_thermal.py`)
- 实验结论概览 + 准确率分析

**建议 prompt**: "请审查 run_posterior.py 的 MCMC 采样逻辑，检查 burn-in、thinning、convergence diagnostics 是否合理"

---

## D_data_analysis/ — 数据分析与结果解读 (240K, 25 files)

**用途**: 让 GPT 帮你解读实验结果、验证 claims、补充分析

**包含**:
- 8 个分析报告（accuracy, speed, sensitivity, physics, risk, generalization, posterior）
- 权威数据摘要 (`CANONICAL_DATA.md`)
- 结果草稿 + 实验详情
- 关键 CSV 数据（metrics, sobol, forward UQ, posterior benchmark, interval quality）
- BNN 决策记录 + 证据链
- 审计清单 (`AUDIT_CHECKLIST.md`)
- 核心贡献 + 实验配置

**建议 prompt**: "请对照 CANONICAL_DATA.md 和 18_sobol_stress_keff.csv，检验论文中关于 Sobol 主效应因素排序的 claim 是否有数据支撑"
