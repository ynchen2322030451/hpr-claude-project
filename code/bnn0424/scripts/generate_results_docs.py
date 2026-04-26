#!/usr/bin/env python3
"""为 bnn0414/results/ 中所有数据文件生成同名 .txt 说明文档。"""

import os
from pathlib import Path

BNN0414 = Path(__file__).resolve().parents[1]
RESULTS = BNN0414 / "results"

DESCRIPTIONS = {}

# ═══════════════════════════════════════════════════════════════
# 顶层结果文件
# ═══════════════════════════════════════════════════════════════

DESCRIPTIONS["master_comparison_table.csv"] = """
================================================================================
master_comparison_table.csv — 六模型总对比表（论文 Table 1 数据源）
================================================================================

【秒懂版】
一句话：6种模型 × 5个输出 × 多个指标的总汇表——论文中最重要的定量对比数据源。

通俗解释：
这张表回答"哪个模型最好？"。6种模型包括4种BNN变体（baseline, data-mono,
data-mono-ineq, phy-mono）和2种外部基线（MC-Dropout, Deep Ensemble）。
每个模型在5个输出（应力、k_eff、燃料温度、单体温度、wall expansion）上的
RMSE、R²、CRPS、ECE、PICP等指标全在这张表里。BNN行有5-seed平均值和标准差。

【详细版】
论文定位：主文 Table 1 的直接数据源
列结构：model_id, output, RMSE, R2, MAE, CRPS, NLL, ECE, PICP_90, MPIW_90, ...
关键结论：
- phy-mono 应力 ECE = 0.106（最低）
- BNN 燃料温度 RMSE ≈ 4.26 vs MC-Dropout 4.50
- k_eff R² 外部基线略高（~0.86 vs ~0.63），但 CRPS 差距不大
生成脚本：code/experiments_0404/evaluation/run_eval_0404.py
"""

DESCRIPTIONS["mf_correlation_check.csv"] = """
================================================================================
mf_correlation_check.csv — 多保真度相关性检查
================================================================================

【秒懂版】
一句话：检查低保真度（非耦合）和高保真度（耦合）输出之间的相关性。

通俗解释：
多保真度建模的前提是低保真度和高保真度输出之间有足够的相关性。
这个文件检查各输出量的 iter1（非耦合）和 iter2（耦合）之间的 Pearson/Spearman 相关系数。
相关性高的输出适合做残差建模（高-低保真度差值预测）。

【详细版】
用途：评估是否适合使用多保真度混合策略
列结构：output, pearson_r, spearman_rho, p_value, ...
结论：应力和wall2残差适合，温度残差相关性不够强
"""

DESCRIPTIONS["mf_gate_analysis.csv"] = """
================================================================================
mf_gate_analysis.csv — 多保真度门控分析
================================================================================

【秒懂版】
一句话：决定哪些输出适合用"残差建模"vs"直接建模"的分析结果。

通俗解释：
不是所有输出都适合多保真度残差策略。这个文件的分析结果决定了
只有 stress 和 wall2 被标记为"residual-eligible"（可以用残差建模），
其他输出仍然直接建模。

【详细版】
用途：模型架构决策的数据支撑
列结构：output, correlation, residual_std_ratio, eligible, ...
结论：gate = 只有 stress + wall2 适合残差建模
"""

# ═══════════════════════════════════════════════════════════════
# accuracy/ 子目录
# ═══════════════════════════════════════════════════════════════

DESCRIPTIONS["accuracy/calibration_manifest.json"] = """
================================================================================
calibration_manifest.json — 校准实验 manifest
================================================================================

【秒懂版】
一句话：校准实验的元数据——记录了实验配置、git版本、生成时间。

通俗解释：
Manifest 文件是"实验身份证"，记录了这次实验在什么代码版本、什么配置下运行的，
确保结果可追溯。不包含实际数据，只包含元信息。

【详细版】
用途：可追溯性/复现性
内容：git_sha, config_sha256, dataset_sha256, 生成时间戳
"""

DESCRIPTIONS["accuracy/calibration_multi_alpha.csv"] = """
================================================================================
calibration_multi_alpha.csv — 多覆盖率校准数据（Fig. 1A 数据源）
================================================================================

【秒懂版】
一句话：在不同标称覆盖率（50%-99%）下，各模型的实际经验覆盖率——画可靠性图的数据。

通俗解释：
如果模型说"90%的预测落在这个区间内"，实际上有多少落在里面？
这个文件记录了每个模型、每个输出、每个标称覆盖率的经验覆盖率。
理想情况下 empirical_coverage ≈ nominal_alpha。

【详细版】
论文定位：Fig. 1A (Reliability diagram) 的数据源
列结构：model_id, output, nominal_alpha, empirical_coverage
生成脚本：run_eval_0404.py
"""

