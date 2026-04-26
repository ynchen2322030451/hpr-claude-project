# v3418 Canonical Data Summary — Single Source of Truth

> **All manuscript numerical values must match this document.**
> Any discrepancy between this file and manuscript text is a bug in the manuscript.
>
> **Last data update**: 2026-04-19 (all experiments complete except optional items)
> **Last manuscript check**: 2026-04-20 (all 4 nc_draft files verified; writing upgrade from 0414_v4 applied)

---

## How to use this document

1. **Writing/editing manuscripts**: look up every number here before inserting it into
   draft_paper, manuscript_en, manuscript_bilingual, or supplementary information files.
2. **After running new experiments**: update this file FIRST, then propagate to manuscripts.
3. **Manuscript update checklist**: search each section header in all manuscript files;
   verify numbers match. Record the check date in "Last manuscript check" above.

### Manuscript files that must stay in sync

| File | Location |
|------|----------|
| `manuscript_en.txt` | `manuscript/nc_draft/en/` |
| `manuscript_bilingual.txt` | `manuscript/nc_draft/bilingual/` |
| `supplementary_information_en.txt` | `manuscript/nc_draft/en/` |
| `supplementary_information_bilingual.txt` | `manuscript/nc_draft/bilingual/` |
| `draft_paper_0414_v4.txt` | `manuscript/0414_v4/` (legacy, lower priority) |

---

## 0. Dataset & Split

| Field | Value | Source |
|-------|-------|--------|
| Raw CSV rows | 3418 | `dataset_v3_updated.csv` |
| After NaN filter | 3341 | `results_v3418/fixed_split/split_meta.json` |
| n_train | 2339 | split_meta.json |
| n_val | 501 | split_meta.json |
| n_test | 501 | split_meta.json |
| Split seed | 2026 | split_meta.json |
| Rerun tag | v3418 | split_meta.json |
| Input parameters | 8 (E_slope, E_intercept, nu, alpha_base, alpha_slope, SS316_T_ref, SS316_k_ref, SS316_alpha) | |
| Output columns | 15 (7 iter1 + 8 iter2) | |
| Primary coupled outputs | 5 (stress, keff, fuel_temp, monolith_temp, wall2) | |

**Paper wording**: "n = 3418 samples" (raw), split into train/val/test = 2339/501/501

---

## 1. Model Naming Convention

| Internal ID | Paper term | Role |
|-------------|-----------|------|
| bnn-phy-mono | Physics-regularized BNN / Physics-regularized surrogate | **Main model** |
| bnn-baseline | Reference surrogate / Reference BNN | Main comparison |
| bnn-baseline-homo | Homoscedastic ablation | Ablation (SI) |
| bnn-mf-hybrid | Multi-fidelity hybrid | Ablation (SI) |
| mc-dropout | MC-Dropout | External baseline |
| deep-ensemble | Deep Ensemble (5-member) | External baseline |

---

## 2. Fixed-Split Accuracy (Single Best Model)

**Source**: `results_v3418/models/<model>/fixed_eval/metrics_per_output_fixed.csv`

### 2a. Physics-regularized BNN (bnn-phy-mono)

| Output | R^2 | RMSE | MAE | PICP | MPIW | CRPS |
|--------|-----|------|-----|------|------|------|
| stress | 0.9438 | 7.390 MPa | 5.438 MPa | 0.9860 | 39.38 | 4.350 |
| keff | 0.8492 | 0.000278 | 0.000212 | 0.9741 | 0.00132 | 0.000161 |
| fuel_temp | 0.6278 | 4.054 K | 3.071 K | 0.9441 | 15.87 | 2.248 |
| monolith_temp | 0.6269 | 4.585 K | 3.473 K | 0.9461 | 17.71 | 2.540 |
| wall2 | 0.9974 | 0.00121 | 0.000949 | 1.000 | 0.0200 | 0.00151 |

### 2b. Reference BNN (bnn-baseline)

