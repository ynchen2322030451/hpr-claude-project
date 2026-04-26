# Gemini 独立审查意见 — 落实核查清单

Date: 2026-04-19
Source: Gemini 独立项目审查 + GPT 交叉评议 + Claude 独立核实
Status: **AUDIT ONLY — 逐项核查后标记，未核查项不执行**

---

## 核查原则

每一条 Gemini 意见，按以下维度标记：

| 标记 | 含义 |
|------|------|
| `[VALID]` | 意见正确，当前稿件确实存在该问题 |
| `[PARTIAL]` | 意见方向正确，但程度或细节有偏差 |
| `[ALREADY]` | 当前稿件已处理或已部分处理 |
| `[OVERCLAIM]` | Gemini 的批评本身过度或不准确 |
| `[ACTION]` | 需要具体执行的改动 |
| `[DEFER]` | 有价值但非投稿前必须 |

---

## I. 立意拔高：从"核工程应用"跃升为"计算科学范式"

### Gemini 原文要点
> 将核心痛点抽象为"在计算成本极高的强耦合多物理场系统中，如何用单一代理模型同时保证三类分析的一致性"。反应堆只是验证平台（Testbed）。

### 核查

**`[PARTIAL]`** 方向有道理，但需要权衡。

- **当前稿件状态**：Introduction 第1–3段已经从 general coupled multi-physics 出发（L94–165），只在第4段落到 HPR 具体问题。Title 已含 "Coupled Multi-Physics Reactor Analysis" 而非纯 HPR。Abstract 也先说 BNN surrogate 方法再说 HPR 应用。
- **Gemini 过度之处**：要求稿件论证对"气候建模、CFD、生物医学"的启发是不切实际的——NCS 也发过大量 domain-specific 的计算科学论文（如材料、蛋白质折叠），不要求每篇都做 cross-domain 泛化。
- **合理内核**：Discussion 可以更明确地说"this workflow is not reactor-specific"——这句话在 Limitations 3.5 (L516–518) 已有，但可以更突出。

#### `[ACTION]` 需要做的
- [ ] **Discussion 末段或 Conclusion**：强化一句 "the workflow generalises to any coupled multi-physics system for which a BNN surrogate can be trained"（当前 L918-920 已有，保留即可，但考虑在 Discussion 3.3 也呼应一次）
- [ ] **Introduction 第3段**：检查 "dimensionality constraints" (L140) 的措辞是否 overclaim（见下条 §II）

#### 不需要做的
- 不需要把摘要/引言改成纯方法论导向而淡化 HPR
- 不需要举其他领域的应用例子

---

## II. 基线对比：GP/PCE 8维不是维度灾难

### Gemini 原文要点
> 8维对稀疏PCE或现代GP完全是舒适区。不要说 GP/PCE 遇到维度灾难。应改为：多输出联合分布、异方差噪声、物理单调性注入才是 BNN 的真正优势。

### 核查

**`[VALID]`** 这是当前稿件中最危险的 overclaim 之一。

- **当前稿件 L140-141**："Gaussian-process and polynomial-chaos surrogates face dimensionality constraints in nonlinear coupled settings"
- **问题**：8维 + 3418样本，对现代 GP (SGPR, DKL) 和稀疏 PCE 完全可行。这句话在 NCS 会被传统 UQ 审稿人（Sudret、Le Gratiet 学派）直接反驳。
- **正确的 BNN 优势定位**：(1) 15输出联合异方差分布；(2) 单调性约束自然注入；(3) 同一 posterior predictive 支撑三类分析无需重训

#### `[ACTION]` 必须修改
- [ ] **L140-141 重写**：删除"dimensionality constraints"说法，改为聚焦 BNN 的真正优势：
  - GP 处理 15 输出异方差联合分布需要复杂的多输出协方差结构
  - PCE 难以施加物理单调性约束
  - 两者都不能自然产生一个同时适用于 forward UQ / Sobol / MCMC 的 posterior predictive distribution
- [ ] **补充引用 Sudret (2008)**：作为 PCE/GP 在全局敏感性中的经典坐标，必须引用并定位自身

---

## III. "Physics-regularized" 命名风险