DESCRIPTIONS["accuracy/external_baseline_calibration.csv"] = """
================================================================================
external_baseline_calibration.csv — 外部基线校准数据（Fig. S5 数据源）
================================================================================

【秒懂版】
一句话：MC-Dropout 和 Deep Ensemble 的校准数据——与BNN对比用。

通俗解释：
与 calibration_multi_alpha.csv 格式相同，但只包含两种外部基线方法的数据。
用于画 figS5_external_calib。

【详细版】
论文定位：Supplementary Fig. S5 数据源
列结构：同 calibration_multi_alpha.csv
"""

DESCRIPTIONS["accuracy/external_baseline_risk.csv"] = """
================================================================================
external_baseline_risk.csv — 外部基线风险估计
================================================================================

【秒懂版】
一句话：MC-Dropout 和 Deep Ensemble 的应力超限概率估计。

通俗解释：
用外部基线方法做正向传播后计算的 P(σ>τ) 值，与BNN结果对比。

【详细版】
用途：横向对比风险估计的一致性
"""

DESCRIPTIONS["accuracy/external_baseline_scoring.csv"] = """
================================================================================
external_baseline_scoring.csv — 外部基线评分规则
================================================================================

【秒懂版】
一句话：MC-Dropout 和 Deep Ensemble 的 CRPS、NLL 等评分指标。

通俗解释：
概率预测的评分规则（scoring rules）对比。CRPS越低越好。

【详细版】
用途：与BNN评分指标横向对比
列结构：model_id, output, CRPS, NLL, ...
"""

DESCRIPTIONS["accuracy/pit_values.npz"] = """
================================================================================
pit_values.npz — PIT 原始值（Fig. 1B/C 数据源）
================================================================================

【秒懂版】
一句话：所有模型的概率积分变换（PIT）值——画PIT直方图的原始数据。

通俗解释：
npz 文件，每个 key 是 model_id，值是 (N_test, N_outputs) 的数组。
PIT值应该均匀分布在[0,1]之间，否则说明模型校准有偏。
用 np.load(path) 加载。

【详细版】
论文定位：Fig. 1B/C 数据源
格式：np.load(path), keys = model_id, values = ndarray (435, 15)
"""

DESCRIPTIONS["accuracy/repeat_eval_global_summary.csv"] = """
================================================================================
repeat_eval_global_summary.csv — 重复评估全局汇总
================================================================================

【秒懂版】
一句话：5个随机种子重复训练的BNN的全局汇总指标（均值±标准差）。

通俗解释：
为了证明BNN结果不是"碰巧"得到的，用5个不同种子训练了5个模型。
这个文件汇总了5次评估的全局平均指标。

【详细版】
用途：Table 1 中 BNN 行的 mean±std 数据源
列结构：model_id, metric, mean, std, min, max
"""

DESCRIPTIONS["accuracy/repeat_eval_paper_table.csv"] = """
================================================================================
repeat_eval_paper_table.csv — 论文表格格式的评估结果
================================================================================

【秒懂版】
一句话：直接可以粘贴进论文 Table 1 的格式化评估结果。

通俗解释：
预格式化版本，按论文Table 1的行列结构排列。包含 mean±std 格式的字符串。

【详细版】
论文定位：Table 1 的最终格式化数据源
"""

DESCRIPTIONS["accuracy/repeat_eval_per_output_summary.csv"] = """
================================================================================
repeat_eval_per_output_summary.csv — 按输出分的重复评估结果
================================================================================

【秒懂版】
一句话：5-seed 重复评估在每个输出上的指标明细。

通俗解释：
比 global_summary 更详细——每个输出量（应力、k_eff、温度等）单独列出。

【详细版】
列结构：model_id, output, metric, mean, std, ...
"""

DESCRIPTIONS["accuracy/scoring_rules.csv"] = """
================================================================================
scoring_rules.csv — 评分规则（单次评估）
================================================================================

【秒懂版】
一句话：单次固定种子训练的所有模型的 CRPS、NLL 等评分。

通俗解释：
与 repeat_eval 不同，这是固定种子单次评估的结果。
用于快速对比和调试。

【详细版】
列结构：model_id, output, CRPS, NLL, calibration_error, ...
"""

DESCRIPTIONS["accuracy/scoring_rules_multi_seed_ci.csv"] = """
================================================================================
scoring_rules_multi_seed_ci.csv — 评分规则（多种子+置信区间）
================================================================================

【秒懂版】
一句话：5个种子评分的均值和95%置信区间。

通俗解释：
每个模型×输出×指标的 mean, lower_ci, upper_ci。用于论文中报告
"CRPS = 0.xx ± 0.yy"这样的写法。

【详细版】
列结构：model_id, output, metric, mean, ci_lower, ci_upper
"""

# ═══════════════════════════════════════════════════════════════
# data_efficiency/ 子目录
# ═══════════════════════════════════════════════════════════════

DESCRIPTIONS["data_efficiency/data_efficiency_manifest.json"] = """
================================================================================
data_efficiency_manifest.json — 数据效率实验 manifest
================================================================================

【秒懂版】
一句话：数据效率实验的元数据。

【详细版】
记录实验配置和运行环境。
"""

