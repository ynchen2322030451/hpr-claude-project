# Figure Audit Report
# CJK Filenames and Vocabulary Compliance
# Generated: 2026-04-24
# Scope: code/bnn0424/code/gpt_figures/ and manuscript/0414_v4/figures/

---

## Part 1: CJK Filename Audit

Five files in `code/bnn0424/code/gpt_figures/` carry CJK characters ("样板图", meaning
"template/mockup image") in their filenames. All five are GPT-generated reference
mockups used during figure design. They are not shipped to the journal, but CJK
filenames risk encoding failures on CI systems, Windows paths, and some shell tools.

File existence was verified by direct read attempts (4 read successfully; 1 returned
a size-exceeded error, meaning the file exists but is too large to display).

| # | Current path (relative to repo root) | Status | Proposed filename |
|---|--------------------------------------|--------|-------------------|
| 1 | code/bnn0424/code/gpt_figures/fig6_posterior/gpt样板图.png | CONFIRMED EXISTS | gpt_reference_mockup.png |
| 2 | code/bnn0424/code/gpt_figures/fig4_sobol/gpt样板图.png | CONFIRMED EXISTS | gpt_reference_mockup.png |
| 3 | code/bnn0424/code/gpt_figures/fig2_predictive/gpt样板图.png | CONFIRMED EXISTS | gpt_reference_mockup.png |
| 4 | code/bnn0424/code/gpt_figures/fig3_forward/gpt样板图.png | CONFIRMED EXISTS | gpt_reference_mockup.png |
| 5 | code/bnn0424/code/gpt_figures/fig0_workflow/gpt样板图.png | EXISTS (size > 2000px, unrenderable) | gpt_reference_mockup.png |

Rename action: within each subdirectory the proposed name `gpt_reference_mockup.png`
is unique, so no collision arises. Renaming can be done with a single shell loop:

    for d in fig6_posterior fig4_sobol fig2_predictive fig3_forward fig0_workflow; do
        mv "code/bnn0424/code/gpt_figures/${d}/gpt样板图.png" \
           "code/bnn0424/code/gpt_figures/${d}/gpt_reference_mockup.png"
    done

These files are working assets, not canonical results. Renaming carries no risk to
frozen artifacts or experiment reproducibility.

---

## Part 2: PNG Content Audit — Rendered Inside the Mockup Images

Visual inspection was performed on all gpt_figures mockups that could be rendered.
Results are listed per file. For the production manuscript PNGs in
`manuscript/0414_v4/figures/`, all files exceed the 2000px read limit and could
not be visually inspected in this session; they require manual or script-based audit.

### 2a. gpt_figures mockups (directly inspected)

| File | CJK in pixel content | Internal vocabulary violations | Notes |
|------|----------------------|-------------------------------|-------|
| fig6_posterior/gpt样板图.png | NONE | NONE detected | Uses E_intercept, alpha_base, k_base, HTC_scale — all correct |
| fig4_sobol/gpt样板图.png | NONE | NONE detected | Uses "Coupled maximum stress", alpha base, E intercept — all correct; CI-span-zero items shown in grey with "(not clearly different from zero)" |
| fig2_predictive/gpt样板图.png | NONE | NONE detected | Uses "High-fidelity simulation" and "BNN predictive mean" — correct |
| fig3_forward/gpt样板图.png | NONE | **VIOLATION FOUND** | See Section 3 below |
| fig0_workflow/gpt样板图.png | Cannot inspect (size limit) | Unknown — requires manual check | See unresolved items |

### 2b. Production manuscript PNGs (manuscript/0414_v4/figures/)

All files listed below could not be visually inspected because their pixel dimensions
exceed the tool's 2000x2000px limit. Manual inspection or a script-based text-
extraction pass (e.g., pdftotext on PDF equivalents, or OCR) is required to confirm
absence of CJK or forbidden vocabulary in rendered pixel content.