| Output | R^2 | RMSE | MAE | PICP | MPIW | CRPS |
|--------|-----|------|-----|------|------|------|
| stress | 0.9418 | 7.524 MPa | 5.661 MPa | 0.9900 | 40.21 | 4.424 |
| keff | 0.8445 | 0.000282 | 0.000215 | 0.9581 | 0.00139 | 0.000168 |
| fuel_temp | 0.6274 | 4.056 K | 3.102 K | 0.9461 | 15.39 | 2.249 |
| monolith_temp | 0.6267 | 4.586 K | 3.505 K | 0.9401 | 17.43 | 2.541 |
| wall2 | 0.9944 | 0.00177 | 0.001272 | 1.000 | 0.0186 | 0.00149 |

### 2c. Homoscedastic ablation (bnn-baseline-homo)

| Output | R^2 | RMSE | PICP | MPIW | CRPS |
|--------|-----|------|------|------|------|
| stress | 0.9402 | 7.625 MPa | 0.9920 | 45.17 | 4.683 |
| keff | 0.8327 | 0.000292 | 1.000 | 0.00411 | 0.000318 |
| fuel_temp | 0.6263 | 4.062 K | 0.9401 | 15.71 | 2.248 |
| monolith_temp | 0.6263 | 4.589 K | 0.9421 | 17.70 | 2.537 |
| wall2 | 0.9910 | 0.00224 | 1.000 | 0.0319 | 0.00245 |

### 2d. Multi-fidelity hybrid (bnn-mf-hybrid)

| Output | R^2 | RMSE | PICP | MPIW | CRPS |
|--------|-----|------|------|------|------|
| stress | 0.9417 | 7.532 MPa | 0.9920 | 47.80 | 4.772 |
| keff | 0.8110 | 0.000311 | 0.9940 | 0.00217 | 0.000215 |
| fuel_temp | 0.6194 | 4.099 K | 0.9621 | 18.56 | 2.350 |
| monolith_temp | 0.6313 | 4.558 K | 0.9521 | 18.78 | 2.548 |
| wall2 | 0.9918 | 0.00214 | 1.000 | 0.0322 | 0.00241 |

### 2e. External baselines (trained on v3418 split)

**Source**: `results_v3418/models/{mc-dropout,deep-ensemble}/fixed_eval/metrics_fixed.json`

| Model | Overall R^2 mean | Overall RMSE mean | stress R^2 | keff R^2 | fuel_temp R^2 | stress RMSE |
|-------|------------------|-------------------|-----------|---------|---------------|-------------|
| MC-Dropout | 0.7669 | 4.727 | 0.9479 | 0.8273 | 0.6264 | ~7.66 MPa |
| Deep Ensemble | 0.7783 | 4.501 | 0.9531 | 0.8341 | 0.6431 | ~7.64 MPa |

**Note**: per-output RMSE/CRPS not directly available in metrics_fixed.json;
stress CRPS values from external_baseline_scoring.csv (if available) or
phase1_evidence_v4.md: MC-D CRPS=4.52, DE CRPS=4.50.

### 2f. Cross-model comparison table (for manuscript Table 1 / ablation table)

| Model | stress R^2 | stress CRPS | keff R^2 | Overall R^2 |
|-------|-----------|------------|---------|-------------|
| BNN-phy-mono | **0.9438** | **4.350** | **0.8492** | — |
| BNN-baseline | 0.9418 | 4.424 | 0.8445 | — |
| BNN-homo | 0.9402 | 4.683 | 0.8327 | — |
| BNN-mf-hybrid | 0.9417 | 4.772 | 0.8110 | — |
| MC-Dropout | 0.9479 | 4.52 | 0.8273 | 0.7669 |
| Deep Ensemble | 0.9531 | 4.50 | 0.8341 | 0.7783 |

---

## 3. 5-Seed Repeat Evaluation

