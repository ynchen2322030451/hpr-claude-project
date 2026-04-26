# Figure 1 Data Reference — Real Project Data for GPT Illustration

This file contains verified data from the HPR project for correcting/refining the Figure 1 workflow diagram.

---

## (A) Input Parameters — 8 Uncertain SS316 Material Properties

All inputs follow **Normal (Gaussian) distributions**.

| Parameter | Symbol | Mean (nominal) | Std (σ) | Units | Physical meaning |
|-----------|--------|---------------|---------|-------|------------------|
| E_slope | $E_\mathrm{slope}$ | −7×10⁷ | 7×10⁶ | Pa/K | Young's modulus temperature coefficient |
| E_intercept | $E_\mathrm{intercept}$ | 2×10¹¹ | 2×10¹⁰ | Pa | Young's modulus reference intercept |
| ν | $\nu$ | 0.31 | 0.031 | — | Poisson's ratio |
| α_base | $\alpha_\mathrm{base}$ | 1×10⁻⁵ | 1×10⁻⁶ | 1/K | Thermal expansion coefficient (base) |
| α_slope | $\alpha_\mathrm{slope}$ | 5×10⁻⁹ | 5×10⁻¹⁰ | 1/K² | Thermal expansion coefficient (slope) |
| SS316_T_ref | $T_\mathrm{ref}^\mathrm{SS316}$ | 923.15 | 92.315 | K | Thermal conductivity reference temperature |
| SS316_k_ref | $k_\mathrm{ref}^\mathrm{SS316}$ | 23.2 | 2.32 | W/(m·K) | Thermal conductivity reference value |
| SS316_α | $\alpha_\mathrm{SS316}$ | 0.01333 | 0.00133 | W/(m·K²) | Thermal conductivity temperature slope |

**Coefficient of variation (CoV)**: 10% for all parameters.

**Source**: `code/bnn0414/code/hf_simulation/material_config.py`

---

## (B) High-Fidelity Simulation — OpenMC + FEniCS Coupled System

### Reactor geometry (from .geo mesh file)
| Dimension | Value | Units |
|-----------|-------|-------|
| Heat pipe diameter | 1.575 | cm |
| Heat pipe pitch | 2.7713 (= 1.6√3) | cm |
| Fuel pin diameter | 1.425 | cm |
| Fuel pin pitch | 1.6 | cm |
| Inner core region radius | 8.84 | cm |
| Outer reflector radius | 55.625 | cm |
| Active core height (nominal) | ~25 (updates to ~152 after expansion) | cm |
| Thermal power | 5 | MW_th |
| Heat pipe boundary temperature | 897.5 | K |

### FEniCS mesh
- **Nodes**: 98,398
- **Cells (elements)**: 190,790
- 2D cross-section mesh (xy-plane), extruded for z-expansion
- VTU format output files (~11 MB thermal, ~38 MB stress per run)

### Coupling scheme
Two-pass iterative coupling: **uncoupled pass → coupled steady state**.

**Example convergence (one sample, from PrintOut.txt):**

| Quantity | Uncoupled pass | Coupled steady state | Change |
|----------|---------------|---------------------|--------|
| k_eff | 1.1134 ± 0.0002 | 1.1039 ± 0.0002 | −0.85% |
| Avg fuel temp | 1014.08 K | 1000.41 K | −13.67 K |
| Max fuel temp | 1099.91 K | 1073.70 K | −26.21 K |
| Max monolith temp | 1064.47 K | 1035.96 K | −28.51 K |
| Max global stress | 162.52 MPa | 130.92 MPa | −31.60 MPa |
| Core height (Hcore) | 150 → 152.23 cm | 152.22 cm | converged |
| Wall thickness (wall2) | 29.90 cm | 29.90 cm | converged |

**Coupling convergence criteria**: relative error of fuel/monolith temperature drops from ~1.2/1.1 (iter 1) to ~0.12/0.07 (iter 2).

