# Figure 5: Observation-Conditioned Posterior Shift

## Purpose
Most important posterior figure. Show that:
**Observation-conditioned updating changes the inferred parameter distribution and shifts posterior predictive stress toward observation-compatible regimes.**

## Layout (3 panels)
- **(A) Prior vs posterior marginals** — 4 small sub-panels (one per calibrated parameter), showing prior density and posterior density overlaid
- **(B) Representative joint posterior** — E_intercept vs alpha_base (the compensation ridge)
- **(C) Posterior predictive stress vs observed/true stress** — Dot + CI for each of 18 cases

## Data Files in This Folder

### benchmark_summary_4chain.csv
18 benchmark cases x 4 calibrated parameters = 72 rows (from 4-chain MCMC rerun).
Columns: case_idx, row_idx, category, param, true_value, post_mean, post_std, post_lo_5, post_hi_95, in_90ci, bias, rel_bias, accept_rate, n_posterior, stress_true_MPa, rhat

Key diagnostics:
- R_hat max = 1.010 (all < 1.05, well-converged)
- Acceptance rates: 0.58-0.63
- n_posterior per chain = 4800 (4 chains x 1200 post-burn-in samples)

### benchmark_case_meta.json
18 cases with category and stress_true:
- 6 low-stress: 96.82-117.68 MPa
- 6 near-threshold: 121.44-130.23 MPa
- 6 high-stress: 133.18-198.38 MPa

### chain_samples_case0.npz, chain_samples_case7.npz, chain_samples_case12.npz
Raw MCMC chain samples (numpy arrays) for 3 representative cases.
- case 0: low stress (110.29 MPa)
- case 7: near threshold (121.44 MPa)
- case 12: high stress (134.96 MPa)
Use these for joint posterior contour plots (Panel B).

### prior_ranges.csv
Prior distribution ranges for the 4 calibrated parameters (uniform priors).

### Key Numbers

#### Coverage
- 90% CI coverage across 18 cases x 4 params = 72 checks
- in_90ci = True for 62/72 = 0.861

#### Per-case posterior summary (selected representative cases)
| Case | Category | Stress true | Accept rate | Coverage (4 params) |
|------|----------|-------------|-------------|---------------------|
| 0 | low | 110.29 MPa | 0.607 | 3/4 |
| 7 | near | 121.44 MPa | 0.592 | 4/4 |
| 12 | high | 134.96 MPa | 0.608 | 4/4 |
| 15 | high | 198.38 MPa | 0.595 | 4/4 |

#### Compensation ridge
E_intercept and alpha_base show a trade-off in the joint posterior:
sigma ~ E * alpha * DeltaT — multiplicative structure means the product E*alpha can remain invariant while individual values shift. This cross-coupling is visible only in the joint posterior, not in single-output calibration.

## Design Rules
- Panel A: 4 small density plots arranged as 2x2 or 1x4
  - Prior = flat uniform (light gray fill)
  - Posterior = peaked (colored line/fill)
  - Show for a representative case (e.g., case 12 = high stress)
- Panel B: 2D contour/scatter of E_intercept vs alpha_base
  - Show the compensation ridge (negative correlation)
  - Use case 12 or overlay multiple cases
- Panel C: Dot plot with 90% CI bars for all 18 cases
  - x-axis: case index (sorted by stress category)
  - y-axis: posterior predictive stress
  - Overlay true stress as a marker
  - Color by category (low/near/high)

## Do NOT include in main text
- Trace plots (-> Supplementary)
- R-hat / ESS tables (-> Supplementary)
- Coverage dot chart as main visual
- Feasible region / pass-fail / threshold gate narrative

## Parameter labels (paper-facing)
- E_intercept -> "$E$ intercept (Pa)"
- alpha_base -> "$\\alpha$ base (K$^{-1}$)"
- alpha_slope -> "$\\alpha$ slope (K$^{-2}$)"
- SS316_k_ref -> "$k$ reference (W/m/K)"

## Style
- Panel A: clean density overlays, no box frames
- Panel B: contour lines or scatter with density shading
- Panel C: error-bar dot plot, cases ordered left-to-right by category
- Consistent color scheme across panels
- English only, no CJK
- Figure size: ~170mm wide
