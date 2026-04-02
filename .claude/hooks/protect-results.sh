#!/bin/bash
set -e

INPUT=$(cat)

# 阻止编辑 raw data 和 frozen artifacts
echo "$INPUT" | grep -E 'data/raw|fixed_surrogate_fixed_level2|checkpoint_level2|scalers_level2' >/dev/null && {
  echo "Blocked: do not edit raw data or frozen surrogate artifacts without explicit permission."
  exit 2
}

exit 0