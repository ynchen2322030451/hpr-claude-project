# Literature Verification Log

Date: 2026-04-19 (Batches 1–4 complete + GPT-Gemini consensus)
Source: GPT verification (4 batches) + Gemini self-verification + GPT-Gemini consensus review
Status: **All verification complete. Consensus rules applied to REFERENCE_BANK.**

> This document records external review findings on the 110-ref literature
> bank. No entries have been deleted — only flagged with status and action.
> **Consensus rules from GPT+Gemini final review have been applied to
> LITERATURE_REFERENCE_BANK.md** — see its "Consensus Rules" section.

---

## Tier Classification

All 110 refs are classified into three tiers based on verification status:

| Tier | Meaning | Can enter manuscript? |
|------|---------|----------------------|
| **A** | Verified (DOI confirmed or high confidence) | Yes — main text or SI |
| **B** | Exists but current entry needs rebuild (wrong title/vol/pages) | Only after correction |
| **C** | Frozen — placeholder, unverified, or high hallucination risk | No — do not cite |

---

## GPT Batch 1: High-Load Main-Text References

### [20] Stauff et al. (2024) — BlueCrab HPR multiphysics
- **Tier: A (with corrections needed)**
- **GPT verdict**: Real. DOI: 10.1080/00295639.2024.2375175. Title confirmed:
  "High-Fidelity Multiphysics Modeling of a Heat Pipe Microreactor Using BlueCrab"
- **Issues**: Author list truncated in our entry. Pages "1–15" unconfirmed.
  Our own bank already flagged this as "volume/pages approximate."
- **Action**: Keep. Update entry from DOI metadata. Do not hand-write vol/pages.

### [21] Miao et al. (2025) — KRUSTY + MOOSE
- **Tier: A (with corrections needed)**
- **GPT verdict**: Real. DOI: 10.1080/00295639.2025.2560170. Title confirmed:
  "Multiphysics Simulation of KRUSTY Warm Critical Experiments Using MOOSE Tools"
- **Issues**: No vol/pages in our entry (very new publication). Our bank
  already flagged "high hallucination risk" — GPT confirms it's real.
- **Action**: Keep. Retrieve vol/pages from DOI. Use for "HF platform
  landscape" in Introduction, not as primary problem-definition support.

### [29] Kapteyn et al. (2021) — NCS digital twin
- **Tier: A**
- **GPT verdict**: Real and accurate. NCS 1(5):337–347.
- **Issues**: None with the entry itself.
- **Usage warning from GPT**: Do NOT use to claim "we are a digital twin."
  Our work is a probabilistic surrogate workflow, not a live-updating DT.
  Use only for NCS-scope positioning and "unified probabilistic layer" framing.
- **Action**: Keep. Restrict to Introduction final paragraph or Discussion.

---

## GPT Batch 2: Introduction-Critical References

### [19] McClure et al. (2015) — KRUSTY/HPR design
- **Tier: B (title wrong, must rebuild)**
- **GPT verdict**: Real paper exists, but our entry has WRONG TITLE.
  - Our entry says: "Design of Kilopower Reactor Using Solid-Core (KRUSTY)
    Experiments"
  - Actual title: "Design of megawatt power level heat pipe reactors"
  - DOI: 10.2172/1226133 (OSTI confirmed)
  - Authors also differ: actual = McClure, Poston, Dasari, Reid
- **Root cause**: Gemini conflated the 2015 megawatt HPR report with the
  later KRUSTY/Kilopower experiment series.
- **Action**: Keep ref but rebuild entry with correct title/authors/DOI.
  Use for "early HPR design background," NOT as KRUSTY experiment citation.

Corrected entry:
> McClure, P. R., Poston, D. I., Dasari, V. R., & Reid, R. S. (2015).
> Design of megawatt power level heat pipe reactors. Los Alamos National
> Laboratory. DOI: 10.2172/1226133.

### [22] Ma et al. (2021) — HPR thermo-mechanical analysis
- **Tier: B (unconfirmed, needs DOI)**
- **GPT verdict**: Could not find exact match for "Thermo-mechanical analysis
  of a heat pipe cooled microreactor core under nominal and faulted conditions,
  ANE 160, 108422" with authors Ma, Hu, Su.
