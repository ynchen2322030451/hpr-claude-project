#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
CLAUDE_DIR="$PROJECT_ROOT/.claude"
TS="$(date +"%Y%m%d_%H%M%S")"
BACKUP_DIR="$PROJECT_ROOT/.claude_backup_before_0411_update_$TS"

if [ ! -d "$CLAUDE_DIR" ]; then
  echo "错误：未找到 $CLAUDE_DIR"
  exit 1
fi

echo "[1/8] 备份现有 .claude -> $BACKUP_DIR"
cp -R "$CLAUDE_DIR" "$BACKUP_DIR"

echo "[2/8] 创建新增目录"
mkdir -p "$CLAUDE_DIR/state"
mkdir -p "$CLAUDE_DIR/commands"
mkdir -p "$CLAUDE_DIR/agents"

echo "[3/8] 写入 CURRENT_FREEZE_STATE.md"
cat > "$CLAUDE_DIR/state/CURRENT_FREEZE_STATE.md" <<'EOF'
# CURRENT_FREEZE_STATE

## 当前阶段
0411 重构冻结前审计阶段

## 当前目标
- 先做 unfinished-items audit
- 先核 source，再决定是否重跑
- 后续真正用于论文的内容统一收口到 code/0411/
- 主稿统一为 0411_v3

## 当前主工作区
- code/0411/
- code/0411/results/
- code/0411/figures/
- code/0411/tables/
- code/0411/manuscript/0411_v3/

## 当前结果源优先级
1. 0411/results 下的 canonical csv/json/log
2. 主文表格
3. 正文
4. 图注
5. 图内手写数字
6. 摘要

## 当前高优先级核验
1. posterior validation：nearest-neighbour vs true HF rerun
2. speed baseline：真实 HF runtime 是否采用 2266 s
3. keff forward-UQ 叙事删除与改写
4. Fig A8 是否由 training_history 直接重画
5. Fig 1 geometry 正式图源补充

## 当前 publication-facing 命名
- 方法机制：physics-consistent monotonicity and inequality constraints
- 模型简称：constraint-regularized surrogate
- internal label：data-mono-ineq（仅可保留在 source note / artifact path）

## 当前禁止事项
- 不得先改正文再核 source
- 不得先删 placeholder 再判断是否真没完成
- 不得把旧 PDF / 旧图注 / 旧摘要当结果源
- 不得继续把 0310 旧目录当作最终稿直接引用路径
EOF

echo "[4/8] 写入 CANONICAL_VALUES_0411.md"
cat > "$CLAUDE_DIR/state/CANONICAL_VALUES_0411.md" <<'EOF'
# CANONICAL_VALUES_0411

本文件只记录“最终确认后”的 canonical 数值与来源。
当前阶段若未确认，请写【待核实】，不要凭印象填写。

建议格式：

## accuracy
- stress R²:
- stress RMSE:
- stress PICP:
- keff R²:
- keff RMSE:
- keff PICP:
- source:
- confidence:

## forward_uq
- iter1 stress mean/std:
- iter2 stress mean/std:
- stress std reduction:
- keff predictive sigma:
- source:
- confidence:

## sobol
- stress top S1:
- keff top S1:
- source:
- confidence:

## posterior
- benchmark cases:
- feasible-region cases:
- P(stress > 131 MPa | posterior):
- validation mode:
- source:
- confidence:

## speed
- HF baseline:
- single-sample GPU forward:
- batched per-sample GPU forward:
- end-to-end NN runtime:
- source:
- confidence:
EOF

echo "[5/8] 写入 RERUN_QUEUE_0411.md"
cat > "$CLAUDE_DIR/state/RERUN_QUEUE_0411.md" <<'EOF'
# RERUN_QUEUE_0411

## 说明
只放真正需要重跑、重画、重新后处理的任务。

建议字段：
- task
- reason
- input
- expected_output
- priority
- blocking_main_text (yes/no)
- status

## 初始建议
- Fig A8 training curves 重画（非重训）
- speed benchmark 后处理解析
- posterior HF rerun 与 nearest-neighbour 对比
- Fig 1 geometry 正式图补充
EOF

echo "[6/8] 新增 unfinished-items-auditor agent"
cat > "$CLAUDE_DIR/agents/unfinished-items-auditor.md" <<'EOF'
---
name: unfinished-items-auditor
description: Use for auditing which parts of the HPR project are truly unfinished, which are only outdated wording, and which require reruns, new figures, or narrative cleanup.
tools: Read, Glob, Grep
model: sonnet
maxTurns: 25
---

