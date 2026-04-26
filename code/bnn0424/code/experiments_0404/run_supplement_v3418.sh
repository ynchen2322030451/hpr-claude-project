#!/bin/bash
# run_supplement_v3418.sh
# ============================================================
# v3418 补充实验：5-seed repeat + external baselines + physics
#
# 在服务器上运行：
#   cd ~/Documents/fenics_data/fenics_data/bnn0414/code/experiments_0404
#   nohup bash run_supplement_v3418.sh > /tmp/supplement_v3418.log 2>&1 &
#
# 前提：
#   - v3418 基础训练和评估已完成 (run_all_eval_v3418.sh)
#   - conda env: nn_env (BNN), pytorch-env (external baselines)
# ============================================================

set -e

# ── Conda ──
source /opt/software/miniconda3/etc/profile.d/conda.sh
conda activate pytorch-env

# ── Environment (same as run_all_eval_v3418.sh) ──
export HPR_FIXED_SPLIT_DIR=~/Documents/fenics_data/fenics_data/bnn0414/results_v3418/fixed_split
export HPR_CSV_PATH=~/Documents/fenics_data/fenics_data/txt_extract/dataset_v3.csv
export HPR_EXPR_ROOT=~/Documents/fenics_data/fenics_data/bnn0414/results_v3418
export HPR_LEGACY_DIR=~/Documents/fenics_data/fenics_data
export PYTHONUNBUFFERED=1

SCRIPT_DIR=~/Documents/fenics_data/fenics_data/bnn0414/code/experiments_0404
cd "$SCRIPT_DIR"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "============================================================"
echo "  v3418 Supplementary Experiments"
echo "  Started: $(date)"
echo "============================================================"

# ════════════════════════════════════════════════════════════
# P1: 5-seed Repeat Training + Eval (bnn-baseline & bnn-phy-mono)
# ════════════════════════════════════════════════════════════
echo ""
echo "============================================================"
echo "[P1] 5-seed repeat training (bnn-baseline, bnn-phy-mono)"
echo "============================================================"

for MODEL_ID in bnn-baseline bnn-phy-mono; do
    echo ""
    echo "--- Training $MODEL_ID (repeat, seeds 2026-2030) ---"
    MODEL_ID=$MODEL_ID SPLIT_TYPE=repeat FORCE_RETRAIN=0 \
        python training/run_train_0404.py 2>&1 || {
        echo "[WARN] Repeat training failed for $MODEL_ID"
    }
done

echo ""
echo "[P1b] 5-seed repeat evaluation"
for MODEL_ID in bnn-baseline bnn-phy-mono; do
    echo ""
    echo "--- Eval $MODEL_ID (repeat) ---"
    MODEL_ID=$MODEL_ID EVAL_MODE=repeat \
        python evaluation/run_eval_0404.py 2>&1 || {
        echo "[WARN] Repeat eval failed for $MODEL_ID"
    }
done

echo ""
echo "[P1c] Repeat summary table"
python experiments/run_repeat_summary_table_0404.py 2>&1 || {
    echo "[WARN] Repeat summary table failed"
}

# ════════════════════════════════════════════════════════════
# P2: External Baselines (MC-Dropout + Deep Ensemble)
# ════════════════════════════════════════════════════════════
echo ""
echo "============================================================"
echo "[P2] External baselines on v3418 split"
echo "============================================================"

# External baselines (same pytorch-env)
for MODEL_ID in mc-dropout deep-ensemble; do
    echo ""
    echo "--- External baseline: $MODEL_ID ---"
    MODEL_ID=$MODEL_ID python experiments/run_external_baselines_0404.py 2>&1 || {
        echo "[WARN] External baseline failed for $MODEL_ID"
    }
done

# Run external baseline UQ comparison (scoring rules)
echo ""
echo "[P2b] External baseline UQ scoring"
python experiments/run_external_baseline_uq_0404.py 2>&1 || {
    echo "[WARN] External baseline UQ scoring failed"
}


# ════════════════════════════════════════════════════════════
# P3: Physics Consistency (monotonicity + inequality)
# ════════════════════════════════════════════════════════════
echo ""
echo "============================================================"
echo "[P3] Physics consistency checks"
echo "============================================================"

for MODEL_ID in bnn-baseline bnn-phy-mono bnn-baseline-homo bnn-mf-hybrid; do
    echo ""
    echo "--- Monotonicity: $MODEL_ID ---"
    MODEL_ID=$MODEL_ID python experiments/run_monotonicity_violation_0404.py 2>&1 || {
        echo "[WARN] Monotonicity check failed for $MODEL_ID"
    }
done

echo ""
echo "[P3b] Physics consistency (full)"
python experiments/run_physics_consistency_0404.py 2>&1 || {
    echo "[WARN] Physics consistency failed"
}

# ════════════════════════════════════════════════════════════
# P4: Uncertainty Decomposition
# ════════════════════════════════════════════════════════════
echo ""
echo "============================================================"
echo "[P4] Uncertainty decomposition (epistemic vs aleatoric)"
echo "============================================================"

for MODEL_ID in bnn-baseline bnn-phy-mono; do
    echo ""
    echo "--- Uncertainty decomposition: $MODEL_ID ---"
    MODEL_ID=$MODEL_ID python experiments/run_uncertainty_decomposition_0404.py 2>&1 || {
        echo "[WARN] Uncertainty decomposition failed for $MODEL_ID"
    }
done

# ════════════════════════════════════════════════════════════
# P5: Calibration scoring rules (CRPS, NLL, PIT, etc.)
# ════════════════════════════════════════════════════════════
echo ""
echo "============================================================"
echo "[P5] Calibration & scoring rules"
echo "============================================================"

python experiments/run_calibration_0404.py 2>&1 || {
    echo "[WARN] Calibration scoring failed"
}

echo ""
echo "============================================================"
echo "  ALL SUPPLEMENTARY EXPERIMENTS COMPLETE"
echo "  Finished: $(date)"
echo "============================================================"

# ── Summary ──
echo ""
echo "=== New output artifacts ==="
find $HPR_EXPR_ROOT -newer /tmp/supplement_v3418.log -type f \
    \( -name '*.csv' -o -name '*.json' \) 2>/dev/null | sort | head -50
