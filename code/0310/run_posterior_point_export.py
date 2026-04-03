# run_posterior_point_export.py
# ============================================================
# Export posterior mean points + surrogate predictions
# for later high-fidelity rerun in a separate environment.
#
# Run in: pytorch-env
# Outputs:
#   experiments_phys_levels/posterior_hf_rerun/posterior_hf_rerun_inputs.csv
#   experiments_phys_levels/posterior_hf_rerun/posterior_hf_rerun_inputs_meta.json
# ============================================================

import os
import sys
import json
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
import torch

# -------------------------------------------------------
# Path setup
# -------------------------------------------------------
THIS_DIR = Path(__file__).resolve().parent
SRC_0310 = THIS_DIR
OUT_DIR_0310 = SRC_0310 / "experiments_phys_levels"
BENCHMARK_DIR = OUT_DIR_0310 / "benchmark_case"
RERUN_OUT_DIR = OUT_DIR_0310 / "posterior_hf_rerun"
RERUN_OUT_DIR.mkdir(parents=True, exist_ok=True)

if str(SRC_0310) not in sys.path:
    sys.path.insert(0, str(SRC_0310))

# -------------------------------------------------------
# Imports from project
# -------------------------------------------------------
from paper_experiment_config import (
    CSV_PATH,
    FIXED_CKPT_PATH,
    FIXED_SCALER_PATH,
)
from run_phys_levels_main import HeteroMLP, _to_numpy

# -------------------------------------------------------
# Settings
# -------------------------------------------------------
RUN_TAG = "reduced_maintext"

CALIBRATION_COLS = ["E_intercept", "alpha_base", "alpha_slope", "nu"]
FIXED_COLS = ["E_slope", "SS316_T_ref", "SS316_k_ref", "SS316_alpha"]

INPUT_COLS = [
    "E_slope", "E_intercept", "nu", "alpha_base",
    "alpha_slope", "SS316_T_ref", "SS316_k_ref", "SS316_alpha",
]

MATERIAL_KEYS = [
    "E_slope", "E_intercept", "nu", "alpha_base", "alpha_slope",
    "SS316_T_ref", "SS316_k_ref", "SS316_alpha", "SS316_scale",
]
SS316_SCALE_NOMINAL = 1.0 / 100.0

OUTPUT_COLS_ITER1 = [
    "iteration1_avg_fuel_temp",
    "iteration1_max_fuel_temp",
    "iteration1_max_monolith_temp",
    "iteration1_max_global_stress",
    "iteration1_monolith_new_temperature",
    "iteration1_Hcore_after",
    "iteration1_wall2",
]
OUTPUT_COLS_ITER2 = [
    "iteration2_keff",
    "iteration2_avg_fuel_temp",
    "iteration2_max_fuel_temp",
    "iteration2_max_monolith_temp",
    "iteration2_max_global_stress",
    "iteration2_monolith_new_temperature",
    "iteration2_Hcore_after",
    "iteration2_wall2",
]
ALL_OUTPUT_COLS = OUTPUT_COLS_ITER1 + OUTPUT_COLS_ITER2

SELECTED_CASE_INDICES = [0, 4, 9, 14, 19]

_LEGACY_DIR = OUT_DIR_0310 / "_legacy_unused_20260325_161538"

def _resolve_calib_pool() -> Path:
    canonical = OUT_DIR_0310 / "inverse_calibration_pool.csv"
    legacy    = _LEGACY_DIR   / "inverse_calibration_pool.csv"
    if canonical.exists():
        return canonical
    if legacy.exists():
        return legacy
    return canonical   # let load_case_ground_truth raise the informative error

CALIB_POOL_PATH = _resolve_calib_pool()


# -------------------------------------------------------
# Helpers
# -------------------------------------------------------
def save_json(obj, path: Path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)


def load_surrogate():
    ckpt = torch.load(FIXED_CKPT_PATH, map_location="cpu")
    bp = ckpt["best_params"]

    model = HeteroMLP(
        in_dim=len(INPUT_COLS),
        out_dim=len(ALL_OUTPUT_COLS),
        width=int(bp["width"]),
        depth=int(bp["depth"]),
        dropout=float(bp["dropout"]),
    )
    model.load_state_dict(ckpt["model_state_dict"], strict=False)
    model.eval()

    with open(FIXED_SCALER_PATH, "rb") as f:
        scalers = pickle.load(f)

    return model, scalers["sx"], scalers["sy"]


def surrogate_predict(theta8_raw, model, sx, sy):
    x_s = sx.transform(theta8_raw.reshape(1, -1))
    x_t = torch.tensor(x_s, dtype=torch.float32)
    with torch.no_grad():
        mu_s, _ = model(x_t)
    mu_raw = sy.inverse_transform(_to_numpy(mu_s))[0]
    return mu_raw


def build_material_params_9d(theta8):
    mapping = {col: float(theta8[i]) for i, col in enumerate(INPUT_COLS)}
    mapping["SS316_scale"] = SS316_SCALE_NOMINAL
    return np.array([mapping[k] for k in MATERIAL_KEYS], dtype=float)


def load_posterior_mean(case_i, prior_mean8_raw):
    post_file = BENCHMARK_DIR / f"benchmark_case{case_i:03d}_posterior_samples_{RUN_TAG}.csv"
    if not post_file.exists():
        raise FileNotFoundError(f"Missing posterior samples: {post_file}")

    post_df = pd.read_csv(post_file)
    theta = prior_mean8_raw.copy()

    for col in CALIBRATION_COLS:
        if col in post_df.columns:
            theta[INPUT_COLS.index(col)] = float(post_df[col].mean())

    return theta


