# Figure 1: Probabilistic Analysis Pipeline

## Purpose
Define the single main storyline of the paper:
**uncertain inputs -> coupled HF simulation -> Bayesian surrogate -> forward propagation -> sensitivity attribution -> posterior calibration**

## Layout
One unified workflow diagram (no separate panels). If panels must exist:
- (A) Uncertain SS316 material-property inputs (8 parameters)
- (B) Coupled high-fidelity simulation: OpenMC + FEniCS, uncoupled pass -> coupled steady state
- (C) Bayesian neural surrogate as unified posterior predictive layer (VISUAL CENTER, largest weight)
- (D) Downstream analyses: forward UQ / Sobol / posterior calibration

## Key Design Rules
- NO result numbers in this figure
- NO speedup numbers
- NO threshold gate
- NOT a "project management" flowchart
- BNN surrogate must be visually centered and most prominent
- Use English only (no CJK characters)
- Use paper-facing terms only (see vocabulary below)

## Vocabulary (mandatory)
- "uncoupled pass" (not iter1/iteration1)
- "coupled steady state" or "coupled response" (not iter2/iteration2)
- "Reference surrogate" (not level0/baseline)
- "Physics-regularized surrogate" (not level2/phy-mono)

## Scientific Content for Text Labels

### Input block
8 SS316 material-property parameters:
- E_slope, E_intercept (Young's modulus temperature dependence)
- nu (Poisson's ratio)
- alpha_base, alpha_slope (thermal expansion coefficient)
- SS316_T_ref, SS316_k_ref (thermal conductivity reference)
- SS316_alpha (thermal diffusivity)

### HF simulation block
- OpenMC (neutronics) + FEniCS (thermo-mechanical)
- Two-pass coupling: uncoupled pass -> coupled steady state
- Outputs: temperature fields, stress fields, k_eff

### BNN surrogate block
- Constraint-regularized Bayesian neural network
- Posterior predictive distribution (mean + uncertainty)
- 15 outputs, 5 primary coupled outputs

### Downstream analyses
- Forward UQ: Monte Carlo propagation through surrogate
- Sobol: Variance-based sensitivity decomposition
- Posterior calibration: Observation-conditioned parameter updating

## Bottom Note (optional)
"Primary role of the surrogate: a unified posterior predictive layer enabling forward uncertainty propagation, variance-based attribution, and observation-conditioned posterior updating."

## Style
- Minimalist, publication-quality
- Muted color palette, no annotation boxes
- Visual hierarchy: BNN block >> other blocks
- Suggested figure size: ~170mm wide (Nature double-column)
