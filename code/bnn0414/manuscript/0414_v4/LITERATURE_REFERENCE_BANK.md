# Literature Reference Bank for NCS Submission

Date: 2026-04-19 (all phases merged, GPT+Gemini consensus applied)
Source: Gemini literature survey (Phases 1–7, 110 refs) + GPT 4-batch verification + Gemini cross-review
Status: **4-bucket screening complete. See "Consensus Rules" section below.**

> **Important**: These references were selected by Gemini and claimed to be
> cross-verified. Before inserting into the manuscript, independently verify
> each entry (DOI, volume, pages, year) against the actual publication.

---

## GPT+Gemini Consensus Rules (2026-04-19)

### 全局叙事基准：绝对不可偏离

1. 本文输入不确定性仅来自 8 个 SS316 经验公式参数（弹性模量、泊松比、热膨胀系数、热导率的斜率/截距/参考值）。
2. 所有 8 个参数统一赋予 ±10% prior。
3. 绝对禁止把 nuclear data / ENDF / X1–X5 写成本文输入不确定性的核心主线。

### 高危参考文献硬规则

| Ref | Rule |
|-----|------|
| [19] McClure 2015 | 标题锁定为 "Design of megawatt power level heat pipe reactors"。DOI: 10.2172/1226133 |
| [22] Ma 2021 | **在人工确认 DOI 和出版元数据前，不进入主文。** |
| [42] ASME BPVC | 使用 "ASME BPVC Section II Part D（按最终核定版本）"，不锁死年份为 2019 |
| [52] ENDF/B-VIII.0 | 仅允许作为 OpenMC 使用核数据库的一句话背景引用；不得进入 input uncertainty 主线 |
| [57] Radaideh 2020 | 废弃当前条目；若确有需要，改用 verification log 中已核实的替代条目 |
| [89] Hu 2019 | 废弃当前条目，若需引用，重建为 Hu et al. (2021), *Nuclear Technology*, 207(7), 1020–1040 |

### 主文核心锚点（25–35 条骨架）

**Introduction:**
- [19] McClure 2015 (rebuilt), [20] Stauff 2024, [21] Miao 2025, [29] Kapteyn 2021
- [46] Gaston 2009, [47] Knoll 2004, [56] Gomez-Fernandez 2020 (title corrected)

**Methods:**
- [4] Blundell 2015, [5] Kendall & Gal 2017, [10] Kennedy & O'Hagan 2001
- [11] Saltelli 2010, [12] Romano 2015, [13] Logg 2012
- [34] Vehtari 2021, [35] Blei 2017, [42] ASME BPVC Section II Part D
- [48] MacKay 1992, [50] Kingma & Welling 2014, [54] McKay 1979

**Results–Discussion:**
- [1] Karniadakis 2021, [3] Willard 2022, [31] Gneiting 2007, [32] Guo 2017
- [33] Pearce 2018, [37] Der Kiureghian 2009, [38] Hüllermeier 2021
- [39] Peherstorfer 2018, [40] Meng & Karniadakis 2020, [61] Karpatne 2017
- [85] Perdikaris 2017 (MF negative-result defense)

**Software:**
- [109] Paszke 2019, [110] Akiba 2019

### 4-Bucket Summary

| Bucket | Count | Description |
|--------|-------|-------------|
| A: 主文优先保留 | ~30 | 直接支撑主线 + 真实性低风险 |
| B: SI/附录可用 | ~40 | 真实但与主线不够贴 |
| C: 题录不稳需重建 | ~12 | 方向对但元数据有误 |
| D: 冻结不进稿件 | ~28 | Placeholder + 重复 + 弱关联 |

---

## Quick Placement Map

```
Introduction (§1):
  ├─ Para 1-2 (HF simulation bottleneck → surrogate motivation)
  │    [1] Karniadakis 2021, [2] Raissi 2019, [18] Abdar 2021
  │    [19] McClure 2015 (HPR design — REBUILT), [22] Ma 2021 ⚠️ FROZEN until DOI confirmed
  │    [20] Stauff 2024 (BlueCrab), [21] Miao 2025 (MOOSE-KRUSTY)
  ├─ Para 1 (HF coupling bottleneck)
  │    [46] Gaston 2009 (MOOSE), [47] Knoll 2004 (JFNK complexity)
  ├─ Para 2-3 (BNN for physics systems, UQ gap)
  │    [5] Zhu 2018, [9] Psaros 2023, [16] Pestourie 2020
  │    [24] Sudret 2008 (PCE limitation), [27] Wu 2018 (GP in nuclear)
  │    [26] Smith 2013 (UQ textbook), [53] Cacuci 2003 (nuclear SA)
  │    [56] Gomez-Fernandez 2020 (ML in nuclear — title corrected)
  │    [57] ⚠️ FROZEN — current entry unverifiable, use replacement from verification log
  ├─ Para 3-4 (physics priors, baselines, TGDS)
  │    [3] Willard 2022, [6] Gal 2016, [7] Lakshminarayanan 2017
  │    [61] Karpatne 2017 (TGDS paradigm)
  └─ Para 4-5 (digital twin / acceleration framing)
       [28] Glaessgen 2012 (DT definition), [29] Kapteyn 2021 (NCS DT)

Methods (§4):
  ├─ §4.1 Dataset generation
  │    [12] Romano 2015 (OpenMC), [13] Logg 2012 (FEniCS)
  │    [41] Fink 2000 (UO2), [42] ASME BPVC (SS316), [43] MATPRO (fuel)
  ├─ §4.1 Input uncertainty sources (8 SS316 empirical parameters only)
  │    [54] McKay 1979 (LHS)
  │    [52] Brown 2018 ⚠️ SI-ONLY — one-sentence solver background, NOT input UQ
  ├─ §4.3 BNN inference
  │    [4] Blundell 2015 (Bayes-by-Backprop)
  │    [35] Blei 2017 (VI/ELBO review), [36] Kingma 2014 (Adam)
  │    [48] MacKay 1992 (BNN founder), [49] Neal 1996 (BNN bible)
  │    [50] Kingma 2014 (reparam trick), [51] Graves 2011 (practical VI)
  ├─ §4.3 Uncertainty decomposition
  │    [5] Kendall 2017
  │    [37] Der Kiureghian 2009 (eng. epi/alea), [38] Hüllermeier 2021
  ├─ §4.4 Physics constraints / monotonicity
  │    [44] Sill 1998 (monotonic nets), [45] Gupta 2016 (calibrated mono)
  ├─ §4.5 Evaluation metrics
  │    [31] Gneiting 2007 (CRPS), [32] Guo 2017 (ECE), [33] Pearce 2018 (PICP/MPIW)
  ├─ §4.4 Physics constraints (see also above)
  │    [3] Willard 2022
  ├─ §4.5 Sobol
  │    [11] Saltelli 2010
  └─ §4.6 MCMC calibration
       [10] Kennedy & O'Hagan 2001
       [34] Vehtari 2021 (rank-normalized Rhat — matches code's 1.01 threshold)
       [55] Hoffman 2014 (NUTS/HMC — future high-dim alternative)

Results (§2):
  ├─ §2.1 External baseline comparison
  │    [6] Gal 2016 (MC-Dropout), [7] Lakshminarayanan 2017 (DE)
  ├─ §2.1 Uncertainty decomposition
  │    [5] Kendall 2017
  └─ §2.1 Metric definitions
       [31] Gneiting 2007 (CRPS), [32] Guo 2017 (ECE)

Discussion (§3):
  ├─ §3.1 Why BNN not PINN
  │    [15] Wang 2021 (gradient pathologies)
  ├─ §3.2 OOD generalization
  │    [14] Ovadia 2019
  ├─ §3.3 Measurement design
  │    (no specific ref needed — argument is self-contained)
  ├─ §3.x Multi-fidelity discussion
  │    [39] Peherstorfer 2018 (MF-UQ survey), [40] Meng 2020 (MF-NN composite)
  ├─ §3.x Sobol vs XAI / interpretability
  │    [59] Lundberg 2017 (SHAP), [60] Iooss 2015 (global SA review)
  └─ §3.4 Future work
       [17] Cranmer 2020 (symbolic regression)
       [55] Hoffman 2014 (NUTS for high-dim scaling)
```

---

## Category 1: Scientific Machine Learning & Physics-Informed ML

### [1] Karniadakis et al. (2021) — SciML gold-standard review

Karniadakis, G. E., Kevrekidis, I. G., Lu, L., Perdikaris, P., Wang, S.,
& Yang, L. (2021). Physics-informed machine learning. *Nature Reviews
Physics*, 3(6), 422–440.

**Placement**: Introduction §1 (motivate physics-aware surrogate landscape)

```bibtex
@article{karniadakis2021physics,
  title   = {Physics-informed machine learning},
  author  = {Karniadakis, George Em and Kevrekidis, Ioannis G and Lu, Lu
             and Perdikaris, Paris and Wang, Sifan and Yang, Liu},
  journal = {Nature Reviews Physics},
  volume  = {3},
  number  = {6},
  pages   = {422--440},
  year    = {2021}
}
```

### [2] Raissi et al. (2019) — PINN foundational paper

Raissi, M., Perdikaris, P., & Karniadakis, G. E. (2019). Physics-informed
neural networks: A deep learning framework for solving forward and inverse
problems involving nonlinear partial differential equations. *Journal of
Computational Physics*, 378, 686–707.

**Placement**: Introduction (cite to distinguish our approach); Discussion
(contrast: we are physics-*constrained* surrogate, not PDE-solving PINN)

```bibtex
@article{raissi2019physics,
  title   = {Physics-informed neural networks: A deep learning framework for
             solving forward and inverse problems involving nonlinear partial
             differential equations},
  author  = {Raissi, Maziar and Perdikaris, Paris and Karniadakis, George E},
  journal = {Journal of Computational Physics},
  volume  = {378},
  pages   = {686--707},
  year    = {2019}
}
```

### [3] Willard et al. (2022) — Physics–ML integration survey (monotonicity priors)

Willard, J., Jia, X., Xu, S., Steinbach, M., & Kumar, V. (2022).
Integrating physics-based modeling with machine learning: A survey. *ACM
Computing Surveys*, 55(4), 1–34.

**Placement**: Methods §4.4 (justify monotonicity constraint as physics prior)

```bibtex
@article{willard2022integrating,
  title   = {Integrating physics-based modeling with machine learning: A survey},
  author  = {Willard, Jared and Jia, Xiaowei and Xu, Shaoming and Steinbach,
             Michael and Kumar, Vipin},
  journal = {ACM Computing Surveys},
  volume  = {55},
  number  = {4},
  pages   = {1--34},
  year    = {2022}
}
```

---

## Category 2: Bayesian Neural Networks & Uncertainty Quantification

### [4] Blundell et al. (2015) — Bayes-by-Backprop (core algorithm for bnn_model.py)

Blundell, C., Cornebise, J., Kavukcuoglu, K., & Wierstra, D. (2015).
Weight uncertainty in neural networks. In *Proceedings of the 32nd
International Conference on Machine Learning* (pp. 1613–1622). PMLR.

**Placement**: Methods §4.3 (BNN variational inference / ELBO)

```bibtex
@inproceedings{blundell2015weight,
  title        = {Weight uncertainty in neural networks},
  author       = {Blundell, Charles and Cornebise, Julien and Kavukcuoglu, Koray
                  and Wierstra, Daan},
  booktitle    = {International Conference on Machine Learning},
  pages        = {1613--1622},
  year         = {2015},
  organization = {PMLR}
}
```

### [5] Kendall & Gal (2017) — Epistemic vs aleatoric uncertainty decomposition

Kendall, A., & Gal, Y. (2017). What uncertainties do we need in Bayesian
deep learning for computer vision? *Advances in Neural Information
Processing Systems*, 30.

**Placement**: Methods / Results (uncertainty decomposition panels)

```bibtex
@article{kendall2017what,
  title   = {What uncertainties do we need in {B}ayesian deep learning for
             computer vision?},
  author  = {Kendall, Alex and Gal, Yarin},
  journal = {Advances in Neural Information Processing Systems},
  volume  = {30},
  year    = {2017}
}
```

### [6] Gal & Ghahramani (2016) — MC-Dropout (external baseline)

Gal, Y., & Ghahramani, Z. (2016). Dropout as a Bayesian approximation:
Representing model uncertainty in deep learning. In *Proceedings of the 33rd
International Conference on Machine Learning* (pp. 1050–1059). PMLR.