DESCRIPTIONS["data_efficiency/data_efficiency_all.csv"] = """
================================================================================
data_efficiency_all.csv — 数据效率完整结果
================================================================================

【秒懂版】
一句话：所有训练集大小 × 所有种子 × 所有输出的详细指标。

通俗解释：
训练集大小从500到2000递增，每个大小用2个种子训练，记录每个输出的RMSE等指标。
是 data_efficiency_summary.csv 的详细版。

【详细版】
列结构：model_id, train_size, seed, output, RMSE, R2, ...
"""

DESCRIPTIONS["data_efficiency/data_efficiency_bnn-baseline.csv"] = """
================================================================================
data_efficiency_bnn-baseline.csv — Baseline BNN 的数据效率结果
================================================================================

【秒懂版】
一句话：Reference BNN 在不同训练集大小下的精度变化。

【详细版】
模型：bnn-baseline
列结构：train_size, seed, output, RMSE, ...
"""

DESCRIPTIONS["data_efficiency/data_efficiency_bnn-phy-mono.csv"] = """
================================================================================
data_efficiency_bnn-phy-mono.csv — Physics-regularized BNN 的数据效率结果
================================================================================

【秒懂版】
一句话：物理正则化BNN在不同训练集大小下的精度变化。

【详细版】
模型：bnn-phy-mono
列结构：train_size, seed, output, RMSE, ...
"""

DESCRIPTIONS["data_efficiency/data_efficiency_summary.csv"] = """
================================================================================
data_efficiency_summary.csv — 数据效率汇总表（Fig. 7B 数据源）
================================================================================

【秒懂版】
一句话：两个模型在各训练集大小下的应力RMSE均值和标准差——画学习曲线的数据。

通俗解释：
汇总了2个种子的均值和标准差。是 fig7_efficiency Panel B 和
figA3_efficiency Panel A 的直接数据源。

【详细版】
论文定位：Fig. 7B 数据源
列结构：model_id, train_size, rmse_mean, rmse_std
关键数值：phy-mono 在500样本时 RMSE≈4.95, 2000样本时≈4.60
"""

# ═══════════════════════════════════════════════════════════════
# hf_sensitivity/ 子目录
# ═══════════════════════════════════════════════════════════════

DESCRIPTIONS["hf_sensitivity/prcc_results.csv"] = """
================================================================================
prcc_results.csv — 偏秩相关系数（PRCC）结果
================================================================================

【秒懂版】
一句话：直接在高保真数据上计算的偏秩相关系数——与BNN Sobol结果交叉验证用。

通俗解释：
PRCC 是一种非参数敏感性度量。在训练数据上直接计算，不需要代理模型。
如果 PRCC 和 Sobol 的参数排序一致，说明BNN正确学到了输入-输出关系。

【详细版】
列结构：input, output, prcc, p_value
对应论文：Supplementary Note D 的 HF 交叉验证
"""

DESCRIPTIONS["hf_sensitivity/src_results.csv"] = """
================================================================================
src_results.csv — 标准化回归系数（SRC）结果
================================================================================

【秒懂版】
一句话：标准化回归系数——另一种基于高保真数据的敏感性度量。

通俗解释：
SRC 通过线性回归估计每个参数的标准化贡献。与 PRCC 互为补充。

【详细版】
列结构：input, output, src, p_value
"""

# ═══════════════════════════════════════════════════════════════
# ood/ 子目录
# ═══════════════════════════════════════════════════════════════

DESCRIPTIONS["ood/ood_calibration_comparison.csv"] = """
================================================================================
ood_calibration_comparison.csv — OOD校准对比（Fig. S4 数据源）
================================================================================

【秒懂版】
一句话：分布内 vs 分布外区域的不确定性指标对比——检验BNN是否"知道自己不知道"。

通俗解释：
对每个输入参数，取其训练数据的尾部（<10% 或 >90%分位数）作为OOD子集。
对比OOD子集和分布内子集的 epistemic std ratio、PICP coverage 等指标。
ratio > 1 说明BNN在OOD区域更不确定——这是正确的行为。

【详细版】
论文定位：Fig. S4, Fig. A3(B) 数据源
列结构：model_id, param, epi_ratio, picp_in, picp_ood, ...
关键数值：epi_ratio = 1.07-1.21（所有参数都>1）
"""

# ═══════════════════════════════════════════════════════════════
# physics_consistency/ 子目录
# ═══════════════════════════════════════════════════════════════

DESCRIPTIONS["physics_consistency/monotonicity_manifest.json"] = """
================================================================================
monotonicity_manifest.json — 单调性检查 manifest
================================================================================

【秒懂版】
一句话：单调性实验的元数据。

【详细版】
记录实验配置、模型版本、检查的参数对列表。
"""

