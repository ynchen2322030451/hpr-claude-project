# run_sobol_convergence_0404.py
# ============================================================
# SERVER — Sobol convergence curve: S₁ vs N_base for key outputs
#
# Runs Sobol analysis at increasing N_base values to show that
# indices have converged at the canonical N_base used in the paper.
#
# Input:  BNN model checkpoint + scalers
# Output: results/sensitivity/sobol_convergence.csv
#         results/sensitivity/sobol_convergence.png
# ============================================================

import os, sys, json, pickle, logging
from datetime import datetime

import numpy as np
import pandas as pd

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_CODE_ROOT = _SCRIPT_DIR
while _CODE_ROOT and os.path.basename(_CODE_ROOT) != 'code':
    _CODE_ROOT = os.path.dirname(_CODE_ROOT)
_BNN_CONFIG_DIR = os.path.join(_CODE_ROOT, 'experiments_0404', 'config')
_CODE_TOP = os.path.dirname(os.path.dirname(_CODE_ROOT))
_ROOT_0310 = os.path.join(_CODE_TOP, '0310')
for _p in (_SCRIPT_DIR, _CODE_ROOT, _BNN_CONFIG_DIR, _ROOT_0310,
           os.environ.get('HPR_LEGACY_DIR', '')):
    if _p and os.path.isdir(_p) and _p not in sys.path:
        _is_legacy = any(seg in _p for seg in ('/0310', 'hpr_legacy'))
        if _is_legacy:
            sys.path.append(_p)
        else:
            sys.path.insert(0, _p)

import torch
from experiment_config_0404 import (
    INPUT_COLS, OUTPUT_COLS, PRIMARY_SA_OUTPUTS,
    SOBOL_N_BASE, BNN_N_MC_SOBOL,
    SEED, DEVICE,
    FIXED_SPLIT_DIR, EXPR_ROOT_OLD,
    model_artifacts_dir, ensure_dir,
)
from model_registry_0404 import MODELS
from bnn_model import BayesianMLP, mc_predict, get_device, seed_all

