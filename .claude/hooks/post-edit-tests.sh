#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$PROJECT_ROOT"

echo "[HOOK] post-edit-tests: start"

# ------------------------------------------------------------
# 1) Basic Python syntax check on project scripts
# ------------------------------------------------------------
if [ -d "code/0310" ]; then
  echo "[HOOK] Checking Python syntax under code/0310 ..."
  while IFS= read -r -d '' f; do
    python -m py_compile "$f"
  done < <(find code/0310 -maxdepth 1 -name "*.py" -print0)
fi

# ------------------------------------------------------------
# 2) Basic config symbol existence check
# ------------------------------------------------------------
echo "[HOOK] Checking core config symbols ..."
python - <<'PY'
import os
import sys
sys.path.insert(0, os.path.abspath("code/0310"))

from paper_experiment_config import (
    CSV_PATH, OUT_DIR, INPUT_COLS, OUTPUT_COLS, SEED
)

assert isinstance(CSV_PATH, str) and len(CSV_PATH) > 0
assert isinstance(OUT_DIR, str) and len(OUT_DIR) > 0
assert isinstance(INPUT_COLS, list) and len(INPUT_COLS) > 0
assert isinstance(OUTPUT_COLS, list) and len(OUTPUT_COLS) > 0
assert isinstance(SEED, int)

print("[HOOK] core config symbols OK")
PY

# ------------------------------------------------------------
# 3) Check that key training helpers are importable
# ------------------------------------------------------------
echo "[HOOK] Checking training helper symbols ..."
python - <<'PY'
import os
import sys
sys.path.insert(0, os.path.abspath("code/0310"))

from run_phys_levels_main import (
    load_dataset,
    get_device,
    objective_factory,
    train_with_params,
    HeteroMLP,
)

assert callable(load_dataset)
assert callable(get_device)
assert callable(objective_factory)
assert callable(train_with_params)
assert HeteroMLP is not None

print("[HOOK] training helper symbols OK")
PY

# ------------------------------------------------------------
# 4) Shape / pairing sanity check for DELTA_PAIRS if present
# ------------------------------------------------------------
echo "[HOOK] Checking iter1/iter2 delta-pair compatibility ..."
python - <<'PY'
import os
import sys
sys.path.insert(0, os.path.abspath("code/0310"))

from paper_experiment_config import OUTPUT_COLS

try:
    from paper_experiment_config import DELTA_PAIRS
except Exception:
    DELTA_PAIRS = None

if DELTA_PAIRS is not None:
    assert isinstance(DELTA_PAIRS, list) and len(DELTA_PAIRS) > 0
    for a, b in DELTA_PAIRS:
        assert a in OUTPUT_COLS, f"{a} missing from OUTPUT_COLS"
        assert b in OUTPUT_COLS, f"{b} missing from OUTPUT_COLS"
        assert a.startswith("iteration1_"), f"{a} is not iteration1_*"
        assert b.startswith("iteration2_"), f"{b} is not iteration2_*"

print("[HOOK] delta-pair compatibility OK")
PY

# ------------------------------------------------------------
# 5) Optional dataset existence check (non-fatal warning only)
# ------------------------------------------------------------
echo "[HOOK] Checking dataset path ..."
python - <<'PY'
import os
import sys
sys.path.insert(0, os.path.abspath("code/0310"))

from paper_experiment_config import CSV_PATH

if os.path.exists(CSV_PATH):
    print(f"[HOOK] dataset exists: {CSV_PATH}")
else:
    print(f"[HOOK-WARN] dataset missing: {CSV_PATH}")
PY

echo "[HOOK] post-edit-tests: done"