DESCRIPTIONS["physics_consistency/monotonicity_violation_rate.csv"] = """
================================================================================
monotonicity_violation_rate.csv — 单调性违反率（Fig. 5A 数据源）
================================================================================

【秒懂版】
一句话：每个输入-输出对的单调性违反比例——物理正则化是否有效的核心证据。

通俗解释：
物理上，某些参数对输出有明确的单调关系（如增大弹性模量→增大应力）。
这个文件记录BNN预测是否遵守了这些关系。违反率 = 不遵守的测试样本比例。
几乎全部为0%（物理约束有效），仅 α_SS316→fuel_temp 约37%（该对物理关系弱）。

【详细版】
论文定位：Fig. 5A, Fig. A2(A) 数据源
列结构：model_id, input, output, n_violations, n_total, violation_rate
关键数值：高置信对全部 0%，α_SS316→fuel_temp ≈ 37%
"""

DESCRIPTIONS["physics_consistency/inequality_violation_rate.csv"] = """
================================================================================
inequality_violation_rate.csv — 不等式约束违反率
================================================================================

【秒懂版】
一句话：BNN是否遵守不等式物理约束（如 coupled_stress ≤ uncoupled_stress）。

通俗解释：
除了单调性，还有一些跨迭代的不等式约束。这个文件记录违反比例。

【详细版】
列结构：model_id, constraint_type, n_violations, n_total, violation_rate
对应论文：Supplementary Note B
"""

# ═══════════════════════════════════════════════════════════════
# sensitivity/ 子目录
# ═══════════════════════════════════════════════════════════════

DESCRIPTIONS["sensitivity/sobol_convergence.csv"] = """
================================================================================
sobol_convergence.csv — Sobol指数收敛数据（Fig. S1 数据源）
================================================================================

【秒懂版】
一句话：不同样本量下的 Sobol 指数及其标准差——验证结果是否稳定可靠。

通俗解释：
记录了 N_base = 256, 512, 1024, 2048, 4096, 8192 下每个参数的
S₁ 均值和标准差（50次重复）。N_base ≥ 2048 时标准差 < 0.04。

【详细版】
论文定位：Fig. S1 数据源，Supplementary Note D.2
列结构：model_id, output, input, N_base, S1_mean, S1_std, S1_ci_lo, S1_ci_hi
关键数值：N=8192时 std < 0.011
"""

# ═══════════════════════════════════════════════════════════════
# speed/ 子目录
# ═══════════════════════════════════════════════════════════════

DESCRIPTIONS["speed/budget_matched_manifest.json"] = """
================================================================================
budget_matched_manifest.json — 速度实验 manifest
================================================================================

【秒懂版】
一句话：速度对比实验的元数据。

【详细版】
记录实验配置、HF 单次耗时来源等信息。
"""

DESCRIPTIONS["speed/budget_matched_risk.csv"] = """
================================================================================
budget_matched_risk.csv — 预算匹配风险对比（Fig. 7A 数据源）
================================================================================

【秒懂版】
一句话：达到相同风险估计精度目标时，HF仿真和BNN分别需要多少时间和多少样本。

通俗解释：
对不同的目标CI半宽（0.001到0.05），计算HF直接Monte Carlo和BNN各需要
多少样本、多少计算时间。加速比 = HF总时间 / BNN总时间 ≈ 1.7×10⁸。

【详细版】
论文定位：Fig. 7A, Fig. A3(C) 数据源
列结构：model_id, surrogate_mode, tau_MPa, target_CI_half,
        n_samples_HF, HF_total_sec, n_samples_surr, surrogate_total_sec,
        speedup_HF_over_surr
关键数值：speedup ≈ 1.7e8（每次HF ~2266s，BNN推断 ~13μs）
"""

DESCRIPTIONS["speed/hf_wallclock_source.json"] = """
================================================================================
hf_wallclock_source.json — 高保真仿真耗时来源
================================================================================

【秒懂版】
一句话：高保真仿真单次运行的平均耗时（~2266秒）及其来源说明。

通俗解释：
记录了HF仿真耗时的来源（从实际运行日志中提取），用于计算加速比。

【详细版】
内容：hf_mean_sec, source_description, n_samples_measured
"""

# ═══════════════════════════════════════════════════════════════
# uncertainty_decomposition/ 子目录
# ═══════════════════════════════════════════════════════════════

DESCRIPTIONS["uncertainty_decomposition/uncertainty_decomposition.csv"] = """
================================================================================
uncertainty_decomposition.csv — 不确定性分解（Fig. 5B 数据源）
================================================================================

【秒懂版】
一句话：每个模型、每个输出的 epistemic vs aleatoric 不确定性占比。

通俗解释：
BNN的总预测不确定性可以分解为：
- Epistemic（认知）：来自模型参数的不确定性，可通过更多数据减少
- Aleatoric（偶然）：来自数据噪声，不可减少
frac_epistemic = epistemic_var / total_var

【详细版】
论文定位：Fig. 5B, Fig. A2(B) 数据源
列结构：model_id, output_label, epi_std_mean, ale_std_mean,
        frac_epistemic_mean, frac_epistemic_std
关键数值：wall_temp epistemic 42%，k_eff 21%
"""

