#!/usr/bin/env python3
"""为 bnn0414 中所有 PNG 图片生成同名 .txt 说明文档。

每个文档包含：
  - 秒懂版：一句话 + 一段通俗解释
  - 详细版：数据来源、论文定位、阅读指南、关键数值
"""

import os
from pathlib import Path

BNN0414 = Path(__file__).resolve().parents[1]

# ═══════════════════════════════════════════════════════════════
# 说明文档内容
# ═══════════════════════════════════════════════════════════════

DESCRIPTIONS = {}

# ────────────────────────────────────────────────────────────
# Composed figures（正式论文图）
# ────────────────────────────────────────────────────────────

DESCRIPTIONS["manuscript/0414_v4/figures/fig0_workflow.png"] = """
================================================================================
fig0_workflow — 研究整体流程图
================================================================================

【秒懂版】
一句话：展示了从"材料参数不确定性"到"反应堆安全结论"的完整分析链条。

通俗解释：
这张图是整篇论文的"地图"。从左到右，8个不确定的材料参数（弹性模量、热膨胀系数等）
输入到高保真耦合仿真（OpenMC+FEniCS），生成约2900组训练数据；然后用贝叶斯神经网络
（BNN）学习这些数据，产出5个关键输出（应力、k_eff、温度等）的概率预测分布。最终
这个代理模型被用于四种分析：正向不确定性传播、Sobol敏感性分析、后验校准、高保真
一致性验证。相当于"花几天训练一个快速模型，代替原本需要几年的直接仿真"。

【详细版】
论文定位：Supplementary Fig. S1（补充材料第一张图）
论文作用：为读者提供全局方法论视角，是理解后续所有分析的入口

布局说明：
- 左侧两个色块：8个输入参数，分为认知不确定性（核数据 X1-X5）和偶然不确定性（制造 M1-M3）
- 中间色块：高保真求解器（先做非耦合pass，再做耦合稳态）→ BNN 代理模型 → 5个输出
- 右侧四个色块：四种下游分析应用
- 下方图例：实线=数据流，虚线=概率流，点线=验证

数据来源：概念图，无直接数据源
生成脚本：code/figures/compose/fig0_workflow.py → code/figures/bank/ 无（直接绘制）
"""

DESCRIPTIONS["manuscript/0414_v4/figures/fig1_accuracy.png"] = """
================================================================================
fig1_accuracy — 预测精度与校准质量
================================================================================

【秒懂版】
一句话：BNN预测的不确定性区间"说到做到"——说90%覆盖率就真的覆盖90%的数据。

通俗解释：
这张图回答"BNN的预测靠谱吗？"。Panel A 是可靠性图（reliability diagram），
如果模型说"90%的预测落在这个区间内"，那真实数据是否确实有90%落在区间内？
越贴近对角线说明校准越好。Panel B-C 是 PIT 直方图，理想情况应该是均匀的
（说明预测分布和真实分布一致）。Panel D-E 是不同模型间的评分规则对比（CRPS越低
越好，ECE越低越好），展示BNN在校准质量上优于 MC-Dropout 和 Deep Ensemble。

【详细版】
论文定位：主文 Fig. 1（对应 Results 第 2.1 节 Surrogate accuracy and calibration）
论文作用：建立代理模型的可信度基础——后续所有分析的前提是"模型预测靠谱"

布局（5 panels）：
- (A) 可靠性图：Reference BNN vs Physics-regularized BNN，5个输出量
- (B) PIT直方图（应力）
- (C) PIT直方图（k_eff）
- (D) CRPS评分条形图（越低越好）
- (E) ECE校准误差条形图（越低越好）

数据来源：
- results/accuracy/calibration_multi_alpha.csv
- results/accuracy/pit_values.npz
- results/master_comparison_table.csv

关键数值：
- phy-mono 应力 ECE = 0.106（所有模型中最低）
- BNN 燃料温度 RMSE ≈ 4.26 vs MC-Dropout 4.50 vs Ensemble 4.49
- 可靠性图两模型均紧贴对角线 → 校准良好

生成脚本：code/figures/compose/fig1_accuracy.py
组成子图：B4_calibration_reliability + B6_pit_histogram + B7_scoring_rules
"""

DESCRIPTIONS["manuscript/0414_v4/figures/fig2_predictive.png"] = """
================================================================================
fig2_predictive — 预测分布可视化（奇偶图）
================================================================================

【秒懂版】
一句话：每个测试样本的BNN预测值 vs 真实值散点图，越贴近对角线说明预测越准。

通俗解释：
三张子图分别展示应力、k_eff、燃料温度的预测效果。每个点代表一个测试样本，
X轴是高保真仿真的真实值，Y轴是BNN的预测均值，颜色深浅表示点的密度。
阴影带是90%预测区间。理想情况下所有点应该落在对角线上且被阴影带包裹。
应力图用了六角密度图（hexbin），因为样本多时散点图会太密集。

【详细版】
论文定位：主文 Fig. 2（对应 Results 第 2.1 节）
论文作用：直观展示"BNN预测有多准"，是精度评估最直观的一张图

布局（3 panels）：
- (A) 应力 parity plot（hexbin密度图 + PI带）
- (B) k_eff parity plot
- (C) 最大燃料温度 parity plot

数据来源：results/accuracy/ 目录下的 test predictions
生成脚本：code/figures/compose/fig2_predictive.py
组成子图：B1_stress_parity + B2_keff_parity + B3_thermal_parity
"""

DESCRIPTIONS["manuscript/0414_v4/figures/fig3_forward.png"] = """
================================================================================
fig3_forward — 正向不确定性传播与风险评估
================================================================================

【秒懂版】
一句话：材料参数的不确定性会让应力从"一个值"变成"一个分布"——耦合效应让应力降低约48 MPa。

通俗解释：
这张图回答"如果材料参数不确定，反应堆的安全指标会变成什么样？"。
Panel A 对比了非耦合（灰色）和耦合稳态（蓝色）下的应力分布——耦合后应力均值
降低了约48 MPa（Δμ = -47.8 MPa），说明忽略耦合效应会高估应力。
Panel B 展示 k_eff 的分布（很窄，σ=0.0007，说明反应性对材料不确定性不敏感）。
Panel C 是耦合引起的各输出偏移量。
Panel D 是应力超限概率曲线——在131 MPa设计限值下约96%的样本超限。

【详细版】
论文定位：主文 Fig. 3（对应 Results 第 2.3 节 Forward uncertainty propagation）
论文作用：核心结果之一——展示BNN正向传播不确定性的能力，以及耦合效应的影响

布局（4 panels）：
- (A) 应力分布对比：非耦合 pass vs 耦合稳态，标注均值差 Δμ
- (B) k_eff 分布（含 rug plot）
- (C) 耦合偏移量水平条形图（各输出的 coupled - uncoupled 差值）
- (D) 应力超限概率曲线 P(σ>τ)，三条线对应 τ = 110, 120, 131 MPa

数据来源：
- results/forward_uq/ 目录
- results/risk/ 目录

关键数值：
- 应力均值（耦合）≈ 163.55 MPa，σ ≈ 33.6 MPa
- k_eff 均值 ≈ 1.1035，σ ≈ 0.0007
- 耦合效应使应力降低 ~48 MPa

生成脚本：code/figures/compose/fig3_forward.py
组成子图：C1_stress_coupling + C2_keff_distribution + C4_coupling_delta + C3_risk_curve
"""

