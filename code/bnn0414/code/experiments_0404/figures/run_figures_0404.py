"""
run_figures_0404.py  --  BNN 0414 figure generation (skeleton)

PLACEHOLDER: figure functions are defined but not yet implemented.
Actual plotting code will be adapted after BNN training results are available.

Usage (environment variable control):
    python run_figures_0404.py                        # list all figures
    FIG_SET=main    python run_figures_0404.py        # main-text figures
    FIG_SET=appendix python run_figures_0404.py       # appendix figures
    FIG_LIST=fig1,fig2 python run_figures_0404.py     # selected figures only

Output: experiments_0404/figures/  (.pdf .svg .png)
"""

import json, os, sys, warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

warnings.filterwarnings("ignore")

# -- path setup ----------------------------------------------------------------
_HERE      = os.path.dirname(os.path.abspath(__file__))   # figures/
_EXPR_DIR  = os.path.dirname(_HERE)                       # experiments_0404/
_BNN_CODE  = os.path.dirname(_EXPR_DIR)                   # bnn0414/code/
_BNN_ROOT  = os.path.dirname(_BNN_CODE)                   # bnn0414/
_CODE_TOP  = os.path.dirname(_BNN_ROOT)                   # code/
for _p in [os.path.join(_EXPR_DIR, "config"), _BNN_CODE, _EXPR_DIR]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from experiment_config_0404 import (
    EXPR_ROOT_0404, EXPR_ROOT_OLD,
    PRIMARY_OUTPUTS, PRIMARY_STRESS_OUTPUT, PRIMARY_STRESS_THRESHOLD,
    INPUT_COLS, OUTPUT_COLS, PARAM_META, OUTPUT_META,
    BNN_N_MC_EVAL,
    model_artifacts_dir, model_fixed_eval_dir, experiment_dir, ensure_dir,
)
from model_registry_0404 import MODELS, list_models

# -- output directory ----------------------------------------------------------
FIG_DIR = ensure_dir(os.path.join(EXPR_ROOT_0404, "figures"))

# -- model display labels ------------------------------------------------------
MODEL_LABELS = {
    "bnn-baseline":       "BNN Baseline",
    "bnn-data-mono":      "BNN + Data Monotone",
    "bnn-phy-mono":       "BNN + Physics Monotone",
    "bnn-data-mono-ineq": "BNN + Full Constraints",
}

PRIMARY_LABELS = {
    "iteration2_keff":              r"$k_\mathrm{eff}$",
    "iteration2_max_fuel_temp":     "Max fuel\ntemp (K)",
    "iteration2_max_monolith_temp": "Max monolith\ntemp (K)",
    "iteration2_max_global_stress": "Max global\nstress (MPa)",
    "iteration2_wall2":             "Wall\nexpansion (mm)",
}

INPUT_LABELS = {m: PARAM_META[m]["label"] for m in INPUT_COLS}

# -- color scheme --------------------------------------------------------------
BLUE   = "#2E86AB"; ORANGE = "#E76F51"; GREEN  = "#57A773"
GRAY   = "#888888"; RED    = "#C0392B"; PURPLE = "#9B5DE5"

MODEL_COLORS = {
    "bnn-baseline":       BLUE,
    "bnn-data-mono":      ORANGE,
    "bnn-phy-mono":       GREEN,
    "bnn-data-mono-ineq": PURPLE,
}

plt.rcParams.update({
    "font.family": "sans-serif", "font.size": 10,
    "axes.spines.top": False, "axes.spines.right": False,
    "figure.dpi": 150,
})

# -- helper functions ----------------------------------------------------------

def savefig(fig, name):
    """Save figure to FIG_DIR in pdf/svg/png."""
    for ext in ("pdf", "svg", "png"):
        p = os.path.join(FIG_DIR, f"{name}.{ext}")
        kw = {"bbox_inches": "tight"}
        if ext == "png":
            kw["dpi"] = 150
        fig.savefig(p, **kw)
    print(f"  saved  {name}  [pdf/svg/png]")
    plt.close(fig)