# ═══════════════════════════════════════════════════════════════
# results_v3418/ — 实验底层结果（0404 pipeline 产出）
# ═══════════════════════════════════════════════════════════════

DESCRIPTIONS["results_v3418/meta_stats.json"] = """
================================================================================
meta_stats.json — 数据集元统计
================================================================================

【秒懂版】
一句话：完整数据集的统计摘要（均值、标准差、范围等）。

通俗解释：
记录 n=2900 个样本的各列统计量，用于数据完整性检查和归一化参考。

【详细版】
内容：n_total, feature_stats（per-column mean, std, min, max）
"""

# --- fixed_split ---
DESCRIPTIONS["results_v3418/fixed_split/split_meta.json"] = """
================================================================================
split_meta.json — 固定数据划分元信息
================================================================================

【秒懂版】
一句话：训练/验证/测试集的划分方式记录——seed=2026，70/15/15比例。

通俗解释：
所有实验使用同一个固定划分（fixed split），确保结果可比。
2029训练 + 436验证 + 435测试。

【详细版】
内容：seed=2026, n_total=2900, n_train=2029, n_val=436, n_test=435
"""

for fname in ["train.csv", "val.csv", "test.csv"]:
    split = fname.replace(".csv", "")
    n = {"train": 2029, "val": 436, "test": 435}[split]
    DESCRIPTIONS[f"results_v3418/fixed_split/{fname}"] = f"""
================================================================================
{fname} — {split}集数据（{n}样本）
================================================================================

【秒懂版】
一句话：{split}集的完整数据——8个输入 + 15个输出列。

通俗解释：
每行是一个仿真样本，前8列是输入材料参数，后15列是仿真输出（iter1+iter2的各物理量）。

【详细版】
行数：{n}
列：E_intercept, E_slope, nu, alpha_base, alpha_slope, k_ref, T_ref, alpha_SS316,
    + 15个输出列（iter1_* + iter2_*）
"""

for fname in ["train_indices.csv", "val_indices.csv", "test_indices.csv"]:
    split = fname.replace("_indices.csv", "")
    DESCRIPTIONS[f"results_v3418/fixed_split/{fname}"] = f"""
================================================================================
{fname} — {split}集索引
================================================================================

【秒懂版】
一句话：{split}集样本在原始数据集中的行索引编号。

【详细版】
用途：根据索引从完整数据集中复现划分
"""

# --- models ---
for model in ["bnn-baseline", "bnn-baseline-homo", "bnn-mf-hybrid", "bnn-phy-mono"]:
    nice = {
        "bnn-baseline": "Reference BNN（基准贝叶斯神经网络）",
        "bnn-baseline-homo": "Homoscedastic Baseline BNN（同方差基准BNN）",
        "bnn-mf-hybrid": "Multi-fidelity Hybrid BNN（多保真度混合BNN）",
        "bnn-phy-mono": "Physics-regularized BNN（物理正则化BNN）",
    }[model]
    role = {
        "bnn-baseline": "主对比模型——无物理约束的标准BNN",
        "bnn-baseline-homo": "消融实验——同方差噪声假设的变体",
        "bnn-mf-hybrid": "消融实验——利用非耦合/耦合残差的多保真度变体",
        "bnn-phy-mono": "主推荐模型——加入单调性物理约束的BNN",
    }[model]

    DESCRIPTIONS[f"results_v3418/models/{model}/artifacts/metrics_{model}_fixed.json"] = f"""
================================================================================
metrics_{model}_fixed.json — {nice} 训练指标
================================================================================

【秒懂版】
一句话：{nice}训练过程中的最终指标（最佳验证NLL等）。

【详细版】
角色：{role}
内容：best_val_nll, best_epoch, training_time_sec, ...
"""

    DESCRIPTIONS[f"results_v3418/models/{model}/artifacts/training_history_{model}_fixed.json"] = f"""
================================================================================
training_history_{model}_fixed.json — {nice} 训练历史
================================================================================

【秒懂版】
一句话：每个epoch的训练损失和验证损失变化记录。

【详细版】
角色：{role}
内容：per-epoch train_loss, val_loss, val_nll, lr, ...
用途：检查是否收敛、是否过拟合
"""

    for suffix in ["eval_manifest_fixed.json", "metrics_fixed.json",
                   "metrics_per_output_fixed.csv",
                   f"test_predictions_{model}_fixed.json",
                   "test_predictions_fixed.json"]:
        path = f"results_v3418/models/{model}/fixed_eval/{suffix}"
        if "manifest" in suffix:
            DESCRIPTIONS[path] = f"""
================================================================================
{suffix} — {nice} 评估 manifest
================================================================================

【秒懂版】
一句话：固定划分评估实验的元数据。

【详细版】
角色：{role}
内容：eval配置、git_sha、checkpoint路径
"""
        elif "metrics_fixed" in suffix and suffix.endswith(".json"):
            DESCRIPTIONS[path] = f"""
================================================================================
{suffix} — {nice} 全局评估指标
================================================================================

【秒懂版】
一句话：在435个测试样本上的全局 RMSE、R²、NLL 等指标。

【详细版】
角色：{role}
内容：overall RMSE, R2, MAE, NLL, CRPS, ECE, PICP, ...
"""
        elif "metrics_per_output" in suffix:
            DESCRIPTIONS[path] = f"""
================================================================================
{suffix} — {nice} 按输出的评估指标
================================================================================

【秒懂版】
一句话：每个输出量单独的 RMSE、R² 等指标明细。

【详细版】
角色：{role}
列结构：output, RMSE, R2, MAE, NLL, CRPS, ECE, PICP, MPIW
"""
        elif "test_predictions" in suffix:
            DESCRIPTIONS[path] = f"""
================================================================================
{suffix} — {nice} 测试集预测值
================================================================================

【秒懂版】
一句话：435个测试样本的预测均值、预测标准差、真实值。

【详细版】
角色：{role}
内容：pred_mean, pred_std, true_value (per sample per output)
用途：画奇偶图、计算校准指标的原始数据
"""

    for suffix in ["eval_manifest_fixed.json",
                   f"training_manifest_{model}_fixed.json"]:
        path = f"results_v3418/models/{model}/manifests/{suffix}"
        DESCRIPTIONS[path] = f"""
================================================================================
{suffix} — {nice} manifest副本
================================================================================

【秒懂版】
一句话：训练/评估 manifest 的备份（与 artifacts/ 或 fixed_eval/ 中的相同）。

【详细版】
角色：{role}
用途：集中存放所有 manifest 便于检索
"""