DESCRIPTIONS["manuscript/0414_v4/figures/fig4_sobol.png"] = """
================================================================================
fig4_sobol — Sobol 敏感性分析
================================================================================

【秒懂版】
一句话：应力主要被弹性模量截距 E_intercept 控制（~55%），k_eff 主要被热膨胀系数 α_base 控制（~77%）。

通俗解释：
Sobol分析回答"哪个材料参数对输出不确定性贡献最大？"。每根柱子代表一个参数
对输出方差的贡献，分为一阶效应 S₁（直接影响）和总效应 S_T（含交互作用）。
左图是应力：E_intercept 一个参数就解释了55%的方差，颜色按物理类别区分
（绿=弹性/结构，橙=热膨胀，紫=热传导）。右图是 k_eff：α_base 解释77%。
两个输出的主导参数几乎不重叠——这意味着实验测量可以并行进行。

【详细版】
论文定位：主文 Fig. 4 / Table 3（对应 Results 第 2.4 节 Sensitivity attribution）
论文作用：核心结果——指导实验优先级，"要减少应力不确定性，先测 E_intercept"

布局（2 panels）：
- (A) 耦合稳态最大应力的 S₁ 和 S_T（8个参数，按贡献排序）
- (B) 耦合 k_eff 的 S₁ 和 S_T

数据来源：results/sensitivity/ 目录
- 使用 N_base = 4096, 50 replications, 90% CI

关键数值：
- 应力 S₁: E_intercept = 0.548 [0.498, 0.572], α_base = 0.210
- k_eff S₁: α_base = 0.771 [0.747, 0.788], α_slope = 0.195
- S₁ ≈ S_T → 交互作用极小

生成脚本：code/figures/compose/fig4_sobol.py
组成子图：D3_sobol_total

注意：此图与 figA4_sobol_detail 目前内容重复，后续需区分
"""

DESCRIPTIONS["manuscript/0414_v4/figures/fig5_physics.png"] = """
================================================================================
fig5_physics — 物理一致性：单调性与不确定性分解
================================================================================

【秒懂版】
一句话：BNN学到的物理规律是对的（几乎零违反单调性），而且能区分"不知道"和"本来就随机"。

通俗解释：
Panel A 是单调性违反率热力图：物理上，增大弹性模量应该增大应力（正单调性），
BNN确实学到了这些关系（几乎全是0%违反率）。唯一的例外是 α_SS316 → 燃料温度
（~37%违反率），但这是一个物理上没有强单调关系的弱效应对。
Panel B 是不确定性分解：蓝色=认知不确定性（epistemic，模型不够确定，可通过
更多数据减少），灰色=偶然不确定性（aleatoric，数据本身固有的噪声）。
Wall temp 的 epistemic 占比最高（42%），说明模型在该输出上最需要更多训练数据。

【详细版】
论文定位：主文 Fig. 5（对应 Results 第 2.2 节 Physics consistency and regularization）
论文作用：展示物理正则化的效果——BNN不仅拟合数据，还遵守物理规律

布局（2 rows）：
- (A) 单调性违反率热力图：2个子图（Reference vs Physics-regularized），
      rows = 输入参数，cols = 4个主要输出，颜色 = 违反率（0%=绿，高%=红）
- (B) 不确定性分解条形图：5个输出，蓝色=epistemic fraction，灰色=aleatoric

数据来源：
- results/physics_consistency/monotonicity_violation_rate.csv
- results/uncertainty_decomposition/uncertainty_decomposition.csv

关键数值：
- 所有高置信单调对违反率 = 0%
- α_SS316 → fuel_temp 违反率 ~37%（物理上弱关系，可接受）
- Wall temp epistemic fraction = 42%（最高）
- k_eff epistemic fraction = 21%

生成脚本：code/figures/compose/fig5_physics.py
组成子图：F3_monotonicity + F4_uncertainty_decomp

注意：此图与 figA2_physics_robustness 目前内容重复，后续需区分
"""

DESCRIPTIONS["manuscript/0414_v4/figures/fig6_posterior.png"] = """
================================================================================
fig6_posterior — 后验校准：MCMC诊断与参数收缩
================================================================================

【秒懂版】
一句话：给BNN"看"一组观测数据后，它能正确地缩窄参数分布——从"什么都可能"变成"大概是这个范围"。

通俗解释：
这是全文最复杂也最重要的图之一。
Panel A（MCMC轨迹图）：4条彩色链条应该充分混合（说明采样收敛了），每行一个参数。
Panel B（先验→后验）：红色实线是后验分布（"看了数据后的信念"），浅粉色阴影是
先验分布（"看数据前的信念"）。后验比先验窄 → 数据提供了信息量。蓝色框是真实值
的位置。Panel C（R-hat诊断）：所有点应该在1.01虚线以下，说明链收敛了。
Panel D（ESS）：有效样本量应该在150虚线以上，说明采样效率足够。

【详细版】
论文定位：主文 Fig. 6 / Fig. 5（对应 Results 第 2.5 节 Posterior calibration）
论文作用：展示"反向问题"——从观测数据推断材料参数的能力

布局（4 panels）：
- (A) MCMC轨迹图：4个参数 × 4条独立链，1200次迭代
- (B) 先验 vs 后验边际分布：4个参数的对比，含真值标记
- (C) split-rank R̂：18个 benchmark cases × 4个参数，阈值线 1.01
- (D) ESS：18个 cases × 4个参数，阈值线 150

数据来源：
- code/experiments_0404/experiments/posterior/bnn-phy-mono/diagnostics/
- chains/case_*.npz（MCMC 链数据）
- mcmc_diagnostics.csv（R̂, ESS, acceptance rate）

关键数值：
- R̂_max = 1.017（<1.01 阈值内）
- ESS_min = 352（>150 阈值）
- Mean acceptance rate = 0.605
- 90%-CI coverage = 0.917（18 cases 中 17 个参数真值被覆盖）

生成脚本：code/figures/compose/fig6_posterior.py
组成子图：H1_mcmc_trace + E1_prior_posterior + H3_mcmc_diagnostics
"""

DESCRIPTIONS["manuscript/0414_v4/figures/fig7_efficiency.png"] = """
================================================================================
fig7_efficiency — 计算效率：加速比与数据效率
================================================================================

【秒懂版】
一句话：BNN比直接仿真快1.7亿倍，而且只需要500个训练样本就能达到可用精度。

通俗解释：
Panel A（加速比）：要得到同样精度的风险估计（P(σ>131 MPa)），高保真仿真需要
几百万秒（灰色柱子），而BNN只需要几秒（蓝色柱子，几乎看不到）。
加速比 ≈ 1.7×10⁸ 倍。这意味着原本需要几年的Monte Carlo分析，
BNN几秒就能完成。
Panel B（数据效率学习曲线）：随着训练集增大（500→2000），RMSE逐渐降低。
物理正则化的BNN（蓝线）在小训练集时表现更稳定。

【详细版】
论文定位：主文 Fig. 7（对应 Results 第 2.6 节 Computational cost）
论文作用：量化代理模型的实用价值——回答"用这个方法到底省多少时间？"

布局（2 panels）：
- (A) Budget-matched risk 对比条形图（log-y），X=目标CI半宽，Y=总耗时(秒)
- (B) 数据效率学习曲线：X=训练集大小，Y=应力RMSE，含置信区间阴影

数据来源：
- results/speed/budget_matched_risk.csv
- results/data_efficiency/data_efficiency_summary.csv

关键数值：
- 加速比 ≈ 1.7×10⁸（每次HF仿真 ~2266秒，BNN推断 ~13微秒）
- 在目标CI半宽 0.001 时，HF需 ~3.4×10⁸ 秒（~11年），BNN需 ~3秒
- 训练集500时 RMSE ≈ 4.95 MPa，2000时 ≈ 4.60 MPa

生成脚本：code/figures/compose/fig7_efficiency.py
组成子图：G1_speedup + F1_data_efficiency
"""