**Placement**: Results §2.1 + Appendix (external baseline comparison)

```bibtex
@inproceedings{gal2016dropout,
  title        = {Dropout as a {B}ayesian approximation: Representing model
                  uncertainty in deep learning},
  author       = {Gal, Yarin and Ghahramani, Zoubin},
  booktitle    = {International Conference on Machine Learning},
  pages        = {1050--1059},
  year         = {2016},
  organization = {PMLR}
}
```

### [7] Lakshminarayanan et al. (2017) — Deep Ensembles (external baseline)

Lakshminarayanan, B., Pritzel, A., & Blundell, C. (2017). Simple and
scalable predictive uncertainty estimation using deep ensembles. *Advances
in Neural Information Processing Systems*, 30.

**Placement**: Results §2.1 + Appendix (external baseline comparison)

```bibtex
@article{lakshminarayanan2017simple,
  title   = {Simple and scalable predictive uncertainty estimation using deep
             ensembles},
  author  = {Lakshminarayanan, Balaji and Pritzel, Alexander and Blundell,
             Charles},
  journal = {Advances in Neural Information Processing Systems},
  volume  = {30},
  year    = {2017}
}
```

### [8] Zhu & Zabaras (2018) — BNN for PDE uncertainty quantification

Zhu, Y., & Zabaras, N. (2018). Bayesian deep learning for uncertainty
quantification in computational PDEs. *Journal of Computational Physics*,
350, 408–432.

**Placement**: Introduction (BNN applied to physical systems)

```bibtex
@article{zhu2018bayesian,
  title   = {Bayesian deep learning for uncertainty quantification in
             computational {PDE}s},
  author  = {Zhu, Yinhao and Zabaras, Nicholas},
  journal = {Journal of Computational Physics},
  volume  = {350},
  pages   = {408--432},
  year    = {2018}
}
```

### [9] Psaros et al. (2023) — UQ methods/metrics comparison in SciML

Psaros, A. F., Meng, X., Zou, Z., Guo, L., & Karniadakis, G. E. (2023).
Uncertainty quantification in scientific machine learning: Methods, metrics,
and physics-informed ELBO. *Journal of Computational Physics*, 477, 111902.

**Placement**: Introduction (UQ gap in engineering surrogates)

```bibtex
@article{psaros2023uncertainty,
  title   = {Uncertainty quantification in scientific machine learning:
             Methods, metrics, and physics-informed {ELBO}},
  author  = {Psaros, Apostolos F and Meng, Xuhui and Zou, Zongren and Guo,
             Ling and Karniadakis, George Em},
  journal = {Journal of Computational Physics},
  volume  = {477},
  pages   = {111902},
  year    = {2023}
}
```

### [18] Abdar et al. (2021) — Deep learning UQ comprehensive review

Abdar, M., Pourpanah, F., Hussain, S., Rezazadegan, D., Liu, L.,
Ghavamzadeh, M., ... & Nahavandi, S. (2021). A review of uncertainty
quantification in deep learning: Techniques, applications and challenges.
*Information Fusion*, 76, 243–297.

**Placement**: Introduction (broad UQ landscape)

```bibtex
@article{abdar2021review,
  title   = {A review of uncertainty quantification in deep learning:
             Techniques, applications and challenges},
  author  = {Abdar, Moloud and Pourpanah, Farhad and Hussain, Syed and
             Rezazadegan, Danish and Liu, Li and Ghavamzadeh, Mohammad and
             Fieguth, Paul and Cao, Xiaochun and Khosravi, Abbas and Acharya,
             U Rajendra and others},
  journal = {Information Fusion},
  volume  = {76},
  pages   = {243--297},
  year    = {2021}
}
```

---

## Category 3: Sensitivity Analysis & Bayesian Calibration

### [10] Kennedy & O'Hagan (2001) — Bayesian calibration of computer models

Kennedy, M. C., & O'Hagan, A. (2001). Bayesian calibration of computer
models. *Journal of the Royal Statistical Society: Series B (Statistical
Methodology)*, 63(3), 425–464.

**Placement**: Methods §4.6 (MCMC calibration theory); Results §2.4

```bibtex
@article{kennedy2001bayesian,
  title   = {Bayesian calibration of computer models},
  author  = {Kennedy, Marc C and O'Hagan, Anthony},
  journal = {Journal of the Royal Statistical Society: Series B (Statistical
             Methodology)},
  volume  = {63},
  number  = {3},
  pages   = {425--464},
  year    = {2001}
}
```

### [11] Saltelli et al. (2010) — Sobol total sensitivity index estimator

Saltelli, A., Annoni, P., Azzini, I., Campolongo, F., Ratto, M., &
Tarantola, S. (2010). Variance based sensitivity analysis of model output.
Design and estimator for the total sensitivity index. *Computer Physics
Communications*, 179(4), 259–270.

**Placement**: Methods §4.5 (Sobol decomposition); Results §2.3

```bibtex
@article{saltelli2010variance,
  title   = {Variance based sensitivity analysis of model output. Design and
             estimator for the total sensitivity index},
  author  = {Saltelli, Andrea and Annoni, Paola and Azzini, Ivano and
             Campolongo, Francesca and Ratto, Marco and Tarantola, Stefano},
  journal = {Computer Physics Communications},
  volume  = {179},
  number  = {4},
  pages   = {259--270},
  year    = {2010}
}
```

---

## Category 4: Multiphysics Solver Citations

### [12] Romano et al. (2015) — OpenMC

Romano, P. K., Horelik, N. E., Herman, B. R., Nelson, A. G., Forget, B.,
& Smith, K. (2015). OpenMC: A state-of-the-art Monte Carlo code for
research and development. *Annals of Nuclear Energy*, 82, 90–97.

**Placement**: Methods §4.1 (dataset generation — neutronics solver)

```bibtex
@article{romano2015openmc,
  title   = {{OpenMC}: A state-of-the-art {Monte Carlo} code for research and
             development},
  author  = {Romano, Paul K and Horelik, Nicholas E and Herman, Bryan R and
             Nelson, Adam G and Forget, Benoit and Smith, Kord},
  journal = {Annals of Nuclear Energy},
  volume  = {82},
  pages   = {90--97},
  year    = {2015}
}
```

### [13] Logg et al. (2012) — FEniCS

Logg, A., Mardal, K. A., & Wells, G. (Eds.). (2012). *Automated Solution
of Differential Equations by the Finite Element Method: The FEniCS Book*
(Vol. 84). Springer.

**Placement**: Methods §4.1 (dataset generation — thermal-structural solver)

```bibtex
@book{logg2012automated,
  title     = {Automated Solution of Differential Equations by the Finite
               Element Method: The {FEniCS} Book},
  author    = {Logg, Anders and Mardal, Kent-Andre and Wells, Garth},
  volume    = {84},
  year      = {2012},
  publisher = {Springer}
}
```

---

## Category 5: Discussion & Future Work Support

### [14] Ovadia et al. (2019) — OOD uncertainty under dataset shift

Ovadia, Y., Fertig, E., Ren, J., Nado, Z., Sculley, D., Nowozin, S., ...
& Snoek, J. (2019). Can you trust your model's uncertainty? Evaluating
predictive uncertainty under dataset shift. *Advances in Neural Information
Processing Systems*, 32.

**Placement**: Discussion §3.2 (OOD generalization — support PICP argument)

```bibtex
@article{ovadia2019can,
  title   = {Can you trust your model's uncertainty? Evaluating predictive
             uncertainty under dataset shift},
  author  = {Ovadia, Yaniv and Fertig, Emily and Ren, Jie and Nado, Zachary
             and Sculley, D and Nowozin, Sebastian and Dillon, Joshua V and
             Lakshminarayanan, Balaji and Snoek, Jasper},
  journal = {Advances in Neural Information Processing Systems},
  volume  = {32},
  year    = {2019}
}
```

### [15] Wang et al. (2021) — PINN gradient pathologies

Wang, S., Teng, Y., & Perdikaris, P. (2021). Understanding and mitigating
gradient flow pathologies in physics-informed neural networks. *SIAM Journal
on Scientific Computing*, 43(5), A3055–A3081.

**Placement**: Discussion §3.1 (why physics-constrained BNN, not hard-constraint PINN)

```bibtex
@article{wang2021understanding,
  title   = {Understanding and mitigating gradient flow pathologies in
             physics-informed neural networks},
  author  = {Wang, Sifan and Teng, Yujun and Perdikaris, Paris},
  journal = {SIAM Journal on Scientific Computing},
  volume  = {43},
  number  = {5},
  pages   = {A3055--A3081},
  year    = {2021}
}
```

### [16] Pestourie et al. (2020) — Active learning deep surrogates for PDEs

Pestourie, R., Mroueh, U., Nguyen, T. V., Ma, P., & Johnson, S. G. (2020).
Active learning of deep surrogates for PDEs: Application to metasurface
design. *npj Computational Materials*, 6(1), 164.

**Placement**: Introduction (surrogate efficiency / data efficiency context)

```bibtex
@article{pestourie2020active,
  title   = {Active learning of deep surrogates for {PDE}s: Application to
             metasurface design},
  author  = {Pestourie, Raphael and Mroueh, Youssef and Nguyen, T-V and Ma,
             Peng and Johnson, Steven G},
  journal = {npj Computational Materials},
  volume  = {6},
  number  = {1},
  pages   = {164},
  year    = {2020}
}
```

### [17] Cranmer et al. (2020) — Symbolic regression from deep learning

Cranmer, M., Sanchez Gonzalez, A., Battaglia, P., Xu, R., Cranmer, K.,
Spergel, D., & Ho, S. (2020). Discovering symbolic models from deep
learning with inductive biases. *Advances in Neural Information Processing
Systems*, 33, 17429–17442.

**Placement**: Discussion §3.4 future work (extracting interpretable physics laws)

```bibtex
@article{cranmer2020discovering,
  title   = {Discovering symbolic models from deep learning with inductive
             biases},
  author  = {Cranmer, Miles and Sanchez Gonzalez, Alvaro and Battaglia, Peter
             and Xu, Richard and Cranmer, Kyle and Spergel, David and Ho,
             Shirley},
  journal = {Advances in Neural Information Processing Systems},
  volume  = {33},
  pages   = {17429--17442},
  year    = {2020}
}
```

---

---

## Category 6: Heat Pipe Microreactors & Multiphysics (Phase 2)

### [19] McClure et al. (2015) — HPR design concept ⚠️ REBUILT

McClure, P. R., Poston, D. I., Dasari, V. R., & Reid, R. S. (2015).
Design of megawatt power level heat pipe reactors. *Los Alamos National
Laboratory*. DOI: 10.2172/1226133.

**Placement**: Introduction §1 (early HPR design background)

> **⚠️ CONSENSUS RULE**: Title locked to "Design of megawatt power level
> heat pipe reactors". Do NOT revert to KRUSTY title. Authors corrected
> from original Gemini entry. See LITERATURE_VERIFICATION_LOG.md Batch 2.

```bibtex
@techreport{mcclure2015design,
  title       = {Design of megawatt power level heat pipe reactors},
  author      = {McClure, Patrick R and Poston, David I and Dasari,
                 Venkateswara R and Reid, Robert S},
  year        = {2015},
  institution = {Los Alamos National Lab., Los Alamos, NM},
  doi         = {10.2172/1226133}
}
```

### [20] Stauff et al. (2024) — BlueCrab multiphysics for HPR

Stauff, N. E., Miao, Y., Cao, Y., & Lee, J. (2024). High-fidelity
multiphysics modeling of a heat pipe microreactor using BlueCrab. *Nuclear
Science and Engineering*, 198(1), 1–15.

**Placement**: Introduction (state-of-art HF multiphysics for microreactors)

> **Verification note**: Gemini flagged volume/pages as approximate. Must
> confirm via DOI before use.

```bibtex
@article{stauff2024high,
  title   = {High-fidelity multiphysics modeling of a heat pipe microreactor
             using {BlueCrab}},
  author  = {Stauff, Nicolas E and Miao, Yinbin and Cao, Y and Lee, J},
  journal = {Nuclear Science and Engineering},
  volume  = {198},
  number  = {1},
  pages   = {1--15},
  year    = {2024}
}
```

### [21] Miao et al. (2025) — MOOSE simulation of KRUSTY

Miao, Y., Cao, Y., Mo, K., & Lee, J. (2025). Multiphysics simulation of
KRUSTY warm critical experiments using MOOSE tools. *Nuclear Science and
Engineering*.

