#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$PROJECT_ROOT"

echo "[HOOK] protect-results: start"

TARGET_DIR="code/0310"
if [ ! -d "$TARGET_DIR" ]; then
  echo "[HOOK] No code/0310 directory found, skipping result protection checks."
  exit 0
fi

# ------------------------------------------------------------
# Files whose direct overwrite is risky
# ------------------------------------------------------------
RISKY_PATTERNS=(
  "paper_metrics_table.csv"
  "metrics_level"
  "test_predictions_level"
  "paper_posterior_hf_validation_summary.csv"
  "paper_posterior_hf_validation_per_output.csv"
  "paper_posterior_hf_validation_meta.json"
)

# ------------------------------------------------------------
# Find python files that contain direct writes to risky outputs
# ------------------------------------------------------------
found_risky=0

while IFS= read -r -d '' f; do
  content="$(cat "$f")"

  # If script references fixed_surrogate subdirs, that is safer.
  uses_fixed_dir=0
  if grep -q "fixed_surrogate_" "$f"; then
    uses_fixed_dir=1
  fi

  # If script references a tag in output filename, that is safer.
  uses_run_tag=0
  if grep -Eq 'RUN_TAG|run_tag|f".*{RUN_TAG}.*"|f".*{run_tag}.*"' "$f"; then
    uses_run_tag=1
  fi

  for p in "${RISKY_PATTERNS[@]}"; do
    if grep -q "$p" "$f"; then
      found_risky=1
      echo "[HOOK-WARN] Risky output pattern '$p' found in: $f"

      if [ "$uses_fixed_dir" -eq 0 ] && [ "$uses_run_tag" -eq 0 ]; then
        echo "[HOOK-FAIL] $f writes risky output(s) without obvious fixed-surrogate directory or run tag protection."
        echo "[HOOK-FAIL] Add one of the following before proceeding:"
        echo "            1) write into fixed_surrogate_* subdirectory"
        echo "            2) add RUN_TAG or dedicated rerun directory"
        echo "            3) explicitly isolate OUT_DIR for reruns"
        exit 1
      fi
    fi
  done
done < <(find "$TARGET_DIR" -maxdepth 1 -name "*.py" -print0)

if [ "$found_risky" -eq 0 ]; then
  echo "[HOOK] No risky output patterns detected."
else
  echo "[HOOK] Risky outputs detected, but at least one protection pattern was present."
fi

# ------------------------------------------------------------
# If canonical results already exist, warn before same-dir reuse
# ------------------------------------------------------------
if [ -d "code/0310/experiments_phys_levels" ]; then
  echo "[HOOK-WARN] Canonical result directory exists: code/0310/experiments_phys_levels"
  echo "[HOOK-WARN] Before rerunning training, prefer one of:"
  echo "            - new OUT_DIR"
  echo "            - new RUN_TAG"
  echo "            - archived old outputs"
fi

echo "[HOOK] protect-results: done"