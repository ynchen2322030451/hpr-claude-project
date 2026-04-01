---
name: forward-uq
description: Run or audit forward uncertainty propagation, threshold risk export, and CVR summaries for the HPR surrogate project.
---

Use this skill when the user asks to run, check, summarize, or revise forward-UQ analysis.

Workflow:
1. Read `paper_experiment_config.py` first.
2. Verify whether the task is:
   - rerun experiment
   - summarize existing CSV
   - regenerate figures only
3. If the task is figure/text only, prefer saved outputs under `experiments_phys_levels/`.
4. Treat `iteration2_max_global_stress` as the primary stress output.
5. Treat `131 MPa` as the main manuscript threshold unless the user explicitly requests appendix sweep discussion.
6. State whether the result is based on:
   - predictive distribution
   - posterior mean only
   - ground truth

Do not:
- silently rerun expensive workflows
- mix appendix threshold sweep into main text unless explicitly requested
- change threshold definitions without editing config and reporting it