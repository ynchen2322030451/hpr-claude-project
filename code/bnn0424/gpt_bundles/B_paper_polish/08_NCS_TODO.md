# NCS Submission TODO — Consolidated from GPT + Claude Reviews

Date: 2026-04-19
Status: **NEAR-COMPLETE — P1–P4 all done; P5.2/P5.3 need user decisions**

## State Assessment

P1 blocking items (boundary stmt, numerical alignment, fig1/fig6 restructure) — all resolved.
P2 important items (k_eff defense, phy-mono pivot, external baseline, MCMC diagnostics) — all resolved.
P3 editorial items — all resolved.
P4 figure items — all reviewed/resolved.
Remaining: P5.2 (data/code availability statement) and P5.3 (cover letter) require user decisions.

---

## Canonical Values (FREEZE THESE — source of truth)

All numbers below come from `results/results_v3418/` (bnn0414 runs).
The `code/experiments_legacy/` directory contains OLD runs and must NOT be cited.

| Metric | Canonical value | Source file | Draft discrepancies |
|--------|----------------|-------------|---------------------|
| 90%-CI coverage | **0.861** | results_v3418/posterior/bnn-phy-mono/benchmark_summary.csv | ~~Abstract 0.875; Conclusion 0.917~~ **FIXED** |
| Acceptance rate | **0.58–0.63, mean 0.61** | rerun_4chain/benchmark_summary.csv | ✅ updated from 4-chain rerun |
| Coupling std damping | **≈ 30%** (std_coupled/std_uncoupled = sqrt(0.4901) = 0.70) | results_v3418/risk_propagation/bnn-phy-mono/D3_coupling.json | ~~Intro & Conclusion "≈ 28%"~~ **FIXED** |
| Stress Δμ (coupled − uncoupled) | **−41.8 MPa** | same D3_coupling.json | Section 2.2 says "≈ 42 MPa" — OK |
| Speedup (single draw) | **≈ 1.43 × 10⁵** | consistent across draft | OK |
| Rhat | **max R̂ = 1.010** (4-chain rerun) | rerun_4chain/benchmark_summary.csv | ✅ all < 1.02 |
| Stress forward mean (coupled) | **161.7 MPa** (sigma_k=1.0, predictive draw) | D1_nominal_risk.csv | OK ✓ |
| Stress forward std (coupled) | **31.9 MPa** (sigma_k=1.0, predictive draw) | D1_nominal_risk.csv | OK ✓ |
| k_eff forward std | **77 pcm** (sigma_k=1.0) | D1_nominal_risk.csv | ~~107 pcm~~ **FIXED** (107 was legacy bnn-data-mono-ineq) |

### ⚠ RESOLVED: forward UQ numbers reconciled
D1_nominal_risk.csv at sigma_k=1.0 (RISK_PROP_SIGMA_K_MAIN) matches manuscript:
stress mean=161.7, std=31.9. The sigma_k=0.5 row was a red herring. keff std was wrong
(107 pcm from legacy model) → corrected to 77 pcm.

### ✅ RESOLVED: 4-chain MCMC rerun complete
Rerun with 4 independent chains completed 2026-04-19. All 18 cases × 4 params:
max R̂ = 1.010, all < 1.02. Results in `rerun_4chain/benchmark_summary.csv`.
Acceptance rates: 0.58–0.63, mean 0.61. 90CI coverage: 0.861 (unchanged).

### ⚠ FLAG: Sampling distribution mismatch (Methods 4.1 vs code)
Methods 4.1 states uniform priors θ_k ~ U[0.9θ_nom, 1.1θ_nom].
But the forward UQ code (run_risk_propagation_0404.py) uses:
  `rng.normal(loc=nominal, scale=sigma_k * DESIGN_SIGMA)`
where DESIGN_SIGMA = 10% of nominal. Gaussian σ=10% is wider than Uniform ±10%.
Training data generation (generater.py) also uses LHS + Gaussian inverse CDF.
**Decision needed**: either (a) rerun forward UQ with uniform sampling on server,
or (b) change manuscript to describe Gaussian prior. Option (b) is simpler but
changes the methodological framing.

---

## Priority 1 — BLOCKING (must fix before any submission attempt)

### P1.1 Prior-Work Boundary Statement → Introduction
- [ ] Write 1 paragraph in Introduction (after current para 5) distinguishing:
  - Energy 2025: deterministic HF coupling + data-driven surrogate + NSGA-II stress optimization
  - 核动力工程 2025: multi-module surrogates + Sobol + MC + single-factor perturbation (steady-state UQ)
  - Current paper: constraint-regularized BNN as unified posterior predictive layer
    for forward propagation, dominant-factor separation, observation-conditioned calibration