- **GPT found instead**:
  - Jiao et al. (2023), *Progress in Nuclear Energy* — HPR thermal-mechanical
    coupling + heat pipe failure
  - Jeong et al. (2023), *Frontiers in Energy Research* — multiphysics
    analysis of HPR with thermal stress reduction
  - Peng et al. (2025) — HPR thermo-mechanical response
- **Action**: Do NOT use in main text until DOI confirmed. If needed for
  "monolithic HPR stress is a safety concern," consider substituting with
  one of the GPT-suggested alternatives above.
- **Gemini self-check**: Gemini later proposed filling [64] with this same
  entry (Ma 2021 ANE 160:108422), which contradicts GPT's inability to
  verify it. **Conflict unresolved — must independently verify via DOI.**

### [56] Gomez-Fernandez et al. (2020) — ML in nuclear engineering
- **Tier: B (title wrong, must correct)**
- **GPT verdict**: Real paper, but WRONG TITLE in our entry.
  - Our entry says: "Status and perspectives of machine learning in nuclear
    engineering"
  - Actual title: "Status of research and development of learning-based
    approaches in nuclear science and engineering: A review"
  - Journal: Nuclear Engineering and Design, 359, 110479
  - DOI: 10.1016/j.nucengdes.2019.110479
- **Action**: Keep. Correct title, volume (359 not 367), and article number
  (110479 not 110738).

Corrected entry:
> Gomez-Fernandez, M., et al. (2020). Status of research and development
> of learning-based approaches in nuclear science and engineering: A review.
> *Nuclear Engineering and Design*, 359, 110479.

### [57] Radaideh & Kozlowski (2020) — Neural surrogate for reactor UQ
- **Tier: B/C (title unconfirmed)**
- **GPT verdict**: Could not find exact match for "Neural-based surrogate
  modeling for uncertainty quantification in reactor physics, ANE 136, 107021."
  Found instead: "Analyzing nuclear reactor simulation data and uncertainty
  with the group method of data handling" (2020, Nuclear Engineering and
  Technology).
- **GPT assessment**: Likely a "plausible-sounding rewrite" of Radaideh's
  real research direction, but may not correspond to an actual paper.
- **Gemini self-check**: Gemini later re-proposed this exact entry to fill
  [104]. **This is contradictory — Gemini is filling a placeholder with
  an entry GPT could not verify.**
- **Action**: Do NOT use until independently verified via DOI search.
  If unverifiable, replace with a confirmed Radaideh publication.

