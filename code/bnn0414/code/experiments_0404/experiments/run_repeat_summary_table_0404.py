# run_repeat_summary_table_0404.py
# ============================================================
# LOCAL ONLY — 聚合 5-seed repeat_eval → paper-ready mean±std table
# ============================================================

import os, sys, json, logging
import numpy as np
import pandas as pd

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_CODE_ROOT = _SCRIPT_DIR
while _CODE_ROOT and os.path.basename(_CODE_ROOT) != 'code':
    _CODE_ROOT = os.path.dirname(_CODE_ROOT)
_BNN_CONFIG_DIR = os.path.join(_CODE_ROOT, 'experiments_0404', 'config')
for _p in (_SCRIPT_DIR, _CODE_ROOT, _BNN_CONFIG_DIR):
    if _p and os.path.isdir(_p) and _p not in sys.path:
        sys.path.insert(0, _p)

from experiment_config_0404 import OUTPUT_COLS, PRIMARY_OUTPUTS, REPEAT_SEEDS, ensure_dir
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
    "iteration2_max_global_stress": "Max. global stress",
    "iteration2_keff":              r"$k_{\mathrm{eff}}$",
    "iteration2_max_fuel_temp":     "Max. fuel temp.",
    "iteration2_max_monolith_temp": "Max. monolith temp.",
    "iteration2_wall2":             "Wall expansion",
}

METRICS = ["RMSE", "R2", "PICP", "MPIW", "CRPS", "MAE"]


def run():
    out_dir = ensure_dir(os.path.join(_BNN_ROOT, "results", "accuracy"))

    # --- Per-model aggregate (global) ---
    global_rows = []
    for mid in MODELS:
        repeat_dir = os.path.join(_CODE_ROOT, "models", mid, "repeat_eval")
        seed_dfs = []
        for seed in REPEAT_SEEDS:
            p = os.path.join(repeat_dir, f"seed_{seed}", "metrics.json")
            if not os.path.exists(p):
                logger.warning(f"  [{mid}] 缺少 seed_{seed}/metrics.json")
                continue
            with open(p) as f:
                seed_dfs.append(json.load(f))
        if not seed_dfs:
            continue
        row = {"model_id": mid, "paper_label": MODEL_PAPER_LABEL.get(mid, mid),
               "n_seeds": len(seed_dfs)}
        for m in METRICS:
            key = f"{m}_mean"
            vals = [d[key] for d in seed_dfs if key in d]
            if vals:
                row[f"{m}_mean"] = float(np.mean(vals))
                row[f"{m}_std"] = float(np.std(vals, ddof=1)) if len(vals) > 1 else 0.0
        global_rows.append(row)

    gdf = pd.DataFrame(global_rows)
    gdf.to_csv(os.path.join(out_dir, "repeat_eval_global_summary.csv"), index=False)
    logger.info(f"Global summary: {len(gdf)} models")

    # --- Per-model × per-output ---
    detail_rows = []
    for mid in MODELS:
        repeat_dir = os.path.join(_CODE_ROOT, "models", mid, "repeat_eval")
        per_out_dfs = []
        for seed in REPEAT_SEEDS:
            p = os.path.join(repeat_dir, f"seed_{seed}", "metrics_per_output.csv")
            if not os.path.exists(p):
                continue
            df = pd.read_csv(p)
            df["seed"] = seed
            per_out_dfs.append(df)
        if not per_out_dfs:
            continue
        all_seeds = pd.concat(per_out_dfs, ignore_index=True)
        for col in OUTPUT_COLS:
            sub = all_seeds[all_seeds["output"] == col]
            if sub.empty:
                continue
            row = {"model_id": mid, "paper_label": MODEL_PAPER_LABEL.get(mid, mid),
                   "output": col, "output_label": OUTPUT_PAPER_LABEL.get(col, col),
                   "is_primary": col in PRIMARY_OUTPUTS, "n_seeds": len(sub)}
            for m in METRICS:
                if m in sub.columns:
                    vals = sub[m].dropna().values
                    if len(vals) > 0:
                        row[f"{m}_mean"] = float(np.mean(vals))
                        row[f"{m}_std"] = float(np.std(vals, ddof=1)) if len(vals) > 1 else 0.0
            detail_rows.append(row)

    ddf = pd.DataFrame(detail_rows)
    ddf.to_csv(os.path.join(out_dir, "repeat_eval_per_output_summary.csv"), index=False)
    logger.info(f"Per-output summary: {len(ddf)} rows")

    # --- 纸面格式 (primary outputs only) ---
    primary = ddf[ddf["is_primary"]].copy()
    if not primary.empty:
        pivot_rows = []
        for mid in MODELS:
            sub = primary[primary["model_id"] == mid]
            for _, r in sub.iterrows():
                for m in ["RMSE", "R2", "CRPS", "PICP"]:
                    mk, sk = f"{m}_mean", f"{m}_std"
                    if mk in r and not pd.isna(r[mk]):
                        pivot_rows.append({
                            "model": MODEL_PAPER_LABEL.get(mid, mid),
                            "output": r["output_label"],
                            "metric": m,
                            "value": f"{r[mk]:.4f} ± {r.get(sk, 0):.4f}",
                        })
        pdf = pd.DataFrame(pivot_rows)
        pdf.to_csv(os.path.join(out_dir, "repeat_eval_paper_table.csv"), index=False)
        logger.info(f"Paper table: {len(pdf)} entries")

    print("\n=== Global summary ===")
    print(gdf.to_string(index=False))


if __name__ == "__main__":
    run()
