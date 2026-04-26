# Figure Bank — bnn0414 manuscript

Sub-figure catalog. Each item is a self-contained, publication-quality panel.
Final main-text / appendix assignment happens later by composing items.

## A. Workflow / setup
| ID  | Title | Science role | Likely home |
|-----|-------|-------------|-------------|
| A1  | Probabilistic analysis pipeline | Frame the full BNN-centric workflow | Main Fig 1 |
| A2  | BNN architecture schematic | Show network structure + posterior predictive | Appendix / Main inset |
| A3  | Data split / lineage diagram | Train/val/test provenance | Appendix |

## B. Predictive behaviour
| ID  | Title | Science role | Likely home |
|-----|-------|-------------|-------------|
| B1  | Stress parity (main panel) | Primary accuracy evidence | Main Fig 2 (dominant) |
| B2  | keff parity | Secondary accuracy | Main Fig 2 (minor) |
| B3  | Thermal parity (max fuel temp) | Multi-output evidence | Main Fig 2 (minor) |
| B4  | Stress residual distribution | Bias / heteroscedasticity check | Appendix |
| B5  | Selected metrics summary table-figure | Compact R²/RMSE/PICP/MPIW | Caption or appendix |
| B6  | Calibration curve (coverage vs nominal) | Interval calibration | Appendix |
| B7  | Coverage vs interval width | Trade-off visualisation | Appendix |
| B8  | Epistemic / aleatoric decomposition | Uncertainty component | Appendix |

## C. Forward UQ
| ID  | Title | Science role | Likely home |
|-----|-------|-------------|-------------|
| C1  | Coupled vs uncoupled stress distribution | Core coupling compression | Main Fig 3 (dominant) |
| C2  | Coupled keff distribution | Reactivity spread | Main Fig 3 (secondary) |
| C3  | Thermal output distribution | Additional output | Appendix |
| C4  | Forward summary stats panel | Compact mean/std/percentile table | Caption or appendix |
| C5  | Decoupled/coupled comparison (another output) | Coupling generality | Appendix |

## D. Sobol / attribution
| ID  | Title | Science role | Likely home |
|-----|-------|-------------|-------------|
| D1  | Stress S1 bar | Dominant factor for stress | Main Fig 4 (left) |
| D2  | keff S1 bar | Dominant factor for keff | Main Fig 4 (right) |
| D3  | Stress ST bar | Total-order comparison | Appendix |
| D4  | keff ST bar | Total-order comparison | Appendix |
| D5  | S1 vs ST scatter | Interaction detection | Appendix |
| D6  | All-output Sobol heatmap | Full attribution matrix | Appendix |
| D7  | Replicate stability / CI width | Method robustness | Appendix |

## E. Posterior
| ID  | Title | Science role | Likely home |
|-----|-------|-------------|-------------|
| E1  | Prior vs posterior marginals | Parameter shift under observations | Main Fig 5 (A) |
| E2  | Representative joint posterior | Correlation structure | Main Fig 5 (B) |
| E3  | Posterior predictive vs observed stress | Predictive calibration | Main Fig 5 (C) |
| E4  | Posterior predictive distribution shift | Distribution-level view | Appendix |
| E5  | Case-level predictive intervals | Per-case interval plot | Appendix |
| E6  | Parameter coverage summary | 90CI hit/miss per case | Appendix |
| E7  | MCMC trace plots | Convergence defense | Appendix |
| E8  | R-hat / ESS summary | Diagnostics defense | Appendix |

## F. Defense / supplementary
| ID  | Title | Science role | Likely home |
|-----|-------|-------------|-------------|
| F1  | Training history curves | Training stability | Appendix (撤 if no bnn0414 logs) |
| F2  | OOD robustness check | Extrapolation indication | Appendix |
| F3  | HF consistency spot-check | Direct HF agreement | Appendix |
| F4  | Full metrics heatmap (15 outputs) | Complete accuracy picture | Appendix |
| F5  | Additional marginals / pairwise densities | Extended posterior | Appendix |

---

## Composition plan (tentative)

| Main figure | Composed from |
|-------------|--------------|
| Fig 1       | A1 (+ optional A2 inset) |
| Fig 2       | B1 (large) + B2 (small) + B3 (small) |
| Fig 3       | C1 (large) + C2 (small) |
| Fig 4       | D1 + D2 |
| Fig 5       | E1 + E2 + E3 |
