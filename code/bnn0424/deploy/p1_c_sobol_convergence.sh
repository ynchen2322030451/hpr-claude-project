#!/bin/bash
# =============================================================================
# Task C: Sobol convergence curve — push + run + pull
# =============================================================================

set -eo pipefail

SERVER="tjzs@100.68.18.85"
LOCAL_ROOT="/Users/yinuo/Projects/hpr-claude-project/code/bnn0414"
REMOTE_ROOT="/home/tjzs/Documents/fenics_data/hpr_surrogate/hpr-claude-project/code/bnn0414"

CONDA_ENV="${CONDA_ENV:-pytorch-env}"
LEGACY_DIR="${LEGACY_DIR:-/home/tjzs/Documents/fenics_data/hpr_surrogate/hpr-claude-project/code/0310}"

echo "=============================================================="
echo "Task C: Sobol Convergence Curve"
echo "=============================================================="

echo "[1/3] Push script..."
rsync -avz --exclude='__pycache__' \
    "$LOCAL_ROOT/code/experiments_0404/experiments/run_sobol_convergence_0404.py" \
    "$SERVER:$REMOTE_ROOT/code/experiments_0404/experiments/"

echo "[2/3] Run on server..."
ssh "$SERVER" bash -s <<EOF
set -e
cd "$REMOTE_ROOT/code/experiments_0404"
export HPR_ENV=server
export HPR_LEGACY_DIR=$LEGACY_DIR
source /opt/software/miniconda3/etc/profile.d/conda.sh
conda run -n $CONDA_ENV python experiments/run_sobol_convergence_0404.py
EOF

echo "[3/3] Pull results..."
mkdir -p "$LOCAL_ROOT/results/sensitivity"
rsync -avz \
    "$SERVER:$REMOTE_ROOT/results/sensitivity/sobol_convergence*" \
    "$LOCAL_ROOT/results/sensitivity/"

echo ""
echo "=============================================================="
echo "Task C done."
ls -la "$LOCAL_ROOT/results/sensitivity/sobol_convergence"* 2>/dev/null
echo "=============================================================="
