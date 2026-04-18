# BNN Model Upgrade Plan

Date: 2026-04-18 (created) / 2026-04-18 (v2 — revised per user feedback)
Status: **Confirmed** — ready for execution

---

## 0. GPT vs Claude assessment + user corrections

### GPT correctly identified

1. **Physics regularization provides negligible improvement.**
   Confirmed. Across all primary iter2 outputs, baseline vs phy-mono R² differences
   are within 0.2–0.7%. Posterior acceptance rates are also nearly identical
   (baseline 0.60–0.64 vs phy-mono 0.58–0.62; baseline is actually slightly better).
   Sobol rankings are identical between models.

2. **Current BNN is already heteroscedastic.**
   Confirmed. `bnn_model.py:254-255` defines both `mu_head` and `logvar_head` as
   `BayesianLinear` layers. The logvar head produces input-dependent aleatoric
   variance. This is a full heteroscedastic BNN.

3. **Multi-fidelity iter1→iter2 is the most natural structural upgrade.**
   Agreed. The solver hierarchy (decoupled → coupled) is a genuine physics-based
   fidelity ladder, not an artificial construction.

4. **Conformal prediction = appendix level only.** Agreed.

5. **Active learning = not now.** Agreed.

### GPT was wrong on one critical claim (user confirmed retraction)

**GPT said**: "MCMC likelihood uses external 2% noise, NOT the surrogate's predicted variance."

**Reality** (verified in `run_posterior_0404.py:209-224`):
```python
def _log_likelihood(...):
    mu_raw, sigma_raw = _predict_single_bnn(model, sx, sy, x_full, device)
    # sigma_raw = sqrt(epistemic_var + aleatoric_var) from mc_predict()
    total_noise = np.sqrt(obs_noise**2 + sig_obs**2)  # line 221
    z = (y_obs - mu_obs) / (total_noise + 1e-30)
```

The likelihood **already combines** obs noise (2%) and surrogate total predictive
uncertainty (epistemic + aleatoric) via quadrature sum. GPT's "缺口 B" does not exist.
User explicitly retracted this claim on 2026-04-18.

### Claude's observations (retained from v1)

1. **The real bottleneck is iter2 temperature R² ≈ 0.59.**
   Multi-fidelity has the best chance of helping here, because iter1 temperatures
   (R² ~ 0.81–0.82) are much better predicted, and the iter1→iter2 correction
   should be a smaller/smoother function than the full x→iter2 mapping.

2. **iter2_keff has no iter1 counterpart.**
   keff only exists in iter2 (coupled criticality). Multi-fidelity cannot help
   this output directly — it must remain a direct x→keff mapping.
   Current R² = 0.87, which is acceptable.

3. **Narrative reframe is more important than model tricks.**
   The strongest paper is "complete uncertainty-to-risk pipeline for coupled nuclear
   simulations" — not "physics regularization improves BNN."

---

## 1. Immediate manuscript fix (before any new experiments)

The method section currently describes the posterior likelihood abstractly as
"induced by BNN posterior predictive mean and observation-noise model." This is
too vague and led even careful readers (GPT) to misinterpret it as external-noise-only.

**Required clarification** — change to something like:

> The likelihood variance combines an externally specified measurement-noise term
> and the BNN predictive uncertainty returned by the surrogate, where the latter
> aggregates epistemic (weight-posterior) and aleatoric (heteroscedastic head)
> components via quadrature sum:
> σ²_total = σ²_obs + σ²_surrogate(θ)

This must appear in the method section before submission, regardless of whether
multi-fidelity is pursued.

---

## 2. Execution plan

### Phase 1: Heteroscedastic ablation (low effort, high narrative value)

**Goal**: Prove the logvar head matters. Already present in model but never ablated.

**Tasks**:
- [x] 1.1 ~~Train a **homoscedastic BNN** variant~~ — **CODE DONE (2026-04-18)**:
      `bnn_model.py` BayesianMLP gains `homoscedastic=True` flag →
      replaces `logvar_head` (BayesianLinear) with `nn.Parameter log_noise`.
      `forward()`, `kl_divergence()` updated. All 7 downstream load sites patched.
      Model registered as `bnn-baseline-homo` in `model_registry_0404.py`.
      **Needs server training run to produce checkpoint.**
- [ ] 1.2 Evaluate on the same fixed test split: MAE, RMSE, R², PICP, MPIW, CRPS.
- [ ] 1.3 Compare calibration: are the heteroscedastic intervals better-calibrated
      near the 131 MPa stress threshold vs bulk?
- [ ] 1.4 Document finding (either direction is publishable).

### Phase 2: Multi-fidelity iter1→iter2 surrogate (main upgrade)

#### Phase 2.1: Three-part go/no-go gate

**This gate is output-specific, not all-or-nothing.**

- [x] **2.1A — Raw correlation**: **DONE (2026-04-18)** → saved to
      `results/mf_correlation_check.csv`. 6/7 pairs pass Pearson r > 0.8.
      Hcore_after fails linearly (r=0.096) but Spearman ρ=0.991.
      stress r=0.954, wall2 r=0.998, temperatures r~0.92.