**Source**: `results_v3418/models/<model>/repeat_eval/`
**Method**: Single checkpoint evaluated on 5 different random splits (seeds 2026-2030)

### 3a. All-output mean (15 outputs averaged)

| Model | RMSE (mean +/- std) | R^2 (mean +/- std) | CRPS (mean +/- std) | PICP (mean +/- std) |
|-------|--------------------|--------------------|--------------------|--------------------|
| bnn-baseline | 3.42 +/- 0.14 | 0.744 +/- 0.048 | 1.97 +/- 0.07 | 0.976 +/- 0.005 |
| bnn-phy-mono | 3.41 +/- 0.13 | 0.747 +/- 0.050 | 1.92 +/- 0.07 | 0.970 +/- 0.006 |

### 3b. Per-output (bnn-phy-mono, 5 seeds)

| Output | R^2 (mean +/- std) | RMSE (mean +/- std) | PICP (mean +/- std) | CRPS (mean +/- std) |
|--------|--------------------|--------------------|--------------------|--------------------|
| stress | 0.935 +/- 0.008 | 7.74 +/- 0.40 MPa | 0.979 +/- 0.012 | 4.53 +/- 0.15 |
| keff | 0.803 +/- 0.057 | 0.0003 +/- 0.0001 | 0.977 +/- 0.004 | 0.0002 +/- 0.0000 |
| fuel_temp | 0.599 +/- 0.025 | 4.28 +/- 0.25 K | 0.938 +/- 0.015 | 2.36 +/- 0.14 |
| monolith_temp | 0.598 +/- 0.026 | 4.83 +/- 0.30 K | 0.938 +/- 0.017 | 2.65 +/- 0.17 |
| wall2 | 0.997 +/- 0.001 | 0.0013 +/- 0.0001 | 1.000 +/- 0.000 | 0.0015 +/- 0.0000 |

### 3c. Per-output (bnn-baseline, 5 seeds)

| Output | R^2 (mean +/- std) | RMSE (mean +/- std) |
|--------|--------------------|--------------------|
| stress | 0.939 +/- 0.010 | 7.54 +/- 0.51 MPa |
| keff | 0.803 +/- 0.063 | 0.0003 +/- 0.0001 |
| fuel_temp | 0.608 +/- 0.029 | 4.23 +/- 0.29 K |
| monolith_temp | 0.607 +/- 0.031 | 4.78 +/- 0.34 K |
| wall2 | 0.994 +/- 0.001 | 0.0017 +/- 0.0001 |

---

## 4. Forward UQ / Risk Propagation

**Source**: `results_v3418/experiments/risk_propagation/bnn-phy-mono/D1_nominal_risk.json`
**Method**: 20,000 LHS samples, 50 MC weight samples, predictive draws

### 4a. Coupled stress distribution (bnn-phy-mono)

| sigma_k | stress_mean (MPa) | stress_std (MPa) | P(>131 MPa) | keff_mean | keff_std |
|---------|------------------|-----------------|-------------|-----------|----------|
| 0.5 | 160.6 | 17.8 | 0.957 | 1.1036 | 0.000466 |
| **1.0** | **161.7** | **31.9** | **0.836** | **1.1035** | **0.000773** |
| 1.5 | 162.8 | 47.1 | 0.742 | 1.1035 | 0.00117 |
| 2.0 | 163.9 | 65.3 | 0.681 | 1.1035 | 0.00179 |

### 4b. Threshold sweep at sigma_k = 1.0

| Threshold (MPa) | P_exceed |
|-----------------|----------|
| 110 | 0.959 |
| 120 | 0.913 |
| **131** | **0.836** |
| 150 | 0.628 |
| 180 | 0.266 |
| 200 | 0.116 |

### 4c. Decoupled vs coupled stress (derived from D3_coupling.json)

| Quantity | Coupled | Decoupled |
|----------|---------|-----------|
| Stress mean | 161.7 MPa | 203.5 MPa |
| Stress std | 31.9 MPa | 45.5 MPa |
| Std reduction | — | **30%** |
| Mean reduction | — | ~41.8 MPa |

