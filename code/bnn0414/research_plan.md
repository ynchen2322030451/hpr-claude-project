# BNN0414 Research Plan & Checklist

> Created: 2026-04-18
> Context: consolidates GPT discussion analysis + independent Claude assessment
> Rule: wait for user confirmation before executing experiments

---

## Background

Current BNN surrogate (`BayesianMLP` in `bnn_model.py`) already has:
- **Weight-space Bayesian layers** (Blundell et al. 2015 reparameterization)
- **Heteroscedastic output heads**: `mu_head` (mean) + `logvar_head` (aleatoric)
- **Epistemic uncertainty** via MC forward passes (50 at eval, configurable)
- **4 model variants**: baseline, data-mono, phy-mono, data-mono-ineq
- **Physics regularization**: monotonicity (Spearman / physics-prior) + inequality constraints

Paper main comparison: **baseline vs phy-mono** (data-mono-ineq demoted to appendix ablation).

---

## Direction 1: Heteroscedastic BNN Deepening

### GPT assessment
GPT judged this as "already done" and not worth additional effort. The current model already captures aleatoric + epistemic uncertainty via the dual-head BNN.

### Claude assessment
**Agree — this is already implemented and working.** The `BayesianMLP` has `mu_head` + `logvar_head` with per-output learned aleatoric variance, plus weight-space uncertainty for epistemic. This is the standard heteroscedastic BNN architecture (Kendall & Gal 2017 style but with full Bayesian weights instead of MC Dropout).

No further deepening needed unless we want:
- Mixture density outputs (overkill for this problem)
- Deeper variance network (separate NN for variance — marginal gain, training instability risk)

### Verdict: **No action needed. Already the paper's core contribution.**

---

## Direction 2: Multi-Fidelity iter1 → iter2 Transfer Learning

