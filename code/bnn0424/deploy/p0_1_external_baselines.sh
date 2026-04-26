#!/bin/bash
# =============================================================================
# P0-1: External Baselines (MC-Dropout + 5-member Deep Ensemble)
# conda env: pytorch-env (NOT nn_env)
# =============================================================================

set -eo pipefail

SERVER="tjzs@100.68.18.55"
LOCAL_ROOT="/Users/yinuo/Projects/hpr-claude-project/code/bnn0414"
REMOTE_ROOT="/home/tjzs/Documents/fenics_data/hpr_surrogate/hpr-claude-project/code/bnn0414"

MODEL="${MODEL:-all}"
ENSEMBLE_SIZE="${ENSEMBLE_SIZE:-5}"
DROPOUT_RATE="${DROPOUT_RATE:-0.1}"
CONDA_ENV="${CONDA_ENV:-pytorch-env}"
LEGACY_DIR="${LEGACY_DIR:-/home/tjzs/Documents/fenics_data/hpr_surrogate/hpr-claude-project/code/0310}"

echo "=============================================================="
echo "P0-1 External Baselines"
echo "  MODEL          = $MODEL  (mc-dropout | deep-ensemble | all)"
echo "  ENSEMBLE_SIZE  = $ENSEMBLE_SIZE"
echo "  DROPOUT_RATE   = $DROPOUT_RATE"
echo "  CONDA_ENV      = $CONDA_ENV"
echo "=============================================================="

echo "[1/3] 推送脚本 + 依赖..."
# 推送 experiment 脚本
rsync -avz --exclude='__pycache__' \
    "$LOCAL_ROOT/code/experiments_0404/experiments/run_external_baselines_0404.py" \
    "$SERVER:$REMOTE_ROOT/code/experiments_0404/experiments/"

# 推送 config + training infra（确保服务器有最新版）
rsync -avz --exclude='__pycache__' \
    "$LOCAL_ROOT/code/experiments_0404/config/" \
    "$SERVER:$REMOTE_ROOT/code/experiments_0404/config/"
rsync -avz --exclude='__pycache__' \
    "$LOCAL_ROOT/code/experiments_0404/training/run_train_0404.py" \
    "$SERVER:$REMOTE_ROOT/code/experiments_0404/training/"
rsync -avz --exclude='__pycache__' \
    "$LOCAL_ROOT/code/bnn_model.py" \
    "$SERVER:$REMOTE_ROOT/code/"

echo "[2/3] 远端训练（预计 ~30-60min）..."
ssh "$SERVER" bash -s <<EOF
set -e
cd "$REMOTE_ROOT/code/experiments_0404"
export HPR_ENV=server
export HPR_LEGACY_DIR=$LEGACY_DIR
export MODEL_ID=$MODEL
export ENSEMBLE_SIZE=$ENSEMBLE_SIZE
export DROPOUT_RATE=$DROPOUT_RATE
conda run -n $CONDA_ENV python experiments/run_external_baselines_0404.py
EOF

echo "[3/3] 拉回结果..."
for m in mc-dropout deep-ensemble; do
    mkdir -p "$LOCAL_ROOT/code/models/$m"
    rsync -avz \
        "$SERVER:$REMOTE_ROOT/code/models/$m/" \
        "$LOCAL_ROOT/code/models/$m/" 2>/dev/null || true
done
rsync -avz \
    "$SERVER:$REMOTE_ROOT/code/models/external_baselines_summary.json" \
    "$LOCAL_ROOT/code/models/" 2>/dev/null || true

echo ""
echo "=============================================================="
echo "P0-1 完成。产物："
for m in mc-dropout deep-ensemble; do
    d="$LOCAL_ROOT/code/models/$m"
    for f in fixed_eval/test_predictions_fixed.json fixed_eval/metrics_fixed.json; do
        p="$d/$f"
        [ -f "$p" ] && echo "  ✓ $p" || echo "  ✗ 缺 $m/$f"
    done
done
echo "=============================================================="
