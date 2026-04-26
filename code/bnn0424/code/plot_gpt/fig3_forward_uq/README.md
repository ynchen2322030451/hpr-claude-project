# Figure 3: Forward Uncertainty Propagation Under Coupling

## Purpose
Demonstrate that **coupling feedback changes the response distribution** — you cannot use decoupled intuition to understand coupled uncertainty.

Key message: neutronic-thermal feedback damps stress variability by ~30% and shifts the mean downward by ~42 MPa.

## Layout (2-3 panels)
- **(A) Max stress: uncoupled vs coupled distribution** — MAIN PANEL
  - Two distributions side by side (violin, ridge, or overlaid density)
  - Show: median, central 90% interval, spread difference
- **(B) Coupled k_eff distribution** — Secondary
  - Single distribution (decoupled k_eff is effectively constant, so only coupled matters)
- **(C) Coupled max fuel temperature** — OPTIONAL, delete if layout is too tight

## Data Files in This Folder

### coupling_shift_summary.csv
Coupling shift statistics from D3_coupling.csv (iter1 -> iter2):
| Output | Delta mean | Delta std | Var ratio (iter2/iter1) |
|--------|-----------|-----------|------------------------|
| max_stress | -41.8 MPa | 14.6 MPa | 0.490 |
| max_fuel_temp | -28.4 K | 9.9 K | 0.298 |
| keff | (N/A — iter1 has no keff) | — | — |

### test_predictions_selected.csv
501 test samples with columns:
- True and predicted values for iter1_stress, iter2_stress, iter2_keff, iter2_fuel_temp, iter1_fuel_temp
- pred_mean and pred_std for each

### forward_uq_summary.csv
Forward propagation statistics at sigma_k = 1.0 (nominal uncertainty level):
- Coupled stress: mean=161.7 MPa, std=31.9 MPa, P5=112.7, P50=159.9, P95=217.0
- Coupled k_eff: mean=1.10354, std=7.73e-4
- Epistemic vs aleatoric decomposition included

### Key Numbers

#### Stress distribution shift (from D3_coupling.csv)
- Iter1 (uncoupled) stress: mean ≈ 203.5 MPa, std ≈ 45.6 MPa
  (Derived: iter2_mean - delta_mean = 161.7 - (-41.8) = 203.5; iter2_std / sqrt(var_ratio) = 31.9 / sqrt(0.49) ≈ 45.6)
- Iter2 (coupled) stress: mean ≈ 161.7 MPa, std ≈ 31.9 MPa
- **Reduction: ~30% in std, ~42 MPa downward shift in mean**
- Mechanism: negative feedback — thermal expansion modifies core geometry, offsetting direct stress increase

#### k_eff (coupled only, at sigma_k=1.0)
- Mean: 1.10354
- Std: 7.73e-4 (~77 pcm)
- Nearly Gaussian

## Design Rules
- Do NOT use threshold line as main visual element
- Show distribution shape directly: violin + inner box, ridge, or half-violin
- Mark median, P5, P95 explicitly
- Use paper-facing labels:
  - "Uncoupled pass" vs "Coupled steady state"
  - "Max stress (MPa)"
  - "$k_\mathrm{eff}$"
- English only, no CJK
- Muted palette: two distinguishable colors for uncoupled vs coupled

## Style
- Violin or ridge plot preferred over plain histogram
- Annotation: coupling effect arrow or delta label between distributions
- Figure size: ~170mm wide (or 85mm single-column if 2 panels)