DESCRIPTIONS["manuscript/0414_v4/figures/figA1_model_validation.png"] = """
================================================================================
figA1_model_validation — 模型验证（附录 Extended Data）
================================================================================

【秒懂版】
一句话：把BNN和其他两种常用方法（MC-Dropout、Deep Ensemble）横向对比——BNN校准更好。

通俗解释：
Panel A 是可靠性图（同fig1），但只显示两个BNN变体的汇总对比。
Panel B 是6个模型 × 5个输出的 R² 条形图——柱子越长说明决定系数越高，
预测点越贴近真值。Panel C 是 RMSE 条形图（log-x），越短说明误差越小。
BNN在温度预测上RMSE几乎是外部基线的一半。但注意 k_eff 的 R²，
外部基线（MC-Dropout, Deep Ensemble）反而略高（~0.86 vs ~0.63）。

【详细版】
论文定位：Extended Data Fig. A1
论文作用：为正文的"BNN更好"提供更完整的对比证据

布局（3 panels）：
- (A) 可靠性图：Reference vs Physics-regularized
- (B) R²条形图：3种方法 × 5个输出
- (C) RMSE条形图（log-x）：3种方法 × 5个输出

数据来源：results/master_comparison_table.csv
生成脚本：code/figures/compose/figA1_model_validation.py
组成子图：B4_calibration_reliability + B5_external_baseline
"""

DESCRIPTIONS["manuscript/0414_v4/figures/figA2_physics_robustness.png"] = """
================================================================================
figA2_physics_robustness — 物理鲁棒性（附录 Extended Data）
================================================================================

【秒懂版】
一句话：与fig5相同的单调性+不确定性分解图（目前为重复图，后续需区分化）。

通俗解释：
当前版本与主文fig5完全相同——都展示单调性违反率和不确定性分解。
设计意图是作为附录扩展版，应当展示更多模型变体（如4个BNN全部对比）
或更多输出量的详细结果。待后续更新。

【详细版】
论文定位：Extended Data Fig. A2（待区分化）
论文作用：原设计为fig5的扩展版本

当前状态：与 fig5_physics 内容完全重复
计划改进：应展示全部4个BNN变体的单调性对比，或展示更多输出对

生成脚本：code/figures/compose/figA2_physics_robustness.py
组成子图：F3_monotonicity + F4_uncertainty_decomp（与fig5相同）
"""

DESCRIPTIONS["manuscript/0414_v4/figures/figA3_efficiency.png"] = """
================================================================================
figA3_efficiency — 效率综合图（附录 Extended Data）
================================================================================

【秒懂版】
一句话：把数据效率、OOD检测能力、计算加速比三个维度放在一张图里总览。

通俗解释：
Panel A（数据效率）：训练数据从500增加到2000时，RMSE如何下降？物理正则化的BNN
在小数据集时表现更稳定（蓝色带更窄）。
Panel B（OOD检测）：当输入参数超出训练范围时，BNN的epistemic不确定性是否会增大？
柱子>1说明确实增大了——BNN知道自己"不确定"，这是比MC-Dropout更好的性质。
虚线=1是分布内基线。
Panel C（计算加速）：与fig7(A)相同的加速比对比图。

【详细版】
论文定位：Extended Data Fig. A3
论文作用：将三个独立实验的结论整合展示

布局（1×3）：
- (A) F1_data_efficiency: 学习曲线
- (B) F2_ood_epistemic: OOD epistemic ratio（4个参数）
- (C) G1_speedup: 加速比条形图

数据来源：
- results/data_efficiency/data_efficiency_summary.csv
- results/ood/ood_calibration_comparison.csv
- results/speed/budget_matched_risk.csv

生成脚本：code/figures/compose/figA3_efficiency.py
"""

DESCRIPTIONS["manuscript/0414_v4/figures/figA4_sobol_detail.png"] = """
================================================================================
figA4_sobol_detail — Sobol 详细图（附录 Extended Data）
================================================================================

【秒懂版】
一句话：与fig4相同的Sobol敏感性柱状图（目前为重复图，后续需区分化）。

通俗解释：
当前版本与主文fig4完全相同。设计意图是作为附录扩展版，应展示更多输出量
（如燃料温度、单体温度、wall expansion 的Sobol指数），或对比全部4个BNN变体。

【详细版】
论文定位：Extended Data Fig. A4（待区分化）
当前状态：与 fig4_sobol 内容完全重复
计划改进：应展示 fuel temp / monolith temp / wall expansion 的 Sobol 指数

生成脚本：code/figures/compose/figA4_sobol_detail.py
组成子图：D3_sobol_total（与fig4相同）
"""

DESCRIPTIONS["manuscript/0414_v4/figures/figS1_sobol_convergence.png"] = """
================================================================================
figS1_sobol_convergence — Sobol 指数收敛性分析
================================================================================

【秒懂版】
一句话：Sobol指数在样本量 ≥ 2048 时稳定——说明我们的结论不是"碰巧"得到的。

通俗解释：
Monte Carlo 方法计算 Sobol 指数时，样本量不够会导致结果不稳定。这张图展示
随着基础样本量 N_base 从 256 增加到 8192，各参数的一阶 Sobol 指数 S₁ 是否
稳定。每条线是一个参数，阴影带是50次重复的标准差。N_base ≥ 2048 时
标准差 < 0.04，说明结论稳定可靠。

【详细版】
论文定位：Supplementary Fig. S5（对应 Supplementary Note D.2）
论文作用：为主文Sobol分析的收敛性提供证据

布局（1×2）：
- (A) 应力 S₁ 收敛：E_intercept, α_base, k_ref 三条线
- (B) k_eff S₁ 收敛：α_base, α_slope, ν 三条线

数据来源：results/sensitivity/sobol_convergence.csv
关键数值：N_base=8192时，std < 0.011

生成脚本：code/figures/compose/figS1_sobol_convergence.py
组成子图：D4_sobol_convergence
"""

DESCRIPTIONS["manuscript/0414_v4/figures/figS2_prior_sensitivity.png"] = """
================================================================================
figS2_prior_sensitivity — 先验敏感性分析
================================================================================

【秒懂版】
一句话：只有"太窄"的先验会让后验校准失败——标准先验和宽松先验都没问题。

通俗解释：
MCMC校准时需要选择先验分布。这张热力图测试了6种不同的先验设置
（canonical标准、diffuse更宽、tight更窄、flat均匀、shift偏移正/负）。
绿色=90% CI覆盖率高（好），红色=覆盖率低（差）。
只有 tight（太窄的先验）导致覆盖率降至50%——因为先验太强，数据无法纠正它。
其他5种先验都 ≥83% 覆盖率。结论：我们的标准先验选择是稳健的。

【详细版】
论文定位：Supplementary Fig. S12（对应 Supplementary Note C.4 Prior sensitivity）
论文作用：验证后验校准结果对先验选择不敏感（除非故意选很窄的先验）

布局：6×4 热力图
- 行：6种先验变体（canonical, diffuse, tight, flat, shift+, shift-）
- 列：4个校准参数（E_int, α_base, α_slope, k_ref）
- 色值：90% CI 覆盖率

数据来源：
code/experiments_0404/experiments/posterior/bnn-phy-mono/prior_sensitivity/prior_sensitivity_summary.csv

关键数值：
- Canonical: 100% coverage（全部参数）
- Tight: 50-83% coverage（显著退化）
- Flat/Diffuse: 100% coverage

生成脚本：code/figures/compose/figS2_prior_sensitivity.py
组成子图：H4_prior_sensitivity
"""

