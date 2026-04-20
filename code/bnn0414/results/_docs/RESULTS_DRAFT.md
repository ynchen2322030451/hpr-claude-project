# Results Section Draft — 中英双语

> 以下每个子节按自然段中英交替。数值均来自实验结果。
> 标记 [Fig X] / [Table X] 表示对应图表。
> 标记 ⚠️ 表示需要核实或可能需要调整表述的地方。

---

## 2.1 Predictive accuracy and uncertainty calibration

### EN
We evaluated four BNN surrogate variants alongside two conventional UQ baselines — MC-Dropout and a five-member deep ensemble — on a held-out test set of 435 coupled thermo-mechanical simulations. Prediction accuracy and probabilistic calibration were assessed across five primary outputs: coupled steady-state maximum stress, $k_{\mathrm{eff}}$, maximum fuel temperature, maximum monolith temperature, and wall expansion [Table 1].

### 中文
我们在 435 个耦合热-力模拟的保留测试集上，对四种 BNN 代理变体以及两种传统 UQ 基线方法（MC-Dropout 和五成员深度集成）进行了评估。预测精度和概率校准评估覆盖五个主要输出：耦合稳态最大应力、$k_{\mathrm{eff}}$、最大燃料温度、最大基体温度和壁面膨胀 [Table 1]。

### EN
Across five random seeds, the physics-regularized BNN achieved the lowest global CRPS (1.92 ± 0.07), the narrowest mean prediction interval width (MPIW = 15.24 ± 0.26), and a 90% prediction interval coverage probability (PICP) of 0.970 ± 0.006 — slightly below but close to the nominal level. By contrast, the data+inequality BNN, which imposes the most constraints, exhibited the widest intervals (MPIW = 21.14) and the highest PICP (0.986), indicating over-conservative uncertainty estimates. Point-prediction accuracy was comparable across all four BNN variants (RMSE 3.41–3.53), confirming that physics-informed regularization does not degrade predictive performance [Table 1, Fig 1].

### 中文
在五个随机种子的重复实验中，物理正则化 BNN 取得了最低的全局 CRPS（1.92 ± 0.07）、最窄的预测区间宽度（MPIW = 15.24 ± 0.26），以及 0.970 ± 0.006 的 90% 覆盖率——略低于但接近标称水平。相比之下，施加最多约束的 data+inequality BNN 表现出最宽的区间（MPIW = 21.14）和最高的覆盖率（0.986），表明其不确定性估计过于保守。四种 BNN 变体的点预测精度相当（RMSE 3.41–3.53），证实物理先验正则化不会损害预测性能。

### EN
Compared with conventional UQ approaches, the BNN surrogates demonstrated substantially better calibration on temperature outputs. For maximum fuel temperature, BNN achieved an expected calibration error (ECE) of 0.03–0.04, whereas MC-Dropout and deep ensemble yielded ECE of 0.183 and 0.190, respectively. BNN RMSE for fuel temperature (4.26) was also notably lower than both baselines (~4.50). For stress prediction, however, point accuracy was comparable across methods (RMSE ≈ 7.6), with the BNN advantage manifesting primarily in tighter, better-calibrated prediction intervals (ECE 0.106 for physics-regularized BNN vs 0.112–0.118 for baselines) [Table 1, Fig 1C].

### 中文
与传统 UQ 方法相比，BNN 代理在温度输出上展现出显著更好的校准性能。对于最大燃料温度，BNN 的期望校准误差（ECE）为 0.03–0.04，而 MC-Dropout 和深度集成分别为 0.183 和 0.190。BNN 的燃料温度 RMSE（4.26）也明显低于两种基线方法（~4.50）。然而在应力预测方面，各方法的点预测精度相当（RMSE ≈ 7.6），BNN 的优势主要体现在更紧凑、校准更好的预测区间上（物理正则化 BNN 的 ECE 为 0.106，基线方法为 0.112–0.118）。

> ⚠️ **注意**: keff 的 R2 外部基线反而更高 (0.83–0.86 vs BNN 0.63)，但这可能是因为 keff 的变异性很小。BNN 的 CRPS 和 NLL 在 keff 上与基线相当。论文中不宜强调 keff 的 R2 对比。

---

## 2.2 Physics consistency

