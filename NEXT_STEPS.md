# NEXT STEPS

## 1. Canonical training
### Script
`python run_train_fixed_surrogates.py`

### Inputs
- `paper_experiment_config.py`
- current `dataset_v3.csv`
- existing helper functions from `run_phys_levels_main.py`

### Outputs
- `experiments_phys_levels/fixed_surrogate_fixed_base/`
- `experiments_phys_levels/fixed_surrogate_fixed_level2/`
- `experiments_phys_levels/fixed_split/`
- root-level compatibility files may also be refreshed

### Overwrite risk
Yes — root-level compatibility files may be overwritten; fixed split may be
replaced if configured with remake flag.

### Dependency
Must complete before: calibration benchmark, posterior HF proxy validation,
forward UQ / Sobol if these depend on fixed artifacts.

---

## 2. Inverse benchmark (canonical)
### Script
`python code/0310/run_inverse_benchmark_fixed_surrogate.py`

### Inputs
- canonical fixed surrogate (`fixed_surrogate_fixed_level2/`)
- canonical fixed split (`fixed_split/`)
- `paper_experiment_config.py`

### Outputs
- `experiments_phys_levels/inverse_calibration_pool.csv`
- `experiments_phys_levels/inverse_case_indices_<run_tag>.csv`
- `experiments_phys_levels/benchmark_case/benchmark_caseXXX_posterior_samples_<run_tag>.csv` (50 cases)
- `experiments_phys_levels/inverse_benchmark_case_summary_<run_tag>.csv`
- `experiments_phys_levels/inverse_benchmark_parameter_recovery_<run_tag>.csv`

### Overwrite risk
Yes if same RUN_TAG is reused.

### Dependency
Requires canonical training to be complete and consistent.

---

## 3. Posterior HF rerun validation
### Script
`python code/run_posterior_hf_rerun.py`

### Inputs
- canonical fixed surrogate (`fixed_surrogate_fixed_level2/`)
- `experiments_phys_levels/inverse_calibration_pool.csv`
- `experiments_phys_levels/inverse_case_indices_<run_tag>.csv`
- `experiments_phys_levels/benchmark_case/benchmark_caseXXX_posterior_samples_<run_tag>.csv`
- generater.py (OpenMC–FEniCS coupled runner)

### Outputs
- `experiments_phys_levels/posterior_hf_rerun/posterior_hf_rerun_summary.csv`
- `experiments_phys_levels/posterior_hf_rerun/posterior_hf_rerun_per_output.csv`
- `experiments_phys_levels/posterior_hf_rerun/posterior_hf_rerun_meta.json`
- archived HF run dirs under `posterior_hf_rerun/case*/`

### Overwrite risk
Yes if same output directory already exists.

### Dependency
Requires: canonical training complete, inverse benchmark complete,
`inverse_calibration_pool.csv` and `inverse_case_indices_<run_tag>.csv` present.

### Notes
- Each HF run takes ~1 h on the compute server.
- Ground truth comes from `inverse_calibration_pool.csv` indexed by
  `pool_case_index`, NOT from `fixed_split/test_indices.csv`.

---

## 4. Historical rerun isolation
If rerunning historical scripts such as `run_phys_levels_main_remain_delta.py`,
do NOT write into canonical result directories.

Use one of:
- a new `OUT_DIR`
- a rerun-only subdirectory
- archived old outputs first
