# Core Contribution Statement

> **Purpose**: This file defines the paper's central argument. All Abstract, Introduction,
> and Discussion revisions must align with the framing here.
>
> **Authority**: Numbers in this file are drawn from CANONICAL_DATA_SUMMARY.md (last
> verified 2026-04-24). Any discrepancy between this file and the canonical source
> is a bug in this file.

---

## Core Contribution Statement (EN)

The central contribution of this work is not a more accurate surrogate model. On peak
stress prediction, the physics-regularized BNN (R² = 0.944) and a five-member deep
ensemble (R² = 0.934) achieve comparable accuracy. The contribution is instead a
**unified probabilistic layer**: a single posterior predictive distribution that serves
forward uncertainty propagation, variance-based sensitivity decomposition, and
observation-conditioned posterior calibration without retraining between analyses. This
design produces coherent conclusions across the three analysis stages. The Sobol analysis
identifies E_intercept as the dominant driver of stress variance (S₁ = 0.58) and
alpha_base as the dominant driver of k_eff variance (S₁ = 0.79) — distinct physical
pathways with minimal overlap. The posterior calibration contracts most strongly along
precisely these same parameter directions. This alignment is not imposed: it emerges
because all three analyses share the same posterior predictive distribution. Point-estimate
surrogates require separate uncertainty wrappers for each task, and post-hoc wrappers
carry no structural guarantee that the wrappers will agree with one another. The BNN
posterior eliminates this inconsistency by construction.

---

## 核心贡献声明（中文）

本文的核心贡献不在于代理模型预测精度的提升。在峰值应力预测方面，物理正则化贝叶斯
神经网络（R² = 0.944）与五成员深度集成模型（R² = 0.934）的精度相当。本文真正的贡献
在于构建了一个**统一概率层**：同一个后验预测分布无需重训练，即可同时驱动前向不确
定性传播、基于方差的全局敏感性分解以及基于观测的后验参数标定。这一设计使三个分析
阶段在逻辑上相互一致。Sobol 分析识别出 E_intercept 主导应力方差（S₁ = 0.58），
alpha_base 主导有效增殖因子 k_eff 的方差（S₁ = 0.79），二者分属不同的物理机制通道，
几乎没有重叠。后验标定中参数分布的收缩方向与上述 Sobol 主导参数高度吻合。这种一
致性并非人为强制，而是三个分析共享同一后验预测分布的自然结果。点估计代理模型需要
为各分析阶段分别构建不确定性包装器，而后挂式包装器之间并不存在结构性一致性保证。
贝叶斯神经网络的后验分布从设计上消除了这一不一致性。

---

## Key Evidence Chain

The coherence claim rests on four linked empirical observations, all from the
physics-regularized BNN (bnn-phy-mono) on the v3418 dataset.

### 1. Forward UQ — coupling damps stress variability by 30%

**Source**: `results_v3418/experiments/risk_propagation/bnn-phy-mono/D3_coupling.json`

Propagating 20,000 LHS samples through the BNN posterior predictive mean yields:

| Quantity | Coupled | Single-pass (pre-feedback) | Change |
|----------|---------|---------------------------|--------|
| Stress mean | 161.7 MPa | 203.5 MPa | −41.8 MPa |
| Stress std | 31.9 MPa | 45.5 MPa | **−30%** |

The variance-ratio between coupled and single-pass (pre-feedback) predictions is 0.490
(D3_coupling.json), giving std reduction = 1 − √0.490 = 30%. The "single-pass" baseline
is the first Picard iteration before iterative feedback converges; it is not a fully
decoupled single-physics solve (see Limitation v in the honest disclaimer paragraph below).

### 2. Sobol — distinct parameter pathways for stress and k_eff

**Source**: `results_v3418/experiments/sensitivity/bnn-phy-mono/sobol_results.csv`

| Output | Dominant parameter | S₁ | 90% CI | Physical domain |
|--------|-------------------|-----|--------|-----------------|
| Stress | E_intercept | 0.579 | [0.574, 0.583] | Structural mechanics |
| k_eff | alpha_base | 0.785 | [0.783, 0.788] | Thermal deformation |