### Coupling feedback loop
```
OpenMC (neutronics)
   → power distribution → FEniCS (thermal)
   → temperature field → FEniCS (mechanical)
   → thermal expansion/deformation → geometry update
   → updated geometry → OpenMC (next iteration)
```

### Average coupling effects across 501 test samples (from D3_coupling.json)
| Output | Δmean (iter2 − iter1) | Variance ratio (iter2/iter1) |
|--------|----------------------|------------------------------|
| Avg fuel temp | −14.78 K | 0.25 |
| Max fuel temp | −28.38 K | 0.30 |
| Max monolith temp | −30.65 K | 0.27 |
| Max global stress | −41.79 MPa | 0.49 |

### Simulation runtime
- OpenMC: ~4100–4200 sec per iteration
- FEniCS (thermal + mechanical): ~1300–1700 sec per iteration
- Total per coupled run (2 iterations): ~11,200 sec (~3.1 hours)

---

## (C) Bayesian Neural Surrogate

### Architecture
| Property | Value |
|----------|-------|
| Model class | BayesianMLP (reparameterized BNN) |
| Input dim | 8 |
| Output dim | 15 (7 iter1 + 8 iter2 outputs) |
| Primary coupled outputs | 5 (keff, max_fuel_temp, max_monolith_temp, max_global_stress, wall2) |
| Hidden activation | SiLU (Swish) |
| Output activation | None (mean head), clamped logvar (aleatoric head) |
| Output heads | 2 — mean (μ) and log-variance (log σ²) → heteroscedastic |
| Weight posterior | Gaussian q(w) = N(μ_w, softplus(ρ_w)²) |
| Weight prior | Gaussian p(w) = N(0, σ_prior²) |
| Training loss | ELBO = NLL + (kl_weight × KL) / N_train |

### bnn-phy-mono (Physics-regularized surrogate — main model)
| Hyperparameter | Value |
|----------------|-------|
| Width (hidden units) | 254 |
| Depth (hidden layers) | 2 |
| Total architecture | 8 → 254 → 254 → (15 mean + 15 logvar) |
| Learning rate | 9.81×10⁻⁴ |
| Weight decay | 8.09×10⁻⁸ |
| Batch size | 32 |
| Epochs | 399 |
| Gradient clipping | 0.674 |
| Prior σ | 0.478 |
| KL weight | 1.93×10⁻⁴ |
| Monotonicity weight (w_mono) | 0.212 |
| Physics-prior pairs | 10 high-confidence monotone pairs |
| MC samples (eval) | 50 |
| MC samples (Sobol) | 30 |
| MC samples (posterior MCMC) | 20 |
| Training time | ~4,866 sec (~81 min) on GPU |
| Optuna trials | 30 |

### bnn-baseline (Reference surrogate)
| Hyperparameter | Value |
|----------------|-------|
| Width | 99 |
| Depth | 2 |
| Epochs | 180 |
| Prior σ | 0.191 |
| KL weight | 2.12×10⁻⁴ |
| Training time | ~2,023 sec |

### Physics-prior monotonicity constraints (10 pairs)
| Input → Output | Direction |
|----------------|-----------|
| E_intercept → iter2_max_global_stress | + (positive) |
| alpha_base → iter2_max_global_stress | + |
| alpha_slope → iter2_max_global_stress | + |
| SS316_k_ref → iter2_max_global_stress | − (negative) |
| E_slope → iter2_max_global_stress | + |
| E_intercept → iter1_max_global_stress | + |
| alpha_base → iter1_max_global_stress | + |
| SS316_k_ref → iter1_max_global_stress | − |
| SS316_k_ref → iter2_max_fuel_temp | − |
| SS316_k_ref → iter1_max_fuel_temp | − |

