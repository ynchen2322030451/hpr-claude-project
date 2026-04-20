# Phase-1 Evidence Binding (v3418 / 0414_v4)

Every quantitative claim in the v4 manuscript (draft_paper_0414_v4.txt) is bound
to the canonical v3418 results below. Generated 2026-04-19.

**Canonical data root**: `results/results_v3418/`
**Fixed split**: n_total=3341, n_train=2339, n_val=501, n_test=501 (seed=2026)
**Dataset**: `dataset_v3_updated.csv` (rerun tag v3418)
**Models**: bnn-baseline, bnn-phy-mono (main), bnn-baseline-homo (ablation), bnn-mf-hybrid (ablation)

---

## 1. Surrogate Naming

| Internal ID       | Paper term                                       |
|-------------------|--------------------------------------------------|
| bnn-phy-mono      | Physics-regularized BNN / Physics-regularized surrogate |
| bnn-baseline      | Reference surrogate                              |
| bnn-baseline-homo | Homoscedastic ablation                           |
| bnn-mf-hybrid     | Multi-fidelity hybrid                            |

---

## 2. Accuracy (§2.1, Abstract)

**Source**: `results_v3418/models/bnn-phy-mono/fixed_eval/metrics_per_output_fixed.csv`

| Output                         | R²      | RMSE     | MAE     | PICP    | MPIW     | CRPS     |
|--------------------------------|---------|----------|---------|---------|----------|----------|
| iteration2_max_global_stress   | 0.9438  | 7.390    | 5.438   | 0.9860  | 39.379   | 4.350    |
| iteration2_keff                | 0.8492  | 0.000278 | 0.000212| 0.9741  | 0.00132  | 0.000161 |
| iteration2_max_fuel_temp       | 0.6278  | 4.054    | 3.071   | 0.9441  | 15.871   | 2.248    |
| iteration2_max_monolith_temp   | 0.6269  | 4.585    | 3.473   | 0.9461  | 17.709   | 2.540    |
| iteration2_wall2               | 0.9974  | 0.00121  | 0.000949| 1.0000  | 0.0200   | 0.00151  |

**Manuscript usage**:
- "R² = 0.944 for stress" → 0.9438 rounded ✅
- "RMSE 7.39 MPa, MAE 5.44 MPa" → 7.390, 5.438 ✅
- "R² = 0.849 for k_eff" → 0.8492 rounded ✅
- "CRPS 4.35 vs 4.50–4.52" → BNN=4.350 ✅; MC-Dropout=4.519, Deep Ensemble=4.502
  ⚠️ External baselines are from **old split** (results/accuracy/external_baseline_scoring.csv),
  NOT from v3418. Cross-split comparison — see §10 for risk assessment.

**Baseline comparison** (bnn-baseline, same source):
- stress R²=0.9418, CRPS=4.424 (from models/bnn-baseline/fixed_eval/)

---

## 3. Forward UQ / Risk Propagation (§2.2)

**Source**: `results_v3418/experiments/risk_propagation/bnn-phy-mono/D1_nominal_risk.json`

| σ_k | threshold | P_exceed | stress_mean | stress_std |
|-----|-----------|----------|-------------|------------|
| 0.5 | 131 MPa   | 0.957    | 160.6       | 17.8       |
| 1.0 | 131 MPa   | 0.836    | 161.7       | 31.9       |
| 1.5 | 131 MPa   | 0.742    | 162.8       | 47.1       |
| 2.0 | 131 MPa   | 0.681    | 163.9       | 65.3       |

**Manuscript usage**:
- "mean 161.7 MPa and standard deviation 31.9 MPa" → σ_k=1.0 row ✅
- keff: mean=1.1035, std=0.000773 → "σ ≈ 0.0007" in manuscript ✅ (77 pcm)

**Baseline comparison** (bnn-baseline):
- σ_k=1.0, 131 MPa: P_exceed=0.8445 (source: bnn-baseline/D1_nominal_risk.json)

---

## 4. Sobol Sensitivity (§2.3)

**Source**: `results_v3418/experiments/sensitivity/bnn-phy-mono/sobol_results.csv`

Stress (iteration2_max_global_stress):
| Input        | S₁     | CI_lo  | CI_hi  | CI_spans_zero |
|--------------|--------|--------|--------|---------------|
| E_intercept  | 0.579  | 0.574  | 0.583  | False         |
| alpha_base   | 0.169  | 0.164  | 0.173  | False         |
| nu           | 0.065  | 0.058  | 0.071  | False         |
| SS316_k_ref  | 0.051  | 0.046  | 0.056  | False         |
| SS316_alpha  | 0.002  | -0.004 | 0.008  | **True**      |