- [x] **2.1B — Delta complexity**: **DONE (2026-04-18)** → `results/mf_gate_analysis.csv`.
      Only **2/7** outputs pass the residual gate (r>0.8 AND Var(Δ)<0.5×Var(y₂)):
      - **stress**: ratio=0.298, residual LR MAE 7.07 vs direct 12.18 (42% reduction)
      - **wall2**: ratio=0.005, coupling barely changes it
      Temperature outputs FAIL: Var(Δ)/Var(y₂) = 2.3–5.0 (coupling INCREASES variance).
      Hcore_after FAILS: r=0.096, ratio=1.48.
      keff: direct only (no iter1 pair).

- [x] **2.1C — Per-output gate decision**: **DONE (2026-04-18)**.
      | Output | Gate |
      |--------|------|
      | max_global_stress | **residual** |
      | wall2 | **residual** (trivial) |
      | avg_fuel_temp | direct |
      | max_fuel_temp | direct |
      | max_monolith_temp | direct |
      | monolith_new_temp | direct |
      | Hcore_after | direct |
      | keff | direct (always) |

      **Implication**: The MF residual architecture should use hybrid routing —
      residual path for stress+wall2, direct path for temperatures+Hcore+keff.
      This changes the architecture from the original plan.

**Output of Phase 2.1**: A table like:

| Output | Pearson r | Var(y₂) | Var(Δ) | ratio | x→y₂ MAE | x→Δ MAE | Gate |
|--------|-----------|---------|--------|-------|----------|---------|------|
| avg_fuel_temp | ? | ? | ? | ? | ? | ? | residual / direct |
| max_fuel_temp | ? | ? | ? | ? | ? | ? | residual / direct |
| ... | | | | | | | |
| keff | N/A | — | — | — | — | — | direct (always) |

#### Phase 2.2: Implementation (only for outputs that pass gate)

**Priority order of architectures**:

1. **Residual / correction (first priority)**:
   ```
   Stage 1: BNN_1(x) → ŷ₁        (predict iter1, 7 outputs)
   Stage 2: BNN_Δ(x, ŷ₁) → Δ̂     (predict Δ = y₂ − y₁, for gate-passing outputs)
   Final:   ŷ₂ = ŷ₁ + Δ̂          (for gate-passing outputs)
            ŷ₂_direct             (for gate-failing outputs + keff)
   ```
   - Physically interpretable: "coupled response = decoupled response + feedback correction"
   - Best narrative fit

2. **Stacked / compositional (second priority, only if residual underperforms)**:
   ```
   Stage 1: BNN_1(x) → ŷ₁
   Stage 2: BNN_2(x, ŷ₁) → ŷ₂    (all 8 iter2 outputs)
   ```
   - More flexible but harder to interpret
   - Risk of error propagation from stage 1

3. **Joint multi-task (not recommended for first pass)**:
   Shared backbone predicting iter1 + iter2 simultaneously.
   Save for future work if needed.

**Tasks**:
- [x] 2.2 ~~Implement multi-fidelity BNN~~ — **CODE DONE (2026-04-18)**:
      `bnn_multifidelity.py` defines `MultiFidelityBNN_Stacked` and
      `MultiFidelityBNN_Residual`. Both implement `predict_mc()`.
      `run_train_mf_0404.py` handles MF-specific training (Optuna + final train).
      `run_0404.py` dispatches MF models to `run_train_mf_0404.py`.
      `run_eval_0404.py` updated with MF-aware model loading + output reordering.
      Models registered: `bnn-mf-stacked`, `bnn-mf-residual` in registry.
      **Needs server training run to produce checkpoints.**
- [ ] 2.3 Train and evaluate on fixed test split.
      Key metrics per output:
      - MAE / RMSE / R²
      - PICP / MPIW / CRPS
      - Near-threshold stress subset (around 131 MPa)
- [ ] 2.4 **Small-sample regime test**: retrain with 20%, 40%, 60% of training data.
      If multi-fidelity advantage is most visible at low data, that strengthens
      the "sample efficiency" claim.
- [ ] 2.5 Run forward UQ + Sobol with best multi-fidelity model to verify
      sensitivity rankings are preserved.
- [ ] 2.6 Run posterior calibration with best multi-fidelity model.

**Implementation notes**:
- New model IDs: `bnn-mf-residual` (primary), `bnn-mf-stacked` (backup)
- DELTA_PAIRS already defined in `experiment_config_0404.py:129-137`
- keff always uses direct path
- Output dirs: `models/bnn-mf-residual/`, etc.
- Do NOT replace existing model artifacts

**Expected outcomes**:
- Temperature outputs (R² ~0.59): most likely to benefit → target ~0.7+
- Stress (R² ~0.92): marginal improvement at best
- keff (R² ~0.87): unchanged (direct model)
- Small-sample regime: clearer advantage expected

### Phase 3: Conformal calibration test (appendix supplement)

