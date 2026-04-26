#!/usr/bin/env python3
"""
rerun_v3418.py — Retrain + rerun all experiments with updated dataset (3418 samples).

This script:
  1. Creates a NEW fixed split from dataset_v3.csv (3418 rows)
  2. Points all config to the new split and new output root
  3. Runs run_0404.py with ALL stages enabled (train → eval → all experiments → figures)
  4. Old results (bnn0414/code/) are untouched; new results go to bnn0414/results_v3418/

Usage (on server, with pytorch-env):
    source /opt/software/miniconda3/etc/profile.d/conda.sh
    conda activate pytorch-env
    cd /path/to/bnn0414/code/experiments_0404
    python rerun_v3418.py              # full pipeline
    python rerun_v3418.py --dry-run    # check config only
    python rerun_v3418.py --skip-train # skip training (if checkpoints already exist)
    python rerun_v3418.py --only-split # only create the new fixed split, then exit
"""

import argparse
import json
import os
import sys
import subprocess
from datetime import datetime

import numpy as np
import pandas as pd

# ── Path setup ──
_SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))   # experiments_0404/
_BNN_CODE    = os.path.dirname(_SCRIPT_DIR)                  # bnn0414/code/
_BNN_ROOT    = os.path.dirname(_BNN_CODE)                    # bnn0414/
_CODE_TOP    = os.path.dirname(_BNN_ROOT)                    # code/

# Config imports
sys.path.insert(0, os.path.join(_SCRIPT_DIR, "config"))
from experiment_config_0404 import (
    INPUT_COLS, OUTPUT_COLS, SEED, TEST_FRAC, VAL_FRAC,
)

# ── Constants ──
RERUN_TAG = "v3418"

CSV_CANDIDATES = [
    "/home/tjzs/Documents/fenics_data/fenics_data/txt_extract/dataset_v3.csv",
    os.path.join(_CODE_TOP, "dataset_v3_updated.csv"),
    os.path.join(_CODE_TOP, "dataset_v3.csv"),
]

NEW_EXPR_ROOT  = os.path.join(_BNN_ROOT, f"results_{RERUN_TAG}")
NEW_SPLIT_DIR  = os.path.join(NEW_EXPR_ROOT, "fixed_split")


def find_csv():
    for c in CSV_CANDIDATES:
        if os.path.exists(c):
            return c
    return None