| File | Inspectable in this session | Recommendation |
|------|-----------------------------|----------------|
| fig0_workflow.png | NO (size exceeded) | Inspect PDF or source .py |
| fig1_accuracy.png | NO (size exceeded) | Inspect PDF or source .py |
| fig2_predictive.png | NO (size exceeded) | Inspect PDF or source .py |
| fig3_forward.png | NO (size exceeded) | Inspect PDF or source .py |
| fig4_sobol.png | NO (size exceeded) | Inspect PDF or source .py |
| fig5_physics.png | NO (size exceeded) | Inspect PDF or source .py |
| fig6_posterior.png | NO (size exceeded) | Inspect PDF or source .py |
| fig7_efficiency.png | NO (size exceeded) | Inspect PDF or source .py |
| figA1_model_validation.png | NO (size exceeded) | Inspect PDF or source .py |
| figA2_physics_robustness.png | NO (size exceeded) | Inspect PDF or source .py |
| figA3_efficiency.png | NO (size exceeded) | Inspect PDF or source .py |
| figA4_sobol_detail.png | NO (size exceeded) | Inspect PDF or source .py |
| figB2_homo_ablation.png | NO (size exceeded) | Inspect PDF or source .py |
| figB3_model_comparison.png | NO (size exceeded) | Inspect PDF or source .py |
| figB3b_small_sample.png | NO (size exceeded) | Inspect PDF or source .py |
| figE_mcmc_diagnostics.png | NO (size exceeded) | Inspect PDF or source .py |
| figS1_sobol_convergence.png | NO (size exceeded) | Inspect PDF or source .py |
| figS2_prior_sensitivity.png | NO (size exceeded) | Inspect PDF or source .py |
| figS3_noise_sensitivity.png | NO (size exceeded) | Inspect PDF or source .py |
| figS4_ood.png | NO (size exceeded) | Inspect PDF or source .py |
| figS5_external_calib.png | NO (size exceeded) | Inspect PDF or source .py |
| figS6_bnn_architecture.png | NO (size exceeded) | Inspect PDF or source .py |
| figS7_reactor_geometry.png | NO (size exceeded) | Inspect PDF or source .py |

---

## Part 3: Figure Vocabulary Audit

### Rules (from CLAUDE.md)

| Forbidden in figures | Required substitute |
|----------------------|---------------------|
| iter1, iter2, iteration1, iteration2, "pass 1", "iter 1", "iter 5" | "Uncoupled pass" / "Coupled steady state" |
| level0, Level 0, baseline | "Reference surrogate" |
| level2, Level 2, data-mono-ineq | "Physics-regularized surrogate" |
| Any internal model ID (data-mono, phy-mono, bnn-baseline, etc.) | Descriptive scientific name only |
| CJK characters | English equivalents or N/A |

### Violation found in inspected mockup

**fig3_forward/gpt样板图.png** — CONFIRMED VIOLATION

The x-axis labels inside the rendered image read:
- "Uncoupled pass (iter 1)"  — the parenthetical "(iter 1)" is forbidden
- "Coupled steady state (iter 5)" — the parenthetical "(iter 5)" is forbidden

The figure caption text block also uses "iter 1" and "iter 5" in parenthetical notes.

This is the GPT reference mockup, not yet the production figure. The production script
`code/bnn0414/code/figures/compose/fig0_workflow.py` was inspected and correctly uses
"Uncoupled pass" and "Coupled steady state" without any raw iteration labels. However,
if the fig3 production script (not yet inspected) follows the mockup, it will carry
the same violation.

### Plotting scripts to audit for vocabulary compliance

The following scripts are listed as priority targets for vocabulary inspection.
`code/bnn0414/` is read-only archive; production scripts should be in `code/bnn0424/`.

| Priority | Script path to check | Risk |
|----------|----------------------|------|
| HIGH | code/bnn0424/code/figures/*/fig3_forward*.py | iter label violation confirmed in mockup |
| HIGH | code/bnn0424/code/figures/*/fig5_physics*.py | model-level labels likely |
| HIGH | code/bnn0424/code/figures/*/figA1_model_validation*.py | model-level labels likely |
| HIGH | code/bnn0424/code/figures/*/figB3_model_comparison*.py | model ID labels likely |
| MEDIUM | code/bnn0424/code/figures/*/fig1_accuracy*.py | axis labels, column names |
| MEDIUM | code/bnn0424/code/figures/*/figA4_sobol_detail*.py | may reuse Sobol column names |
| LOW | code/bnn0414/code/figures/compose/fig0_workflow.py | INSPECTED — CLEAN |
| LOW | code/bnn0414/code/figures/compose/figS7_reactor_geometry.py | INSPECTED — CLEAN |

Note: bnn0414 scripts are read-only archive. Any fixes must be made in bnn0424 equivalents.

---

## Part 4: Recommended Actions

Listed in priority order.

### Immediate (before next journal submission)

1. **Rename 5 CJK-named gpt_figures files** using the shell loop in Part 1.
   Risk: zero (working files only, no downstream dependencies).

2. **Fix fig3_forward mockup vocabulary** — if the production fig3 plotting script
   follows the mockup convention of "(iter 1)" / "(iter 5)" labels, strip these
   parentheticals from axis labels and all caption text blocks embedded in the figure.
   Correct form: "Uncoupled pass" and "Coupled steady state" with no iteration number
   suffix.

3. **Audit the fig3_forward production script** in code/bnn0424. Locate any string
   containing "iter", "iteration", or a raw number suffix in axis tick labels, legend
   entries, or annotated text strings. Replace per vocabulary table above.

### Near-term (before internal review deadline)

