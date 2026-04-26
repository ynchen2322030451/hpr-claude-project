#!/bin/bash
# run_all_eval_v3418.sh
# ============================================================
# 自动化评估脚本：对 v3418 数据集上训练的所有模型跑完整评估
#
# 在服务器上运行：
#   bash run_all_eval_v3418.sh 2>&1 | tee /tmp/eval_all_v3418.log
#
# 前提：
#   - bnn-baseline, bnn-phy-mono, bnn-baseline-homo 训练完成
#   - bnn-mf-hybrid 训练完成（或正在完成）
# ============================================================

set -e

# Environment
export HPR_FIXED_SPLIT_DIR=~/Documents/fenics_data/fenics_data/bnn0414/results_v3418/fixed_split
export HPR_CSV_PATH=~/Documents/fenics_data/fenics_data/txt_extract/dataset_v3.csv
export HPR_EXPR_ROOT=~/Documents/fenics_data/fenics_data/bnn0414/results_v3418
export HPR_LEGACY_DIR=~/Documents/fenics_data/fenics_data
export PYTHONUNBUFFERED=1

cd ~/Documents/fenics_data/fenics_data/bnn0414/code/experiments_0404

MODELS_STANDARD="bnn-baseline bnn-phy-mono bnn-baseline-homo"
MODELS_ALL="bnn-baseline bnn-phy-mono bnn-baseline-homo bnn-mf-hybrid"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "============================================================"
echo "  v3418 Full Evaluation Pipeline"
echo "  Started: $(date)"
echo "  MODELS: $MODELS_ALL"
echo "============================================================"

# ── Phase 0: Wait for MF hybrid training if still running ──
echo ""
echo "[Phase 0] Checking MF hybrid training status..."
while pgrep -f "run_train_mf_0404" > /dev/null 2>&1; do
    echo "  MF hybrid still training... waiting 60s ($(date +%H:%M:%S))"
    sleep 60
done
echo "  MF hybrid training done. Proceeding."

# ── Phase 1: Fixed-split evaluation (R², RMSE, PICP, MPIW, CRPS) ──
echo ""
echo "============================================================"
echo "[Phase 1] Fixed-split evaluation for all models"
echo "============================================================"
for MODEL_ID in $MODELS_ALL; do
    echo ""
    echo "--- Evaluating $MODEL_ID (fixed split) ---"
    MODEL_ID=$MODEL_ID SPLIT_TYPE=fixed python evaluation/run_eval_0404.py 2>&1 || {
        echo "[WARN] Eval failed for $MODEL_ID, continuing..."
    }
done

# ── Phase 2: Risk propagation ──
echo ""
echo "============================================================"
echo "[Phase 2] Risk propagation"
echo "============================================================"
for MODEL_ID in $MODELS_ALL; do
    echo ""
    echo "--- Risk propagation: $MODEL_ID ---"
    MODEL_ID=$MODEL_ID python experiments/run_risk_propagation_0404.py 2>&1 || {
        echo "[WARN] Risk propagation failed for $MODEL_ID, continuing..."
    }
done

# ── Phase 3: Sensitivity / Sobol ──
echo ""
echo "============================================================"
echo "[Phase 3] Sensitivity analysis (Sobol)"
echo "============================================================"
for MODEL_ID in bnn-baseline bnn-phy-mono bnn-mf-hybrid; do
    echo ""
    echo "--- Sensitivity: $MODEL_ID ---"
    MODEL_ID=$MODEL_ID python experiments/run_sensitivity_0404.py 2>&1 || {
        echo "[WARN] Sensitivity failed for $MODEL_ID, continuing..."
    }
done

# ── Phase 4: Sobol convergence ──
echo ""
echo "============================================================"
echo "[Phase 4] Sobol convergence"
echo "============================================================"
for MODEL_ID in bnn-baseline bnn-mf-hybrid; do
    echo ""
    echo "--- Sobol convergence: $MODEL_ID ---"
    MODEL_ID=$MODEL_ID python experiments/run_sobol_convergence_0404.py 2>&1 || {
        echo "[WARN] Sobol convergence failed for $MODEL_ID, continuing..."
    }
done

# ── Phase 5: Generalization / OOD ──
echo ""
echo "============================================================"
echo "[Phase 5] Generalization (OOD)"
echo "============================================================"
for MODEL_ID in bnn-baseline bnn-phy-mono bnn-mf-hybrid; do
    echo ""
    echo "--- Generalization: $MODEL_ID ---"
    MODEL_ID=$MODEL_ID python experiments/run_generalization_0404.py 2>&1 || {
        echo "[WARN] Generalization failed for $MODEL_ID, continuing..."
    }
done

# ── Phase 6: Speed benchmark ──
echo ""
echo "============================================================"
echo "[Phase 6] Computational speed benchmark"
echo "============================================================"
for MODEL_ID in bnn-baseline bnn-mf-hybrid; do
    echo ""
    echo "--- Speed: $MODEL_ID ---"
    FORCE=1 MODEL_ID=$MODEL_ID python experiments/run_speed_0404.py 2>&1 || {
        echo "[WARN] Speed benchmark failed for $MODEL_ID, continuing..."
    }
done

# ── Phase 7: Posterior calibration ──
echo ""
echo "============================================================"
echo "[Phase 7] Posterior calibration (MCMC)"
echo "============================================================"
for MODEL_ID in bnn-baseline bnn-phy-mono bnn-mf-hybrid; do
    echo ""
    echo "--- Posterior: $MODEL_ID ---"
    MODEL_ID=$MODEL_ID python experiments/run_posterior_0404.py 2>&1 || {
        echo "[WARN] Posterior failed for $MODEL_ID, continuing..."
    }
done

echo ""
echo "============================================================"
echo "  ALL EVALUATIONS COMPLETE"
echo "  Finished: $(date)"
echo "============================================================"

# ── Summary: list all output artifacts ──
echo ""
echo "=== Output artifacts ==="
find $HPR_EXPR_ROOT -type f \( -name 'metrics_*.json' -o -name '*_summary.csv' -o -name '*_manifest.json' \) | sort
