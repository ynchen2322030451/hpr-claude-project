# Figure Layout Specification: Fig. 1 — Workflow Overview

> **Spec version**: 2026-04-24
> **Author**: manuscript editor
> **Status**: draft — to be reviewed before GPT mockup generation

---

## Figure identity

| Field | Value |
|-------|-------|
| Figure number | Figure 1 (main text) |
| Manuscript location | End of Introduction / beginning of Results, or as a standalone overview figure preceding Section 2.1 |
| Caption target file | `manuscript/nc_draft/en/manuscript_en.txt` and bilingual counterpart |
| Current version | `current_version.png` (this directory) |
| GPT mockup reference | `gpt_reference_mockup.png` (rename from `gpt样板图.png` before use) |

---

## Key message

**One sentence this figure must convey:**

> A single posterior predictive distribution — trained once from high-fidelity coupled simulation data — serves forward uncertainty propagation, variance-based sensitivity decomposition, and observation-conditioned parameter calibration without retraining, making the three downstream analyses structurally coherent.

The figure must make this "single source, three uses" structure immediately readable to a reader who has not yet read the text.

---

## Panel layout

The figure is a single-panel flow diagram with three tiers, arranged top-to-bottom (portrait orientation preferred for NCS single-column; landscape acceptable for two-column if width permits).

### Tier 1 — Data generation (top)

Left-to-right sequence of three blocks:

```
[8 input parameters]  →  [OpenMC + FEniCS  →  [Training dataset
(material / geometry)     coupled solver]        n = 3341 samples]
```

- Block 1 label: "8 uncertain input parameters" with a small annotation listing the four calibrated ones: E_intercept, alpha_base, alpha_slope, SS316_k_ref (the remaining four can be listed in parentheses as "fixed at nominal").
- Block 2 label: "High-fidelity coupled simulation" (do NOT write "HF solver", "OpenMC-FEniCS pipeline", "iter1/iter2", or any code-level identifier).
- Block 3 label: "Training dataset (n = 3341)" — include the split footnote "train / val / test = 2339 / 501 / 501" in small text below the block.

Arrow from block 1 to block 2: thin, no label.
Arrow from block 2 to block 3: thin, no label.

### Tier 2 — Surrogate training and the central distribution (middle)

Single wide block spanning the full figure width, visually larger than any other block:

```
[BNN training with physics-consistent monotonicity and inequality constraints]
                             ↓
              ╔══════════════════════════════════╗
              ║  Posterior Predictive             ║
              ║  Distribution  p(y | x, D)        ║
              ║  (shared across all analyses)     ║
              ╚══════════════════════════════════╝
```

- The BNN training block sits above the central box with a downward arrow.
- The central distribution box must be the largest single element in the figure. Use a double border or a filled background to distinguish it from the surrounding blocks.
- Inside the central box, a small illustrative probability density curve (e.g., a bell curve with shaded tails) is encouraged, representing a predictive distribution over one output. This is purely schematic — do not label it with specific numbers.
- Label below the central box: "Trained once; used without modification for all three downstream analyses"

Arrow from Tier 1 (training dataset) to BNN training block: medium weight, downward.

### Tier 3 — Three downstream analyses (bottom)

Three equal-width boxes arranged horizontally below the central distribution, connected to it by three downward arrows of equal weight:

```
        ╱               |                ╲
[Forward UQ]   [Sobol sensitivity]   [Posterior calibration]
```

Box labels and sub-labels:

| Box | Main label | Sub-label (smaller font) |
|-----|-----------|--------------------------|
| Left | "Forward UQ" | "Stress exceedance probability; coupling effect on output distributions" |
| Centre | "Sobol sensitivity decomposition" | "First-order and total-effect indices; dominant-parameter identification" |
| Right | "Posterior calibration" | "MCMC-based parameter inference; 90%-CI coverage assessment" |

The three boxes must have **identical width and height** — equal visual weight is mandatory.

### Coherence connector (bottom arc)

A curved bracket or arc below all three boxes, pointing upward into the three boxes, labeled:

> "Coherent evidence chain: shared distribution enforces consistency across analyses"

This connector is the visual payoff of the figure. It must be visually distinct (e.g., dashed arc with a label) but not so heavy that it competes with the central distribution box.

---

## Visual hierarchy

| Priority | Element | Treatment |
|----------|---------|-----------|
| 1 (highest) | Central posterior predictive distribution box | Largest box, filled background (light blue recommended), double border |
| 2 | BNN training block + arrow into central box | Bold border, medium font |
| 3 | Three downstream analysis boxes | Equal size, slightly smaller than BNN block, colored borders matching Section color scheme |
| 4 | Coherence connector arc | Dashed line, small label |
| 5 | Tier 1 data generation blocks | Smallest boxes, lightest weight |

The reader's eye should land on the central distribution box first, then follow the arrows downward to the three analyses, then follow the arc back upward to understand coherence. The data generation tier is background context, not the story.

---

## Color scheme (colorblind-friendly)

Use the Paul Tol "muted" or "bright" palette throughout. Do NOT use red/green as the sole distinguishing pair.