def clean_ax(ax):
    """Remove top/right spines."""
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def _load_test_preds(model_id):
    """Load BNN test predictions.

    BNN eval stores MC-sampled predictions. Expected file structure:
        models/<model_id>/fixed_eval/test_predictions_<model_id>.json
    with keys: mu_te, sigma_te, y_te_true
       - mu_te:    (N, n_outputs)  posterior predictive mean
       - sigma_te: (N, n_outputs)  posterior predictive std
       - y_te_true: (N, n_outputs) ground truth

    Returns (mu, sigma, y_true) as numpy arrays, or (None, None, None).
    """
    eval_dir = model_fixed_eval_dir(model_id)
    p = os.path.join(eval_dir, f"test_predictions_{model_id}.json")
    if not os.path.exists(p):
        print(f"    [WARN] not found: {p}")
        return None, None, None
    with open(p) as f:
        d = json.load(f)
    mu    = np.array(d["mu_te"])
    sigma = np.array(d["sigma_te"])
    y     = np.array(d["y_te_true"])
    return mu, sigma, y


def _load_per_dim_metrics(model_id):
    """Load per-output metrics CSV for a BNN model."""
    eval_dir = model_fixed_eval_dir(model_id)
    p = os.path.join(eval_dir, f"paper_metrics_per_dim_{model_id}.csv")
    if not os.path.exists(p):
        print(f"    [WARN] not found: {p}")
        return None
    return pd.read_csv(p)


# ==============================================================================
# Fig 1  --  BNN accuracy: predicted vs true + residual
# ==============================================================================
def fig1_bnn_accuracy():
    """Scatter: predicted vs true for all BNN variants on primary outputs."""
    print("[SKIP] fig1_bnn_accuracy: not yet implemented -- run after BNN training")


# ==============================================================================
# Fig 2  --  Risk comparison across BNN variants
# ==============================================================================
def fig2_risk_comparison():
    """Threshold exceedance P(stress > 131 MPa) across sigma_k levels."""
    print("[SKIP] fig2_risk_comparison: not yet implemented -- run after BNN training")


# ==============================================================================
# Fig 3  --  Sobol sensitivity indices
# ==============================================================================
def fig3_sobol():
    """Sobol first-order and total-order indices with CI bars."""
    print("[SKIP] fig3_sobol: not yet implemented -- run after BNN training")


# ==============================================================================
# Fig 4  --  Posterior contraction / parameter recovery
# ==============================================================================
def fig4_posterior():
    """Prior vs posterior marginal for calibrated parameters."""
    print("[SKIP] fig4_posterior: not yet implemented -- run after BNN training")


# ==============================================================================
# Fig 5  --  Uncertainty decomposition (BNN-specific)
# ==============================================================================
def fig5_uncertainty_decomposition():
    """Epistemic vs aleatoric uncertainty decomposition.

    BNN naturally decomposes predictive uncertainty:
        - Epistemic: variance across MC weight samples (model uncertainty)
        - Aleatoric: mean of per-sample predicted variance (data noise)
    This figure shows the decomposition for primary outputs.

    NOTE: This is a BNN-specific figure not present in the HeteroMLP pipeline.
    """
    print("[SKIP] fig5_uncertainty_decomposition: not yet implemented -- run after BNN training")


# ==============================================================================
# Figure registry
# ==============================================================================
MAIN_FIGS = {
    "fig1": ("BNN accuracy",                fig1_bnn_accuracy),
    "fig2": ("Risk comparison",             fig2_risk_comparison),
    "fig3": ("Sobol sensitivity",           fig3_sobol),
    "fig4": ("Posterior contraction",        fig4_posterior),
    "fig5": ("Uncertainty decomposition",   fig5_uncertainty_decomposition),
}

APPENDIX_FIGS = {
    # Appendix figures to be added as BNN results become available
}

ALL_FIGS = {**MAIN_FIGS, **APPENDIX_FIGS}


# ==============================================================================
# Main
# ==============================================================================
if __name__ == "__main__":
    fig_set  = os.environ.get("FIG_SET", "all").lower()
    fig_list = os.environ.get("FIG_LIST", "")

    # Determine which figures to generate
    if fig_list:
        keys = [k.strip() for k in fig_list.split(",") if k.strip()]
    elif fig_set == "main":
        keys = list(MAIN_FIGS.keys())
    elif fig_set == "appendix":
        keys = list(APPENDIX_FIGS.keys())
    else:
        keys = list(ALL_FIGS.keys())

    print("=" * 60)
    print("  BNN 0414 -- Figure Generation (skeleton)")
    print(f"  FIG_DIR:  {FIG_DIR}")
    print(f"  figures:  {keys}")
    print("=" * 60)

    for k in keys:
        if k not in ALL_FIGS:
            print(f"  [ERR] unknown figure key: {k}")
            continue
        label, func = ALL_FIGS[k]
        print(f"\n--- {k}: {label} ---")
        func()

    print("\n[DONE] BNN figure skeleton complete.")
