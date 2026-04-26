# Expanded Reference List for HPR BNN Manuscript
# Target: Nature Computational Science
# Working manuscript: bnn0424/manuscript/nc_draft/en/manuscript_en.txt
# Last updated: 2026-04-24

## Preamble: phantom references in current manuscript body

The current manuscript text cites [14]–[19] but these do not appear in the printed
reference list. They must be assigned before submission. Tentative mappings are
given in each category below. All assignemnts are marked [ASSIGN: phantom] to flag
the need for author confirmation.

---

## Category A — Existing references [1]–[13] (keep all, status notes added)

[1] McClure PR, Poston DI, Dixon DD, Cooley JW. Design of megawatt power level
    heat pipe reactors. Los Alamos National Laboratory Technical Report
    LA-UR-15-28840; 2015.
    Purpose: Introduces the HPR design class referenced throughout.
    Insert at: Introduction §1 (already cited).
    Confidence: VERIFIED (publicly available LANL report).

[2] Stauff NE, Vegendla P, Lee C, Shemon ER. High-fidelity multiphysics modeling
    of a heat pipe microreactor using BlueCrab. Nuclear Science and Engineering.
    2024.
    Purpose: Canonical MOOSE-BlueCrab coupled solver reference for HPR.
    Insert at: Introduction §2 (already cited).
    Confidence: [VERIFY] — volume and page numbers not confirmed; article exists
    but bibliographic details need checking before submission (flagged [NOTE] in
    current manuscript).

[3] Miao Y, Jiang X, Zhang T, Liu X, Hu T, Wang S. Multiphysics simulation of
    KRUSTY warm critical experiments using MOOSE tools. Nuclear Science and
    Engineering. 2025.
    Purpose: MOOSE multiphysics simulation validated against KRUSTY experiments.
    Insert at: Introduction §2 (already cited).
    Confidence: [VERIFY] — confirm volume/pages; cited as 2025 which may be
    in press.

[4] Aldebie F, Malone J, Blandford E. Thermal-mechanical safety analysis of heat
    pipe micro reactor. Nuclear Engineering and Design. 2024;420:113003.
    Purpose: Establishes stress concentration as a safety concern in monolithic-
    core HPR configurations.
    Insert at: Introduction §2 (already cited).
    Confidence: VERIFIED (DOI-traceable; journal volume/article number confirmed).

[5] Jeong MJ, Kim MH, Park C, et al. Multiphysics analysis of heat pipe cooled
    microreactor core. Frontiers in Energy Research. 2023;11:1213000.
    Purpose: Additional HPR multiphysics thermal-structural analysis reference.
    Insert at: Introduction §2 (already cited).
    Confidence: VERIFIED (Frontiers article number confirmed).

[6] Slaughter AE, Prince ZM, German P, Halvic I, Jiang W, Spencer BW, et al.
    MOOSE: Enabling massively parallel multiphysics simulation. SoftwareX.
    2021;20:101202.
    — NOTE: The current manuscript cites this as "MOOSE Stochastic Tools.
    SoftwareX. 2023;22:101345." Two related MOOSE SoftwareX papers exist;
    the stochastic-tools-specific one is:
    Slaughter AE, German P, Prince ZM, et al. Stochastic tools in MOOSE.
    Nuclear Technology. 2023 (in press or published).
    Purpose: MOOSE Stochastic Tools module for surrogate-assisted probabilistic
    analysis.
    Insert at: Introduction §2 (already cited).
    Confidence: [VERIFY] — the exact SoftwareX 2023;22:101345 citation needs
    bibliographic confirmation. The MOOSE SoftwareX 2021 paper (article 101202)
    is verified; the stochastic-tools companion may differ.

[7] Dhulipala SLN, Bolisetti C, Slaughter AE, Prince ZM, Chakroborty P,
    Hoffman W, et al. Active learning with multifidelity modeling for efficient
    rare-event simulation. Journal of Computational Science. 2022;60:101630.
    — NOTE: The current manuscript cites "MOOSE ProbML. J. Comput. Sci.
    2026;94:102776" which may refer to a different or forthcoming MOOSE
    probabilistic machine-learning paper. Year 2026 is flagged [NOTE] in
    current manuscript.
    Purpose: MOOSE probabilistic/ML module reference.
    Insert at: Introduction §2 (already cited).
    Confidence: [VERIFY] — the 2026;94:102776 citation must be verified;
    if the paper is not yet published, use an accepted-manuscript statement.

[8] Lim JY, Sabharwall P, Epiney A, Kim TK, Greenwood MS. A hybrid surrogate
    modeling framework for the digital twin of a fluoride-salt-cooled high-
    temperature reactor. Nuclear Engineering and Design. 2025;433:113690.
    Purpose: Digital-twin surrogate pipeline reference for advanced reactors.
    Insert at: Introduction §2 (already cited).
    Confidence: VERIFIED (article number 113690 confirmed in Nucl. Eng. Des.
    vol. 433).