logging.basicConfig(level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger(__name__)

_BNN_ROOT = os.path.dirname(_CODE_ROOT)

N_BASE_VALUES = [256, 512, 1024, 2048, 4096, 8192]
N_REPEATS = 20
FOCUS_MODELS = ["bnn-baseline", "bnn-phy-mono"]
FOCUS_OUTPUTS = {
    "iteration2_max_global_stress": "Max stress",
    "iteration2_keff": r"$k_{\mathrm{eff}}$",
}

MODEL_PAPER_LABEL = {
    "bnn-baseline":       "Reference surrogate",
    "bnn-data-mono":      "Data-monotone BNN",
    "bnn-phy-mono":       "Physics-regularized BNN",
    "bnn-data-mono-ineq": "Data+inequality BNN",
}


def _resolve_artifacts(model_id):
    art_dir = model_artifacts_dir(model_id)
    candidates = [
        (os.path.join(art_dir, f"checkpoint_{model_id}.pt"),
         os.path.join(art_dir, f"scalers_{model_id}.pkl")),
        (os.path.join(art_dir, f"checkpoint_{model_id}_fixed.pt"),
         os.path.join(art_dir, f"scalers_{model_id}_fixed.pkl")),
    ]
    for ckpt, sca in candidates:
        if os.path.exists(ckpt) and os.path.exists(sca):
            return ckpt, sca
    raise FileNotFoundError(f"[{model_id}] checkpoint/scaler not found")


def _load_model(ckpt_path, device):
    ckpt = torch.load(ckpt_path, map_location=device)
    hp = ckpt.get("best_params", ckpt.get("hp", {}))
    model = BayesianMLP(
        in_dim=len(INPUT_COLS), out_dim=len(OUTPUT_COLS),
        width=int(hp["width"]), depth=int(hp["depth"]),
        prior_sigma=float(hp.get("prior_sigma", 1.0)),
        homoscedastic=ckpt.get("homoscedastic", False),
    ).to(device)
    model.load_state_dict(ckpt["model_state_dict"])
    model.eval()
    return model


def _load_scalers(scaler_path):
    with open(scaler_path, "rb") as f:
        d = pickle.load(f)
    if isinstance(d, dict):
        return d["sx"], d["sy"]
    return d


def _bnn_predict_mean(model, X_np, sx, sy, device):
    mu_mean, _, _, _, _ = mc_predict(
        model, X_np, sx, sy, device, n_mc=BNN_N_MC_SOBOL
    )
    return mu_mean


def _load_input_bounds():
    candidates = [
        os.path.join(EXPR_ROOT_OLD, "fixed_surrogate_fixed_level2", "meta_stats.json"),
        os.path.join(EXPR_ROOT_OLD, "fixed_surrogate_fixed_base", "meta_stats.json"),
        os.path.join(EXPR_ROOT_OLD, "meta_stats.json"),
    ]
    meta_path = next((p for p in candidates if os.path.exists(p)), None)
    if meta_path is None:
        raise FileNotFoundError("Cannot find meta_stats.json for Sobol input bounds.")
    with open(meta_path) as f:
        meta = json.load(f)
    bounds = []
    for c in INPUT_COLS:
        st = meta["input_stats"][c]
        lo, hi = float(st["min"]), float(st["max"])
        bounds.append((lo, hi))
    return bounds


def _jansen(YA, YB, YABi):
    VY = np.var(np.concatenate([YA, YB]), ddof=1)
    if VY <= 1e-15:
        return 0.0, 0.0
    ST = np.mean((YA - YABi) ** 2) / (2.0 * VY)
    S1 = 1.0 - np.mean((YB - YABi) ** 2) / (2.0 * VY)
    return float(S1), float(ST)


def run():
    seed_all(SEED)
    device = get_device()
    bounds = _load_input_bounds()
    d = len(bounds)

    out_dir = ensure_dir(os.path.join(_BNN_ROOT, "results", "sensitivity"))
    rows = []

    for mid in FOCUS_MODELS:
        logger.info(f"Model: {mid}")
        ckpt_path, scaler_path = _resolve_artifacts(mid)
        model = _load_model(ckpt_path, device)
        sx, sy = _load_scalers(scaler_path)

        for out_col, out_label in FOCUS_OUTPUTS.items():
            out_idx = OUTPUT_COLS.index(out_col)
            logger.info(f"  Output: {out_col}")

            for n_base in N_BASE_VALUES:
                s1_per_input = {c: [] for c in INPUT_COLS}

                for r in range(N_REPEATS):
                    rng = np.random.RandomState(SEED + 1000 * r + out_idx + n_base)
                    A = np.column_stack([rng.uniform(lo, hi, n_base) for lo, hi in bounds])
                    B = np.column_stack([rng.uniform(lo, hi, n_base) for lo, hi in bounds])

                    YA = _bnn_predict_mean(model, A, sx, sy, device)[:, out_idx]
                    YB = _bnn_predict_mean(model, B, sx, sy, device)[:, out_idx]

                    for j in range(d):
                        ABj = A.copy()
                        ABj[:, j] = B[:, j]
                        YABj = _bnn_predict_mean(model, ABj, sx, sy, device)[:, out_idx]
                        s1, st = _jansen(YA, YB, YABj)
                        s1_per_input[INPUT_COLS[j]].append(s1)

                for inp_col in INPUT_COLS:
                    vals = np.array(s1_per_input[inp_col])
                    rows.append({
                        "model_id": mid,
                        "output": out_col,
                        "output_label": out_label,
                        "input": inp_col,
                        "N_base": n_base,
                        "S1_mean": float(np.mean(vals)),
                        "S1_std": float(np.std(vals, ddof=1)) if len(vals) > 1 else 0.0,
                        "S1_ci_lo": float(np.percentile(vals, 5)),
                        "S1_ci_hi": float(np.percentile(vals, 95)),
                        "n_repeats": len(vals),
                    })
                logger.info(f"    N_base={n_base} done ({N_REPEATS} repeats)")

    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(out_dir, "sobol_convergence.csv"), index=False)
    logger.info(f"Saved {len(df)} rows → sobol_convergence.csv")

    # Plot
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        for mid in FOCUS_MODELS:
            for out_col, out_label in FOCUS_OUTPUTS.items():
                sub = df[(df["model_id"] == mid) & (df["output"] == out_col)]
                top_inputs = sub[sub["N_base"] == sub["N_base"].max()].nlargest(3, "S1_mean")["input"].values

                fig, ax = plt.subplots(figsize=(8, 5))
                for inp in top_inputs:
                    s = sub[sub["input"] == inp]
                    ax.errorbar(s["N_base"], s["S1_mean"],
                                yerr=[s["S1_mean"] - s["S1_ci_lo"], s["S1_ci_hi"] - s["S1_mean"]],
                                marker="o", capsize=3, label=inp)
                ax.set_xscale("log", base=2)
                ax.set_xlabel("N_base (Sobol sample size)")
                ax.set_ylabel(r"$S_1$")
                ax.set_title(f"{MODEL_PAPER_LABEL.get(mid, mid)} — {out_label}: Sobol convergence")
                ax.legend(fontsize=8)
                ax.grid(True, alpha=0.3)
                plt.tight_layout()
                fname = f"sobol_convergence_{mid}_{out_col.split('_')[-1]}"
                for ext in ("pdf", "png"):
                    fig.savefig(os.path.join(out_dir, f"{fname}.{ext}"), dpi=200)
                plt.close(fig)
        logger.info("Convergence figures saved")
    except Exception as e:
        logger.warning(f"Figure generation failed: {e}")

    print("\n=== Sobol Convergence Summary (top-3 inputs at max N) ===")
    for mid in FOCUS_MODELS:
        for out_col, out_label in FOCUS_OUTPUTS.items():
            sub = df[(df["model_id"] == mid) & (df["output"] == out_col) & (df["N_base"] == df["N_base"].max())]
            top = sub.nlargest(3, "S1_mean")
            print(f"\n{mid} / {out_label}:")
            for _, r in top.iterrows():
                print(f"  {r['input']:15s}  S1 = {r['S1_mean']:.4f} ± {r['S1_std']:.4f}")


if __name__ == "__main__":
    run()