DESCRIPTIONS["manuscript/0414_v4/figures/figS3_noise_sensitivity.png"] = """
================================================================================
figS3_noise_sensitivity — 观测噪声敏感性分析
================================================================================

【秒懂版】
一句话：观测噪声从0.5%到10%变化时，后验推断结果基本稳定。

通俗解释：
实际观测数据总有测量噪声。这张图测试不同噪声水平对MCMC结果的影响。
Panel A 展示后验CI宽度（归一化到标准噪声水平）——各参数线基本在1.0附近，
说明后验宽度对噪声不太敏感。Panel B 展示接受率（acceptance rate）随噪声
增加而增加——噪声越大，似然函数越平坦，采样越容易被接受。

【详细版】
论文定位：Supplementary Fig. S13（对应 Supplementary Note C.5 Noise sensitivity）
论文作用：验证后验推断对观测噪声水平的鲁棒性

布局（1×2）：
- (A) 归一化CI宽度 vs 噪声分数（4条线=4个参数）
- (B) 平均接受率 vs 噪声分数

数据来源：
code/experiments_0404/experiments/posterior/bnn-phy-mono/noise_sensitivity/noise_sensitivity_summary.csv

关键数值：
- 标准噪声 = 2%（σ_obs/y_obs = 0.02）
- 噪声从0.5%到10%变化时，CI宽度变化 < 10%
- 接受率从0.58（低噪声）增至0.67（高噪声）

生成脚本：code/figures/compose/figS3_noise_sensitivity.py
组成子图：H5_noise_sensitivity
"""

DESCRIPTIONS["manuscript/0414_v4/figures/figS4_ood.png"] = """
================================================================================
figS4_ood — 分布外（OOD）检测能力
================================================================================

【秒懂版】
一句话：当输入参数偏离训练范围时，BNN的不确定性确实会增大——它知道自己"不确定"。

通俗解释：
一个好的概率模型应该在不熟悉的区域表达更大的不确定性。这张图测试了4个参数
分别超出训练范围尾部时，BNN的epistemic标准差是否增大。所有柱子都 >1
（7-21%增长），说明BNN确实在OOD区域更不确定。虚线=1是分布内基线。

【详细版】
论文定位：Supplementary Fig. S4（对应主文 Discussion 中 OOD 段落）
论文作用：展示BNN相对于频率学派方法的结构优势——自动信号"模型不确信"

布局：水平条形图
- 4个参数（E_intercept, α_base, ν, α_slope）
- X轴：epistemic不确定性比率（OOD / in-distribution）
- 虚线=1.0（分布内基线）

数据来源：results/ood/ood_calibration_comparison.csv

关键数值：
- E_intercept: ratio ≈ 1.18（增大18%）
- α_base: ratio ≈ 1.15
- ν: ratio ≈ 1.10
- α_slope: ratio ≈ 1.16

生成脚本：code/figures/compose/figS4_ood.py
组成子图：F2_ood_epistemic
"""

DESCRIPTIONS["manuscript/0414_v4/figures/figS5_external_calib.png"] = """
================================================================================
figS5_external_calib — 外部基线校准图
================================================================================

【秒懂版】
一句话：MC-Dropout 和 Deep Ensemble 两种外部基线方法的可靠性图——校准质量不如BNN。

通俗解释：
作为对比，这两种非BNN方法（MC-Dropout = 训练时随机关闭神经元，
Deep Ensemble = 训练多个独立模型取平均）的校准情况。每张子图5条线（5个输出），
越偏离对角线说明校准越差。可以看到部分输出的线偏离了对角线。

【详细版】
论文定位：Supplementary Fig. S2（对应 Supplementary Note A）
论文作用：提供外部基线的校准细节，支撑"BNN校准更好"的主文结论

布局（1×2）：
- (A) MC-Dropout 可靠性图（5条线）
- (B) Deep Ensemble 可靠性图（5条线）

数据来源：results/accuracy/external_baseline_calibration.csv
生成脚本：code/figures/compose/figS5_external_calib.py
组成子图：B8_external_baseline_calib
"""

DESCRIPTIONS["manuscript/0414_v4/figures/figS6_bnn_architecture.png"] = """
================================================================================
figS6_bnn_architecture — BNN 网络架构示意图
================================================================================

【秒懂版】
一句话：BNN的结构图——8个输入、3层隐藏层、5个输出，权重是概率分布而非固定值。

通俗解释：
这张图展示BNN的神经网络结构。左侧8个输入参数分为两类颜色：
绿色 = 认知不确定性（核数据相关：E, ν, α），橙色 = 偶然不确定性（制造相关：k, T, α_SS316）。
中间是3层隐藏层，每个权重 w_ij 服从高斯分布 N(μ, σ²)（而非固定数值）。
右侧是5个输出，每个输出不是单一数值而是一个预测分布 ŷ = μ ± σ。
下方绿色虚线框表示物理正则化项 L_phys：对指定 (i,j) 对强制 ∂y/∂x ≥ 0。

【详细版】
论文定位：Supplementary Fig. S16（对应 Supplementary Note E / Methods）
论文作用：帮助读者理解BNN的技术细节——"概率权重"和"物理约束"如何工作

布局：网络结构示意图
- 左列：8个输入节点（颜色编码）
- 中间：3层全连接隐藏层（权重用概率椭圆表示）
- 右列：5个输出节点 + 预测分布示意
- 下方：物理正则化项说明框

数据来源：概念图，无数据
生成脚本：code/figures/compose/figS6_bnn_architecture.py
"""

DESCRIPTIONS["manuscript/0414_v4/figures/figS7_reactor_geometry.png"] = """
================================================================================
figS7_reactor_geometry — 反应堆几何模型
================================================================================

【秒懂版】
一句话：热管冷却反应堆（HPR）的3D剖面图——展示堆芯的物理结构。

通俗解释：
这张图展示我们研究的反应堆长什么样。主要组件包括：
- 热管（Heat pipes）：顶部的圆柱形通道，负责导热
- 单体结构（Monolith, SS316不锈钢）：棕色/金色部分，是主要承力结构
- 燃料（Fuel, UO₂）：粉红色部分，产生核裂变热量
- 反射体（Reflector）：底部粉色区域，反射中子

这是一种新型微型反应堆概念，用于偏远地区供电。我们的仿真就是在这个几何上
进行中子输运+热-力耦合计算。

【详细版】
论文定位：Supplementary Fig. S17 / 主文 Methods 引用
论文作用：帮助非核工程背景的读者理解研究对象

布局：3D CAD渲染剖面图
- 左侧：完整单元体剖面
- 右侧：1/4切割视角

数据来源：CAD模型渲染
生成脚本：code/figures/compose/figS7_reactor_geometry.py
"""

# ────────────────────────────────────────────────────────────
# Bank figures（子图面板）
# ────────────────────────────────────────────────────────────

DESCRIPTIONS["manuscript/0414_v4/figures/bank/B1_stress_parity.png"] = """
================================================================================
B1_stress_parity — 应力奇偶图（子图面板）
================================================================================

【秒懂版】
一句话：BNN预测的应力值 vs 高保真仿真真实值的散点图。

通俗解释：
每个点是一个测试样本，X=真实应力，Y=预测应力。用hexbin密度着色避免
过度绘制。对角线=完美预测。阴影带=90%预测区间。
点越集中在对角线上，说明预测越准。

【详细版】
被组合进：fig2_predictive (Panel A)
数据来源：test set predictions
生成脚本：code/figures/bank/B1_stress_parity.py
"""

DESCRIPTIONS["manuscript/0414_v4/figures/bank/B2_keff_parity.png"] = """
================================================================================
B2_keff_parity — k_eff 奇偶图（子图面板）
================================================================================

【秒懂版】
一句话：BNN预测的 k_eff（有效增殖因子）vs 真实值的散点图。

通俗解释：
k_eff 是核反应堆的关键安全参数：k_eff=1 意味着恰好临界，>1 意味着超临界。
这张图展示BNN对 k_eff 的预测精度。k_eff 的变化范围很小（~1.10-1.11），
所以 R² 较低（~0.63），但绝对误差很小。

【详细版】
被组合进：fig2_predictive (Panel B)
数据来源：test set predictions
注意：k_eff R² 较低是因为方差极小（σ ≈ 0.0007），并非预测质量差
生成脚本：code/figures/bank/B2_keff_parity.py
"""

