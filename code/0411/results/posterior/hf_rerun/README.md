# HF rerun lightweight archive

Five direct HF evaluations of the coupled OpenMC + FEniCS solver, used as a
spot-check of the `data-mono-ineq` surrogate's per-case `(mu, sigma)`
predictions. This is a small direct validation set, not a generalization
experiment.

## Layout

- `hf_rerun_summary.json` — canonical values: per-case params, HF outputs,
  surrogate `(mu, sigma)`, summary MAE/RMSE, classification, and wording
  guidance for the manuscript.
- `case_manifest.csv` — one row per case: 8 material parameters, HF outputs,
  nearest dataset-row match, whether the case is unseen by the surrogate.
- `hf_rerun_vs_nn_comparison.csv` — side-by-side surrogate vs nearest-neighbour
  baseline; retained only for traceability (the NN baseline is NOT used in the
  0411_v3 manuscript).
- `cases/<case_id>/` — per-case archive of six small files copied verbatim
  from the original run directories: `setting.txt`, `fenics_scalar_data.txt`,
  `fuel_nearby_maxstress.txt`, `hp_nearby_maxstress.txt`, `out_keff.txt`,
  `parameters_and_geo_feom_fenics.txt`, `out_fenicsdata_coupled.txt`.

## Not included

The original HF run directories contain roughly 600 MB per case
(`statepoint.600.h5`, `tallies.out`, `summary.h5`, `*.vtu`). Those files stay
in place at
`/Users/yinuo/Projects/hpr-claude-project/5posttttttttttttttttttttttttttttttttttttttttttttttttttttttttt/<case_id>/0/`.
This archive keeps only the lightweight, human-readable text files needed to
reproduce the summary table.

## Case classification

| Case | Class | Strictly new LHS | Unseen by surrogate |
|---|---|---|---|
| 2026_04_03_21_00_23 | exact reproduction of row 552 | No | No |
| 2026_04_04_00_01_51 | NaN refill of row 260 | No | Yes (row 260 dropped from training) |
| 2026_04_04_03_09_02 | strictly new LHS point | Yes | Yes |
| 2026_04_04_06_25_14 | strictly new LHS point | Yes | Yes |
| 2026_04_04_09_39_17 | strictly new LHS point | Yes | Yes |

Net: 3 strictly-new LHS points, 4 points unseen by the surrogate during training,
1 reproducibility check.

## Headline results

- Stress: MAE = 0.70 MPa, RMSE = 0.86 MPa, all 5 within 1 sigma of the
  predictive distribution. HF-solver intrinsic noise floor ~0.1 MPa.
- keff: MAE = 26 pcm, RMSE = 27 pcm, all 5 within 1 sigma.
- Surrogate is ~8x better than train+val nearest-neighbour retrieval on stress
  (archived for traceability; not reported in the manuscript).