# --- experiments: sensitivity ---
for model in ["bnn-baseline", "bnn-mf-hybrid", "bnn-phy-mono"]:
    nice = model.replace("-", " ").title()
    for fname in ["prcc_results.csv", "sensitivity_comparison.csv",
                   "sensitivity_manifest.json", "sobol_full.json",
                   "sobol_results.csv", "spearman_results.csv"]:
        path = f"results_v3418/experiments/sensitivity/{model}/{fname}"
        if "prcc" in fname:
            DESCRIPTIONS[path] = f"""
================================================================================
{fname} — {nice} PRCC 敏感性
================================================================================

【秒懂版】
一句话：{nice} BNN代理上计算的偏秩相关系数。

【详细版】
列结构：input, output, prcc, p_value
用途：与 Sobol 指数交叉验证
"""
        elif "comparison" in fname:
            DESCRIPTIONS[path] = f"""
================================================================================
{fname} — {nice} 敏感性方法对比
================================================================================

【秒懂版】
一句话：Sobol、PRCC、SRC、Spearman 四种敏感性度量的排序对比。

【详细版】
用途：验证不同方法的一致性
"""
        elif "manifest" in fname:
            DESCRIPTIONS[path] = f"""
================================================================================
{fname} — {nice} 敏感性实验 manifest
================================================================================

【秒懂版】
一句话：Sobol敏感性实验的元数据。

【详细版】
内容：N_base, n_replications, model_id, config_sha256, ...
"""
        elif "sobol_full" in fname:
            DESCRIPTIONS[path] = f"""
================================================================================
{fname} — {nice} Sobol 完整结果
================================================================================

【秒懂版】
一句话：所有参数×所有输出的 S₁、S_T 及其置信区间的完整 JSON。

【详细版】
内容：per (input, output) pair: S1_mean, S1_ci, ST_mean, ST_ci
用途：Fig. 4, Fig. A4 的最终数据源
"""
        elif "sobol_results" in fname:
            DESCRIPTIONS[path] = f"""
================================================================================
{fname} — {nice} Sobol CSV 结果
================================================================================

【秒懂版】
一句话：Sobol指数的CSV格式版本（与 sobol_full.json 内容相同，格式不同）。

【详细版】
列结构：input, output, S1, S1_ci_lo, S1_ci_hi, ST, ST_ci_lo, ST_ci_hi
"""
        elif "spearman" in fname:
            DESCRIPTIONS[path] = f"""
================================================================================
{fname} — {nice} Spearman 秩相关
================================================================================

【秒懂版】
一句话：Spearman秩相关系数——另一种非参数敏感性度量。

【详细版】
列结构：input, output, rho, p_value
"""