DESCRIPTIONS["manuscript/0414_v4/figures/bank/B3_thermal_parity.png"] = """
================================================================================
B3_thermal_parity — 燃料温度奇偶图（子图面板）
================================================================================

【秒懂版】
一句话：BNN预测的最大燃料温度 vs 真实值的散点图。

通俗解释：
燃料温度是反应堆安全的另一个关键指标——过高会导致燃料损坏。
BNN在温度预测上表现优秀，RMSE ≈ 4.26 K，优于MC-Dropout和Deep Ensemble。

【详细版】
被组合进：fig2_predictive (Panel C)
数据来源：test set predictions
生成脚本：code/figures/bank/B3_thermal_parity.py
"""

DESCRIPTIONS["manuscript/0414_v4/figures/bank/B4_calibration_reliability.png"] = """
================================================================================
B4_calibration_reliability — 可靠性图（子图面板）
================================================================================

【秒懂版】
一句话：检验BNN的置信区间是否"诚实"——说覆盖90%就真覆盖90%。

通俗解释：
X轴=标称覆盖率（模型声称的），Y轴=经验覆盖率（实际做到的）。
完美校准的模型应该落在对角线上。两个模型（Reference和Physics-regularized）
都紧贴对角线，说明BNN的不确定性估计是可信的。

【详细版】
被组合进：fig1_accuracy (Panel A), figA1_model_validation (Panel A)
数据来源：results/accuracy/calibration_multi_alpha.csv
生成脚本：code/figures/bank/B4_calibration_reliability.py
"""

DESCRIPTIONS["manuscript/0414_v4/figures/bank/B5_external_baseline.png"] = """
================================================================================
B5_external_baseline — 外部基线对比条形图（子图面板）
================================================================================

【秒懂版】
一句话：3种方法（BNN、MC-Dropout、Deep Ensemble）的 R² 和 RMSE 对比。

通俗解释：
横向条形图对比三种方法在5个输出上的预测精度。BNN在温度预测上优势明显
（RMSE更低），但在k_eff上R²不如外部基线。

【详细版】
被组合进：figA1_model_validation (Panels B, C)
数据来源：results/master_comparison_table.csv
生成脚本：code/figures/bank/B5_external_baseline.py
"""

DESCRIPTIONS["manuscript/0414_v4/figures/bank/B6_pit_histogram.png"] = """
================================================================================
B6_pit_histogram — PIT 直方图（子图面板）
================================================================================

【秒懂版】
一句话：概率积分变换（PIT）的分布——越接近均匀分布说明模型越好。

通俗解释：
PIT 是把每个观测值代入预测的CDF得到的值。如果模型完美，PIT值应该是
均匀分布（直方图每个柱子一样高）。偏态/峰态意味着系统性偏差。

【详细版】
被组合进：fig1_accuracy (Panels B, C)
数据来源：results/accuracy/pit_values.npz
生成脚本：code/figures/bank/B6_pit_histogram.py
"""

DESCRIPTIONS["manuscript/0414_v4/figures/bank/B7_scoring_rules.png"] = """
================================================================================
B7_scoring_rules — 评分规则条形图（子图面板）
================================================================================

【秒懂版】
一句话：CRPS 和 ECE 两种评分指标的对比——越低越好。

通俗解释：
CRPS（连续等级概率评分）衡量预测分布与真实值的总体距离。
ECE（期望校准误差）衡量置信区间的诚实程度。BNN在ECE上表现最好。

【详细版】
被组合进：fig1_accuracy (Panels D, E)
数据来源：results/master_comparison_table.csv
生成脚本：code/figures/bank/B7_scoring_rules.py
"""

DESCRIPTIONS["manuscript/0414_v4/figures/bank/B8_external_baseline_calib.png"] = """
================================================================================
B8_external_baseline_calib — 外部基线可靠性图（子图面板）
================================================================================

【秒懂版】
一句话：MC-Dropout 和 Deep Ensemble 各自的可靠性图。

通俗解释：
与B4类似，但展示的是两种外部基线方法的校准质量。每条线代表一个输出量。

【详细版】
被组合进：figS5_external_calib
数据来源：results/accuracy/external_baseline_calibration.csv
生成脚本：code/figures/bank/B8_external_baseline_calib.py
"""

DESCRIPTIONS["manuscript/0414_v4/figures/bank/C1_stress_coupling.png"] = """
================================================================================
C1_stress_coupling — 耦合效应对应力的影响（子图面板）
================================================================================

【秒懂版】
一句话：非耦合 vs 耦合稳态的应力分布对比——耦合后应力降低约48 MPa。

通俗解释：
灰色=非耦合（不考虑热-力相互作用），蓝色=耦合稳态。耦合后应力均值下降，
分布变窄，说明忽略耦合效应会高估应力和应力不确定性。

【详细版】
被组合进：fig3_forward (Panel A)
数据来源：forward UQ results
生成脚本：code/figures/bank/C1_stress_coupling.py
"""

DESCRIPTIONS["manuscript/0414_v4/figures/bank/C2_keff_distribution.png"] = """
================================================================================
C2_keff_distribution — k_eff 分布（子图面板）
================================================================================

【秒懂版】
一句话：耦合稳态下 k_eff 的概率分布——非常窄，σ ≈ 0.0007。

通俗解释：
k_eff 的变化极小，说明反应性对材料参数不确定性非常不敏感。
均值约1.1035，包含rug plot显示个体样本位置。

【详细版】
被组合进：fig3_forward (Panel B)
数据来源：forward UQ results
生成脚本：code/figures/bank/C2_keff_distribution.py
"""

DESCRIPTIONS["manuscript/0414_v4/figures/bank/C3_risk_curve.png"] = """
================================================================================
C3_risk_curve — 应力超限概率曲线（子图面板）
================================================================================

【秒懂版】
一句话：应力超过安全阈值的概率随输入不确定性大小的变化。

通俗解释：
X轴是输入不确定性的"放大倍数"σ_k，Y轴是 P(σ > τ)。
三条线对应三个阈值（110/120/131 MPa）。σ_k=1时即标准先验，
P(σ>131 MPa) ≈ 96%。

【详细版】
被组合进：fig3_forward (Panel D)
数据来源：results/risk/ 目录
生成脚本：code/figures/bank/C3_risk_curve.py
"""

DESCRIPTIONS["manuscript/0414_v4/figures/bank/C4_coupling_delta.png"] = """
================================================================================
C4_coupling_delta — 耦合偏移量（子图面板）
================================================================================

【秒懂版】
一句话：各输出量因耦合效应产生的偏移（coupled - uncoupled）。

通俗解释：
水平条形图展示四个输出量因为考虑热-力耦合而产生的系统性偏移。
应力偏移最大（约-48 MPa），温度偏移约-10到-20度。

【详细版】
被组合进：fig3_forward (Panel C)
数据来源：forward UQ results
生成脚本：code/figures/bank/C4_coupling_delta.py
"""

DESCRIPTIONS["manuscript/0414_v4/figures/bank/D1_stress_sobol.png"] = """
================================================================================
D1_stress_sobol — 应力 Sobol 指数（子图面板）
================================================================================

【秒懂版】
一句话：哪个参数对应力不确定性贡献最大？E_intercept（~55%）。

通俗解释：
单独展示应力输出的 Sobol 一阶/总效应指数，按颜色分物理类别。

【详细版】
被组合进：fig4_sobol 的数据来源之一（实际使用 D3 综合版）
数据来源：results/sensitivity/
生成脚本：code/figures/bank/D1_stress_sobol.py
"""

DESCRIPTIONS["manuscript/0414_v4/figures/bank/D2_keff_sobol.png"] = """
================================================================================
D2_keff_sobol — k_eff Sobol 指数（子图面板）
================================================================================

【秒懂版】
一句话：哪个参数对 k_eff 不确定性贡献最大？α_base（~77%）。

通俗解释：
单独展示 k_eff 输出的 Sobol 一阶/总效应指数。

【详细版】
被组合进：fig4_sobol 的数据来源之一（实际使用 D3 综合版）
数据来源：results/sensitivity/
生成脚本：code/figures/bank/D2_keff_sobol.py
"""

