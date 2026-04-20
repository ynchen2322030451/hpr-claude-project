# Manuscript Directory Structure

This directory contains two parallel manuscript drafts that must be kept in sync.

## Folders

| Folder | Description | Target |
|--------|-------------|--------|
| `0414_v4/` | Working draft (v4), bilingual txt format. Contains the most up-to-date structural outline, figure descriptions, appendix framework, and all supporting documents (revision plan, literature bank, verification log). | NCS (Nature Computational Science) |
| `nc_draft/bilingual/` | Formatted submission draft, bilingual `.tex` + `.txt`. Contains the LaTeX source and plain-text mirror with full abstract, main text, methods, acknowledgements, and CRediT author contributions. | NCS |

## Sync Rule

**Any content update must be applied to both folders simultaneously.**

This includes but is not limited to:
- Author list and affiliations
- CRediT author contribution statements
- Abstract text
- Main text sections (Introduction, Results, Discussion, Methods)
- Acknowledgements and funding
- Competing interests
- Reference list changes that affect in-text citations

## Known Differences

| Item | `0414_v4/` | `nc_draft/` |
|------|-----------|-------------|
| Corresponding author | T.Z. only | T.Z. only |
| Format | Plain text (.txt) | LaTeX (.tex) + plain text (.txt) |
| Supporting docs | Revision plan, literature bank, verification log, figure bank, source notes | None (submission-ready only) |

Corresponding author unified to T.Z. only (2026-04-19).

## Supporting Documents (in `0414_v4/` only)

- `NCS_REVISION_PLAN.md` — 20-task revision plan from GPT+Gemini review
- `LITERATURE_REFERENCE_BANK.md` — 110-ref library with 4-bucket classification and consensus rules
- `LITERATURE_VERIFICATION_LOG.md` — GPT 4-batch verification + Gemini cross-review + consensus
- `NCS_TODO.md` — Quick task checklist
- `GEMINI_AUDIT_CHECKLIST.md` — Gemini audit tracking
- `figures/` — Figure descriptions and figure bank
- `source_notes/` — Evidence summaries and BNN decision log
