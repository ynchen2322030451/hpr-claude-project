# build_bnn_hf_rerun_manifest.py
# ============================================================
# Build HF-rerun input CSV from BNN posterior benchmark results.
#
# 产物：<posterior>/<model_id>/hf_rerun/posterior_hf_rerun_inputs.csv
#        每个 (case_idx, label) 一行；label ∈ {post_mean, post_lo_5, post_hi_95}
#        （可用 --labels 改）
#
# 列（顺序保证）：
#   case_i, pool_case_index, label, category, row_idx, stress_true_MPa
#   theta9_post__<MATERIAL_KEYS[0..8]>       ← 9 维，SS316_scale=1.0 nominal
#   y_true__<OUTPUT_COL>                      ← 15 个输出真值（供 HF driver 比对）
#
# 典型用法：
#   python build_bnn_hf_rerun_manifest.py --model bnn-data-mono-ineq
#   python build_bnn_hf_rerun_manifest.py --model bnn-phy-mono --labels post_mean
# ============================================================

import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd


# ------------------------------------------------------------
# Paths
# ------------------------------------------------------------
THIS_FILE = Path(__file__).resolve()
BNN_CODE  = THIS_FILE.parent.parent       # .../bnn0414/code
BNN_ROOT  = BNN_CODE.parent                # .../bnn0414

# 本地 / 服务器都要能跑 —— 在两个 posterior 候选根目录里找
POSTERIOR_ROOTS = [
    # 服务器落地（run_posterior_0404.py 写到 code/experiments/posterior/<mid>/）
    BNN_CODE / "experiments" / "posterior",
    # 万一有 rerun_tag 子目录
    BNN_CODE / "experiments" / "posterior" / "rerun_latest",
    # 兼容老路径
    BNN_CODE.parent / "code" / "bnn0414" / "code" / "experiments" / "posterior",
]

FIXED_SPLIT_CANDIDATES = [
    # .../code/0310/...  (0310 is sibling of bnn0414 under code/)
    BNN_CODE.parent.parent / "0310" / "experiments_phys_levels" / "fixed_split" / "test.csv",
    BNN_CODE / "experiments_0404" / "_shared" / "fixed_split" / "test.csv",
    # legacy fallback (one level up was wrong before)
    BNN_CODE.parent / "0310" / "experiments_phys_levels" / "fixed_split" / "test.csv",
]


# ------------------------------------------------------------
# Schema
# ------------------------------------------------------------
# HF pipeline (generater.start_generater) 需要 9 维；bnn0414 INPUT_COLS 只有 8 维
# 第 9 维 SS316_scale 在训练数据里是固定为 1.0 的标称；HF rerun 也用 1.0。
MATERIAL_KEYS = [
    "E_slope", "E_intercept", "nu",
    "alpha_base", "alpha_slope",
    "SS316_T_ref", "SS316_k_ref", "SS316_alpha",
    "SS316_scale",
]
SS316_SCALE_NOMINAL = 0.01  # 1/100, matches generater.py parameters_dic["SS316_scale"]

# BNN MCMC 标定的 4 个参数（benchmark_summary.csv 里的 param 字段）
CALIB_PARAMS = ["E_intercept", "alpha_base", "alpha_slope", "SS316_k_ref"]
# 其余 4 个从 test 真值填
FIXED_PARAMS_FROM_TRUTH = [
    "E_slope", "nu", "alpha_slope",  # alpha_slope 也标定；见覆盖逻辑
    "SS316_T_ref", "SS316_alpha",
]
FIXED_PARAMS_FROM_TRUTH = [p for p in MATERIAL_KEYS
                           if p not in CALIB_PARAMS
                           and p != "SS316_scale"]

OUTPUT_COLS = [
    "iteration1_avg_fuel_temp",
    "iteration1_max_fuel_temp",
    "iteration1_max_monolith_temp",
    "iteration1_max_global_stress",
    "iteration1_monolith_new_temperature",
    "iteration1_Hcore_after",
    "iteration1_wall2",
    "iteration2_keff",
    "iteration2_avg_fuel_temp",
    "iteration2_max_fuel_temp",
    "iteration2_max_monolith_temp",
    "iteration2_max_global_stress",
    "iteration2_monolith_new_temperature",
    "iteration2_Hcore_after",
    "iteration2_wall2",
]


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------
def locate_posterior_dir(model_id: str, override: str = None) -> Path:
    if override:
        p = Path(override)
        if not p.is_dir():
            sys.exit(f"[error] --posterior-dir {override} does not exist")
        return p
    for root in POSTERIOR_ROOTS:
        cand = root / model_id
        if (cand / "benchmark_summary.csv").exists():
            return cand
    sys.exit(
        f"[error] benchmark_summary.csv not found for model_id={model_id}. "
        f"Searched: {[str(r/model_id) for r in POSTERIOR_ROOTS]}"
    )


def locate_test_split(override: str = None) -> Path:
    if override:
        p = Path(override)
        if not p.exists():
            sys.exit(f"[error] --test-csv {override} does not exist")
        return p
    for c in FIXED_SPLIT_CANDIDATES:
        if c.exists():
            return c
    sys.exit(
        "[error] test.csv not found. Searched:\n  " +
        "\n  ".join(str(c) for c in FIXED_SPLIT_CANDIDATES)
    )


