# run_model_misspecification_0404.py
# ============================================================
# Model misspecification sensitivity test (Phase 1.7.3)
#
# Train BNN on a subset of data (e.g., 80%), then run posterior
# calibration using held-out samples NOT in the training set as
# "observations". Compare posterior coverage vs the standard
# synthetic-observation pipeline to assess robustness to
# model-form mismatch (held-out data acts as a mild model
# misspecification probe).
#
# Usage (on server, pytorch-env):
#   python run_model_misspecification_0404.py
#
# Output:
#   results/posterior/misspecification_test/
#     benchmark_summary.csv
#     coverage_comparison.csv
# ============================================================

import os, sys, json, logging
import numpy as np
import pandas as pd
import torch

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_CODE_ROOT = _SCRIPT_DIR
while _CODE_ROOT and os.path.basename(_CODE_ROOT) != 'code':
    _CODE_ROOT = os.path.dirname(_CODE_ROOT)
_BNN_CONFIG_DIR = os.path.join(_CODE_ROOT, 'experiments_0404', 'config')
for _p in (_SCRIPT_DIR, _CODE_ROOT, _BNN_CONFIG_DIR):
    if _p and os.path.isdir(_p) and _p not in sys.path:
        sys.path.insert(0, _p)

from experiment_config_0404 import (
    INPUT_COLS, OUTPUT_COLS, PRIMARY_OUTPUTS,
    SEED, DEVICE, FIXED_SPLIT_DIR, model_dir, ensure_dir,
)
from bnn_model import BayesianMLP, mc_predict, get_device, seed_all

logging.basicConfig(level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger(__name__)

_BNN_ROOT = os.path.dirname(_CODE_ROOT)
MODEL_ID = "bnn-phy-mono"
NOISE_FRAC = 0.02
N_MCMC = 5000
N_BURNIN = 1000
N_BENCHMARK = 18


def load_data():
    """Load the fixed-split test data as candidate 'observations'."""
    split_dir = FIXED_SPLIT_DIR
    X_test = pd.read_csv(os.path.join(split_dir, "X_test.csv")).values
    Y_test = pd.read_csv(os.path.join(split_dir, "Y_test.csv")).values
    return X_test, Y_test


def select_benchmark_cases(Y_test, n_cases=N_BENCHMARK):
    """Select benchmark cases stratified by stress level.

    Use a different selection from the standard pipeline to ensure
    these are genuinely 'unseen' by the calibration design.
    """
    stress_idx = OUTPUT_COLS.index("iteration2_max_global_stress")
    stress_vals = Y_test[:, stress_idx]

    sorted_idx = np.argsort(stress_vals)
    n = len(sorted_idx)

    # Pick 6 low, 6 mid, 6 high — offset from standard selection
    n_per = n_cases // 3
    low_candidates = sorted_idx[:n // 3]
    mid_candidates = sorted_idx[n // 3: 2 * n // 3]
    high_candidates = sorted_idx[2 * n // 3:]

    rng = np.random.RandomState(SEED + 999)
    low_sel = rng.choice(low_candidates, n_per, replace=False)
    mid_sel = rng.choice(mid_candidates, n_per, replace=False)
    high_sel = rng.choice(high_candidates, n_per, replace=False)

    return np.concatenate([low_sel, mid_sel, high_sel])


def run():
    """Main entry point.

    NOTE: This script requires:
    1. A BNN checkpoint trained on the full dataset (standard)
    2. The posterior calibration machinery from run_posterior_0404.py

    The key comparison is:
    - Standard: synthetic obs = HF_true + 2% noise (closed loop)
    - Misspec: held-out obs = actual test-set HF outputs + 2% noise
      (these are from the SAME simulator, but the BNN hasn't seen them
       during training, so there's a mild surrogate-truth mismatch)

    If coverage drops significantly, it signals sensitivity to
    model misspecification. If coverage holds, it strengthens the
    closed-loop validation.
    """
    logger.info("Model misspecification test")
    logger.info("This script provides the framework; adapt run_posterior_0404.py")
    logger.info("to use held-out test observations instead of synthetic ones.")
    logger.info("")
    logger.info("Key steps:")
    logger.info("1. Load standard BNN checkpoint (trained on full data)")
    logger.info("2. Select 18 benchmark cases from test set")
    logger.info("3. Use their TRUE HF outputs + 2%% noise as observations")
    logger.info("4. Run MCMC posterior calibration")
    logger.info("5. Compare 90%%-CI coverage vs standard synthetic pipeline")
    logger.info("")
    logger.info("Expected result: coverage should be comparable to 0.861")
    logger.info("because the test data comes from the same HF simulator.")
    logger.info("Any significant drop would indicate surrogate-truth mismatch.")

    X_test, Y_test = load_data()
    case_idx = select_benchmark_cases(Y_test)

    logger.info(f"Selected {len(case_idx)} benchmark cases from test set")

    stress_idx = OUTPUT_COLS.index("iteration2_max_global_stress")
    stress_vals = Y_test[case_idx, stress_idx]
    logger.info(f"Stress range: {stress_vals.min():.1f} - {stress_vals.max():.1f} MPa")

    out_dir = ensure_dir(os.path.join(_BNN_ROOT, "results", "posterior",
                                       "misspecification_test"))

    np.save(os.path.join(out_dir, "case_indices.npy"), case_idx)
    logger.info(f"Case indices saved to {out_dir}/case_indices.npy")
    logger.info("")
    logger.info("To complete: integrate with run_posterior_0404.py's MCMC loop,")
    logger.info("replacing synthetic observations with Y_test[case_idx] + noise.")


if __name__ == "__main__":
    run()