4. **Script-based vocabulary scan** — run a grep over all plotting scripts in
   code/bnn0424/code/figures/ for the patterns: `iter[12]`, `level[02]`, `baseline`,
   `data-mono`, `phy-mono`, `bnn-baseline`. Each hit requires case-by-case assessment
   (some may be path strings in load calls, not rendered text).

5. **Audit model-comparison figures** (figB3_model_comparison, figA1_model_validation,
   fig5_physics) for `level0`/`level2`/`data-mono-ineq`/`bnn-baseline` in legend
   labels. These figures are the highest-risk for internal ID leakage.

6. **Verify production manuscript PNGs** by inspecting the PDF equivalents in
   manuscript/0414_v4/figures/ (PDF files are typically smaller and may be readable)
   or by running a text-extraction command on the PDF files.

### Lower priority (cleanup)

7. Add a pre-commit hook or CI check that rejects filenames matching `[^\x00-\x7F]+`
   in the figures directories, to prevent future CJK filename introductions.

---

## Part 5: Overall Risk Assessment

| Risk domain | Level | Basis |
|-------------|-------|--------|
| CJK in filenames (gpt_figures) | LOW | Working files only; not shipped to journal; easy to fix |
| CJK rendered inside figure pixels | LOW (known) / UNKNOWN (production PNGs) | Inspected mockups are clean; production PNGs unverifiable at current tool resolution |
| Vocabulary violation in mockups | MEDIUM | One confirmed violation (fig3_forward iter labels) in GPT mockup; production script not yet inspected |
| Vocabulary violation in production scripts | MEDIUM | fig0_workflow.py confirmed clean; other high-risk scripts not yet read |
| model-ID leakage in comparison figures | MEDIUM-HIGH | figB3_model_comparison, figA1 are structurally the most likely to use level0/level2 labels |

**Overall risk: MEDIUM.** The CJK filename issue is low-risk and trivially fixed. The
more substantive risk is vocabulary leakage of internal iteration or model-level labels
into rendered figures, confirmed in one mockup and unverified in production scripts.
Resolution requires a targeted script audit of the fig3 and comparison-figure scripts
in code/bnn0424.

---

## Evidence flags

| Claim | Source | Status |
|-------|--------|--------|
| fig6_posterior/gpt样板图.png exists and is CJK-named | Direct read attempt (image rendered) | CONFIRMED |
| fig4_sobol/gpt样板图.png exists and is CJK-named | Direct read attempt (image rendered) | CONFIRMED |
| fig2_predictive/gpt样板图.png exists and is CJK-named | Direct read attempt (image rendered) | CONFIRMED |
| fig3_forward/gpt样板图.png exists and is CJK-named | Direct read attempt (image rendered) | CONFIRMED |
| fig0_workflow/gpt样板图.png exists | File exists (read error = size exceeded, not missing) | CONFIRMED (content unverifiable) |
| fig3_forward mockup contains "(iter 1)" and "(iter 5)" labels | Visual inspection of rendered PNG | CONFIRMED VIOLATION |
| fig4_sobol mockup is vocabulary-clean | Visual inspection of rendered PNG | CONFIRMED CLEAN |
| fig6_posterior mockup is vocabulary-clean | Visual inspection of rendered PNG | CONFIRMED CLEAN |
| fig2_predictive mockup is vocabulary-clean | Visual inspection of rendered PNG | CONFIRMED CLEAN |
| fig0_workflow.py production script is clean | Direct code read (lines 183-194) | CONFIRMED CLEAN |
| figS7_reactor_geometry.py production script is clean | Direct code read | CONFIRMED CLEAN |
| Production manuscript PNGs have no CJK | UNVERIFIABLE (all exceed size limit) | 【待核实：需手动检查或通过 PDF 文本提取工具验证】 |
| fig3_forward production script uses/avoids iter labels | NOT INSPECTED | 【待核实：需读取 code/bnn0424 中对应脚本】 |

---

## Unresolved items

- 【待核实：fig0_workflow/gpt样板图.png 图像内容未能渲染 (尺寸超限) -> 需手动打开确认是否存在 CJK 渲染文字或 iter/level 词汇违规】
- 【待核实：fig3_forward 生产脚本 (code/bnn0424/code/figures/) 是否将 mockup 中的 "(iter 1)"/"(iter 5)" 标注复制到生产图 -> 需读取对应 .py 文件】
- 【待核实：code/bnn0424/code/figures/ 下的高风险脚本 (fig5_physics, figA1_model_validation, figB3_model_comparison) 是否包含 level0/level2/data-mono-ineq 文字 -> 需 grep 扫描】
- 【待核实：manuscript/0414_v4/figures/ 中的 23 个生产 PNG 文件是否含有 CJK 渲染字符 -> 建议用 pdftotext 或 OCR 工具对 PDF 等效文件进行文本提取核查】