No elasticity parameter has a nonzero first-order effect on k_eff (CI crosses zero for
all except alpha_base and alpha_slope). No thermal-deformation parameter appears among
the top-four stress contributors. The two outputs are governed by nearly disjoint
parameter sets. Alpha_base is a secondary stress contributor (S₁ = 0.169) but the
primary k_eff driver — the partial overlap is mechanistically expected (thermal expansion
affects both geometry and stress state) and is quantified rather than hidden.

Consistency check: E_intercept S₁ for stress = 0.600 (reference BNN) vs 0.579
(physics-regularized BNN) — a 3.5% difference, confirming the ranking is not an artifact
of the regularization.

### 3. Posterior — contraction aligns with Sobol-dominant directions

**Source**: `results_v3418/experiments/posterior/bnn-phy-mono/rerun_4chain/benchmark_summary.csv`

- Overall 90%-CI coverage: **0.861** (62/72 parameter-case combinations)
- Acceptance rate: 0.582–0.632, mean 0.606 (within optimal range for 4-D targets)
- R-hat max: **1.010** (well below 1.1 threshold)
- ESS min: 352

In high-stress benchmark cases, the E_intercept marginal shifts toward larger values,
consistent with its dominant Sobol role for stress. The joint E_intercept–alpha_base
posterior develops a compensation ridge (higher stiffness partially offset by lower
thermal expansion coefficient), reflecting the multiplicative structure σ ∝ E · α · ΔT.
This cross-parameter correlation is visible only because both parameters are calibrated
jointly within the same posterior, not sequentially with separate models.

Coverage is heterogeneous by stress category: 0.917 (high), 0.958 (near-threshold),
0.708 (low-stress). The low-stress shortfall is the largest acknowledged limitation of
the posterior analysis and is attributable primarily to alpha_slope, which has the weakest
Sobol sensitivity and is therefore least constrained by the five observed outputs.

### 4. Coherence — the structural property

All three analyses (forward UQ in §1, Sobol in §2, posterior in §3) operate on the same
BNN posterior predictive distribution without retraining or recalibration between them.
The consistency between Sobol-identified dominant parameters and posterior contraction
directions is therefore structurally guaranteed in the sense that no modelling choice
between the analyses can introduce inconsistency. It is not guaranteed to produce
large contraction (the data may be uninformative), but any contraction that does occur
must reflect parametric sensitivity that the Sobol analysis can also detect.

Point-estimate surrogates cannot provide this guarantee. Deep ensembles provide
distributional predictions through aggregation of independent networks, but applying
Bayesian posterior calibration to an ensemble requires a second modelling layer
(e.g. approximate Bayesian computation or likelihood-free inference) that is external
to the ensemble itself — introducing a potential source of inconsistency between the
forward-propagation and calibration stages.

---

## Draft Abstract (EN)

Coupled multiphysics reactor models require simultaneous forward uncertainty propagation,
global sensitivity attribution, and parameter calibration from observations — three
analyses that are typically carried out with separately constructed models, producing no
structural guarantee of mutual consistency. We address this gap by implementing a unified
probabilistic layer through a Bayesian neural network (BNN) trained on n = 3,418 coupled
OpenMC–FEniCS simulations of a heat-pipe-cooled microreactor. Forward propagation through
the posterior predictive distribution shows that iterative multi-physics feedback damps
the peak stress standard deviation by approximately 30% relative to the single-pass
prediction, while k_eff variability is created entirely by thermal-expansion modification
of core geometry. Sobol sensitivity decomposition identifies distinct parameter pathways
for the two safety-relevant outputs: Young's modulus intercept dominates stress variance
(S₁ = 0.58) and thermal-expansion coefficient dominates k_eff variance (S₁ = 0.79),
with minimal overlap. Posterior calibration on 18 synthetic benchmark cases contracts
the parameter distribution toward observation-compatible regions (90%-CI coverage 0.861),
with contraction strongest along the same Sobol-dominant parameter directions — a
coherence that emerges because all three analyses share the same posterior. Each
surrogate evaluation is 1.43 × 10⁵ times faster than a coupled high-fidelity solve,
enabling the full probabilistic workflow on a single workstation. The framework is
applicable to other coupled multiphysics systems for which training data can be generated.