### Gemini 原文要点
> 所谓物理只是单调性偏导约束，不是 PDE 残差嵌入。称 "Physics-regularized" 有蹭 PINN 嫌疑。建议用 "Physics-Prior Constrained" 或 "Constitutive-Law-Informed"。

### 核查

**`[PARTIAL]`** 命名确实需要精确化，但当前稿件已有部分防御。

- **当前稿件状态**：
  - L141-142 已明确说 "physics-informed neural networks require a closed residual form that iterative solver exchange does not supply"——这已经主动与 PINN 划了界
  - L384 用的是 "Physics-prior monotonicity constraints"，不是 "Physics-regularized BNN"
  - L772 也是 "Physics-prior monotonicity constraints"
  - 但模型 ID "phy-mono" 在代码中使用（不进正文即可）

- **Gemini 过度之处**：稿件实际上已经用 "physics-prior" 而非 "physics-regularized"。Gemini 可能基于旧版或 plan 中的措辞批评。

#### `[ACTION]` 需要核查并加固
- [ ] **全文搜索**：确认正文中无 "physics-regularized" 或 "physics-informed BNN" 等容易混淆的措辞
- [ ] **Methods 4.3 末段**：加一句明确区分——"These constraints derive from constitutive-law monotonicity priors, not from PDE residual minimisation as in physics-informed neural networks (PINNs)"
- [ ] **补充引用 Raissi et al. (2019) + Karniadakis et al. (2021)**：在 Introduction 中引用，然后在同一句中划界

---

## IV. 数据获取成本 / Active Learning 缺位

### Gemini 原文要点
> 2900次耦合运行 × 2266s ≈ 76天单核CPU时间。代理的整体经济性（ROI）还有那么高吗？必须在 Discussion 中构建防御。

### 核查

**`[VALID]`** 当前稿件确实没有正面讨论离线数据生成成本。

- **当前稿件状态**：
  - 3.4 只讨论了推断加速比，没有讨论训练数据生成成本
  - Limitations 3.5 没有提及数据成本
  - MODEL_UPGRADE_PLAN.md 已决定不做 Active Learning

- **防御逻辑**：
  - 2900 样本 × ~2300s ≈ 6.7M s ≈ 77天单核。但实际是集群并行，wall-clock 远低于此
  - 关键论点：这些样本的成本被**分摊到三类分析**（forward UQ 20,000 samples + Sobol 50×40,960 evaluations + MCMC 18×4×8000 chains）——如果每类分析各自生成训练数据，总 HF 调用量远超 2900
  - Active Learning 是 future work

#### `[ACTION]` 需要在 Discussion 或 Limitations 补充
- [ ] **Limitations 3.5 新增一段（或 Discussion 3.4 末尾）**：
  - 坦诚离线数据生成成本 (~3400 coupled HF solves)
  - 论证统一框架的 ROI：单次训练成本分摊到三类下游分析
  - 若三类分析各自建代理，总 HF 调用量更高
  - Active learning / sequential design 列为 future work
- [ ] **计算具体数字**：3418 × 2266s = 7.7M s ≈ 89 天单核；但框架下游使用 > 2.2M surrogate evaluations (Sobol alone ~2M)，等效 HF 成本 ~5×10⁹ s

---

## V. k_eff R² 反常（与 external baseline 交叉）

### Gemini 原文要点
> MC-Dropout/DE 在 k_eff R² 上高于 BNN (0.86 vs 0.63)。审稿人一定会揪住。

### 核查

**`[VALID]`** 这是当前稿件最大的 narrative vulnerability。NCS_REVISION_PLAN 已标为 Gap 3。

- **数据现状**（from `external_baseline_scoring.csv`）：
  - MC-Dropout keff R² = 0.856
  - Deep Ensemble keff R² = 0.828
  - BNN (phy-mono) keff R² ≈ 0.845（from Appendix B2 table: 0.8445）
  - **实际差距没有想象中大**：BNN 0.845 vs MC-Dropout 0.856，差 0.011
  - NCS_REVISION_PLAN 中说 "BNN ~0.63" 可能引用的是旧数据或不同评估条件

#### `[ACTION]` 需要核实并防御