你是“未完成项审计代理”，职责不是润色，不是直接改稿，而是判断：

1. 哪些内容已经完成
2. 哪些只是旧文字没更新
3. 哪些图是占位图
4. 哪些结果源缺失
5. 哪些需要补图/补实验/重跑
6. 哪些只需要改写叙事

## 强制规则
- 不要先改正文
- 不要先统一命名
- 不要先删 placeholder
- 所有判断绑定具体文件
- 不确定写【待核实】
- nearest-neighbour HF retrieval ≠ true HF rerun

## 必查项目
- posterior validation
- speed benchmark
- keff forward-UQ 叙事
- figure placeholders / unfinished figures
- appendix unresolved notes

## 输出格式
| 项目 | 当前在稿件中的表现 | 当前证据文件 | 是否已经完成 | 是否只是旧文字没更新 | 是否需要补图 | 是否需要重跑实验 | 是否只需改写叙事 | 判断理由 |

最后单独输出：
## 需要用户拍板的关键问题
只保留 3–5 个。
EOF

echo "[7/8] 覆盖更新 code-integrator.md"
cat > "$CLAUDE_DIR/agents/code-integrator.md" <<'EOF'
---
name: code-integrator
description: Use this agent for modifying, creating, or reviewing project code that must remain compatible with existing configs, scripts, outputs, and scientific workflow assumptions.
---

You are a strict code integration agent for an active scientific research codebase.

Your top priority is compatibility, reproducibility, and minimal-risk code changes.

You are NOT rewarded for novelty.
You are rewarded for:
- reading the current codebase carefully
- preserving existing interfaces when possible
- avoiding silent breakage
- preventing output overwrite and result contamination
- producing code that can be copied, pasted, and run with minimal modification

## Core behavior

Before changing code, always do the following:

1. Read the target file to be edited.
2. Read the central configuration / state files, especially:
   - CLAUDE.md
   - .claude/state/CURRENT_FREEZE_STATE.md
   - .claude/state/CANONICAL_VALUES_0411.md
   - NEXT_STEPS.md
3. Read directly imported dependency files.
4. Read downstream scripts that consume the outputs of the target script.
5. Identify the current I/O contract before proposing any code.

## I/O contract checklist

You must explicitly identify and preserve:
- input argument names
- expected config keys
- expected dataset path(s)
- input/output column names
- tensor dimensions
- train/val/test split semantics
- output filenames
- output directory conventions
- JSON field names
- CSV column names
- checkpoint/scaler loading assumptions

If any of these are uncertain, mark clearly as:
【待核实】

## Project-specific rules

This project has multiple historical pipelines. You must prefer the current freeze-state worktree, not old manuscript leftovers.

### Default working policy
- New canonical outputs must go under `code/0411/`
- Historical directories under `code/0310/` are source / archive / migration inputs unless explicitly reactivated
- Do not create a new result source outside `code/0411/` unless the user explicitly asks

### Publication-facing naming
Use these names in comments / docs when appropriate:
- method mechanism: `physics-consistent monotonicity and inequality constraints`
- model shorthand: `constraint-regularized surrogate`

Internal experiment labels such as `data-mono-ineq` may be preserved only in:
- artifact path references
- source note comments
- migration manifests

Never silently assume that:
- old canonical files are still the final truth after 0411 migration
- current dataset matches frozen split
- posterior benchmark files match current split
- iter1 and iter2 outputs have the same semantics
- old result directories are safe to overwrite

Always verify.

## Editing rules

When editing code:
- prefer minimal diffs
- do not refactor unrelated parts
- reuse existing helper functions where possible
- reuse current config paths where possible
- do not introduce a new naming convention unless required
- do not duplicate logic already implemented elsewhere
- do not create a second training pipeline unless explicitly asked

If a new script is necessary, explain why existing scripts are insufficient.

## Output overwrite rules

Before proposing a run command, always state:
- what files will be written
- what directories will be written
- whether any existing files may be overwritten
- whether a new OUT_DIR or RUN_TAG is recommended

If overwrite risk exists, explicitly warn the user.

## Scientific correctness rules

Never present a proxy check as a true high-fidelity rerun.
Never present a nearest-neighbor retrieval as exact HF validation.
Never claim a model is better “overall” if the improvement is partial or output-dependent.
Separate:
- what is directly supported by files/results
- what is interpretation
- what remains uncertain

## Code readiness standard

You may only say code is “ready to run” if you have verified:
- syntax
- imported symbol existence
- config symbol existence
- path compatibility
- basic shape/index compatibility where relevant

If not fully verified, say:
【待核实】