- [ ] Add corresponding CN paragraph
- [ ] Suggested text in NCS_REVISION_PLAN.md Task A — adapt, don't copy verbatim
- **Source**: GPT review (缺口1) + Claude review — both agree this is #1 risk
- **Why blocking**: Editor/reviewer will immediately question novelty overlap

### P1.2 Numerical Alignment Sweep
- [ ] **Coverage**: unify to 0.861 everywhere (abstract, 2.4, conclusion, all CN parallels)
  - Abstract line 75: change 0.875 → 0.861
  - Conclusion line 908: change 0.917 → 0.861
- [ ] **Coupling damping**: unify to "≈ 30%" everywhere
  - Intro para 5 line 172: change "≈ 28%" → "≈ 30%"
  - Conclusion line 902: change "≈ 28%" → "≈ 30%"
  - Define precisely: "(standard-deviation reduction relative to decoupled prediction)"
- [ ] **Acceptance rate**: verify 0.58–0.64 from canonical CSV; update all mentions
  - Section 2.4 line 309: currently "0.58 to 0.64, mean 0.61" — verify against CSV ✓
- [ ] **Rhat**: investigate NaN in canonical CSV. Options:
  - (a) Compute from raw chain files if they exist
  - (b) Use legacy value if chain settings are identical
  - (c) Mark as TO_BE_FILLED and schedule rerun
- [ ] **Forward UQ numbers** (stress mean/std, keff std): reconcile D1 JSON vs manuscript
  - Trace which script/run produced Section 2.2 values (161.7 / 31.9 / 107 pcm)
  - Determine whether pred_mu or full predictive draw was used
  - Freeze one set, update all references
- [ ] **Conclusion coverage**: line 908 says 0.917 — this is from legacy runs, must fix
- **Source**: GPT (缺口4) + Claude — both agree this is blocking

### P1.3 Figure 1 Restructure
- [ ] Current fig0_workflow.png — evaluate if BNN is visually central
- [ ] If not: redraw with BNN posterior predictive layer as the central node
- [ ] Remove any elements suggesting: threshold gate, old surrogate upgrade path,
      engineering action box, equal-weight parallel analysis blocks
- [ ] Downstream analyses (forward UQ, Sobol, posterior) must visually radiate FROM
      the BNN layer, not sit beside it
- **Source**: GPT (Figure 1 裁定) + Claude — both agree needs restructure
- **Why blocking**: "Editor's first-impression figure" — determines methodology-first read

### P1.4 Figure 5/6 Posterior Restructure
- [ ] Current fig6_posterior.png — evaluate current panel structure
- [ ] Target: 3 panels only in main text:
  - (A) Prior vs posterior marginals (key parameters)
  - (B) Representative joint posterior (E_intercept × α_base compensation ridge)
  - (C) Posterior predictive stress vs observed/true stress
- [ ] Move to appendix: trace plots, Rhat, ESS, autocorrelation, coverage dot chart
- [ ] Core narrative = "observation-conditioned distribution shift + predictive agreement"
- [ ] Zero tolerance for: feasible region, pass-fail gate, tolerance-from-threshold language
- **Source**: GPT (Figure 5 裁定 — "当前最不成熟") + Claude — both agree

---

## Priority 2 — IMPORTANT (high risk if omitted)

### P2.1 k_eff R² Preemptive Defense
- [ ] Write 2–3 sentences in Section 2.1 or Discussion acknowledging k_eff R² ≈ 0.63
      is low relative to MC-Dropout (~0.856)
- [ ] Explain: material-parameter perturbations produce near-constant k_eff (σ ≈ 0.0007),
      making R² dominated by noise — misleading metric
- [ ] Pivot to CRPS/NLL where BNN is competitive
- [ ] Add CN parallel
- **Source**: Gemini review (via NCS_REVISION_PLAN Gap 3) — GPT didn't cover this

### P2.2 Phy-mono Narrative Pivot
- [ ] Do NOT claim "prevents physics violations" — Baseline also has 0% violation
- [ ] Change pitch to: physics prior prunes non-physical weight-space regions →
      MPIW narrows from 46.2 → 41.5 MPa without degrading coverage
- [ ] Check Discussion 3.2 (lines 380–407) for current framing — update if needed
- [ ] This matters for Section 2.1 and Discussion 3.2
- **Source**: Gemini review (NCS_REVISION_PLAN Gap 4) — GPT didn't cover this

### P2.3 External Probabilistic Baseline Write-up
- [ ] MC-Dropout and Deep Ensemble results already exist (CSV scored)
- [ ] Write 1 sentence in main text (Section 2.1 or Discussion 3.2)
- [ ] Add 1 Supplementary Table with head-to-head metrics
- [ ] Frame: "why BNN and not MC-Dropout / Deep Ensemble"
- **Source**: Both reviews — NCS_REVISION_PLAN Gap 1