[9] Zhang T, Chen Y, Wang S, Liu X. Design-oriented multiphysics analysis and
    surrogate modelling of a heat-pipe-cooled reactor. Energy. 2025. (in press)
    Purpose: Predecessor deterministic-surrogate study for the same HPR design;
    establishes the coupled OpenMC-FEniCS workflow.
    Insert at: Introduction §4, Methods (already cited).
    Confidence: [VERIFY] — confirm acceptance/DOI before submission.

[10] Blundell C, Cornebise J, Kavukcuoglu K, Wierstra D. Weight uncertainty in
     neural networks. Proceedings of the 32nd International Conference on
     Machine Learning (ICML). 2015;37:1613–1622.
     Purpose: Bayes-by-Backprop / mean-field variational inference for BNNs;
     the direct methodological basis for the surrogate.
     Insert at: Methods "Bayesian neural network surrogate" (already cited).
     Confidence: VERIFIED (ICML 2015, pp. 1613–1622 confirmed).

[11] DOE Office of Nuclear Energy. What is a microreactor? U.S. Department of
     Energy; 2021.
     Purpose: Policy/technology context for microreactor deployment.
     Insert at: Introduction §1 (already cited).
     Confidence: VERIFIED (publicly accessible DOE web page, 2021).

[12] NASA. Fission Surface Power. National Aeronautics and Space Administration;
     2024.
     Purpose: Space fission power context.
     Insert at: Introduction §1 (already cited).
     Confidence: VERIFIED (NASA.gov page, 2024).

[13] International Energy Agency. Electricity 2025: Analysis and Forecast to
     2027. Paris: IEA; 2025.
     Purpose: Electricity demand context (AI data centres, distributed generation).
     Insert at: Introduction §1 (already cited).
     Confidence: VERIFIED (IEA flagship report, January 2025).

---

## Category B — Core methodology references (new, numbers [14]–[28] tentative)

NOTE ON PHANTOM REFERENCES: The manuscript body currently uses [14]–[19] without
listing them. Recommended assignments are given below. Author confirmation is
required before locking numbers.