### [89] Hu et al. (2019) — Heat pipe microreactor modeling
- **Tier: B (likely error-spliced entry)**
- **GPT verdict**: Current entry ("Modeling and simulations of heat pipe
  solid core microreactor, Nuclear Technology 205(1–2):190–205") is likely
  a splice of two different sources:
  1. Hu, G., Hu, R., et al. (2019). "Multi-Physics Simulations of Heat Pipe
     Micro Reactor." Argonne report. OSTI DOI: 10.2172/1569948.
  2. Hu et al. (2021). "Coupled Multiphysics Simulations of Heat Pipe–Cooled
     Nuclear Microreactors." Nuclear Technology (journal article).
- **Action**: Do NOT use current entry. Choose one:
  - If citing the 2019 Argonne report → use OSTI DOI
  - If citing a peer-reviewed journal article → use the 2021 Nuclear
    Technology paper instead

---

## GPT Batch 3: Methods & Appendix References (COMPLETED)

### [25] Williams (1986) — "Reactor physics" review
- **Tier: C → DELETE**
- **GPT verdict**: Could not find reliable first-hand match. Even if a broad
  reactor physics review exists under this title, it does NOT support
  "nuclear UQ history" — it's a generic reactor physics overview.
- **Our bank's own flag** ("confirm UQ content relevance") was correct.
- **Action**: **Delete from library.** Cacuci 2003 [53] already covers the
  nuclear SA/UQ authority role. No need for a broad 1986 review.

### [33] Pearce et al. (2018) — PICP/MPIW prediction intervals
- **Tier: A (minor correction needed)**
- **GPT verdict**: Real. PMLR/ICML 2018, pages 4075–4084. Full title:
  "High-Quality Prediction Intervals for Deep Learning: A Distribution-Free,
  Ensembled Approach."
- **Author verification**: Alexandra Brintrup is correct (our "verify
  Brintrup" flag can be closed). Author order in our entry is correct:
  Tim Pearce, Alexandra Brintrup, Mohamed Zaki, Andy Neely.
- **Action**: Keep. Entry is now verified. Close verification flag.

### [70] Gawlikowski et al. (2021/2023) — Deep learning UQ survey
- **Tier: A (must update to journal version)**
- **GPT verdict**: Real. Journal version published in *Artificial Intelligence
  Review* (2023), Springer. Title unchanged: "A survey of uncertainty in
  deep neural networks."
- **Action**: Keep. **Must update** from arXiv 2021 to AIR 2023 journal
  version. Add DOI, volume, pages from Springer.
- **Usage note**: Broad DL survey — suitable for Introduction background
  or SI, but should not carry nuclear-engineering-specific arguments.

### [75] OECD/NEA (2019) — Material properties handbook
- **Tier: C → DELETE**
- **GPT verdict**: The title in our entry ("Handbook on Lead-bismuth Eutectic
  Alloy and Lead Properties") is about **lead/LBE materials**, NOT SS316
  stainless steel. This is a **fundamental mismatch** with our intended use
  (SS316 high-temperature elastic modulus and thermal expansion).
- **Action**: **Delete from library.** For SS316 properties, [42] ASME BPVC
  Section II Part D is the correct and already-included reference.

### [76] Popov et al. (2000) — UO2/MOX thermophysical properties
- **Tier: A (minor title correction)**
- **GPT verdict**: Real. Report number ORNL/TM-2000/351 confirmed.
- **Issue**: Our entry truncated the title. Full title is:
  "Thermophysical Properties of MOX and UO2 Fuels Including the Effects
  of Irradiation"
- **Action**: Keep. Update to full title. Note: supports fuel properties
  only, NOT SS316 thermo-mechanical uncertainty. Place in SI Note E.

### [90] Owen (2013) — Variance components / generalized Sobol indices
- **Tier: A (journal corrected)**
- **GPT verdict**: Real. The correct journal is **SIAM/ASA Journal on
  Uncertainty Quantification**, 1(1), 19–41. NOT JASA.
- **Action**: Keep. Update journal name. Our bank's "JASA vs SIAM/ASA JUQ"
  flag is now resolved in favor of SIAM/ASA JUQ.

### [98] Dugas et al. (2000) — Functional knowledge in neural networks
- **Tier: A (year/venue corrected)**
- **GPT verdict**: Real. Published at **NeurIPS 2000** (NIPS 13), NOT
  "2009 JMLR" as Gemini originally wrote.
- **Full title**: "Incorporating Second-Order Functional Knowledge for
  Better Option Pricing"
- **Action**: Keep. Our bank's BibTeX already has the correct year (2000)
  and venue (NeurIPS). Close verification flag.
- **Usage note**: Indirectly relevant to monotonicity soft penalty. Better
  suited for SI than main text.

---

### Batch 3 Summary: Entries to Delete

| Ref | Reason |
|-----|--------|
| [25] Williams 1986 | No UQ content; broad reactor physics review |
| [75] OECD/NEA 2019 | Wrong material system (lead/LBE ≠ SS316) |

### Batch 3 Summary: Entries Corrected and Cleared

| Ref | Correction | New Tier |
|-----|-----------|----------|
| [33] Pearce 2018 | Author "Brintrup" confirmed correct | A |
| [70] Gawlikowski | Update to AIR 2023 journal version | A |
| [76] Popov 2000 | Add full title (+ "Including Effects of Irradiation") | A |
| [90] Owen 2013 | Journal = SIAM/ASA JUQ, not JASA | A |
| [98] Dugas 2000 | Year = 2000, venue = NeurIPS (not 2009 JMLR) | A |

---

## GPT Batch 4: Nuclear-Specific References (COMPLETED)

### [57] Radaideh & Kozlowski (2020) — Neural surrogate for reactor UQ
- **Tier: B → DELETE current entry, REPLACE**
- **GPT verdict (Batch 4 update)**: The entry in our bank ("Neural-based
  surrogate modeling for uncertainty quantification in reactor physics,
  ANE 136, 107021") remains **unverifiable**. GPT performed targeted search
  and confirmed this specific paper does not exist.
- **Verified replacement**: Radaideh, M. I., & Kozlowski, T. (2020).
  "Analyzing nuclear reactor simulation data and uncertainty with the group
  method of data handling." *Nuclear Engineering and Technology*, 52(3),
  601–611. DOI: 10.1016/j.net.2019.08.015.
- **Alternative**: Radaideh, M. I., et al. (2021). "Neural-based time series
  forecasting of loss of coolant accidents in nuclear power plants."
  *Expert Systems with Applications*, 160, 113699.
- **Action**: **Delete current [57].** If a "neural surrogate for reactor UQ"
  citation is needed, use the verified 2020 NET paper or the 2021 ESWA paper.
  Update LITERATURE_REFERENCE_BANK.md accordingly.

### [89] Hu et al. (2019) — Heat pipe microreactor modeling
- **Tier: B → REBUILD**
- **GPT verdict (Batch 4 update)**: Confirmed the current entry is a splice.
  GPT now provides two clean options:
  1. **Argonne report (2019)**: Hu, G., Hu, R., Kelly, J. M., & Ortensi, J.
     "Multi-Physics Simulations of Heat Pipe Micro Reactor." ANL/NSE-19/25.
     OSTI DOI: 10.2172/1569948.
  2. **Journal article (2021)**: Hu, G., Hu, R., Kelly, J. M., & Ortensi, J.
     "Coupled Multiphysics Simulations of Heat Pipe–Cooled Nuclear
     Microreactors." *Nuclear Technology*, 207(7), 1020–1040.
     DOI: 10.1080/00295450.2021.1882588.
- **GPT recommendation**: Use the **2021 journal article** for main text
  (peer-reviewed, specific DOI). Use Argonne report only if citing
  institutional lineage.
- **Action**: Rebuild [89] with the 2021 Nuclear Technology entry.

### [41] Fink (2000) — UO2 thermophysical properties
- **Tier: A (scope-limited)**
- **GPT verdict**: Real. *Journal of Nuclear Materials*, 279(1), 1–18.
  DOI: 10.1016/S0022-3115(99)00273-1. Full title: "Thermophysical properties
  of uranium dioxide."
- **Scope warning from GPT**: This covers **UO2 fuel properties ONLY**, NOT
  SS316 structural steel. Our manuscript's thermo-mechanical uncertainty
  involves both fuel and monolith (SS316). [41] supports fuel-side material
  property inputs but cannot anchor SS316 thermal expansion or elastic
  modulus claims.
- **Action**: Keep. Use in SI Note E (material property input distributions)
  for fuel parameters. Pair with [42] ASME BPVC for SS316 properties.
  Do NOT use alone to justify "material property uncertainty" in main text.

### [42] ASME BPVC Section II Part D (2021) — Material properties
- **Tier: A (strongest nuclear-specific ref in bank)**
- **GPT verdict**: Real and authoritative. ASME Boiler and Pressure Vessel
  Code, Section II — Materials, Part D — Properties (Customary), 2021 Edition.
- **GPT assessment**: "This is the single most defensible reference in your
  nuclear-specific group. ASME BPVC is the de facto standard for nuclear
  structural material properties. Any reviewer who questions SS316 property
  inputs will accept this."
- **Action**: Keep. **Strongest anchor** for SS316 material property inputs
  (elastic modulus, thermal expansion, yield strength). Place in Methods
  and/or SI Note E. Can also support the prior-specification argument
  ("input distributions derived from code-qualified property tables").

### [43] Hagrman et al. (1981) — MATPRO fuel material library
- **Tier: A (NUREG number corrected)**
- **GPT verdict**: Real. But our entry has the **WRONG NUREG number**.
  - Our entry says: NUREG/CR-0446
  - Correct number: **NUREG/CR-0497, Rev. 2** (also known as EGG-2179)
  - Full title: "MATPRO — Version 11 (Revision 2): A Handbook of Materials
    Properties for Use in the Analysis of Light Water Reactor Fuel Rod
    Behavior"
  - Authors: Hagrman, D. L., Reymann, G. A., & Mason, R. E. (1981)
  - Institution: EG&G Idaho, Inc., for U.S. NRC
- **Action**: Keep. **Correct NUREG number** from CR-0446 to CR-0497 Rev. 2.
  Add EGG-2179 as alternate report number. Use in SI Note E alongside [41]
  and [76] for fuel property input justification.

Corrected entry:
> Hagrman, D. L., Reymann, G. A., & Mason, R. E. (1981). MATPRO — Version 11
> (Revision 2): A Handbook of Materials Properties for Use in the Analysis of
> Light Water Reactor Fuel Rod Behavior. NUREG/CR-0497, Rev. 2 (EGG-2179).
> U.S. Nuclear Regulatory Commission.

### [52] ENDF/B-VIII.0 — Brown et al. (2018) — Nuclear data library
- **Tier: A → REMOVE from main text (keep in SI only if needed)**
- **GPT verdict**: Real and authoritative. Brown, D. A., et al. (2018).
  "ENDF/B-VIII.0: The 8th Major Release of the Nuclear Reaction Data Library
  with CIELO-project Cross Sections, New Standards and Thermal Scattering
  Data." *Nuclear Data Sheets*, 148, 1–142. DOI: 10.1016/j.nds.2018.02.001.
- **GPT assessment**: "This is a real and important reference in nuclear
  engineering, but it does NOT belong in your manuscript unless you explicitly
  propagate nuclear cross-section data uncertainty. Your paper's UQ focuses
  on geometric/material/thermal inputs → coupled response. ENDF/B-VIII.0
  is upstream of your simulation chain but not part of your uncertainty
  characterization."
- **Action**: **Remove from main text.** If the paper mentions OpenMC as the
  neutronics solver (which uses ENDF/B data), a single sentence in Methods
  or SI ("neutronics calculations used ENDF/B-VIII.0 cross-section
  libraries [52]") is acceptable. Do NOT place in the UQ input distribution
  discussion.

---

### Batch 4 Summary

#### Entries to Delete
| Ref | Reason |
|-----|--------|
| [57] Radaideh 2020 (current entry) | Unverifiable — replace with verified NET 2020 paper |

#### Entries Corrected and Cleared
| Ref | Correction | New Tier |
|-----|-----------|----------|
| [89] Hu 2019 | Rebuild with 2021 Nuclear Technology journal article | A (after rebuild) |
| [41] Fink 2000 | Confirmed real; scope-limited to UO2 fuel only | A |
| [42] ASME BPVC 2021 | Confirmed real and authoritative; strongest ref | A |
| [43] Hagrman 1981 | NUREG number corrected: CR-0446 → CR-0497 Rev. 2 | A |
| [52] ENDF/B-VIII.0 | Real but should be removed from main text | A (SI only) |

#### GPT's Executable Summary After All 4 Batches

**DELETE** (do not include in final .bib):
- [25] Williams 1986 — no UQ content
- [57] current entry — unverifiable
- [75] OECD/NEA 2019 — wrong material (lead/LBE)
- [52] from main text — not part of UQ scope (SI only)

**REBUILD** (entry exists but must be rewritten with correct metadata):
- [19] McClure 2015 — correct title/DOI from OSTI
- [22] Ma 2021 — needs independent DOI confirmation or replacement
- [43] Hagrman 1981 — NUREG CR-0446 → CR-0497 Rev. 2
- [56] Gomez-Fernandez 2020 — correct title, vol 359, article 110479
- [57] replacement — use Radaideh 2020 NET paper
- [89] Hu — use 2021 Nuclear Technology journal version

**KEEP** (verified, can enter manuscript):
- [20] Stauff 2024, [21] Miao 2025, [29] Kapteyn 2021
- [33] Pearce 2018, [41] Fink 2000, [42] ASME BPVC 2021
- [70] Gawlikowski 2023, [76] Popov 2000, [90] Owen 2013, [98] Dugas 2000

---

## Gemini Self-Verification Results

Gemini performed its own final check and proposed the following fixes:

### Duplicates to Resolve

| Issue | Gemini recommendation | Status |
|-------|----------------------|--------|
| [80] = reprint of [54] (McKay LHS) | Delete [80], keep [54] | **Agreed** — do not cite both |
| [108] = duplicate of [18] (Abdar 2021) | Replace with Abadi 2016 (TensorFlow) | **Agreed** — but verify if TF is actually used in project (we use PyTorch) |
| [100] overlaps with [6] (Gal MC-Dropout) | Replace with Srivastava 2014 (original Dropout) | **Reasonable** — but [100] Concrete Dropout is technically distinct |

### Placeholder Fills Proposed by Gemini

| Slot | Gemini proposal | GPT-verified? | Status |
|------|----------------|---------------|--------|
| [23]/[65] | Own team's prior work | N/A (self-citation) | User must fill |
| [30] | Lu et al. 2021 DeepONet, *Nature Machine Intelligence* | Not verified | **Tier C until DOI checked** |
| [58] | Gramacy 2020 *Surrogates* book, CRC Press | Not verified | **Tier C until DOI checked** |
| [62] | Runge et al. 2019, *Nature Communications* 10:2553 | Not verified | **Tier C until DOI checked** |
| [63] | Pearce et al. 2020, AISTATS | Not verified | **Tier C until DOI checked** |
| [64] | Ma et al. 2021, ANE 160:108422 | **GPT COULD NOT VERIFY [22]** | **CONFLICT — same entry GPT flagged as unconfirmed** |
| [67] | Sargsyan et al. 2014, JCP 273:251-269 | Not verified | **Tier C until DOI checked** |
| [93] | Nix & Weigend 1994 (already [92]) | **DUPLICATE of [92]** | **Do not use — already in bank** |
| [103] | Meng & Karniadakis 2020, JCP 401:109020 | **Already [40]** | **DUPLICATE — do not double-cite** |
| [104] | Radaideh 2020, ANE 136:107021 | **GPT COULD NOT VERIFY [57]** | **CONFLICT — same unverified entry** |
| [107] | Zhang et al. 2020 ICLR (Cyclical SGMCMC) | Not verified | **Tier C until DOI checked** |

### Critical Conflicts Identified

1. **[64] and [22] are the same entry** (Ma 2021 ANE). GPT could not verify
   it exists. Gemini re-proposed it as a placeholder fill. **Do not use
   until DOI independently confirmed.**

2. **[93] and [92] are the same entry** (Nix & Weigend 1994). Gemini
   proposed filling [93] with a ref already in the bank as [92].
   **Delete [93] placeholder — already covered.**

3. **[103] and [40] are the same entry** (Meng & Karniadakis 2020 JCP).
   Gemini proposed filling [103] with a ref already present as [40].
   **Delete [103] placeholder — already covered.**

4. **[104] and [57] are the same entry** (Radaideh 2020 ANE). GPT could
   not verify [57]. Gemini re-proposed the same unverified entry for [104].
   **Do not use either until DOI confirmed.**

---

## Systematic Issue: "Half-True Rewrites"

GPT's most important meta-finding:

> "Your literature bank's biggest problem is not outright fabrication but
> **semi-accurate bibliographic rewrites**. The research direction is real,
> the author group is often real, but the title, year, journal, volume,
> and article number have been recombined. This is MORE dangerous than pure
> hallucination because it passes casual inspection."

**Affected entries identified so far**:
- [19] McClure — wrong title (megawatt HPR ≠ KRUSTY)
- [22] Ma — unverified combination
- [56] Gomez-Fernandez — wrong title, wrong volume, wrong article number
- [57] Radaideh — plausible-sounding but unconfirmed
- [89] Hu — spliced from report + journal article

**Recommendation**: Before any ref enters the final .bib file, confirm it
via DOI resolution. Do NOT trust title + author + year alone.

---

## Current Tier Summary (after Batch 4 — all GPT batches complete)

| Tier | Count | Description |
|------|-------|-------------|
| A (verified, can use) | ~78 | Classic refs + GPT-confirmed across 4 batches |
| B (exists but entry wrong, must rebuild) | ~7 | [19], [22], [43], [56], [57]→replace, [89]→rebuild |
| C (frozen/deleted) | ~25 | 12 placeholders + 7 deleted + unverified Gemini fills |

### Entries Marked for Deletion (do NOT include in final .bib)

- [25] Williams 1986 — no UQ content relevance
- [57] current entry — unverifiable (replace with verified Radaideh 2020 NET)
- [75] OECD/NEA 2019 — wrong material system (lead/LBE ≠ SS316)
- [80] McKay 2000 — duplicate of [54]
- [93] — duplicate of [92] (Nix & Weigend)
- [103] — duplicate of [40] (Meng & Karniadakis)
- [108] — duplicate of [18] (Abdar)

### Main Text vs SI Placement Decisions from Batch 4

| Ref | Placement | Reason |
|-----|-----------|--------|
| [42] ASME BPVC | **Main text** (Methods) | Strongest nuclear-specific ref; anchors SS316 inputs |
| [41] Fink 2000 | **SI Note E** | UO2 fuel only, not SS316 |
| [43] MATPRO | **SI Note E** | Fuel property handbook |
| [52] ENDF/B-VIII.0 | **SI only** or one-sentence Methods mention | Not part of UQ scope |
| [76] Popov 2000 | **SI Note E** | Fuel properties (from Batch 3) |

### Remaining Verification Work

1. ~~Complete GPT Batch 3~~ — **DONE**
2. ~~Complete GPT Batch 4~~ — **DONE**
3. DOI-check all Gemini placeholder fills ([30], [58], [62], [63], [67], [107])
4. Resolve the Ma 2021 [22]/[64] conflict
5. Resolve the Radaideh 2020 [57]/[104] conflict (partially resolved: [57] current deleted, replacement identified)
6. Fill [23]/[65] with own team's publication
7. Rebuild entries: [19], [43], [56], [89] with corrected metadata
8. Final .bib export only from Tier A entries
9. GPT proposed next step: create **主文最小可信参考文献集** (minimum credible main-text reference set, 20–30 refs)

### GPT Meta-Observations

**After Batch 3:**
> "Your library has many ML methodology surveys and supplementary citations,
> but the directly nuclear-engineering-HPR-specific references are the
> weakest group. This creates a risk: the manuscript reads like an
> 'ML methods paper with nuclear application' rather than a 'computational
> science paper addressing HPR multiphysics uncertainty.' This misalignment
> matters for NCS positioning."

**After Batch 4:**
> "Of the six nuclear-specific refs checked, only [42] ASME BPVC is fully
> stable for main text without any caveats. [41] and [43] are real but
> scope-limited to fuel properties. [52] is authoritative but irrelevant to
> your UQ scope. This confirms the pattern: your nuclear domain citations
> need the most remediation work."

---

## Appendix: GPT's Recommended Alternative References

For entries GPT flagged as unreliable, these verified alternatives were
suggested:

**For [22] Ma 2021 (HPR thermo-mechanical)** — if needed for "monolithic
HPR core stress is a persistent safety concern":
- Jiao et al. (2023). Thermal-mechanical coupling characteristics and heat
  pipe failure analysis of heat pipe cooled space reactor. *Progress in
  Nuclear Energy*.
- Jeong et al. (2023). Multiphysics analysis of heat pipe cooled
  microreactor core with adjusted heat sink temperature for thermal stress
  reduction. *Frontiers in Energy Research*.

**For [89] Hu 2019 (heat pipe microreactor modeling)**:
- Hu, G., Hu, R., Kelly, J. M., & Ortensi, J. (2019). Multi-Physics
  Simulations of Heat Pipe Micro Reactor. Argonne report. OSTI DOI:
  10.2172/1569948.
- OR: Hu et al. (2021). Coupled Multiphysics Simulations of Heat Pipe–Cooled
  Nuclear Microreactors. *Nuclear Technology* (journal article).

**For [57] Radaideh 2020**:
- Radaideh, M. I., & Kozlowski, T. (2020). Analyzing nuclear reactor
  simulation data and uncertainty with the group method of data handling.
  *Nuclear Engineering and Technology*, 52(3), 601–611.
  DOI: 10.1016/j.net.2019.08.015.
- OR: Radaideh, M. I., et al. (2021). Neural-based time series forecasting
  of loss of coolant accidents in nuclear power plants. *Expert Systems with
  Applications*, 160, 113699.

**For [43] Hagrman 1981 MATPRO** (correction only):
- Hagrman, D. L., Reymann, G. A., & Mason, R. E. (1981). MATPRO — Version 11
  (Revision 2). NUREG/CR-0497, Rev. 2 (EGG-2179). U.S. NRC.
  [corrected from CR-0446]

---

## GPT+Gemini Consensus Review (Final)

Date: 2026-04-19

GPT and Gemini reached consensus on a 4-bucket classification and hard rules
for the manuscript. This section records the final agreed positions.

### 全局叙事基准（绝对不可偏离）

1. 本文输入不确定性仅来自 **8 个 SS316 经验公式参数**（弹性模量、泊松比、热膨胀系数、热导率的斜率/截距/参考值）。
2. 所有 8 个参数统一赋予 **±10% prior**；该尺度与团队前期相关研究中的参数扰动设定保持一致。
3. **绝对禁止**把 nuclear data / ENDF / X1–X5 写成本文输入不确定性的核心主线。

### 高危参考文献硬规则

| Ref | Status | Rule |
|-----|--------|------|
| [19] McClure 2015 | REBUILT | 标题锁定 "Design of megawatt power level heat pipe reactors" |
| [22] Ma 2021 | FROZEN | 在人工确认 DOI 前不进入主文 |
| [42] ASME BPVC | ANCHOR | "Section II Part D（按最终核定版本）"，不锁死 2019 |
| [52] ENDF/B-VIII.0 | SI-ONLY | 仅一句话 OpenMC 背景，不进 input uncertainty 主线 |
| [57] Radaideh 2020 | REPLACED | 废弃当前条目，改用 NET 2020 已核实替代 |
| [89] Hu 2019 | REBUILT | 废弃拼接条目，重建为 2021 Nuclear Technology |

### GPT 最终结论

> "你的文献库核心问题不是'假文献太多'，而是：**真方向 + 假精确题录 +
> 过量方法学补充 + HPR 直接文献不够稳**。现在最该做的是收缩，不是继续扩。"

### 主文最小可信参考文献集骨架（25–35 条）

**Introduction**: [1], [19]✓, [20], [21], [29], [46], [47], [56]✓
**Methods**: [4], [5], [10], [11], [12], [13], [34], [35], [42]✅, [48], [50], [54]
**Results–Discussion**: [3], [31], [32], [33], [37], [38], [39], [40], [61], [85]
**Software**: [109], [110]

✓ = rebuilt entry   ✅ = strongest anchor

### 与 Zhang et al. (2025, Energy) 一致性说明

> 所有 8 个参数统一赋予 ±10% prior；该尺度与团队前期相关研究中的参数扰动
> 设定保持一致。不要硬写成"完全与 Zhang et al. (2025, Energy) 一致"，除非
> 后面逐项核对过那篇文里的同一组参数和同一扰动定义。

### Consensus Applied To

- `LITERATURE_REFERENCE_BANK.md` — entries [19], [22], [42], [43], [52], [57], [89] updated
- Quick Placement Map updated with warnings
- Suggested Main Text vs SI Split table rewritten
- Verification notes updated (resolved items checked off)