def pivot_bench_to_wide(bench_df: pd.DataFrame, label_col: str) -> pd.DataFrame:
    """
    把 benchmark_summary.csv（长表：case_idx × param）透视成宽表，
    每 case 一行，列为 <label_col>__<param>。
    """
    assert label_col in bench_df.columns, \
        f"{label_col} not in benchmark_summary.csv columns: {list(bench_df.columns)}"
    wide = (bench_df
            .pivot(index="case_idx", columns="param", values=label_col)
            .reset_index())
    wide.columns.name = None
    return wide


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="Build BNN HF rerun manifest")
    ap.add_argument("--model", required=True,
                    help="BNN model id, e.g. bnn-data-mono-ineq")
    ap.add_argument("--labels", nargs="+",
                    default=["post_mean", "post_lo_5", "post_hi_95"],
                    choices=["post_mean", "post_lo_5", "post_hi_95"],
                    help="Posterior labels to emit (one HF run per label per case)")
    ap.add_argument("--posterior-dir", default=None,
                    help="Override posterior artifacts dir")
    ap.add_argument("--test-csv", default=None,
                    help="Override fixed_split/test.csv path")
    ap.add_argument("--out", default=None,
                    help="Override output CSV path")
    args = ap.parse_args()

    post_dir = locate_posterior_dir(args.model, args.posterior_dir)
    bench_df = pd.read_csv(post_dir / "benchmark_summary.csv")
    with open(post_dir / "benchmark_case_meta.json") as f:
        case_meta = json.load(f)

    test_df = pd.read_csv(locate_test_split(args.test_csv))

    # test.csv 的第一列可能带 BOM：手动归一化列名
    test_df.columns = [c.replace("\ufeff", "").strip() for c in test_df.columns]

    # 每 label 一张宽表
    wide_by_label = {lbl: pivot_bench_to_wide(bench_df, lbl) for lbl in args.labels}

    # 校验：所有 label 宽表都应覆盖 benchmark_case_meta 里的 18 case
    n_expected = len(case_meta)
    for lbl, w in wide_by_label.items():
        missing = set(m["case_idx"] for m in case_meta) - set(w["case_idx"])
        if missing:
            sys.exit(f"[error] label={lbl} missing case_idx={sorted(missing)}")
        for p in CALIB_PARAMS:
            if p not in w.columns:
                sys.exit(f"[error] label={lbl}: param {p} missing from benchmark_summary")

    rows = []
    for case in case_meta:
        ci       = int(case["case_idx"])
        row_idx  = int(case["row_idx"])
        category = case["category"]
        stress_t = float(case["stress_true"])

        # test 真值行 —— row_idx 是 test-split-内 0-based 索引（run_posterior_0404.py 约定）
        try:
            truth = test_df.iloc[row_idx]
        except IndexError:
            sys.exit(f"[error] row_idx={row_idx} out of range (len(test_df)={len(test_df)})")

        for lbl in args.labels:
            w = wide_by_label[lbl]
            theta_post = w[w["case_idx"] == ci].iloc[0]   # 标定参在该 label 下的值

            rec = {
                "case_i":           ci,
                "pool_case_index":  ci,       # 兼容老 HF driver 的命名
                "label":            lbl,
                "category":         category,
                "row_idx":          row_idx,
                "stress_true_MPa":  stress_t,
            }

            # θ9：标定参用 posterior 对应 label；非标定参用 test 真值；SS316_scale 用 nominal
            for k in MATERIAL_KEYS:
                col = f"theta9_post__{k}"
                if k == "SS316_scale":
                    rec[col] = SS316_SCALE_NOMINAL
                elif k in CALIB_PARAMS:
                    rec[col] = float(theta_post[k])
                else:
                    rec[col] = float(truth[k])

            # y_true：15 个输出
            for col in OUTPUT_COLS:
                rec[f"y_true__{col}"] = float(truth[col]) if col in truth else np.nan

            rows.append(rec)

    df_out = pd.DataFrame(rows)

    # 输出路径
    if args.out:
        out_csv = Path(args.out)
    else:
        out_dir = post_dir / "hf_rerun"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_csv = out_dir / "posterior_hf_rerun_inputs.csv"

    df_out.to_csv(out_csv, index=False, encoding="utf-8-sig")

    # manifest 侧 meta
    meta = {
        "model_id":                 args.model,
        "labels":                   list(args.labels),
        "n_cases":                  n_expected,
        "n_rows_emitted":           len(df_out),
        "material_keys":            MATERIAL_KEYS,
        "ss316_scale_nominal":      SS316_SCALE_NOMINAL,
        "calib_params":             CALIB_PARAMS,
        "fixed_params_from_truth":  FIXED_PARAMS_FROM_TRUTH,
        "output_cols":              OUTPUT_COLS,
        "posterior_dir":            str(post_dir),
        "test_csv":                 str(locate_test_split(args.test_csv)),
        "notes": [
            "post_lo_5 / post_hi_95 use *marginal* posterior quantiles per "
            "calibrated param — NOT joint quantiles; if calib params are "
            "correlated in the posterior, the joint tail is not exactly at "
            "these points. Treat as an 'envelope' rather than a joint "
            "probability statement.",
            "SS316_scale=1.0 is the training-data nominal value; HF pipeline "
            "still takes a 9-dim input. bnn0414 INPUT_COLS has 8 dims "
            "(SS316_scale dropped because it was fixed in training).",
            "Non-calibrated params (E_slope, nu, SS316_T_ref, SS316_alpha) "
            "are taken from the test-split true values, so any y_HF deviation "
            "from y_true is attributable to calibration of the 4 MCMC params.",
        ],
    }
    with open(out_csv.with_name("posterior_hf_rerun_manifest.json"), "w") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)

    print(f"[ok] wrote {len(df_out)} rows × {len(df_out.columns)} cols → {out_csv}")
    print(f"[ok] labels: {list(args.labels)} × {n_expected} cases")
    # Quick sanity sample
    show_cols = ["case_i", "label", "category", "stress_true_MPa",
                 "theta9_post__E_intercept", "theta9_post__alpha_base"]
    print(df_out[show_cols].head(9).to_string(index=False))


if __name__ == "__main__":
    main()
