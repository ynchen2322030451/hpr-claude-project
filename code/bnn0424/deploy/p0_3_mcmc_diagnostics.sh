#!/bin/bash
# =============================================================================
# P0-3: MCMC 诊断 — push + run + pull
# =============================================================================
#
# 用途：
#   1. 把 run_posterior_diagnostics_0404.py 推到 tjzs 服务器
#   2. 服务器上用多链跑 benchmark 并产出 rhat / ESS / full chains
#   3. 把结果拉回本地 code/experiments/posterior/<model>/diagnostics/
#
# 使用：
#   bash deploy/p0_3_mcmc_diagnostics.sh            # 默认 4 模型全跑
#   MODEL=bnn-phy-mono bash deploy/p0_3_mcmc_diagnostics.sh   # 单模型
#   DIAG_N_CHAINS=2 bash deploy/p0_3_mcmc_diagnostics.sh      # 降低链数
#
# 资源预估（每 case 单模型）：
#   1 case × 4 chains × 8000 iter × mc_posterior=20 ≈ 4–6 min on 3090
#   18 cases × 4 models ≈ 5–8 小时
# =============================================================================

set -eo pipefail

SERVER="tjzs@100.68.18.85"
LOCAL_ROOT="/Users/yinuo/Projects/hpr-claude-project/code/bnn0414"
REMOTE_ROOT="/home/tjzs/Documents/fenics_data/hpr_surrogate/hpr-claude-project/code/bnn0414"

MODEL="${MODEL:-all}"
DIAG_N_CHAINS="${DIAG_N_CHAINS:-4}"
CONDA_ENV="${CONDA_ENV:-pytorch-env}"
LEGACY_DIR="${LEGACY_DIR:-/home/tjzs/Documents/fenics_data/hpr_surrogate/hpr-claude-project/code/0310}"

echo "=============================================================="
echo "P0-3 MCMC Diagnostics"
echo "  MODEL          = $MODEL"
echo "  DIAG_N_CHAINS  = $DIAG_N_CHAINS"
echo "  CONDA_ENV      = $CONDA_ENV"
echo "  SERVER         = $SERVER"
echo "=============================================================="

# ── Step 1: push 脚本 ─────────────────────────────────────────
echo ""
echo "[1/3] 推送脚本到服务器..."
rsync -avz --exclude='__pycache__' \
    "$LOCAL_ROOT/code/experiments_0404/experiments/run_posterior_diagnostics_0404.py" \
    "$SERVER:$REMOTE_ROOT/code/experiments_0404/experiments/"

# ── Step 2: server-side run ───────────────────────────────────
echo ""
echo "[2/3] 服务器端执行..."
ssh "$SERVER" bash -s <<EOF
set -e
cd "$REMOTE_ROOT/code/experiments_0404"
export HPR_ENV=server
export HPR_LEGACY_DIR=$LEGACY_DIR
export MODEL_ID=$MODEL
export DIAG_N_CHAINS=$DIAG_N_CHAINS
echo "[server] cwd=\$(pwd), MODEL_ID=\$MODEL_ID, N_CHAINS=\$DIAG_N_CHAINS"
conda run -n $CONDA_ENV python experiments/run_posterior_diagnostics_0404.py
EOF

# ── Step 3: pull 结果 ─────────────────────────────────────────
echo ""
echo "[3/3] 拉取结果到本地..."
if [ "$MODEL" = "all" ]; then
    MODELS_TO_PULL=("bnn-baseline" "bnn-data-mono" "bnn-phy-mono" "bnn-data-mono-ineq")
else
    MODELS_TO_PULL=("$MODEL")
fi

for MID in "${MODELS_TO_PULL[@]}"; do
    echo "  → $MID"
    mkdir -p "$LOCAL_ROOT/code/experiments/posterior/$MID/diagnostics"
    rsync -avz \
        "$SERVER:$REMOTE_ROOT/code/experiments_0404/experiments/posterior/$MID/diagnostics/" \
        "$LOCAL_ROOT/code/experiments/posterior/$MID/diagnostics/"
done

# cross-model summary
rsync -avz \
    "$SERVER:$REMOTE_ROOT/code/experiments_0404/experiments/posterior/diagnostics_all_models.json" \
    "$LOCAL_ROOT/code/experiments/posterior/" 2>/dev/null || true

echo ""
echo "=============================================================="
echo "P0-3 完成。产物："
for MID in "${MODELS_TO_PULL[@]}"; do
    CSV="$LOCAL_ROOT/code/experiments/posterior/$MID/diagnostics/mcmc_diagnostics.csv"
    if [ -f "$CSV" ]; then
        echo "  ✓ $CSV ($(wc -l < "$CSV") lines)"
    else
        echo "  ✗ 缺失 $CSV"
    fi
done
echo "=============================================================="
