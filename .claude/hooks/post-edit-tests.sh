#!/bin/bash
set -e

INPUT=$(cat)

# 只有当修改核心脚本时才做快速语法检查
echo "$INPUT" | grep -E 'run_forward_uq_analysis.py|run_sobol_analysis.py|run_safety_threshold_analysis.py|run_compare_fixed_models.py' >/dev/null || exit 0

python -m py_compile \
  run_forward_uq_analysis.py \
  run_sobol_analysis.py \
  run_safety_threshold_analysis.py \
  run_compare_fixed_models.py

exit 0