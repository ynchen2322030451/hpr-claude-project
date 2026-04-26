# Table 1 — Revised Design (Phase 4.2)

> **Status**: Phase 4.2 draft — pending author review before propagation to manuscript files.
> **Numerical source**: `code/bnn0424/results/CANONICAL_DATA_SUMMARY.md` (v3418, 2026-04-19).
> **Do not propagate** to `manuscript_en.txt` or `manuscript_bilingual.txt` until ECE flag below is resolved.

---

## Evidence flags

| Claim | Source | Status |
|-------|--------|--------|
| BNN-phy-mono stress R², RMSE, CRPS, PICP, MPIW | CANONICAL §2a | Verified |
| BNN-baseline stress R², RMSE, CRPS, PICP, MPIW | CANONICAL §2b | Verified |
| BNN-phy-mono keff R², RMSE, CRPS, PICP, MPIW | CANONICAL §2a | Verified |
| BNN-baseline keff R², RMSE, CRPS, PICP, MPIW | CANONICAL §2b | Verified |
| MC-Dropout stress R², stress CRPS | CANONICAL §2e, §14 | Verified (CRPS from phase1_evidence_v4 via §2e note — confirm external_baseline_scoring.csv) |
| Deep Ensemble stress R², stress CRPS | CANONICAL §2e, §14 | Verified (same caveat as MC-D above) |
| MC-Dropout / DE stress RMSE (~7.66, ~7.64) | CANONICAL §2e | Approximate (~) values confirmed |
| MC-Dropout / DE keff R² | CANONICAL §2e | Verified |
| BNN-baseline stress ECE ~0.13 | CANONICAL §16 note 3 | Implied in canonical caveats; confirm from metrics CSV |
| BNN-phy-mono stress ECE ~0.12 | phase1_evidence_v4.md | **【待核实：需从 metrics_per_output_fixed.csv 或 ECE 专项文件核对 phy-mono ECE 值】** |
| MC-Dropout / DE ECE | Not in canonical data | Not available — mark as "n/a" in table |
| keff σ ≈ 0.00077 (77 pcm) | CANONICAL §4d (σ_k=1.0 keff_std) | Verified |

---

## Unresolved items

- 【待核实：BNN-phy-mono stress ECE ~0.12 — 需核对 `results_v3418/models/bnn-phy-mono/fixed_eval/metrics_per_output_fixed.csv` 或专项 ECE 输出文件。若不存在，将 phy-mono ECE 改为 "n/a" 并删除该列的加粗。】
- 【待核实：MC-Dropout 和 Deep Ensemble 的 CRPS 值 (4.52, 4.50) 是否已在 `results_v3418/models/mc-dropout/fixed_eval/` 或 `external_baseline_scoring.csv` 中直接确认，或仍依赖 phase1_evidence_v4.md？若依赖后者，在脚注中注明来源并降为"参考值"。】

---

## Narrative framing note (from IMPROVEMENT_PLAN §1.3)

The table design below implements IMPROVEMENT_PLAN task 1.3.1: all metrics have
their best value bolded, not only CRPS. Footnote ‡ makes the editorial intent
explicit. Panel separation (a)/(b) implements task 4.2.3: readers can see that
BNN-phy-mono is competitive but not superior on point prediction (panel a), and
gains advantage on distributional quality (panel b).

---

## Caption

**Table 1.** Surrogate accuracy comparison on the held-out test set (*n* = 501).
**(a)** Point-prediction metrics. **(b)** Distributional quality metrics.
For stress (σ_max, coupled steady-state maximum global stress) and *k*_eff
(coupled effective multiplication factor), all four surrogate types were evaluated.
External baselines (MC-Dropout and Deep Ensemble) were trained on the same
fixed split (2339/501/501, seed 2026); per-output distributional metrics are
not available for these methods.
Bold denotes the best value per column within each output.‡
MC-Dropout and Deep Ensemble results marked "—" indicate metrics not reported
in their per-output evaluation files.

---

## Panel (a): Point-Prediction Quality