**Placement**: Introduction (MOOSE ecosystem reference)

> **Verification note**: 2025 publication — may be online-first. Confirm
> volume/pages/DOI exist. High hallucination risk for very recent papers.

```bibtex
@article{miao2025multiphysics,
  title   = {Multiphysics simulation of {KRUSTY} warm critical experiments
             using {MOOSE} tools},
  author  = {Miao, Yinbin and Cao, Y and Mo, K and Lee, J},
  journal = {Nuclear Science and Engineering},
  year    = {2025}
}
```

### [22] Ma et al. (2021) — Thermo-mechanical analysis of HPR core ⚠️ FROZEN

Ma, Z., Hu, R., & Su, J. (2021). Thermo-mechanical analysis of a heat
pipe cooled microreactor core under nominal and faulted conditions. *Annals
of Nuclear Energy*, 160, 108422.

**Placement**: Introduction (stress concentration as persistent safety concern
in monolithic HPR cores — directly supports our problem statement)

> **⚠️ CONSENSUS RULE**: 保留为待人工 DOI/出版元数据最终确认的候选条目；
> 在人工确认前，不进入主文。GPT 无法验证此条目存在。Gemini 曾将同一条目
> 再次提议填入 [64]，形成矛盾。若需替代，可用：
> - Jiao et al. (2023), *Progress in Nuclear Energy*
> - Jeong et al. (2023), *Frontiers in Energy Research*

```bibtex
@article{ma2021thermo,
  title   = {Thermo-mechanical analysis of a heat pipe cooled microreactor
             core under nominal and faulted conditions},
  author  = {Ma, Z and Hu, R and Su, J},
  journal = {Annals of Nuclear Energy},
  volume  = {160},
  pages   = {108422},
  year    = {2021}
}
```

### [23] — PLACEHOLDER for own team's prior simulation work

> Replace with Wang Sicheng / Zhang Tengfei's published HPR simulation or
> coupling framework paper to show research continuity. This slot is reserved
> for a self-citation that establishes the solver pipeline used to generate
> training data.

---

## Category 7: Traditional UQ in Nuclear Engineering (Phase 2)

### [24] Sudret (2008) — PCE for global sensitivity analysis

Sudret, B. (2008). Global sensitivity analysis using polynomial chaos
expansions. *Reliability Engineering & System Safety*, 93(7), 964–979.

**Placement**: Introduction (contrast BNN with classical PCE/GP surrogates;
motivate why PCE struggles with coupled nonlinear systems)

```bibtex
@article{sudret2008global,
  title   = {Global sensitivity analysis using polynomial chaos expansions},
  author  = {Sudret, Bruno},
  journal = {Reliability Engineering \& System Safety},
  volume  = {93},
  number  = {7},
  pages   = {964--979},
  year    = {2008}
}
```

### [25] Williams (1986) — Early uncertainty perspective in reactor physics

Williams, M. M. R. (1986). Reactor physics. *Progress in Nuclear Energy*,
17(2), 113–140.

**Placement**: Introduction (historical framing of epistemic/aleatoric
uncertainty origins in nuclear data)

> **Verification note**: This is a broad review chapter. Confirm it actually
> discusses uncertainty propagation, not just reactor physics methods.

```bibtex
@article{williams1986reactor,
  title   = {Reactor physics},
  author  = {Williams, M M R},
  journal = {Progress in Nuclear Energy},
  volume  = {17},
  number  = {2},
  pages   = {113--140},
  year    = {1986}
}
```

### [26] Smith (2013) — UQ textbook (comprehensive reference)

Smith, R. C. (2013). *Uncertainty Quantification: Theory, Implementation,
and Applications* (Vol. 12). SIAM.

**Placement**: Methods or Introduction (general UQ framework reference)

```bibtex
@book{smith2013uncertainty,
  title     = {Uncertainty Quantification: Theory, Implementation, and
               Applications},
  author    = {Smith, Ralph C},
  volume    = {12},
  year      = {2013},
  publisher = {SIAM}
}
```

### [27] Wu et al. (2018) — Kriging/GP-based inverse UQ in nuclear

Wu, X., Kozlowski, T., & Meidani, H. (2018). Kriging-based inverse
uncertainty quantification of nuclear reactor physics parameters. *Nuclear
Engineering and Design*, 335, 39–47.

**Placement**: Introduction (prior GP-based surrogate UQ attempts in nuclear
engineering → motivates why BNN is an advance)

```bibtex
@article{wu2018kriging,
  title   = {Kriging-based inverse uncertainty quantification of nuclear
             reactor physics parameters},
  author  = {Wu, Xingang and Kozlowski, Tomasz and Meidani, Hadi},
  journal = {Nuclear Engineering and Design},
  volume  = {335},
  pages   = {39--47},
  year    = {2018}
}
```

---

## Category 8: Digital Twins & Computational Acceleration (Phase 2)

### [28] Glaessgen & Stargel (2012) — Digital twin paradigm definition

Glaessgen, M., & Stargel, D. (2012). The digital twin paradigm for future
NASA and US Air Force vehicles. In *53rd AIAA/ASME/ASCE/AHS/ASC Structures,
Structural Dynamics and Materials Conference* (p. 1818).

**Placement**: Introduction or Discussion (frame surrogate speedup as
enabling digital-twin-class real-time response)

```bibtex
@inproceedings{glaessgen2012digital,
  title     = {The digital twin paradigm for future {NASA} and {US Air Force}
               vehicles},
  author    = {Glaessgen, Edward and Stargel, David},
  booktitle = {53rd AIAA/ASME/ASCE/AHS/ASC Structures, Structural Dynamics
               and Materials Conference},
  pages     = {1818},
  year      = {2012}
}
```

### [29] Kapteyn et al. (2021) — Probabilistic digital twins at scale (NCS!)

Kapteyn, M. G., Pretorius, J. V., & Willcox, K. E. (2021). A
probabilistic graphical model foundation for enabling predictive digital
twins at scale. *Nature Computational Science*, 1(5), 337–347.

**Placement**: Introduction / Discussion (highly relevant — published in
target journal NCS; probabilistic model supporting digital twin, parallels
our "unified predictive layer" concept)

> **Strategic note**: Citing an NCS paper signals awareness of target journal
> scope and positions our work in conversation with existing NCS literature.

```bibtex
@article{kapteyn2021probabilistic,
  title   = {A probabilistic graphical model foundation for enabling
             predictive digital twins at scale},
  author  = {Kapteyn, Michael G and Pretorius, Jacob V and Willcox, Karen E},
  journal = {Nature Computational Science},
  volume  = {1},
  number  = {5},
  pages   = {337--347},
  year    = {2021}
}
```

### [30] — PLACEHOLDER for recent AI-for-PDE / ML-accelerated simulation

> Gemini suggested a generic slot here. Fill with a specific recent paper
> on ML-accelerated multiphysics (e.g., from Nature Computational Science,
> CMAME, or JCP 2023–2025) once identified through manual search.

---

## Verification Checklist

Before inserting any reference into the final manuscript:

- [ ] Verify DOI exists and resolves to correct paper
- [ ] Confirm volume/pages/year match actual publication
- [ ] Check author list completeness (Gemini may have truncated "et al.")
- [ ] Ensure no duplicate entries with existing bibliography
- [ ] Cross-check against Zotero/EndNote import

**Extra caution for Phase 2 refs**:
- [ ] [20] Stauff 2024: volume/pages approximate — verify via DOI
- [ ] [21] Miao 2025: very recent, high hallucination risk — confirm exists
- [ ] [25] Williams 1986: broad title — confirm UQ content relevance
- [ ] [23] and [30]: placeholders — fill with verified real papers

---

## Category 9: Evaluation Metrics — Rigorous Sources (Phase 3)

### [31] Gneiting & Raftery (2007) — CRPS authoritative definition

Gneiting, T., & Raftery, A. E. (2007). Strictly proper scoring rules,
prediction, and estimation. *Journal of the American Statistical
Association*, 102(477), 359–378.

**Placement**: Methods (metric definitions); explains why CRPS simultaneously
rewards sharpness and calibration.

```bibtex
@article{gneiting2007strictly,
  title   = {Strictly proper scoring rules, prediction, and estimation},
  author  = {Gneiting, Tilmann and Raftery, Adrian E},
  journal = {Journal of the American Statistical Association},
  volume  = {102},
  number  = {477},
  pages   = {359--378},
  year    = {2007}
}
```

### [32] Guo et al. (2017) — ECE definition in deep learning

Guo, C., Pleiss, G., Sun, Y., & Weinberger, K. Q. (2017). On calibration
of modern neural networks. In *International Conference on Machine Learning*
(pp. 1321–1330). PMLR.

**Placement**: Methods / Results §2.1 (calibration metric definition)

```bibtex
@inproceedings{guo2017calibration,
  title        = {On calibration of modern neural networks},
  author       = {Guo, Chuan and Pleiss, Geoff and Sun, Yu and Weinberger,
                  Kilian Q},
  booktitle    = {International Conference on Machine Learning},
  pages        = {1321--1330},
  year         = {2017},
  organization = {PMLR}
}
```

### [33] Pearce et al. (2018) — PICP/MPIW for deep learning intervals

Pearce, T., Brintrup, M., Zaki, M., & Neely, A. (2018). High-quality
prediction intervals for deep learning: A distribution-free, ensembled
approach. In *International Conference on Machine Learning* (pp. 4075–4084).

**Placement**: Methods (interval quality metrics — PICP coverage vs MPIW
sharpness tradeoff)

```bibtex
@inproceedings{pearce2018high,
  title     = {High-quality prediction intervals for deep learning: A
               distribution-free, ensembled approach},
  author    = {Pearce, Tim and Brintrup, Mohamed and Zaki, Mohamed and Neely,
               Andy},
  booktitle = {International Conference on Machine Learning},
  pages     = {4075--4084},
  year      = {2018}
}
```

---

## Category 10: MCMC Diagnostics & Variational Inference (Phase 3)

### [34] Vehtari et al. (2021) — Rank-normalized R-hat (critical!)

Vehtari, A., Gelman, A., Simpson, D., Carpenter, B., & Bürkner, P. C.
(2021). Rank-normalization, folding, and localization: An improved R-hat
for assessing convergence of MCMC (with discussion). *Bayesian Analysis*,
16(2), 667–718.

**Placement**: Methods §4.6 / Results §2.4 (MCMC diagnostics). The 1.01
threshold used in `run_posterior_0404.py` and Fig 6C comes from this paper.
Citing it signals methodological awareness to Bayesian-literate reviewers.

```bibtex
@article{vehtari2021rank,
  title   = {Rank-normalization, folding, and localization: An improved
             {$\hat{R}$} for assessing convergence of {MCMC} (with discussion)},
  author  = {Vehtari, Aki and Gelman, Andrew and Simpson, Daniel and
             Carpenter, Bob and B{\"u}rkner, Paul-Christian},
  journal = {Bayesian Analysis},
  volume  = {16},
  number  = {2},
  pages   = {667--718},
  year    = {2021}
}
```

### [35] Blei et al. (2017) — Variational inference & ELBO review

Blei, D. M., Kucukelbir, A., & McAuliffe, J. D. (2017). Variational
inference: A review for statisticians. *Journal of the American Statistical
Association*, 112(518), 859–877.

**Placement**: Methods §4.3 (ELBO derivation / VI framework)

```bibtex
@article{blei2017variational,
  title   = {Variational inference: A review for statisticians},
  author  = {Blei, David M and Kucukelbir, Alp and McAuliffe, Jon D},
  journal = {Journal of the American Statistical Association},
  volume  = {112},
  number  = {518},
  pages   = {859--877},
  year    = {2017}
}
```

### [36] Kingma & Ba (2014) — Adam optimizer

Kingma, D. P., & Ba, J. (2014). Adam: A method for stochastic optimization.
*arXiv preprint arXiv:1412.6980*. (Published at ICLR 2015.)

**Placement**: Methods §4.3 (training procedure)

```bibtex
@article{kingma2014adam,
  title   = {Adam: A method for stochastic optimization},
  author  = {Kingma, Diederik P and Ba, Jimmy},
  journal = {arXiv preprint arXiv:1412.6980},
  year    = {2014}
}
```

---

## Category 11: Epistemic vs Aleatoric — Engineering Significance (Phase 3)

### [37] Der Kiureghian & Ditlevsen (2009) — Classic engineering decomposition