- [ ] **紧急核实**：BNN keff R² 到底是 0.845 (B2 table) 还是 0.63 (revision plan)？
  - 检查 `results/accuracy/` 中 BNN 主模型的 keff R²
  - 如果是 0.845 vs 0.856，差距很小，防御策略不同
  - 如果确实是 ~0.63，则需要 NCS_REVISION_PLAN 中标出的强防御
- [ ] **正文 2.1 或 Discussion**：主动说明 keff 变异范围极窄（σ ≈ 0.0007 = 几十 pcm），R² 对此类近常数输出不是有意义的精度指标
- [ ] **转向 CRPS/NLL 比较**：在这些分布质量指标上 BNN 是否有优势？核实数据

---

## VI. OOD 区域物理约束是否保持

### Gemini 原文要点
> 在 OOD 区域，模型的单调性物理约束是否依然保持？建议在附录补一句。

### 核查

**`[VALID]`** 当前稿件没有回答这个问题。

- **当前状态**：Limitations 3.5 (L538-548) 只说了 OOD 精度退化，没说物理约束是否保持
- **数据是否存在**：需要检查 `results/ood/` 或 `results/physics_consistency/` 中是否有 OOD 子集的 monotonicity violation rate

#### `[ACTION]`
- [ ] **检查现有数据**：OOD 子集的 monotonicity violation rate 是否已计算？
  - 如已有：在 Appendix A (OOD) 中加一句
  - 如未有：在 Limitations 中加一句定性说明 "monotonicity constraints are enforced as a soft penalty during training; their empirical satisfaction on OOD subsets is reported in Appendix A"

---

## VII. 数值对齐问题（GPT + Claude 共同标出，Gemini 未提）

### 核查

**`[VALID]`** 当前稿件存在三处数值不一致，必须统一。

#### 问题 1: Coupling damping percentage
| 位置 | 当前值 |
|------|--------|
| Abstract EN (L72) | "≈ 30%" |
| Abstract CN (L83) | "约 30%" |
| Intro summary EN (L172) | "≈ 28%" |
| Intro summary CN (L181) | "约 28%" |
| Results 2.2 EN (L230) | "≈ 30%" |
| Discussion 3.1 EN (L353) | "≈ 30%" |
| Conclusion EN (L902) | "≈ 28%" |

- **实际计算**：(45.6 - 31.9) / 45.6 = 30.0%（标准差降幅）
- **决策**：统一为 "≈ 30%"

#### `[ACTION]`
- [ ] L172, L181, L902, L926：将 "28%" 改为 "30%"

#### 问题 2: 90%-CI coverage
| 位置 | 当前值 |
|------|--------|
| Abstract (L75) | 0.875 |
| Results 2.4 (L317) | 0.861 |
| Conclusion (L908) | 0.917 |

- **需要核实**：哪个是 canonical？检查 `experiments_0404/experiments/posterior/bnn-phy-mono/benchmark_summary.csv`
- **可能原因**：0.875 / 0.861 / 0.917 可能对应不同模型或不同计算方式

#### `[ACTION]`
- [ ] **紧急核实**：从 canonical posterior results 确定真实 90%-CI coverage
- [ ] 全文统一为一个数字

#### 问题 3: Speedup factor
| 位置 | 当前值 |
|------|--------|
| Abstract (L76) | ≈ 1.43 × 10⁵ |
| Section 3.4 (L482) | ≈ 1.43 × 10⁵ (single draw), ≈ 1.37 × 10⁸ (batch) |

- **状态**：这两个数是一致的（单次 vs 批处理），但 Abstract 只报了单次
- **注意**：NCS_REVISION_PLAN 提到 "elsewhere ~1.76×10⁵"——需要搜索这个数是否出现在稿件中

#### `[ACTION]`
- [ ] 确认 Abstract 用 1.43×10⁵ (single draw) 是否合适，统一口径

---

## VIII. 模型选择逻辑统一（GPT 提出，Gemini 间接支持）

### 核查

**`[VALID]`** 当前稿件的模型选择逻辑还不够统一。

- **问题**：一旦写入 external baseline 结果，如果 BNN 不在所有指标上都最优，需要一个统一的选择理由贯穿全文
- **核心逻辑**：BNN 被选中不是因为点精度最高，而是因为它提供了最一致的 posterior-predictive object，可以无需重训地支撑三类分析