def create_fixed_split(csv_path: str, split_dir: str, seed: int = SEED):
    """Create a new train/val/test split from the full CSV."""
    print(f"\n{'='*60}")
    print(f"Creating fixed split from: {csv_path}")
    print(f"Output dir: {split_dir}")
    print(f"{'='*60}")

    df = pd.read_csv(csv_path, encoding="utf-8-sig")
    missing = [c for c in INPUT_COLS + OUTPUT_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns in CSV: {missing}")

    keep_mask = df[INPUT_COLS + OUTPUT_COLS].notna().all(axis=1)
    df_clean = df[keep_mask].reset_index(drop=True)
    n_total = len(df_clean)
    print(f"Total valid samples: {n_total}")

    rng = np.random.RandomState(seed)
    idx = np.arange(n_total)
    rng.shuffle(idx)
    n_test = int(n_total * TEST_FRAC)
    idx_test = idx[:n_test]
    idx_trainval = idx[n_test:]
    rng2 = np.random.RandomState(seed + 1)
    rng2.shuffle(idx_trainval)
    n_val = int(len(idx_trainval) * VAL_FRAC)
    idx_val = idx_trainval[:n_val]
    idx_train = idx_trainval[n_val:]

    os.makedirs(split_dir, exist_ok=True)

    for name, indices in [("train", idx_train), ("val", idx_val), ("test", idx_test)]:
        pd.DataFrame({"index": sorted(indices)}).to_csv(
            os.path.join(split_dir, f"{name}_indices.csv"), index=False
        )
        df_clean.iloc[sorted(indices)].to_csv(
            os.path.join(split_dir, f"{name}.csv"), index=False
        )

    meta = {
        "csv_path": csv_path,
        "seed": seed,
        "test_frac": TEST_FRAC,
        "val_frac_within_train": VAL_FRAC,
        "n_total": n_total,
        "n_train": len(idx_train),
        "n_val": len(idx_val),
        "n_test": len(idx_test),
        "input_cols": INPUT_COLS,
        "output_cols": OUTPUT_COLS,
        "created": datetime.now().isoformat(),
        "rerun_tag": RERUN_TAG,
    }
    with open(os.path.join(split_dir, "split_meta.json"), "w") as f:
        json.dump(meta, f, indent=2)

    print(f"  train: {len(idx_train)}")
    print(f"  val:   {len(idx_val)}")
    print(f"  test:  {len(idx_test)}")
    print(f"  total: {n_total}")
    print(f"Split saved to: {split_dir}\n")
    return meta


def build_run_config_patch():
    """Return the RUN_CONFIG dict for a full rerun."""
    return {
        "preset": "custom",
        "custom_models": [
            "bnn-baseline",
            "bnn-data-mono",
            "bnn-phy-mono",
            "bnn-data-mono-ineq",
        ],
        "modules": {
            "train":                True,
            "eval_fixed":           True,
            "eval_repeat":          True,
            "risk_propagation":     True,
            "sensitivity":          True,
            "posterior_inference":   True,
            "generalization":       True,
            "computational_speedup": True,
            "physics_consistency":  True,
            "supplementary":        True,
            "figures_main":         True,
            "figures_appendix":     True,
        },
        "force_retrain": True,
        "dry_run": False,
        "log_level": "INFO",
    }


def write_run_config_override(skip_train: bool = False):
    """Write a temporary run config file that run_0404.py will pick up."""
    cfg = build_run_config_patch()
    if skip_train:
        cfg["modules"]["train"] = False
        cfg["force_retrain"] = False

    override_path = os.path.join(_SCRIPT_DIR, f"_run_config_{RERUN_TAG}.json")
    with open(override_path, "w") as f:
        json.dump(cfg, f, indent=2)
    return override_path


def main():
    parser = argparse.ArgumentParser(description=f"Rerun BNN pipeline with {RERUN_TAG} dataset")
    parser.add_argument("--dry-run", action="store_true", help="Print config and exit")
    parser.add_argument("--skip-train", action="store_true", help="Skip training stage")
    parser.add_argument("--only-split", action="store_true", help="Only create split, then exit")
    parser.add_argument("--csv", default=None, help="Override CSV path")
    args = parser.parse_args()

    csv_path = args.csv or find_csv()
    if csv_path is None:
        print("ERROR: Cannot find dataset_v3.csv. Use --csv to specify.")
        sys.exit(1)

    print(f"[rerun_{RERUN_TAG}] CSV: {csv_path}")
    print(f"[rerun_{RERUN_TAG}] New output root: {NEW_EXPR_ROOT}")

    # Step 1: Create new fixed split
    os.makedirs(NEW_EXPR_ROOT, exist_ok=True)
    meta = create_fixed_split(csv_path, NEW_SPLIT_DIR)

    if args.only_split:
        print("--only-split: done.")
        return

    # Step 2: Write run config override
    config_path = write_run_config_override(skip_train=args.skip_train)

    # Step 3: Set environment variables
    env = os.environ.copy()
    env["HPR_FIXED_SPLIT_DIR"] = NEW_SPLIT_DIR
    env["HPR_CSV_PATH"]        = csv_path
    env["HPR_EXPR_ROOT"]       = NEW_EXPR_ROOT
    env["RERUN_TAG"]           = RERUN_TAG
    env["FORCE_RETRAIN"]       = "1" if not args.skip_train else ""
    env["RUN_CONFIG_OVERRIDE"] = config_path

    if args.dry_run:
        print("\n=== DRY RUN ===")
        print(f"HPR_FIXED_SPLIT_DIR = {NEW_SPLIT_DIR}")
        print(f"HPR_CSV_PATH        = {csv_path}")
        print(f"HPR_EXPR_ROOT       = {NEW_EXPR_ROOT}")
        print(f"RERUN_TAG           = {RERUN_TAG}")
        print(f"RUN_CONFIG_OVERRIDE = {config_path}")
        print(f"\nSplit meta: {json.dumps(meta, indent=2)}")
        print(f"\nRun config: {json.dumps(build_run_config_patch(), indent=2)}")
        print("\nWould run: python run_0404.py")
        print("=== END DRY RUN ===")
        return

    # Step 4: Run the main pipeline
    print(f"\n{'='*60}")
    print(f"Launching run_0404.py with {RERUN_TAG} configuration")
    print(f"{'='*60}\n")

    run_script = os.path.join(_SCRIPT_DIR, "run_0404.py")
    result = subprocess.run(
        [sys.executable, run_script],
        env=env,
        cwd=_SCRIPT_DIR,
    )

    if result.returncode != 0:
        print(f"\n[rerun_{RERUN_TAG}] run_0404.py exited with code {result.returncode}")
        sys.exit(result.returncode)

    print(f"\n{'='*60}")
    print(f"[rerun_{RERUN_TAG}] All stages complete.")
    print(f"Results: {NEW_EXPR_ROOT}")
    print(f"Old results: {os.path.join(_BNN_CODE, 'models')} + {os.path.join(_BNN_CODE, 'experiments')}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