# --- experiments: posterior ---
for model in ["bnn-baseline", "bnn-mf-hybrid", "bnn-phy-mono"]:
    nice = model.replace("-", " ").title()
    for fname in ["benchmark_case_meta.json", "benchmark_summary.csv",
                   "feasible_region.csv", "posterior_manifest.json"]:
        path = f"results_v3418/experiments/posterior/{model}/{fname}"
        if "meta" in fname:
            DESCRIPTIONS[path] = f"""
================================================================================
{fname} — {nice} 后验 benchmark 案例元信息
================================================================================

【秒懂版】
一句话：18个benchmark案例的选取逻辑和真实参数值。

【详细版】
内容：18 cases (6 low / 6 near / 6 high stress)，每个案例的
      test_index, true_params, stress_category
"""
        elif "summary" in fname:
            DESCRIPTIONS[path] = f"""
================================================================================
{fname} — {nice} 后验 benchmark 汇总
================================================================================

【秒懂版】
一句话：18个案例的后验推断结果汇总——coverage, R̂, ESS, acceptance rate。

通俗解释：
每行一个案例×参数，记录后验均值、90%CI、是否覆盖真值、R̂、ESS等。
是 Fig. 6 和 Table 的核心数据源。

【详细版】
列结构：case_id, param, posterior_mean, ci_lo, ci_hi, covers_true,
        rhat, ess, acceptance_rate
关键数值（phy-mono）：mean coverage 0.917, R̂_max 1.017, ESS_min 352
"""
        elif "feasible" in fname:
            DESCRIPTIONS[path] = f"""
================================================================================
{fname} — {nice} 可行域分析
================================================================================

【秒懂版】
一句话：后验样本中有多少比例满足安全约束（σ < 131 MPa）。

通俗解释：
用后验参数样本做正向传播，计算 P(σ > 131 MPa | posterior)。
高应力案例的这个概率应该较高（确实观测到高应力）。

【详细版】
列结构：case_id, stress_category, P_exceed_131, n_feasible, ...
"""
        elif "manifest" in fname:
            DESCRIPTIONS[path] = f"""
================================================================================
{fname} — {nice} 后验实验 manifest
================================================================================

【秒懂版】
一句话：后验校准实验的元数据。

【详细版】
内容：n_chains, n_iterations, burn_in, noise_frac, model_id, ...
"""

# --- experiments: risk_propagation ---
for model in ["bnn-baseline", "bnn-baseline-homo", "bnn-mf-hybrid", "bnn-phy-mono"]:
    nice = model.replace("-", " ").title()
    for fname in ["D1_nominal_risk.csv", "D1_nominal_risk.json",
                   "D2_case_risk.csv", "D2_case_risk.json",
                   "D3_coupling.csv", "D3_coupling.json",
                   "risk_manifest.json"]:
        path = f"results_v3418/experiments/risk_propagation/{model}/{fname}"
        if "D1" in fname:
            fmt = "JSON" if fname.endswith(".json") else "CSV"
            DESCRIPTIONS[path] = f"""
================================================================================
{fname} — {nice} 标称风险估计 ({fmt})
================================================================================

【秒懂版】
一句话：标准先验下的正向传播风险结果——P(σ>131 MPa), 应力分布统计量。

通俗解释：
用20000个Monte Carlo样本传播输入不确定性，统计应力的均值、标准差、
各阈值下的超限概率。

【详细版】
关键字段：stress_mean, stress_std, P_exceed_131, P_exceed_120, P_exceed_110
对应论文：Fig. 3 (forward UQ), Table 2
"""
        elif "D2" in fname:
            fmt = "JSON" if fname.endswith(".json") else "CSV"
            DESCRIPTIONS[path] = f"""
================================================================================
{fname} — {nice} 风险分案例结果 ({fmt})
================================================================================

【秒懂版】
一句话：不同输入不确定性放大倍数下的应力超限概率曲线数据。

通俗解释：
σ_k 从0.5到2.0变化时，P(σ>τ) 如何变化。σ_k=1为标准先验。

【详细版】
对应论文：Fig. 3D (Risk curve)
"""
        elif "D3" in fname:
            fmt = "JSON" if fname.endswith(".json") else "CSV"
            DESCRIPTIONS[path] = f"""
================================================================================
{fname} — {nice} 耦合效应分析 ({fmt})
================================================================================

【秒懂版】
一句话：各输出量的耦合偏移（coupled - uncoupled）的统计量。

通俗解释：
记录非耦合和耦合稳态之间的均值差、标准差变化、分布偏移量。

【详细版】
对应论文：Fig. 3C (Coupling delta)
"""
        elif "manifest" in fname:
            DESCRIPTIONS[path] = f"""
================================================================================
{fname} — {nice} 风险传播实验 manifest
================================================================================

【秒懂版】
一句话：风险传播实验的元数据。

【详细版】
内容：n_mc_samples, tau_list, model_id, ...
"""

