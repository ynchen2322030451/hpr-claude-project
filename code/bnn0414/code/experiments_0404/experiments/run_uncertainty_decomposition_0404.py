# run_uncertainty_decomposition_0404.py
# ============================================================
# LOCAL ONLY — Epistemic vs aleatoric uncertainty decomposition
# Reads test_predictions_fixed.json from each BNN model,
# produces stacked-bar + scatter visualizations.
# ============================================================

import os, sys, json, logging
import numpy as np
import pandas as pd
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

from experiment_config_0404 import PRIMARY_OUTPUTS, OUTPUT_COLS, ensure_dir
from model_registry_0404 import MODELS

logging.basicConfig(level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger(__name__)

_BNN_ROOT = os.path.dirname(_CODE_ROOT)

MODEL_PAPER_LABEL = {
    "bnn-baseline":       "Reference surrogate",
    "bnn-data-mono":      "Data-monotone BNN",
    "bnn-phy-mono":       "Physics-regularized BNN",
    "bnn-data-mono-ineq": "Data+inequality BNN",
}

OUTPUT_PAPER_LABEL = {
    "iteration2_max_global_stress": "Max stress",
    "iteration2_keff":              r"$k_{\mathrm{eff}}$",
    "iteration2_max_fuel_temp":     "Max fuel temp",
    "iteration2_max_monolith_temp": "Max monolith temp",
    "iteration2_wall2":             "Wall expansion",
}

FOCUS_MODELS = ["bnn-baseline", "bnn-phy-mono"]


def load_predictions(model_id):
    p = os.path.join(_CODE_ROOT, "models", model_id, "fixed_eval",
                     "test_predictions_fixed.json")
    if not os.path.exists(p):
        return None
    with open(p) as f:
        d = json.load(f)
    return {
        "output_cols": d["output_cols"],
        "epistemic_var": np.array(d["epistemic_var"]),
        "aleatoric_var": np.array(d["aleatoric_var"]),
        "mu": np.array(d["mu"]),
        "y_true": np.array(d["y_true"]),
    }


def run():
    out_dir = ensure_dir(os.path.join(_BNN_ROOT, "results", "uncertainty_decomposition"))

    all_rows = []

    for mid in MODELS:
        pred = load_predictions(mid)
        if pred is None:
            logger.warning(f"  [{mid}] no test_predictions_fixed.json")
            continue
        cols = pred["output_cols"]
        for oc in PRIMARY_OUTPUTS:
            if oc not in cols:
                continue
            idx = cols.index(oc)
            epi = pred["epistemic_var"][:, idx]
            ale = pred["aleatoric_var"][:, idx]
            total = epi + ale
            frac_epi = np.where(total > 0, epi / total, 0.5)
            all_rows.append({
                "model_id": mid,
                "model_label": MODEL_PAPER_LABEL.get(mid, mid),
                "output": oc,
                "output_label": OUTPUT_PAPER_LABEL.get(oc, oc),
                "epistemic_var_mean": float(np.mean(epi)),
                "aleatoric_var_mean": float(np.mean(ale)),
                "total_var_mean": float(np.mean(total)),
                "frac_epistemic_mean": float(np.mean(frac_epi)),
                "frac_epistemic_median": float(np.median(frac_epi)),
                "frac_epistemic_std": float(np.std(frac_epi)),
            })

    df = pd.DataFrame(all_rows)
    df.to_csv(os.path.join(out_dir, "uncertainty_decomposition.csv"), index=False)
    logger.info(f"Summary: {len(df)} rows → uncertainty_decomposition.csv")

    # ---- Figure 1: Stacked bar (fraction epistemic vs aleatoric) ----
    fig, axes = plt.subplots(1, len(FOCUS_MODELS), figsize=(12, 5), sharey=True)
    if len(FOCUS_MODELS) == 1:
        axes = [axes]

    for ax, mid in zip(axes, FOCUS_MODELS):
        sub = df[df["model_id"] == mid].copy()
        sub = sub.sort_values("output")
        labels = [OUTPUT_PAPER_LABEL.get(o, o) for o in sub["output"]]
        frac_epi = sub["frac_epistemic_mean"].values
        frac_ale = 1.0 - frac_epi

        x = np.arange(len(labels))
        ax.barh(x, frac_epi, color="#2196F3", label="Epistemic", height=0.6)
        ax.barh(x, frac_ale, left=frac_epi, color="#FF9800", label="Aleatoric", height=0.6)
        ax.set_yticks(x)
        ax.set_yticklabels(labels, fontsize=9)
        ax.set_xlim(0, 1)
        ax.set_xlabel("Fraction of total variance")
        ax.set_title(MODEL_PAPER_LABEL.get(mid, mid), fontsize=11)
        ax.legend(loc="lower right", fontsize=8)

    fig.suptitle("Epistemic vs aleatoric uncertainty decomposition", fontsize=13)
    plt.tight_layout()
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(out_dir, f"uncertainty_decomposition_bar.{ext}"), dpi=200)
    plt.close(fig)
    logger.info("Saved stacked bar figure")

    # ---- Figure 2: Scatter (epistemic std vs aleatoric std) per output ----
    for mid in FOCUS_MODELS:
        pred = load_predictions(mid)
        if pred is None:
            continue
        cols = pred["output_cols"]
        n_primary = len(PRIMARY_OUTPUTS)
        fig, axes = plt.subplots(1, n_primary, figsize=(4 * n_primary, 4))
        if n_primary == 1:
            axes = [axes]
        for ax, oc in zip(axes, PRIMARY_OUTPUTS):
            if oc not in cols:
                continue
            idx = cols.index(oc)
            epi_std = np.sqrt(pred["epistemic_var"][:, idx])
            ale_std = np.sqrt(pred["aleatoric_var"][:, idx])
            ax.scatter(ale_std, epi_std, s=8, alpha=0.4, c="#555")
            maxv = max(epi_std.max(), ale_std.max()) * 1.05
            ax.plot([0, maxv], [0, maxv], "k--", lw=0.8, alpha=0.5)
            ax.set_xlabel("Aleatoric std")
            ax.set_ylabel("Epistemic std")
            ax.set_title(OUTPUT_PAPER_LABEL.get(oc, oc), fontsize=10)
            ax.set_aspect("equal", adjustable="datalim")
        fig.suptitle(f"{MODEL_PAPER_LABEL.get(mid, mid)} — per-sample uncertainty",
                     fontsize=12)
        plt.tight_layout()
        for ext in ("pdf", "png"):
            fig.savefig(os.path.join(out_dir, f"epi_vs_ale_scatter_{mid}.{ext}"), dpi=200)
        plt.close(fig)
        logger.info(f"Saved scatter figure for {mid}")

    # ---- Figure 3: All 4 models comparison bar ----
    fig, ax = plt.subplots(figsize=(10, 6))
    model_ids = [m for m in MODELS if m in df["model_id"].values]
    n_models = len(model_ids)
    n_outputs = len(PRIMARY_OUTPUTS)
    bar_width = 0.18
    x = np.arange(n_outputs)

    for i, mid in enumerate(model_ids):
        sub = df[df["model_id"] == mid]
        fracs = []
        for oc in PRIMARY_OUTPUTS:
            row = sub[sub["output"] == oc]
            fracs.append(row["frac_epistemic_mean"].values[0] if len(row) > 0 else 0)
        offset = (i - n_models / 2 + 0.5) * bar_width
        ax.bar(x + offset, fracs, bar_width, label=MODEL_PAPER_LABEL.get(mid, mid))

    ax.set_xticks(x)
    ax.set_xticklabels([OUTPUT_PAPER_LABEL.get(o, o) for o in PRIMARY_OUTPUTS],
                       fontsize=9, rotation=15, ha="right")
    ax.set_ylabel("Epistemic fraction of total variance")
    ax.set_ylim(0, 1)
    ax.legend(fontsize=8)
    ax.set_title("Epistemic uncertainty fraction by model and output", fontsize=12)
    plt.tight_layout()
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(out_dir, f"uncertainty_decomposition_comparison.{ext}"), dpi=200)
    plt.close(fig)
    logger.info("Saved 4-model comparison figure")

    print("\n=== Uncertainty Decomposition Summary ===")
    for mid in FOCUS_MODELS:
        sub = df[df["model_id"] == mid]
        print(f"\n{MODEL_PAPER_LABEL.get(mid, mid)}:")
        for _, r in sub.iterrows():
            print(f"  {r['output_label']:25s}  epi={r['frac_epistemic_mean']:.3f}  "
                  f"ale={1-r['frac_epistemic_mean']:.3f}")


if __name__ == "__main__":
    run()
