# Publication Figure Style Spec — bnn0414

All sub-figures in `bank/` must conform. No exceptions, no per-script overrides.

## 1. Dimensions
- Single-column width: 88 mm = 3.46 in
- Double-column width: 180 mm = 7.09 in (use 7.1 in)
- Default main figure: 7.1 in wide
- Height: content-driven, avoid >9 in or <2 in per figure

## 2. Typography
- Font: sans-serif (Arial > Helvetica > DejaVu Sans)
- Axis labels: 8–9 pt
- Tick labels: 7–8 pt
- Panel labels: 9–10 pt, **bold italic**, placed inside axes at (-0.08, 1.05)
- Legend: 7 pt, frameon=False
- Minimum visible text: 7 pt (nothing smaller)
- No CJK glyphs in any figure

## 3. Lines
- Main data line: 1.5 pt
- Auxiliary line: 0.8 pt
- Reference / identity line: 0.6 pt dashed
- Error bars: 0.8 pt, capsize 2
- All figures use the same widths; no per-script variation

## 4. Colours (semantic, immutable)
| Semantic role | Hex | Name |
|---|---|---|
| BNN main model | #1f3b73 | deep blue |
| Reference / baseline | #707070 | mid gray |
| Posterior | #8c3a3a | dark red |
| Prior | #a9b8d6 | light blue-gray |
| Coupled / main | #1f3b73 | (same as BNN main) |
| Uncoupled | #9a8a78 | warm gray |
| CI crosses zero | #b0b0b0 | light gray |
| Reference line | #444444 | charcoal |
| Observed / true value | #222222 | near-black |
| Density underlay | same as scatter colour, alpha 0.08 | – |

No other colours allowed without spec amendment.

## 5. Scatter / density
- Default scatter: s=8, alpha=0.4, edgecolors="none"
- For dense parity plots: use hexbin or Gaussian KDE density underlay
  (alpha 0.08–0.12) + foreground scatter (alpha 0.6, s=6)
- Error bars on random subsample only (n≤150), rest scatter-only

## 6. Information density
- Figure face: maximum 2 metrics per panel, as plain text (no rounded box)
- Use `add_metric_text()` helper, not matplotlib `ax.text(..., bbox=...)`
- Everything else goes in caption or appendix
- No "annotation box" pattern anywhere

## 7. Spacing
- constrained_layout=True (never tight_layout)
- subplot hspace ≥ 0.35, wspace ≥ 0.30
- Title pad: 6 pt
- Label pad: 4 pt
- Tick length: 4 pt major, 2 pt minor
- Tick width: 0.6 pt

## 8. Axes
- Top + right spines off
- Left + bottom spines: 0.6 pt, color #333333
- White background (facecolor="white")
- No background grid (grid off)

## 9. Export
- All figures via `figure_io.savefig(fig, stem, out_dir)`
- Formats: pdf + svg + png@600dpi
- PPTX: batch via `export_pptx.py` after all sub-figures are done
- Naming: `{bank_id}_{slug}.{ext}` in bank; `fig{N}_{slug}.{ext}` in compose

## 10. Anti-patterns (forbidden)
- Rounded-corner annotation boxes (`bbox=dict(boxstyle="round,pad=...")`)
- Rainbow or jet/turbo colormaps
- Grid lines in scatter/bar plots
- Panel labels floating outside axes
- 5 pt text anywhere
- "marketing" language in titles
- Multiple legends in one panel
- Equal-weight panel layouts when content has clear primary/secondary hierarchy
