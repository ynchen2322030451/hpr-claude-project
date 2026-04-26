# DEPRECATED — see /IMPROVEMENT_PLAN.md for the current plan

# NCS Revision Plan

Date: 2026-04-19 (created) / 2026-04-19 (v2 — Gemini review merged)
Source: GPT external review + Gemini external review of current project state
Status: **PLAN ONLY — no changes made yet**

---

## Overall Assessment

Current state: strong computational workflow paper with real results, but not yet
organized as a methodology paper that NCS would accept. HF rerun is complete (54/54,
MAE 5.65 MPa). The gap is now structural/editorial, not missing core experiments.

**Two hard evidence gaps + one editorial round** remain before submission-ready.

---

## I. Hard Evidence Gaps (must fix)

### Gap 1: External Probabilistic Baseline

**Status**: planned in MODEL_UPGRADE_PLAN.md (Appendix O) but not yet executed.
**What**: MC-Dropout or Deep Ensemble (pick one), run on same test split.
**Where**: Appendix only. Main text gets one sentence.
**Why**: Without this, reviewers will ask "why BNN and not X?" with no answer.

Suggested main-text sentence (EN):
> Compared with common posterior-approximation alternatives such as MC-Dropout,
> the Bayesian surrogate was retained because it provided the most coherent
> predictive distribution across forward propagation, sensitivity attribution
> and posterior calibration (Supplementary Table X).

Suggested main-text sentence (CN):
> 相较于 MC-Dropout 等常见后验近似替代方案，本文最终保留当前贝叶斯代理模型，
> 是因为它能在前向传播、敏感性归因与后验标定三项任务中提供最一致的预测分布表示
> （补充材料表 X）。

### Gap 2: MCMC Convergence Diagnostics (quantitative freeze)

**Status**: runs complete, trace plots likely exist, but no frozen quantitative
statement in main text.
**What**: report Rhat < 1.1 (all chains), no directional drift, ESS if available.
**Where**: one sentence in main text (Results 2.4), full table in Appendix E.

Suggested main-text sentence (EN):
> All four-chain runs satisfied the convergence criterion R-hat < 1.1,
> with no directional drift in the trace diagnostics (Appendix E).

Suggested main-text sentence (CN):
> 全部四链采样结果均满足 R-hat < 1.1 的收敛判据，且迹图中未见方向性漂移
> （附录 E）。

### Gap 3: k_eff R² Narrative Vulnerability (Gemini)

**Status**: not yet addressed in manuscript.
**Problem**: External baselines (MC-Dropout ~0.856, Deep Ensemble ~0.827) beat BNN
(~0.63) on k_eff R². This is a dangerous reviewer attack surface.
**Root cause**: material-parameter perturbations produce extremely narrow k_eff
variance (σ ≈ 0.0007), making R² hypersensitive to noise — misleading metric.
**Fix**: Preemptively "self-detonate" in main text. Pivot to CRPS and MAE where BNN
is competitive. Add explicit note that R² is unreliable for near-constant outputs.

Suggested defense (EN):
> Because material-parameter perturbations induce only minimal k_eff variation
> (σ ≈ 0.0007), the coefficient of determination is dominated by noise and
> provides a misleading comparison. The calibration-sensitive metrics CRPS and
> NLL, which reward well-shaped predictive distributions rather than explained
> variance, show the Bayesian surrogate performing on par with or better than
> frequentist alternatives (Supplementary Table X).

### Gap 4: Phy-mono Narrative Pivot (Gemini)

**Status**: narrative mismatch — Baseline also has 0% monotonicity violation.
**Problem**: If Baseline already perfectly obeys physics, "physics correction" is a
hollow selling point. Reviewers will ask: why bother with phy-mono?
**Fix**: Pivot from "prevents physics violations" → "shrinks epistemic uncertainty."
Key evidence: phy-mono MPIW 41.5 MPa vs Baseline 46.2 MPa (from REPORT_01).
Physics constraints prune non-physical prior space → sharper intervals without
losing coverage. Also check data-efficiency advantage at 25%/50% training size.