# --- experiments: generalization ---
for model in ["bnn-baseline", "bnn-mf-hybrid", "bnn-phy-mono"]:
    nice = model.replace("-", " ").title()
    for fname in ["generalization_manifest.json", "ood_per_output.csv", "ood_summary.csv"]:
        path = f"results_v3418/experiments/generalization/{model}/{fname}"
        if "manifest" in fname:
            DESCRIPTIONS[path] = f"""
================================================================================
{fname} — {nice} 泛化实验 manifest
================================================================================

【秒懂版】
一句话：OOD泛化实验的元数据。

【详细版】
内容：ood_definition（尾部百分位）、model_id、n_test_samples
"""
        elif "per_output" in fname:
            DESCRIPTIONS[path] = f"""
================================================================================
{fname} — {nice} OOD 按输出指标
================================================================================

【秒懂版】
一句话：每个输出量在 OOD 区域的 RMSE、PICP、epistemic ratio 明细。

【详细版】
列结构：output, rmse_in, rmse_ood, picp_in, picp_ood, epi_ratio
"""
        elif "summary" in fname:
            DESCRIPTIONS[path] = f"""
================================================================================
{fname} — {nice} OOD 汇总
================================================================================

【秒懂版】
一句话：该模型的OOD泛化能力总结——epistemic inflation 和 coverage 保持情况。

【详细版】
列结构：param, epi_ratio_mean, picp_ood, picp_in, coverage_drop, ...
"""

# --- experiments: computational_speedup ---
for model in ["bnn-baseline", "bnn-mf-hybrid"]:
    nice = model.replace("-", " ").title()
    for fname in ["bnn_speed_benchmark.json", "manifest.json"]:
        path = f"results_v3418/experiments/computational_speedup/{model}/{fname}"
        if "speed" in fname:
            DESCRIPTIONS[path] = f"""
================================================================================
{fname} — {nice} 速度基准测试
================================================================================

【秒懂版】
一句话：BNN单次推断耗时的基准测试结果（微秒级）。

通俗解释：
记录 batch_size=1 和 batch 模式下的推断耗时。
单次约13微秒，与HF的2266秒相比加速 ~1.7×10⁸。

【详细版】
内容：single_sample_sec, batch_1000_sec, per_sample_batch_sec
"""
        else:
            DESCRIPTIONS[path] = f"""
================================================================================
{fname} — {nice} 速度实验 manifest
================================================================================

【秒懂版】
一句话：速度基准测试的元数据。

【详细版】
内容：model_id, n_warmup, n_trials, device, ...
"""

# --- experiments: small_sample ---
for model in ["bnn-baseline", "bnn-mf-hybrid"]:
    nice = model.replace("-", " ").title()
    for frac in ["0.2", "0.4", "0.6"]:
        pct = int(float(frac) * 100)
        path = f"results_v3418/experiments/small_sample/{model}/frac_{frac}/metrics.json"
        DESCRIPTIONS[path] = f"""
================================================================================
metrics.json — {nice} 小样本({pct}%训练数据)
================================================================================

【秒懂版】
一句话：只用{pct}%训练数据时的模型精度——测试小数据下的鲁棒性。

通俗解释：
用 {pct}% 的训练集（约{int(2029*float(frac))}样本）训练后，
在完整测试集上的 RMSE、R²、CRPS 等指标。
是数据效率分析的底层数据。

【详细版】
内容：per-output RMSE, R2, NLL, CRPS, ...
对应论文：Fig. 7B (data efficiency curve) 的底层数据点
"""

# --- analysis ---
DESCRIPTIONS["results_v3418/analysis/conformal_calibration.csv"] = """
================================================================================
conformal_calibration.csv — 共形校准分析
================================================================================

【秒懂版】
一句话：用共形预测方法对BNN的预测区间进行后处理校准的结果。

通俗解释：
共形预测（conformal prediction）是一种无分布假设的校准方法。
这个文件记录了共形校准前后的覆盖率变化。

【详细版】
列结构：model_id, output, nominal_level, uncalibrated_coverage,
        conformal_coverage
"""

DESCRIPTIONS["results_v3418/analysis/near_threshold_calibration.csv"] = """
================================================================================
near_threshold_calibration.csv — 阈值附近校准分析
================================================================================

【秒懂版】
一句话：在应力接近131 MPa设计阈值的样本子集上，校准质量是否退化？

通俗解释：
安全评估最关心的是阈值附近的预测精度。这个文件单独分析了
应力在 120-145 MPa 范围内的样本的校准指标。

【详细版】
列结构：model_id, output, subset, PICP, MPIW, ECE, n_samples
用途：检验模型在"最重要的区域"是否仍然可靠
"""


# ═══════════════════════════════════════════════════════════════
# 写入文件
# ═══════════════════════════════════════════════════════════════

def main():
    written = 0
    skipped = 0
    for rel_path, content in DESCRIPTIONS.items():
        data_path = RESULTS / rel_path
        if not data_path.exists():
            print(f"  SKIP (not found): {data_path}")
            skipped += 1
            continue
        txt_path = data_path.with_suffix(".txt")
        txt_path.write_text(content.strip() + "\n", encoding="utf-8")
        written += 1
    print(f"\nDone: {written} result description files written, {skipped} skipped.")


if __name__ == "__main__":
    main()