#### `[ACTION]` 需要在四处形成回声
- [ ] **Abstract**：目前无模型选择声明，需加入
- [ ] **2.1 末段 (L207-209)**：当前说 "accuracy is sufficient for distribution-level analyses"——需加一句关于为什么选 BNN 而非其他 probabilistic alternative
- [ ] **3.2 (L380-407)**：当前比较了 ELBO-only / homo / hetero，但未将 BNN vs external alternatives 纳入
- [ ] **Conclusion (L895-920)**：当前无模型选择 justification

---

## IX. phy-mono Narrative Pivot（GPT + Claude 标出，Gemini 未明确提）

### 核查

**`[VALID]`** Baseline 也有 0% monotonicity violation，所以 "prevents violations" 不是卖点。

- **当前稿件状态**：3.2 (L381-383) "adding physics-prior monotonicity constraints shrinks the 90% predictive interval without reducing coverage"——这其实已经是 sharpness pivot！但后面 L384-387 又回去讲 monotonicity enforcement，混淆了重点。
- **NCS_REVISION_PLAN Gap 4** 已标出：pivot from "prevents physics violations" → "shrinks epistemic uncertainty"

#### `[ACTION]`
- [ ] **3.2 重点调整**：主论点从 "enforces monotonicity" 转为 "prunes non-physical weight-space regions → sharper intervals"
- [ ] **具体数字**：MPIW 46.2 → 41.5 MPa (from REPORT_01)，或 B2 table stress MPIW 40.2 MPa
- [ ] **检查数据一致性**：NCS_REVISION_PLAN 说 46.2→41.5，B2 table 说 reference MPIW 40.2——这是否因为 reference = phy-mono 而非 baseline？需要核实

---

## X. 前作边界声明（三方共识）

### 核查

**`[VALID]`** 当前稿件没有任何前作边界声明。必须加。

- **前作清单**：
  1. Energy 2025 [9]：design-oriented multiphysics coupling + surrogate + optimization
  2. RPHA conference：BNN + Sobol + MCMC inverse-UQ demonstration
  3. 核动力工程（中文）：steady-state multiphysics coupling + UQ + sensitivity

- **当前引用状态**：Energy 2025 = [9]，在 Methods 4.2 中引用为耦合方案来源。RPHA 和中文稿尚未明确引用。

#### `[ACTION]`
- [ ] **Introduction 末段（L166 之前）**：插入 3-4 句边界声明
- [ ] 核心逻辑：Energy = design optimization; RPHA = proof-of-concept demo; 本文 = unified posterior-predictive layer
- [ ] 不要起独立小节，融入现有贡献段

---

## XI. 缺失文献（Gemini + Claude）

### 核查

**`[VALID]`** 以下文献是 NCS 审稿人期望看到的坐标参考。

| 文献 | 功能 | 当前是否引用 |
|------|------|-------------|
| Sudret (2008) *Reliability Eng & System Safety* | PCE/GP global sensitivity 经典坐标 | 未引 |
| Raissi et al. (2019) *J Comp Phys* | PINN 原始论文，划界用 | 未引 |
| Karniadakis et al. (2021) *Nature Reviews Physics* | PINN 综述，NCS 审稿人熟悉 | 未引 |
| Kennedy & O'Hagan (2001) *JRSS-B* | Bayesian calibration 金标准 | 未引 |
| Lakshminarayanan et al. (2017) | Deep Ensemble，已用作 baseline | 需确认是否在 Intro 中引用 |
| Gal & Ghahramani (2016) | MC-Dropout，已用作 baseline | 需确认 |

#### `[ACTION]`
- [ ] Introduction 中引用 Sudret, Raissi, Kennedy-O'Hagan
- [ ] 引用时不只是列名，要用来**定位**：
  - Sudret → "established PCE/GP methods for global sensitivity (Sudret, 2008) operate on separate surrogate constructions for each analysis"
  - Raissi → "PINNs embed PDE residuals directly; the present approach uses constitutive-law priors instead"
  - K&O → "the Bayesian calibration framework follows Kennedy & O'Hagan (2001), with the BNN replacing the GP emulator"

---

