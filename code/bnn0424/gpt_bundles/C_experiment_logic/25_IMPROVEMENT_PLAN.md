# bnn0424 改进计划 — 从 C+ 到 A+ 的路线图

> **创建日期**: 2026-04-24
> **目标期刊**: Nature Computational Science
> **当前状态**: 实验基本完成，论文叙事逻辑有结构性缺陷，需要根本性重构
> **预计周期**: 4-6 周（Phase 0-1 紧急，Phase 2-3 可并行）

---

## 评估标准：A+ 论文模板

| 维度 | C+ (当前) | A+ (目标) | 差距描述 |
|------|-----------|-----------|----------|
| **科学创新** | BNN vs DE/GP 的优势未被证明 | 论文的核心贡献不是 BNN 本身，而是"统一概率层"的方法学思想，且有定量证据支撑 | 需要彻底重新定义 contribution |
| **实验严谨性** | Synthetic closed-loop, 4/8 固定, temp R²=0.60 | 每个弱点都有 preemptive defense + 消融实验 | 需要补实验 + 诚实讨论 |
| **叙事逻辑** | 结果罗列 + cherry-picking metrics | 环环相扣的证据链：coupling → Sobol → posterior → coherence | 需要重写主线 |
| **写作质量** | Introduction 有 straw-man，Discussion 平淡 | 每段都有且仅有一个论点，所有 claim 有 evidence | 需要大幅度重写 |
| **参考文献** | 13 篇，缺失关键基础文献 | 40-50 篇，覆盖 UQ/surrogate/BNN/calibration 全领域 | 需要大量补充 |
| **图表** | 功能性但不是 Nature 水平 | 5 张主图讲一个完整故事，每张图有明确论点 | 需要重绘 |
| **工程管理** | 项目副本式管理，文档膨胀 | 单一权威源，版本控制 | 需要重组 |

---

## Phase 0: 工程整顿（1-2 天）

### 0.1 消灭 bnn0424 副本，建立单一权威源

**问题**: bnn0424 是 bnn0414 的字节级副本 + gpt_figures 工作区。两个副本并行存在是版本管理灾难。

**任务**:
- [x] **0.1.1** 决定权威目录：bnn0424 为唯一活跃目录 (2026-04-24)
- [x] **0.1.2** gpt_figures/ 已在 bnn0424 中创建 (2026-04-24)
- [x] **0.1.3** bnn0414 降级为只读 archive（含 960MB fig0_geometry_ref 等大文件）(2026-04-24)
- [x] **0.1.4** CLAUDE.md 已更新路径引用 (2026-04-24)

**验收标准**: 只有一个目录包含活跃代码和论文文件

### 0.2 精简文档体系

**问题**: CANONICAL_DATA_SUMMARY.md、EXPERIMENT_CONCLUSIONS_OVERVIEW.md、phase1_evidence_v4.md、BNN_DECISIONS.md、NCS_REVISION_PLAN.md 有大量重叠。

**任务**:
- [x] **0.2.1** 保留且升级 CANONICAL_DATA_SUMMARY.md 为唯一数字源
- [x] **0.2.2** 本 IMPROVEMENT_PLAN.md 取代 NCS_REVISION_PLAN.md（后者标注为已废弃）
- [x] **0.2.3** phase1_evidence_v4.md 降级为 historical reference，不再更新
- [x] **0.2.4** EXPERIMENT_CONCLUSIONS_OVERVIEW.md 合并入 CANONICAL_DATA_SUMMARY.md 的 caveats 小节

**验收标准**: 不超过 3 个活跃文档：CANONICAL_DATA_SUMMARY.md（数字）、IMPROVEMENT_PLAN.md（计划）、manuscript 文件

---

## Phase 1: 科学叙事重构（1-2 周，最关键）

这是整个改进计划的核心。当前论文最大的问题不是数字不对，而是 **故事讲错了**。

### 1.1 重新定义核心贡献 — "统一概率层" 而非 "BNN 好"

**当前问题**: 论文暗示 BNN > DE/GP，但数据不支持（DE stress R² = 0.9340 ≈ BNN 0.9438）。

**目标叙事**: 本文的贡献不是 BNN 本身的预测精度，而是：
> **一个单一的后验预测分布同时服务于 forward UQ、Sobol 分析和 posterior calibration，三者之间无需重训练或重校准，且产生相互一致的结论。**

这才是 GP/DE/MC-Dropout 做不到的事——不是精度，而是 **coherence**。

**任务**:

