# High-Fidelity Coupled OpenMC-FEniCS Simulation Code

Reference implementation of the coupled neutronics-thermal-mechanical
simulation used to generate the training dataset for the BNN surrogate.

## File overview

| File | Role |
|------|------|
| `material_config.py` | Defines the 9 material parameters (8 uncertain + SS316_scale fixed) with nominal values and standard deviations |
| `generater.py` | Orchestrates sample generation, parameter perturbation, and batch execution of coupled simulations |
| `Mega_new_compling.py` | Core Picard iteration loop: OpenMC -> FEniCS thermal -> FEniCS stress -> geometry update -> repeat |
| `MEGA_OpenMC_test.py` | OpenMC neutronics driver: sets up geometry, materials, tallies, runs transport, extracts k_eff and power distribution |
| `fenics_thermal_TE.py` | FEniCS thermal-mechanical solver: heat conduction + linear elasticity with temperature-dependent properties |
| `heatpipe.py` | Heat pipe boundary condition model: effective conductivity and temperature coupling |
| `change_geo_file.py` | Utility to update GMSH geometry files with perturbed dimensional parameters |
| `parameter_perturber.py` | Sobol/LHS sample generation for material parameter perturbation |
| `0405-UQ-test-fenics.py` | Entry point: Sobol-based sensitivity analysis using direct HF evaluations (n=8192) |
| `0318-UQ-test-fenics.py` | Entry point: single-sample testing/debugging variant |
| `extract_dataset_v3.py` | Post-processing: extracts scalar outputs from simulation directories into dataset_v3.csv |

## Coupling workflow

```
Input parameters (8 uncertain material properties)
        |
        v
  OpenMC transport (k_eff, fission power)
        |
        v
  FEniCS thermal solve (temperature field)
        |
        v
  FEniCS stress solve (thermal expansion, stress field)
        |
        v
  Geometry update (core height, wall expansion)
        |
        v
  Convergence check (delta_T < 1 K)
        |-- not converged --> back to OpenMC
        |-- converged --> extract 15 scalar outputs
```

## Parameters

8 uncertain inputs (BNN training features):
- `E_slope`, `E_intercept`: temperature-dependent Young's modulus E(T) = E_slope * T + E_intercept
- `nu`: Poisson's ratio
- `alpha_base`, `alpha_slope`: CTE alpha(T) = alpha_base + alpha_slope * T
- `SS316_T_ref`, `SS316_k_ref`, `SS316_alpha`: thermal conductivity k(T) = k_ref + SS316_alpha * (T - T_ref)

1 fixed parameter:
- `SS316_scale`: scaling factor for conductivity, fixed at 1/100

## Runtime environment

- Server: EPYC 9654 / 96 cores
- Conda env: `HP-env`
- Dependencies: FEniCS 2019.1, OpenMC, GMSH, SALib, pyDOE
- Single HF evaluation: ~38 minutes (2 Picard iterations)
- OpenMC settings: 600 batches, 250 inactive, 30000 particles

## Dataset

- Total completed simulations: 3124 (as of 2026-03-18 in dataset_v3.csv)
- 192 additional samples computed in April 2026, not yet extracted
- BNN training uses a frozen split of 2900 samples (seed=2026)
