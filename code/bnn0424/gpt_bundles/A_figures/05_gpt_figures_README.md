# GPT Figure Workspace

Each subfolder = one figure. Upload the entire folder contents to GPT when working on that figure.

## Main Text Figures (Fig. 0–7)

| Folder | Figure | Content | GPT Draft |
|--------|--------|---------|-----------|
| `fig0_workflow/` | Fig. 0 | Probabilistic analysis pipeline schematic | Yes (from old fig1_workflow) |
| `fig1_accuracy/` | Fig. 1 | Surrogate accuracy — parity plots + external baseline | No — needs new draft |
| `fig2_predictive/` | Fig. 2 | Predictive behavior — parity + calibration + intervals | Yes (from old fig2_surrogate_selection) |
| `fig3_forward/` | Fig. 3 | Forward UQ — coupling reshapes distributions | Yes (from old fig3_forward_uq) |
| `fig4_sobol/` | Fig. 4 | Sobol variance decomposition — sensitivity pathways | Yes (from old fig4_sobol) |
| `fig5_physics/` | Fig. 5 | Physics consistency — monotonicity + constraint effects | No — needs new draft |
| `fig6_posterior/` | Fig. 6 | Posterior inference — prior/posterior shift + predictive | Yes (from old fig5_posterior) |
| `fig7_efficiency/` | Fig. 7 | Data efficiency + computational speedup | No — needs new draft |

## SI Figures

| Folder | Figure | Content |
|--------|--------|---------|
| `figS1_sobol_convergence/` | Fig. S1 | Sobol bootstrap convergence |
| `figS2_prior_sensitivity/` | Fig. S2 | Prior sensitivity analysis |
| `figS3_noise_sensitivity/` | Fig. S3 | Noise sensitivity analysis |
| `figS4_ood/` | Fig. S4 | Out-of-distribution epistemic uncertainty |
| `figS5_external_calib/` | Fig. S5 | External baseline calibration comparison |
| `figS6_bnn_architecture/` | Fig. S6 | BNN architecture diagram |
| `figS7_reactor_geometry/` | Fig. S7 | Reactor geometry cross-section |

## Appendix Figures

| Folder | Figure | Content |
|--------|--------|---------|
| `figA1_model_validation/` | Fig. A1 | Extended model validation |
| `figA2_physics_robustness/` | Fig. A2 | Physics regularization robustness |
| `figA3_efficiency/` | Fig. A3 | Extended efficiency analysis |
| `figA4_sobol_detail/` | Fig. A4 | Sobol detail — all outputs |

## Folder Contents

Each figure folder may contain:
- `manuscript_spec.txt` — figure caption/annotation spec from manuscript
- `current_version.png` — current rendered figure for reference
- `compose_script.py` — the Python script that generates the figure from bank panels
- `README.md` — figure purpose and panel descriptions (from old plot_gpt)
- `*.csv` / `*.json` / `*.npz` — source data for plotting
- `*_notes.txt` — bilingual caption notes
- `gpt样板图.png` — GPT reference/template image
- `outputs/` — previous GPT-generated outputs (pdf/png/svg/pptx)

## Shared Utilities

`_shared/` contains common style and export helpers.
