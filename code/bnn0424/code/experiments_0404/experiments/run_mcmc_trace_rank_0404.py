# run_mcmc_trace_rank_0404.py
# ============================================================
# LOCAL ONLY — MCMC trace + rank plots for representative cases
#
# Reads chain .npz from posterior diagnostics, produces:
#   - trace plots (all chains overlaid) for 3 representative cases
#   - rank plots (Vehtari 2021 style) for same cases
#
# Input:  posterior/<model>/diagnostics/chains/case_*.npz
# Output: results/posterior/trace_<model>_case_*.png
#         results/posterior/rank_<model>_case_*.png
# ============================================================

import os, sys, logging
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_CODE_ROOT = _SCRIPT_DIR
while _CODE_ROOT and os.path.basename(_CODE_ROOT) != 'code':
    _CODE_ROOT = os.path.dirname(_CODE_ROOT)
_BNN_CONFIG_DIR = os.path.join(_CODE_ROOT, 'experiments_0404', 'config')
for _p in (_SCRIPT_DIR, _CODE_ROOT, _BNN_CONFIG_DIR):
    if _p and os.path.isdir(_p) and _p not in sys.path:
        sys.path.insert(0, _p)

from experiment_config_0404 import ensure_dir

logging.basicConfig(level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger(__name__)

_BNN_ROOT = os.path.dirname(_CODE_ROOT)

MODELS_TO_PLOT = ["bnn-baseline", "bnn-phy-mono"]
REPRESENTATIVE_CASES = [0, 6, 12]  # low/near/high stress categories
CHAIN_COLORS = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"]

MODEL_PAPER_LABEL = {
    "bnn-baseline":       "Reference surrogate",
    "bnn-data-mono":      "Data-monotone BNN",
    "bnn-phy-mono":       "Physics-regularized BNN",
    "bnn-data-mono-ineq": "Data+inequality BNN",
}


def load_chain(model_id, case_idx):
    chain_dir = os.path.join(
        _CODE_ROOT, "experiments_0404", "experiments", "posterior",
        model_id, "diagnostics", "chains"
    )
    p = os.path.join(chain_dir, f"case_{case_idx:02d}.npz")
    if not os.path.exists(p):
        return None
    d = np.load(p, allow_pickle=True)
    return {
        "chains": d["chains"],           # (n_chains, n_steps, n_params)
        "param_names": list(d["param_names"]),
        "category": str(d["category"]),
        "accept": d["per_chain_accept"],
    }


def plot_trace(chain_data, model_id, case_idx, out_dir):
    chains = chain_data["chains"]
    param_names = chain_data["param_names"]
    n_chains, n_steps, n_params = chains.shape
    cat = chain_data["category"]

    fig, axes = plt.subplots(n_params, 1, figsize=(10, 2.5 * n_params), sharex=True)
    if n_params == 1:
        axes = [axes]

    for j, (ax, pname) in enumerate(zip(axes, param_names)):
        for c in range(n_chains):
            ax.plot(chains[c, :, j], alpha=0.6, lw=0.5, color=CHAIN_COLORS[c % len(CHAIN_COLORS)],
                    label=f"Chain {c+1}" if j == 0 else None)
        ax.set_ylabel(pname, fontsize=9)
        ax.tick_params(labelsize=8)

    axes[-1].set_xlabel("MCMC step")
    axes[0].legend(fontsize=8, ncol=n_chains, loc="upper right")
    fig.suptitle(f"{MODEL_PAPER_LABEL.get(model_id, model_id)} — Case {case_idx} ({cat}): trace plot", fontsize=11)
    plt.tight_layout()
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(out_dir, f"trace_{model_id}_case{case_idx:02d}.{ext}"), dpi=200)
    plt.close(fig)


def plot_rank(chain_data, model_id, case_idx, out_dir):
    chains = chain_data["chains"]
    param_names = chain_data["param_names"]
    n_chains, n_steps, n_params = chains.shape
    cat = chain_data["category"]

    fig, axes = plt.subplots(n_params, 1, figsize=(10, 2.5 * n_params), sharex=True)
    if n_params == 1:
        axes = [axes]

    for j, (ax, pname) in enumerate(zip(axes, param_names)):
        all_vals = chains[:, :, j].flatten()
        ranks = np.empty_like(all_vals)
        order = all_vals.argsort()
        ranks[order] = np.arange(len(all_vals))

        n_bins = 20
        for c in range(n_chains):
            chain_ranks = ranks[c * n_steps:(c + 1) * n_steps]
            ax.hist(chain_ranks, bins=n_bins, alpha=0.5,
                    color=CHAIN_COLORS[c % len(CHAIN_COLORS)],
                    label=f"Chain {c+1}" if j == 0 else None)

        expected = n_steps / n_bins
        ax.axhline(expected, color="k", ls="--", lw=0.8, alpha=0.5)
        ax.set_ylabel(pname, fontsize=9)
        ax.tick_params(labelsize=8)

    axes[-1].set_xlabel("Rank")
    axes[0].legend(fontsize=8, ncol=n_chains, loc="upper right")
    fig.suptitle(f"{MODEL_PAPER_LABEL.get(model_id, model_id)} — Case {case_idx} ({cat}): rank plot", fontsize=11)
    plt.tight_layout()
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(out_dir, f"rank_{model_id}_case{case_idx:02d}.{ext}"), dpi=200)
    plt.close(fig)


def run():
    out_dir = ensure_dir(os.path.join(_BNN_ROOT, "results", "posterior"))

    for mid in MODELS_TO_PLOT:
        for case_idx in REPRESENTATIVE_CASES:
            data = load_chain(mid, case_idx)
            if data is None:
                logger.warning(f"  [{mid}] case_{case_idx:02d}.npz not found, skip")
                continue

            logger.info(f"  [{mid}] case {case_idx} ({data['category']}): "
                        f"{data['chains'].shape[0]} chains × {data['chains'].shape[1]} steps, "
                        f"accept = {data['accept']}")
            plot_trace(data, mid, case_idx, out_dir)
            plot_rank(data, mid, case_idx, out_dir)
            logger.info(f"    trace + rank plots saved")

    logger.info("Done.")


if __name__ == "__main__":
    run()
