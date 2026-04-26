#!/usr/bin/env python3
"""Build the wide-format input CSV for HF rerun validation of BNN posterior results.

BNN version of 0411/code/postproc/build_rerun_manifest.py.

This script reads BNN posterior benchmark/feasible results and builds a CSV
with posterior mean parameters for HF rerun validation.

Source: bnn0414/results/posterior/<model_id>/benchmark_summary.csv
Output: bnn0414/results/posterior/hf_rerun/posterior_hf_rerun_inputs.csv

NOTE: This script requires BNN training and posterior inference to be complete.
      Run after run_posterior_0404.py has produced results.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]           # bnn0414/
CODE_TOP = ROOT.parent                                # code/

# Add paths for imports
for _p in [
    str(ROOT / "code" / "experiments_0404" / "config"),
    str(ROOT / "code" / "experiments_0404"),
    str(ROOT / "code"),
    str(CODE_TOP / "0310"),
]:
    if os.path.isdir(_p) and _p not in sys.path:
        sys.path.insert(0, _p)

MODEL_ID = "bnn-data-mono-ineq"

CALIB_PARAMS = ["E_intercept", "alpha_base", "alpha_slope", "SS316_k_ref"]
FIXED_PARAMS = ["E_slope", "SS316_T_ref", "SS316_alpha", "nu"]
INPUT_COLS_9 = [
    "E_slope", "E_intercept", "nu", "alpha_base", "alpha_slope",
    "SS316_T_ref", "SS316_k_ref", "SS316_alpha", "SS316_scale",
]


def _pivot_benchmark(bench_csv: Path, case_idx: int, row_idx: int) -> dict:
    df = pd.read_csv(bench_csv)
    sub = df[(df.case_idx == case_idx) & (df.row_idx == row_idx)]
    if len(sub) != len(CALIB_PARAMS):
        raise RuntimeError(
            f"benchmark_summary.csv: expected {len(CALIB_PARAMS)} param rows for "
            f"case_idx={case_idx}, row_idx={row_idx}, got {len(sub)}"
        )
    return {row["param"]: float(row["post_mean"]) for _, row in sub.iterrows()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model-id", default=MODEL_ID)
    ap.add_argument("--out-dir", default=None)
    ap.add_argument("--dry-run", action="store_true",
                    help="Only check file existence, don't build CSV")
    args = ap.parse_args()

    results_dir = ROOT / "results" / "posterior" / args.model_id
    bench_csv = results_dir / "benchmark_summary.csv"
    feas_csv  = results_dir / "feasible_region.csv"

    if not bench_csv.exists():
        print(f"[SKIP] {bench_csv} not found. Run posterior inference first.")
        return

    out_dir = Path(args.out_dir) if args.out_dir else (ROOT / "results" / "posterior" / "hf_rerun")
    out_dir.mkdir(parents=True, exist_ok=True)

    bench_df = pd.read_csv(bench_csv)
    available_cases = bench_df.groupby(["case_idx", "row_idx"]).size().reset_index()

    if args.dry_run:
        print(f"[dry-run] Found {len(available_cases)} benchmark cases in {bench_csv}")
        print(f"[dry-run] Feasible CSV exists: {feas_csv.exists()}")
        return

    # Build rows from all available benchmark cases
    rows = []
    for _, case in available_cases.iterrows():
        ci, ri = int(case["case_idx"]), int(case["row_idx"])
        try:
            post_mean = _pivot_benchmark(bench_csv, ci, ri)
        except RuntimeError as e:
            print(f"  [WARN] {e}")
            continue
        rows.append({
            "source": "benchmark",
            "case_idx": ci,
            "row_idx": ri,
            **{f"post_mean__{k}": v for k, v in post_mean.items()},
        })

    df = pd.DataFrame(rows)
    out_csv = out_dir / "posterior_hf_rerun_inputs.csv"
    df.to_csv(out_csv, index=False)

    manifest = {
        "model_id": args.model_id,
        "model_type": "BayesianMLP",
        "built_at": datetime.now().isoformat(),
        "n_cases": len(rows),
        "source_bench_csv": str(bench_csv),
        "output_csv": str(out_csv),
    }
    out_json = out_dir / "posterior_hf_rerun_inputs_manifest.json"
    with open(out_json, "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"wrote {out_csv}  ({len(rows)} cases)")
    print(f"wrote {out_json}")


if __name__ == "__main__":
    main()