DESCRIPTIONS["manuscript/0414_v4/figures/bank/D3_sobol_total.png"] = """
================================================================================
D3_sobol_total — Sobol 综合图：应力 + k_eff（子图面板）
================================================================================

【秒懂版】
一句话：应力和k_eff的Sobol指数并排展示，色彩按物理类别编码。

通俗解释：
左侧=应力（E_intercept主导），右侧=k_eff（α_base主导）。
每个参数同时显示 S₁（直接影响）和 S_T（含交互影响），配有误差棒（90% CI）。

【详细版】
被组合进：fig4_sobol, figA4_sobol_detail
数据来源：results/sensitivity/
生成脚本：code/figures/bank/D3_sobol_total.py
"""

DESCRIPTIONS["manuscript/0414_v4/figures/bank/D4_sobol_convergence.png"] = """
================================================================================
D4_sobol_convergence — Sobol 收敛性（子图面板）
================================================================================

【秒懂版】
一句话：Sobol指数随 N_base 增大而趋于稳定的过程。

通俗解释：
每条线跟踪一个参数的 S₁ 在不同样本量下的值，阴影带是标准差。
N_base ≥ 2048 时阴影带变窄 → 收敛。

【详细版】
被组合进：figS1_sobol_convergence
数据来源：results/sensitivity/sobol_convergence.csv
生成脚本：code/figures/bank/D4_sobol_convergence.py
"""

DESCRIPTIONS["manuscript/0414_v4/figures/bank/E1_prior_posterior.png"] = """
================================================================================
E1_prior_posterior — 先验→后验边际分布（子图面板）
================================================================================

【秒懂版】
一句话：4个参数的先验分布（浅色宽）和后验分布（深色窄）对比——后验收缩=数据有信息量。

通俗解释：
每个子图一个参数。浅粉色=先验（观测前的信念），深红线=后验（观测后的信念）。
后验比先验窄说明观测数据成功约束了参数。蓝色框标记真值位置。

【详细版】
被组合进：fig6_posterior (Panel B)
数据来源：MCMC chain files
生成脚本：code/figures/bank/E1_prior_posterior.py
"""

DESCRIPTIONS["manuscript/0414_v4/figures/bank/E2_posterior_coverage.png"] = """
================================================================================
E2_posterior_coverage — 后验覆盖率（子图面板）
================================================================================

【秒懂版】
一句话：18个benchmark案例中，后验90% CI覆盖了多少参数真值？（0.917）

通俗解释：
如果90%CI工作正常，18个案例×4个参数=72个真值中应该有约65个被覆盖。
实际覆盖率0.917（约66个），非常接近标称值。

【详细版】
被组合进：fig6_posterior 的整体评估
数据来源：posterior benchmark_summary.csv
生成脚本：code/figures/bank/E2_posterior_coverage.py
"""

DESCRIPTIONS["manuscript/0414_v4/figures/bank/E3_posterior_predictive.png"] = """
================================================================================
E3_posterior_predictive — 后验预测检验（子图面板）
================================================================================

【秒懂版】
一句话：用后验参数预测的输出 vs 实际观测值——检验后验是否合理。

通俗解释：
后验推断出参数后，代入BNN预测输出，看是否与原始观测一致。
如果一致，说明后验校准成功。

【详细版】
被组合进：fig6_posterior 的补充检验
数据来源：posterior chains + forward pass
生成脚本：code/figures/bank/E3_posterior_predictive.py
"""

DESCRIPTIONS["manuscript/0414_v4/figures/bank/F1_data_efficiency.png"] = """
================================================================================
F1_data_efficiency — 数据效率学习曲线（子图面板）
================================================================================

【秒懂版】
一句话：训练数据越多，RMSE越低——物理正则化在小数据集时更稳定。

通俗解释：
X=训练集大小（500-2000），Y=应力RMSE。两条线分别是Reference和
Physics-regularized BNN。阴影带是2个种子的方差。

【详细版】
被组合进：fig7_efficiency (Panel B), figA3_efficiency (Panel A)
数据来源：results/data_efficiency/data_efficiency_summary.csv
生成脚本：code/figures/bank/F1_data_efficiency.py
"""

DESCRIPTIONS["manuscript/0414_v4/figures/bank/F2_ood_epistemic.png"] = """
================================================================================
F2_ood_epistemic — OOD 认知不确定性比率（子图面板）
================================================================================

【秒懂版】
一句话：参数超出训练范围时，BNN的epistemic不确定性增大7-21%。

通俗解释：
柱子 >1 说明BNN在分布外区域更加"不确定"，这是正确的行为。
虚线=1是分布内基线。

【详细版】
被组合进：figS4_ood, figA3_efficiency (Panel B)
数据来源：results/ood/ood_calibration_comparison.csv
生成脚本：code/figures/bank/F2_ood_epistemic.py
"""

DESCRIPTIONS["manuscript/0414_v4/figures/bank/F3_monotonicity.png"] = """
================================================================================
F3_monotonicity — 单调性违反率热力图（子图面板）
================================================================================

【秒懂版】
一句话：BNN是否遵守物理单调性？几乎全部遵守（绿色=0%违反率）。

通俗解释：
行=输入参数，列=输出量，颜色=违反率。绿色(0%)=物理规律被完美遵守。
唯一例外是 α_SS316→fuel_temp（~37%），但该对没有强物理单调约束。

【详细版】
被组合进：fig5_physics (Panel A), figA2_physics_robustness (Panel A)
数据来源：results/physics_consistency/monotonicity_violation_rate.csv
生成脚本：code/figures/bank/F3_monotonicity.py
"""

DESCRIPTIONS["manuscript/0414_v4/figures/bank/F4_uncertainty_decomp.png"] = """
================================================================================
F4_uncertainty_decomp — 不确定性分解（子图面板）
================================================================================

【秒懂版】
一句话：每个输出的不确定性中有多少来自"模型不够确定"vs"数据本身有噪声"。

通俗解释：
蓝色=epistemic（认知不确定性，可通过更多数据减少），灰色=aleatoric（偶然不确定性，固有噪声）。
Wall temp 的 epistemic 占42%（最高），k_eff 占21%。

【详细版】
被组合进：fig5_physics (Panel B), figA2 (Panel B)
数据来源：results/uncertainty_decomposition/uncertainty_decomposition.csv
生成脚本：code/figures/bank/F4_uncertainty_decomp.py
"""

DESCRIPTIONS["manuscript/0414_v4/figures/bank/G1_speedup.png"] = """
================================================================================
G1_speedup — 计算加速比（子图面板）
================================================================================

【秒懂版】
一句话：BNN vs 高保真仿真的计算时间对比——加速约1.7亿倍。

通俗解释：
蓝色柱子（BNN）几乎看不到，因为太快了（秒级）。灰色柱子（HF）高达10⁸秒。
不同X位置代表不同精度要求（CI半宽），精度要求越高差距越大。

【详细版】
被组合进：fig7_efficiency (Panel A), figA3_efficiency (Panel C)
数据来源：results/speed/budget_matched_risk.csv
生成脚本：code/figures/bank/G1_speedup.py
"""

DESCRIPTIONS["manuscript/0414_v4/figures/bank/H1_mcmc_trace.png"] = """
================================================================================
H1_mcmc_trace — MCMC 轨迹图（子图面板）
================================================================================

【秒懂版】
一句话：4条MCMC链在1200次迭代中的采样轨迹——良好混合说明收敛。

通俗解释：
每行一个参数，4条彩色线代表4条独立链。如果链充分混合（看起来像"毛线团"），
说明采样器已经收敛到后验分布。如果某条链卡在一个区域不动，就有问题。

【详细版】
被组合进：fig6_posterior (Panel A)
数据来源：posterior/bnn-phy-mono/diagnostics/chains/case_*.npz
生成脚本：code/figures/bank/H1_mcmc_trace.py
"""

