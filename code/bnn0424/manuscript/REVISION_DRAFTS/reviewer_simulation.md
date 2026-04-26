# Simulated Reviewer Reports — Pre-submission Stress Test

> Generated 2026-04-25 from manuscript_en.txt + supplementary_information_en.txt

---

## Reviewer 1: ML/UQ Specialist

### Major Concerns

**1. MFVI underestimates epistemic uncertainty — acknowledged but not quantified**
- Location: Methods (line ~656), Limitations not explicitly listed
- The paper acknowledges mean-field VI assumes factorised posteriors but only cites PICP/coverage as indirect evidence of adequacy.
- **Defense exists?** Partial. PICP 0.937-1.000 and coverage 0.861 are cited, but no direct comparison with a full-rank VI or HMC gold standard is provided.
- **Rating:** Partially addresses. Suggest adding a sentence: "A full-rank or low-rank variational posterior [ref] could tighten the epistemic estimate; our factorised approximation provides a lower bound on epistemic uncertainty."

**2. Optuna hyperparameter search — 30 trials on validation RMSE only**
- Location: Methods (line ~645)
- 30 trials is reasonable, but optimising only on validation RMSE may not optimise distributional quality (CRPS, ECE).
- **Defense exists?** No explicit defense. Table S2 reports hyperparameters but not the sensitivity of CRPS/ECE to Optuna choices.
- **Rating:** Insufficient. Add 1 sentence noting that post-hoc CRPS evaluation confirmed the RMSE-selected architecture also performs well on distributional metrics.

**3. Deep ensemble comparison uses a single run vs 5-seed BNN**
- Location: Table 1, Results 2.1 (line ~211)
- The BNN reports mean±std across 5 seeds; DE and MC-D are single runs. This asymmetry weakens the comparison.
- **Defense exists?** Partially — the text notes "single run" in Table 1 caption.
- **Rating:** Partially addresses. The 5-seed BNN std (±0.008 for R²) is small enough that the comparison is informative, but a reviewer may still flag this.

**4. ECE values not shown in Table 1 for all baselines**
- Location: Table 1 (lines ~230-242)
- ECE is listed for BNN but not for MC-D/DE on k_eff, wall, monolith outputs.
- **Defense exists?** No.
- **Rating:** Minor. Consider adding a note: "ECE computed only on outputs where all methods produce distributional predictions."

### Minor
- The claim "five to six times lower ECE" (line ~215) should specify the exact numbers in parentheses.

---

## Reviewer 2: Nuclear Engineer

### Major Concerns

**1. "Decoupled" baseline is misleading — it's the first Picard iteration**
- Location: Results 2.2 (line ~258), Methods (line ~623), Limitation (v) (line ~577)
- The paper now clearly defines this as "single-pass (first Picard iteration, before multi-physics feedback)" and Limitation (v) explicitly acknowledges the distinction.
- **Defense exists?** Yes — Methods, Results, and Limitation (v) all address this.
- **Rating:** Adequate. The three-location defense is thorough.

**2. Only 8 monolith parameters — fuel and heat-pipe properties fixed**
- Location: Methods (line ~598-604)
- Fixing fuel thermal conductivity and heat-pipe BCs may miss important coupled uncertainties.
- **Defense exists?** Yes — "preliminary one-at-a-time sensitivity screening showed negligible influence" (line ~603) + Note E.
- **Rating:** Adequate, if the screening results are in Note E. Verify Note E contains the OAT screening data.

**3. Synthetic-only calibration — no real data**
- Location: Results 2.4 (line ~371-373), Limitation (iii) (line ~562-571)
- The paper explicitly calls this a "closed computational loop" and states coverage "characterises self-consistency rather than robustness to model-form error."
- **Defense exists?** Yes — Limitation (iii) is the strongest defense in the paper.
- **Rating:** Adequate. The honesty here is a strength.