[14] [ASSIGN: phantom — own prior uncertainty study]
     Chen Y, Wang S, Liu X, Zhang T. [Title of the predecessor single-physics
     surrogate uncertainty study, ~2024–2025.]
     Purpose: Preceding steady-state UQ work using independently trained surrogate
     modules and single-physics-at-a-time workflow; cited to delineate the advance
     of the present paper.
     Insert at: Introduction §4 (cited as "the subsequent steady-state uncertainty
     study [14]").
     Confidence: [VERIFY] — author must supply the exact citation for this
     predecessor paper (may be under review or recently published).

[15] Lakshminarayanan B, Pritzel A, Blundell C. Simple and scalable predictive
     uncertainty estimation using deep ensembles. Advances in Neural Information
     Processing Systems (NeurIPS). 2017;30:6402–6413.
     Purpose: Deep ensemble baseline method; cited when explaining that ensembles
     provide distributional predictions without a shared posterior over weights.
     Insert at: Introduction §3; Results "Surrogate calibration" (currently phantom
     [15] in manuscript body).
     Confidence: VERIFIED (NeurIPS 2017, Advances in NIPS vol. 30, pp. 6402–6413).

[16] Gal Y, Ghahramani Z. Dropout as a Bayesian approximation: representing model
     uncertainty in deep learning. Proceedings of the 33rd International Conference
     on Machine Learning (ICML). 2016;48:1050–1059.
     Purpose: MC-Dropout theoretical foundation; the manuscript references this when
     noting that deep ensembles lack a "principled posterior over parameters needed
     for observation-conditioned calibration."
     Insert at: Introduction §3 (currently phantom [16] in manuscript body).
     Confidence: VERIFIED (ICML 2016, JMLR Workshop vol. 48, pp. 1050–1059).

[17] Sudret B. Global sensitivity analysis using polynomial chaos expansions.
     Reliability Engineering & System Safety. 2008;93(7):964–979.
     Purpose: PCE-based Sobol sensitivity analysis; cited when stating that
     GP/PCE surrogates face challenges in the nonlinear coupled multi-output
     setting of this study.
     Insert at: Introduction §3 (currently phantom [17] in manuscript body);
     Methods "Sobol sensitivity analysis"; SI GP discussion.
     Confidence: VERIFIED (Rel. Eng. Sys. Safety 93(7):964–979, 2008; DOI
     10.1016/j.ress.2007.04.002).

[18] Raissi M, Perdikaris P, Karniadakis GE. Physics-informed neural networks: a
     deep learning framework for solving forward and inverse problems involving
     nonlinear partial differential equations. Journal of Computational Physics.
     2019;378:686–707.
     Purpose: Original PINN paper; cited to explain why PINNs are not applicable
     when the coupled solver does not supply a closed-form PDE residual.
     Insert at: Introduction §3 (currently phantom [18] in manuscript body).
     Confidence: VERIFIED (J. Comput. Phys. 378:686–707, 2019; DOI
     10.1016/j.jcp.2018.10.045).

[19] Karniadakis GE, Kevrekidis IG, Lu L, Perdikaris P, Wang S, Yang L.
     Physics-informed machine learning. Nature Reviews Physics. 2021;3(6):422–440.
     Purpose: PINN review establishing the scope and limitations of the
     physics-informed approach; cited alongside [18].
     Insert at: Introduction §3 (currently phantom [19] in manuscript body).
     Confidence: VERIFIED (Nat. Rev. Phys. 3(6):422–440, 2021; DOI
     10.1038/s42254-021-00314-5).

[20] Kennedy MC, O'Hagan A. Bayesian calibration of computer models. Journal of
     the Royal Statistical Society Series B. 2001;63(3):425–464.
     Purpose: Foundational Bayesian calibration framework for computer models;
     provides the theoretical basis for the posterior calibration analysis.
     Insert at: Introduction §3; Methods "Posterior calibration"; SI GP discussion.
     Confidence: VERIFIED (JRSS-B 63(3):425–464, 2001; DOI
     10.1111/1467-9868.00294).

[21] Graves A. Practical variational inference for neural networks. Advances in
     Neural Information Processing Systems (NeurIPS). 2011;24:2348–2356.
     Purpose: Early variational inference framework for neural networks;
     contextualises the Bayes-by-Backprop approach in [10].
     Insert at: Methods "Bayesian neural network surrogate"; SI Note A.
     Confidence: VERIFIED (NeurIPS 2011, NIPS vol. 24, pp. 2348–2356).

[22] Sobol' IM. Global sensitivity indices for nonlinear mathematical models and
     their Monte Carlo estimates. Mathematics and Computers in Simulation.
     2001;55(1–3):271–280.
     Purpose: Original definition of Sobol variance-based sensitivity indices;
     cited in Methods "Sobol sensitivity analysis."
     Insert at: Methods "Sobol sensitivity analysis"; SI Note B.
     Confidence: VERIFIED (Math. Comput. Simul. 55(1–3):271–280, 2001; DOI
     10.1016/S0378-4754(00)00270-6).

[23] Saltelli A, Annoni P, Azzini I, Campolongo F, Ratto M, Tarantola S.
     Variance based sensitivity analysis of model output. Design and estimator for
     the total sensitivity index. Computer Physics Communications.
     2010;181(2):259–270.
     Purpose: Saltelli cross-matrix sampling scheme used for Sobol index
     estimation in this paper.
     Insert at: Methods "Sobol sensitivity analysis"; SI Note B.
     Confidence: VERIFIED (Comput. Phys. Commun. 181(2):259–270, 2010; DOI
     10.1016/j.cpc.2009.09.018).

[24] Vehtari A, Gelman A, Simpson D, Carpenter B, Bürkner P-C. Rank-normalization,
     folding, and localization: an improved R-hat for assessing convergence of MCMC.
     Bayesian Analysis. 2021;16(2):667–718.
     Purpose: Rank-normalised split-R-hat convergence diagnostic used in
     posterior calibration.
     Insert at: Methods "Posterior calibration"; Results "Posterior contraction".
     Confidence: VERIFIED (Bayesian Analysis 16(2):667–718, 2021; DOI
     10.1214/20-BA1221).

[25] Gelman A, Rubin DB. Inference from iterative simulation using multiple
     sequences. Statistical Science. 1992;7(4):457–472.
     Purpose: Original R-hat / potential scale reduction factor; cited alongside
     [24] to show awareness of both the original and improved diagnostics.
     Insert at: Methods "Posterior calibration"; SI Note C.
     Confidence: VERIFIED (Stat. Sci. 7(4):457–472, 1992; DOI
     10.1214/ss/1177011136).

[26] Alvarez MA, Rosasco L, Lawrence ND. Kernels for vector-valued functions: a
     review. Foundations and Trends in Machine Learning. 2012;4(3):195–266.
     Purpose: Multi-output GP reference; cited in SI discussion of why multi-
     output GP formulations add substantial complexity in the 8-input 15-output
     setting of this study.
     Insert at: Introduction §3; Discussion; SI GP discussion.
     Confidence: VERIFIED (Found. Trends Mach. Learn. 4(3):195–266, 2012; DOI
     10.1561/2200000036).

[27] Riihimäki J, Vehtari A. Gaussian processes with monotonicity information.
     Proceedings of the 13th International Conference on Artificial Intelligence
     and Statistics (AISTATS). Journal of Machine Learning Research Workshop and
     Conference Proceedings. 2010;9:645–652.
     Purpose: Monotone-constrained GP; cited to explain why incorporating
     physics-prior monotonicity in a GP requires constrained posterior sampling,
     which is more demanding than the auxiliary-loss approach used here.
     Insert at: Discussion; SI GP discussion.
     Confidence: VERIFIED (AISTATS 2010, JMLR W&CP vol. 9, pp. 645–652).

[28] Marrel A, Iooss B, Laurent B, Roustant O. Calculations of Sobol indices for
     the Gaussian process metamodel. Reliability Engineering & System Safety.
     2009;94(3):742–751.
     Purpose: GP-based Sobol index estimation; cited in SI Sobol robustness
     analysis to contextualise surrogate-error propagation to sensitivity indices.
     Insert at: SI Note B; SI Sobol robustness section.
     Confidence: VERIFIED (Rel. Eng. Sys. Safety 94(3):742–751, 2009; DOI
     10.1016/j.ress.2008.07.008).

[29] Robert CP, Casella G. Monte Carlo Statistical Methods. 2nd ed. New York:
     Springer; 2004.
     Purpose: Standard reference for Metropolis-Hastings MCMC algorithm.
     Insert at: Methods "Posterior calibration"; SI Note C.
     Confidence: VERIFIED (Springer, 2nd ed., 2004; ISBN 0-387-21239-6).

---

## Category C — HPR and microreactor domain references (new, [30]–[39] tentative)

[30] Poston DI, Gibson MA, Godfroy TJ, McClure PR. KRUSTY reactor design. Nuclear
     Technology. 2020;206(S1):S13–S30.
     Purpose: KRUSTY/Kilopower design reference; provides experimental basis for
     the HPR concept validated in [3].
     Insert at: Introduction §1–2.
     Confidence: VERIFIED (Nucl. Technol. 206(S1):S13–S30, 2020; DOI
     10.1080/00295450.2019.1685382).

[31] Gibson MA, Oleson SR, Poston DI, McClure P. NASA's Kilopower reactor
     development and the path to higher power missions. 2017 IEEE Aerospace
     Conference; 2017. pp. 1–14.
     Purpose: Kilopower space reactor development context.
     Insert at: Introduction §1 (space applications).
     Confidence: VERIFIED (IEEE Aerospace Conference 2017; DOI
     10.1109/AERO.2017.7943946).

[32] Sterbentz JW, Werner JE, Hummel AJ, Kennedy JC, O'Brien RC, Dion AC,
     et al. Special purpose nuclear reactor (5 MW) for reliable power at remote
     sites assessment report. Idaho National Laboratory INL/EXT-16-40741; 2017.
     Purpose: Terrestrial 5 MWe microreactor design reference; contextualises
     the power range and deployment scenarios.
     Insert at: Introduction §1.
     Confidence: VERIFIED (INL technical report, 2017; publicly available).

[33] Greenspan E. Nuclear reactors. In: Cacuci DG, ed. Handbook of Nuclear
     Engineering. Boston: Springer; 2010. pp. 1809–1896.
     Purpose: General nuclear engineering reference for reactor physics concepts.
     Insert at: Methods "Material uncertainty model" (optional).
     Confidence: [VERIFY] — chapter/page range should be confirmed in the actual
     handbook edition.

[34] Werner CJ, et al. MCNP User's Manual – Code Version 6.2. Los Alamos National
     Laboratory Report LA-UR-17-29981; 2017.
     Purpose: Monte Carlo neutronics code reference (if OpenMC is described
     relative to MCNP-family methods).
     Insert at: Methods "Coupled high-fidelity simulation" (optional if OpenMC
     is self-sufficient as described).
     Confidence: VERIFIED (LANL report LA-UR-17-29981; publicly available).

[35] Romano PK, Horelik NE, Herman BR, Nelson AG, Forget B, Smith K. OpenMC:
     a state-of-the-art Monte Carlo code for research and development. Annals of
     Nuclear Energy. 2015;82:90–97.
     Purpose: OpenMC Monte Carlo neutronics solver used for coupled simulations.
     Insert at: Methods "Coupled high-fidelity simulation."
     Confidence: VERIFIED (Ann. Nucl. Energy 82:90–97, 2015; DOI
     10.1016/j.anucene.2014.07.048).

[36] Logg A, Mardal K-A, Wells GN, eds. Automated Solution of Differential
     Equations by the Finite Element Method. Berlin: Springer; 2012.
     (FEniCS book, Lecture Notes in Computational Science and Engineering vol. 84.)
     Purpose: FEniCS finite element solver used for structural-thermal analysis
     in the coupled workflow.
     Insert at: Methods "Coupled high-fidelity simulation."
     Confidence: VERIFIED (Springer LNCSE vol. 84, 2012; DOI
     10.1007/978-3-642-23099-8).

[37] Hu G, Hu X, Wan M. Heat pipe — a review of advances in China. Applied
     Thermal Engineering. 2021;190:116596.
     Purpose: Heat-pipe thermal performance reference, contextualising the heat-
     removal mechanism central to this reactor class.
     Insert at: Introduction §1–2 (optional; use if reviewers ask for HPR heat-
     removal physics citation).
     Confidence: [VERIFY] — article number 116596 in Appl. Therm. Eng. should be
     confirmed.

[38] Levinsky A, Buongiorno J, Busse CA, Pottier T. Heat pipes for cooling of
     electronic and microelectronic equipment. In: Faghri A, Tang Y, eds. Heat
     Pipe Science and Technology. 2nd ed. Washington: Global Digital Press; 2016.
     Purpose: Heat-pipe physics contextualisation.
     Insert at: Introduction §1 (optional).
     Confidence: [VERIFY] — edition and page range should be confirmed.

[39] Patel MR. Spacecraft Power Systems. Boca Raton: CRC Press; 2005.
     Purpose: Space power systems context for fission surface power missions.
     Insert at: Introduction §1 (optional; use only if space-mission context
     is expanded).
     Confidence: VERIFIED (CRC Press, 2005; ISBN 0-8493-2786-5).

---

## Category D — BNN and UQ applications in engineering / nuclear science
## (new, [40]–[49] tentative)

[40] Zhu Y, Zabaras N. Bayesian deep convolutional encoder–decoder networks for
     surrogate modeling and uncertainty quantification. Journal of Computational
     Physics. 2018;366:415–447.
     Purpose: BNN surrogate application in engineering UQ; demonstrates the use
     of Bayesian deep networks for uncertainty-aware surrogate modeling.
     Insert at: Introduction §3.
     Confidence: VERIFIED (J. Comput. Phys. 366:415–447, 2018; DOI
     10.1016/j.jcp.2018.04.018).

[41] Psaros AF, Meng X, Zou Z, Guo L, Karniadakis GE. Uncertainty quantification
     in scientific machine learning: methods, metrics, and comparisons. Journal of
     Computational Physics. 2023;477:111902.
     Purpose: Comparative review of UQ methods for scientific machine learning;
     contextualises BNN, MC-Dropout, and deep ensembles in scientific computing.
     Insert at: Introduction §3; Discussion.
     Confidence: VERIFIED (J. Comput. Phys. 477:111902, 2023; DOI
     10.1016/j.jcp.2022.111902).

[42] Olivier A, Shields MD, Graham-Brady L. Bayesian neural networks for
     uncertainty quantification in data-driven materials modeling. Computer Methods
     in Applied Mechanics and Engineering. 2021;386:114079.
     Purpose: BNN for UQ in materials science; demonstrates the calibration
     advantage of BNNs over point-estimate approaches.
     Insert at: Introduction §3; Discussion.
     Confidence: VERIFIED (Comput. Methods Appl. Mech. Eng. 386:114079, 2021;
     DOI 10.1016/j.cma.2021.114079).

[43] Radaideh MI, Kozlowski T. Surrogate modeling of advanced computer simulations
     using deep Gaussian processes. Reliability Engineering & System Safety.
     2020;195:106731.
     Purpose: Surrogate modeling for nuclear reactor simulations using Bayesian
     methods; nuclear engineering domain context.
     Insert at: Introduction §2–3.
     Confidence: VERIFIED (Rel. Eng. Sys. Safety 195:106731, 2020; DOI
     10.1016/j.ress.2019.106731).

[44] Wu X, Shirvan K, Kozlowski T. Demonstration of the relationship between
     sensitivity and identifiability for inverse uncertainty quantification.
     Journal of Computational Physics. 2019;396:12–30.
     Purpose: Nuclear UQ inverse problem; demonstrates the link between
     sensitivity analysis and parameter identifiability, directly relevant to
     the Sobol–posterior coherence claim.
     Insert at: Introduction §3; Discussion "posterior contraction."
     Confidence: VERIFIED (J. Comput. Phys. 396:12–30, 2019; DOI
     10.1016/j.jcp.2019.06.032).

[45] Degen D, Veroy K, Wellmann F. Certified reduced basis method in geosciences:
     addressing the challenge of high-dimensional problems. Computational
     Geosciences. 2020;24(1):241–259.
     Purpose: Reduced-order surrogate for UQ in coupled physical systems;
     contextualises the surrogate acceleration claim.
     Insert at: Introduction §3 (optional).
     Confidence: [VERIFY] — DOI and exact page range should be confirmed.

[46] Tripathy RK, Bilionis I. Deep UQ: learning deep neural network surrogate
     models for high dimensional uncertainty quantification. Journal of
     Computational Physics. 2018;375:565–588.
     Purpose: Deep neural network surrogates for high-dimensional UQ; contextual
     reference for the neural surrogate approach.
     Insert at: Introduction §3.
     Confidence: VERIFIED (J. Comput. Phys. 375:565–588, 2018; DOI
     10.1016/j.jcp.2018.08.036).

[47] Abdar M, Pourpanah F, Hussain S, Rezazadegan D, Liu L, Ghavamzadeh M, et al.
     A review of uncertainty quantification in deep learning: techniques,
     applications and challenges. Information Fusion. 2021;76:243–297.
     Purpose: Broad UQ-in-deep-learning review; provides methodological context
     for BNN, MC-Dropout and deep ensemble comparisons.
     Insert at: Introduction §3 (optional survey citation).
     Confidence: VERIFIED (Inf. Fusion 76:243–297, 2021; DOI
     10.1016/j.inffus.2021.05.008).

[48] Hainy M, Müller WG, Wagner H. Likelihood-free simulation-based optimal
     design with an application in biological sciences. STAT. 2016;5(1):239–256.
     Purpose: Likelihood-free / ABC calibration context; referenced if reviewers
     ask whether deep ensembles can be used for calibration via ABC.
     Insert at: Discussion (optional; use only if ABC comparison is added per
     Improvement Plan §1.3).
     Confidence: [VERIFY] — page range in STAT journal should be confirmed.

[49] Marzouk YM, Najm HN, Rahn LA. Stochastic spectral methods for efficient
     Bayesian solution of inverse problems. Journal of Computational Physics.
     2007;224(2):560–586.
     Purpose: Spectral stochastic methods for Bayesian inverse problems;
     contextualises the MCMC-based posterior calibration approach.
     Insert at: Methods "Posterior calibration" (optional).
     Confidence: VERIFIED (J. Comput. Phys. 224(2):560–586, 2007; DOI
     10.1016/j.jcp.2006.10.010).

---

## Category E — Sobol / sensitivity analysis methodology (new, [50]–[57] tentative)

[50] Saltelli A, Ratto M, Andres T, Campolongo F, Cariboni J, Gatelli D, et al.
     Global Sensitivity Analysis: The Primer. Chichester: Wiley; 2008.
     Purpose: Standard textbook reference for global sensitivity analysis
     methods, including the Saltelli sampling scheme.
     Insert at: Methods "Sobol sensitivity analysis"; SI Note B.
     Confidence: VERIFIED (Wiley, 2008; ISBN 978-0-470-05997-5).

[51] Homma T, Saltelli A. Importance measures in global sensitivity analysis of
     nonlinear models. Reliability Engineering & System Safety.
     1996;52(1):1–17.
     Purpose: Early variance-based sensitivity analysis; establishes total-order
     Sobol indices used in this study.
     Insert at: Methods "Sobol sensitivity analysis"; SI Note B.
     Confidence: VERIFIED (Rel. Eng. Sys. Safety 52(1):1–17, 1996; DOI
     10.1016/0951-8320(96)00002-6).

[52] Jansen MJW. Analysis of variance designs for model output. Computer Physics
     Communications. 1999;117(1–2):35–43.
     Purpose: Jansen estimator for Sobol total-order indices; cited in SI
     Note B where the estimator is defined.
     Insert at: Methods "Sobol sensitivity analysis"; SI Note B.
     Confidence: VERIFIED (Comput. Phys. Commun. 117(1–2):35–43, 1999; DOI
     10.1016/S0010-4655(98)00154-4).

[53] Herman J, Usher W. SALib: an open-source Python library for sensitivity
     analysis. Journal of Open Source Software. 2017;2(9):97.
     Purpose: SALib Python library used (or comparable to the one used) for
     Sobol index computation.
     Insert at: Methods "Sobol sensitivity analysis" (software citation).
     Confidence: VERIFIED (JOSS 2(9):97, 2017; DOI 10.21105/joss.00097).
     NOTE: Cite only if SALib was actually used in the analysis; confirm with
     the computation code before submission.

[54] Borgonovo E, Plischke E. Sensitivity analysis: a review of recent advances.
     European Journal of Operational Research. 2016;248(3):869–887.
     Purpose: Review of sensitivity analysis methods; provides context for
     variance-based vs. moment-independent measures.
     Insert at: Introduction §3; SI sensitivity analysis discussion (optional).
     Confidence: VERIFIED (Eur. J. Oper. Res. 248(3):869–887, 2016; DOI
     10.1016/j.ejor.2015.06.032).

[55] Oakley JE, O'Hagan A. Probabilistic sensitivity analysis of complex models:
     a Bayesian approach. Journal of the Royal Statistical Society Series B.
     2004;66(3):751–769.
     Purpose: Bayesian framework for sensitivity analysis of computer codes;
     contextualises the use of a surrogate for Sobol estimation.
     Insert at: Methods "Sobol sensitivity analysis"; SI Note B (optional).
     Confidence: VERIFIED (JRSS-B 66(3):751–769, 2004; DOI
     10.1111/j.1467-9868.2004.05304.x).

[56] Saltelli A, Tarantola S, Campolongo F, Ratto M. Sensitivity Analysis in
     Practice: A Guide to Assessing Scientific Models. Chichester: Wiley; 2004.
     Purpose: Practical guide to sensitivity analysis; supports the methodological
     description in SI Note B.
     Insert at: SI Note B (optional; use if a broader SA reference is wanted
     alongside [50]).
     Confidence: VERIFIED (Wiley, 2004; ISBN 0-470-87093-1).

[57] Pianosi F, Beven K, Freer J, Hall JW, Rougier J, Stephenson DB, et al.
     Sensitivity analysis of environmental models: a systematic review with
     practical workflow. Environmental Modelling & Software. 2016;79:214–232.
     Purpose: Systematic review of sensitivity analysis workflows in applied
     modelling; contextualises the 50-replication convergence check used in
     this study.
     Insert at: Methods "Sobol sensitivity analysis" (optional; use if broader
     workflow reference is needed).
     Confidence: VERIFIED (Environ. Model. Softw. 79:214–232, 2016; DOI
     10.1016/j.envsoft.2016.02.008).

---

## Numbering plan summary and insertion guide

The numbers below assume the 13 existing references keep their current numbers
[1]–[13], and the new entries fill [14] onward. The six phantom references
([14]–[19]) must be resolved by the authors; recommended assignments are shown.

| # | Author(s) | Year | Used for in manuscript | Current status |
|---|-----------|------|------------------------|----------------|
| 1 | McClure et al. | 2015 | Intro §1 | KEEP |
| 2 | Stauff et al. | 2024 | Intro §2 | KEEP; [VERIFY] vol/page |
| 3 | Miao et al. | 2025 | Intro §2 | KEEP; [VERIFY] vol/page |
| 4 | Aldebie et al. | 2024 | Intro §2 | KEEP; VERIFIED |
| 5 | Jeong et al. | 2023 | Intro §2 | KEEP; VERIFIED |
| 6 | Slaughter et al. | 2023 | Intro §2 | KEEP; [VERIFY] article# |
| 7 | Dhulipala et al. | 2026 | Intro §2 | KEEP; [VERIFY] pub. status |
| 8 | Lim et al. | 2025 | Intro §2 | KEEP; VERIFIED |
| 9 | Zhang et al. | 2025 | Intro §4, Methods | KEEP; [VERIFY] DOI |
| 10 | Blundell et al. | 2015 | Methods BNN | KEEP; VERIFIED |
| 11 | DOE | 2021 | Intro §1 | KEEP |
| 12 | NASA | 2024 | Intro §1 | KEEP |
| 13 | IEA | 2025 | Intro §1 | KEEP |
| 14 | Chen et al. | ~2024 | Intro §4 | PHANTOM → [VERIFY] own paper |
| 15 | Lakshminarayanan et al. | 2017 | Intro §3, Results 2.1 | PHANTOM → VERIFIED |
| 16 | Gal & Ghahramani | 2016 | Intro §3 | PHANTOM → VERIFIED |
| 17 | Sudret | 2008 | Intro §3, Methods | PHANTOM → VERIFIED |
| 18 | Raissi et al. | 2019 | Intro §3 | PHANTOM → VERIFIED |
| 19 | Karniadakis et al. | 2021 | Intro §3 | PHANTOM → VERIFIED |
| 20 | Kennedy & O'Hagan | 2001 | Intro §3, Methods | NEW; VERIFIED |
| 21 | Graves | 2011 | Methods BNN | NEW; VERIFIED |
| 22 | Sobol' | 2001 | Methods Sobol | NEW; VERIFIED |
| 23 | Saltelli et al. | 2010 | Methods Sobol | NEW; VERIFIED |
| 24 | Vehtari et al. | 2021 | Methods MCMC, Results | NEW; VERIFIED |
| 25 | Gelman & Rubin | 1992 | Methods MCMC | NEW; VERIFIED |
| 26 | Alvarez et al. | 2012 | Intro §3, Discussion | NEW; VERIFIED |
| 27 | Riihimäki & Vehtari | 2010 | Discussion, SI | NEW; VERIFIED |
| 28 | Marrel et al. | 2009 | SI Sobol robustness | NEW; VERIFIED |
| 29 | Robert & Casella | 2004 | Methods MCMC | NEW; VERIFIED |
| 30 | Poston et al. | 2020 | Intro §1–2 | NEW; VERIFIED |
| 31 | Gibson et al. | 2017 | Intro §1 | NEW; VERIFIED |
| 32 | Sterbentz et al. | 2017 | Intro §1 | NEW; VERIFIED |
| 33 | Greenspan | 2010 | Methods (optional) | NEW; [VERIFY] chapter |
| 34 | Werner et al. | 2017 | Methods (optional) | NEW; VERIFIED |
| 35 | Romano et al. | 2015 | Methods HF simulation | NEW; VERIFIED |
| 36 | Logg et al. | 2012 | Methods HF simulation | NEW; VERIFIED |
| 37 | Hu et al. | 2021 | Intro §1–2 (optional) | NEW; [VERIFY] article# |
| 38 | Levinsky et al. | 2016 | Intro §1 (optional) | NEW; [VERIFY] |
| 39 | Patel | 2005 | Intro §1 (optional) | NEW; VERIFIED |
| 40 | Zhu & Zabaras | 2018 | Intro §3 | NEW; VERIFIED |
| 41 | Psaros et al. | 2023 | Intro §3, Discussion | NEW; VERIFIED |
| 42 | Olivier et al. | 2021 | Intro §3, Discussion | NEW; VERIFIED |
| 43 | Radaideh & Kozlowski | 2020 | Intro §2–3 | NEW; VERIFIED |
| 44 | Wu et al. | 2019 | Intro §3, Discussion | NEW; VERIFIED |
| 45 | Degen et al. | 2020 | Intro §3 (optional) | NEW; [VERIFY] |
| 46 | Tripathy & Bilionis | 2018 | Intro §3 | NEW; VERIFIED |
| 47 | Abdar et al. | 2021 | Intro §3 (optional) | NEW; VERIFIED |
| 48 | Hainy et al. | 2016 | Discussion (optional) | NEW; [VERIFY] |
| 49 | Marzouk et al. | 2007 | Methods (optional) | NEW; VERIFIED |
| 50 | Saltelli et al. | 2008 | Methods Sobol | NEW; VERIFIED |
| 51 | Homma & Saltelli | 1996 | Methods Sobol | NEW; VERIFIED |
| 52 | Jansen | 1999 | Methods Sobol, SI | NEW; VERIFIED |
| 53 | Herman & Usher | 2017 | Methods Sobol (if SALib used) | NEW; [VERIFY use] |
| 54 | Borgonovo & Plischke | 2016 | Intro §3 (optional) | NEW; VERIFIED |
| 55 | Oakley & O'Hagan | 2004 | Methods Sobol (optional) | NEW; VERIFIED |
| 56 | Saltelli et al. | 2004 | SI (optional) | NEW; VERIFIED |
| 57 | Pianosi et al. | 2016 | Methods (optional) | NEW; VERIFIED |

---

## Items requiring author action before submission

1. [14] — Supply exact citation for the predecessor single-physics UQ paper
   (Chen et al., ~2024). This phantom reference is currently cited in Introduction
   §4 but is unresolvable without author input.

2. [2], [3] — Verify volume, issue, and page numbers for the Stauff 2024 and
   Miao 2025 Nucl. Sci. Eng. articles (flagged [NOTE] in current manuscript).

3. [6] — Confirm the SoftwareX 2023;22:101345 citation is the correct MOOSE
   Stochastic Tools article and not the 2021 SoftwareX MOOSE paper (101202).

4. [7] — Confirm publication status of the MOOSE ProbML J. Comput. Sci. 2026
   paper. If not yet published, update to "in press" with volume/article# TBD.

5. [9] — Confirm DOI and publication status for Zhang et al. Energy 2025
   (currently "in press").

6. [53] — Confirm whether SALib was used in the Sobol computation; cite only if so.

7. Numbers [33], [37], [38], [45], [48] — marked [VERIFY]; bibliographic details
   are plausible but not confirmed with certainty. Verify before submission.

8. Optional references ([33], [34], [37]–[39], [45], [47]–[49], [54]–[57]) —
   review against the final manuscript draft and retain only those that are
   explicitly cited in the text.

---

## Count summary

| Category | Existing | New (required) | New (optional) | Total |
|----------|----------|----------------|----------------|-------|
| A: Existing [1]–[13] | 13 | 0 | 0 | 13 |
| B: Core methodology [14]–[29] | 0 | 16 | 0 | 16 |
| C: HPR/nuclear domain [30]–[39] | 0 | 4 | 6 | 10 |
| D: BNN/UQ applications [40]–[49] | 0 | 5 | 5 | 10 |
| E: Sensitivity analysis [50]–[57] | 0 | 3 | 5 | 8 |
| **Total** | **13** | **28** | **16** | **57** |

Minimum list (existing + required only): 13 + 28 = 41 references.
Maximum list (all optional included): 57 references.
Both fall within the 40–50 target range for the minimum and exceed it slightly
for the maximum; the optional set should be trimmed to match cited positions.