| Model | Output | R² | RMSE |
|-------|--------|----|------|
| BNN-phy-mono (physics-regularized) | σ_max (MPa) | 0.9438 | 7.390 |
| BNN-baseline (reference) | σ_max (MPa) | 0.9418 | 7.524 |
| MC-Dropout | σ_max (MPa) | **0.9479** | ~7.66 |
| Deep Ensemble | σ_max (MPa) | **0.9531** | **~7.64** |
| | | | |
| BNN-phy-mono (physics-regularized) | *k*_eff †  | **0.8492** | **0.000278** |
| BNN-baseline (reference) | *k*_eff †  | 0.8445 | 0.000282 |
| MC-Dropout | *k*_eff †  | 0.8273 | — |
| Deep Ensemble | *k*_eff †  | 0.8341 | — |

---

## Panel (b): Distributional Quality

| Model | Output | CRPS | ECE | PICP |
|-------|--------|------|-----|------|
| BNN-phy-mono (physics-regularized) | σ_max | **4.350** | **~0.12** 【待核实】 | 0.9860 |
| BNN-baseline (reference) | σ_max | 4.424 | ~0.13 | **0.9900** |
| MC-Dropout | σ_max | 4.52 | — | — |
| Deep Ensemble | σ_max | 4.50 | — | — |
| | | | | |
| BNN-phy-mono (physics-regularized) | *k*_eff | **0.000161** | n/a | **0.9741** |
| BNN-baseline (reference) | *k*_eff | 0.000168 | n/a | 0.9581 |
| MC-Dropout | *k*_eff | — | — | — |
| Deep Ensemble | *k*_eff | — | — | — |

---

## Footnotes

**†** The total *k*_eff variance in the test set is σ ≈ 0.00077 (77 pcm at
the nominal operating point; CANONICAL §4d). At this scale, R² is sensitive
to small residual errors and should not be used as a primary comparison
metric. CRPS provides a more reliable measure of distributional accuracy for
near-constant outputs.

**‡** Best value per metric is in bold. The BNN's advantage lies in
calibration quality (ECE) and distributional accuracy (CRPS), not in point
prediction. Deep Ensemble achieves the highest stress R² (0.9531) and lowest
stress RMSE (~7.64 MPa) among all models. The physics-regularized BNN
achieves the best stress CRPS (4.350) and the lowest ECE, reflecting
tighter and better-calibrated predictive intervals.

ECE (expected calibration error) is not reported for MC-Dropout and Deep
Ensemble because per-output calibration curves were not computed in their
fixed-split evaluation files. This is a limitation of the current external
baseline evaluation, not an inherent property of those methods.

---

## Formatting notes for LaTeX conversion

When converting to LaTeX:

1. Use `\multirow` or a blank rule to visually separate the σ_max block from
   the *k*_eff block within each panel.
2. The "~" prefix on MC-D / DE RMSE values (e.g., ~7.66 MPa) indicates
   approximate values; render as ${\approx}7.66$ in LaTeX.
3. The `【待核实】` markers on ECE values must be resolved and removed before
   final manuscript submission.
4. Panel labels (a) and (b) should appear as sub-captions above each sub-table,
   not as separate figures.
5. Internal model labels (`bnn-phy-mono`, `bnn-baseline`) must not appear in
   the published table. Use only "physics-regularized surrogate" and
   "reference surrogate" (or abbreviated forms after first mention).

---

## Comparison with current Table 1 (what changed)

| Aspect | Before (current draft) | After (this revision) |
|--------|------------------------|----------------------|
| Bold metric | CRPS only | All metrics — best per column |
| Structure | Single flat table | Two panels: (a) point, (b) distributional |
| keff footnote | None | † explaining R² unreliability at 77 pcm scale |
| BNN vs DE framing | Implicit BNN dominance | Explicit: DE wins R²/RMSE, BNN wins CRPS/ECE |
| ECE column | Absent | Added for BNN variants; "—" for external baselines |
| PICP column | Present in both models | Retained in panel (b) |
| MPIW column | Present | Removed from main table (moved to SI) — see note below |

**Note on MPIW removal**: MPIW (mean prediction interval width) is retained in
the SI ablation table (Table S-ablation). Removing it from Table 1 reduces
column count and keeps the two-panel structure compact. If the editor or
reviewers request it, MPIW can be added back to panel (b) as a sixth column.
Values: phy-mono stress MPIW = 39.38 MPa; baseline = 40.21 MPa.
