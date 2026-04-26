#!/bin/bash
# =============================================================================
# P1-7: Prior sensitivity sweep — push + run + pull
# =============================================================================

set -eo pipefail

SERVER="tjzs@100.68.18.85"
LOCAL_ROOT="/Users/yinuo/Projects/hpr-claude-project/code/bnn0414"
REMOTE_ROOT="/home/tjzs/Documents/fenics_data/hpr_surrogate/hpr-claude-project/code/bnn0414"

MODEL="${MODEL:-all}"
PRIOR_SENS_N_CASES="${PRIOR_SENS_N_CASES:-6}"
PRIOR_SENS_N_TOTAL="${PRIOR_SENS_N_TOTAL:-4000}"
PRIOR_SENS_N_CHAINS="${PRIOR_SENS_N_CHAINS:-2}"
CONDA_ENV="${CONDA_ENV:-pytorch-env}"
LEGACY_DIR="${LEGACY_DIR:-/home/tjzs/Documents/fenics_data/hpr_surrogate/hpr-claude-project/code/0310}"

echo "=============================================================="
echo "P1-7 Prior Sensitivity"
echo "  MODEL                = $MODEL"
echo "  N_CASES              = $PRIOR_SENS_N_CASES"
echo "  N_TOTAL              = $PRIOR_SENS_N_TOTAL"
echo "  N_CHAINS             = $PRIOR_SENS_N_CHAINS"
echo "=============================================================="

echo "[1/3] 推送..."
rsync -avz --exclude='__pycache__' \
    "$LOCAL_ROOT/code/experiments_0404/experiments/run_prior_sensitivity_0404.py" \
    "$SERVER:$REMOTE_ROOT/code/experiments_0404/experiments/"

echo "[2/3] 远端执行..."
ssh "$SERVER" bash -s <<EOF
set -e
cd "$REMOTE_ROOT/code/experiments_0404"
export HPR_ENV=server
export HPR_LEGACY_DIR=$LEGACY_DIR
export MODEL_ID=$MODEL
export PRIOR_SENS_N_CASES=$PRIOR_SENS_N_CASES
export PRIOR_SENS_N_TOTAL=$PRIOR_SENS_N_TOTAL
export PRIOR_SENS_N_CHAINS=$PRIOR_SENS_N_CHAINS
conda run -n $CONDA_ENV python experiments/run_prior_sensitivity_0404.py
EOF

echo "[3/3] 拉回..."
mkdir -p "$LOCAL_ROOT/code/experiments_0404/experiments/posterior"
rsync -avz \
    --include='*/' --include='prior_sensitivity/**' --include='prior_sensitivity_all_models.json' --exclude='*' \
    "$SERVER:$REMOTE_ROOT/code/experiments_0404/experiments/posterior/" \
    "$LOCAL_ROOT/code/experiments_0404/experiments/posterior/"

echo ""
echo "=============================================================="
echo "P1-7 完成。产物："
for m in bnn-baseline bnn-data-mono bnn-phy-mono bnn-data-mono-ineq; do
    d="$LOCAL_ROOT/code/experiments_0404/experiments/posterior/$m/prior_sensitivity"
    for f in prior_sensitivity_per_case.csv prior_sensitivity_summary.csv prior_sensitivity_${m}.png; do
        p="$d/$f"
        [ -f "$p" ] && echo "  ✓ $p" || echo "  ✗ 缺 $f"
    done
done
echo "=============================================================="