DESCRIPTIONS["manuscript/0414_v4/figures/bank/H2_mcmc_rank.png"] = """
================================================================================
H2_mcmc_rank — MCMC 秩直方图（子图面板）
================================================================================

【秒懂版】
一句话：秩直方图——另一种检查MCMC收敛性的方法，理想情况下应该是均匀的。

通俗解释：
把所有链的样本合并排序，然后看每条链的秩在整体中的分布。
均匀=链充分混合，偏斜=链不够独立。

【详细版】
被组合进：fig6_posterior 的诊断补充
数据来源：posterior chains
生成脚本：code/figures/bank/H2_mcmc_rank.py
"""

DESCRIPTIONS["manuscript/0414_v4/figures/bank/H3_mcmc_diagnostics.png"] = """
================================================================================
H3_mcmc_diagnostics — MCMC 诊断汇总（子图面板）
================================================================================

【秒懂版】
一句话：18个案例的 R̂ 和 ESS 散点图——全部通过收敛标准。

通俗解释：
左图 R̂（越接近1越好），红色虚线=1.01阈值，所有点都在阈值以下=收敛。
右图 ESS（有效样本量，越高越好），红色虚线=150阈值，所有点都在阈值以上=采样充分。

【详细版】
被组合进：fig6_posterior (Panels C, D)
数据来源：posterior/bnn-phy-mono/diagnostics/mcmc_diagnostics.csv
生成脚本：code/figures/bank/H3_mcmc_diagnostics.py
"""

DESCRIPTIONS["manuscript/0414_v4/figures/bank/H4_prior_sensitivity.png"] = """
================================================================================
H4_prior_sensitivity — 先验敏感性热力图（子图面板）
================================================================================

【秒懂版】
一句话：测试6种不同先验设置对后验覆盖率的影响——只有太窄的先验会失效。

通俗解释：
6行×4列热力图，色值=90% CI覆盖率。只有"Tight"行出现红/黄色（覆盖率低）。

【详细版】
被组合进：figS2_prior_sensitivity
数据来源：prior_sensitivity_summary.csv
生成脚本：code/figures/bank/H4_prior_sensitivity.py
"""

DESCRIPTIONS["manuscript/0414_v4/figures/bank/H5_noise_sensitivity.png"] = """
================================================================================
H5_noise_sensitivity — 噪声敏感性（子图面板）
================================================================================

【秒懂版】
一句话：不同观测噪声水平下，后验CI宽度和接受率的变化——基本稳定。

通俗解释：
Panel A: CI宽度归一化后各参数线近似水平 → 噪声不敏感。
Panel B: 接受率随噪声增大略增 → 似然更平坦时更容易接受。

【详细版】
被组合进：figS3_noise_sensitivity
数据来源：noise_sensitivity_summary.csv
生成脚本：code/figures/bank/H5_noise_sensitivity.py
"""

# ────────────────────────────────────────────────────────────
# Results 目录图（中间产物/诊断图）
# ────────────────────────────────────────────────────────────

# --- accuracy ---
for model in ["bnn-baseline", "bnn-data-mono", "bnn-data-mono-ineq", "bnn-phy-mono",
              "mc-dropout", "deep-ensemble"]:
    nice = model.replace("-", " ").title()
    DESCRIPTIONS[f"results/accuracy/pit_{model}.png"] = f"""
================================================================================
pit_{model} — PIT 直方图：{nice}
================================================================================

【秒懂版】
一句话：{nice} 模型的概率积分变换直方图——越接近均匀分布说明校准越好。

通俗解释：
PIT（Probability Integral Transform）把每个真实值代入模型预测的CDF，
得到一个0到1之间的值。如果模型完美，这些值应该均匀分布。
每个子图对应一个输出量。偏斜=模型有系统性偏差。

【详细版】
分类：中间诊断图（intermediate diagnostic）
对应模型：{model}
数据来源：results/accuracy/pit_values.npz
对应论文图：被汇总进 fig1_accuracy 或 figS5_external_calib
"""

    DESCRIPTIONS[f"results/accuracy/reliability_{model}.png"] = f"""
================================================================================
reliability_{model} — 可靠性图：{nice}
================================================================================

【秒懂版】
一句话：{nice} 模型的校准曲线——越贴近对角线说明预测区间越诚实。

通俗解释：
X=标称覆盖率，Y=经验覆盖率。5条线=5个输出量。
对角线=完美校准。线在对角线上方=保守（区间偏宽），下方=过度自信。

【详细版】
分类：中间诊断图
对应模型：{model}
数据来源：results/accuracy/calibration_multi_alpha.csv
对应论文图：被汇总进 fig1_accuracy 或 figS5_external_calib
"""

# --- data_efficiency ---
DESCRIPTIONS["results/data_efficiency/data_efficiency_curve.png"] = """
================================================================================
data_efficiency_curve — 数据效率学习曲线（results版）
================================================================================

【秒懂版】
一句话：训练数据量 vs 测试RMSE的学习曲线。

通俗解释：
这是 results 目录下的原始版本。与 bank/F1_data_efficiency 内容相同，
但可能是更早期的绘图风格。正式论文使用 bank/F1 的重绘版本。

【详细版】
分类：原始结果图（直接由实验脚本生成）
数据来源：results/data_efficiency/data_efficiency_summary.csv
对应论文图：fig7_efficiency (Panel B)
"""

# --- hf_sensitivity ---
DESCRIPTIONS["results/hf_sensitivity/hf_sensitivity_bar.png"] = """
================================================================================
hf_sensitivity_bar — 高保真敏感性条形图
================================================================================

【秒懂版】
一句话：直接用高保真仿真计算的敏感性指标——用于与BNN-Sobol结果交叉验证。

通俗解释：
用有限差分法在高保真仿真上直接扰动参数，计算各参数对输出的偏导数/敏感性。
这是"金标准"参考，用于验证BNN代理的Sobol分析是否可信。

【详细版】
分类：验证图
数据来源：results/hf_sensitivity/ 目录
对应论文：Supplementary Note D 中的 HF 交叉验证讨论
"""

DESCRIPTIONS["results/hf_sensitivity/hf_vs_bnn_sensitivity_comparison.png"] = """
================================================================================
hf_vs_bnn_sensitivity_comparison — HF vs BNN 敏感性对比
================================================================================

【秒懂版】
一句话：高保真仿真的敏感性排序与BNN Sobol分析是否一致？答：是的。

通俗解释：
并排对比高保真有限差分敏感性和BNN Sobol指数的参数排序。
如果排序一致，说明BNN正确学到了参数-输出关系。

【详细版】
分类：验证图
数据来源：HF扰动结果 + Sobol结果
对应论文：Supplementary Note D 的交叉验证
"""

# --- ood ---
DESCRIPTIONS["results/ood/ood_coverage_comparison.png"] = """
================================================================================
ood_coverage_comparison — OOD 覆盖率对比
================================================================================

【秒懂版】
一句话：分布内 vs 分布外区域的90% PICP对比——BNN在OOD区域仍保持>96%覆盖。

通俗解释：
分组条形图对比模型在分布内和分布外子集上的预测区间覆盖率。
覆盖率不应在OOD区域崩溃。BNN保持了良好的覆盖。

【详细版】
分类：原始结果图
数据来源：results/ood/ood_calibration_comparison.csv
对应论文图：Supplementary Fig. S4 的补充数据
"""

DESCRIPTIONS["results/ood/ood_epistemic_ratio.png"] = """
================================================================================
ood_epistemic_ratio — OOD 认知不确定性比率（results版）
================================================================================

【秒懂版】
一句话：OOD区域的epistemic不确定性与分布内的比率——>1说明BNN正确增大了不确定性。

通俗解释：
与 bank/F2_ood_epistemic 内容相同，这是原始实验脚本生成的版本。

【详细版】
分类：原始结果图
数据来源：results/ood/ood_calibration_comparison.csv
对应论文图：figS4_ood
"""