Suggested defense (EN):
> Both the unconstrained baseline and the physics-regularised surrogate achieve
> zero monotonicity violations on the test set. The value of the monotonicity
> prior therefore lies not in correcting point predictions but in pruning
> non-physical regions of the weight posterior, which reduces the mean prediction
> interval width from 46.2 MPa to 41.5 MPa without degrading coverage — a
> sharpness gain that matters for downstream risk quantification.

---

## II. Editorial / Structural Tasks (must fix)

### Task A: Prior-Work Boundary Statement

**Problem**: Energy 2025, NPE (Chinese journal), and RPHA conference paper overlap
significantly in methods/domain. Reviewers will question novelty if boundary is not
explicitly drawn.
**Location**: Introduction final paragraph or contribution paragraph. NOT a separate section.

Suggested text (EN):
> Our previous studies addressed adjacent but different questions. The earlier
> high-fidelity coupling and optimization work focused on reactor design and
> stress mitigation under a deterministic or point-predictive workflow, rather
> than on uncertainty propagation and observation-conditioned inference. The
> subsequent conference paper introduced a Bayesian surrogate and an inverse-UQ
> demonstration, but did not establish a unified posterior-predictive layer that
> coherently supports forward propagation, sensitivity attribution and posterior
> calibration within one coupled workflow. The present study is positioned at
> that methodological level.

Suggested text (CN):
> 我们前期工作的研究问题与本文相邻但并不相同。此前面向设计的多物理分析主要关注
> 反应堆优化与应力缓解，其分析链条本质上仍是确定性或点预测驱动的，而非面向
> 不确定性传播与观测条件反演。后续会议论文虽然已经引入贝叶斯代理与逆向不确定性
> 分析示范，但尚未将前向传播、敏感性归因与后验标定统一到同一个后验预测层之上。
> 本文的定位正是在这一方法层面。

### Task B: Results 2.3 Upgrade (Sobol → information channels)

**Problem**: currently reads as parameter ranking; needs to become "why multi-output
calibration is justified" — the methodological payoff.

Key rewrite direction:
- Stress governed by stiffness/expansion parameters (E_intercept dominant)
- k_eff governed by geometry-mediated thermal-expansion feedback (alpha_base dominant)
- Two outputs constrain **different** parts of parameter space → not redundant
- This is the evidential foundation for multi-observable calibration in 2.4

Suggested core paragraph (EN):
> The key result of the Sobol analysis is not the ranking itself, but the
> separation of informative parameter channels across outputs. Peak stress is
> governed primarily by stiffness- and expansion-related parameters, whereas
> coupled k_eff is dominated by the thermal-expansion pathway that perturbs
> the neutronic balance through geometry-mediated feedback. These two outputs
> therefore do not provide redundant information. Instead, they constrain
> different parts of parameter space and create a natural rationale for
> multi-observable calibration.

Suggested core paragraph (CN):
> Sobol 分析最重要的结果并不在于"谁排第一、谁排第二"，而在于不同输出所对应的
> 信息通道是分离的。峰值应力主要受材料刚度与热膨胀相关参数控制，而耦合 k_eff
> 则主要受热膨胀引起的几何反馈通道支配。这意味着两类输出提供的并不是重复信息。
> 相反，它们约束的是参数空间中不同的方向，因此天然适合用于多观测量联合标定。

### Task C: Results 2.4 Upgrade (posterior ↔ Sobol coherence)

**Problem**: posterior contraction not yet explicitly linked to Sobol-identified
informative directions.

Suggested core paragraph (EN):
> Posterior contraction occurs predominantly along the same parameter directions
> identified as informative in the forward Sobol analysis. This agreement matters
> more than the coverage statistic alone: it shows that the calibration step is
> not shrinking parameters arbitrarily, but is concentrating probability mass
> along directions that the forward model already marked as most relevant to the
> observed response. In that sense, the forward sensitivity analysis and the
> posterior update form a coherent evidence chain rather than two disconnected
> analyses.

