# NC Draft — File Sync Guide

## Structure

```
nc_draft/
├── README.md                    ← this file
├── convert_to_docx.py           ← txt → docx converter (both versions)
├── manuscript.txt               ← original EN-only source (kept for reference)
├── supplementary_information.txt← original EN-only SI source (kept for reference)
│
├── en/                          ← English-only version
│   ├── manuscript_en.txt        ← [SOURCE] English manuscript
│   ├── manuscript_en.tex        ← LaTeX version
│   ├── manuscript_en.pdf        ← compiled PDF
│   ├── manuscript_en.docx       ← Word version
│   ├── supplementary_information_en.txt   ← [SOURCE] English SI
│   ├── supplementary_information_en.tex   ← LaTeX SI (with figures)
│   ├── supplementary_information_en.pdf   ← compiled SI PDF
│   └── supplementary_information_en.docx  ← Word SI
│
└── bilingual/                   ← Chinese-English bilingual version
    ├── manuscript_bilingual.txt        ← [SOURCE] bilingual manuscript
    ├── manuscript_bilingual.tex        ← LaTeX version
    ├── manuscript_bilingual.pdf        ← compiled PDF
    ├── manuscript_bilingual.docx       ← Word version
    ├── supplementary_information_bilingual.txt   ← [SOURCE] bilingual SI
    ├── supplementary_information_bilingual.tex   ← LaTeX SI (with figures)
    ├── supplementary_information_bilingual.pdf   ← compiled SI PDF
    └── supplementary_information_bilingual.docx  ← Word SI
```

## ⚠️ Editing rules — MUST READ before modifying

**The txt files are the single source of truth.** When you edit content:

1. **Edit the txt file first** (both `en/` and `bilingual/` versions).
2. **Then regenerate the derived formats:**
   - **docx**: `python convert_to_docx.py` (from `nc_draft/` directory)
   - **pdf**: `cd en && xelatex manuscript_en.tex` or `cd bilingual && xelatex manuscript_bilingual.tex`
   - **tex**: must be updated manually (not auto-generated from txt)

### Cross-version sync checklist

When you change **any content** (data, wording, structure), you must update
**all** of the following:

| What changed         | Files to update                                    |
|----------------------|----------------------------------------------------|
| Manuscript text      | `en/manuscript_en.txt`, `bilingual/manuscript_bilingual.txt`, both `.tex` |
| SI text              | `en/supplementary_information_en.txt`, `bilingual/supplementary_information_bilingual.txt`, both SI `.tex` |
| Table data           | Same as above (tables are inline in txt)           |
| Section structure    | All 4 txt files + both tex files                   |
| References           | All 4 txt files + both tex files                   |

After editing, rebuild all derived files:
```bash
cd nc_draft
python convert_to_docx.py                          # rebuild all docx
cd en && xelatex manuscript_en.tex && xelatex supplementary_information_en.tex && cd ..
cd bilingual && xelatex manuscript_bilingual.tex && xelatex supplementary_information_bilingual.tex
```

### Notes
- The `.tex` files are **independently maintained** (not generated from txt).
  They contain proper LaTeX macros (`\keff`, `\Eint`, etc.) and formatted tables.
  If you change content in txt, you must also update the corresponding tex.
- The bilingual tex is slightly condensed in the Discussion/Methods to keep
  page count reasonable; the bilingual txt has the full translation.
- SI has its own `.tex` files with all available figures embedded
  (10 figures from `0414_v4/figures/`: figS1--S5, figA1--A4, fig0_workflow).