### Test performance (bnn-phy-mono, test set n=435)
| Output | R² | RMSE | Units |
|--------|-----|------|-------|
| iteration2_max_global_stress | 0.9385 | 7.53 | MPa |
| iteration2_keff | 0.8162 | 3.05×10⁻⁴ | — |
| iteration2_max_fuel_temp | 0.6606 | 4.23 | K |
| iteration2_max_monolith_temp | 0.6570 | 4.79 | K |
| iteration2_wall2 | 0.9949 | 1.64×10⁻³ | cm |
| iteration1_max_global_stress | 0.9408 | 10.49 | MPa |
| Overall test NLL | 0.390 | — | — |

### 15 output variables (all outputs)
**Iteration 1 (uncoupled pass, 7 outputs):**
1. avg_fuel_temp (K)
2. max_fuel_temp (K)
3. max_monolith_temp (K)
4. max_global_stress (MPa)
5. monolith_new_temperature (K)
6. Hcore_after (cm)
7. wall2 (cm)

**Iteration 2 (coupled steady state, 8 outputs):**
1. keff (dimensionless)
2. avg_fuel_temp (K)
3. max_fuel_temp (K)
4. max_monolith_temp (K)
5. max_global_stress (MPa)
6. monolith_new_temperature (K)
7. Hcore_after (cm)
8. wall2 (cm)

---

## (D) Downstream Analyses

### Forward UQ / Risk Propagation
| Parameter | Value |
|-----------|-------|
| MC input samples | 20,000 |
| Design sigma scaling (main) | 1.0 |
| Primary stress threshold | **131 MPa** |
| Threshold sweep (appendix) | 110, 120, 131, 150, 180, 200 MPa |
| Draw from predictive distribution | Yes (not just mean) |

### Sobol Sensitivity Attribution
| Parameter | Value |
|-----------|-------|
| N_base (Saltelli design) | 4,096 |
| Bootstrap samples | 512 |
| CI level | 90% |
| Estimator | Jansen's method |
| Convergence study N values | 256, 512, 1024, 2048, 4096, 8192 |
| Independent repeats | 20 per N_base |

**Key Sobol results (bnn-phy-mono, iteration2_max_global_stress):**

| Input | S₁ (mean) | S₁ 90% CI | S_T (mean) |
|-------|-----------|-----------|------------|
| E_intercept | **0.579** | [0.574, 0.583] | 0.597 |
| α_base | **0.169** | [0.164, 0.173] | 0.184 |
| ν | 0.065 | [0.058, 0.071] | 0.068 |
| E_slope | 0.050 | [0.044, 0.057] | 0.058 |
| SS316_k_ref | 0.051 | [0.046, 0.056] | 0.066 |
| α_slope | 0.027 | [0.021, 0.032] | 0.034 |
| SS316_T_ref | 0.019 | [0.013, 0.024] | 0.031 |
| SS316_α | 0.002 | [−0.004, 0.008]* | 0.007 |

*CI spans zero → not statistically significant at 90% level.

**Key Sobol results (bnn-phy-mono, iteration2_keff):**

| Input | S₁ (mean) | S₁ 90% CI | S_T (mean) |
|-------|-----------|-----------|------------|
| α_base | **0.785** | [0.783, 0.788] | 0.783 |
| α_slope | **0.179** | [0.171, 0.187] | 0.186 |
| ν | 0.028 | [0.020, 0.037] | 0.027 |
| Others | <0.006 | CI spans zero* | <0.006 |

### Posterior Calibration (MCMC)
| Parameter | Value |
|-----------|-------|
| Method | Metropolis-Hastings MCMC |
| MCMC chains | 4 |
| Samples per chain | 5,000 (after burn-in) |
| Max Gelman–Rubin R̂ | 1.010 |
| Benchmark cases | 18 (6 low / 6 near-threshold / 6 high stress) |
| Observation noise | 2% artificial Gaussian noise on true HF outputs |
| 90% CI coverage (mean) | 0.89–0.92 |
| Acceptance rate | 0.58–0.67 |
| BNN MC samples per likelihood eval | 20 |

