# Figure 2: Surrogate Predictive Behaviour

## Purpose
Show why BNN is chosen as the main model. NOT "best point accuracy" but rather:
unified posterior predictive distribution with well-calibrated uncertainty.

## Layout (3-4 panels)
- **(A) Stress parity** — MAIN PANEL, largest. Coupled steady-state max stress. Hexbin or scatter with 90% PI shading.
- **(B) k_eff parity** — Secondary panel. Coupled k_eff.
- **(C) Max fuel temperature parity** — Secondary panel. One representative thermal output.
- **(D) Metrics summary strip** (OPTIONAL, small) — R^2, RMSE, PICP90 for 3 outputs. Can be inline text in caption if too crowded.

Panel A must be visually dominant (e.g., 2x area of B or C).

## Data Files in This Folder

### parity_data_phy_mono.csv
- Columns: sample_idx, output, y_true, y_pred_mean, y_pred_std
- 501 test samples x 3 outputs (iteration2_max_global_stress, iteration2_keff, iteration2_max_fuel_temp)
- y_pred_std = predictive standard deviation for 90% PI: mean +/- 1.645*std

### parity_data_baseline.csv
- Same format, for Reference surrogate (bnn-baseline). Can be used for comparison overlay if desired.

### metrics_summary.csv
- Per-output metrics for both models: R2, RMSE, MAE, PICP, MPIW, CRPS

## Key Numbers (from canonical results)

### Physics-regularized BNN (bnn-phy-mono)
| Output | R^2 | RMSE | MAE | PICP90 | MPIW |
|--------|-----|------|-----|--------|------|
| Coupled max stress | 0.944 | 7.39 MPa | 5.44 MPa | 0.986 | 39.4 MPa |
| Coupled k_eff | 0.849 | 2.78e-4 | 2.12e-4 | 0.974 | 1.32e-3 |
| Coupled max fuel temp | 0.628 | 4.05 K | 3.07 K | 0.944 | 15.9 K |

### Reference BNN (bnn-baseline)
| Output | R^2 | RMSE | MAE | PICP90 | MPIW |
|--------|-----|------|-----|--------|------|
| Coupled max stress | 0.942 | 7.52 MPa | 5.66 MPa | 0.990 | 40.2 MPa |
| Coupled k_eff | 0.844 | 2.82e-4 | 2.15e-4 | 0.958 | 1.39e-3 |
| Coupled max fuel temp | 0.627 | 4.06 K | 3.10 K | 0.946 | 15.4 K |

### Notes on k_eff R^2
k_eff R^2 ~ 0.85 looks moderate but the total variance is only ~77 pcm; RMSE = 278 pcm is <0.03% of k_eff ~ 1.10. Low R^2 is an artifact of small dynamic range, not poor prediction.

## Design Rules
- Stress panel must be the main visual
- Do NOT make all 3 panels equal-width
- Do NOT turn this into a model comparison poster
- Do NOT include HeteroMLP or old surrogate comparisons
- Use paper-facing labels:
  - "Coupled steady-state max stress (MPa)"
  - "$k_\mathrm{eff}$ (coupled)"
  - "Max fuel temperature (K)"
- 90% prediction interval shown as shaded band or error bars
- Identity line (y=x) in each parity panel
- English only, no CJK

## Style
- Hexbin preferred for stress (501 points, dense). Or scatter with alpha.
- Consistent color: blue for predictions, gray for identity line
- Figure size: ~170mm wide