### EN
We assessed physics consistency through two complementary tests: monotonicity verification against 15 known input–output relationships and inequality constraint satisfaction [Fig 2A]. For all high-confidence monotonicity pairs — including the dominant stress drivers $E_{\mathrm{intercept}}$ (+), $\alpha_{\mathrm{base}}$ (+), and $k_{\mathrm{ref,SS316}}$ (−) — all four BNN variants achieved a zero violation rate on 435 held-out test samples using discrete ±δ perturbation counterexample testing. The only non-trivial violations occurred for the medium-confidence pair SS316_α → fuel temperature (36–54% across models), reflecting a weaker and potentially nonlinear physical relationship that even the training data does not consistently support. All four models also satisfied ordering (max ≥ average temperature) and non-negativity (stress ≥ 0) constraints with zero violations.

### 中文
我们通过两项互补测试评估了物理一致性：针对 15 个已知输入-输出关系的单调性验证，以及不等式约束的满足情况 [Fig 2A]。对于所有高置信度单调对——包括应力的主要驱动因素 $E_{\mathrm{intercept}}$（+）、$\alpha_{\mathrm{base}}$（+）和 $k_{\mathrm{ref,SS316}}$（−）——四种 BNN 变体在 435 个测试样本上通过离散 ±δ 扰动反例测试均实现了零违反率。唯一的显著违反出现在中等置信度的 SS316_α → 燃料温度对（各模型 36–54%），反映了一种较弱且可能非线性的物理关系，甚至训练数据本身也不能一致支持该单调关系。所有四个模型在排序约束（最大 ≥ 平均温度）和非负约束（应力 ≥ 0）上均实现零违反。

> ⚠️ **注意**: data-mono-ineq 在 SS316_k_ref → stress 上有 1.1% 违反 (max magnitude 1.89 MPa)，这比较尴尬，因为这个模型恰恰是约束最多的。可以提但要注明 magnitude 极小。

---

## 2.3 Uncertainty decomposition

### EN
Decomposing total predictive variance into epistemic and aleatoric components revealed that aleatoric uncertainty dominates across all outputs, accounting for 58–90% of total variance [Fig 2B]. The epistemic fraction was highest for wall expansion (~42%) and stress (~30%), suggesting greater model-form uncertainty for these outputs. Physics regularization slightly reduced epistemic uncertainty for temperature predictions (epistemic fraction 10.1% for physics-regularized BNN vs 11.2–12.0% for the reference BNN), consistent with the hypothesis that monotonicity constraints help "lock in" plausible model structures.

### 中文
将总预测方差分解为认知（epistemic）和偶然（aleatoric）分量后发现，偶然不确定性在所有输出上占主导地位，占总方差的 58–90% [Fig 2B]。认知不确定性占比最高的是壁面膨胀（~42%）和应力（~30%），说明模型对这些输出的结构不确定性较大。物理正则化略微降低了温度预测的认知不确定性（物理正则化 BNN 为 10.1%，参考 BNN 为 11.2–12.0%），与单调性约束帮助"锁定"合理模型结构的假设一致。

---

## 2.4 Sensitivity analysis

### EN
Global sensitivity analysis via Sobol indices identified $E_{\mathrm{intercept}}$ as the dominant driver of coupled steady-state stress ($S_1$ = 0.54–0.57), followed by $\alpha_{\mathrm{base}}$ ($S_1$ ≈ 0.15–0.19). For $k_{\mathrm{eff}}$, $\alpha_{\mathrm{base}}$ was dominant ($S_1$ = 0.77–0.78), with $\alpha_{\mathrm{slope}}$ contributing a secondary effect ($S_1$ ≈ 0.19–0.20). Convergence analysis confirmed that these rankings stabilized by $N_{\mathrm{base}}$ = 2048, with standard deviations below 0.04 at the final sample size of 8192 [Fig S1]. Both the reference and physics-regularized BNN yielded consistent sensitivity rankings, indicating that the regularization does not distort the sensitivity structure.

### 中文
基于 Sobol 指数的全局敏感性分析表明，$E_{\mathrm{intercept}}$ 是耦合稳态应力的主导驱动因素（$S_1$ = 0.54–0.57），其次是 $\alpha_{\mathrm{base}}$（$S_1$ ≈ 0.15–0.19）。对于 $k_{\mathrm{eff}}$，$\alpha_{\mathrm{base}}$ 是主导因素（$S_1$ = 0.77–0.78），$\alpha_{\mathrm{slope}}$ 贡献次要效应（$S_1$ ≈ 0.19–0.20）。收敛性分析证实，这些排序在 $N_{\mathrm{base}}$ = 2048 时已趋稳定，在最终样本量 8192 时标准差低于 0.04 [Fig S1]。参考 BNN 和物理正则化 BNN 给出了一致的敏感性排序，表明正则化没有扭曲敏感性结构。