## XII. Methods 独立性（Gemini 提出）

### Gemini 原文要点
> Methods 是最薄的部分；NCS 要求独立可复现。必须覆盖：8 input 选择理由、OpenMC-FEniCS 耦合方案、2900 样本生成方式、BNN 架构细节、物理约束、Sobol 方法、MCMC 设定。

### 核查

**`[PARTIAL]`** Methods 已经相当完整，但 Gemini 的几个具体点值得检查。

- **已覆盖**：
  - 8 inputs + 为什么选择这 8 个：4.1 (L577-662) ✓
  - OpenMC-FEniCS coupling：4.2 (L667-731) ✓
  - 3418 samples + LHS：4.2 (L720-731) ✓
  - BNN architecture：4.3 (L734-781) ✓
  - Forward UQ：4.4 (L786-801) ✓
  - Sobol method：4.5 (L804-823) ✓
  - MCMC setup：4.6 (L828-889) ✓

- **可能不足**：
  - ±10% range 的 justification：4.1 (L649-656) 说 "conventional uncertainty margin" 但没引用
  - 为什么固定 4 个参数而非 8 个全标定：4.6 有，但可以更明确
  - Convergence criterion (1K)：4.2 (L678) ✓
  - 4 chains × 8000 iterations：4.6 (L877) ✓

#### `[ACTION]`
- [ ] **4.1**：±10% 范围加一个引用或更强的 justification
- [ ] 其余无需大改——Methods 已经是稿件中写得最完整的部分

---

## XIII. Figure 1 重绘（Gemini + NCS_REVISION_PLAN）

### 核查

**`[VALID]`** 但执行优先级低于文字修改。

- NCS_REVISION_PLAN 已标为 Priority 4 中的 Q
- Figure 1 workflow 图对 NCS editor first impression 重要，但属于 polish 阶段

#### `[DEFER]`
- [ ] 重绘为 methodology-first 而非 engineering-flowchart
- [ ] 突出 "one BNN, three analyses" 的统一性
- [ ] 对比 conventional approach（三套代理各自训练）

---

## XIV. 残留阈值叙事（NCS_REVISION_PLAN Task F）

### 核查

**`[ALREADY / NEED VERIFY]`** 需要搜索是否还有 RPHA 时代的阈值语言残留。

#### `[ACTION]`
- [ ] 全文搜索 "45 MPa"、"feasible range"、"actionable guidance"、"threshold-based filtering"
- [ ] 如有残留，删除或改写为 observation-conditioned updating 语言

---

## XV. MCMC acceptance rate 解释（Gemini Q4）

### Gemini 原文要点
> 0.58-0.62 看起来高（理论最优 ~0.234）

### 核查

**`[VALID]`** 需要在附录中解释。

- 0.234 是高维 random-walk Metropolis 的渐近最优
- 对 4D + tuned proposal scale，0.6 是合理的
- Roberts & Rosenthal (2001) 的建议是 0.234 for d→∞

#### `[ACTION]`
- [ ] **Appendix E**：加一句解释 acceptance rate 合理性
- [ ] 引用 Roberts et al. 或说明 4D 情形下最优接受率高于渐近值

---

## 执行优先级总表

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
P0 — 投稿前必须完成（数据 freeze + 叙事安全）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  1. [BLOCKED] XVI.E 采样分布不一致决策 (uniform vs truncated Gaussian)
  2. VII  数值对齐 (damping->30%, coverage [BLOCKED on 4-chain], speedup OK)
  3. V+XVI.A  k_eff R2 defense (DOWNGRADED: gap only 0.007, BNN CRPS/ECE better)
  4. IX+XVI.C  phy-mono pivot (MPIW diff only 2%! Use CRPS/ECE instead)
  5. VIII  模型选择逻辑统一 (Abstract/2.1/3.2/Conclusion)
  6. [BLOCKED] VI  MCMC diagnostics (single-chain Rhat=NaN, wait 4-chain)