*(Word count: 196)*

---

## Draft Abstract (CN)

耦合多物理场反应堆模型的完整不确定性分析需要同时开展前向不确定性传播、全局敏感性
归因以及基于观测的参数标定。这三类分析通常由各自独立构建的模型分别完成，彼此之间
缺乏结构性一致性保证。本文通过一个统一概率层解决上述问题：以贝叶斯神经网络（BNN）
为核心，在热管冷却微型反应堆的 3418 个耦合 OpenMC–FEniCS 模拟样本上进行训练。
将完整的参数不确定性经后验预测分布传播后发现，多物理场迭代反馈将峰值应力标准差较
单次预测降低约 30%，而有效增殖因子 k_eff 的变异性则完全由热膨胀引起的堆芯几何形
变贡献。Sobol 敏感性分解表明，两个安全相关输出量受不同参数组控制：弹性模量截距主
导应力方差（S₁ = 0.58），热膨胀系数主导 k_eff 方差（S₁ = 0.79），二者几乎互不
重叠。在 18 个合成基准案例上开展的后验参数标定将分布收缩至与观测相容的区域（90%
置信区间覆盖率 0.861），且收缩最强的方向恰好与 Sobol 分析识别出的主导参数方向一
致——这种一致性正是三类分析共享同一后验预测分布的内在结果。代理模型的单次评估速度
比耦合高保真求解快约 1.43 × 10⁵ 倍，完整的概率分析流程可在单台工作站上于数分钟内
完成。该框架在原则上适用于其他可生成耦合训练数据的多物理场系统。

---

## Honest Disclaimer Paragraph

*Intended location: Introduction, after the contribution bullet list and before the
section overview sentence. This paragraph replaces any implied claim that BNN dominates
conventional baselines on predictive accuracy.*

---

**EN version:**

We do not claim that the BNN produces more accurate point predictions than deep ensembles
or MC-Dropout. On peak stress, the physics-regularized BNN achieves R² = 0.944 and the
deep ensemble achieves R² = 0.934 (Table 1); on calibration quality, the BNN's
expected calibration error (ECE) is five to six times lower than either baseline. The
BNN's advantage is structural, not metric-wise. A deep ensemble produces a mixture
distribution by aggregating five independent point-estimate networks; applying
observation-conditioned posterior calibration to such a mixture requires a second
modelling layer — for example, approximate Bayesian computation or likelihood-free
inference — that is external to the ensemble and not guaranteed to remain consistent
with the forward propagation stage. The BNN posterior predictive distribution, by
contrast, is the same object used in all three analyses. Forward propagation, sensitivity
decomposition, and posterior calibration are all operations on this single distribution,
which eliminates by construction any inconsistency that could arise from maintaining
separate probabilistic models for each task.

---

**中文版本：**

本文并不主张贝叶斯神经网络在点预测精度上优于深度集成或 MC-Dropout 方法。在峰值应
力预测方面，物理正则化 BNN 的 R² 为 0.944，深度集成模型的 R² 为 0.934（见表 1）；
而在概率校准质量方面，BNN 的期望校准误差（ECE）比两种基线方法低五至六倍。BNN 的
优势在于方法结构，而非单一指标。深度集成通过聚合五个独立点估计网络生成混合分布；
若要对这种混合分布进行基于观测的后验参数标定，需要引入第二层建模——例如近似贝叶斯
计算或无似然推断——而这一外加层与前向传播阶段之间并不存在一致性保证。相比之下，BNN
的后验预测分布本身即是三类分析共用的同一概率对象：前向传播、敏感性分解与后验标定
均作用于这同一分布，从设计层面消除了分阶段使用不同概率模型所可能引入的内在矛盾。

---

*End of CORE_CONTRIBUTION.md*