---

## Dataset Summary

| Property | Value |
|----------|-------|
| Total HF samples (pre-filter) | 3,418 |
| After NaN filtering | 3,341 |
| Train set | 2,339 (70%) |
| Validation set | 501 (15%) |
| Test set | 501 (15%) |
| Split method | Stratified by case_id |
| Random seed | 2026 |

### Output range (train set statistics)

| Output | Min | Max | Mean | Std |
|--------|-----|-----|------|-----|
| iter2_keff | 1.0588 | 1.1062 | 1.1035 | 0.0013 |
| iter2_max_fuel_temp | 1058.2 K | 1113.7 K | 1074.2 K | 7.0 K |
| iter2_max_monolith_temp | 1018.8 K | 1081.8 K | 1036.6 K | 7.9 K |
| iter2_max_global_stress | 81.9 MPa | 293.5 MPa | 162.2 MPa | 29.8 MPa |
| iter2_wall2 | 29.853 cm | 30.001 cm | 29.918 cm | 0.023 cm |

---

## Available 3D/2D Field Data (for illustration)

VTU files available in `5posttttttttttttttttttttttttttttttttttttttttttttttttttttttttt/` directory (5 HF runs):

| File | Size | Content | Mesh |
|------|------|---------|------|
| Thermal_conduction000000.vtu | 11 MB | Temperature field (2D cross-section) | 98,398 nodes |
| Thermal_expansion_stress000000.vtu | 38 MB | Von Mises stress field (2D cross-section) | 190,790 cells |
| Thermal_expansion_xy000000.vtu | 13 MB | XY-plane thermal expansion/displacement | — |
| Thermal_expansion_z000000.vtu | 711 KB | Z-direction expansion | — |
| Initial/ subdirectory | — | Uncoupled pass (iter1) versions of all above | — |

**Both coupled (iter2) and uncoupled (iter1, in Initial/) fields are available for comparison.**

Sample VTU path:
```
5posttttttttttttttttttttttttttttttttttttttttttttttttttttttttt/2026_04_04_00_01_51/0/Thermal_conduction000000.vtu
5posttttttttttttttttttttttttttttttttttttttttttttttttttttttttt/2026_04_04_00_01_51/0/Thermal_expansion_stress000000.vtu
5posttttttttttttttttttttttttttttttttttttttttttttttttttttttttt/2026_04_04_00_01_51/0/Initial/Thermal_conduction000000.vtu
```

---

## Corrections to GPT Draft

Based on the real data above, the following items in the GPT draft may need correction:

1. **Panel (A)**: The 8 input parameters and their symbols are correct. The figure correctly shows E_slope, E_intercept, ν, α_base, α_slope, T_ref, k_ref, α_SS316.

2. **Panel (B)**: The coupling scheme shows "iterate to convergence" — in practice, we run exactly 2 iterations (uncoupled pass + coupled steady state), not arbitrary convergence.

3. **Panel (C)**: The BNN has **15 outputs** (correct in figure), with **5 primary coupled outputs** (correct). Architecture is 8→254→254→30 for the physics-regularized model. The "posterior predictive distributions" sub-panel with T_f(r), T_m(r), σ_eq(r) is schematic — our BNN predicts scalar summaries (max/avg), not spatial fields.

4. **Panel (D)**: Sobol figure shows correct parameter ranking (E_intercept dominant for stress, α_base dominant for keff). The posterior calibration schematic is conceptually correct.

5. **k_eff convergence subplot** (bottom of panel B): Should show 2 iterations only, not a smooth curve. k_eff drops from ~1.113 to ~1.104.

6. **"Posterior predictive distributions" sub-panel**: Our BNN does NOT predict radial profiles T(r). It predicts scalar outputs (max_fuel_temp, max_stress, keff, etc.). The radial profile illustration is misleading — consider replacing with scalar distribution plots.