### P2.4 MCMC Diagnostics Quantitative Freeze
- [ ] After resolving Rhat NaN issue (P1.2), add 1 sentence to Section 2.4:
      "All four-chain runs satisfied R̂ < 1.1 with no directional drift (Appendix E)."
- [ ] Ensure Appendix E has: Rhat table, trace plots, ESS if available
- **Source**: Both reviews — NCS_REVISION_PLAN Gap 2

---

## Priority 3 — EDITORIAL (quality improvement, not blocking)

### P3.1 Internal Label Cleanup in Main Text
- [ ] Line 387: `bnn-data-mono-ineq` → "inequality-constraint variant" or just remove name
- [ ] Line 402: same in CN
- [ ] Line 383: `bnn-phy-mono` → keep in parenthetical? Or remove entirely from main text?
      Decision: keep ONE mention in parenthetical for reproducibility, e.g.
      "The primary model (hereafter phy-mono; code identifier bnn-phy-mono)"
- [ ] Line 1059: `bnn-baseline-homo` → "homoscedastic ablation variant"
- [ ] Search for any remaining: `HeteroMLP`, `deterministic.*prior work`, `mirror.*HeteroMLP`
      → Currently NONE found in v4 draft ✓
- **Source**: GPT + Claude (both flagged)

### P3.2 Results 2.3 Upgrade (Sobol → Information Channels)
- [ ] Current Section 2.3 already emphasizes pathway separation — good
- [ ] Strengthen the bridge sentence to 2.4: "These two outputs constrain different
      regions of parameter space" → make this the HEADLINE, not just closing remark
- [ ] NCS_REVISION_PLAN Task B has suggested text
- **Source**: GPT (缺口2 — Sobol should be "separation", not "ranking")

### P3.3 Results 2.4 ↔ Sobol Coherence
- [ ] Add 1–2 sentences linking posterior contraction directions to Sobol-identified
      informative directions
- [ ] Currently partially done (line 318–328 mentions E_intercept shift and compensation ridge)
- [ ] NCS_REVISION_PLAN Task C has suggested text
- **Source**: GPT/Claude review agreement

### P3.4 Discussion 3.3 → Information-Channel-Aware Measurement Design
- [ ] Current 3.3 is decent but generic. Upgrade "Material-characterisation priority"
      to explicitly connect Sobol channels → measurement design
- [ ] NCS_REVISION_PLAN Task D has suggested text
- **Source**: GPT review

### P3.5 Methods Supplementary Gaps (not rewrite, just fill)
- [ ] Add MCMC chain settings: number of chains (4), burn-in, thinning, proposal scale
- [ ] Add Sobol estimator detail: Jansen estimator, Saltelli cross-matrix design,
      50 replications, bootstrap CI method
- [ ] Verify all symbols are defined before first use
- [ ] Remove any remaining implementation-level detail that belongs in code, not Methods
- **Source**: GPT ("Methods is thinnest") — but actual state is better than GPT thought

### P3.6 Missing Literature References
- [ ] Sudret 2008 (PCE for global sensitivity) — justify why BNN over established surrogate-UQ
- [ ] Raissi et al. 2019 / Karniadakis et al. 2021 (PINN) — clarify this is NOT PINN
- [ ] Kennedy & O'Hagan 2001 (Bayesian calibration gold standard)
- [ ] Lakshminarayanan et al. 2017 (Deep Ensembles) — cite in Intro, not just Methods
- **Source**: Gemini review (NCS_REVISION_PLAN Task J)

### P3.7 OOD Narrative Guard
- [ ] Section 3.5 lines 538–548: check that OOD is framed as "epistemic σ inflation"
      and PICP ≥ 0.98, NOT as "better OOD accuracy"
- [ ] Currently looks OK — "k_eff R² drops to ≈ 0.31" is honest
- [ ] Verify no other section overclaims OOD performance
- **Source**: Gemini review (NCS_REVISION_PLAN Task H)

---

## Priority 4 — FIGURES (after P1/P2 resolved)

### P4.1 Figure 2 (Parity / Accuracy) Polish
- [ ] Verify parity plots use canonical fixed_eval values
- [ ] Add caption note about k_eff narrow x-axis scale (explains visually low R²)
- [ ] Stress panel should have visual dominance over keff/thermal panels

### P4.2 Figure 3 (Forward UQ) Strengthen
- [ ] Uncoupled vs coupled comparison — enhance visual contrast
- [ ] Ensure "Δμ = −42 MPa" (or corrected value) has highest visual hierarchy
- [ ] k_eff panel should not feel subordinate

### P4.3 Figure 4 (Sobol) Sharpen
- [ ] Frame as "separation" not "ranking" — visually separate stress-pathway vs keff-pathway
- [ ] CI crosses zero parameters must be visually distinct (grayed out or de-emphasized)