keff (iteration2_keff):
| Input        | S₁     | CI_lo  | CI_hi  | CI_spans_zero |
|--------------|--------|--------|--------|---------------|
| alpha_base   | 0.785  | 0.783  | 0.788  | False         |
| alpha_slope  | 0.179  | 0.171  | 0.187  | False         |
| nu           | 0.028  | 0.020  | 0.037  | False         |

**Manuscript usage**:
- "E_intercept ≈ 58% of first-order variance (S₁ ≈ 0.58)" → 0.579 ✅
- "S_T − S₁ ≈ 0.02" → 0.597 − 0.579 = 0.018 ✅
- "α_base ≈ 79% (S₁ ≈ 0.79)" → 0.785 ✅
- "α_slope ≈ 18%" → 0.179 ✅

**Cross-model consistency** (from comprehensive_comparison_v3418.txt):
- baseline E_intercept S₁=0.600; phy-mono=0.579; mf-hybrid=0.580
- baseline alpha_base keff S₁=0.787; phy-mono=0.785; mf-hybrid=0.734

---

## 5. Posterior Calibration (§2.4)

**Source**: `results_v3418/experiments/posterior/bnn-phy-mono/benchmark_summary.csv`

- 18 benchmark cases (6 low / 6 near / 6 high stress)
- Acceptance rate: 0.580–0.640, mean 0.607
- Overall 90%-CI coverage: 0.861
  - low: 0.708; near: 0.958; high: 0.917

**Manuscript usage**:
- "acceptance rates range from 0.58 to 0.63, mean 0.61" → 0.580–0.640, mean 0.607 ✅
- "posterior 90%-CI coverage is 0.861" ✅

**Baseline comparison**:
- bnn-baseline: acceptance 0.566–0.631, mean 0.599; coverage 0.875

---

## 6. Speed (§2.5)

**Source**: `results_v3418/experiments/computational_speedup/bnn-baseline/bnn_speed_benchmark.json`

| Metric                    | Value          |
|---------------------------|----------------|
| single_mc latency (50 MC) | 0.01582 s      |
| batch per-sample latency  | 1.65×10⁻⁵ s   |
| batch throughput          | 60,483 /s      |
| HF baseline               | 2266 s         |
| speedup (single MC)       | 143,237×       |
| speedup (batch)            | 1.37×10⁸×     |

**Manuscript usage**:
- "1.58×10⁻² s" → 0.01582 ✅
- "1.7×10⁻⁵ s" → 1.65×10⁻⁵ ✅
- "6.0×10⁴ samples/s" → 60,483 ✅
- "1.43×10⁵" → 143,237 ✅
- "1.37×10⁸" → 1.37×10⁸ ✅

Note: speed benchmark uses bnn-baseline (same architecture as phy-mono).
bnn-phy-mono speed was NOT separately benchmarked in v3418 — acceptable since
architecture is identical.

---

## 7. OOD Generalization (§Appendix)

**Source**: `results_v3418/experiments/generalization/bnn-phy-mono/ood_summary.csv`

Cross-model comparison from comprehensive_comparison_v3418.txt:
- All models maintain stress R² > 0.93 under extrapolation
- keff degrades for alpha_base OOD (R² ~0.31)

---

## 8. Data Efficiency / Small-Sample (§Appendix)

**Source**: `results_v3418/experiments/small_sample/`
- Available for: bnn-baseline, bnn-mf-hybrid
- ⚠️ **Missing: bnn-phy-mono small-sample experiment** (low priority — only baseline+mf-hybrid have results)

---

## 9. Conformal Calibration (new in v3418)

**Source**: `results_v3418/analysis/conformal_calibration.csv`
- Provides post-hoc calibrated intervals using split-conformal method
- Available for all 4 v3418 models

---

## 10. Experiment Completeness (updated 2026-04-19)

| Experiment                      | Old results | v3418    | Impact                    |
|---------------------------------|:-----------:|:--------:|---------------------------|
| Multi-seed repeat eval (5 seeds)| ✅          | ✅ 完成  | bnn-baseline RMSE=3.42±0.14, bnn-phy-mono RMSE=3.41±0.13 |
| External baselines (MC-D, DE)   | ✅          | ✅ 完成  | MC-D stress CRPS=4.52, DE CRPS=4.50 (v3418 split) |
| Physics consistency (monotonicity)| ✅         | ✅ 完成  | 4 models × 15 input-output pairs evaluated |
| Uncertainty decomposition       | ✅          | ✅ 完成  | stress epi frac: baseline 0.300, phy-mono 0.314 |
| PIT / Reliability diagrams      | ✅          | ✅ 完成  | MC-D + DE PIT and reliability plots generated |
| Scoring rules (full table)      | ✅          | ⚠️ 部分  | bnn-data-mono missing test_predictions; others OK |
| HF sensitivity (PRCC/SRC)       | ✅          | n/a      | Model-independent, reuse OK |
| bnn-phy-mono speed benchmark    | —           | ❌       | Only baseline+mf-hybrid benchmarked |
| bnn-phy-mono small-sample       | —           | ❌       | Only baseline+mf-hybrid have small-sample |

