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
- Treat `experiment_config_0404.py` (in bnn0414/bnn0424) as the single source of truth for primary outputs, thresholds, seeds, and paths. Legacy `paper_experiment_config.py` applies only to code/0310.
- Prefer reusing saved CSV summaries when only figures/tables/text need updates.
- For manuscript edits, separate main-text claims from appendix-only claims.

## Figure vocabulary rule (applies to ALL manuscript figures, panels, legends, axis labels, captions)
Never use code-level or raw internal identifiers inside figures. Translate them into paper-facing terms:

| forbidden in figures                                  | use instead                                      |
|-------------------------------------------------------|--------------------------------------------------|
| `iter1`, `iteration1`, `iteration 1`, "pass 1"        | "uncoupled pass" (or omit — usually not needed)  |
| `iter2`, `iteration2`, `iteration 2`                  | "coupled steady state" / "coupled response"     |
| `iteration2_max_global_stress`                        | "coupled steady-state max stress"                |
| `iteration2_keff`, `k_eff` (raw col name)             | r"$k_\mathrm{eff}$ (coupled)"                    |
| `iteration2_max_fuel_temp`, `_monolith_temp`          | "max fuel temp", "max monolith temp"             |
| `level0`, `Level 0`, `baseline`                       | "Reference surrogate"                            |
| `level2`, `Level 2`, `data-mono-ineq`, `phy-mono`     | "Physics-regularized surrogate"                  |
| internal model IDs (`data-mono`, `phy-mono`, etc.)    | descriptive scientific name only                 |

Also: figures must not contain CJK characters (matplotlib default fonts have no CJK glyphs → 乱码). Use English placeholders like "N/A" or "pending audit" instead of "待核实" inside figures. CJK is fine in `.txt` companion files and captions written in Chinese manuscript files.

## 当前科学约定
- Primary outputs:
  - iteration2_keff
  - iteration2_max_fuel_temp
  - iteration2_max_monolith_temp
  - iteration2_max_global_stress
  - iteration2_wall2
- Primary stress threshold: 131 MPa
- Threshold sweep (appendix only unless explicitly requested): 110, 120, 131, 150, 180, 200 MPa
- Main comparison focus: bnn-baseline (Reference surrogate) vs bnn-phy-mono (Physics-regularized surrogate)

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

Canonical training artifacts (BNN, bnn0414/bnn0424):
- results_v3418/models/bnn-phy-mono/ (primary model)
- results_v3418/models/bnn-baseline/ (reference)
- results_v3418/fixed_split/ (v3418 split: 2339/501/501)

Legacy (code/0310 only, do NOT use for BNN work):
- experiments_phys_levels/fixed_surrogate_fixed_base/
- experiments_phys_levels/fixed_surrogate_fixed_level2/

Root-level metrics/test_predictions are compatibility outputs only, not primary truth sources.

**Authoritative directory**: `code/bnn0424/` is the sole active working directory for all BNN manuscript, code, and figure work. `code/bnn0414/` is a read-only archive (contains large files like plot_gpt/fig0_geometry_ref/ not copied to bnn0424). Do not edit bnn0414.

1. Never overwrite canonical result directories without explicit rerun tag or new OUT_DIR.
2. Always check dataset size against split_meta before using fixed_split.
3. For code edits, prefer minimal diffs and reuse existing helper functions.
4. Treat fixed_surrogate_* as canonical model artifacts.
5. Treat root-level paper_metrics_table / metrics_level*.json / test_predictions_level*.json as compatibility outputs only unless explicitly stated otherwise.
6. If iter1 and iter2 output dimensions differ, do not use naive vector subtraction.

## Project invariants for code and results

### Canonical training artifacts
For BNN work (bnn0414/bnn0424), canonical artifacts are:
- `results_v3418/models/bnn-phy-mono/` (primary)
- `results_v3418/models/bnn-baseline/` (reference)
- `results_v3418/fixed_split/` (n=3341, seed=2026)

For legacy 0310 work only:
- `experiments_phys_levels/fixed_surrogate_fixed_base/`
- `experiments_phys_levels/fixed_surrogate_fixed_level2/`
- `experiments_phys_levels/fixed_split/`

### Compatibility-only outputs
The following root-level files are not automatically the primary truth source:
- `experiments_phys_levels/metrics_level*.json`
- `experiments_phys_levels/test_predictions_level*.json`
- `experiments_phys_levels/paper_metrics_table.csv`

If both fixed-subdirectory and root-level outputs exist, prefer fixed-subdirectory unless told otherwise.

### Posterior benchmark rule (current method — 0404 scripts, 4-chain canonical)
Benchmark cases in `run_posterior_0404.py` come from the **test split**, NOT from any calibration pool.
- "Observations" = true HF outputs from test samples + 2% artificial noise.
- 18 benchmark cases (6 low / 6 near / 6 high stress), 4 independent chains per case.
- Key results (phy-mono, 4-chain): 90CI coverage = 0.861 (62/72); acceptance 0.58–0.63; max R-hat = 1.010.
- Low-stress coverage = 0.667 (weaker); near-stress 1.000; high-stress 0.917.
- HF rerun (phy-mono): 54/54 complete, stress MAE 5.65 MPa.
- Source: `results_v3418/experiments/posterior/<model_id>/rerun_4chain/benchmark_summary.csv`.

Deprecated values: coverage 0.875/0.917 (1-chain), acceptance 0.47–0.61 — all replaced by 4-chain results above.

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