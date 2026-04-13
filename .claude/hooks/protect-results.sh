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