### GPT assessment
GPT was enthusiastic about stacked/compositional multi-fidelity (Kennedy & O'Hagan style):
- Use iter1 (uncoupled pass) predictions as auxiliary inputs to predict iter2 (coupled steady state)
- Two approaches: (a) residual/discrepancy δ = iter2 − iter1, (b) stacked: iter2 = f(x, iter1_pred)
- GPT favored stacked approach for interpretability

### Claude assessment
**Partially agree, but with important caveats:**

1. **Physical justification is strong.** iter1 is the uncoupled thermal-mechanical pass; iter2 is the Picard-converged coupled response. The correction iter2 − iter1 is physically meaningful (coupling effect). This is genuine multi-fidelity, not just a trick.

2. **Implementation complexity is moderate.** For the stacked approach, need to:
   - Train an iter1-only surrogate (8→7, already a subset of current 8→15 model)
   - Use iter1 predictions as additional features for iter2 prediction (8+7→8 or 8+7→15)
   - Handle the information leakage carefully during training (iter1 predictions should come from a held-out model or cross-validation)

3. **Risk: diminishing returns.** Current BNN already achieves good accuracy on iter2 outputs directly. The marginal improvement from multi-fidelity may be small, and the added complexity hurts the paper's clarity.

4. **Difference from GPT:** GPT overestimated the novelty. Multi-fidelity surrogates (Perdikaris et al. 2017, Meng & Karniadakis 2020) are well-established. The contribution would be "applying multi-fidelity BNN to HPR coupled simulation" — valid but incremental.

5. **Practical concern:** iter1 and iter2 have different output dimensionality (7 vs 8 — iter2 includes keff). The DELTA_PAIRS in config only cover the 7 shared outputs. keff has no iter1 counterpart, so multi-fidelity doesn't help for keff prediction specifically.

### Verdict: **Worth a focused appendix experiment, but NOT main-text material.**

Priority: Medium. Implementation: 1–2 days.

### Implementation plan (if approved):
- [ ] Create `models/multifidelity/mf_bnn.py` — stacked BNN that takes (x, iter1_pred) → iter2
- [ ] Train iter1-only BNN on the 7 iter1 outputs
- [ ] Generate iter1 predictions for all samples (using cross-val or held-out model)
- [ ] Train stacked iter2 BNN with augmented inputs
- [ ] Compare test-set RMSE/NLL with single-fidelity baseline
- [ ] If improvement > 5% RMSE: include as appendix experiment
- [ ] If improvement < 5%: mention in text as "explored but marginal improvement"

---

## Direction 3: Conformal Prediction (Post-hoc Calibration)

### GPT assessment
GPT recommended split conformal prediction as a distribution-free calibration layer on top of BNN predictions. Provides guaranteed marginal coverage without retraining.

### Claude assessment
**Agree this is low-cost and high-value for the paper.**

1. **Why it matters for this paper:** BNN calibration varies across models — ECE ranges from 0.109 (baseline) to 0.135 (data-mono-ineq). Conformal prediction provides a distribution-free fallback that guarantees marginal coverage regardless of model quality.

2. **Implementation is trivial.** Split conformal on the calibration set (can reuse val set):
   - Compute nonconformity scores: |y_true − y_pred| / σ_pred (normalized residuals)
   - Find the (1−α)(1+1/n)-quantile of scores on calibration set
   - Apply to test set: prediction interval = y_pred ± q * σ_pred
   - Report coverage and interval width

3. **Difference from GPT:** GPT didn't emphasize the key nuance — conformal prediction gives **marginal** coverage (averaged over all test points), NOT conditional coverage. For risk-critical outputs like stress, marginal coverage can be misleading if the intervals are too wide on safe samples and too narrow on high-stress samples. We should report both marginal and conditional (binned by stress level) coverage.

4. **Paper positioning:** This belongs in the appendix as a "robustness check on UQ calibration" — showing that even without conformal post-processing, the BNN's native calibration is already reasonable.

### Verdict: **Do it. Appendix-level, 0.5 day implementation.**

### Implementation plan:
- [ ] Create `experiments_0404/experiments/run_conformal_0404.py`
- [ ] Use val set as calibration set, test set for evaluation
- [ ] Compute conformal intervals at α = 0.10, 0.05
- [ ] Report: marginal coverage, mean interval width, conditional coverage by stress bin
- [ ] Compare with BNN native prediction intervals (MC-based)
- [ ] Generate comparison figure: BNN interval vs conformal interval width

---

## Direction 4: Active Learning / Adaptive Sampling

### GPT assessment
GPT was lukewarm — said it's a "future work" item since the HF simulation budget is already spent and active learning requires iterative HF calls.

### Claude assessment
**Agree — this is clearly future work, not implementable now.**

1. Active learning requires an acquisition function (e.g., expected improvement, uncertainty-based) and iterative HF simulation calls. Our HF pipeline runs on the tjzs server with ~40 min/sample wall-clock time.

2. The 3418-sample dataset was generated by LHS + batch execution, not adaptively. Retrofitting active learning is not meaningful — it would be a simulation study ("what if we had used active learning?") rather than actual deployment.

3. **One thing we CAN do:** a retrospective analysis showing which regions of input space have high predictive uncertainty, as motivation for future adaptive sampling. This is essentially a visualization of the BNN's epistemic uncertainty map.

### Verdict: **Future work only. Mention in conclusions, no implementation.**

---

## Priority-Ordered Execution Plan

### Phase A: Rerun with v3418 dataset (BLOCKED — needs server)
- [ ] SSH to tjzs, sync updated code
- [ ] Run `rerun_v3418.py` with `pytorch-env` on server
- [ ] Verify results in `results_v3418/`
- [ ] Compare key metrics (RMSE, NLL, ECE) with original results

### Phase B: Conformal prediction experiment (can run locally with existing results)
- [ ] Implement `run_conformal_0404.py`
- [ ] Run on existing bnn0414 results (current split)
- [ ] Generate appendix figure
- [ ] Write appendix section draft

### Phase C: Multi-fidelity experiment (optional, after Phase A)
- [ ] Implement stacked BNN architecture
- [ ] Train and evaluate on v3418 split
- [ ] Assess if improvement justifies appendix inclusion
- [ ] If yes: write appendix section; if no: add one paragraph to conclusions

### Phase D: Paper integration
- [ ] Update manuscript with v3418 results
- [ ] Add conformal prediction appendix
- [ ] Add multi-fidelity appendix (if Phase C positive)
- [ ] Update conclusions with active learning as future work

---

## GPT vs Claude: Summary of Differences

| Direction | GPT | Claude | Key difference |
|-----------|-----|--------|----------------|
| Heteroscedastic BNN | Already done | Already done | Full agreement |
| Multi-fidelity | Enthusiastic, main-text worthy | Cautious, appendix-level | Claude flags diminishing returns + keff has no iter1 counterpart |
| Conformal prediction | Recommended | Recommended + conditional coverage caveat | Claude adds conditional-coverage nuance |
| Active learning | Future work | Future work | Full agreement |

---

## Status tracking

Last updated: 2026-04-18
Current phase: **Waiting for user confirmation before executing**