def load_inverse_case_map():
    candidates = [
        OUT_DIR_0310  / f"inverse_case_indices_{RUN_TAG}.csv",
        _LEGACY_DIR   / f"inverse_case_indices_{RUN_TAG}.csv",
        OUT_DIR_0310  / f"calibration_benchmark_case_summary_{RUN_TAG}.csv",
        _LEGACY_DIR   / f"calibration_benchmark_case_summary_{RUN_TAG}.csv",
        OUT_DIR_0310  / f"inverse_benchmark_case_summary_{RUN_TAG}.csv",
        _LEGACY_DIR   / f"inverse_benchmark_case_summary_{RUN_TAG}.csv",
        OUT_DIR_0310  / "calibration_benchmark_case_summary.csv",
        _LEGACY_DIR   / "calibration_benchmark_case_summary.csv",
    ]

    for path in candidates:
        if not path.exists():
            continue
        df = pd.read_csv(path)
        id_col = None
        for c in ("benchmark_case_id", "case_id"):
            if c in df.columns:
                id_col = c
                break
        if id_col is None or "pool_case_index" not in df.columns:
            continue
        return df[[id_col, "pool_case_index"]].rename(columns={id_col: "benchmark_case_id"})

    raise FileNotFoundError(
        f"Cannot find inverse case mapping for RUN_TAG={RUN_TAG}. "
        "Please run inverse benchmark first."
    )


def load_case_ground_truth(case_i):
    case_map = load_inverse_case_map()
    hit = case_map[case_map["benchmark_case_id"] == case_i]
    if hit.empty:
        raise ValueError(f"benchmark_case_id={case_i} not found in inverse case mapping")

    pool_case_index = int(hit.iloc[0]["pool_case_index"])

    if not CALIB_POOL_PATH.exists():
        raise FileNotFoundError(
            f"Missing calibration pool: {CALIB_POOL_PATH}. "
            "Please run run_inverse_benchmark_fixed_surrogate.py first."
        )

    pool_df = pd.read_csv(CALIB_POOL_PATH)
    if pool_case_index >= len(pool_df):
        raise IndexError(
            f"pool_case_index={pool_case_index} out of range for {CALIB_POOL_PATH}"
        )

    row = pool_df.iloc[pool_case_index]
    x_true = row[INPUT_COLS].to_numpy(dtype=float)
    y_true = row[ALL_OUTPUT_COLS].to_numpy(dtype=float)

    return x_true, y_true, pool_case_index


# -------------------------------------------------------
# Main
# -------------------------------------------------------
def main():
    print("=" * 60)
    print("POSTERIOR POINT EXPORT")
    print(f"Cases: {SELECTED_CASE_INDICES}")
    print("=" * 60)

    model, sx, sy = load_surrogate()

    # raw-space training-set mean
    prior_mean8_raw = sx.mean_.copy()

    rows = []

    for case_i in SELECTED_CASE_INDICES:
        print(f"[INFO] exporting case {case_i}")

        x_true, y_true, pool_case_index = load_case_ground_truth(case_i)
        theta8_post = load_posterior_mean(case_i, prior_mean8_raw)
        theta9_post = build_material_params_9d(theta8_post)

        mu_prior = surrogate_predict(prior_mean8_raw, model, sx, sy)
        mu_post = surrogate_predict(theta8_post, model, sx, sy)

        row = {
            "case_i": int(case_i),
            "pool_case_index": int(pool_case_index),
        }

        for j, col in enumerate(INPUT_COLS):
            row[f"x_true__{col}"] = float(x_true[j])
            row[f"prior_mean8__{col}"] = float(prior_mean8_raw[j])
            row[f"theta8_post__{col}"] = float(theta8_post[j])

        for j, key in enumerate(MATERIAL_KEYS):
            row[f"theta9_post__{key}"] = float(theta9_post[j])

        for j, col in enumerate(ALL_OUTPUT_COLS):
            row[f"y_true__{col}"] = float(y_true[j])
            row[f"surr_prior__{col}"] = float(mu_prior[j])
            row[f"surr_post__{col}"] = float(mu_post[j])

        rows.append(row)

    df = pd.DataFrame(rows)
    out_csv = RERUN_OUT_DIR / "posterior_hf_rerun_inputs.csv"
    df.to_csv(out_csv, index=False, encoding="utf-8-sig")

    meta = {
        "run_tag": RUN_TAG,
        "selected_case_indices": SELECTED_CASE_INDICES,
        "n_cases": len(rows),
        "input_cols": INPUT_COLS,
        "material_keys": MATERIAL_KEYS,
        "calibration_cols": CALIBRATION_COLS,
        "fixed_cols": FIXED_COLS,
        "all_output_cols": ALL_OUTPUT_COLS,
        "source_benchmark_dir": str(BENCHMARK_DIR),
        "source_calibration_pool": str(CALIB_POOL_PATH),
        "source_ckpt": str(FIXED_CKPT_PATH),
        "source_scaler": str(FIXED_SCALER_PATH),
    }
    save_json(meta, RERUN_OUT_DIR / "posterior_hf_rerun_inputs_meta.json")

    print(f"[DONE] saved: {out_csv}")


if __name__ == "__main__":
    main()