- [x] **1.1.1** 写一段 200 字的"核心论点声明"（EN + CN）→ manuscript/CORE_CONTRIBUTION.md (2026-04-24)。例：

  > *EN*: The central contribution is not a more accurate surrogate but a
  > unified probabilistic layer: a single posterior predictive distribution
  > that serves forward propagation, variance-based sensitivity
  > decomposition, and observation-conditioned calibration without
  > retraining between analyses. The coherence this provides — Sobol-
  > identified dominant parameters are precisely the directions along which
  > the posterior contracts — is a structural property that point-estimate
  > surrogates and post-hoc uncertainty wrappers cannot guarantee.
  >
  > *CN*: 本文的核心贡献不在于更精确的代理模型，而在于一个统一的概率层：
  > 同一个后验预测分布无需重训练即可同时服务于前向不确定性传播、基于方差的
  > 敏感性分解和基于观测的后验标定。这种一致性——Sobol 分析识别出的主导参数
  > 恰恰是后验收缩最强的方向——是点估计代理模型和后挂不确定性包装器在结构上
  > 无法保证的性质。

- [x] **1.1.2** Abstract 已替换为 coherence-framed 版本；Introduction 末段已有 honest disclaimer (2026-04-24)

- [x] **1.1.3** Introduction honest disclaimer 已插入 manuscript_en.txt + manuscript_bilingual.txt (2026-04-24)

### 1.2 修正 "coupling damps stress by 30%" 的因果推断

**当前问题**: iteration 1 (decoupled) 是未收敛的 Picard 迭代结果，不是"无耦合"基线。严格来说，你比较的是"收敛 vs 未收敛"而非"coupled vs uncoupled"。

**任务**:

- [x] **1.2.1** Methods "Coupled high-fidelity simulation" 已修正定义 (2026-04-24)。在 Methods Note E 中明确定义：
  - decoupled = single-pass evaluation (first Picard iteration, before any feedback)
  - coupled = converged steady-state (after Picard iteration converges)
  - 必须声明："The 'decoupled' prediction is not a true single-physics
    baseline — it retains the coupled geometry at the initial condition
    — but rather the response before iterative feedback has been applied."

- [x] **1.2.2** Results + Discussion 已修正语言：decoupled→single-pass, coupling reduces→iterative feedback (2026-04-24)

- [x] **1.2.3** Limitation (v) 已添加 (2026-04-24)：
  > "(v) The decoupled baseline is the first Picard iteration rather than
  > a fully uncoupled single-physics solve. The reported coupling effect
  > therefore includes contributions from iterative convergence beyond
  > pure physics feedback."

**验收标准**: 没有审稿人能说 "你在比较苹果和橘子"

### 1.3 正面面对 BNN vs Deep Ensemble 的劣势

**当前问题**: Table 1 用 CRPS 加粗来暗示 BNN 胜出，但 DE 在 stress R² 上稍低 (0.9340 vs 0.9438)，但幅度接近。需要公正呈现。

**任务**:

- [x] **1.3.1** Table 1 caption 已修改为 "Bold: best value per metric" (2026-04-24)。原：
  - R²: bold DE
  - RMSE: bold DE
  - CRPS: bold BNN
  - ECE: bold BNN
  - 加注脚："Best value per metric in bold. The BNN's advantage lies in
    calibration quality (ECE) and distributional accuracy (CRPS), not in
    point prediction."

- [x] **1.3.2** Results 2.1 已增加 BNN vs DE 诚实比较段落 (2026-04-24)。注：实际数据验证后发现 DE stress R²=0.934 (非0.953)，BNN略优。原提议：
  > "The deep ensemble achieves slightly higher stress R² (0.953 vs 0.944,
  > Table 1). However, the deep ensemble produces a distributional output
  > by aggregating five independent point-estimate networks, with no
  > shared posterior over weights. In the downstream analyses (Sections
  > 2.2-2.4), this distinction matters: forward UQ, Sobol decomposition
  > and posterior calibration all operate on the same BNN posterior
  > predictive distribution, whereas applying these analyses to a deep
  > ensemble would require separate ad hoc uncertainty propagation for
  > each task."

