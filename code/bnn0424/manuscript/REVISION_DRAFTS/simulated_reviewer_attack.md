# Simulated Reviewer Attack — Phase 5.2

> Generated 2026-04-24. Purpose: identify remaining weak points before submission.

---

## Reviewer 1 — ML/UQ Specialist

### Major concerns

**M1.1 — MFVI quality not validated.**
The BNN uses mean-field variational inference, which assumes factored posteriors and
is known to underestimate posterior uncertainty. No comparison to HMC or full-rank
variational inference is provided. The 5-seed repeat shows R² std of 0.008 on stress,
but this captures seed-level, not posterior-approximation-level uncertainty.

> **Current defense**: None explicit. **Fix**: Add 1-2 sentences in Methods or SI
> acknowledging MFVI limitation: "Mean-field VI assumes factorised weight posteriors
> and may underestimate epistemic uncertainty; however, the calibration metrics
> (PICP 0.937-1.000) and posterior coverage (0.861) suggest adequate uncertainty
> quantification for the present application."

**M1.2 — Optuna 30 trials may be insufficient.**
30 trials over 11 hyperparameters is a sparse search. How sensitive are the
results to the chosen hyperparameters?

> **Current defense**: 5-seed repeat shows stability. **Status**: Adequate — the
> 5-seed repeat (Table 1 std columns) shows the results are not an artifact of a
> single lucky hyperparameter set.

### Minor concerns

**m1.1 — Table 1 missing keff/wall for external baselines.**
MC-Dropout and Deep Ensemble rows only show fuel_temp and stress. The reader
cannot compare keff or wall expansion across methods.

> **Fix**: Add a note: "External baselines were evaluated on all 15 outputs;
> only stress and fuel temperature are shown for brevity. Full results in
> Supplementary Table S3." Or add the missing rows.

**m1.2 — ECE definition not given.**
ECE is reported in Table 1 and text but never defined in Methods or SI.

> **Fix**: Add ECE definition to Methods or SI Note A.

**m1.3 — "CRPS is lowest on all five outputs" claim.**
Table 1 only shows CRPS for BNN. External baselines show CRPS only for
fuel_temp and stress. The claim cannot be verified from the table alone.

> **Fix**: Either show CRPS for all outputs for all methods, or soften to
> "CRPS is lowest on stress and fuel temperature."

---

## Reviewer 2 — Nuclear Engineer

### Major concerns

**M2.1 — Single-pass baseline is not physically meaningful.**
The "single-pass (pre-feedback)" is the first Picard iteration, which retains
coupled geometry at initial condition. This is neither a true uncoupled solve
nor a converged coupled solve. The 30% reduction is not directly interpretable
as "coupling effect."

> **Current defense**: Limitation (v) acknowledges this explicitly. Methods
> defines the baseline precisely. **Status**: Adequately defended.

**M2.2 — Only 8 of potentially dozens of uncertain parameters.**
Fuel conductivity, heat pipe thermal resistance, gap conductance, and many
other parameters are fixed. How do the authors know these don't matter?

> **Current defense**: Methods states "preliminary one-at-a-time sensitivity
> screening showed negligible influence... (Supplementary Note E)." **Status**:
> Adequate if Note E contains the screening data. **Check**: Verify Note E
> actually has this screening data.

**M2.3 — No experimental validation.**
All results use synthetic data from the same solver. This is acknowledged in
Limitation (iii), but a nuclear engineer may view this as a fundamental flaw.

> **Current defense**: Limitation (iii) + Methods closed-loop statement +
> Outlook mentions real data as future work. **Status**: Adequately defended
> for a methods paper. The honest framing helps.

### Minor concerns

**m2.1 — Picard convergence criteria not in main text.**
How many iterations does convergence typically require? What is the convergence
tolerance?

> **Fix**: Add "typically 3-5 iterations" or similar to Methods, or ensure
> Note E has this.

**m2.2 — ±10% uniform prior justification.**
Why 10% and not 5% or 20%? Is this based on actual manufacturing data?

> **Current defense**: "representing representative manufacturing and handbook-
> data variability" — somewhat circular. **Fix**: Could add a citation to
> handbook data or state "in the absence of component-specific characterisation
> data, ±10% is a conventional engineering margin."

---

## Reviewer 3 — Statistician

### Major concerns

**M3.1 — 4 of 8 parameters fixed at true values in calibration.**
This is a significant simplification. The posterior contraction results may
not hold when all 8 parameters are free, especially if correlations exist
between fixed and calibrated parameters.

> **Current defense**: Limitation (ii) acknowledges this. Results state the
> scope covers Sobol-dominant parameters. **Status**: Adequately defended.

**M3.2 — ESS min = 352 may be low.**
352 effective samples for 4-parameter posterior may be marginal for reliable
posterior summaries, especially for tail quantiles.

> **Current defense**: R-hat max = 1.010, acceptance 0.58-0.63. **Fix**: Could
> add: "ESS > 300 provides reliable estimation of posterior means and 90% CIs
> [ref], though tail quantiles beyond the 95th percentile should be interpreted
> with caution."

**M3.3 — Coverage 0.708 for low-stress cases is concerning.**
Missing 29% of 90% CIs in a specific regime suggests systematic bias, not
random variation.

> **Current defense**: Limitation (vi) diagnoses alpha_slope as the weak
> parameter. Results §2.4 reports stratified coverage. **Status**: Adequately
> defended — the honest reporting and diagnosis prevent this from being a
> rejection issue.

### Minor concerns

**m3.1 — "90% CI" vs "90% credible interval."**
The posterior intervals are Bayesian credible intervals, not frequentist
confidence intervals. The text uses "90%-CI" which could confuse.

> **Fix**: Clarify "90% posterior credible interval" on first use.

**m3.2 — Sobol CI construction.**
The 90% CI from 50 replications uses percentiles (empirical), not bootstrap.
This is fine but should be stated explicitly.

> **Current defense**: SI Note B.4 describes this. **Status**: OK.

---

## Summary: Items to fix before submission

| Priority | Issue | Fix type |
|----------|-------|----------|
| HIGH | m1.2 ECE definition missing | Add to Methods/SI |
| HIGH | m1.3 CRPS claim too broad | Soften language or add data |
| MED | M1.1 MFVI limitation | Add 1-2 sentences |
| MED | m2.2 ±10% justification | Strengthen wording |
| MED | m3.1 CI vs credible interval | Terminology fix |
| LOW | m1.1 Table 1 incomplete | Add note or rows |
| LOW | m2.1 Picard iterations | Add number to Methods |
| LOW | M3.2 ESS interpretation | Add qualification |

All major concerns (M-level) have existing defenses in the current manuscript.
No new experiments are needed to address reviewer concerns.