━━━━━���━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
P1 — 叙事完整性（缺一条审稿人就会 major revision）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  6. §V+VIII  External baseline 写入稿件（含 k_eff defense）
  7. §X       前作边界声明
  8. §II      L140-141 GP/PCE overclaim 修正
  9. §III     Physics-prior 命名精确化 + PINN 划界
 10. §IV      数据获取成本防御（Discussion/Limitations）

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
P2 — 段落升级（方向正确，幅度适度）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

 11. §NCS-B   Results 2.3 补信息通道总结段
 12. §NCS-C   Results 2.4 补 Sobol↔posterior coherence 总结句
 13. §NCS-D   Discussion 3.3 measurement design 表述加强
 14. §I       Discussion/Conclusion 强化 generalisability 声明

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
P3 — 引用与防御细节
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

 15. §XI     补 Sudret / Raissi / K&O / Lakshminarayanan 引用
 16. §VI     OOD monotonicity preservation 附录一句
 17. §XIV    残留阈值叙事搜索清除
 18. §XV     MCMC acceptance rate 解释（Appendix E）
 19. §XII    Methods ±10% justification 加固

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
P4 — 图表 polish（文字定稿后执行）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

 20. §XIII   Figure 1 重绘
 21. §NCS-R  Figure 5 restructure
 22. §NCS-S  Fig A2 deduplication
 23. §NCS-T  Figures 2-4 micro-fixes