**Derivation**: D3_coupling.json provides pred_delta_mean = -41.79 MPa (iter2 - iter1)
and pred_var_ratio_2to1 = 0.490. Uncoupled mean = 161.7 + 41.8 = 203.5;
uncoupled_std = 31.9 / sqrt(0.490) = 45.5; reduction = 1 - 31.9/45.5 = 30%.

### 4d. keff coupled distribution

| sigma_k | keff_mean | keff_std | keff_std (pcm) |
|---------|-----------|----------|----------------|
| 0.5 | 1.10356 | 0.000466 | 47 |
| **1.0** | **1.10354** | **0.000773** | **77** |
| 1.5 | 1.10351 | 0.00117 | 117 |
| 2.0 | 1.10347 | 0.00179 | 179 |

### 4e. Cross-model P(>131 MPa) at sigma_k = 1.0

| Model | P(>131 MPa) |
|-------|-------------|
| bnn-baseline | 0.845 |
| bnn-phy-mono | 0.836 |
| bnn-baseline-homo | 0.834 |
| bnn-mf-hybrid | 0.834 |

---

## 5. Sobol Sensitivity Analysis

**Source**: `results_v3418/experiments/sensitivity/<model>/sobol_results.csv`
**Method**: Saltelli scheme, N_S = 4096, 50 replications, 90% CI

### 5a. Stress (iteration2_max_global_stress) — bnn-phy-mono

| Input | S1_mean | S1_CI_lo | S1_CI_hi | ST_mean | CI_spans_zero |
|-------|---------|----------|----------|---------|---------------|
| E_intercept | **0.579** | 0.574 | 0.583 | 0.597 | False |
| alpha_base | 0.169 | 0.164 | 0.173 | 0.184 | False |
| nu | 0.065 | 0.058 | 0.071 | 0.068 | False |
| SS316_k_ref | 0.051 | 0.046 | 0.056 | 0.066 | False |
| E_slope | 0.050 | 0.044 | 0.057 | 0.058 | False |
| alpha_slope | 0.027 | 0.021 | 0.032 | 0.034 | False |
| SS316_T_ref | 0.019 | 0.013 | 0.024 | 0.031 | False |
| SS316_alpha | 0.002 | -0.004 | 0.008 | 0.007 | **True** |

### 5b. keff (iteration2_keff) — bnn-phy-mono

| Input | S1_mean | S1_CI_lo | S1_CI_hi | ST_mean | CI_spans_zero |
|-------|---------|----------|----------|---------|---------------|
| alpha_base | **0.785** | 0.783 | 0.788 | 0.783 | False |
| alpha_slope | 0.179 | 0.171 | 0.187 | 0.186 | False |
| nu | 0.028 | 0.020 | 0.037 | 0.027 | False |
| All others | <0.01 | — | — | — | True |

### 5c. Key derived values for manuscript

- E_intercept: "~58% of first-order variance (S1 = 0.58)" -- 0.579 rounds to 0.58
- ST - S1 gap: 0.597 - 0.579 = 0.018, "~0.02" -- minimal interaction
- alpha_base stress: "~17%" -- 0.169
- alpha_base keff: "~79% (S1 = 0.79)" -- 0.785 rounds to 0.79
- alpha_slope keff: "~18%" -- 0.179

### 5d. Cross-model Sobol consistency

| Model | stress E_int S1 | keff alpha_base S1 |
|-------|-----------------|-------------------|
| bnn-baseline | 0.600 | 0.787 |
| bnn-phy-mono | 0.579 | 0.785 |
| bnn-mf-hybrid | 0.580 | 0.734 |

---

## 6. Posterior Calibration (MCMC)