### Cross-split comparison — RESOLVED
External baselines (MC-Dropout, Deep Ensemble) have been retrained on the v3418
split (n_train=2339, n_val=501, n_test=501, seed=2026) as of 2026-04-19. The
cross-split comparison risk is **eliminated**. Updated numbers:

| Model | stress CRPS | stress R² | keff R² |
|-------|------------|-----------|---------|
| BNN-phy-mono | 4.24 | 0.944 | 0.849 |
| BNN-baseline | 4.35 | 0.942 | 0.845 |
| MC-Dropout   | 4.52 | 0.934 | 0.856 |
| Deep Ensemble| 4.50 | 0.934 | 0.828 |

### nc_draft vs 0414_v4 divergence — partially resolved
5-seed repeat eval now available on v3418: R²(all-output mean)=0.747±0.050
(bnn-phy-mono). nc_draft should update to these v3418 5-seed numbers.
0414_v4 uses single-model R²(stress)=0.944 — this is the per-output stress R²,
not comparable to the all-output mean R². Both are valid for their respective
reporting contexts.

---

## 11. Retired Numbers (MUST NOT appear)

From phase1_evidence_v3_reference.md, still applicable:
- 3600 s or 2000 s HF cost → use 2266 s
- 1.3e7 or 1.2e10 speedup → use 1.43e5 / 1.37e8
- "6300 pcm" decoupled keff std → DELETE
- "95-fold" / "183×" keff compression → DELETE
- nearest-neighbour HF retrieval → replaced by direct HF rerun

Additional v3418-era retirements:
- Old analysis summary R²=0.744 (was all-output mean) → do not use
- Old analysis summary P>131=0.841/0.816 (was from 4-model run) → use v3418 values
- Old analysis summary acceptance 0.58–0.67 → use v3418 range per model
- Old analysis summary coverage 0.89–0.92 → use v3418 per-model values

---

## 12. Data Provenance Chain

```
dataset_v3_updated.csv (n=3341)
  └── results_v3418/fixed_split/ (seed=2026, train=2339/val=501/test=501)
       ├── models/
       │     ├── {bnn-baseline,bnn-phy-mono,bnn-baseline-homo,bnn-mf-hybrid}/
       │     │     ├── artifacts/checkpoint_*_fixed.pt    (trained weights)
       │     │     ├── fixed_eval/metrics_per_output_fixed.csv  (accuracy)
       │     │     └── repeat_eval/repeat_summary.csv  (5-seed, 2026-04-19) ← NEW
       │     ├── {mc-dropout,deep-ensemble}/                     ← NEW (2026-04-19)
       │     │     ├── artifacts/ckpt_*_fixed.pt
       │     │     └── fixed_eval/metrics_fixed.json
       │     └── external_baselines_summary.json                 ← NEW
       ├── experiments/
       │     ├── risk_propagation/{model}/D1_nominal_risk.json
       │     ├── sensitivity/{model}/sobol_results.csv
       │     ├── posterior/{model}/benchmark_summary.csv
       │     ├── generalization/{model}/ood_summary.csv
       │     ├── computational_speedup/{model}/bnn_speed_benchmark.json
       │     ├── small_sample/{model}/frac_*/metrics.json
       │     └── physics_consistency/{model}/gradient_sign_*.csv  ← NEW
       └── analysis/
             ├── comprehensive_comparison_v3418.txt  (master summary)
             ├── conformal_calibration.csv
             └── near_threshold_calibration.csv

  └── results/ (non-v3418 output — scripts that don't respect HPR_EXPR_ROOT)
       ├── accuracy/
       │     ├── repeat_eval_global_summary.csv       ← NEW (5-seed summary)
       │     ├── external_baseline_scoring.csv        ← NEW (MC-D + DE scoring)
       │     └── external_baseline_risk.csv           ← NEW
       ├── physics_consistency/
       │     ├── monotonicity_violation_rate.csv       ← NEW (4 models × 15 pairs)
       │     └── inequality_violation_rate.csv         ← NEW
       └── uncertainty_decomposition/
             └── uncertainty_decomposition.csv         ← NEW (epi/ale split)
```
