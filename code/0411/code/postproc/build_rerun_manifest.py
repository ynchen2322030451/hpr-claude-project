#!/usr/bin/env python3
"""Build the wide-format input CSV that `run_posterior_hf_rerun.py` expects.

Plan A (3 HF runs):  benchmark row 433 + feasible rows 250, 385
Plan B (5 HF runs):  Plan A + benchmark row 176 + feasible row 210

Source of truth: 0411/results/posterior/hf_rerun/candidate_selection.json.

For each selected case this script produces one row with:
  - 4 calibration-parameter posterior means (E_intercept, nu, alpha_base, alpha_slope)
  - 5 fixed non-calibration parameters pulled from DESIGN_NOMINAL
      (E_slope, SS316_T_ref, SS316_k_ref, SS316_alpha) + SS316_scale=1.0
  - y_true for all 15 outputs from test_df.iloc[row_idx]
  - surr_prior and surr_post predictions for all 15 outputs

Benchmark rows: per-param post_mean is read directly from the canonical
benchmark_summary.csv (pivoted from long to wide).
Feasible rows: per-param post_mean is NOT cached, so we replay MCMC for the
target test rows using the exact machinery in run_posterior_0404.run_feasible_region.
Each replay takes roughly 5 minutes on GPU.

This script MUST run on the server (needs dataset_v3.csv, FIXED_SPLIT_DIR and
the data-mono-ineq checkpoint). It writes:
    <out_dir>/posterior_hf_rerun_inputs.csv
    <out_dir>/posterior_hf_rerun_inputs_manifest.json

and does NOT touch posterior_hf_rerun_summary.csv / posterior_hf_rerun_meta.json
— those belong to run_posterior_hf_rerun.py.
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
import torch


REPO_ROOT = Path(__file__).resolve().parents[3]
CAND_JSON = REPO_ROOT / "0411" / "results" / "posterior" / "hf_rerun" / "candidate_selection.json"
BENCH_CSV = REPO_ROOT / "0411" / "results" / "posterior" / "data-mono-ineq" / "benchmark_summary.csv"
FEAS_CSV  = REPO_ROOT / "0411" / "results" / "posterior" / "data-mono-ineq" / "feasible_region.csv"

MODEL_ID = "data-mono-ineq"

CALIB_PARAMS = ["E_intercept", "nu", "alpha_base", "alpha_slope"]
FIXED_PARAMS = ["E_slope", "SS316_T_ref", "SS316_k_ref", "SS316_alpha"]
MATERIAL_KEYS_9 = [
    "E_slope", "E_intercept", "nu", "alpha_base", "alpha_slope",
    "SS316_T_ref", "SS316_k_ref", "SS316_alpha", "SS316_scale",
]

PLAN_ROWS = {
    "A": {
        "benchmark": [(3, 433)],
        "feasible":  [(6, 250), (0, 385)],
    },
    "B": {
        "benchmark": [(3, 433), (1, 176)],
        "feasible":  [(6, 250), (0, 385), (8, 210)],
    },
}


def _import_posterior_module():
    """Import run_posterior_0404 and pull the pieces we need for an MCMC replay."""
    # matches the _SCRIPT_DIR setup inside run_posterior_0404.py
    legacy = os.environ.get("HPR_LEGACY_DIR", "/home/tjzs/Documents/0310")
    candidates = [
        os.path.join(legacy, "experiments_0404", "code", "experiments"),
        os.path.join(legacy, "experiments_0404", "code", "config"),
        os.path.join(legacy, "experiments_0404"),
        legacy,
    ]
    for p in candidates:
        if os.path.isdir(p) and p not in sys.path:
            sys.path.insert(0, p)
    import run_posterior_0404 as rp  # noqa
    return rp


def _pivot_benchmark(case_idx: int, row_idx: int) -> dict:
    df = pd.read_csv(BENCH_CSV)
    sub = df[(df.case_idx == case_idx) & (df.row_idx == row_idx)]
    if len(sub) != 4:
        raise RuntimeError(
            f"benchmark_summary.csv: expected 4 param rows for "
            f"case_idx={case_idx}, row_idx={row_idx}, got {len(sub)}"
        )
    return {row["param"]: float(row["post_mean"]) for _, row in sub.iterrows()}


def _replay_feasible_mcmc(rp, model, sx, sy, device, train_df, test_df, row_idx: int) -> dict:
    """Replay MCMC for one feasible-region test row; return per-param posterior mean.

    Uses the same seed schedule as run_feasible_region so the replay is reproducible
    relative to the canonical run. The seed schedule keys on case_idx, which is the
    positional index within feasible_region.csv; we use the row_idx→case_idx lookup
    from the canonical feasible_region.csv.
    """
    feas_df = pd.read_csv(FEAS_CSV)
    hit = feas_df[feas_df.row_idx == row_idx]
    if len(hit) == 0:
        raise RuntimeError(f"feasible_region.csv has no row_idx={row_idx}")
    case_idx = int(hit.iloc[0]["case_idx"])

    prior_stats = rp._get_prior_stats(train_df)
    case_row = test_df.iloc[row_idx]
    x_true = case_row[rp.INPUT_COLS].values.astype(float)
    y_true_all = case_row[rp.OUTPUT_COLS].values.astype(float)

    obs_idx = [rp.OUTPUT_COLS.index(c) for c in rp.OBS_COLS]
    y_obs_full = y_true_all[obs_idx]
    noise = np.abs(y_obs_full) * rp.OBS_NOISE_FRAC + 1e-10
    y_obs_noisy = y_obs_full + np.random.RandomState(rp.SEED + 200 + case_idx).normal(0, noise)

    base_seed = rp.SEED + 3000 + case_idx
    if rp.N_CHAINS > 1:
        posterior, accept_rate, rhat, _ = rp.run_mcmc_multi_chain(
            ref_x_full=x_true, y_obs=y_obs_noisy, obs_noise=noise,
            prior_stats=prior_stats,
            model=model, sx=sx, sy=sy, device=device,
            base_seed=base_seed, n_chains=rp.N_CHAINS,
        )
    else:
        rng = np.random.RandomState(base_seed)
        posterior, accept_rate = rp.run_mcmc(
            ref_x_full=x_true, y_obs=y_obs_noisy, obs_noise=noise,
            prior_stats=prior_stats,
            model=model, sx=sx, sy=sy, device=device, rng=rng,
        )
        rhat = None

    post_mean = {}
    for i, c in enumerate(rp.INVERSE_CALIB_PARAMS):
        post_mean[c] = float(np.mean(posterior[:, i]))
    return {
        "post_mean": post_mean,
        "accept_rate": float(accept_rate),
        "rhat": {c: float(rhat[i]) for i, c in enumerate(rp.INVERSE_CALIB_PARAMS)}
                if rhat is not None else None,
        "case_idx": case_idx,
        "x_true_full": x_true,
        "y_true_full": y_true_all,
    }


def _surrogate_predict(rp, model, sx, sy, device, x_full: np.ndarray) -> np.ndarray:
    mu, _ = rp._predict_single(model, sx, sy, x_full, device)
    return mu  # shape (15,)


def _build_theta_vector(post_mean: dict, ref_x_full: np.ndarray, input_cols: list) -> np.ndarray:
    """Fill 8 slots with post_mean on calib params + ref_x_full on fixed params, then append SS316_scale=1.0 at the end."""
    theta8 = ref_x_full.copy()
    for c in CALIB_PARAMS:
        theta8[input_cols.index(c)] = post_mean[c]
    return theta8  # 8-dim; SS316_scale handled in the caller


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", choices=["A", "B"], required=True)
    ap.add_argument("--out-dir", default=None,
                    help="Output directory (defaults to HPR_RERUN_OUT_DIR or "
                         "/home/tjzs/Documents/0310/experiments_phys_levels/posterior_hf_rerun/)")
    ap.add_argument("--dry-run", action="store_true",
                    help="Skip MCMC replay and emit NaN post_mean for feasible cases (local sanity check).")
    args = ap.parse_args()

    out_dir = Path(args.out_dir or os.environ.get(
        "HPR_RERUN_OUT_DIR",
        "/home/tjzs/Documents/0310/experiments_phys_levels/posterior_hf_rerun",
    ))
    out_dir.mkdir(parents=True, exist_ok=True)

    rp = _import_posterior_module() if not args.dry_run else None

    if not args.dry_run:
        device = rp.get_device()
        ckpt_path, scaler_path = rp._resolve_artifacts(MODEL_ID)
        model = rp._load_model(ckpt_path, device)
        scalers = rp._load_scalers(scaler_path)
        sx, sy = scalers["sx"], scalers["sy"]
        model.eval()

        train_df = pd.read_csv(os.path.join(rp.FIXED_SPLIT_DIR, "train.csv"))
        test_df = pd.read_csv(os.path.join(rp.FIXED_SPLIT_DIR, "test.csv"))
        input_cols = rp.INPUT_COLS
        output_cols = rp.OUTPUT_COLS
        # prior nominal = column mean of the training set (what run_posterior_0404 calls _get_prior_stats).
        prior_stats = rp._get_prior_stats(train_df)
        prior_nominal = {c: prior_stats[c]["mean"] for c in CALIB_PARAMS}
    else:
        input_cols = [
            "E_slope", "E_intercept", "nu", "alpha_base",
            "alpha_slope", "SS316_T_ref", "SS316_k_ref", "SS316_alpha",
        ]
        output_cols = None  # not used in dry-run
        test_df = None
        prior_nominal = None

    picks = PLAN_ROWS[args.plan]
    rows = []
    manifest_cases = []

    for bench_case_idx, bench_row_idx in picks["benchmark"]:
        post_mean = _pivot_benchmark(bench_case_idx, bench_row_idx)
        if args.dry_run:
            rows.append({"source": "benchmark", "case_idx": bench_case_idx,
                         "row_idx": bench_row_idx, "post_mean": post_mean})
            manifest_cases.append({"source": "benchmark", "case_idx": bench_case_idx,
                                   "row_idx": bench_row_idx, "theta_source": "benchmark_summary"})
            continue

        case_row = test_df.iloc[bench_row_idx]
        x_true = case_row[input_cols].values.astype(float)
        y_true = case_row[output_cols].values.astype(float)

        theta_post_8 = _build_theta_vector(post_mean, x_true, input_cols)
        x_prior_nominal = x_true.copy()
        for c in CALIB_PARAMS:
            x_prior_nominal[input_cols.index(c)] = prior_nominal[c]

        mu_post  = _surrogate_predict(rp, model, sx, sy, device, theta_post_8)
        mu_prior = _surrogate_predict(rp, model, sx, sy, device, x_prior_nominal)

        rows.append({
            "source": "benchmark",
            "case_i_internal": len(rows),
            "bench_case_idx": bench_case_idx,
            "row_idx": bench_row_idx,
            "theta8_post": {c: float(theta_post_8[input_cols.index(c)]) for c in input_cols},
            "y_true": dict(zip(output_cols, map(float, y_true))),
            "mu_prior": dict(zip(output_cols, map(float, mu_prior))),
            "mu_post":  dict(zip(output_cols, map(float, mu_post))),
        })
        manifest_cases.append({
            "source": "benchmark", "bench_case_idx": bench_case_idx,
            "row_idx": bench_row_idx, "theta_source": "benchmark_summary.csv pivot",
        })

    for feas_case_idx, feas_row_idx in picks["feasible"]:
        if args.dry_run:
            rows.append({"source": "feasible", "row_idx": feas_row_idx,
                         "post_mean": {c: float("nan") for c in CALIB_PARAMS}})
            manifest_cases.append({"source": "feasible", "row_idx": feas_row_idx,
                                   "theta_source": "dry-run (nan)"})
            continue

        print(f"[replay-MCMC] feasible row_idx={feas_row_idx} "
              f"(canonical case_idx={feas_case_idx}) ...")
        replay = _replay_feasible_mcmc(rp, model, sx, sy, device, train_df, test_df, feas_row_idx)
        post_mean = replay["post_mean"]
        case_row = test_df.iloc[feas_row_idx]
        x_true = case_row[input_cols].values.astype(float)
        y_true = case_row[output_cols].values.astype(float)

        theta_post_8 = _build_theta_vector(post_mean, x_true, input_cols)
        x_prior_nominal = x_true.copy()
        for c in CALIB_PARAMS:
            x_prior_nominal[input_cols.index(c)] = prior_nominal[c]

        mu_post  = _surrogate_predict(rp, model, sx, sy, device, theta_post_8)
        mu_prior = _surrogate_predict(rp, model, sx, sy, device, x_prior_nominal)

        rows.append({
            "source": "feasible",
            "case_i_internal": len(rows),
            "feas_case_idx": feas_case_idx,
            "row_idx": feas_row_idx,
            "theta8_post": {c: float(theta_post_8[input_cols.index(c)]) for c in input_cols},
            "y_true": dict(zip(output_cols, map(float, y_true))),
            "mu_prior": dict(zip(output_cols, map(float, mu_prior))),
            "mu_post":  dict(zip(output_cols, map(float, mu_post))),
            "replay_accept_rate": replay["accept_rate"],
            "replay_rhat": replay["rhat"],
        })
        manifest_cases.append({
            "source": "feasible", "feas_case_idx": feas_case_idx,
            "row_idx": feas_row_idx,
            "theta_source": f"replayed MCMC (accept={replay['accept_rate']:.3f})",
        })

    if args.dry_run:
        out_json = out_dir / f"rerun_plan_{args.plan}_dryrun.json"
        with open(out_json, "w") as f:
            json.dump({"plan": args.plan, "cases": rows}, f, indent=2)
        print(f"[dry-run] wrote {out_json}")
        return

    # Assemble wide CSV expected by run_posterior_hf_rerun.py
    wide_rows = []
    for i, r in enumerate(rows):
        row = {"case_i": i, "pool_case_index": int(r["row_idx"])}
        # theta9_post__*: 9 material keys (post_mean on calib, ref on fixed, SS316_scale=1.0)
        for k in MATERIAL_KEYS_9:
            if k == "SS316_scale":
                row[f"theta9_post__{k}"] = 1.0
            else:
                row[f"theta9_post__{k}"] = r["theta8_post"][k]
        # theta8_post__*: the 4 calibration params (what the summary CSV emits)
        for k in CALIB_PARAMS:
            row[f"theta8_post__{k}"] = r["theta8_post"][k]
        for k in output_cols:
            row[f"y_true__{k}"]     = r["y_true"][k]
            row[f"surr_prior__{k}"] = r["mu_prior"][k]
            row[f"surr_post__{k}"]  = r["mu_post"][k]
        wide_rows.append(row)

    df_wide = pd.DataFrame(wide_rows)
    out_csv = out_dir / "posterior_hf_rerun_inputs.csv"
    df_wide.to_csv(out_csv, index=False, encoding="utf-8-sig")

    manifest = {
        "plan": args.plan,
        "built_at": datetime.now().isoformat(),
        "source_candidate_selection": str(CAND_JSON.relative_to(REPO_ROOT.parent)) if CAND_JSON.exists() else None,
        "model_id": MODEL_ID,
        "n_cases": len(rows),
        "cases": manifest_cases,
        "output_csv": str(out_csv),
        "run_command": (
            "cd /home/tjzs/Documents/0310 && "
            "python run_posterior_hf_rerun.py "
            f"--input {out_csv}"
        ),
    }
    out_json = out_dir / "posterior_hf_rerun_inputs_manifest.json"
    with open(out_json, "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"wrote {out_csv}  ({len(rows)} cases)")
    print(f"wrote {out_json}")


if __name__ == "__main__":
    main()
