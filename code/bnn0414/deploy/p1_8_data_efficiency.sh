#!/bin/bash
# =============================================================================
# P1-8: Data efficiency curve — push + run + pull
# WARNING: 贵。默认只跑 core 模型对（bnn-baseline + bnn-phy-mono）
#          × 4 fractions × 2 seeds = 16 次训练。
# =============================================================================

set -eo pipefail

SERVER="tjzs@100.68.18.85"
LOCAL_ROOT="/Users/yinuo/Projects/hpr-claude-project/code/bnn0414"
REMOTE_ROOT="/home/tjzs/Documents/fenics_data/hpr_surrogate/hpr-claude-project/code/bnn0414"

MODEL="${MODEL:-core}"
TRAIN_FRACS="${TRAIN_FRACS:-0.25,0.5,0.75,1.0}"
DE_SEEDS="${DE_SEEDS:-2026,2027}"
CONDA_ENV="${CONDA_ENV:-pytorch-env}"
LEGACY_DIR="${LEGACY_DIR:-/home/tjzs/Documents/fenics_data/hpr_surrogate/hpr-claude-project/code/0310}"

echo "=============================================================="
echo "P1-8 Data Efficiency"
echo "  MODEL_SET    = $MODEL  (core | all)"
echo "  TRAIN_FRACS  = $TRAIN_FRACS"
echo "  DE_SEEDS     = $DE_SEEDS"
echo "=============================================================="

echo "[1/3] 推送..."
rsync -avz --exclude='__pycache__' \
    "$LOCAL_ROOT/code/experiments_0404/experiments/run_data_efficiency_0404.py" \
    "$SERVER:$REMOTE_ROOT/code/experiments_0404/experiments/"

echo "[2/3] 远端执行（预计 >1h）..."
ssh "$SERVER" bash -s <<EOF
set -e
cd "$REMOTE_ROOT/code/experiments_0404"
export HPR_ENV=server
export HPR_LEGACY_DIR=$LEGACY_DIR
export DE_MODEL_SET=$MODEL
export TRAIN_FRACS=$TRAIN_FRACS
export DE_SEEDS=$DE_SEEDS
conda run -n $CONDA_ENV python experiments/run_data_efficiency_0404.py
EOF

echo "[3/3] 拉回..."
mkdir -p "$LOCAL_ROOT/results/data_efficiency"
rsync -avz \
    "$SERVER:$REMOTE_ROOT/results/data_efficiency/" \
    "$LOCAL_ROOT/results/data_efficiency/"

echo ""
echo "=============================================================="
echo "P1-8 完成。产物："
for f in data_efficiency_all.csv data_efficiency_summary.csv data_efficiency_curve.png data_efficiency_manifest.json; do
    p="$LOCAL_ROOT/results/data_efficiency/$f"
    [ -f "$p" ] && echo "  ✓ $p" || echo "  ✗ 缺 $f"
done
echo "=============================================================="
