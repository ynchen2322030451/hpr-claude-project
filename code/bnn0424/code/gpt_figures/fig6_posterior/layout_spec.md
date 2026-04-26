# Figure Layout Specification: Fig. 5 — Sobol–Posterior Coherence

> **Spec version**: 2026-04-24
> **Author**: manuscript editor
> **Status**: draft — to be reviewed before GPT mockup generation
> **Note on numbering**: referred to internally as "fig6_posterior" but likely Figure 5 in the
> final manuscript. Confirm figure number against main text section count before submission.

---

## Figure identity

| Field | Value |
|-------|-------|
| Figure number | Figure 5 (main text, Section 2.4 / posterior calibration) |
| Manuscript section | "Observation-driven posterior inference and safety-feasible region" |
| Caption target file | `manuscript/nc_draft/en/manuscript_en.txt` and bilingual counterpart |
| Canonical data source | `results_v3418/experiments/posterior/bnn-phy-mono/rerun_4chain/benchmark_summary.csv` |
| Sobol data source | `results_v3418/experiments/sensitivity/bnn-phy-mono/sobol_results.csv` |

---

## Key message

**One sentence this figure must convey:**

> The posterior contracts most strongly along the parameter directions identified as dominant by Sobol analysis — E_intercept for coupled stress and alpha_base for effective multiplication factor — a coherence that arises because both analyses draw from the same posterior predictive distribution.

The figure must make the correspondence between Sobol-dominant parameters and strong posterior contraction visible without any explanatory text in the figure body itself. The three panels must tell a left-to-right story: (A) which parameters drive variance → (B) those same parameters show the most prior-to-posterior contraction → (C) the calibrated posterior yields accurate predictive coverage.

---

## Panel layout

Three horizontal panels, labeled (A), (B), (C), arranged left to right. Approximate width ratio: A : B : C = 1 : 1.2 : 1.

### Panel A — Sobol first-order sensitivity indices

**What to show**: Horizontal bar chart of first-order Sobol indices (S₁) for two outputs:
- Coupled steady-state maximum stress (σ_max)
- Coupled effective multiplication factor (k_eff)

Show one group of bars per output. Within each group, show all eight input parameters sorted by descending S₁ for that output.

**Data to use** (from CANONICAL_DATA_SUMMARY.md §5, bnn-phy-mono):

Stress S₁:

| Parameter | S₁ | 90% CI (lo, hi) | Note |
|-----------|-----|-----------------|------|
| E_intercept | 0.579 | (0.574, 0.583) | dominant |
| alpha_base | 0.169 | (0.164, 0.173) | |
| nu | 0.065 | (0.058, 0.071) | |
| SS316_k_ref | 0.051 | (0.046, 0.056) | calibrated |
| E_slope | 0.050 | (0.044, 0.057) | |
| alpha_slope | 0.027 | (0.021, 0.032) | calibrated |
| SS316_T_ref | 0.019 | (0.013, 0.024) | |
| SS316_alpha | 0.002 | (-0.004, 0.008) | CI spans zero — do NOT label as stable contributor |

k_eff S₁:

| Parameter | S₁ | 90% CI (lo, hi) | Note |
|-----------|-----|-----------------|------|
| alpha_base | 0.785 | (0.783, 0.788) | dominant |
| alpha_slope | 0.179 | (0.171, 0.187) | calibrated |
| nu | 0.028 | (0.020, 0.037) | |
| All others | < 0.01 | CI spans zero | do NOT label as stable contributors |

**Visual treatment**:
- Use error bars to show 90% CI for each bar.
- SS316_alpha (stress) must NOT be labeled "dominant" or colored the same as the dominant bars; its CI spans zero. Use a visually lighter bar with a note: "CI includes zero."
- Highlight the two dominant parameters by using the same accent colors that are used in Panel B: E_intercept in teal, alpha_base in orange. This color linkage is the primary visual bridge between Panel A and Panel B.
- All other parameters: light grey bars.
- x-axis: "First-order Sobol index (S₁)", range 0.0 to 1.0.
- y-axis: parameter names. Use the paper-facing names specified in the terminology section below — never raw column names.
- Two sub-panels within Panel A, stacked vertically: top for stress, bottom for k_eff. Both share the same color scheme for E_intercept (teal) and alpha_base (orange).

**What NOT to show**: Total-effect indices (S_T) may appear as a secondary overlay (open circles or triangles) but must not dominate. If space is tight, omit S_T entirely; state in caption that S_T values are in the Supplementary Information.

