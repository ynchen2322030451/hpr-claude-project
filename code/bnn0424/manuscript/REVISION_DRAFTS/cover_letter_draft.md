# Cover Letter Draft — Nature Computational Science

> Draft date: 2026-04-25. To be finalized by corresponding author.

---

Dear Editors,

We submit for your consideration a manuscript entitled "A framework for
uncertainty analysis reveals coupling effects in multiphysics reactor
models" [TITLE MAY CHANGE — see 2.1.1].

**Motivation.** Coupled multiphysics reactor simulations require forward
uncertainty propagation, global sensitivity analysis and parameter
calibration -- three tasks conventionally performed with separately
constructed surrogate models. This separation offers no guarantee that
the sensitivity rankings inferred by one model are consistent with the
posterior contraction observed by another.

**Core contribution.** We show that a single Bayesian neural network
(BNN) posterior predictive distribution can serve as a unified
probabilistic layer for all three analyses without retraining or
recalibration. Applied to a heat-pipe-cooled microreactor simulated by
coupled OpenMC-FEniCS, the framework reveals that iterative
multi-physics feedback damps stress variability by ~30%, that stress
and k_eff are governed by distinct parameter pathways (Young's modulus
intercept vs thermal-expansion coefficient), and that posterior
calibration contracts most strongly along the same Sobol-dominant
directions -- a coherence that emerges structurally from the shared
posterior.

**Why NCS.** The manuscript addresses a methodological gap at the
intersection of computational science and nuclear engineering:
demonstrating how a shared Bayesian posterior can unify uncertainty
quantification tasks that the community currently handles with separate
models. The approach is domain-general -- any coupled simulation
workflow that produces input-output training data can be substituted --
but the nuclear engineering application provides a concrete safety-
relevant demonstration. Each surrogate evaluation is ~10^5 times faster
than a coupled high-fidelity solve, making the full probabilistic
workflow feasible on a single workstation.

**Reproducibility.** The coupled simulation dataset, fixed train/test
split, trained model checkpoints and analysis code will be released
upon acceptance at [repository URL].

We confirm that this work has not been published elsewhere and is not
under consideration at another journal. All authors have approved the
manuscript for submission.

Sincerely,

Tengfei Zhang (corresponding author)
School of Nuclear Science and Engineering
Shanghai Jiao Tong University
zhangtengfei@sjtu.edu.cn