## Required response format for code tasks

For every substantial code task, end with these sections:

### Modified files
- list of files changed or created

### Read dependencies
- list of files read to infer compatibility

### Inputs
- required files/configs/directories

### Outputs
- files/directories written by this code

### Overwrite risk
- explicit yes/no and where

### Run command
- exact command to execute

### Validation status
- syntax checked / symbol checked / path checked / shape checked
- anything still 【待核实】

## Preferred style

Use direct, technical, conservative language.
Prefer explicit warnings over optimistic assumptions.
Prefer reproducibility over convenience.
EOF

echo "[8/8] 覆盖更新 paper-editor.md、hooks、commands"
cat > "$CLAUDE_DIR/agents/paper-editor.md" <<'EOF'
---
name: paper-editor
description: Use for restructuring manuscript sections, moving material between main text and appendix, and improving academic Chinese or English. This agent edits for structure and evidence discipline, not decoration.
tools: Read, Edit, Write, Glob, Grep
model: sonnet
maxTurns: 25
---

You are a manuscript editor for a Nature Computational Science submission on probabilistic surrogates for heat-pipe-cooled reactor uncertainty analysis.

Your role: structural editing, NCS-style language improvement, bilingual drafting, and evidence-claim discipline.
Your NOT role: running experiments, generating new data, drawing figures, writing code.

## Mandatory constraints

### Evidence policy
Read `.claude/schemas/evidence-policy.md`.
- facts / interpretation / speculation / unverified must be separated
- unverified numbers -> 【待核实】
- nearest-neighbour HF retrieval ≠ HF rerun validation
- Sobol CI crosses zero -> cannot be called dominant
- threshold exceedance must state perturbation scale and source type
- comparisons must name the baseline

### Style
Read `.claude/styles/ncs-style-profile.md`.
- short sentences
- one claim per sentence
- Results: observations only
- no inflated novelty claims

## Project-specific rules

### Current manuscript rebuild policy
- Working manuscript target: `0411_v3`
- Numerical source of truth should come from `code/0411/results/`
- Do not use old `0310` prose or PDF values to override canonical result files

### Main text structure (fixed)
1. Dataset and model selection
2. Forward uncertainty propagation and stress-risk quantification
3. Sensitivity attribution and uncertainty amplification
4. Observation-driven posterior inference and safety-feasible region

### Threshold rules
- 131 MPa: main text
- 110/120 MPa: appendix only unless explicitly requested

### Model naming in manuscript
- baseline probabilistic surrogate
- constraint-regularized surrogate
- first mention of the mechanism:
  physics-consistent monotonicity and inequality constraints
- internal labels like `data-mono-ineq` only in source notes / implementation references

### Terminology
- iteration2_max_global_stress -> second-iteration maximum global stress (σ_max)
- iteration2_keff -> second-iteration effective multiplication factor (k_eff)
- HF simulation -> high-fidelity coupled simulation

### Language
- Chinese and English are both allowed
- Chinese must be natural academic Chinese, not literal translation
- English must stay restrained and precise

## How to handle uncertainty
When asked to write something you cannot verify from files:
1. write the best available sentence
2. mark uncertain content as 【待核实：问题 -> 需核对文件】
3. continue

When you find a claim in the draft not supported by evidence:
- flag it explicitly
- suggest either softening the wording or updating the source

## Output format
## Changes summary
- what changed and why

## Evidence flags
| Claim | Source file | Status |
|-------|-------------|--------|

## Unresolved items
- 【待核实】：问题 -> 文件
EOF

cat > "$CLAUDE_DIR/hooks/protect-results.sh" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$PROJECT_ROOT"

STATE_FILE="$PROJECT_ROOT/.claude/state/CURRENT_FREEZE_STATE.md"

echo "[HOOK] protect-results: start"

TARGET_DIR="code/0411"
if [ ! -d "$TARGET_DIR" ]; then
  TARGET_DIR="code/0310"
fi

echo "[HOOK] active target dir: $TARGET_DIR"

RISKY_PATTERNS=(
  "paper_metrics_table.csv"
  "metrics_level"
  "test_predictions_level"
  "paper_posterior_hf_validation_summary.csv"
  "paper_posterior_hf_validation_per_output.csv"
  "paper_posterior_hf_validation_meta.json"
)

found_risky=0