```

---

## 与 NCS_REVISION_PLAN.md 的关系

本文件是对 Gemini 审查意见的**独立核查**，与已有的 `NCS_REVISION_PLAN.md` 互补：

| 内容 | NCS_REVISION_PLAN | 本文件 |
|------|-------------------|--------|
| External baseline | Gap 1 | §V, §VIII |
| MCMC diagnostics | Gap 2 | §VII (data check) |
| k_eff R² vulnerability | Gap 3 | §V (核实 + defense) |
| phy-mono pivot | Gap 4 | §IX |
| Prior-work boundary | Task A | §X |
| 2.3/2.4/3.3 upgrade | Tasks B-D | §P2 items |
| Methods rewrite | Task E | §XII（已大部分完成） |
| Numerical alignment | Task G | §VII |
| OOD narrative | Task H | §VI |
| GP/PCE overclaim | **新增** | §II |
| PINN naming risk | **新增** | §III |
| Data acquisition cost | **新增** | §IV |
| Generalisability framing | **新增** | §I |
| Missing literature | **新增** (partially in Task J) | §XI |
| MCMC acceptance defense | **新增** | §XV |

---

---

## XVI. 数据核实结果（2026-04-19 Claude 独立验证）

以下为从 canonical v3418 结果文件中直接提取的数值，用于 freeze 决策。

### A. k_eff R² 真实数据（§V 的关键核实）

| Model | keff R² | keff CRPS | keff ECE | keff PICP |
|-------|---------|-----------|----------|-----------|
| bnn-baseline | 0.844 | 1.68e-4 | 0.147 | 0.958 |
| **bnn-phy-mono** | **0.849** | **1.61e-4** | **0.123** | **0.974** |
| MC-Dropout | 0.856 | 1.75e-4 | 0.152 | — |
| Deep Ensemble | 0.828 | 1.84e-4 | 0.141 | — |

**结论**：NCS_REVISION_PLAN 中说 "BNN ~0.63" 是**错误的旧数据**。
canonical v3418 bnn-phy-mono keff R² = 0.849，与 MC-Dropout (0.856) 仅差 0.007。
同时 BNN 的 CRPS 更优 (1.61e-4 vs 1.75e-4)，ECE 更低 (0.123 vs 0.152)。

**防御策略调整**：不再需要 "R² is misleading for near-constant outputs" 的强防御。
改为：BNN 在 keff 上 R² 与 baselines 相当，CRPS/ECE 更优。

### B. Stress 对比

| Model | stress R² | stress CRPS | stress MPIW | stress PICP |
|-------|-----------|-------------|-------------|-------------|
| bnn-baseline | 0.942 | 4.42 | 40.2 MPa | 0.990 |
| **bnn-phy-mono** | **0.944** | **4.35** | **39.4 MPa** | **0.986** |
| MC-Dropout | 0.934 | 4.52 | — | — |
| Deep Ensemble | 0.934 | 4.50 | — | — |

**结论**：BNN 在 stress 上全面优��� external baselines。

### C. MPIW 对比（§IX phy-mono pivot 的关键核实）

| Model | stress MPIW |
|-------|-------------|
| bnn-baseline | 40.2 MPa |
| bnn-phy-mono | 39.4 MPa |
| bnn-baseline-homo | 45.2 MPa |

**结论**：NCS_REVISION_PLAN 引用的 "46.2→41.5 MPa" 是旧值。
canonical v3418 实际 MPIW 差异 = 40.2→39.4 = **仅 2% 收窄**。
这个差异**不够显著**，不能作为 phy-mono 的主要卖点。

**phy-mono pivot 策略调整**：
- 不能用 "MPIW 从 46.2 降至 41.5" 这个叙事
- 但 **bnn-phy-mono vs bnn-baseline-homo**（40.2 vs 45.2 = 12.4% 收窄）仍然有效——这说明 heteroscedastic + physics-prior 的组���效果
- 更好的 pivot：phy-mono 的价值在于 **CRPS 最优 (4.35 vs 4.42)** + **ECE 最低 (0.106 vs 0.130)** + 全面最优的分布质量
- 或者强调：physics prior 的真正价值在 **小样本数据效率**（如果有数据的话）——但你说 phy-mono 小样本实验不存在

### D. 90%-CI Coverage 对齐（§VII 的核实��

| Source | Coverage | Notes |
|--------|----------|-------|
| v3418 bnn-phy-mono posterior | **0.861** (62/72) | 单链 × 18 cases × 4 params |
| legacy bnn-phy-mono posterior | **0.917** (66/72) | 单链，不同 run |
| Abstract | 0.875 | 来源不明 |
| Results 2.4 | 0.861 | 与 v3418 一致 |
| Conclusion | 0.917 | 与 legacy 一致 |

**结论**：0.861 和 0.917 来自不同 runs（v3418 vs legacy��。
两者都是单链结果，4-chain 重跑正在服务器上进行。
**必须等 4-chain 结果出来后才能 freeze coverage 数字。**

临时决策建议：
- 如果 4-chain 结果很快可用 → 等它
- 如果无法及时获得 → 使用 v3418 的 0.861（因为是 canonical model 的结果）
- Abstract 中的 0.875 无来源支撑，必须改

### E. 采样分布不一致问题（confirmed）

| 稿件声称 | 代码实际 |
|----------|----------|
| "independent uniform priors with half-width 10%" (L649) | 训练数据: LHS + Gaussian CDF (`norm.ppf`, σ=10% of nominal) |
| "Latin hypercube sampling over the 8-dimensional prior" (L720) | 前向 UQ: `rng.normal(loc=nominal, scale=σ)` |
| "uniform priors" for MCMC (implied) | MCMC prior: truncated Gaussian (hard bounds + Gaussian kernel) |

**结论**：这是一个**实质性不一致**，不仅是措辞问题。

**决策选项**：
1. 修改稿件：将 "uniform prior" 改为 "truncated Gaussian prior"，σ = 10% of nominal
2. 修改代码：将采样改为 uniform（需要重跑所有结果）
3. 论证两者差异在实际中可忽略（如果 ±3σ 范围内 truncated Gaussian ≈ nearly uniform）

**推荐**���选项 1 + 论证。实际的 truncated Gaussian 在 [μ-3σ, μ+3σ] 范围内已经涵盖了 99.7% 的质量，而 uniform ±10% = ±1σ 的范围。这意味着**两者在形状上差异很大**：Gaussian 集中在中心，uniform 是平的。
**这需要你拍板**——是修改代码统一为 uniform，还是修改稿件说实话。

### F. Speedup factor 核实

| 稿件 | 计算 |
|------|------|
| Abstract: ≈ 1.43 × 10⁵ | 2266s / 0.0158s = 143,418 ✓ |
| 3.4: ≈ 1.37 × 10⁸ (batch) | 2266s / 1.7e-5s = 1.33 × 10⁸ ✓ |

**结论**：speedup 数字内部自洽。NCS_REVISION_PLAN 提到的 "1.76×10⁵" 可能来自旧版。
当前稿件中未见 1.76×10⁵，无需修改。

---

## 核查状态追踪

每完成一项，在对应 `[ ]` 中标 `[x]` 并注明日期和修改位置。