### P4.4 Supplementary Figure Audit
- [ ] Verify main-text vs supplementary migration matches NCS_REVISION_PLAN table
- [ ] Each supplementary figure must be explicitly called from main text or Methods
- [ ] Remove any supplementary figure that duplicates a main figure (Fig A2 ↔ Fig 5 issue)
- [ ] Training history: only include if bnn0414 logs exist, NOT old 0411 curves

---

## Priority 5 — PRE-SUBMISSION (after all above)

### P5.1 Threshold Narrative Backflow Prevention
- [ ] Final grep for: `feasible`, `actionable`, `threshold` (beyond 131 MPa risk context),
      `tolerance`, `pass-fail`, `safety gate`
- [ ] Check figure captions, appendix text, any companion .txt files
- [ ] Current main text is mostly clean ✓ (only "manufacturing tolerances" in 3.1, which is OK)
- [ ] Ensure cover letter and any response letter do NOT revert to RPHA language

### P5.2 Data & Code Availability Statement
- [ ] Decide: which data can be shared openly?
- [ ] Decide: which code can be shared (GitHub)?
- [ ] Decide: what needs "available upon request"?
- [ ] Draft availability statement

### P5.3 Cover Letter
- [ ] Must include boundary statement vs prior works
- [ ] Must not use threshold/engineering-guidance framing

---

## Completion Tracker

| Item | Status | Date completed | Notes |
|------|--------|---------------|-------|
| P1.1 Boundary statement | ✅ | 2026-04-19 | EN+CN inserted after intro para 4, cites [9] and [14] |
| P1.2 Numerical alignment | ✅ | 2026-04-19 | All fixed: coverage 0.861, coupling ≈30%, keff 77 pcm, acceptance 0.58–0.63, R̂ max=1.010 (4-chain rerun complete) |
| P1.3 Figure 1 restructure | ✅ | 2026-04-19 | Probabilistic arrows now radiate FROM BNN (not Outputs); regenerated |
| P1.4 Figure 5/6 restructure | ✅ | 2026-04-19 | 3-panel (A:marginals B:joint-posterior C:predictive) complete; E4_joint_posterior bank plot created; trace/Rhat/ESS → figE appendix |
| P2.1 k_eff R² defense | ✅ | 2026-04-19 | Added to Section 2.1 (σ≈0.0007, pivot to CRPS) |
| P2.2 Phy-mono pivot | ✅ | 2026-04-19 | Discussion 3.2 rewritten with correct MPIW 40.2→39.4 |
| P2.3 External baseline | ✅ | 2026-04-19 | Added MC-Dropout/DE CRPS comparison to Section 2.1 |
| P2.4 MCMC diagnostics | ✅ | 2026-04-19 | R̂ < 1.02 (max 1.010) sentence added to §2.4; Methods 4.6 already says 4 chains |
| P3.1 Internal labels | ✅ | 2026-04-19 | Removed bnn-phy-mono, bnn-data-mono-ineq, bnn-baseline-homo |
| P3.2 Results 2.3 upgrade | ✅ | 2026-04-19 | Information-channel headline + calibration implication |
| P3.3 Results 2.4 coherence | ✅ | 2026-04-19 | Added contraction-direction ↔ Sobol-dominant-direction sentence |
| P3.4 Discussion 3.3 upgrade | ✅ | 2026-04-19 | Channel-separation opening + "information-channel-aware" framing |
| P3.5 Methods gaps | ✅ | 2026-04-19 | 4.5: Saltelli/N_S/50 reps already present; 4.6: 4 chains/8000/burn-in/thin already present |
| P3.6 Missing refs | ✅ | 2026-04-19 | Added [14]NPE, [15]Lakshminarayanan, [16]K&O, [17]Sudret, [18]Raissi, [19]Karniadakis; cited in Intro + 2.4 |
| P3.7 OOD guard | ✅ | 2026-04-19 | Verified: §3.5 frames as degradation (R²→0.31), not improvement |
| P4.1 Figure 2 polish | ✅ | 2026-04-19 | Reviewed: calibration+PIT+CRPS/ECE panels look clean, stress has visual dominance |
| P4.2 Figure 3 strengthen | ✅ | 2026-04-19 | Reviewed: Δμ annotation visible, coupling shift clear, k_eff not subordinate |
| P4.3 Figure 4 sharpen | ✅ | 2026-04-19 | Reviewed: stress vs k_eff side-by-side already frames as separation; CI-small bars de-emphasized |
| P4.4 Supp figure audit | ✅ | 2026-04-19 | figA2 confirmed duplicate of fig5, not referenced — exclude from submission; all other supp figs mapped to appendices |
| P5.1 Threshold backflow | ✅ | 2026-04-19 | Clean: no feasible/actionable/pass-fail/safety-gate; only legitimate "near-threshold" category label in appendix |
| P5.2 Data/code avail | ☐ | | |
| P5.3 Cover letter | ☐ | | |