# --- physics_consistency ---
DESCRIPTIONS["results/physics_consistency/monotonicity_violation_primary.png"] = """
================================================================================
monotonicity_violation_primary — 主要输出的单调性违反率
================================================================================

【秒懂版】
一句话：BNN对物理单调性关系的遵守情况热力图——几乎全部遵守。

通俗解释：
原始实验脚本生成的单调性检查结果。与 bank/F3_monotonicity 内容类似。

【详细版】
分类：原始结果图
数据来源：results/physics_consistency/monotonicity_violation_rate.csv
对应论文图：fig5_physics (Panel A)
"""

DESCRIPTIONS["results/physics_consistency/inequality_violation.png"] = """
================================================================================
inequality_violation — 不等式约束违反率
================================================================================

【秒懂版】
一句话：BNN对物理不等式约束的遵守情况——如 iter2 应力 ≤ iter1 应力。

通俗解释：
除了单调性，还有一些不等式约束（如耦合后应力应低于非耦合应力）。
这张图检查这些约束的违反率。

【详细版】
分类：原始结果图
数据来源：results/physics_consistency/inequality_violation_rate.csv
对应论文：Supplementary Note B 中的约束讨论
"""

# --- posterior ---
for model in ["bnn-baseline", "bnn-phy-mono"]:
    nice = model.replace("-", " ").title()
    for case in ["00", "06", "12"]:
        cat = {"00": "low-stress", "06": "near-threshold", "12": "high-stress"}[case]

        DESCRIPTIONS[f"results/posterior/trace_{model}_case{case}.png"] = f"""
================================================================================
trace_{model}_case{case} — MCMC轨迹图：{nice}, Case {case} ({cat})
================================================================================

【秒懂版】
一句话：{nice}模型在第{case}号benchmark案例（{cat}类别）上的MCMC采样轨迹。

通俗解释：
4条彩色线=4条独立MCMC链，每行一个参数。充分混合（"毛线团"状）=收敛。
Case {case} 属于{cat}类别：{"应力远低于阈值" if cat=="low-stress" else "应力接近131 MPa阈值" if cat=="near-threshold" else "应力远高于阈值"}。

【详细版】
分类：诊断图
数据来源：posterior/{model}/diagnostics/chains/case_{case}.npz
对应论文图：fig6_posterior (Panel A)（使用 case_06 作为代表）
"""

        DESCRIPTIONS[f"results/posterior/rank_{model}_case{case}.png"] = f"""
================================================================================
rank_{model}_case{case} — 秩直方图：{nice}, Case {case} ({cat})
================================================================================

【秒懂版】
一句话：{nice}模型在第{case}号案例上的MCMC秩直方图——另一种收敛性检查。

通俗解释：
将所有链样本混合排序后，检查每条链的秩分布。均匀分布=链间一致=收敛良好。

【详细版】
分类：诊断图
数据来源：posterior/{model}/diagnostics/chains/case_{case}.npz
对应论文：Supplementary Fig. S9 caption 中提及 rank histograms
"""

# --- sensitivity ---
for model in ["bnn-baseline", "bnn-phy-mono"]:
    nice = model.replace("-", " ").title()
    for output in ["stress", "keff"]:
        out_nice = "耦合最大应力" if output == "stress" else "耦合 k_eff"

        DESCRIPTIONS[f"results/sensitivity/sobol_convergence_{model}_{output}.png"] = f"""
================================================================================
sobol_convergence_{model}_{output} — Sobol收敛图：{nice}, {out_nice}
================================================================================

【秒懂版】
一句话：{nice}模型下{out_nice}的Sobol指数随样本量的收敛过程。

通俗解释：
X=基础样本量 N_base（256→8192），Y=一阶Sobol指数 S₁。
每条线跟踪一个参数，阴影带=标准差（50次重复）。
N_base ≥ 2048 时趋于稳定。

【详细版】
分类：原始结果图
数据来源：results/sensitivity/sobol_convergence.csv
对应论文图：figS1_sobol_convergence
"""

# --- speed ---
DESCRIPTIONS["results/speed/budget_matched_risk.png"] = """
================================================================================
budget_matched_risk — 预算匹配风险计算对比（results版）
================================================================================

【秒懂版】
一句话：在同样的风险估计精度目标下，HF仿真 vs BNN需要多少计算时间。

通俗解释：
原始实验脚本生成的版本。与 bank/G1_speedup 内容类似但可能风格不同。

【详细版】
分类：原始结果图
数据来源：results/speed/budget_matched_risk.csv
对应论文图：fig7_efficiency (Panel A)
"""

# --- uncertainty_decomposition ---
DESCRIPTIONS["results/uncertainty_decomposition/epi_vs_ale_scatter_bnn-baseline.png"] = """
================================================================================
epi_vs_ale_scatter_bnn-baseline — Epistemic vs Aleatoric 散点图：Baseline
================================================================================

【秒懂版】
一句话：每个测试样本的认知不确定性 vs 偶然不确定性的散点图。

通俗解释：
每个点=一个测试样本。X=偶然（aleatoric）标准差，Y=认知（epistemic）标准差。
对角线=两者相等。点在对角线上方=认知不确定性主导。

【详细版】
分类：诊断/补充图
数据来源：uncertainty_decomposition/uncertainty_decomposition.csv + per-sample data
对应论文：Supplementary Note B 中的不确定性分解讨论
"""

DESCRIPTIONS["results/uncertainty_decomposition/epi_vs_ale_scatter_bnn-phy-mono.png"] = """
================================================================================
epi_vs_ale_scatter_bnn-phy-mono — Epistemic vs Aleatoric 散点图：Physics-regularized
================================================================================

【秒懂版】
一句话：物理正则化BNN的每个测试样本的认知 vs 偶然不确定性散点图。

通俗解释：
与baseline版类似，但展示物理正则化后的不确定性分解变化。
物理约束可能使epistemic部分更加集中。

【详细版】
分类：诊断/补充图
对应论文：Supplementary Note B
"""

DESCRIPTIONS["results/uncertainty_decomposition/uncertainty_decomposition_bar.png"] = """
================================================================================
uncertainty_decomposition_bar — 不确定性分解条形图（results版）
================================================================================

【秒懂版】
一句话：各输出量的 epistemic vs aleatoric 不确定性占比条形图。

通俗解释：
原始实验脚本生成的版本。与 bank/F4_uncertainty_decomp 类似。

【详细版】
分类：原始结果图
数据来源：results/uncertainty_decomposition/uncertainty_decomposition.csv
对应论文图：fig5_physics (Panel B)
"""

DESCRIPTIONS["results/uncertainty_decomposition/uncertainty_decomposition_comparison.png"] = """
================================================================================
uncertainty_decomposition_comparison — 不确定性分解模型对比
================================================================================

【秒懂版】
一句话：多个BNN变体之间的不确定性分解对比。

通俗解释：
对比4个BNN变体（baseline, data-mono, data-mono-ineq, phy-mono）在
各输出上的 epistemic/aleatoric 比例差异。展示物理约束如何影响
不确定性的内部分配。

【详细版】
分类：原始结果图
数据来源：results/uncertainty_decomposition/uncertainty_decomposition.csv
对应论文：Supplementary Note B 的消融分析
"""


# ═══════════════════════════════════════════════════════════════
# 生成所有说明文件
# ═══════════════════════════════════════════════════════════════

def main():
    written = 0
    skipped = 0
    for rel_path, content in DESCRIPTIONS.items():
        png_path = BNN0414 / rel_path
        if not png_path.exists():
            print(f"  SKIP (png not found): {png_path}")
            skipped += 1
            continue
        txt_path = png_path.with_suffix(".txt")
        txt_path.write_text(content.strip() + "\n", encoding="utf-8")
        written += 1
    print(f"\nDone: {written} description files written, {skipped} skipped.")


if __name__ == "__main__":
    main()
