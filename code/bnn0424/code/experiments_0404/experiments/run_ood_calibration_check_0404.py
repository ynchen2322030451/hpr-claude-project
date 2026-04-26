# run_ood_calibration_check_0404.py
# ============================================================
# LOCAL ONLY — OOD calibration check from existing generalization results
#
# Key question: does the model's predictive uncertainty properly
# increase for out-of-distribution inputs?
#
# Reads: generalization/<model>/ood_summary.csv (already computed)
# Produces:
#   results/ood/ood_calibration_comparison.csv
#   results/ood/ood_epistemic_ratio.png
#   results/ood/ood_coverage_comparison.png
# ============================================================

import os, sys, logging
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

from experiment_config_0404 import ensure_dir

logging.basicConfig(level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger(__name__)

_BNN_ROOT = os.path.dirname(_CODE_ROOT)

MODEL_PAPER_LABEL = {
    "bnn-baseline":       "Reference surrogate",
    "bnn-phy-mono":       "Physics-regularized BNN",
    "bnn-data-mono":      "Data-monotone BNN",
    "bnn-data-mono-ineq": "Data+inequality BNN",
}

FOCUS_MODELS = ["bnn-baseline", "bnn-phy-mono"]
ALL_MODELS = ["bnn-baseline", "bnn-data-mono", "bnn-phy-mono", "bnn-data-mono-ineq"]


def run():
    out_dir = ensure_dir(os.path.join(_BNN_ROOT, "results", "ood"))

    all_dfs = []
    for mid in ALL_MODELS:
        p = os.path.join(_CODE_ROOT, "experiments", "generalization", mid, "ood_summary.csv")
        if not os.path.exists(p):
            logger.warning(f"  [{mid}] ood_summary.csv not found")
            continue
        df = pd.read_csv(p)
        all_dfs.append(df)

    if not all_dfs:
        logger.error("No OOD data found")
        return

    full = pd.concat(all_dfs, ignore_index=True)

    # Compute key metrics: epistemic ratio (OOD/in-dist), coverage change
    rows = []
    for mid in ALL_MODELS:
        sub = full[full["model_id"] == mid]
        for feat in sub["ood_feature"].unique():
            fsub = sub[sub["ood_feature"] == feat]
            ind = fsub[fsub["split"] == "in_dist"]
            ood = fsub[fsub["split"] == "ood"]
            if ind.empty or ood.empty:
                continue
            ind_row = ind.iloc[0]
            ood_row = ood.iloc[0]
            epi_ratio = ood_row["epistemic_std_mean"] / max(ind_row["epistemic_std_mean"], 1e-10)
            ale_ratio = ood_row["aleatoric_std_mean"] / max(ind_row["aleatoric_std_mean"], 1e-10)
            rows.append({
                "model_id": mid,
                "model_label": MODEL_PAPER_LABEL.get(mid, mid),
                "ood_feature": feat,
                "epistemic_std_in": ind_row["epistemic_std_mean"],
                "epistemic_std_ood": ood_row["epistemic_std_mean"],
                "epistemic_ratio": epi_ratio,
                "aleatoric_std_in": ind_row["aleatoric_std_mean"],
                "aleatoric_std_ood": ood_row["aleatoric_std_mean"],
                "aleatoric_ratio": ale_ratio,
                "PICP_in": ind_row["PICP_mean"],
                "PICP_ood": ood_row["PICP_mean"],
                "PICP_change": ood_row["PICP_mean"] - ind_row["PICP_mean"],
                "RMSE_in": ind_row["RMSE_mean"],
                "RMSE_ood": ood_row["RMSE_mean"],
                "RMSE_ratio": ood_row["RMSE_mean"] / max(ind_row["RMSE_mean"], 1e-10),
                "CRPS_in": ind_row["CRPS_mean"],
                "CRPS_ood": ood_row["CRPS_mean"],
            })

    cdf = pd.DataFrame(rows)
    cdf.to_csv(os.path.join(out_dir, "ood_calibration_comparison.csv"), index=False)
    logger.info(f"Saved {len(cdf)} rows → ood_calibration_comparison.csv")

    # ---- Figure 1: Epistemic uncertainty ratio (OOD / in-dist) ----
    fig, ax = plt.subplots(figsize=(10, 5))
    features = sorted(cdf["ood_feature"].unique())
    x = np.arange(len(features))
    bar_w = 0.18
    for i, mid in enumerate(ALL_MODELS):
        sub = cdf[cdf["model_id"] == mid]
        vals = [sub[sub["ood_feature"] == f]["epistemic_ratio"].values[0]
                if len(sub[sub["ood_feature"] == f]) > 0 else 1.0
                for f in features]
        offset = (i - len(ALL_MODELS) / 2 + 0.5) * bar_w
        ax.bar(x + offset, vals, bar_w, label=MODEL_PAPER_LABEL.get(mid, mid))

    ax.axhline(1.0, color="k", ls="--", lw=0.8, alpha=0.5)
    ax.set_xticks(x)
    ax.set_xticklabels(features, fontsize=9, rotation=15, ha="right")
    ax.set_ylabel("Epistemic std ratio (OOD / in-distribution)")
    ax.set_title("OOD epistemic uncertainty inflation", fontsize=12)
    ax.legend(fontsize=8)
    plt.tight_layout()
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(out_dir, f"ood_epistemic_ratio.{ext}"), dpi=200)
    plt.close(fig)
    logger.info("Saved epistemic ratio figure")

    # ---- Figure 2: Coverage comparison (in-dist vs OOD) ----
    fig, axes = plt.subplots(1, len(FOCUS_MODELS), figsize=(6 * len(FOCUS_MODELS), 5), sharey=True)
    if len(FOCUS_MODELS) == 1:
        axes = [axes]

    for ax, mid in zip(axes, FOCUS_MODELS):
        sub = cdf[cdf["model_id"] == mid]
        feats = sub["ood_feature"].values
        picp_in = sub["PICP_in"].values
        picp_ood = sub["PICP_ood"].values
        x = np.arange(len(feats))
        ax.bar(x - 0.15, picp_in, 0.3, label="In-distribution", color="#4CAF50", alpha=0.8)
        ax.bar(x + 0.15, picp_ood, 0.3, label="OOD", color="#F44336", alpha=0.8)
        ax.set_xticks(x)
        ax.set_xticklabels(feats, fontsize=9, rotation=15, ha="right")
        ax.set_ylabel("90% PICP")
        ax.set_title(MODEL_PAPER_LABEL.get(mid, mid), fontsize=11)
        ax.legend(fontsize=8)
        ax.axhline(0.9, color="k", ls="--", lw=0.8, alpha=0.5)
        ax.set_ylim(0.8, 1.05)

    fig.suptitle("Coverage: in-distribution vs OOD", fontsize=13)
    plt.tight_layout()
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(out_dir, f"ood_coverage_comparison.{ext}"), dpi=200)
    plt.close(fig)
    logger.info("Saved coverage comparison figure")

    print("\n=== OOD Calibration Summary (focus models) ===")
    for mid in FOCUS_MODELS:
        sub = cdf[cdf["model_id"] == mid]
        print(f"\n{MODEL_PAPER_LABEL.get(mid, mid)}:")
        for _, r in sub.iterrows():
            print(f"  {r['ood_feature']:15s}  epi_ratio={r['epistemic_ratio']:.3f}  "
                  f"PICP: {r['PICP_in']:.3f}→{r['PICP_ood']:.3f}  "
                  f"RMSE: {r['RMSE_in']:.2f}→{r['RMSE_ood']:.2f}")


if __name__ == "__main__":
    run()
