# Figure 4: Dominant-Factor Separation by Sobol Analysis

## Purpose
Prove that **different outputs have different dominant-factor pathways**:
- Stress is governed by the elastic-constitutive channel (E_intercept dominates)
- k_eff is governed by the thermal-expansion channel (alpha_base dominates)
- These two channels share almost no dominant parameters

This is the "dominant-factor separation" finding.

## Layout (2-3 panels)
- **(A) Stress S1 and ST** — MAIN PANEL (or equal with B)
  - Horizontal bar chart or dot-whisker with 90% CI
  - 8 input parameters, sorted by S1
- **(B) k_eff S1 and ST** — Equal with A
  - Same format
- **(C) Selected thermal output** — OPTIONAL, delete if too crowded
- **(D) All-output heatmap inset** — NOT recommended for main text

## Data Files in This Folder

### sobol_stress_keff.csv
Extracted Sobol indices for the two key outputs (bnn-phy-mono model):

**Stress (iteration2_max_global_stress):**
| Input | S1_mean | S1_ci_lo | S1_ci_hi | ST_mean | ST_ci_lo | ST_ci_hi | S1_spans_zero |
|-------|---------|----------|----------|---------|----------|----------|---------------|
| E_intercept | 0.579 | 0.574 | 0.583 | 0.597 | 0.592 | 0.601 | False |
| alpha_base | 0.169 | 0.164 | 0.173 | 0.184 | 0.182 | 0.187 | False |
| nu | 0.065 | 0.058 | 0.071 | 0.068 | 0.067 | 0.068 | False |
| SS316_k_ref | 0.051 | 0.046 | 0.056 | 0.066 | 0.065 | 0.067 | False |
| E_slope | 0.050 | 0.044 | 0.057 | 0.058 | 0.057 | 0.059 | False |
| alpha_slope | 0.027 | 0.021 | 0.032 | 0.034 | 0.033 | 0.035 | False |
| SS316_T_ref | 0.019 | 0.013 | 0.024 | 0.031 | 0.031 | 0.032 | False |
| SS316_alpha | 0.002 | -0.004 | 0.008 | 0.007 | 0.007 | 0.007 | **True** |

**k_eff (iteration2_keff):**
| Input | S1_mean | S1_ci_lo | S1_ci_hi | ST_mean | ST_ci_lo | ST_ci_hi | S1_spans_zero |
|-------|---------|----------|----------|---------|----------|----------|---------------|
| alpha_base | 0.785 | 0.783 | 0.788 | 0.783 | 0.776 | 0.789 | False |
| alpha_slope | 0.179 | 0.171 | 0.187 | 0.186 | 0.184 | 0.188 | False |
| nu | 0.028 | 0.020 | 0.037 | 0.027 | 0.027 | 0.028 | False |
| SS316_T_ref | 0.005 | -0.003 | 0.013 | 0.004 | 0.004 | 0.004 | **True** |
| E_slope | -0.002 | -0.010 | 0.006 | 0.003 | 0.003 | 0.003 | **True** |
| SS316_alpha | 0.002 | -0.007 | 0.010 | 0.006 | 0.005 | 0.006 | **True** |
| E_intercept | -0.001 | -0.010 | 0.008 | 0.003 | 0.003 | 0.004 | **True** |
| SS316_k_ref | 0.000 | -0.008 | 0.008 | 0.004 | 0.004 | 0.004 | **True** |

### sobol_baseline_stress_keff.csv
Same data for Reference BNN (bnn-baseline) for robustness check.

### Key Interpretation

1. **Stress**: E_intercept alone accounts for ~58% of first-order variance. Together with alpha_base (~17%), they explain ~75%. Near-zero interaction effects (ST - S1 ≈ 0.02).

2. **k_eff**: alpha_base alone accounts for ~79% of variance. alpha_slope adds ~18%. **No elasticity or conductivity parameters significantly affect k_eff** (all CI span zero).

3. **Separation**: The dominant factor for stress (E_intercept) has S1 ≈ -0.001 for k_eff (CI spans zero). The dominant factor for k_eff (alpha_base) has S1 = 0.169 for stress — present but secondary.

4. **Parameters where S1 CI spans zero**: Must NOT be described as stable dominant factors. Use language like "not significantly different from zero" or "negligible contribution."

## Design Rules
- Core message = stress vs k_eff pathways differ
- CI must be visible (whiskers or bands)
- Parameters where S1_ci_spans_zero = True should be visually distinct (grayed out or marked)
- Do NOT pile up all 15 outputs
- Paper-facing parameter names:
  - E_intercept -> "$E$ intercept"
  - alpha_base -> "$\\alpha$ base"
  - alpha_slope -> "$\\alpha$ slope"
  - nu -> "$\\nu$"
  - E_slope -> "$E$ slope"
  - SS316_k_ref -> "$k$ reference"
  - SS316_T_ref -> "$T$ reference"
  - SS316_alpha -> "$\\alpha_\\mathrm{diff}$"
- English only, no CJK

## Style
- Horizontal bar + CI whisker is clearest for comparing 8 parameters
- Two-panel side by side: stress | k_eff
- Color-code S1 vs ST (e.g., filled vs hollow, or two shades)
- Sort by S1 descending within each panel
- Figure size: ~170mm wide
