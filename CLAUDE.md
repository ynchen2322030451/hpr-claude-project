# HPR Probabilistic Surrogate Project

## Project scope
This repository studies probabilistic neural surrogates for uncertainty-to-risk analysis in a coupled thermo-mechanical HPR workflow.

## 项目目标
本项目围绕热管冷却反应堆耦合热-力响应的概率代理建模展开，重点关注：
1. surrogate model performance
2. forward uncertainty propagation and threshold risk
3. Sobol sensitivity analysis with CI-aware interpretation
4. observation-driven posterior inference
5. manuscript figure and text integration

## Non-negotiable rules
- Do not modify raw source data.
- Do not overwrite frozen surrogate artifacts unless explicitly asked.
- Treat `paper_experiment_config.py` as the single source of truth for primary outputs, thresholds, seeds, and paths.
- Prefer reusing saved CSV summaries when only figures/tables/text need updates.
- For manuscript edits, separate main-text claims from appendix-only claims.

## 当前科学约定
- Primary outputs:
  - iteration2_keff
  - iteration2_max_fuel_temp
  - iteration2_max_monolith_temp
  - iteration2_max_global_stress
  - iteration2_wall2
- Primary stress threshold: 131 MPa
- Threshold sweep (appendix only unless explicitly requested): 110, 120, 131 MPa
- Main comparison focus: baseline vs level2 regularized surrogate

## Repository workflow
1. training / fixed split
2. forward UQ and risk
3. Sobol + CI
4. inverse benchmark / posterior contraction
5. speed / OOD
6. manuscript figure + text integration

## Safe-edit policy
- When only text or figures are needed, do not rerun expensive experiments.
- Before changing any script that affects saved paper results, explain whether the change is:
  - text-only
  - plotting-only
  - postprocessing-only
  - experiment-changing

## 写作规则
- 因为当前阶段主要是论文草稿，我偏好中英文双语版本；允许以自然段落为分界交叉行文，但必须保证逻辑清晰，不要中英混乱拼接，例如你说“你可以这样写“xxx”，我希望给我中英文双语版本论文片段，并且两个版本按照自然段交替进行，必要的话还可以标注出比较不太常见的英文和对应释义或者可以考虑替换的词。
- 中文写作必须符合中文学术表达习惯，不做英文直译。
- Separate evidence from claims.
- Never invent references, definitions, data, or quantitative claims.
- If uncertain, mark as 待核实.
- Point out unsupported interpretations directly.

## 项目使用原则
- 优先复用现有 summary csv 和 saved results。
- 如果只是改文字或画图，不要默认重跑 expensive experiments。
- 如果正文与附录边界不清，优先收缩正文，扩展附录。
- Sobol 置信区间跨零的因素，不得写成稳定主导因素。
- 如果结论无法由当前 summary tables 直接支撑，应降级表述。

## Commands
- config inspection: `/config`
- list agents: `/agents`

Canonical training artifacts:
- fixed_surrogate_fixed_base/
- fixed_surrogate_fixed_level2/
- fixed_split/

Root-level metrics/test_predictions are compatibility outputs only, not primary truth sources.

1. Never overwrite canonical result directories without explicit rerun tag or new OUT_DIR.
2. Always check dataset size against split_meta before using fixed_split.
3. For code edits, prefer minimal diffs and reuse existing helper functions.
4. Treat fixed_surrogate_* as canonical model artifacts.
5. Treat root-level paper_metrics_table / metrics_level*.json / test_predictions_level*.json as compatibility outputs only unless explicitly stated otherwise.
6. If iter1 and iter2 output dimensions differ, do not use naive vector subtraction.

## Project invariants for code and results

### Canonical training artifacts
Unless explicitly overridden, treat the following as canonical:
- `experiments_phys_levels/fixed_surrogate_fixed_base/`
- `experiments_phys_levels/fixed_surrogate_fixed_level2/`
- `experiments_phys_levels/fixed_split/`

### Compatibility-only outputs
The following root-level files are not automatically the primary truth source:
- `experiments_phys_levels/metrics_level*.json`
- `experiments_phys_levels/test_predictions_level*.json`
- `experiments_phys_levels/paper_metrics_table.csv`

If both fixed-subdirectory and root-level outputs exist, prefer fixed-subdirectory unless told otherwise.

### Benchmark / calibration pool rule
Benchmark cases (`benchmark_caseXXX_posterior_samples_*.csv`) come from the
**calibration pool** (`split["X_cal"]` in run_inverse_benchmark_fixed_surrogate.py),
NOT from the surrogate test split (`fixed_split/test_indices.csv`).
The mapping is: `inverse_case_indices_<run_tag>.csv` → `pool_case_index` →
`inverse_calibration_pool.csv`.
Never use test-set indices as proxy for benchmark case ground truth.

### Split consistency rule
Before using any frozen split, verify:
- `split_meta.json` exists and `n_total == current dataset length`
- split indices are within bounds for current dataset

### Iter1 / Iter2 rule
Do not assume iteration1 and iteration2 outputs have identical dimensionality.
Use DELTA_PAIRS for any pairwise delta logic.

### Output overwrite rule
Do not overwrite canonical results silently.
For reruns, use a new OUT_DIR, new run tag, or rerun subdirectory.
Always state overwrite risk before providing a run command.

### Code modification rule
For every code editing task:
1. Read config (paper_experiment_config.py)
2. Read target file
3. Read direct imports
4. Read downstream consumers
5. Infer I/O contract
6. Make minimal compatible change

### Scientific interpretation rule
Keep explicit distinctions between:
- direct file-supported result
- interpretation
- uncertainty / limitation

Never describe nearest-neighbor HF retrieval as exact HF rerun validation.