### Panel B — Prior-to-posterior contraction for the four calibrated parameters

**What to show**: Violin plot or overlapping density curves showing prior distribution and posterior distribution for each of the four calibrated parameters, for a representative benchmark case. Show all four parameters in a 2×2 or 4×1 arrangement within the panel.

**Four calibrated parameters**: E_intercept, alpha_base, alpha_slope, SS316_k_ref.

**Visual treatment**:
- Prior: shown as a light grey filled density or thin outline distribution.
- Posterior: shown as a colored filled density. Use the same accent color as Panel A for E_intercept (teal) and alpha_base (orange). Use neutral colors (grey-blue, grey-purple) for alpha_slope and SS316_k_ref.
- The vertical span of the posterior distribution relative to the prior is the visual measure of contraction. For E_intercept and alpha_base, the posterior should visibly narrower than the prior. For alpha_slope and SS316_k_ref, contraction will be weaker — show this honestly.
- Each sub-panel within B should be labeled with the paper-facing parameter name (see terminology section).
- A small "Prior" and "Posterior" legend within Panel B.
- Do NOT annotate specific posterior mean values inside the panel. Numerical values belong in the Supplementary Information table.
- The representative case to use: a "near-threshold" stress case is preferable because coverage is highest (0.958) and the posterior is most informative. State "representative near-threshold case" in the caption.

**Coherence signal (critical)**: The two parameters with strong Sobol S₁ (E_intercept for stress, alpha_base for k_eff) should show visually stronger contraction. The two weaker parameters (alpha_slope, SS316_k_ref) should show less contraction. If the actual posterior data does not show this pattern clearly for the representative case chosen, select a different representative case from the 18 benchmarks, or show the mean contraction width across all 18 cases (bar chart of posterior-to-prior width ratio). Do NOT artificially emphasize contraction — show what the data shows.

**MCMC convergence note**: add a small annotation inside Panel B: "R-hat ≤ 1.010; acceptance 0.58–0.63". Do not add any other numerical values inside the panel.

### Panel C — Posterior predictive accuracy

**What to show**: Scatter plot of posterior-predictive mean versus true (high-fidelity) output values, for the 18 benchmark cases, for the primary output used in calibration (coupled steady-state maximum stress σ_max).

**Data to use** (from benchmark_summary.csv):
- x-axis: true coupled stress (MPa)
- y-axis: posterior predictive mean (MPa)
- Error bars: 90% credible interval half-width
- n = 18 points; color each point by stress category: low-stress (light teal), near-threshold (medium amber), high-stress (dark red-brown)
- Add a 1:1 reference line (thin grey dashed)
- Add a horizontal dashed line at 131 MPa (thin dark grey, labeled "131 MPa threshold")
- Do NOT add a vertical threshold line — the threshold applies to the predicted value, not the true value axis

**Annotations inside Panel C**:
- "90%-CI coverage: 0.861 (62/72 outputs)"
- "Low-stress: 0.708; Near-threshold: 0.958; High-stress: 0.917"
- Place these as a small text block in the lower-right corner (not in an annotation box)
- Font size: 7 pt

**What NOT to show in Panel C**: prior predictive. This is a posterior result panel, not a prior-vs-posterior comparison.

---

## Inter-panel visual connection (A → B)

The color linkage between A and B is the primary mechanism for communicating the Sobol–posterior coherence message.