| Element | Recommended fill | Recommended border |
|---------|-----------------|-------------------|
| Input parameters block | White | Medium grey (#666666) |
| High-fidelity simulation block | Light grey (#E8E8E8) | Dark grey (#444444) |
| Training dataset block | Light grey (#E8E8E8) | Dark grey (#444444) |
| BNN training block | Pale amber (#FFF3CD) | Amber (#D4A017) |
| Central distribution box | Pale blue (#D6EAF8) | Strong blue (#2471A3), double border |
| Forward UQ box | Pale teal (#D1F2EB) | Teal (#1A9874) |
| Sobol sensitivity box | Pale purple (#EBD5F5) | Purple (#7D3C98) |
| Posterior calibration box | Pale orange (#FDEBD0) | Orange (#CA6F1E) |
| Coherence arc | — | Medium grey (#888888), dashed |
| All arrows | — | Dark grey (#444444), solid |

The teal / purple / orange triple for the three analyses must be distinguishable by both color and shape (border style variation is acceptable as a secondary cue).

---

## Typography

| Element | Font size (pt at final print size) | Weight |
|---------|-----------------------------------|--------|
| Figure title (if included) | 9 | Bold |
| Block main labels | 8 | Bold |
| Block sub-labels | 7 | Regular |
| Central distribution box main text | 9 | Bold |
| Central distribution box sub-text | 7 | Regular italic |
| Coherence arc label | 7 | Regular italic |
| Arrow labels (if any) | 7 | Regular |
| Footnote annotation (e.g., split sizes) | 6 | Regular |

Font family: Helvetica Neue, Arial, or Liberation Sans. Do NOT use matplotlib default (DejaVu Sans). The figure must remain legible when printed at NCS single-column width (88 mm).

---

## Data flow arrows

| From | To | Arrow style | Label |
|------|----|------------|-------|
| 8 input parameters | High-fidelity simulation | Thin solid | none |
| High-fidelity simulation | Training dataset | Thin solid | none |
| Training dataset | BNN training | Medium solid, downward | "n = 3341" (optional) |
| BNN training | Central distribution | Bold solid, downward | none |
| Central distribution | Forward UQ | Medium solid, downward-left | none |
| Central distribution | Sobol sensitivity | Medium solid, downward | none |
| Central distribution | Posterior calibration | Medium solid, downward-right | none |
| (Coherence) | All three analyses | Dashed arc, upward | "Coherent evidence chain" |

No bidirectional arrows. No feedback arrows from analyses back to distribution (the coherence is a property of sharing, not a loop).

---

## Anti-patterns: what NOT to do

The following are explicitly forbidden in this figure:

1. **No CJK characters** (Chinese, Japanese, Korean). The figure will be embedded in a PDF rendered by matplotlib/Inkscape with no CJK font. Use English throughout. CJK content belongs only in caption companion `.txt` files.

2. **No internal code identifiers** anywhere in the figure:
   - Forbidden: `iter1`, `iter2`, `iteration1`, `iteration2`, `iteration 1`, `iteration 2`
   - Forbidden: `level0`, `level2`, `bnn-baseline`, `bnn-phy-mono`, `data-mono-ineq`
   - Forbidden: `fixed_split`, `results_v3418`, any file path
   - Forbidden: `OpenMC`, `FEniCS` (may appear in a footnote or caption, not inside figure boxes)

3. **No "pass 1 / pass 2" language** for the coupled simulation iterations.

4. **No inequality in visual weight** between the three downstream analysis boxes. If one box is larger or uses a heavier border, that implies it is more important — the key message requires all three to be equal.

5. **No engineering flowchart decoration**: no diamond decision nodes, no loop-back arrows, no "START / END" terminators. This is a methodology diagram, not a software flowchart.

6. **No annotation boxes with numerical results** in this figure. Numbers (R², coverage, Sobol indices) belong in the results figures, not here.

7. **No "framework" or "pipeline" language** inside figure boxes. These are vague and uninformative.

8. **No "novel" / "proposed" / "our method" labeling** inside the figure. The figure describes the method; it does not evaluate it.

---

## Output specifications

| Parameter | Value |
|-----------|-------|
| Raster export | PNG, 300 dpi minimum (600 dpi preferred for NCS) |
| Vector export | PDF (preferred for submission) or SVG |
| Single-column width | 88 mm (NCS constraint) |
| Double-column width | 180 mm (NCS constraint) |
| Recommended layout | Portrait, single-column (88 mm wide); three-tier vertical flow |
| Aspect ratio | Approximately 1:1.4 (width:height) for single-column portrait |
| Filename (raster) | `fig1_workflow_v[date].png` |
| Filename (vector) | `fig1_workflow_v[date].pdf` |
| Embed fonts | Yes (for PDF) |
| Color space | RGB (sRGB) |

---

## Reference files in this directory

| File | Description |
|------|-------------|
| `current_version.png` | Current fig0_workflow used in `0414_v4` draft — engineering flowchart style, to be superseded |
| `gpt_reference_mockup.png` | Rename from `gpt样板图.png` before referencing in any document; this is the GPT-generated visual reference for the redesign |
| `layout_spec.md` | This file |

---

## Checklist before sending to figure production

- [ ] All text in figure is English only
- [ ] Central distribution box is visually the largest element
- [ ] Three downstream boxes are identical in size
- [ ] No code-level identifiers present
- [ ] Color scheme passes colorblind simulation (use Coblis or similar)
- [ ] Legible at 88 mm width single-column
- [ ] Both PNG (300 dpi) and PDF exported
- [ ] Fonts embedded in PDF
- [ ] Caption (in manuscript file) states the key message as its first sentence