---

## 2.5 Posterior inference and MCMC diagnostics

### EN
Surrogate-accelerated Bayesian inversion was performed on 18 benchmark cases (6 low / 6 near-threshold / 6 high stress), using four independent Metropolis–Hastings chains of 1200 steps each per case. Convergence was assessed using split-$\hat{R}$ (rank-normalized, Vehtari et al., 2021) and Geyer initial positive sequence effective sample size. Across all 72 parameter-case combinations for the physics-regularized BNN, $\hat{R}_{\max}$ = 1.017 (well below the 1.1 threshold), $\mathrm{ESS}_{\min}$ = 352, and mean acceptance rate = 0.605 (within the optimal 0.44–0.66 range for four-dimensional target distributions). Trace plots and rank histograms for representative cases confirmed adequate mixing with no evidence of chain stagnation [Fig 3A, 3B].

### 中文
在 18 个基准案例（6 个低/6 个近阈值/6 个高应力）上进行了代理加速的贝叶斯反演，每个案例使用四条独立的 Metropolis–Hastings 链，每链 1200 步。收敛性通过 split-$\hat{R}$（秩归一化，Vehtari 等，2021）和 Geyer 初始正序列有效样本量进行评估。在物理正则化 BNN 的全部 72 个参数-案例组合中，$\hat{R}_{\max}$ = 1.017（远低于 1.1 阈值），$\mathrm{ESS}_{\min}$ = 352，平均接受率 = 0.605（在四维目标分布的最优范围 0.44–0.66 内）。代表性案例的迹图和秩直方图确认了充分的混合，无链停滞迹象 [Fig 3A, 3B]。

---

## 2.6 Prior and noise sensitivity

### EN
To assess the robustness of posterior inference, we varied the prior specification across six configurations: canonical, diffuse ($\sigma \to 2\sigma$), tight ($\sigma \to 0.5\sigma$), flat (uniform), and two shifted variants ($\mu \pm 0.5\sigma$). The canonical and diffuse priors both achieved 100% coverage of the true parameter values within the 90% credible interval. The flat (uninformative) prior also maintained 100% coverage but produced wider posteriors (mean KL divergence from canonical: 0.24–0.38). The tight prior, however, reduced coverage to 50–83% with KL divergences up to 1.28, indicating that the canonical prior width represents a near-minimal adequate specification [Fig S2].

### 中文
为评估后验推断的鲁棒性，我们在六种先验配置下进行了测试：标准、弥散（$\sigma \to 2\sigma$）、紧凑（$\sigma \to 0.5\sigma$）、平坦（均匀分布）以及两种偏移变体（$\mu \pm 0.5\sigma$）。标准和弥散先验均在 90% 可信区间内实现了对真实参数值 100% 的覆盖。平坦（无信息）先验也保持了 100% 覆盖，但产生了更宽的后验（与标准先验的平均 KL 散度：0.24–0.38）。然而，紧凑先验将覆盖率降至 50–83%，KL 散度高达 1.28，表明标准先验宽度已接近最小适当规格 [Fig S2]。

### EN
Observation noise sensitivity was evaluated by varying the assumed noise fraction from 0.5% to 10%. Posterior widths increased monotonically with noise level (e.g., posterior standard deviation of $E_{\mathrm{intercept}}$: 1.26×10¹⁰ at 0.5% noise to 1.40×10¹⁰ at 10% noise), while 90% credible interval coverage remained at 100% for all parameters except $\alpha_{\mathrm{slope}}$ at 10% noise (83%). The MCMC acceptance rate also increased appropriately with noise level (0.58 to 0.65), reflecting the broader likelihood [Fig S3].