Suggested core paragraph (CN):
> 后验收缩主要发生在前向 Sobol 分析已识别为高信息量的参数方向上。相较于单独
> 汇报覆盖率指标，这一点更重要：它说明标定过程并不是任意地缩小参数范围，而是
> 在将概率质量集中到前向模型已经判定为与观测响应最相关的方向上。从这个意义上说，
> 前向敏感性分析与后验更新构成的是一条连贯的证据链，而不是两块彼此独立的分析结果。

### Task D: Discussion 3.3 Upgrade (measurement design implication)

**Problem**: currently generic engineering implication; needs to become
"information-channel-aware measurement design."

Suggested core paragraph (EN):
> This separation of parameter channels has a practical consequence for
> measurement design. Material-property priors may initially come from handbooks,
> fabrication specifications or engineering judgment, but posterior updating
> should not rely on a single aggregated response. Structural observables are
> most informative for stiffness- and expansion-related directions, whereas
> neutronic observables constrain the geometry-mediated feedback pathway. If the
> objective is to reduce uncertainty efficiently, the next experiment or
> monitoring campaign should therefore be chosen according to which parameter
> channel remains weakly constrained, rather than by adding more measurements
> of the same observable type.

Suggested core paragraph (CN):
> 参数信息通道的分离对观测设计具有直接意义。材料参数的先验可以先来自手册数据、
> 制造规范或工程经验，但后验更新不能依赖单一的综合响应量。结构类观测对刚度和
> 热膨胀相关方向最有信息量，而中子学观测则更能约束几何反馈通道。因此，如果目标
> 是高效降低参数不确定性，下一步实验或监测方案应围绕"哪一类参数方向仍然约束
> 不足"来设计，而不是重复增加同类型观测。

### Task E: Methods Must Be Rewritten to Stand Alone

**Problem**: Methods is the thinnest section; NCS expects independent reproducibility.
**What must be covered**:
1. 8 input parameters: why selected, why independent, why ±10% ranges
2. OpenMC–FEniCS data flow (coupling scheme, convergence criterion)
3. 2900-sample dataset: how generated, LHS or other DOE
4. BNN architecture: prior, variational posterior, ELBO, posterior predictive
5. Physics constraints: what they enforce, where they act, boundary conditions
6. Forward UQ: why predictive mean is used, MC sample count
7. Sobol: Jansen estimator, Saltelli cross-matrix, 50 replications, CI method
8. Posterior calibration: likelihood construction, noise model, chain settings,
   convergence diagnostics, number of chains, burn-in, thinning

### Task F: Remove Residual Threshold Narrative

**Problem**: old RPHA-era threshold language (45 MPa threshold, feasible ranges,
actionable guidance) may still be present. Must be fully excised from main text.
Posterior = observation-conditioned updating, NOT threshold-based filtering.

### Task G: Numerical Alignment Sweep (Gemini)

**Problem**: multiple numerical inconsistencies flagged:
1. **Acceptance rate**: manuscript/memory says 0.58–0.67, but latest REPORT_07
   says 0.58–0.62. Must unify globally to 0.58–0.62.
2. **Coupling damping "≈28%"** in abstract: must specify whether this is variance
   ratio, std reduction, or other statistic. Ambiguity invites reviewer pushback.
3. **Speedup factor**: abstract says ~1.43×10⁵, elsewhere ~1.76×10⁵. Pick one
   and define it precisely (wall-clock per sample? end-to-end?).

### Task H: OOD Narrative Guard (Gemini)

**Problem**: OOD R² > in-distribution R² is counterintuitive (driven by SST
variance expansion, not better prediction). Must NOT claim "better OOD accuracy."
**Fix**: Frame OOD results around PICP ≥ 0.98 and epistemic σ inflation (7–21%).
The story is: BNN honestly widens intervals in extrapolation regions, maintaining
safe envelopes — this is the nuclear-safety-relevant property.

### Task I: Fig A2 Deduplication (Gemini)

**Problem**: Fig A2 is currently identical to main-text Fig 5. Editor will flag as
redundant supplementary material.
**Fix**: Either (a) make A2 show all four BNN variants side-by-side (vs Fig 5
showing only best model), or (b) remove A2 entirely.