**Goal**: Post-hoc calibration wrapper for finite-sample coverage robustness.

**Tasks**:
- [ ] 3.1 Implement split conformal on residuals from best model.
- [ ] 3.2 Compare: raw BNN interval vs conformal-adjusted interval.
- [ ] 3.3 Report marginal coverage + near-threshold coverage + interval width.
- [ ] 3.4 Write as appendix section, not main contribution.

**Implementation notes**:
- Use calibration subset from validation split (not test)
- Do NOT retrain any model
- Target: 1 figure + 1 table for appendix

### Phase 4: Narrative integration

**Goal**: Reframe the paper's contribution structure around verified strengths.

**Tasks**:
- [ ] 4.1 Fix posterior likelihood description (see Section 1 above).
- [ ] 4.2 Rewrite method section to clearly present:
      (a) heteroscedastic BNN with epistemic + aleatoric decomposition
      (b) multi-fidelity architecture exploiting solver hierarchy (if Phase 2 succeeds)
      (c) complete uncertainty-to-risk pipeline as main contribution
- [ ] 4.3 Reposition "physics regularization" as appendix ablation study.
- [ ] 4.4 Main comparison becomes: direct BNN vs multi-fidelity BNN
      (instead of baseline vs phy-mono).

**Manuscript narrative framing**:

English:
> The coupled solver already exposes a natural two-level computational hierarchy:
> a decoupled first pass followed by a feedback-resolved coupled state. We represent
> the converged response as a correction to the first-pass decoupled state rather
> than a monolithic mapping from uncertain inputs to final outputs, thereby
> explicitly exploiting the hierarchical correlation within the coupling process.

中文:
> 耦合求解器本身已提供一个天然的两层计算层次：第一轮解耦响应与最终收敛态。
> 与将收敛态视为从不确定输入到最终输出的单步黑箱映射不同，我们将其表示为
> 对首轮响应的反馈修正，从而显式利用耦合流程中的层次相关性。

---

## 3. What NOT to do

- Do NOT implement active learning — it would change the paper's scope
- Do NOT stack all four upgrades simultaneously
- Do NOT abandon the UQ-to-risk pipeline narrative for a "model comparison" paper
- Do NOT assume multi-fidelity will definitely help — Phase 2.1 is a strict gate
- Do NOT overwrite existing model artifacts — new models get new directories
- Do NOT force all outputs through the same multi-fidelity path — per-output routing

---

## 4. Decision gates (v2 — stricter, per-output)

| Gate | Check | Pass condition | Action if FAIL |
|------|-------|----------------|----------------|
| 2.1A | iter1↔iter2 Pearson r | r > 0.8 per output | That output stays on direct path |
| 2.1B | Var(Δ) / Var(y₂) | ratio < 0.5 per output | That output stays on direct path |
| 2.1B+ | x→Δ vs x→y₂ validation MAE | Δ-route MAE notably lower | That output stays on direct path |
| 2.1C | Aggregate | ≥ 4/7 paired outputs pass A+B | If <4 pass: skip full multi-fidelity build; do only partial or demote to appendix |
| 2.3 | Multi-fidelity vs direct R² | Improvement > 0.03 on ≥1 primary output | Demote multi-fidelity to appendix |
| 2.4 | Small-sample advantage | Visible at 40% training data | Don't claim sample efficiency |

---

## 5. Paper positioning summary

| Element | Role in paper | Justification |
|---------|---------------|---------------|
| Multi-fidelity residual surrogate | **Main structural contribution** (if Phase 2 passes) | Exploits natural solver hierarchy |
| BNN epistemic/aleatoric decomposition + posterior-consistent UQ | **Core methodological framework** (retained) | Already clean; just needs clearer writing |
| Physics regularization (monotonicity) | Appendix ablation | Negligible effect demonstrated |
| Conformal calibration | Appendix supplement | Post-hoc validation, not core method |
| Active learning | Future work mention only | Out of scope |

---

## 6. Priority order and timeline

```
Phase 1   (heteroscedastic ablation)        → 1–2 days
Phase 2.1 (three-part go/no-go gate)        → 0.5–1 day
Phase 2.2–2.6 (multi-fidelity impl + eval)  → 3–5 days (if gate passes)
Phase 3   (conformal appendix)              → 1 day
Phase 4   (narrative rewrite)               → 2–3 days
```

Total: ~8–12 days if multi-fidelity is pursued; ~4–6 days if gate fails.

---

## Changelog

- **v1 (2026-04-18)**: Initial plan based on Claude's independent code verification.
- **v2 (2026-04-18)**: Revised per user feedback:
  - Phase 2.1 gate expanded from correlation-only to three-part check (A: correlation,
    B: delta complexity, C: per-output decision).
  - Residual multi-fidelity prioritized over stacked.
  - Per-output routing: outputs that fail gate stay on direct path; keff always direct.
  - Added manuscript clarification requirement (Section 1).
  - Added narrative framing templates (EN + CN).
  - User confirmed GPT's "缺口 B" retraction.