**4. 30% coupling damping — physical mechanism not fully explained**
- Location: Discussion (line ~448-452)
- The paper attributes it to "negative neutronic-thermal feedback" but doesn't provide a quantitative decomposition of the feedback mechanism.
- **Defense exists?** Partial — the direction is stated but not decomposed.
- **Rating:** Partially addresses. Consider adding: "A detailed feedback-pathway decomposition is beyond the scope of this surrogate-focused study but would complement the statistical findings."

### Minor
- The "3-5 iterations" convergence claim (line ~622) should cite convergence evidence (e.g., residual norms).

---

## Reviewer 3: Statistician

### Major Concerns

**1. 90%-CI coverage = 0.861 is below the nominal 0.90 — is the BNN miscalibrated?**
- Location: Results 2.4 (line ~392), Limitation (vi) (line ~581)
- The shortfall is entirely in low-stress cases (0.667). Near-threshold (1.000) and high-stress (0.917) are adequate.
- **Defense exists?** Yes — Results 2.4 provides stratified coverage, and Limitation (vi) explains the information-theoretic root cause.
- **Rating:** Adequate. The stratified analysis and root-cause attribution are exactly what a statistician would want to see.

**2. 4/8 parameters fixed in calibration — identifiability concern**
- Location: Results 2.4 (line ~362-369), Limitation (ii) (line ~558-561)
- Fixing 4 parameters at true values is a strong simplification. In practice, true values are unknown.
- **Defense exists?** Yes — Limitation (ii) explicitly acknowledges this and states that 8-parameter calibration "would require additional independent observations."
- **Rating:** Adequate.

**3. MCMC diagnostics — R-hat 1.010 is fine, but ESS_min = 352 for how many parameters?**
- Location: Results 2.4 (line ~382-386)
- ESS 352 for a 4-parameter target is adequate (>50 per parameter). But the paper should clarify this is per-chain or bulk ESS.
- **Defense exists?** Partial — the numbers are stated but not explicitly flagged as bulk vs tail ESS.
- **Rating:** Partially addresses. Add "bulk ESS" qualifier.

**4. Sobol CI interpretation — CI spanning zero used correctly?**
- Location: Results 2.3 (Table 3), SI Table S4
- The paper correctly reports only factors with CI lower bound > 0 in the main text (Table 3 note). This is good practice.
- **Defense exists?** Yes — Table 3 caption states "Only factors with CI lower bound > 0 are shown."
- **Rating:** Adequate.

**5. Temperature Sobol indices at R² ~ 0.60 — surrogate error propagation**
- Location: Results 2.3 (line ~320-324)
- The paper adds caution: "should be interpreted with more caution; the first-order rankings are corroborated by rank-based methods (Table S15)."
- **Defense exists?** Yes — cross-method validation + explicit caution statement.
- **Rating:** Adequate.

---

## Summary: Pre-submission Readiness

| Concern | Reviewer | Defense Status |
|---------|----------|---------------|
| Decoupled baseline definition | R2 | ✅ Adequate (3 locations) |
| Synthetic-only calibration | R2 | ✅ Adequate (Lim iii) |
| Coverage 0.861 stratification | R3 | ✅ Adequate (Lim vi) |
| 4/8 params fixed | R3 | ✅ Adequate (Lim ii) |
| Sobol CI interpretation | R3 | ✅ Adequate (Table 3 note) |
| Temperature Sobol caution | R3 | ✅ Adequate (cross-method) |
| 8 params only monolith | R2 | ✅ Adequate (OAT screening) |
| MFVI underestimation | R1 | ⚠️ Partial (add 1 sentence) |
| Optuna RMSE-only objective | R1 | ⚠️ Needs 1 sentence |
| DE single-run asymmetry | R1 | ⚠️ Partial (caption notes it) |
| Coupling mechanism detail | R2 | ⚠️ Partial (add 1 sentence) |
| ESS bulk vs tail | R3 | ⚠️ Minor (add qualifier) |

**Verdict**: 7/12 concerns adequately defended. 5 need minor additions (1 sentence each). No blocking gaps found.
