# HPR Probabilistic Surrogate Project
﻿
## Project scope
This repository studies probabilistic neural surrogates for uncertainty-to-risk analysis in a coupled thermo-mechanical HPR workflow.
﻿
## Non-negotiable rules
- Do not modify raw source data.
- Do not overwrite frozen surrogate artifacts unless explicitly asked.
- Treat `paper_experiment_config.py` as the single source of truth for primary outputs, thresholds, seeds, and paths.
- Prefer reusing saved CSV summaries when only figures/tables/text need updates.
- For manuscript edits, separate main-text claims from appendix-only claims.
﻿
## Current scientific conventions
- Primary outputs:
- iteration2_keff
- iteration2_max_fuel_temp
- iteration2_max_monolith_temp
- iteration2_max_global_stress
- iteration2_wall2
- Primary stress threshold: 131 MPa
- Threshold sweep (appendix only unless explicitly requested): 110, 120, 131 MPa
- Main comparison focus: baseline vs level2 regularized surrogate
﻿
## Repository workflow
1. training / fixed split
2. forward UQ and risk
3. Sobol + CI
4. inverse benchmark / posterior contraction
5. speed / OOD
6. manuscript figure + text integration
﻿
## Safe-edit policy
- When only text or figures are needed, do not rerun expensive experiments.
- Before changing any script that affects saved paper results, explain whether the change is:
- text-only
- plotting-only
- postprocessing-only
- experiment-changing
﻿
## Writing style
-因为是写草稿所以喜欢中英文双语版本，以自然段落为分界交叉行文
- Use rigorous academic Chinese when writing Chinese.
- Separate evidence from claims.
- Never invent references or quantitative claims.
- If uncertain, mark as 待核实.
- Point out unsupported interpretations directly.
﻿
## Commands
- health / config inspection: `/config`
- list agents: `/agents`
- inspect hooks: `/hooks`