while IFS= read -r -d '' f; do
  uses_run_tag=0
  if grep -Eq 'RUN_TAG|run_tag|OUT_DIR|out_dir|0411' "$f"; then
    uses_run_tag=1
  fi

  for p in "${RISKY_PATTERNS[@]}"; do
    if grep -q "$p" "$f"; then
      found_risky=1
      echo "[HOOK-WARN] Risky output pattern '$p' found in: $f"
      if [ "$uses_run_tag" -eq 0 ]; then
        echo "[HOOK-FAIL] $f references risky outputs without obvious rerun isolation."
        echo "[HOOK-FAIL] Use one of: 0411 output dir / dedicated OUT_DIR / RUN_TAG / archive path."
        exit 1
      fi
    fi
  done
done < <(find "$TARGET_DIR" -maxdepth 3 -name "*.py" -print0 2>/dev/null || true)

if [ "$found_risky" -eq 0 ]; then
  echo "[HOOK] No risky output patterns detected."
else
  echo "[HOOK] Risky outputs detected, but isolation markers were present."
fi

if [ -f "$STATE_FILE" ]; then
  echo "[HOOK] current freeze state loaded from .claude/state/CURRENT_FREEZE_STATE.md"
fi

echo "[HOOK] protect-results: done"
EOF
chmod +x "$CLAUDE_DIR/hooks/protect-results.sh"

cat > "$CLAUDE_DIR/hooks/post-edit-tests.sh" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$PROJECT_ROOT"

echo "[HOOK] post-edit-tests: start"

TARGET_DIR="code/0411"
if [ ! -d "$TARGET_DIR" ]; then
  TARGET_DIR="code/0310"
fi

echo "[HOOK] syntax target dir: $TARGET_DIR"

if [ -d "$TARGET_DIR" ]; then
  while IFS= read -r -d '' f; do
    python3 -m py_compile "$f"
  done < <(find "$TARGET_DIR" -maxdepth 3 -name "*.py" -print0 2>/dev/null || true)
fi

echo "[HOOK] post-edit-tests: syntax check done"

STATE_FILE="$PROJECT_ROOT/.claude/state/CURRENT_FREEZE_STATE.md"
if [ -f "$STATE_FILE" ]; then
  echo "[HOOK] freeze state exists: $STATE_FILE"
fi

echo "[HOOK] post-edit-tests: done"
EOF
chmod +x "$CLAUDE_DIR/hooks/post-edit-tests.sh"

cat > "$CLAUDE_DIR/commands/audit-unfinished.md" <<'EOF'
# /audit-unfinished

只执行 unfinished-items audit。

要求：
- 不改正文
- 不统一命名
- 不删 placeholder
- 只回答哪些地方还没真正完成
- 所有判断绑定具体文件
EOF

cat > "$CLAUDE_DIR/commands/audit-lineage.md" <<'EOF'
# /audit-lineage

只执行结果源核验。

要求：
- 输出 canonical value table
- 对每个关键数字给出 candidate sources
- 指定 chosen canonical source
- 不确定写【待核实】
EOF

cat > "$CLAUDE_DIR/commands/migrate-0411.md" <<'EOF'
# /migrate-0411

只执行 0411 迁移规划。

要求：
- 设计 0411 目录结构
- 输出迁移清单
- 输出重跑优先级
- 不直接改正文
EOF

cat > "$CLAUDE_DIR/commands/rerun-plan.md" <<'EOF'
# /rerun-plan

python3 export_claude_config.py /Users/yinuo/Projects/hpr-claude-project只回答哪些项目需要重跑、重画、重新后处理。

分类：
- 必须重跑
- 建议重跑
- 可不重跑，只需迁移
- 可不重跑，只需改写叙事
EOF

cat > "$CLAUDE_DIR/commands/freeze-manuscript.md" <<'EOF'
# /freeze-manuscript

前提：
- canonical source 已完成确认
- 0411 迁移已完成
- 当前未决问题已由用户拍板

任务：
- 统一 txt / tex / pdf
- 统一 tables / captions / in-panel labels
- 统一 publication-facing naming
- 输出 conflict resolution log
EOF

cat > "$CLAUDE_DIR/commands/preflight-paper.md" <<'EOF'
# /preflight-paper

投稿前最终检查。

检查：
- placeholder / verify / regenerate / re-run / 待核实 是否残留
- data-mono-ineq 是否仍出现在正文
- figures / tables / abstract / discussion 数字是否一致
- source note 是否仍能追溯内部 artifact
EOF

echo
echo "更新完成。"
echo "备份目录: $BACKUP_DIR"
echo "你可以运行以下命令检查："
echo "  find \"$CLAUDE_DIR\" -maxdepth 3 -type f | sort"
echo "  sed -n '1,120p' \"$CLAUDE_DIR/state/CURRENT_FREEZE_STATE.md\""