Der Kiureghian, A., & Ditlevsen, O. (2009). Aleatory or epistemic? Does it
matter? *Structural Safety*, 31(2), 105–112.

**Placement**: Discussion / Results (why distinguishing uncertainty types
matters for engineering design — epistemic is reducible by more data/experiments)

```bibtex
@article{der2009aleatory,
  title   = {Aleatory or epistemic? Does it matter?},
  author  = {Der Kiureghian, Armen and Ditlevsen, Ove},
  journal = {Structural Safety},
  volume  = {31},
  number  = {2},
  pages   = {105--112},
  year    = {2009}
}
```

### [38] Hüllermeier & Waegeman (2021) — ML uncertainty concepts review

Hüllermeier, E., & Waegeman, W. (2021). Aleatoric and epistemic uncertainty
in machine learning: An introduction to concepts and methods. *Machine
Learning*, 110, 457–506.

**Placement**: Discussion (modern ML-aware framing of uncertainty decomposition)

```bibtex
@article{hullermeier2021aleatoric,
  title   = {Aleatoric and epistemic uncertainty in machine learning: An
             introduction to concepts and methods},
  author  = {H{\"u}llermeier, Eyke and Waegeman, Willem},
  journal = {Machine Learning},
  volume  = {110},
  pages   = {457--506},
  year    = {2021}
}
```

---

## Category 12: Multi-Fidelity Methods (Phase 3)

### [39] Peherstorfer et al. (2018) — MF methods in UQ survey

Peherstorfer, B., Willcox, K., & Gunzburger, M. (2018). Survey of
multifidelity methods in uncertainty propagation, inference, and
optimization. *SIAM Review*, 60(3), 550–591.

**Placement**: Discussion (contextualize MF-hybrid ablation results; explain
when MF advantage decays — e.g., highly nonlinear low-to-high residuals)

```bibtex
@article{peherstorfer2018survey,
  title   = {Survey of multifidelity methods in uncertainty propagation,
             inference, and optimization},
  author  = {Peherstorfer, Benjamin and Willcox, Karen and Gunzburger, Max},
  journal = {SIAM Review},
  volume  = {60},
  number  = {3},
  pages   = {550--591},
  year    = {2018}
}
```

### [40] Meng & Karniadakis (2020) — Neural network multi-fidelity composite

Meng, X., & Karniadakis, G. E. (2020). A composite neural network that
learns from multi-fidelity data: Application to function approximation and
inverse PDE problems. *Journal of Computational Physics*, 401, 109020.

**Placement**: Discussion / Appendix (MF neural network baseline context)

```bibtex
@article{meng2020composite,
  title   = {A composite neural network that learns from multi-fidelity data:
             Application to function approximation and inverse {PDE} problems},
  author  = {Meng, Xuhui and Karniadakis, George Em},
  journal = {Journal of Computational Physics},
  volume  = {401},
  pages   = {109020},
  year    = {2020}
}
```

---

## Category 13: Nuclear Material Properties — Prior Sources (Phase 3)

### [41] Fink (2000) — UO2 thermophysical properties standard

Fink, J. K. (2000). Thermophysical properties of uranium dioxide. *Journal
of Nuclear Materials*, 279(1), 1–18.

**Placement**: Methods §4.1 (parameter perturbation ranges for fuel properties)

```bibtex
@article{fink2000thermophysical,
  title   = {Thermophysical properties of uranium dioxide},
  author  = {Fink, J K},
  journal = {Journal of Nuclear Materials},
  volume  = {279},
  number  = {1},
  pages   = {1--18},
  year    = {2000}
}
```

### [42] ASME BPVC Section II Part D — SS316 material properties ✅ STRONGEST ANCHOR

ASME. *ASME Boiler and Pressure Vessel Code, Section II: Materials,
Part D: Properties (Customary)*. American Society of Mechanical Engineers.

**Placement**: Methods §4.1 (justifies E_intercept, E_slope, alpha_base
perturbation ranges and monotonicity constraints from engineering standards).
**主文核心锚点** — SS316 弹性模量、热膨胀和强度阈值的主锚点。

> **⚠️ CONSENSUS RULE**: 使用 "ASME BPVC Section II Part D（按最终核定版本）"，
> 不锁死年份。GPT 验证 2021 Edition 存在且权威。BibTeX 年份应按最终采用版本填写。
> "This is the single most defensible reference in your nuclear-specific group." — GPT

```bibtex
@book{asme_bpvc_iid,
  title     = {{ASME} Boiler and Pressure Vessel Code, Section {II}:
               Materials, Part {D}: Properties (Customary)},
  author    = {{ASME}},
  year      = {2021},
  publisher = {American Society of Mechanical Engineers},
  note      = {Update year to match edition actually used}
}
```

### [43] Hagrman et al. (1981) — MATPRO fuel handbook ⚠️ NUREG# CORRECTED

Hagrman, D. L., Reymann, G. A., & Mason, R. E. (1981). *MATPRO — Version 11
(Revision 2): A Handbook of Materials Properties for Use in the Analysis of
Light Water Reactor Fuel Rod Behavior* (NUREG/CR-0497, Rev. 2; EGG-2179).
EG&G Idaho, Inc., for U.S. Nuclear Regulatory Commission.

**Placement**: SI Note E (fuel property input distributions — alongside [41] and [76])

> **⚠️ CORRECTED**: NUREG number changed from CR-0446 (wrong) to CR-0497 Rev. 2.
> Alternate report number: EGG-2179.

```bibtex
@techreport{hagrman1981matpro,
  title       = {{MATPRO} --- Version 11 (Revision 2): A Handbook of Materials
                 Properties for Use in the Analysis of Light Water Reactor
                 Fuel Rod Behavior},
  author      = {Hagrman, D L and Reymann, G A and Mason, R E},
  number      = {NUREG/CR-0497, Rev.~2 (EGG-2179)},
  year        = {1981},
  institution = {EG\&G Idaho, Inc.}
}
```

---

## Category 14: Monotonic Neural Networks (Phase 3)

### [44] Sill (1998) — Early monotonic networks

Sill, J. (1998). Monotonic networks. *Advances in Neural Information
Processing Systems*, 10.

**Placement**: Methods §4.4 / Discussion (foundational reference for
architectural monotonicity enforcement)

```bibtex
@article{sill1998monotonic,
  title   = {Monotonic networks},
  author  = {Sill, Joseph},
  journal = {Advances in Neural Information Processing Systems},
  volume  = {10},
  year    = {1998}
}
```

### [45] Gupta et al. (2016) — Monotonic calibrated look-up tables

Gupta, M., Cotter, A., Pfeifer, J., Voevodski, K., Canini, K.,
Mangylov, A., ... & Anderson, A. (2016). Monotonic calibrated interpolated
look-up tables. *Journal of Machine Learning Research*, 17(1), 3790–3836.

**Placement**: Methods §4.4 (industrial-scale monotonicity constraint
approaches — context for our soft-constraint design choice)

```bibtex
@article{gupta2016monotonic,
  title   = {Monotonic calibrated interpolated look-up tables},
  author  = {Gupta, Maya and Cotter, Andrew and Pfeifer, Jan and Voevodski,
             Konstantin and Canini, Kevin and Mangylov, Alexander and
             Anderson, Andrew},
  journal = {Journal of Machine Learning Research},
  volume  = {17},
  number  = {1},
  pages   = {3790--3836},
  year    = {2016}
}
```

---

---

## Category 15: Multi-Physics Coupling Algorithms & Bottlenecks (Phase 4)

### [46] Gaston et al. (2009) — MOOSE framework

Gaston, D., Newman, C., Hansen, G., & Lebrun-Grandié, D. (2009). MOOSE: A
parallel computational framework for coupled systems for nuclear
applications. *Nuclear Engineering and Design*, 239(10), 1768–1778.

**Placement**: Introduction §1 (HF coupling ecosystem; motivates speedup)

```bibtex
@article{gaston2009moose,
  title   = {{MOOSE}: A parallel computational framework for coupled systems
             for nuclear applications},
  author  = {Gaston, Derek and Newman, Chris and Hansen, Glen and
             Lebrun-Grandi{\'e}, Damien},
  journal = {Nuclear Engineering and Design},
  volume  = {239},
  number  = {10},
  pages   = {1768--1778},
  year    = {2009}
}
```

### [47] Knoll & Keyes (2004) — JFNK survey (coupling complexity)

Knoll, D. A., & Keyes, D. E. (2004). Jacobian-free Newton–Krylov methods:
A survey of approaches and applications. *Journal of Computational Physics*,
193(2), 357–397.

**Placement**: Introduction (why coupled multiphysics iteration is expensive)

```bibtex
@article{knoll2004jacobian,
  title   = {Jacobian-free {Newton--Krylov} methods: a survey of approaches
             and applications},
  author  = {Knoll, Dana A and Keyes, David E},
  journal = {Journal of Computational Physics},
  volume  = {193},
  number  = {2},
  pages   = {357--397},
  year    = {2004}
}
```

---

## Category 16: BNN Classical & Modern Roots (Phase 4)

### [48] MacKay (1992) — BNN founder

MacKay, D. J. C. (1992). A practical Bayesian framework for
backpropagation networks. *Neural Computation*, 4(3), 448–472.

**Placement**: Methods §4.3 (BNN lineage — signals deep algorithmic
understanding to statistical reviewers)

```bibtex
@article{mackay1992practical,
  title   = {A practical {B}ayesian framework for backpropagation networks},
  author  = {MacKay, David JC},
  journal = {Neural Computation},
  volume  = {4},
  number  = {3},
  pages   = {448--472},
  year    = {1992}
}
```

### [49] Neal (1996) — Bayesian Learning for Neural Networks

Neal, R. M. (1996). *Bayesian Learning for Neural Networks*. Springer.

**Placement**: Methods §4.3 (foundational BNN reference)

```bibtex
@book{neal1996bayesian,
  title     = {Bayesian Learning for Neural Networks},
  author    = {Neal, Radford M},
  year      = {1996},
  publisher = {Springer}
}
```

### [50] Kingma & Welling (2014) — Reparameterization trick (VAE)

Kingma, D. P., & Welling, M. (2014). Auto-encoding variational Bayes.
In *International Conference on Learning Representations (ICLR)*.

**Placement**: Methods §4.3 (mathematical basis for reparameterization in
ELBO optimization — directly used in `bnn_model.py`)

```bibtex
@inproceedings{kingma2014auto,
  title     = {Auto-encoding variational {B}ayes},
  author    = {Kingma, Diederik P and Welling, Max},
  booktitle = {International Conference on Learning Representations},
  year      = {2014}
}
```

### [51] Graves (2011) — Practical variational inference for NNs

Graves, A. (2011). Practical variational inference for neural networks.
In *Advances in Neural Information Processing Systems* (pp. 2348–2356).

**Placement**: Methods §4.3 (pre-Blundell VI for neural networks)

```bibtex
@inproceedings{graves2011practical,
  title     = {Practical variational inference for neural networks},
  author    = {Graves, Alex},
  booktitle = {Advances in Neural Information Processing Systems},
  pages     = {2348--2356},
  year      = {2011}
}
```

---

## Category 17: Input Uncertainty Sources — Nuclear Data & Tolerances (Phase 4)

### [52] Brown et al. (2018) — ENDF/B-VIII.0 nuclear data library ⚠️ SI-ONLY

Brown, D. A., Chadwick, M. B., Capote, R., et al. (2018). ENDF/B-VIII.0:
The 8th major release of the nuclear reaction data library with CIELO-project
cross sections, new standards and thermal scattering data. *Nuclear Data
Sheets*, 148, 1–142. DOI: 10.1016/j.nds.2018.02.001.