**Source**: `results_v3418/experiments/posterior/bnn-phy-mono/rerun_4chain/benchmark_summary.csv`
**Method**: Metropolis-Hastings MCMC, 4 independent chains, 8000 iter, burn-in 2000, thin 5
**Cases**: 18 benchmark (6 low / 6 near / 6 high stress) from test split
**Parameters calibrated**: E_intercept, alpha_base, alpha_slope, SS316_k_ref (4 of 8)

### 6a. bnn-phy-mono (4-chain rerun — canonical)

| Metric | Value |
|--------|-------|
| R-hat max | **1.010** |
| R-hat mean | 1.003 |
| Acceptance rate range | 0.582 -- 0.632 |
| Acceptance rate mean | **0.606** |
| 90%-CI coverage | **0.861** (62/72) |
| n_posterior per case | 4800 (4 chains x 1200) |
| Coverage: low-stress | 0.708 (17/24) |
| Coverage: near-stress | 0.958 (23/24) |
| Coverage: high-stress | 0.917 (22/24) |

### 6b. Cross-model posterior comparison

| Model | Acceptance mean | 90%-CI coverage | low | near | high |
|-------|----------------|----------------|-----|------|------|
| bnn-baseline | 0.599 | 0.875 | 0.708 | 1.000 | 0.917 |
| bnn-phy-mono | 0.607 | 0.861 | 0.708 | 0.958 | 0.917 |
| bnn-mf-hybrid | 0.631 | 0.861 | 0.667 | 0.958 | 0.958 |

---

## 7. Computational Speed

**Source**: `results_v3418/experiments/computational_speedup/bnn-baseline/bnn_speed_benchmark.json`
**Note**: bnn-baseline architecture identical to bnn-phy-mono; speed benchmark not
separately run for phy-mono.

### 7a. BNN-baseline (= phy-mono architecture)

| Metric | Value |
|--------|-------|
| Single MC latency (50 MC samples) | **1.582 x 10^-2 s** |
| Batch per-sample latency | **1.65 x 10^-5 s** |
| Batch throughput | **6.05 x 10^4 samples/s** |
| HF baseline | **2266 s** |
| Speedup (single MC) | **1.43 x 10^5** |
| Speedup (batch per-sample) | **1.37 x 10^8** |

### 7b. MF-hybrid (for comparison)

| Metric | Value |
|--------|-------|
| Single MC latency | 5.34 x 10^-2 s |
| Batch per-sample latency | 5.67 x 10^-5 s |
| Speedup (single MC) | 4.25 x 10^4 |
| Batch throughput | 1.76 x 10^4 samples/s |

### 7c. Hardware

- AMD EPYC 9654 96-Core, 566 GB RAM, 2x RTX 5090
- HF baseline: mean of 3 runs, s.d. 1.34 s

---

## 8. OOD Generalization

**Source**: `results_v3418/experiments/generalization/bnn-phy-mono/ood_summary.csv`

### bnn-phy-mono

| OOD feature | In-dist R^2 | OOD R^2 | In-dist PICP | OOD PICP |
|-------------|------------|---------|-------------|----------|
| E_intercept | 0.676 | 0.764 | 0.965 | 0.974 |
| alpha_base | 0.686 | 0.660 | 0.963 | 0.982 |
| nu | 0.672 | 0.734 | 0.969 | 0.965 |
| alpha_slope | 0.668 | 0.810 | 0.963 | 0.978 |

**Key result**: keff R^2 degrades to ~0.31 for alpha_base OOD extrapolation
(from comprehensive_comparison_v3418.txt). All models maintain stress R^2 > 0.93
under extrapolation.

---

## 9. Physics Consistency

**Source**: `results_v3418/experiments/physics_consistency/bnn-phy-mono/`

| Test | Result |
|------|--------|
| Gradient sign correctness | 10/10 physics pairs correct |
| Physics-data agreement | 10/10 pairs agree |
| Monotonicity violation (high-confidence pairs) | 0% for all 4 BNN variants |
| SS316_alpha -> fuel_temp violation | 36-54% (weak/nonlinear relationship) |
| Ordering constraints (max >= avg temp) | 0% violation |
| Non-negativity (stress >= 0) | 0% violation |

