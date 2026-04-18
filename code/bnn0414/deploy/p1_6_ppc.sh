#!/bin/bash
# =============================================================================
# P1-6: Posterior Predictive Check — push + run + pull
# Depends on: p0_3_mcmc_diagnostics.sh 已跑完（chains .npz 已落到服务器）
# =============================================================================

set -eo pipefail

SERVER="tjzs@100.68.18.85"
LOCAL_ROOT="/Users/yinuo/Projects/hpr-claude-project/code/bnn0414"
REMOTE_ROOT="/home/tjzs/Documents/fenics_data/hpr_surrogate/hpr-claude-project/code/bnn0414"

MODEL="${MODEL:-all}"
PPC_N_DRAWS="${PPC_N_DRAWS:-500}"
PPC_N_MC="${PPC_N_MC:-20}"
CONDA_ENV="${CONDA_ENV:-pytorch-env}"
LEGACY_DIR="${LEGACY_DIR:-/home/tjzs/Documents/fenics_data/hpr_surrogate/hpr-claude-project/code/0310}"

echo "=============================================================="
echo "P1-6 Posterior Predictive Check"
echo "  MODEL        = $MODEL"
echo "  PPC_N_DRAWS  = $PPC_N_DRAWS  (θ draws per case)"
echo "  PPC_N_MC     = $PPC_N_MC     (MC samples per θ forward)"
echo "=============================================================="

echo "[1/3] 推送脚本..."
rsync -avz --exclude='__pycache__' \
    "$LOCAL_ROOT/code/experiments_0404/experiments/run_posterior_predictive_check_0404.py" \
    "$SERVER:$REMOTE_ROOT/code/experiments_0404/experiments/"

echo "[2/3] 服务器端执行..."
ssh "$SERVER" bash -s <<EOF
set -e
cd "$REMOTE_ROOT/code/experiments_0404"
export HPR_ENV=server
export HPR_LEGACY_DIR=$LEGACY_DIR
export MODEL_ID=$MODEL
export PPC_N_DRAWS=$PPC_N_DRAWS
export PPC_N_MC=$PPC_N_MC
conda run -n $CONDA_ENV python experiments/run_posterior_predictive_check_0404.py
EOF

echo "[3/3] 拉取结果..."
mkdir -p "$LOCAL_ROOT/code/experiments_0404/experiments/posterior"
rsync -avz \
    --include='*/' --include='ppc/**' --include='ppc_all_models.json' --exclude='*' \
    "$SERVER:$REMOTE_ROOT/code/experiments_0404/experiments/posterior/" \
    "$LOCAL_ROOT/code/experiments_0404/experiments/posterior/"

echo ""
echo "=============================================================="
echo "P1-6 完成。产物："
for m in bnn-baseline bnn-data-mono bnn-phy-mono bnn-data-mono-ineq; do
    d="$LOCAL_ROOT/code/experiments_0404/experiments/posterior/$m/ppc"
    for f in ppc_per_case.csv ppc_summary.csv pit_y_${m}.png ppc_coverage_${m}.png; do
        p="$d/$f"
        [ -f "$p" ] && echo "  ✓ $p" || echo "  ✗ 缺 $f"
    done
done
echo "=============================================================="