### Task J: Missing Literature References (Gemini)

Must add to Introduction or Discussion to preempt reviewer complaints:
1. **PCE/GP classical UQ**: Sudret (2008) *Reliability Eng & System Safety* —
   polynomial chaos expansions for global sensitivity. Needed to justify why BNN
   over established surrogate-UQ methods.
2. **PINN distinction**: Raissi et al. (2019) *J Comp Phys*; Karniadakis et al.
   (2021) *Nature Reviews Physics*. Must clarify: this is a physics-constrained
   data-driven surrogate, NOT a PDE-solving PINN.
3. **Bayesian calibration**: Kennedy & O'Hagan (2001) *JRSS-B*. Gold standard
   for model calibration — must cite when presenting MCMC framework.
4. **Deep Ensembles**: Lakshminarayanan et al. (2017). Already used as baseline;
   ensure cited in Introduction as UQ benchmark, not just Methods.

---

## III. Figure Tasks

### Figure 1: MUST REDRAW (not tweak)
- Currently reads as engineering flowchart / PPT poster
- Must become methodology-first workflow figure
- Surrogate block should be visually central
- Downstream analyses need visual hierarchy (not equal weight)
- This is the editor's first-impression figure

### Figure 2: KEEP but freeze canonical values
- Parity plots are functional but not yet publication-grade
- **Blocker**: fixed_eval vs repeat_eval vs manuscript values must be unified
- Stress panel needs to dominate visually

### Figure 3: KEEP, enhance visual argument
- Uncoupled vs coupled comparison direction is correct
- Needs stronger visual demonstration of "coupling changes distribution shape"
- k_eff panel feels subordinate

### Figure 4: KEEP, sharpen
- Sobol bar chart is standard but not NCS-level
- Needs clearer visual separation of dominant factors
- Currently reads as supplementary-grade

### Figure 5: MOST WORK NEEDED
- Posterior figure is least mature
- 3-panel direction is correct
- Predictive vs observed panel still reads as diagnostic
- Marginal / joint / predictive hierarchy unclear
- Must become "observation-conditioned shift" main figure

### Figure-level micro-fixes (Gemini)
- Fig 1 (accuracy/reliability): add "↓ Lower is better" to CRPS/ECE panels
- Fig 2 (parity): add caption note about k_eff's extremely narrow x-axis scale
  to visually explain why R² appears low
- Fig 3 (forward UQ): ensure "Δμ = -47.8 MPa" has highest visual hierarchy
  (contrast color annotation)
- Fig 5 (physics): since Baseline and phy-mono both show 0% violation,
  Panel B caption must explain how physics constraints change epistemic/aleatoric
  decomposition ratio, not just violation rate

---

## IV. Main Text → Supplementary Migration

Main text keeps **one sentence** mentioning each; all details go to Supplementary:

| Content | Main text | Supplementary |
|---|---|---|
| Full test-set parity (all outputs) | one summary line | full table + plots |
| Complete Sobol indices + CI | conclusion only | S₁/ST tables, 50-rep CI |
| All 15-output accuracy table | headline R²/RMSE | full table |
| MCMC trace / Rhat / ESS | one sentence | full diagnostics |
| Calibration reliability curves | — | Appendix E |
| Epistemic vs aleatoric decomposition | — | Appendix |
| Prior–posterior predictive comparison | — | Appendix |
| Training curves | — | Appendix |
| Speed benchmark full table | headline speedup only | full breakdown |
| Predictive variant comparison | — | Appendix |
| External baseline (MC-Dropout/DE) | one sentence | Appendix O |
| OOD stress extrapolation | one sentence | Appendix |

---

## V. Already Complete (do NOT re-pursue)

