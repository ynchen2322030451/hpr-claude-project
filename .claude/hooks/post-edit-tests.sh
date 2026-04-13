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
