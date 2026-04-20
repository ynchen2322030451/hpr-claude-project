# Pre-v3418 Archived Results

Archived on 2026-04-20. These results were generated on the older dataset
(n ≈ 2900, split: 2029/436/435) before the v3418 dataset expansion
(n = 3341, split: 2339/501/501).

All canonical results for the paper now come from `results_v3418/`.

## Contents

| Folder | Description |
|--------|-------------|
| `experiments_legacy/` | Old experiment outputs (risk, sobol, OOD, posterior, speed, physics) for 4 BNN variants |
| `accuracy/` | Calibration metrics and comparison tables |
| `data_efficiency/` | Small-sample training curves |
| `hf_sensitivity/` | HF vs BNN sensitivity comparison |
| `ood/` | OOD coverage and calibration |
| `physics_consistency/` | Monotonicity and inequality violation rates |
| `posterior/` | MCMC trace/rank plots |
| `sensitivity/` | Sobol convergence plots |
| `speed/` | Budget-matched benchmark |
| `uncertainty_decomposition/` | Epistemic vs aleatoric scatter plots |

## Models trained on old dataset

- bnn-data-mono (code/models/bnn-data-mono/)
- bnn-data-mono-ineq (code/models/bnn-data-mono-ineq/)

These two models were NOT retrained on v3418. Their old-dataset results
are available here for appendix/ablation reference only.