---

## 10. Uncertainty Decomposition

**Source**: `results/uncertainty_decomposition/uncertainty_decomposition.csv` (non-v3418 path)

| Model | Stress epistemic fraction | Stress aleatoric fraction |
|-------|--------------------------|--------------------------|
| bnn-baseline | 0.300 | 0.700 |
| bnn-phy-mono | 0.314 | 0.686 |
| bnn-data-mono | 0.343 | 0.657 |
| bnn-data-mono-ineq | 0.285 | 0.715 |

**Paper wording**: "aleatoric uncertainty dominates (58-90% across outputs);
epistemic fraction ~30% for stress, ~42% for wall expansion"

---

## 11. Conformal Calibration

**Source**: `results_v3418/analysis/conformal_calibration.csv`

### bnn-phy-mono (all_eval subset)

| Output | Raw PICP_90 | Conformal PICP_90 | Raw MPIW | Conformal MPIW |
|--------|------------|-------------------|----------|----------------|
| stress | 0.984 | 0.869 | 39.0 | 20.9 |
| keff | 0.972 | 0.853 | 0.00130 | 0.000831 |
| fuel_temp | 0.932 | 0.920 | 15.75 | 13.03 |
| monolith_temp | 0.936 | 0.908 | 17.58 | 14.47 |
| wall2 | 1.000 | 0.904 | 0.0196 | 0.00382 |

**Near-threshold stress** (110-150 MPa region): conformal PICP = 0.943, MPIW = 18.5

---

## 12. Small-Sample Data Efficiency

**Source**: `results_v3418/experiments/small_sample/`

### bnn-baseline

| Fraction | n_train | stress R^2 | keff R^2 | fuel_temp R^2 | wall2 R^2 | Overall R^2 |
|----------|---------|-----------|---------|---------------|----------|------------|
| 0.2 | 467 | 0.928 | 0.820 | 0.608 | 0.986 | 0.744 |
| 0.4 | 935 | 0.939 | 0.822 | 0.615 | 0.989 | 0.753 |
| 0.6 | 1403 | 0.946 | 0.833 | 0.627 | 0.992 | 0.767 |
| 1.0 | 2339 | 0.942 | 0.845 | 0.627 | 0.994 | — |

### bnn-mf-hybrid

| Fraction | n_train | stress R^2 | keff R^2 | Overall R^2 |
|----------|---------|-----------|---------|------------|
| 0.2 | 467 | 0.911 | 0.684 | 0.719 |
| 0.4 | 935 | 0.935 | 0.756 | 0.748 |
| 0.6 | 1403 | 0.939 | 0.810 | 0.767 |
| 1.0 | 2339 | 0.942 | 0.811 | — |

**Paper wording**: "With only ~500 training samples (25% of full set), achieves
~96% of peak stress R^2 performance"

---

## 13. Retired Numbers (MUST NOT appear in any manuscript)

| Retired value | Correct value | Reason |
|---------------|---------------|--------|
| 3600 s HF cost | 2266 s | Old estimate |
| 2000 s HF cost | 2266 s | Old estimate |
| 1.3e7 speedup | 1.43e5 | Wrong architecture |
| 1.2e10 speedup | 1.37e8 | Wrong architecture |
| "6300 pcm" keff std | DELETE | Decoupled keff nonsense |
| "95-fold" keff compression | DELETE | No longer applicable |
| "183x" keff compression | DELETE | No longer applicable |
| n=2900 dataset | 3418 raw / 3341 filtered | v3418 dataset |
| 2029/436/435 split | 2339/501/501 | v3418 split |
| 0.917 coverage | 0.861 | Old 1-chain result |
| 28% coupling reduction | 30% | v3418 D3_coupling |
| 107 pcm keff std | 77 pcm | v3418 D1 at sigma_k=1.0 |
| 1.76e5 speedup | 1.43e5 | v3418 benchmark |