- [x] HF rerun: 54/54 complete, stress MAE 5.65 MPa, 4.5% relative error
- [x] HF [5%,95%] envelope covers all 18 true stress values
- [x] Posterior benchmark: 18 cases, acceptance 0.58–0.67, 90CI coverage 0.89–0.92
- [x] Sobol canonical results frozen (E_intercept stress, alpha_base keff)
- [x] BNN heteroscedastic architecture confirmed
- [x] MCMC likelihood correctly combines obs noise + surrogate uncertainty
- [x] Threshold narrative removal: direction set, partially executed
- [x] External baseline experiments: MC-Dropout + Deep Ensemble results exist
      (per Gemini review referencing RESULT_accuracy_external_baseline_scoring.csv)

---

## VI. Anticipated Reviewer Questions (Gemini)

Prepare preemptive defenses for these top-5 attack vectors:

**Q1: k_eff R² is worse than MC-Dropout/DE. Why trust BNN for safety?**
→ R² misleading for near-constant outputs (σ ≈ 0.0007). Pivot to CRPS/NLL where
  BNN is competitive. Explain in main text proactively.

**Q2: Baseline already has 0% physics violations. Why bother with phy-mono?**
→ Pivot to sharpness: MPIW 46.2→41.5 MPa. Physics prior prunes non-physical
  weight-space regions. Also check data-efficiency advantage at small N.

**Q3: Only ~3400 samples and 8D input. Does this scale to higher dimensions?**
→ Acknowledge curse of dimensionality in Discussion/Limitations. Physics
  constraints act as strong inductive bias mitigating data hunger. Cite
  data-efficiency ablation (RESULT_data_efficiency_summary.csv).

**Q4: MCMC acceptance rate 0.58–0.62 seems high (theory optimal ~0.234)?**
→ 0.234 is for high-dimensional random-walk Metropolis. For 8D with tuned
  proposal scale, 0.6 is appropriate. Cite Rhat < 1.01 and ESS as convergence
  evidence. Explain in Appendix E.

**Q5: Only steady-state analysis. What about transients/accidents?**
→ Honestly scope as limitation. Transients need RNN/Neural ODE architectures.
  List as future work. Do NOT overclaim.

---

## VII. Nice-to-Have (not blocking submission)

- Prior sensitivity analysis (different prior widths)
- Noise sensitivity (1%, 2%, 5% observation noise)
- Data efficiency curve (learning curve vs dataset size)
- Conformal prediction wrapper (appendix only)

---

## VII. Data & Code Availability (prepare early)

Nature Portfolio requires explicit data/code availability statement:
- Which data can be shared openly?
- Which code can be shared (GitHub repo)?
- Which parts need "available upon request" due to platform/scale?
- Cover letter must address any restrictions

---

## VIII. Execution Priority

```
Priority 1 (boundary + freeze + numerical alignment):
  A. Prior-work boundary statement
  B. Canonical result freeze (fixed_eval vs repeat_eval decision)
  C. Remove all residual threshold language
  D. Numerical alignment sweep (acceptance rate, coupling damping %, speedup)
  E. k_eff R² narrative pivot (preemptive defense)
  F. Phy-mono narrative pivot (sharpness, not violation correction)

Priority 2 (hard evidence):
  G. External baseline results freeze (MC-Dropout/DE already run → write up)
  H. MCMC diagnostics quantitative freeze (Rhat, ESS → main-text sentence)

Priority 3 (main-text rewrite):
  I.  Methods full rewrite (standalone reproducibility)
  J.  Results 2.3 upgrade (Sobol → information channels)
  K.  Results 2.4 upgrade (posterior ↔ Sobol coherence)
  L.  Discussion 3.3 upgrade (measurement design)
  M.  OOD narrative guard (PICP + epistemic inflation, not "better R²")
  N.  Missing literature references (PCE, PINN, Kennedy-O'Hagan, DE)
  O.  Main-text slimming (migrate content to Supplementary)
  P.  Preemptive reviewer Q&A embedded in Discussion/Limitations

Priority 4 (figures):
  Q. Figure 1 redraw (methodology-first)
  R. Figure 5 restructure (observation-conditioned shift)
  S. Fig A2 deduplication
  T. Figures 2–4 polish + micro-fixes (CRPS arrows, k_eff scale note, Δμ)
```