**Placement**: SI only, or one-sentence Methods mention ("neutronics
calculations used ENDF/B-VIII.0 cross-section libraries")

> **⚠️ CONSENSUS RULE**: 仅允许作为 OpenMC 使用核数据库的一句话背景引用。
> 不得进入 input uncertainty 主线。本文 UQ 的输入不确定性来自 8 个 SS316
> 经验参数，不是核数据。"This is upstream of your simulation chain but not
> part of your uncertainty characterization." — GPT

```bibtex
@article{brown2018endf,
  title   = {{ENDF/B-VIII.0}: The 8th major release of the nuclear reaction
             data library},
  author  = {Brown, David A and Chadwick, Mark B and Capote, Roberto and
             others},
  journal = {Nuclear Data Sheets},
  volume  = {148},
  pages   = {1--142},
  year    = {2018},
  doi     = {10.1016/j.nds.2018.02.001}
}
```

### [53] Cacuci (2003) — Nuclear sensitivity & uncertainty analysis textbook

Cacuci, D. G. (2003). *Sensitivity and Uncertainty Analysis, Volume 1:
Theory*. CRC Press.

**Placement**: Introduction / Methods (nuclear-domain UQ authority)

```bibtex
@book{cacuci2003sensitivity,
  title     = {Sensitivity and Uncertainty Analysis, Volume 1: Theory},
  author    = {Cacuci, Dan G},
  year      = {2003},
  publisher = {CRC Press}
}
```

---

## Category 18: Sampling & Experimental Design (Phase 4)

### [54] McKay et al. (1979) — Latin Hypercube Sampling

McKay, M. D., Beckman, R. J., & Conover, W. J. (1979). A comparison of
three methods for selecting values of input variables in the analysis of
output from a computer code. *Technometrics*, 21(2), 239–245.

**Placement**: Methods §4.1 (justifies LHS for dataset generation)

```bibtex
@article{mckay1979comparison,
  title   = {A comparison of three methods for selecting values of input
             variables in the analysis of output from a computer code},
  author  = {McKay, Michael D and Beckman, Richard J and Conover, William J},
  journal = {Technometrics},
  volume  = {21},
  number  = {2},
  pages   = {239--245},
  year    = {1979}
}
```

### [55] Hoffman & Gelman (2014) — NUTS / HMC sampler

Hoffman, M. D., & Gelman, A. (2014). The No-U-Turn sampler: Adaptively
setting path lengths in Hamiltonian Monte Carlo. *Journal of Machine
Learning Research*, 15(1), 1593–1623.

**Placement**: Discussion / Future work (higher-dim MCMC alternative to
current Metropolis-Hastings)

```bibtex
@article{hoffman2014no,
  title   = {The {No-U-Turn} sampler: Adaptively setting path lengths in
             {H}amiltonian {M}onte {C}arlo},
  author  = {Hoffman, Matthew D and Gelman, Andrew},
  journal = {Journal of Machine Learning Research},
  volume  = {15},
  number  = {1},
  pages   = {1593--1623},
  year    = {2014}
}
```

---

## Category 19: ML in Nuclear Engineering — Recent Surveys (Phase 5)

### [56] Gomez-Fernandez et al. (2020) — ML in nuclear engineering status

Gomez-Fernandez, M., et al. (2020). Status and perspectives of machine
learning in nuclear engineering. *Nuclear Engineering and Design*, 367,
110738.

**Placement**: Introduction (positions work within nuclear-ML trend)

```bibtex
@article{gomez2020status,
  title   = {Status and perspectives of machine learning in nuclear
             engineering},
  author  = {Gomez-Fernandez, M and others},
  journal = {Nuclear Engineering and Design},
  volume  = {367},
  pages   = {110738},
  year    = {2020}
}
```

### [57] Radaideh & Kozlowski (2020) — DNN surrogate in reactor physics ⚠️ FROZEN/REPLACE

~~Radaideh, M. I., & Kozlowski, T. (2020). Neural-based surrogate modeling
for uncertainty quantification in reactor physics. *Annals of Nuclear
Energy*, 136, 107021.~~ **← 当前条目不可验证，已废弃**

**Verified replacement** (from GPT Batch 4):
> Radaideh, M. I., & Kozlowski, T. (2020). Analyzing nuclear reactor
> simulation data and uncertainty with the group method of data handling.
> *Nuclear Engineering and Technology*, 52(3), 601–611.
> DOI: 10.1016/j.net.2019.08.015.

**Placement**: Introduction (prior surrogate work lacking coherent Bayesian
UQ — motivates our BNN approach)

> **⚠️ CONSENSUS RULE**: 废弃当前条目。若确有需要，改用上方已核实的替代条目。

```bibtex
% REPLACEMENT — use this instead of the original entry
@article{radaideh2020analyzing,
  title   = {Analyzing nuclear reactor simulation data and uncertainty
             with the group method of data handling},
  author  = {Radaideh, Majdi I and Kozlowski, Tomasz},
  journal = {Nuclear Engineering and Technology},
  volume  = {52},
  number  = {3},
  pages   = {601--611},
  year    = {2020},
  doi     = {10.1016/j.net.2019.08.015}
}
```

### [58] — PLACEHOLDER for surrogate-driven design exploration

> Fill with a specific paper on surrogate-accelerated engineering design
> (e.g., Farthing et al. 2021 or similar). Supports the 10⁵× speedup
> narrative.

---

## Category 20: Sobol & Explainable AI Bridge (Phase 5)

### [59] Lundberg & Lee (2017) — SHAP

Lundberg, S. M., & Lee, S. I. (2017). A unified approach to interpreting
model predictions. *Advances in Neural Information Processing Systems*, 30.

**Placement**: Discussion (contrast: Sobol provides global variance-based
physical attribution, whereas SHAP/saliency are local gradient-based —
our approach is more appropriate for physics-driven sensitivity)

```bibtex
@article{lundberg2017unified,
  title   = {A unified approach to interpreting model predictions},
  author  = {Lundberg, Scott M and Lee, Su-In},
  journal = {Advances in Neural Information Processing Systems},
  volume  = {30},
  year    = {2017}
}
```

### [60] Iooss & Lemaître (2015) — Global sensitivity analysis review

Iooss, B., & Lemaître, P. (2015). A review on global sensitivity analysis
methods. In *Uncertainty Management in Simulation-Optimization of Complex
Systems* (pp. 101–122). Springer.

**Placement**: Methods §4.5 / Discussion (comprehensive SA landscape)

```bibtex
@incollection{iooss2015review,
  title     = {A review on global sensitivity analysis methods},
  author    = {Iooss, Bertrand and Lema{\^\i}tre, Paul},
  booktitle = {Uncertainty Management in Simulation-Optimization of Complex
               Systems},
  pages     = {101--122},
  year      = {2015},
  publisher = {Springer}
}
```

---

## Category 21: Theory-Guided Data Science (Phase 5)

### [61] Karpatne et al. (2017) — TGDS paradigm definition

Karpatne, A., Atluri, G., Faghmous, J. H., Steinbach, M., Banerjee, A.,
Ganguly, A., ... & Kumar, V. (2017). Theory-guided data science: A new
paradigm for scientific discovery from data. *IEEE Transactions on Knowledge
and Data Engineering*, 29(10), 2318–2331.

**Placement**: Introduction (high-level framing: physics-regularized BNN
as an instance of theory-guided data science)

```bibtex
@article{karpatne2017theory,
  title   = {Theory-guided data science: A new paradigm for scientific
             discovery from data},
  author  = {Karpatne, Anuj and Atluri, Gowtham and Faghmous, James H and
             Steinbach, Michael and Banerjee, Arindam and Ganguly, Auroop
             and Shekhar, Shashi and Samatova, Nitesh and Kumar, Vipin},
  journal = {IEEE Transactions on Knowledge and Data Engineering},
  volume  = {29},
  number  = {10},
  pages   = {2318--2331},
  year    = {2017}
}
```

### [62] — PLACEHOLDER for causal/monotonic discovery in physical systems

> Gemini suggested Runge et al. (2019) *Nature Communications* on causal
> discovery. Verify existence and relevance before inserting.

---

## Category 22: Supplementary Method & Domain References (Phase 5)

### [63] — PLACEHOLDER: Bootstrapped neural networks (Osband et al. 2016)
> For comparison with ensemble/seed-based uncertainty methods.

### [64] — PLACEHOLDER: High-temperature reactor thermomechanics
> Fill with specific paper on HPR structural integrity under thermal stress.

### [65] — PLACEHOLDER: Own team's prior work (Zhang/Chen/Wang)
> Self-citation establishing solver pipeline continuity. Same slot as [23].

### [66] Gelman et al. (2013) — Bayesian Data Analysis textbook

Gelman, A., Carlin, J. B., Stern, H. S., Dunson, D. B., Vehtari, A., &
Rubin, D. B. (2013). *Bayesian Data Analysis* (3rd ed.). CRC Press.

**Placement**: Methods / Appendix (general Bayesian framework authority)

```bibtex
@book{gelman2013bayesian,
  title     = {Bayesian Data Analysis},
  author    = {Gelman, Andrew and Carlin, John B and Stern, Hal S and Dunson,
               David B and Vehtari, Aki and Rubin, Donald B},
  edition   = {3rd},
  year      = {2013},
  publisher = {CRC Press}
}
```

### [67] — PLACEHOLDER: PCE dimensionality curse (Sargsyan et al. 2015)
> Supports argument that PCE struggles in high-dim coupled systems.

### [68] O'Hagan (2006) — Bayesian calibration philosophy

O'Hagan, A. (2006). Bayesian analysis of computer code outputs: A tutorial.
*Reliability Engineering & System Safety*, 91(10–11), 1290–1300.

**Placement**: Methods §4.6 / Discussion (philosophical justification for
MCMC calibration as scientific necessity, not just technique)

```bibtex
@article{ohagan2006bayesian,
  title   = {Bayesian analysis of computer code outputs: A tutorial},
  author  = {O'Hagan, Anthony},
  journal = {Reliability Engineering \& System Safety},
  volume  = {91},
  number  = {10--11},
  pages   = {1290--1300},
  year    = {2006}
}
```

### [69] Jospin et al. (2022) — Hands-on BNN tutorial/review

Jospin, L. V., Laga, H., Boussaid, F., Buntine, W., & Bennamoun, M.
(2022). Hands-on Bayesian neural networks — A tutorial for deep learning
users. *IEEE Computational Intelligence Magazine*, 17(2), 29–48.

**Placement**: Methods or Supplementary (reader-friendly BNN entry point
for reproducibility)

```bibtex
@article{jospin2022hands,
  title   = {Hands-on {B}ayesian neural networks---A tutorial for deep
             learning users},
  author  = {Jospin, Laurent Valentin and Laga, Hamid and Boussaid, Farid
             and Buntine, Wray and Bennamoun, Mohammed},
  journal = {IEEE Computational Intelligence Magazine},
  volume  = {17},
  number  = {2},
  pages   = {29--48},
  year    = {2022}
}
```

### [70] Gawlikowski et al. (2021) — Deep learning UQ survey (latest)

Gawlikowski, J., et al. (2021). A survey of uncertainty in deep neural
networks. *arXiv preprint arXiv:2107.03342*.

**Placement**: Introduction (comprehensive recent UQ survey)

> **Verification note**: Check if this has been published in a journal
> (possibly *Artificial Intelligence Review* 2023). Prefer journal version.

```bibtex
@article{gawlikowski2021survey,
  title   = {A survey of uncertainty in deep neural networks},
  author  = {Gawlikowski, Jakob and others},
  journal = {arXiv preprint arXiv:2107.03342},
  year    = {2021}
}
```

---

## Category 23: BNN Training & Weight Initialization — SI Note A (Phase 6)

### [71] He et al. (2015) — He/Kaiming initialization

He, K., Zhang, X., Ren, S., & Sun, J. (2015). Delving deep into
rectifiers: Surpassing human-level performance on ImageNet classification.
In *Proceedings of the IEEE International Conference on Computer Vision*
(pp. 1026–1034).

**Placement**: SI Note A.5 (weight initialization for ReLU networks)

```bibtex
@inproceedings{he2015delving,
  title     = {Delving deep into rectifiers: Surpassing human-level performance
               on {ImageNet} classification},
  author    = {He, Kaiming and Zhang, Xiangyu and Ren, Shaoqing and Sun, Jian},
  booktitle = {Proceedings of the IEEE International Conference on Computer
               Vision},
  pages     = {1026--1034},
  year      = {2015}
}
```

### [72] Glorot & Bengio (2010) — Xavier initialization

Glorot, X., & Bengio, Y. (2010). Understanding the difficulty of training
deep feedforward neural networks. In *AISTATS* (pp. 249–256).

**Placement**: SI Note A.5 (Xavier uniform initialization justification)

> **Verification note**: Confirm venue is AISTATS 2010, not ICML.

```bibtex
@inproceedings{glorot2010understanding,
  title     = {Understanding the difficulty of training deep feedforward
               neural networks},
  author    = {Glorot, Xavier and Bengio, Yoshua},
  booktitle = {Proceedings of the 13th International Conference on Artificial
               Intelligence and Statistics (AISTATS)},
  pages     = {249--256},
  year      = {2010}
}
```

---

## Category 24: Scoring Rules & Bootstrap Theory — SI Note B (Phase 6)

### [73] Gneiting (2011) — Point forecast evaluation (sharpness principle)

Gneiting, T. (2011). Making and evaluating point forecasts. *Journal of the
American Statistical Association*, 106(494), 746–762.

**Placement**: SI Note B (deeper CRPS theory — why probabilistic mass
matters more than point accuracy)

```bibtex
@article{gneiting2011making,
  title   = {Making and evaluating point forecasts},
  author  = {Gneiting, Tilmann},
  journal = {Journal of the American Statistical Association},
  volume  = {106},
  number  = {494},
  pages   = {746--762},
  year    = {2011}
}
```

### [74] Efron & Tibshirani (1994) — Bootstrap methods

Efron, B., & Tibshirani, R. J. (1994). *An Introduction to the Bootstrap*.
CRC Press.

**Placement**: SI Note B.4 (statistical basis for 50-replication Sobol CI
extraction via bootstrap)

```bibtex
@book{efron1994introduction,
  title     = {An Introduction to the Bootstrap},
  author    = {Efron, Bradley and Tibshirani, Robert J},
  year      = {1994},
  publisher = {CRC Press}
}
```

---

## Category 25: Nuclear Material Properties — SI Note E (Phase 6)

### [75] OECD/NEA (2019) — Material properties handbook

OECD/NEA. (2019). *Handbook on Lead-bismuth Eutectic Alloy and Lead
Properties, Materials Compatibility, Thermal-hydraulics and Technologies*.
OECD Publishing.

**Placement**: SI Note E.1 (material property data authority)

> **Verification note**: Gemini's title may be wrong — verify exact OECD/NEA
> handbook relevant to SS316 high-temperature properties. May need to
> substitute with a more specific stainless steel data compilation.

```bibtex
@book{oecd2019handbook,
  title     = {Handbook on Lead-bismuth Eutectic Alloy and Lead Properties},
  author    = {{OECD/NEA}},
  year      = {2019},
  publisher = {OECD Publishing}
}
```

### [76] Popov et al. (2000) — UO2/MOX thermophysical evaluation

Popov, S. G., et al. (2000). *Thermophysical Properties of MOX and UO2
Fuels*. Oak Ridge National Laboratory Report, ORNL/TM-2000/351.

**Placement**: SI Note E.1 (fuel thermal conductivity k(T) fitting basis)

```bibtex
@techreport{popov2000thermophysical,
  title       = {Thermophysical Properties of {MOX} and {UO2} Fuels},
  author      = {Popov, S G and others},
  number      = {ORNL/TM-2000/351},
  year        = {2000},
  institution = {Oak Ridge National Laboratory}
}
```

---

## Category 26: Coupling Iteration Theory — SI Note E.3 (Phase 6)

### [77] Kelley (1995) — Iterative methods for nonlinear equations

Kelley, C. T. (1995). *Iterative Methods for Linear and Nonlinear
Equations*. SIAM.

**Placement**: SI Note E.3 (Picard/fixed-point iteration convergence theory
for nuclear-thermal-structural coupling)

```bibtex
@book{kelley1995iterative,
  title     = {Iterative Methods for Linear and Nonlinear Equations},
  author    = {Kelley, Carl T},
  year      = {1995},
  publisher = {SIAM}
}
```

---

## Category 27: Posterior Consistency & Sampling Theory — SI Note C (Phase 6)

### [78] Stuart (2010) — Inverse problems: A Bayesian perspective

Stuart, A. M. (2010). Inverse problems: A Bayesian perspective. *Acta
Numerica*, 19, 451–559.

**Placement**: SI Note C (mathematical foundation for surrogate-embedded
MCMC posterior consistency — high-prestige reference for NCS editors)

```bibtex
@article{stuart2010inverse,
  title   = {Inverse problems: A {B}ayesian perspective},
  author  = {Stuart, Andrew M},
  journal = {Acta Numerica},
  volume  = {19},
  pages   = {451--559},
  year    = {2010}
}
```

### [79] Tierney (1994) — MCMC stationary distribution theory

Tierney, L. (1994). Markov chains for exploring posterior distributions.
*The Annals of Statistics*, 22(4), 1701–1728.

**Placement**: SI Note C.1 (Metropolis-Hastings ergodicity and stationary
distribution properties)

```bibtex
@article{tierney1994markov,
  title   = {Markov chains for exploring posterior distributions},
  author  = {Tierney, Luke},
  journal = {The Annals of Statistics},
  volume  = {22},
  number  = {4},
  pages   = {1701--1728},
  year    = {1994}
}
```

---

## Anti-Rebuttal Sentence Templates (Phases 4+5 — ready to embed)

**Introduction — coupling bottleneck:**
> Conventional coupled multiphysics simulations rely on Picard or
> Jacobian-free Newton–Krylov iteration [47] within frameworks such as
> MOOSE [46], making each forward solve prohibitively expensive for
> Monte Carlo–based uncertainty propagation [24, 53].

**Introduction — prior surrogates lack UQ:**
> Existing deep-learning surrogates in reactor physics have demonstrated
> impressive point-prediction accuracy [57], yet they typically lack a
> coherent probabilistic framework that propagates predictive uncertainty
> through sensitivity attribution and posterior calibration [56].

**Methods — BNN lineage:**
> Bayesian neural networks were introduced by MacKay [48] and Neal [49]
> and made scalable through variational inference [51, 4] using the
> reparameterization trick [50].

**Methods — input uncertainty:**
> Material-property perturbation ranges follow ASME standards [42] and
> established fuel-property correlations [41, 43]; nuclear cross-section
> uncertainties are inherited from ENDF/B-VIII.0 [52].

**Discussion — Sobol vs SHAP:**
> Unlike local gradient-based attribution methods such as SHAP [59], our
> Sobol-based sensitivity analysis [11, 60] provides global, variance-based
> decomposition that captures nonlinear parameter interactions across the
> full input distribution.

---

## Anti-Rebuttal Sentence Templates (Phase 3 — ready to embed)

These pre-built sentences map Phase 3 refs to specific manuscript locations:

**Methods — metric justification:**
> To comprehensively evaluate probabilistic predictive quality, we employed
> the Continuous Ranked Probability Score (CRPS) [31], which simultaneously
> rewards sharpness and calibration, and the Expected Calibration Error
> (ECE) [32] to quantify predictive interval reliability.

**Methods — MCMC diagnostics:**
> Convergence was verified using the split-rank normalized R-hat
> statistic [34], with a strict threshold of 1.01 applied to all four
> chains across all 18 benchmark cases.

**Discussion — OOD epistemic inflation:**
> A well-calibrated probabilistic surrogate must signal greater epistemic
> uncertainty when queried outside its training manifold [38, 14]. The BNN
> correctly inflated its epistemic standard deviation by 7–21% in
> out-of-distribution tail regions (Supplementary Fig. S4).

**Discussion — why not hard-constraint PINN:**
> Hard-constraint physics-informed networks suffer from gradient flow
> pathologies that destabilize multi-objective training [15]. Our
> soft-constraint approach injects physics as a prior on the loss landscape
> rather than a hard architectural constraint [3, 44].

**Discussion — multi-fidelity context:**
> Although multi-fidelity methods can exploit solver hierarchies for
> efficiency [39, 40], the nonlinear residual between decoupled and coupled
> solutions in our system limits the advantage of simple additive correction
> schemes — a finding consistent with the ablation in Appendix B3b.

---

## Verification Checklist

Before inserting any reference into the final manuscript:

- [ ] Verify DOI exists and resolves to correct paper
- [ ] Confirm volume/pages/year match actual publication
- [ ] Check author list completeness (Gemini may have truncated "et al.")
- [ ] Ensure no duplicate entries with existing bibliography
- [ ] Cross-check against Zotero/EndNote import

**Phase 2 extra caution**:
- [ ] [20] Stauff 2024: volume/pages approximate — verify via DOI
- [ ] [21] Miao 2025: very recent, high hallucination risk — confirm exists
- [ ] [25] Williams 1986: broad title — confirm UQ content relevance
- [ ] [23] and [30]: placeholders — fill with verified real papers

**Phase 3 extra caution**:
- [ ] [33] Pearce 2018: verify author "Brintrup" (may be "Brint" or other)
- [ ] [43] Hagrman 1981: tech report — confirm NUREG number
- [ ] [36] Kingma 2014: arXiv only — some journals prefer ICLR 2015 citation

**Phase 4+5 extra caution**:
- [ ] [58] placeholder — fill with surrogate-driven design paper
- [ ] [62] placeholder — verify Runge et al. 2019 NatComm exists & is relevant
- [ ] [63–65, 67] placeholders — fill with verified papers
- [ ] [70] Gawlikowski 2021: arXiv — check if journal version exists (AI Review 2023?)
- [ ] [75] OECD/NEA 2019: title may not match — verify exact handbook

**SI-specific Phase 6 extra caution**:
- [ ] [72] Glorot 2010: verify it's AISTATS not ICML
- [ ] [75] OECD/NEA: verify exact title and report number
- [ ] [76] Popov 2000: verify ORNL report number

## Summary: All References by Category

| Cat | Topic | Refs | Count |
|-----|-------|------|-------|
| 1 | SciML & Physics-Informed ML | [1–3] | 3 |
| 2 | BNN & UQ | [4–9, 18] | 7 |
| 3 | Sensitivity & Calibration | [10–11] | 2 |
| 4 | Multiphysics Solvers | [12–13] | 2 |
| 5 | Discussion & Future Work | [14–17] | 4 |
| 6 | HPR & Multiphysics (P2) | [19–23] | 5 |
| 7 | Traditional Nuclear UQ (P2) | [24–27] | 4 |
| 8 | Digital Twins (P2) | [28–30] | 3 |
| 9 | Evaluation Metrics (P3) | [31–33] | 3 |
| 10 | MCMC & VI Theory (P3) | [34–36] | 3 |
| 11 | Epistemic/Aleatoric Eng. (P3) | [37–38] | 2 |
| 12 | Multi-Fidelity (P3) | [39–40] | 2 |
| 13 | Nuclear Material Props (P3) | [41–43] | 3 |
| 14 | Monotonic Networks (P3) | [44–45] | 2 |
| 15 | Coupling Algorithms (P4) | [46–47] | 2 |
| 16 | BNN Classical Roots (P4) | [48–51] | 4 |
| 17 | Nuclear Data & Tolerances (P4) | [52–53] | 2 |
| 18 | Sampling & DoE (P4) | [54–55] | 2 |
| 19 | ML in Nuclear (P5) | [56–58] | 3 |
| 20 | Sobol & XAI (P5) | [59–60] | 2 |
| 21 | Theory-Guided DS (P5) | [61–62] | 2 |
| 22 | Supplementary Refs (P5) | [63–70] | 8 |
| 23 | BNN Training/Init (SI-P6) | [71–72] | 2 |
| 24 | Scoring Rules Deep Theory (SI-P6) | [73–74] | 2 |
| 25 | Nuclear Materials (SI-P6) | [75–76] | 2 |
| 26 | Coupling Iteration Theory (SI-P6) | [77] | 1 |
| 27 | Posterior & Sampling Theory (SI-P6) | [78–79] | 2 |
| | **Total** | | **79** |

---

## Category 28: Data Generation & LHS Resampling (Phase 7 — SI)

### [80] McKay et al. (2000) — LHS reprint/modern citation

McKay, M. D., Beckman, R. J., & Conover, W. J. (2000). A comparison of
three methods for selecting values of input variables in the analysis of
output from a computer code. *Technometrics*, 42(1), 55–61.

**Placement**: SI data generation (modern reprint of classic 1979 LHS paper)

> **Note**: This is a reprint of [54]. Use whichever version your field
> cites more commonly. Do not cite both.

```bibtex
@article{mckay2000comparison,
  title   = {A comparison of three methods for selecting values of input
             variables in the analysis of output from a computer code},
  author  = {McKay, Michael D and Beckman, Richard J and Conover, William J},
  journal = {Technometrics},
  volume  = {42},
  number  = {1},
  pages   = {55--61},
  year    = {2000}
}
```

### [81] Viana (2016) — LHS tutorial for engineering surrogates

Viana, F. A. (2016). A tutorial on Latin hypercube design of experiments.
*Quality and Reliability Engineering International*, 32(5), 1975–1985.

**Placement**: SI (justifies sample size selection for surrogate training)

```bibtex
@article{viana2016tutorial,
  title   = {A tutorial on {L}atin hypercube design of experiments},
  author  = {Viana, Felipe AC},
  journal = {Quality and Reliability Engineering International},
  volume  = {32},
  number  = {5},
  pages   = {1975--1985},
  year    = {2016}
}
```

---

## Category 29: Variational Inference Optimization (Phase 7 — SI Note A)

### [82] Hoffman et al. (2013) — Stochastic variational inference

Hoffman, M. D., Blei, D. M., Wang, C., & Paisley, J. (2013). Stochastic
variational inference. *Journal of Machine Learning Research*, 14(1),
1303–1347.

**Placement**: SI Note A / Methods (VI mathematical background)

```bibtex
@article{hoffman2013stochastic,
  title   = {Stochastic variational inference},
  author  = {Hoffman, Matthew D and Blei, David M and Wang, Chong and
             Paisley, John},
  journal = {Journal of Machine Learning Research},
  volume  = {14},
  number  = {1},
  pages   = {1303--1347},
  year    = {2013}
}
```

### [83] Reddi et al. (2019) — Adam convergence analysis

Reddi, S. J., Kale, S., & Kumar, S. (2019). On the convergence of Adam
and beyond. *arXiv preprint arXiv:1904.09237*. (ICLR 2018.)

**Placement**: SI Note A (Adam optimizer convergence properties)

> **Verification note**: Originally ICLR 2018. arXiv version is 2019 update.

```bibtex
@inproceedings{reddi2019convergence,
  title     = {On the convergence of {Adam} and beyond},
  author    = {Reddi, Sashank J and Kale, Satyen and Kumar, Sanjiv},
  booktitle = {International Conference on Learning Representations},
  year      = {2018}
}
```

---

## Category 30: Multi-Fidelity Degradation Theory (Phase 7)

### [84] Fernández-Godino et al. (2016) — MF models review

Fernández-Godino, M. G., Park, C., Kim, N. H., & Haftka, R. T. (2016).
Review of multi-fidelity models. *arXiv preprint arXiv:1609.07196*.

**Placement**: Discussion / Appendix B3b (why MF is not always beneficial)

> **Verification note**: arXiv only — check if journal version exists.

```bibtex
@article{fernandez2016review,
  title   = {Review of multi-fidelity models},
  author  = {Fern{\'a}ndez-Godino, M Giselle and Park, Chanyoung and Kim,
             Nam H and Haftka, Raphael T},
  journal = {arXiv preprint arXiv:1609.07196},
  year    = {2016}
}
```

### [85] Perdikaris et al. (2017) — Nonlinear MF information fusion

Perdikaris, P., Raissi, M., Damianou, A., Lawrence, N. D. (2017).
Nonlinear information fusion algorithms for data-efficient multi-fidelity
modelling. *Proceedings of the Royal Society A*, 473(2198), 20160751.

**Placement**: Discussion / Appendix B3b (when MF fails with nonlinear
residuals — supports our finding)

```bibtex
@article{perdikaris2017nonlinear,
  title   = {Nonlinear information fusion algorithms for data-efficient
             multi-fidelity modelling},
  author  = {Perdikaris, Paris and Raissi, Maziar and Damianou, Andreas
             and Lawrence, Neil D},
  journal = {Proceedings of the Royal Society A},
  volume  = {473},
  number  = {2198},
  pages   = {20160751},
  year    = {2017}
}
```

---

## Category 31: Evaluation Metrics — Extended Sources (Phase 7)

### [86] Naeini et al. (2015) — Bayesian binning for calibration (ECE)

Naeini, M. P., Cooper, G., & Hauskrecht, M. (2015). Obtaining well
calibrated probabilities using Bayesian binning into quantiles. In *AAAI
Conference on Artificial Intelligence*.

**Placement**: SI / Methods (supplementary ECE reference)

```bibtex
@inproceedings{naeini2015obtaining,
  title     = {Obtaining well calibrated probabilities using {B}ayesian binning
               into quantiles},
  author    = {Naeini, Mahdi Pakdaman and Cooper, Gregory and Hauskrecht,
               Milos},
  booktitle = {AAAI Conference on Artificial Intelligence},
  year      = {2015}
}
```

### [87] Khosravi et al. (2011) — PICP/MPIW classic source

Khosravi, A., Nahavandi, S., Creighton, D., & Atiya, A. F. (2011).
Comprehensive review of neural network-based prediction intervals and new
advances. *IEEE Transactions on Neural Networks*, 22(9), 1341–1356.

**Placement**: Methods / SI (PICP and MPIW definitive reference)

```bibtex
@article{khosravi2011comprehensive,
  title   = {Comprehensive review of neural network-based prediction intervals
             and new advances},
  author  = {Khosravi, Abbas and Nahavandi, Saeid and Creighton, Doug and
             Atiya, Amir F},
  journal = {IEEE Transactions on Neural Networks},
  volume  = {22},
  number  = {9},
  pages   = {1341--1356},
  year    = {2011}
}
```

---

## Category 32: HPR Safety Benchmarks (Phase 7)

### [88] Sterbentz et al. (2018) — SPR megawatt-class microreactor design

Sterbentz, P. N., et al. (2018). *Special Purpose Reactor (SPR)
Megawatt-Class Design*. Idaho National Laboratory.

**Placement**: Introduction (microreactor design basis and safety context)

```bibtex
@techreport{sterbentz2018special,
  title       = {Special Purpose Reactor ({SPR}) Megawatt-Class Design},
  author      = {Sterbentz, P N and others},
  year        = {2018},
  institution = {Idaho National Laboratory}
}
```

### [89] Hu et al. (2021) — Heat pipe microreactor multiphysics ⚠️ REBUILT

~~Hu, R., et al. (2019). Modeling and simulations of heat pipe solid core
microreactor. *Nuclear Technology*, 205(1–2), 190–205.~~ **← 拼接条目，已废弃**

**Rebuilt entry** (from GPT Batch 4 — 2021 journal version):
> Hu, G., Hu, R., Kelly, J. M., & Ortensi, J. (2021). Coupled multiphysics
> simulations of heat pipe–cooled nuclear microreactors. *Nuclear Technology*,
> 207(7), 1020–1040. DOI: 10.1080/00295450.2021.1882588.

**Placement**: Introduction (HPR thermal-structural coupling — peer-reviewed)

> **⚠️ CONSENSUS RULE**: 废弃 2019 条目（为两篇文献拼接产物），使用 2021
> Nuclear Technology 期刊版。

```bibtex
@article{hu2021coupled,
  title   = {Coupled multiphysics simulations of heat pipe--cooled nuclear
             microreactors},
  author  = {Hu, Guojun and Hu, Rui and Kelly, Joseph M and Ortensi, Javier},
  journal = {Nuclear Technology},
  volume  = {207},
  number  = {7},
  pages   = {1020--1040},
  year    = {2021},
  doi     = {10.1080/00295450.2021.1882588}
}
```

---

## Category 33: Sobol Convergence & Variance Decomposition (Phase 7)

### [90] Owen (2013) — Variance-based feature importance

Owen, A. B. (2013). Variance components and generalized Sobol' indices.
*SIAM/ASA Journal on Uncertainty Quantification*, 1(1), 19–41.

**Placement**: SI / Methods (Sobol convergence theory)

> **Verification note**: Gemini cited JASA 2013 but Owen's Sobol work is
> in SIAM/ASA JUQ. Verify exact paper.

```bibtex
@article{owen2013variance,
  title   = {Variance components and generalized {Sobol'} indices},
  author  = {Owen, Art B},
  journal = {SIAM/ASA Journal on Uncertainty Quantification},
  volume  = {1},
  number  = {1},
  pages   = {19--41},
  year    = {2013}
}
```

### [91] Glen & Isaacs (2012) — Sobol indices via correlations

Glen, G., & Isaacs, R. (2012). Estimating Sobol sensitivity indices using
correlations. *Environmental Modelling & Software*, 37, 157–166.

**Placement**: SI (sample-size requirements for stable S₁/ST)

```bibtex
@article{glen2012estimating,
  title   = {Estimating {Sobol} sensitivity indices using correlations},
  author  = {Glen, Graham and Isaacs, Rachel},
  journal = {Environmental Modelling \& Software},
  volume  = {37},
  pages   = {157--166},
  year    = {2012}
}
```

---

## Category 34: Heteroscedastic Noise Modeling (Phase 7)

### [92] Nix & Weigend (1994) — Learning input-dependent variance

Nix, D. A., & Weigend, A. S. (1994). Estimating the mean and variance of
the target probability distribution. In *Proceedings of 1994 IEEE
International Conference on Neural Networks* (Vol. 1, pp. 55–60).

**Placement**: Methods / SI Note A (foundational reference for
heteroscedastic neural networks — learning σ²(x))

```bibtex
@inproceedings{nix1994estimating,
  title     = {Estimating the mean and variance of the target probability
               distribution},
  author    = {Nix, David A and Weigend, Andreas S},
  booktitle = {Proceedings of 1994 IEEE International Conference on Neural
               Networks},
  volume    = {1},
  pages     = {55--60},
  year      = {1994}
}
```

### [93] — PLACEHOLDER for heteroscedastic NN regression

> Gemini cited "Le et al. 2005 Neurocomputing" but details are incomplete.
> Verify or replace with a well-established heteroscedastic regression ref.

---

## Category 35: OpenMC Internals & Nuclear Data Processing (Phase 7)

### [94] Herman et al. (2014) — OpenMC tallying improvements

Herman, B. R., et al. (2014). Improved tallying in the OpenMC Monte Carlo
particle transport code. *Transactions of the American Nuclear Society*.

**Placement**: SI (OpenMC k_eff calculation details)

> **Verification note**: ANS Transactions — verify volume/pages.

```bibtex
@article{herman2014improved,
  title   = {Improved tallying in the {OpenMC Monte Carlo} particle transport
             code},
  author  = {Herman, Bryan R and others},
  journal = {Transactions of the American Nuclear Society},
  year    = {2014}
}
```

### [95] MacFarlane et al. (2010) — NJOY nuclear data processing

MacFarlane, R. E., et al. (2010). *The NJOY Nuclear Data Processing
System*. Los Alamos National Laboratory.

**Placement**: SI (cross-section temperature broadening reference)

```bibtex
@techreport{macfarlane2010njoy,
  title       = {The {NJOY} Nuclear Data Processing System},
  author      = {MacFarlane, Robert E and others},
  year        = {2010},
  institution = {Los Alamos National Laboratory}
}
```

---

## Category 36: FEniCS & Structural Mechanics (Phase 7)

### [96] Alnæs et al. (2015) — FEniCS v1.5

Alnæs, M. S., et al. (2015). The FEniCS project version 1.5. *Archive of
Numerical Software*, 3(100).

**Placement**: Methods / SI (supplementary FEniCS citation)

```bibtex
@article{alnaes2015fenics,
  title   = {The {FEniCS} project version 1.5},
  author  = {Aln{\ae}s, Martin S and others},
  journal = {Archive of Numerical Software},
  volume  = {3},
  number  = {100},
  year    = {2015}
}
```

### [97] Zienkiewicz et al. (2013) — FEM for solid mechanics

Zienkiewicz, O. C., Taylor, R. L., & Fox, D. D. (2013). *The Finite
Element Method for Solid and Structural Mechanics* (7th ed.). Elsevier.

**Placement**: SI (linear elasticity / thermal expansion equation authority)

```bibtex
@book{zienkiewicz2013finite,
  title     = {The Finite Element Method for Solid and Structural Mechanics},
  author    = {Zienkiewicz, Olek C and Taylor, Robert L and Fox, David D},
  edition   = {7th},
  year      = {2013},
  publisher = {Elsevier}
}
```

---

## Category 37: Gradient-Based Soft Constraints (Phase 7)

### [98] Dugas et al. (2009) — Incorporating functional knowledge in NNs

Dugas, C., Bengio, Y., Bélisle, F., Nadeau, C., & Garcia, R. (2009).
Incorporating second-order functional knowledge for better option pricing.
*Advances in Neural Information Processing Systems*, 13.

**Placement**: Methods §4.4 / SI (supports monotonicity penalty in ELBO)

> **Verification note**: Gemini cited "2009 JMLR" but the original is
> NeurIPS 2000. Verify correct venue and year.

```bibtex
@inproceedings{dugas2000incorporating,
  title     = {Incorporating second-order functional knowledge for better
               option pricing},
  author    = {Dugas, Charles and Bengio, Yoshua and B{\'e}lisle, Fran{\c{c}}ois
               and Nadeau, Claude and Garcia, Ren{\'e}},
  booktitle = {Advances in Neural Information Processing Systems},
  volume    = {13},
  year      = {2000}
}
```

### [99] Cotter et al. (2019) — Shape constraints for set functions

Cotter, A., et al. (2019). Shape constraints for set functions. In
*International Conference on Machine Learning*.

**Placement**: Methods §4.4 (soft constraints preserve point accuracy while
improving generalization)

```bibtex
@inproceedings{cotter2019shape,
  title     = {Shape constraints for set functions},
  author    = {Cotter, Andrew and others},
  booktitle = {International Conference on Machine Learning},
  year      = {2019}
}
```

---

## Category 38: Extended UQ & Model Comparison (Phase 7)

### [100] Gal et al. (2017) — Concrete Dropout

Gal, Y., Hron, J., & Kendall, A. (2017). Concrete dropout. *Advances in
Neural Information Processing Systems*, 30.

**Placement**: SI / Discussion (Dropout variant comparison)

> **Note**: Use instead of re-citing [6] if a distinct Dropout reference
> is needed for the SI.

```bibtex
@article{gal2017concrete,
  title   = {Concrete dropout},
  author  = {Gal, Yarin and Hron, Jiri and Kendall, Alex},
  journal = {Advances in Neural Information Processing Systems},
  volume  = {30},
  year    = {2017}
}
```

### [101] Yao et al. (2019) — BNN inference quality comparison

Yao, J., Pan, W., Ghosh, S., & Doshi-Velez, F. (2019). Quality of
uncertainty quantification for Bayesian neural network inference. *arXiv
preprint arXiv:1906.09686*.

**Placement**: SI (BNN inference scheme comparison)

```bibtex
@article{yao2019quality,
  title   = {Quality of uncertainty quantification for {B}ayesian neural
             network inference},
  author  = {Yao, Jiayu and Pan, Weiwei and Ghosh, Soumya and Doshi-Velez,
             Finale},
  journal = {arXiv preprint arXiv:1906.09686},
  year    = {2019}
}
```

### [102] Izmailov et al. (2021) — Subspace inference for BDL

Izmailov, P., et al. (2021). Subspace inference for Bayesian deep learning.
In *UAI*.

**Placement**: Discussion (BNN scalability future work)

```bibtex
@inproceedings{izmailov2021subspace,
  title     = {Subspace inference for {B}ayesian deep learning},
  author    = {Izmailov, Pavel and others},
  booktitle = {Conference on Uncertainty in Artificial Intelligence (UAI)},
  year      = {2021}
}
```

### [103] — PLACEHOLDER: Probabilistic surrogate for multiphysics (Wang et al. 2020 JCP)
> Verify existence and relevance.

### [104] — PLACEHOLDER: Physics-informed ML for nuclear engineering (Qiu et al. 2022 ANE)
> Verify existence and relevance.

### [105] Papamakarios et al. (2021) — Normalizing flows review

Papamakarios, G., Nalisnick, E., Rezende, D. J., Mohamed, S., &
Lakshminarayanan, B. (2021). Normalizing flows for probabilistic modeling
and inference. *Journal of Machine Learning Research*, 22(57), 1–64.

**Placement**: Discussion / Future work (alternative to MCMC for posterior)

```bibtex
@article{papamakarios2021normalizing,
  title   = {Normalizing flows for probabilistic modeling and inference},
  author  = {Papamakarios, George and Nalisnick, Eric and Rezende, Danilo Jimenez
             and Mohamed, Shakir and Lakshminarayanan, Balaji},
  journal = {Journal of Machine Learning Research},
  volume  = {22},
  number  = {57},
  pages   = {1--64},
  year    = {2021}
}
```

### [106] Snoek et al. (2012) — Bayesian optimization of ML hyperparameters

Snoek, J., Larochelle, H., & Adams, R. P. (2012). Practical Bayesian
optimization of machine learning algorithms. *Advances in Neural
Information Processing Systems*, 25.

**Placement**: SI (hyperparameter search justification — Optuna context)

```bibtex
@article{snoek2012practical,
  title   = {Practical {B}ayesian optimization of machine learning algorithms},
  author  = {Snoek, Jasper and Larochelle, Hugo and Adams, Ryan P},
  journal = {Advances in Neural Information Processing Systems},
  volume  = {25},
  year    = {2012}
}
```

### [107] — PLACEHOLDER: Cyclical SGMCMC (Zhang et al. 2020 ICLR)
> MCMC scaling for neural networks. Verify.

---

## Category 39: Software Citations (Phase 7 — required by NCS)

### [108] — NOTE: Abdar 2021 already cited as [18]. Skip duplicate.

### [109] Paszke et al. (2019) — PyTorch

Paszke, A., et al. (2019). PyTorch: An imperative style, high-performance
deep learning library. *Advances in Neural Information Processing Systems*,
32, 8026–8037.

**Placement**: Methods / SI (mandatory software citation)

```bibtex
@article{paszke2019pytorch,
  title   = {{PyTorch}: An imperative style, high-performance deep learning
             library},
  author  = {Paszke, Adam and others},
  journal = {Advances in Neural Information Processing Systems},
  volume  = {32},
  pages   = {8026--8037},
  year    = {2019}
}
```

### [110] Akiba et al. (2019) — Optuna

Akiba, T., Sano, S., Yanase, T., Ohta, T., & Koyama, M. (2019). Optuna:
A next-generation hyperparameter optimization framework. In *Proceedings of
the 25th ACM SIGKDD International Conference on Knowledge Discovery & Data
Mining* (pp. 2623–2631).

**Placement**: Methods / SI (supports `_load_bnn_hparams` pipeline)

```bibtex
@inproceedings{akiba2019optuna,
  title     = {Optuna: A next-generation hyperparameter optimization framework},
  author    = {Akiba, Takuya and Sano, Shotaro and Yanase, Toshihiko and Ohta,
               Takeru and Koyama, Masanori},
  booktitle = {Proceedings of the 25th ACM SIGKDD International Conference on
               Knowledge Discovery \& Data Mining},
  pages     = {2623--2631},
  year      = {2019}
}
```

---

## Final Summary: 110 References by Category

| Cat | Topic | Refs | Count |
|-----|-------|------|-------|
| 1 | SciML & Physics-Informed ML | [1–3] | 3 |
| 2 | BNN & UQ | [4–9, 18] | 7 |
| 3 | Sensitivity & Calibration | [10–11] | 2 |
| 4 | Multiphysics Solvers | [12–13] | 2 |
| 5 | Discussion & Future Work | [14–17] | 4 |
| 6 | HPR & Multiphysics (P2) | [19–23] | 5 |
| 7 | Traditional Nuclear UQ (P2) | [24–27] | 4 |
| 8 | Digital Twins (P2) | [28–30] | 3 |
| 9 | Evaluation Metrics (P3) | [31–33] | 3 |
| 10 | MCMC & VI Theory (P3) | [34–36] | 3 |
| 11 | Epistemic/Aleatoric Eng. (P3) | [37–38] | 2 |
| 12 | Multi-Fidelity (P3) | [39–40] | 2 |
| 13 | Nuclear Material Props (P3) | [41–43] | 3 |
| 14 | Monotonic Networks (P3) | [44–45] | 2 |
| 15 | Coupling Algorithms (P4) | [46–47] | 2 |
| 16 | BNN Classical Roots (P4) | [48–51] | 4 |
| 17 | Nuclear Data & Tolerances (P4) | [52–53] | 2 |
| 18 | Sampling & DoE (P4) | [54–55] | 2 |
| 19 | ML in Nuclear (P5) | [56–58] | 3 |
| 20 | Sobol & XAI (P5) | [59–60] | 2 |
| 21 | Theory-Guided DS (P5) | [61–62] | 2 |
| 22 | Supplementary Refs (P5) | [63–70] | 8 |
| 23 | BNN Training/Init (P6) | [71–72] | 2 |
| 24 | Scoring Rules Theory (P6) | [73–74] | 2 |
| 25 | Nuclear Materials SI (P6) | [75–76] | 2 |
| 26 | Coupling Iteration (P6) | [77] | 1 |
| 27 | Posterior Theory (P6) | [78–79] | 2 |
| 28 | Data Generation/LHS (P7) | [80–81] | 2 |
| 29 | VI Optimization (P7) | [82–83] | 2 |
| 30 | MF Degradation Theory (P7) | [84–85] | 2 |
| 31 | Metrics Extended (P7) | [86–87] | 2 |
| 32 | HPR Safety Benchmarks (P7) | [88–89] | 2 |
| 33 | Sobol Convergence (P7) | [90–91] | 2 |
| 34 | Heteroscedastic Modeling (P7) | [92–93] | 2 |
| 35 | OpenMC Internals (P7) | [94–95] | 2 |
| 36 | FEniCS & Structural Mech (P7) | [96–97] | 2 |
| 37 | Soft Constraints (P7) | [98–99] | 2 |
| 38 | Extended UQ & Comparison (P7) | [100–107] | 8 |
| 39 | Software Citations (P7) | [109–110] | 2 |
| | **Total** | | **110** |

### Suggested Main Text vs SI Split (post-consensus)

| Location | Refs | Count |
|----------|------|-------|
| Main text (25–35 core) | [1, 3–5, 10–13, 19✓, 20, 21, 29, 31–35, 37–40, 42, 46–48, 50, 54, 56✓, 61, 85, 109, 110] | ~30 |
| SI / Appendix | [6–9, 14–18, 24, 26, 28, 36, 41, 43✓, 44, 45, 52✓, 53, 55, 59, 60, 66, 68–79, 81–83, 86–87, 90–92, 97–99, 101–102, 105–106] | ~45 |
| Frozen / D-bucket (do NOT use) | [22⚠️, 23, 25❌, 27, 30, 57❌, 58, 62–65, 67, 75❌, 80❌, 84, 88, 91, 93❌, 94–96, 100, 103❌, 104, 107, 108❌] | ~28 |

✓ = corrected/rebuilt entry   ⚠️ = pending DOI confirmation   ❌ = deleted/frozen

### Duplicates / Conflicts to Resolve

- [80] is a 2000 reprint of [54] (McKay 1979 LHS) — **DELETE [80]**, keep [54]
- [108] was flagged as duplicate of [18] (Abdar 2021) — **DELETE [108]**
- [100] Concrete Dropout overlaps with [6] Gal 2016 — use [100] in SI only
- [93] duplicate of [92] (Nix & Weigend) — **DELETE [93]**
- [103] duplicate of [40] (Meng & Karniadakis) — **DELETE [103]**
- [64] same as unverified [22] (Ma 2021) — **CONFLICT unresolved**
- [104] same as unverified [57] (Radaideh 2020) — **CONFLICT unresolved**

### Placeholders Still Needing Fill

[23], [30], [58], [62], [63], [64], [65], [67], [93], [103], [104], [107]
— 12 slots total. **All in D-bucket (frozen)**. Do not fill until independent
DOI search conducted.

### Verification Notes (updated after GPT 4-batch + consensus)

- [x] [19] McClure 2015: **REBUILT** — title/authors/DOI corrected
- [x] [20] Stauff 2024: DOI confirmed (10.1080/00295639.2024.2375175)
- [x] [21] Miao 2025: DOI confirmed (10.1080/00295639.2025.2560170)
- [x] [25] Williams 1986: **DELETED** — no UQ content
- [x] [33] Pearce 2018: **VERIFIED** — "Brintrup" confirmed correct
- [ ] [36] Kingma 2014: prefer ICLR 2015 if journal requires
- [x] [43] Hagrman 1981: **CORRECTED** — NUREG/CR-0497 Rev. 2
- [x] [70] Gawlikowski: **UPDATE** to AIR 2023 journal version
- [ ] [72] Glorot 2010: confirm AISTATS venue
- [x] [75] OECD/NEA: **DELETED** — wrong material (lead/LBE)
- [x] [76] Popov 2000: ORNL/TM-2000/351 confirmed; title extended
- [ ] [83] Reddi 2019: originally ICLR 2018
- [ ] [84] Fernández-Godino 2016: arXiv only — D-bucket
- [x] [90] Owen 2013: **CORRECTED** — SIAM/ASA JUQ (not JASA)
- [ ] [94] Herman 2014: ANS Transactions — D-bucket
- [x] [98] Dugas: **CORRECTED** — NeurIPS 2000 (not 2009 JMLR)