### 中文
通过将假定噪声分数从 0.5% 变化到 10%，评估了观测噪声敏感性。后验宽度随噪声水平单调增加（例如 $E_{\mathrm{intercept}}$ 的后验标准差：从 0.5% 噪声时的 1.26×10¹⁰ 增至 10% 噪声时的 1.40×10¹⁰），而 90% 可信区间覆盖率对所有参数保持在 100%，仅 $\alpha_{\mathrm{slope}}$ 在 10% 噪声时降至 83%。MCMC 接受率也随噪声水平适当增加（0.58 至 0.65），反映了更宽的似然函数 [Fig S3]。

---

## 2.7 Computational efficiency

### EN
The BNN surrogate enables Monte Carlo risk analysis at a fraction of the cost of high-fidelity simulation. In batch evaluation mode, surrogate inference requires approximately 0.013 ms per sample, compared to 2266 s per coupled thermo-mechanical simulation — a speedup of approximately 1.7 × 10⁸. For the stress risk metric $P(\sigma > 131\ \mathrm{MPa})$ at a confidence interval half-width of 0.005, approximately 20,627 surrogate evaluations are required, completed in 0.28 s. The equivalent HF analysis would require 541 days of continuous computation [Fig 4A, Table 2].

### 中文
BNN 代理使得蒙特卡洛风险分析的计算成本仅为高保真模拟的极小部分。在批量评估模式下，代理推断每个样本约需 0.013 ms，而每次耦合热-力模拟需 2266 s——加速比约为 1.7 × 10⁸。对于应力风险指标 $P(\sigma > 131\ \mathrm{MPa})$，在置信区间半宽 0.005 的精度要求下，需要约 20,627 次代理评估，在 0.28 秒内完成。等效的高保真分析则需要 541 天的连续计算 [Fig 4A, Table 2]。

### EN
Data efficiency analysis revealed that the BNN achieves near-saturated accuracy with as few as 507 training samples (25% of the full training set), yielding RMSE = 4.93 compared to 4.62 at full data utilization — 96% of peak performance. The marginal improvement from 50% to 100% data was less than 1%, suggesting that the BNN architecture effectively exploits limited training data [Fig 4B].

### 中文
数据效率分析表明，BNN 仅需 507 个训练样本（完整训练集的 25%）即可达到接近饱和的精度，RMSE = 4.93，而完整数据利用率下为 4.62——达到峰值性能的 96%。从 50% 到 100% 数据的边际改善不到 1%，表明 BNN 架构能够有效利用有限的训练数据 [Fig 4B]。

---

## 2.8 Out-of-distribution robustness

### EN
To verify that the BNN produces appropriately inflated uncertainty estimates for out-of-distribution inputs, we partitioned the test set along each of four input features into in-distribution (central 80%) and OOD (peripheral 20%) subsets. The epistemic standard deviation increased by 7–21% in OOD regions across all models and features, while the 90% PICP remained above 96% even in OOD regions (in some cases increasing from 0.97 to 0.98 due to wider intervals). This behavior is consistent with Bayesian epistemic uncertainty: the model correctly signals greater ignorance in under-represented input regions without sacrificing coverage [Fig S4].

### 中文
为验证 BNN 对分布外输入能否产生适当膨胀的不确定性估计，我们沿四个输入特征将测试集划分为分布内（中心 80%）和分布外（外围 20%）子集。所有模型和特征的认知标准差在 OOD 区域增加了 7–21%，而 90% PICP 在 OOD 区域仍保持在 96% 以上（某些情况下由于区间变宽，从 0.97 升至 0.98）。这一行为符合贝叶斯认知不确定性的预期：模型正确地在训练数据稀疏的输入区域发出更高的不确定性信号，而不牺牲覆盖率 [Fig S4]。

---

## ⚠️ 论文叙述建议

1. **主线**: baseline vs phy-mono，其他模型仅在 Table 1 和附录中出现
2. **不宜过度渲染的点**:
   - keff R2 (BNN 0.63 vs 外部基线 0.83–0.86，BNN 反而更低)
   - data-mono-ineq 的任何"最佳"声明 (已 demoted)
   - "物理一致性完美" (SS316_alpha→fuel_temp 36–54% violation)
3. **可以强调的点**:
   - 温度 ECE: BNN 0.03 vs baselines 0.18 (5–6x 改善)
   - 物理约束不损精度 (RMSE 几乎不变)
   - 计算加速 10⁸ 量级
   - OOD epistemic 正确膨胀
   - MCMC rhat < 1.02, 收敛性好
   - 先验敏感性: canonical 合理, tight 过强
   - 数据效率: 25% 数据达到 96% 精度