---

## 14. Key Numbers Quick Reference (for abstract/conclusion)

| Claim | Value | Manuscript rounding |
|-------|-------|-------------------|
| Stress R^2 | 0.9438 | "R^2 = 0.944" |
| Stress RMSE | 7.390 MPa | "7.39 MPa" |
| keff R^2 | 0.8492 | "R^2 = 0.849" |
| Stress CRPS (phy-mono) | 4.350 | "4.35" |
| Stress CRPS (MC-D) | 4.52 | "4.52" |
| Stress CRPS (DE) | 4.50 | "4.50" |
| Coupling std reduction | 30% | "approximately 30%" |
| Coupled stress mean/std | 161.7 / 31.9 MPa | "mean 161.7 MPa, std 31.9 MPa" |
| keff std (sigma_k=1) | 77 pcm | "~77 pcm" |
| E_intercept S1 | 0.579 | "~58% (S1 = 0.58)" |
| alpha_base keff S1 | 0.785 | "~79% (S1 = 0.79)" |
| 90%-CI coverage | 0.861 | "0.861" |
| Acceptance rate | 0.58-0.63, mean 0.61 | "0.58 to 0.63" |
| R-hat max | 1.010 | "1.010" |
| Speedup (single MC) | 1.43e5 | "1.43 x 10^5" |
| Speedup (batch) | 1.37e8 | "1.37 x 10^8" |
| Throughput | 6.05e4 /s | "6.0 x 10^4 /s" |
| Single MC latency | 0.01582 s | "1.58 x 10^-2 s" |
| Batch per-sample | 1.65e-5 s | "1.7 x 10^-5 s" |
| HF cost | 2266 s | "~2266 s" |
| Dataset size | 3418 | "n = 3418" |
| Test set size | 501 | "501 test samples" |

---

## 15. Data Provenance Chain

```
dataset_v3_updated.csv (n=3341 after NaN filter, raw=3418)
  |
  +-- results_v3418/fixed_split/ (seed=2026, 2339/501/501)
       |
       +-- models/
       |     +-- bnn-{baseline,phy-mono,baseline-homo,mf-hybrid}/
       |     |     +-- artifacts/checkpoint_*_fixed.pt
       |     |     +-- fixed_eval/metrics_per_output_fixed.csv   <-- Section 2
       |     |     +-- repeat_eval/repeat_summary.csv            <-- Section 3
       |     +-- {mc-dropout,deep-ensemble}/
       |     |     +-- fixed_eval/metrics_fixed.json             <-- Section 2e
       |     +-- external_baselines_summary.json
       |
       +-- experiments/
       |     +-- risk_propagation/<model>/D1_nominal_risk.json   <-- Section 4
       |     +-- risk_propagation/<model>/D3_coupling.json       <-- Section 4c
       |     +-- sensitivity/<model>/sobol_results.csv           <-- Section 5
       |     +-- posterior/<model>/benchmark_summary.csv          <-- Section 6
       |     +-- posterior/bnn-phy-mono/rerun_4chain/             <-- Section 6a (canonical)
       |     +-- generalization/<model>/ood_summary.csv          <-- Section 8
       |     +-- computational_speedup/<model>/bnn_speed_*.json  <-- Section 7
       |     +-- small_sample/<model>/frac_*/metrics.json        <-- Section 12
       |     +-- physics_consistency/bnn-phy-mono/               <-- Section 9
       |
       +-- analysis/
             +-- comprehensive_comparison_v3418.txt              <-- overview
             +-- conformal_calibration.csv                       <-- Section 11
             +-- near_threshold_calibration.csv
```

---

*This document supersedes all previous evidence-binding files (phase1_evidence_v4.md,
phase1_evidence_v3_reference.md). When in doubt, read the source CSV/JSON directly.*
