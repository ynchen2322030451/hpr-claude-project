#!/bin/bash
# =============================================================================
# P0-4: Monotonicity + inequality violation rate — push + run + pull
# =============================================================================

set -eo pipefail

SERVER="tjzs@100.68.18.85"
LOCAL_ROOT="/Users/yinuo/Projects/hpr-claude-project/code/bnn0414"
REMOTE_ROOT="/home/tjzs/Documents/fenics_data/hpr_surrogate/hpr-claude-project/code/bnn0414"

MODEL="${MODEL:-all}"
PERTURB_SCALE="${PERTURB_SCALE:-1.0}"
CONDA_ENV="${CONDA_ENV:-pytorch-env}"
LEGACY_DIR="${LEGACY_DIR:-/home/tjzs/Documents/fenics_data/hpr_surrogate/hpr-claude-project/code/0310}"

echo "=============================================================="
echo "P0-4 Monotonicity Violation"
echo "  MODEL          = $MODEL"
echo "  PERTURB_SCALE  = $PERTURB_SCALE × DESIGN_SIGMA"
echo "=============================================================="

echo "[1/3] 推送脚本..."
rsync -avz --exclude='__pycache__' \
    "$LOCAL_ROOT/code/experiments_0404/experiments/run_monotonicity_violation_0404.py" \
    "$SERVER:$REMOTE_ROOT/code/experiments_0404/experiments/"

echo "[2/3] 服务器端执行..."
ssh "$SERVER" bash -s <<EOF
set -e
cd "$REMOTE_ROOT/code/experiments_0404"
export HPR_ENV=server
export HPR_LEGACY_DIR=$LEGACY_DIR
export MODEL_ID=$MODEL
export PERTURB_SCALE=$PERTURB_SCALE
conda run -n $CONDA_ENV python experiments/run_monotonicity_violation_0404.py
EOF

echo "[3/3] 拉取结果..."
mkdir -p "$LOCAL_ROOT/results/physics_consistency"
rsync -avz \
    "$SERVER:$REMOTE_ROOT/results/physics_consistency/" \
    "$LOCAL_ROOT/results/physics_consistency/"

echo ""
echo "=============================================================="
echo "P0-4 完成。产物："
for f in monotonicity_violation_rate.csv inequality_violation_rate.csv monotonicity_violation_primary.png inequality_violation.png; do
    p="$LOCAL_ROOT/results/physics_consistency/$f"
    [ -f "$p" ] && echo "  ✓ $p" || echo "  ✗ 缺失 $f"
done
echo "=============================================================="