- [ ] **1.3.3** 在 SI 中增加一个 "GP baseline" 讨论段落（不需要跑实验，但必须引用文献解释为什么 GP 在 15-output coupled setting 中的 scalability 是个问题）：
  > "Gaussian process surrogates are well-established for Sobol analysis
  > via polynomial chaos expansions [Sudret 2008] and for Bayesian
  > calibration [Kennedy & O'Hagan 2001]. In the present 8-input,
  > 15-output setting, a GP could in principle serve the same role.
  > However, (a) standard GPs scale as O(N³) with training set size,
  > requiring sparse approximations at N = 2339; (b) multi-output GPs
  > that jointly model correlated outputs add substantial complexity
  > [Alvarez et al. 2012]; and (c) incorporating physics-prior
  > monotonicity constraints in a GP requires constrained posterior
  > sampling [Riihimäki & Vehtari 2010], which is more computationally
  > demanding than the auxiliary loss approach used here. We do not
  > claim that BNNs universally outperform GPs; rather, the BNN's
  > gradient-based training and modular loss function made it the more
  > practical choice for this coupled multi-output problem."

- [x] **1.3.4** Discussion 已增加诚实比较段落 (2026-04-24)：
  > "Our comparison shows that the BNN surrogate does not dominate
  > conventional baselines on every metric. Deep ensembles achieve
  > marginally higher point-prediction accuracy on stress (Table 1), and
  > Gaussian processes remain a viable alternative for moderate-
  > dimensional problems. The BNN's value proposition is therefore not
  > predictive superiority but methodological integration: a single
  > posterior predictive distribution eliminates the need to maintain
  > separate uncertainty wrappers for each analysis stage. Whether this
  > integration advantage justifies the additional complexity of
  > variational inference over simpler alternatives is ultimately
  > problem-dependent."

**验收标准**: 审稿人读完之后的感受是 "作者很诚实，清楚自己方法的边界"，而不是 "作者在回避不利数据"

### 1.4 keff R² 的诚实处理

**当前问题**: manuscript_en.txt 中已经有了 keff R² 的防御性叙述（lines 159-165），但还不够透彻。

**任务**:

- [ ] **1.4.1** 在 Table 1 中为 keff 行增加一个注脚：
  > "† k_eff total variance in the dataset is σ ≈ 0.00077 (77 pcm);
  > R² is hypersensitive to residual noise at this scale and is not
  > a meaningful comparison metric. See CRPS for distributional accuracy."

- [ ] **1.4.2** 确认 CRPS 指标确实支持 BNN 优于 DE/MC-D 对 keff 的预测。如果不支持，必须在论文中坦言

- [ ] **1.4.3** 在 SI 中增加一个 keff variance analysis 的小节：
  > 展示 keff 值域 scatter plot，证明其方差极小 → R² 不适用

### 1.5 phy-mono 的定位重塑

**当前问题**: baseline 0% 物理违反 → physics constraint 对正确性无贡献 → 卖点为零。

**正确定位**: phy-mono 的价值不是 "correcting violations"，而是 "pruning non-physical weight-space regions → sharper intervals"。

**任务**:

- [ ] **1.5.1** 从 CANONICAL_DATA_SUMMARY.md 提取以下对比数据：
  - MPIW: phy-mono 39.38 vs baseline 40.21 (stress)
  - CRPS: phy-mono 4.350 vs baseline 4.424
  - 5-seed repeat: phy-mono CRPS std 0.15 vs baseline 0.07 (需要确认)

- [ ] **1.5.2** 从 Table B1b 提取小样本优势：
  - 20% data: phy-mono stress R² = 0.937 vs baseline 0.928 (+0.009)
  - 20% data: phy-mono wall2 R² = 0.991 vs baseline 0.986 (+0.005)

- [x] **1.5.3** Results 2.1 已替换为 posterior-pruning 段落 (2026-04-24)：
  > "Both the reference and physics-regularized surrogates achieve zero
  > monotonicity violations on the test set for all high-confidence
  > physical pairs (Table S8). The value of the physics prior is therefore
  > not error correction but posterior pruning: constraining the weight
  > space to regions consistent with known constitutive monotonicity
  > relationships tightens the stress prediction interval from 40.2 MPa
  > (reference) to 39.4 MPa (physics-regularized) without degrading
  > coverage, and yields a modest CRPS improvement (4.35 vs 4.42). At
  > reduced training size (20% of data), the physics prior provides a
  > more pronounced advantage (stress R² 0.937 vs 0.928; Table B1b),
  > suggesting that the inductive bias is most valuable in the low-data
  > regime."

- [x] **1.5.4** Discussion 已修正为 pruning framing (2026-04-24)

### 1.6 后验覆盖率的诚实讨论

**当前问题**: 90%-CI coverage = 0.861 (10/72 missed)，low-stress coverage = 0.708。论文轻描淡写。

**任务**:

- [ ] **1.6.1** 在 Results 2.4 中增加分层覆盖率报告：
  > "Coverage varies across stress categories: high-stress cases achieve
  > 0.917 and near-threshold cases 0.958, but low-stress cases show only
  > 0.708 coverage (Table S5). The shortfall in low-stress cases arises
  > primarily from the alpha_slope parameter, which has the weakest Sobol
  > sensitivity and is therefore least constrained by the five observed
  > outputs."

- [ ] **1.6.2** 分析 low-stress 覆盖率低的根本原因：
  - 是 BNN 在 low-stress region 精度差？
  - 是 MCMC proposal 在 low-stress region 探索不足？
  - 是 4-parameter subset 不够？
  - 把原因写入 Discussion / Limitations

- [ ] **1.6.3** 在 Limitations 中增加一条关于 coverage 的讨论

**验收标准**: 审稿人看到 0.708 时不会觉得你在隐瞒

### 1.7 "Synthetic observations" 的闭环问题

**当前问题**: 用 HF solver 生成观测 → 用 HF solver 数据训练的 BNN 做 posterior → 验证当然好。

**任务**:

- [ ] **1.7.1** 在 Methods "Posterior calibration" 末尾增加一段明确声明：
  > "Because both the training data and the benchmark observations are
  > generated by the same coupled solver, the calibration exercise
  > operates within a closed computational loop. The posterior coverage
  > and contraction reported here characterise the surrogate's ability
  > to recover parameters within this self-consistent setting. Performance
  > on real experimental data — which may include model-form error,
  > unmodelled physics and measurement systematics absent from the
  > synthetic noise — could differ and remains an open question."

- [ ] **1.7.2** 在 Discussion Limitations 中将此提升为与 (iii) 同等重要的限制，而非脚注式处理

- [ ] **1.7.3** 考虑是否可以做一个 "model misspecification" sensitivity test（optional but strong）：
  - 用 subset of training data 训练 BNN
  - 用 held-out data (不在训练集中) 作为 "observations"
  - 看 posterior coverage 是否下降
  - 如果能做，这将极大增强论文的可信度

### 1.8 Sobol 分析的 surrogate error 传播

**当前问题**: temp R² = 0.60 → 40% unexplained variance → Sobol 指数可能被 surrogate error 污染。

**任务**:

- [x] **1.8.1** Sobol robustness 数据已整理 (revision_1_8_sobol_robustness.md)；Results 中已添加一句话引用 (2026-04-24)。原任务：
  - Cross-model comparison（已有：3 个 BNN 变体的 S₁ 基本一致）
  - 但必须增加：与 Spearman/PRCC 对比验证（你已经有 spearman_results.csv）
  - 核心论点："The dominant-factor rankings are consistent across three
    independent BNN variants and are corroborated by nonparametric
    rank-based methods (Supplementary Table X), suggesting that the
    Sobol rankings reflect genuine parametric sensitivity rather than
    surrogate-specific artefacts."

- [ ] **1.8.2** 明确承认 temperature 输出的 Sobol 可信度较低：
  > "For temperature outputs, where the surrogate R² is lower (~0.60),
  > the Sobol indices should be interpreted with more caution; the
  > first-order rankings are corroborated by rank-based methods but
  > the precise index values carry greater uncertainty."

- [ ] **1.8.3** 考虑在 SI 中增加一个 "surrogate error propagation to
  Sobol indices" 的 analytical bound（optional，但对 A+ 很有价值）：
  - 参考 Marrel et al. (2009) "Calculations of Sobol indices for the
    Gaussian process metamodel"
  - 或简单方法：compare Sobol from 5 different random seeds of BNN training

**验收标准**: 审稿人不能问 "你怎么知道 Sobol 结果不是 surrogate error 的 artifact？"

---

## Phase 2: 写作重构（1-2 周，与 Phase 1 部分并行）

### 2.1 Title 重写

**当前**: "A framework for uncertainty analysis reveals coupling effects in multiphysics reactor models"

**问题**: 太模糊，没有信息量。

**候选方案** (选一个或组合):

- (a) "A unified Bayesian surrogate layer reveals how multi-physics coupling reshapes uncertainty in microreactor design"
- (b) "Coupling damps stress uncertainty by 30%: a Bayesian surrogate framework for multi-physics reactor analysis"
- (c) "Forward propagation, sensitivity and calibration from a single posterior: uncertainty analysis of a coupled microreactor model"

**任务**:
- [ ] **2.1.1** 在合著者之间讨论 3 个候选标题
- [ ] **2.1.2** 最终标题必须满足：(1) 包含核心发现或方法；(2) ≤ 20 词；(3) 不含 "framework" 这种空洞词

### 2.2 Abstract 重构

**当前问题**: 试图包含所有结果，每个只有一个数字，无上下文。

**A+ 模板**: Abstract 应该讲一个三段式故事：
1. **问题** (2-3 句): 耦合多物理系统的 UQ 需要 forward、sensitivity、calibration 三者一致，现有方法做不到
2. **方法 + 发现** (4-5 句): BNN 统一概率层 → 发现 coupling 显著改变不确定性结构 → Sobol 揭示参数分离 → posterior 沿 Sobol 方向收缩 → 这种一致性是结构性的
3. **意义** (1-2 句): 方法可迁移 + 10⁵ 加速

**任务**:
- [x] **2.2.1** Abstract 已重写（Problem→Method+Findings→Significance 结构），196 词 (2026-04-24)
- [ ] **2.2.2** 删除 abstract 中的所有单独数字（0.861、0.58 等），只保留最关键的 1-2 个（30% coupling damping、10⁵ speedup）
- [ ] **2.2.3** Abstract 最后一句不要是 limitation caveat（"conditional on..."），要是 implication

### 2.3 Introduction 重写

**当前结构**: 微堆介绍 → HF solver 存在 → 现有方法不够 → 我们用 BNN

**问题**: 
1. 对 GP/PCE 的批评站不住脚（8D 不是高维）
2. 对 DE 的批评不准确（DE 可以做 calibration）
3. 缺失关键参考文献

**A+ 结构**:
1. **耦合多物理系统的 UQ 挑战**（2 段）
   - 微堆的耦合特性
   - 为什么需要 forward + sensitivity + calibration 三合一
2. **现有方法的局限**（1-2 段）—— 诚实、具体、有引用
   - GP/PCE: 能做单任务 UQ，但多输出耦合 + 物理约束集成更复杂 [引 Sudret, Kennedy-O'Hagan]
   - PINN: 需要 closed-form PDE，不适用于 iterative coupling [引 Raissi, Karniadakis]
   - DE/MC-Dropout: 可以做 forward UQ，但没有 shared posterior [引 Lakshminarayanan]
   - **关键**: 不是说这些方法"不行"，而是说"没有天然提供三者一致的概率层"
3. **本文定位**（1 段）
   - 前期工作的边界声明
   - 本文做什么、不做什么
4. **贡献总结**（1 段，3-4 bullet）

**任务**:
- [ ] **2.3.1** 修正 GP/PCE 叙述，删除 "dimensionality constraints" 的说法，改为：
  > "GP and PCE surrogates can serve as the basis for individual UQ tasks,
  > and indeed Sudret (2008) demonstrated PCE-based Sobol analysis as a
  > mature technique. However, extending these to a joint multi-output
  > setting with heteroscedastic uncertainty and physics-prior constraints
  > requires substantially more complex formulations [Alvarez et al. 2012,
  > Riihimäki & Vehtari 2010]."

- [ ] **2.3.2** 修正 DE 叙述，不能说 DE "lack posterior"：
  > "Deep ensembles [Lakshminarayanan et al. 2017] provide calibrated
  > distributional predictions and can be used for forward uncertainty
  > propagation. However, they yield a mixture distribution rather than
  > a posterior over model parameters, so using them for observation-
  > conditioned calibration requires additional machinery (e.g. ABC or
  > likelihood-free inference), introducing a second modelling layer
  > not inherent in the ensemble itself."

- [ ] **2.3.3** 增加 ~25 篇参考文献（详见 2.8 任务）

### 2.4 Results 重构

**当前结构**: 
- 2.1 Surrogate calibration（精度对比）
- 2.2 Coupling reshapes uncertainty（forward UQ）
- 2.3 Sensitivity patterns（Sobol）
- 2.4 Posterior contraction（MCMC）

**问题**: 各小节独立，看不出证据链。

**A+ 结构**: 保持同样的 4 小节，但每节末尾增加 1 句 transition 连接到下一节：

- [x] **2.4.1** 2.1 → 2.2 transition (2026-04-24): "Having established that the BNN
  posterior predictive captures the coupled response with adequate
  accuracy, we next propagate the full input uncertainty through this
  distribution to characterise the output uncertainty structure."

- [x] **2.4.2** 2.2 → 2.3 transition (2026-04-24): "The coupling-reshaped distributions
  raise a natural question: which input parameters drive the observed
  variability in each output, and do stress and k_eff share the same
  dominant drivers?"

- [x] **2.4.3** 2.3 → 2.4 transition (2026-04-24): "The separation of dominant
  parameters for stress (E_intercept) and k_eff (alpha_base) creates a
  natural multi-observable calibration design: stress observations
  constrain stiffness-related parameters while k_eff observations
  constrain expansion-related parameters, with minimal redundancy."

- [x] **2.4.4** Posterior 末尾 coherence 论点已添加 (2026-04-24)：
  > "The posterior contracts most strongly along the same parameter
  > directions that the Sobol analysis identified as dominant. This
  > alignment is not guaranteed — it emerges because forward propagation,
  > sensitivity decomposition and posterior calibration share the same
  > underlying posterior predictive distribution."

### 2.5 Discussion 重构

**当前问题**: Discussion 只有 4 段 + Limitations。缺少方法论意义的讨论。

**A+ 结构**:

1. **Coupling 改变了什么**（保持当前内容，修正因果推断语言）
2. **参数信息通道分离 → 多观测量标定** (新增)
   - Sobol 揭示 stress 和 keff 信息通道分离
   - 这不是锦上添花——它意味着 single-output calibration 会 miss cross-coupling
   - 工程含义：实验设计应该 target 不同参数通道
3. **为什么"统一概率层"重要** (新增)
   - 现有 pipeline：分别构建 forward UQ surrogate、sensitivity surrogate、calibration model → 不一致
   - BNN 统一层：三个分析自动一致 → Sobol-posterior coherence 是这个一致性的 empirical evidence
   - 诚实比较：DE/GP 也能做，但需要额外工程；BNN 的优势是结构性的简洁
4. **Speed 和实用性**（保持，精简）
5. **Limitations**（扩展，增加 1.2、1.6、1.7 的内容）
6. **Outlook / Future work**（新增 1 段）
   - Transient 扩展
   - Real experimental data
   - Higher-dimensional input space

**任务**:
- [ ] **2.5.1** 写 Discussion 段落 2（参数信息通道）
- [ ] **2.5.2** 写 Discussion 段落 3（统一概率层）
- [ ] **2.5.3** 扩展 Limitations 段落（增加 3 条新 limitation）
- [ ] **2.5.4** 写 Outlook 段落（3-4 句）

### 2.6 Methods 补全

**当前问题**: Methods 太薄，NCS 审稿人不能独立复现。

**任务**:
- [ ] **2.6.1** 增加 "Why these 8 parameters" 段落：
  - 为什么选这 8 个？为什么 ±10% 范围？
  - 燃料导热系数、热管参数为什么固定？
  - 引用 Note E 的内容到 Methods 中（至少摘要级别）

- [ ] **2.6.2** 增加 BNN architecture 的关键数字到 Methods：
  - 目前 Methods 只说 "hyperparameters optimised via Optuna"
  - 至少需要：width, depth, prior sigma 的 optimal value
  - 或 "The optimal architecture (width 254, depth 2) and remaining
    hyperparameters are in Supplementary Table S2"

- [ ] **2.6.3** MCMC Methods 增加 proposal scale 信息：
  - 目前只说 "4 independent chains, 8000 iterations"
  - 需要增加：proposal scale 如何确定、acceptance rate target

- [ ] **2.6.4** 确保 Methods 的独立可复现性：
  - 一个新读者只看 Methods + SI，不看 Results/Discussion
  - 能否复现整个实验？如果不能，缺什么？

### 2.7 Supplementary Information 修缮

**任务**:
- [ ] **2.7.1** 补充 "[TO GENERATE]" 标记的 figure：
  - Fig. S2: "expand to all 15 outputs" — 必须生成
  - Fig. S4: "TO GENERATE from training logs" — 必须生成或移除引用

- [ ] **2.7.2** 检查 S8 Fig. S8 中引用的 "approximately 28%" → 应更新为 30%

- [ ] **2.7.3** 确保 SI 中所有 Table/Figure 都有 manuscript 中的交叉引用

- [ ] **2.7.4** 增加 Sobol robustness analysis（来自 1.8.1）

- [ ] **2.7.5** 增加 GP/DE 不适用的详细讨论（来自 1.3.3）

### 2.8 参考文献补全

**当前**: 13 篇。**目标**: 40-50 篇。

**必须添加的核心文献** (按紧急度排序):

| # | 引用 | 用途 | 位置 |
|---|------|------|------|
| 1 | Kennedy & O'Hagan (2001) JRSS-B | 贝叶斯标定奠基 | Intro + Methods |
| 2 | Sudret (2008) Rel Eng Sys Safety | PCE-Sobol | Intro |
| 3 | Raissi et al. (2019) J Comp Phys | PINN | Intro |
| 4 | Karniadakis et al. (2021) Nat Rev Phys | PINN review | Intro |
| 5 | Lakshminarayanan et al. (2017) NeurIPS | Deep Ensemble | Intro + Results |
| 6 | Gal & Ghahramani (2016) ICML | MC-Dropout 理论 | Intro |
| 7 | Graves (2011) NeurIPS | 变分推断 BNN | Methods |
| 8 | Sobol' (2001) Math Comp Sim | Sobol 指数定义 | Methods |
| 9 | Saltelli et al. (2010) Comp Phys Comm | Saltelli 采样 | Methods |
| 10 | Vehtari et al. (2021) Bayesian Analysis | Rank R-hat | Methods |
| 11 | Gelman & Rubin (1992) Stat Sci | R-hat 原始 | Methods |
| 12 | Alvarez et al. (2012) Found & Trends ML | Multi-output GP | Intro/Discussion |
| 13 | Riihimäki & Vehtari (2010) JMLR | Monotone GP | Discussion |
| 14 | Marrel et al. (2009) Rel Eng Sys Safety | GP-Sobol | SI |
| 15 | Robert & Casella (2004) Monte Carlo Statistical Methods | MCMC textbook | Methods |
| 16-25 | 领域内 HPR/microreactor 文献 | 补充 [1]-[9] | Intro |
| 26-35 | BNN 应用文献 (nuclear/engineering UQ) | 相关工作 | Intro |
| 36-45 | Sobol/sensitivity 应用文献 | 方法对比 | Methods/Discussion |

**任务**:
- [ ] **2.8.1** 编译完整参考文献清单，每篇标注用途和插入位置
- [ ] **2.8.2** 对每篇新增引用，确认论文中有对应的引用语句
- [ ] **2.8.3** 所有参考文献格式统一为 NCS style

---

## Phase 3: 实验补强（1-2 周，与 Phase 2 并行）

这些是可选但对 A+ 很有价值的补充实验。

### 3.1 Sobol 稳健性验证

**目标**: 证明 Sobol 结果不是 surrogate artifact

**任务**:
- [ ] **3.1.1** 从 spearman_results.csv 提取 Spearman/PRCC 排序，与 Sobol S₁ 排序对比
- [ ] **3.1.2** 整理成 SI Table：
  > "Method | Stress rank-1 | Stress rank-2 | keff rank-1 | keff rank-2"
  > "Sobol  | E_intercept   | alpha_base    | alpha_base  | alpha_slope"
  > "Spearman| ...          | ...           | ...         | ...        "

- [ ] **3.1.3** 如果 3 个方法排序一致，写一句话："The dominant-factor rankings
  are robust to the choice of sensitivity method (Supplementary Table X)."

### 3.2 Temperature R² 低的原因分析

**目标**: 为什么 fuel_temp / monolith_temp R² 只有 0.60？是数据问题还是模型问题？

**任务**:
- [ ] **3.2.1** 检查训练数据中 temperature 的分布——是否方差极小（类似 keff）？
- [ ] **3.2.2** 检查 residual plot——是否有系统性 pattern（非线性未捕获）？
- [ ] **3.2.3** 如果发现原因，写入 SI 的一个段落
- [ ] **3.2.4** 如果 temperature 的 variation 确实很小 → 用与 keff 相同的论点辩护（R² not informative for near-constant outputs, pivot to MAE/CRPS）

### 3.3 Low-stress 覆盖率低的根因分析

**任务**:
- [ ] **3.3.1** 从 benchmark_summary_4chain.csv 提取 low-stress cases (0-5) 的详细诊断
- [ ] **3.3.2** 检查是哪个参数 miss coverage 最多（大概率是 alpha_slope，已在 SI 中暗示）
- [ ] **3.3.3** 检查 BNN 在 low-stress region 的 parity plot 残差是否系统偏大
- [ ] **3.3.4** 写入 Results 2.4 和 Discussion

### 3.4 Cross-validation Sobol（Optional，高价值）

**目标**: 用 5 个不同 seed 的 BNN 分别做 Sobol → 展示 S₁ 的 surrogate-induced uncertainty

**任务**:
- [ ] **3.4.1** 如果 repeat_eval 的 5 个 seed checkpoint 还在 → 对每个 seed 跑一次 simplified Sobol (N_base=2048, 10 reps)
- [ ] **3.4.2** 报告 S₁ 的 cross-model mean ± std
- [ ] **3.4.3** 这直接回答 "Sobol results reflect genuine sensitivity vs surrogate noise"

---

## Phase 4: 图表升级（1 周，与 Phase 2 后半段并行）

### 4.1 Figure 1: Workflow 重绘

**当前**: 工程流程图风格
**目标**: 方法论图，BNN 后验预测分布在视觉中心

**任务**:
- [ ] **4.1.1** 设计新布局：
  ```
  [8 inputs] → [OpenMC-FEniCS data] → [BNN training]
                                            ↓
                               [Posterior Predictive Distribution]
                              ╱           |             ╲
                    Forward UQ    Sobol decomposition    Posterior calibration
                              ╲           |             ╱
                               [Coherent evidence chain]
  ```
- [ ] **4.1.2** 中央突出 "single distribution" 的概念
- [ ] **4.1.3** 三个下游分析用相同视觉权重，但有箭头互连（表示一致性）

### 4.2 Table 1: 公正呈现

**任务**:
- [ ] **4.2.1** 所有 metrics 都标注 best（R², RMSE, CRPS, ECE）
- [ ] **4.2.2** 增加 keff 的注脚说明 R² 不适用
- [ ] **4.2.3** 分两个 panel：(a) point prediction (R², RMSE), (b) distributional quality (CRPS, ECE, PICP)
  - 让读者看到 BNN 在 (a) 中与 DE competitive 但不 superior，在 (b) 中明显更好

### 4.3 Figure 5 (Posterior): 重构为"证据一致性"图

**当前**: 独立展示 prior/posterior、predictive、coverage
**目标**: 展示 Sobol → Posterior coherence

**任务**:
- [ ] **4.3.1** Panel A: Sobol 指数（简化版），标注 E_intercept 和 alpha_base
- [ ] **4.3.2** Panel B: 对应参数的 prior → posterior 收缩
- [ ] **4.3.3** Panel C: 后验预测 vs 真值
- [ ] **4.3.4** 视觉连接 A → B：用颜色编码 "Sobol dominant parameter = strongest contraction"

### 4.4 所有图表的通用标准

**任务**:
- [ ] **4.4.1** 检查所有图表无 CJK 字符（包括 gpt_figures/ 中的 "gpt样板图.png"）
- [ ] **4.4.2** 字体统一：axis labels ≥ 8pt，不使用 matplotlib 默认字体
- [ ] **4.4.3** 颜色方案：colorblind-friendly（不能只靠红/绿区分）
- [ ] **4.4.4** 所有图导出为 300 dpi PNG + vector PDF
- [ ] **4.4.5** 每张图一个明确论点，写在 caption 第一句

---

## Phase 5: 终审与投稿准备（3-5 天）

### 5.1 数字一致性全局扫描

**任务**:
- [ ] **5.1.1** 对 CANONICAL_DATA_SUMMARY.md 中的每个数字，grep manuscript 文件确认一致
- [ ] **5.1.2** 特别关注：
  - acceptance rate: 统一为 0.58-0.63 (mean 0.606)
  - coupling damping: 统一为 "approximately 30% (std reduction)"
  - speedup: 统一为 1.43×10⁵ (single-MC) 或 1.37×10⁸ (batched)，每次都说明是哪个
  - coverage: 0.861 (62/72)
- [ ] **5.1.3** Retired numbers check: 确保论文中没有出现 CANONICAL_DATA_SUMMARY.md §13 的任何已退役数值

### 5.2 审稿人模拟攻击

**任务**:
- [ ] **5.2.1** 模拟 3 位审稿人的严厉 review：
  - Reviewer 1 (ML/UQ specialist): BNN vs GP/DE; Optuna 40 trials; MFVI quality
  - Reviewer 2 (Nuclear engineer): Picard decoupled definition; 8 parameters reasonable?; real data?
  - Reviewer 3 (Statistics): Coverage 0.861; 4/8 params fixed; MCMC diagnostics sufficient?
- [ ] **5.2.2** 对每个可能的 concern，确保论文中已有 preemptive defense 或 honest limitation

### 5.3 格式与排版

**任务**:
- [ ] **5.3.1** NCS word limit check (~3000 words Results + Discussion, ~1500 Methods)
- [ ] **5.3.2** 参考文献格式统一
- [ ] **5.3.3** 作者贡献声明更新（如有变化）
- [ ] **5.3.4** Data/Code availability 完善（GitHub repo URL 占位）
- [ ] **5.3.5** Cover letter 草稿

### 5.4 最终审读

**任务**:
- [ ] **5.4.1** 通读全文，检查逻辑链是否连贯
- [ ] **5.4.2** 检查每个 claim 是否有 evidence 支撑（表/图/SI reference）
- [ ] **5.4.3** 检查所有 "[NOTE: verify...]" 标记是否已处理（当前 manuscript 中有 2 个）
- [ ] **5.4.4** 拼写和语法全文检查

---

## 执行时间线

```
Week 1:  Phase 0 (1-2 days) + Phase 1.1-1.4 (核心叙事)
Week 2:  Phase 1.5-1.8 + Phase 2.1-2.4 (写作重构开始)
Week 3:  Phase 2.5-2.8 + Phase 3.1-3.3 (Discussion + 补充实验)
Week 4:  Phase 4 (图表) + Phase 3.4 (optional)
Week 5:  Phase 5 (终审)
Week 6:  Buffer + 合著者审读 + 修改
```

---

## 优先级总结

| 优先级 | 任务 | 理由 |
|--------|------|------|
| **P0-紧急** | 1.1 核心贡献重定义 | 不做这个，其他都白做 |
| **P0-紧急** | 1.3 BNN vs DE 诚实处理 | 审稿人第一个攻击点 |
| **P0-紧急** | 2.3 Introduction 重写 | Straw-man 会导致直接 reject |
| **P1-重要** | 1.2 coupling 因果推断 | 科学严谨性 |
| **P1-重要** | 1.5 phy-mono 定位重塑 | 方法贡献的 justification |
| **P1-重要** | 1.6 coverage 诚实讨论 | 避免被审稿人认为在隐瞒 |
| **P1-重要** | 2.4-2.5 Results+Discussion 重构 | 叙事连贯性 |
| **P1-重要** | 2.8 参考文献补全 | NCS 基本门槛 |
| **P2-有价值** | 1.7 closed-loop 声明 | 增强可信度 |
| **P2-有价值** | 1.8 Sobol robustness | 防御性实验 |
| **P2-有价值** | 3.1-3.4 补充实验 | A vs A+ 的区别 |
| **P3-打磨** | 0.1-0.2 工程整顿 | 提高效率 |
| **P3-打磨** | 4.x 图表升级 | 视觉印象 |
| **P3-打磨** | 5.x 终审 | 投稿门槛 |

---

## Checklist: A+ 论文的必要条件

每条必须在投稿前 check off：

- [ ] 核心贡献不是 "BNN 更准"，而是 "统一概率层提供 coherent 三阶段分析"
- [ ] Table 1 公正地展示 BNN 和 DE 各自的优劣
- [ ] Introduction 不包含任何 straw-man argument
- [ ] "coupling damps 30%" 有精确的操作定义（decoupled = first Picard iteration）
- [ ] phy-mono 的卖点是 interval sharpening，不是 violation prevention
- [ ] keff R² 有注脚解释为什么 misleading + CRPS 支撑
- [ ] 后验 coverage 0.861 有分层报告（low/near/high）和原因分析
- [ ] Synthetic observations 的闭环性质有明确声明
- [ ] Sobol 结果有 cross-method (Spearman/PRCC) 验证
- [ ] Temperature R² = 0.60 有原因讨论
- [ ] Results 四节之间有 transition 构成证据链
- [ ] Discussion 有"统一概率层为什么重要"的方法论段落
- [ ] Limitations 至少 6 条（当前 4 条 + 新增 2-3 条）
- [ ] 参考文献 ≥ 40 篇，包含所有必引经典
- [ ] 所有图表无 CJK 字符
- [ ] 所有数字与 CANONICAL_DATA_SUMMARY.md 一致
- [ ] 所有 "[NOTE: verify...]" 已处理
- [ ] 每张主图有一个明确论点
- [ ] Methods 独立可复现
- [ ] Cover letter 草稿就绪

---

*此文档取代 NCS_REVISION_PLAN.md。后者应标注为 `DEPRECATED — see IMPROVEMENT_PLAN.md`。*