- E_intercept: teal (#1A9874) in both Panel A bars and Panel B density fills
- alpha_base: amber-orange (#D4A017) in both Panel A bars and Panel B density fills
- alpha_slope and SS316_k_ref: neutral grey-blue (#5B8DB8) and grey-purple (#7D6B9E) respectively

Add a thin bracket or dashed connecting line between the dominant bars in Panel A and the corresponding density panels in Panel B, if space permits. This is optional — the color match alone is sufficient if panel spacing makes a connecting line visually cluttered.

Do NOT add text arrows saying "Sobol dominant → strongest contraction" — this is an interpretation to be stated in the caption and main text, not annotated inside the figure.

---

## Visual hierarchy

| Priority | Element | Treatment |
|----------|---------|-----------|
| 1 (highest) | Dominant parameter bars in A + dominant posteriors in B (E_intercept teal, alpha_base amber) | Strongest colors, full opacity |
| 2 | Error bars on Sobol indices in A | Clearly visible but not distracting |
| 3 | 1:1 line and 131 MPa threshold in C | Thin dashed lines |
| 4 | Secondary Sobol bars (non-dominant parameters) | Light grey |
| 5 | Prior distributions in B | Light grey, 50% opacity |
| 6 | Panel labels (A), (B), (C) | Bold, 9 pt |

---

## Color scheme (colorblind-friendly)

| Element | Color | Hex |
|---------|-------|-----|
| E_intercept (dominant, stress) | Teal | #1A9874 |
| alpha_base (dominant, keff) | Amber-orange | #D4A017 |
| alpha_slope | Grey-blue | #5B8DB8 |
| SS316_k_ref | Grey-purple | #7D6B9E |
| Other non-calibrated parameters | Light grey | #AAAAAA |
| SS316_alpha (CI spans zero) | Very light grey | #CCCCCC |
| Prior distributions | Light grey fill | #DDDDDD at 50% opacity |
| Posterior distributions | Per-parameter color above | 80% opacity |
| Low-stress scatter (C) | Light teal | #76C7C0 |
| Near-threshold scatter (C) | Amber | #E8A838 |
| High-stress scatter (C) | Dark red-brown | #8B3A3A |
| 1:1 reference line | Medium grey | #888888 dashed |
| 131 MPa threshold line | Dark grey | #444444 dashed |

All color pairs used to distinguish categories must pass the Coblis colorblind simulator for deuteranopia and protanopia. The teal/amber pair is selected specifically for this criterion.

---

## Typography

| Element | Font size (pt) | Weight |
|---------|---------------|--------|
| Panel labels (A), (B), (C) | 9 | Bold |
| Axis titles | 8 | Bold |
| Tick labels | 7 | Regular |
| Parameter name labels in A | 7 | Regular |
| Contraction annotations in B | 7 | Regular |
| Coverage text block in C | 7 | Regular |
| Legend text | 7 | Regular |
| MCMC convergence annotation in B | 6 | Regular italic |

Font family: Helvetica Neue, Arial, or Liberation Sans. No CJK fonts. No matplotlib default (DejaVu Sans).

---

## Parameter name vocabulary (mandatory — used in all axis labels and legends)

| Internal code name | Paper-facing label for figure |
|-------------------|-------------------------------|
| E_intercept | E_intercept (Young's mod. intercept) |
| E_slope | E_slope |
| nu | ν (Poisson's ratio) |
| alpha_base | α_base (thermal expansion intercept) |
| alpha_slope | α_slope (thermal expansion slope) |
| SS316_T_ref | T_ref (SS316) |
| SS316_k_ref | k_ref (SS316) |
| SS316_alpha | α (SS316) |
| iteration2_max_global_stress | σ_max (coupled) |
| iteration2_keff | k_eff (coupled) |

Do not use any internal code name (raw column name or variable name from the analysis scripts) inside the figure. The subscript notation (e.g., α_base) is preferred where the figure renderer supports it; otherwise use plain text (alpha_base) without underscore ambiguity.

---

## Data flow within the figure

The figure does not show a process flow in the same sense as Fig. 1. Instead, it shows an evidential correspondence:

```
Panel A: sensitivity attribution  ──(color linkage)──►  Panel B: posterior contraction
                                                              │
                                                              ▼
                                                         Panel C: predictive accuracy
                                                         (validates the posterior)
```

There are no arrows between panels in the figure itself. The visual bridge is purely the color encoding. The caption explains the correspondence in words.

---

## Evidence constraints and anti-patterns

### Mandatory evidence constraints

1. **Sobol CI spans zero for SS316_alpha** (stress output): this parameter's bar in Panel A must be visually de-emphasized (very light grey) and must not be placed in the same visual group as the dominant parameters. The caption must state: "SS316_alpha is omitted from the dominant group because its 90% confidence interval includes zero."

2. **Coverage 0.861 must be shown, not rounded up**: do not write "approximately 90% coverage" in the figure annotation. Write "0.861 (62/72)".

3. **Low-stress coverage 0.708**: must appear in Panel C annotation (see above). Do not omit it. It is a limitation, not an error.

4. **Posterior contraction strength must reflect actual data**: do not exaggerate E_intercept or alpha_base contraction relative to what the posterior samples show. If the representative case chosen shows weak contraction, either select a different case (preferring near-threshold cases where contraction is strongest) or show mean statistics across all 18 cases.

5. **No comparison to prior in Panel C**: Panel C is a predictive accuracy plot, not a prior-vs-posterior comparison. Adding prior predictive scatter to Panel C would conflate two separate questions.

6. **HF rerun in Panel C**: the 18 benchmark "true" values are outputs from the test split of the high-fidelity coupled simulation dataset. They are NOT nearest-neighbor retrievals. The caption must be clear that "true" = held-out high-fidelity simulation outputs from the test set, not re-run simulations triggered by the posterior. See evidence-policy: nearest-neighbour HF retrieval ≠ HF rerun validation.

### Anti-patterns: what NOT to do

1. **No CJK characters** anywhere in the figure.

2. **No internal model identifiers**: do not write "bnn-phy-mono", "level2", "data-mono-ineq", "phy-mono", "results_v3418" in the figure.

3. **No "validated" language** inside the figure. Use "posterior predictive vs. true output" not "validated against high-fidelity".

4. **No "dominant" label on SS316_alpha**. Its CI spans zero.

5. **No mixing of 1-chain and 4-chain results**: all posterior values must come from the 4-chain canonical run. Deprecated 1-chain values (coverage 0.875, acceptance 0.47–0.61) must not appear.

6. **No annotation boxes with interpretation text** inside the panels (e.g., do not add a box saying "Sobol → posterior coherence"). This interpretation belongs in the caption and main text.

7. **No title bar above the figure** ("Figure 5: Sobol–posterior coherence"). The figure number and title appear in the caption, not inside the figure image.

8. **Do not bold or annotate alpha_slope** as a dominant k_eff driver in Panel B. Its S₁ = 0.179 makes it secondary. It has a calibrated posterior, but it should not be visually emphasized alongside alpha_base.

---

## Output specifications

| Parameter | Value |
|-----------|-------|
| Raster export | PNG, 300 dpi minimum (600 dpi preferred) |
| Vector export | PDF (preferred for NCS submission) or SVG |
| Single-column width | 88 mm |
| Double-column width | 180 mm |
| Recommended layout | Landscape (three panels side by side), double-column (180 mm wide) |
| Aspect ratio | Approximately 1:0.55 (width:height) for double-column landscape |
| Filename (raster) | `fig5_sobol_posterior_coherence_v[date].png` |
| Filename (vector) | `fig5_sobol_posterior_coherence_v[date].pdf` |
| Embed fonts | Yes (for PDF) |
| Color space | RGB (sRGB) |

---

## Caption guidance (for manuscript file, not inside figure)

The caption first sentence must state the key message:

> "The posterior contracts most strongly along the parameter directions that explain the greatest fraction of output variance."

Follow with one sentence per panel:

> "(A) First-order Sobol indices for coupled stress and k_eff; E_intercept accounts for 58% of stress variance and alpha_base for 79% of k_eff variance (90% confidence intervals shown; SS316_alpha excluded from stable contributors because its CI includes zero). (B) Prior (grey) and posterior (colored) distributions for the four calibrated parameters in a representative near-threshold benchmark case; contraction is strongest for E_intercept (teal) and alpha_base (amber), consistent with their dominant Sobol indices. (C) Posterior-predictive mean versus true coupled stress for 18 benchmark cases; error bars show 90% credible intervals; 90%-CI coverage is 0.861 overall (low-stress: 0.708; near-threshold: 0.958; high-stress: 0.917)."

Do not repeat the key message claim in the main text without citing the figure.

---

## Checklist before sending to figure production

- [ ] Panel A: error bars on all bars, SS316_alpha visually de-emphasized
- [ ] Panel A: E_intercept teal, alpha_base amber — same colors as Panel B
- [ ] Panel A: no raw column names on y-axis
- [ ] Panel B: prior grey, posterior colored, contraction visible for dominant parameters
- [ ] Panel B: MCMC convergence note (R-hat ≤ 1.010; acceptance 0.58–0.63) present
- [ ] Panel B: no numerical posterior mean values annotated inside panel
- [ ] Panel C: coverage annotation "0.861 (62/72)" present with stratified breakdown
- [ ] Panel C: 131 MPa threshold line present and labeled
- [ ] Panel C: 1:1 reference line present
- [ ] All text English only, no CJK
- [ ] No internal model identifiers (bnn-phy-mono, etc.)
- [ ] No 1-chain deprecated values
- [ ] Colors pass colorblind simulation
- [ ] Legible at 180 mm double-column width
- [ ] PNG (300 dpi) and PDF exported
- [ ] Fonts embedded in PDF
