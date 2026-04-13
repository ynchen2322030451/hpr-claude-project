# run_posterior_hf_rerun_only.py
# ============================================================
# Run high-fidelity rerun only, using exported posterior points.
#
# Run in: HF env (OpenMC + FEniCS + generater available)
# Input:
#   experiments_phys_levels/posterior_hf_rerun/posterior_hf_rerun_inputs.csv
#
# Outputs:
#   posterior_hf_rerun_summary.csv
#   posterior_hf_rerun_per_output.csv
#   posterior_hf_rerun_meta.json
# ============================================================

import argparse
import os
import re
import json
import shutil
import datetime
from pathlib import Path

import numpy as np
import pandas as pd

# -------------------------------------------------------
# Path setup (defaults; may be overridden by CLI --input / --out-dir)
# -------------------------------------------------------
THIS_DIR = Path("/home/tjzs/Documents/0310")

RERUN_OUT_DIR = THIS_DIR / "experiments_phys_levels" / "posterior_hf_rerun"
INPUT_CSV = RERUN_OUT_DIR / "posterior_hf_rerun_inputs.csv"

MATERIAL_KEYS = [
    "E_slope", "E_intercept", "nu", "alpha_base", "alpha_slope",
    "SS316_T_ref", "SS316_k_ref", "SS316_alpha", "SS316_scale",
]

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


# -------------------------------------------------------
# Helpers
# -------------------------------------------------------
def _safe_nested(d, *keys):
    cur = d
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return None
        cur = cur[k]
    return cur


def _first_not_none(*vals):
    for v in vals:
        if v is None:
            continue
        try:
            if not np.isnan(float(v)):
                return float(v)
        except Exception:
            pass
    return None


def _find_float(pattern, text, flags=re.MULTILINE):
    m = re.search(pattern, text, flags)
    if not m:
        return None
    try:
        return float(m.group(1))
    except Exception:
        return None


def _find_last_float(pattern, text, flags=re.MULTILINE):
    matches = re.findall(pattern, text, flags)
    if not matches:
        return None
    try:
        val = matches[-1]
        if isinstance(val, tuple):
            val = val[0]
        return float(val)
    except Exception:
        return None


def _parse_iteration1_from_log(content: str) -> dict:
    it1 = re.search(
        r"=+\s*[Ii]teration\s*1\s*[Bb]egins\s*=+(.*?)"
        r"(?:=+\s*[Ii]teration\s*2\s*[Bb]egins\s*=+|$)",
        content,
        re.DOTALL,
    )
    txt = it1.group(1) if it1 else content
    num = r"([\d]+(?:\.\d+)?(?:[eE][+\-]?\d+)?)"

    return {
        "iteration1_avg_fuel_temp": _find_float(
            rf"(?:平均燃料温度|avg_fuel_temp)\s*[:=]\s*{num}", txt, re.IGNORECASE),
        "iteration1_max_fuel_temp": _find_float(
            rf"(?:燃料最高温度|max_fuel_temp)\s*[:=]\s*{num}", txt, re.IGNORECASE),
        "iteration1_max_monolith_temp": _find_float(
            rf"(?:单体最高温度|max_monolith_temp)\s*[:=]\s*{num}", txt, re.IGNORECASE),
        "iteration1_max_global_stress": _find_float(
            rf"(?:全局最大应力|max_global_stress)\s*[:=]\s*{num}", txt, re.IGNORECASE),
        "iteration1_monolith_new_temperature": _find_float(
            rf"(?:[Mm]onolith\s*[Nn]ew\s*[Tt]emp(?:erature)?|monolith_new_temperature)\s*[:=]\s*{num}", txt),
        "iteration1_Hcore_after": _find_float(
            rf"(?:[Nn]ew\s*[Hh]core|Hcore_after)\s*[:=]\s*{num}", txt),
        "iteration1_wall2": _find_float(
            rf"(?:[Nn]ew\s*wall2|wall2)\s*[:=]\s*{num}", txt),
    }


def _parse_iteration2_from_log(content: str) -> dict:
    num = r"([\d]+(?:\.\d+)?(?:[eE][+\-]?\d+)?)"
    it2 = re.search(
        r"=+\s*[Ii]teration\s*2\s*[Bb]egins\s*=+(.*)$",
        content,
        re.DOTALL,
    )
    txt = it2.group(1) if it2 else content

    return {
        "iteration2_avg_fuel_temp": _find_last_float(
            rf"(?:平均燃料温度|avg_fuel_temp)\s*[:=]\s*{num}", txt, re.IGNORECASE),
        "iteration2_max_fuel_temp": _find_last_float(
            rf"(?:燃料最高温度|max_fuel_temp)\s*[:=]\s*{num}", txt, re.IGNORECASE),
        "iteration2_max_monolith_temp": _find_last_float(
            rf"(?:单体最高温度|max_monolith_temp)\s*[:=]\s*{num}", txt, re.IGNORECASE),
        "iteration2_max_global_stress": _find_last_float(
            rf"(?:全局最大应力|max_global_stress)\s*[:=]\s*{num}", txt, re.IGNORECASE),
        "iteration2_monolith_new_temperature": _find_last_float(
            rf"(?:[Mm]onolith\s*[Nn]ew\s*[Tt]emp(?:erature)?|monolith_new_temperature)\s*[:=]\s*{num}", txt),
        "iteration2_Hcore_after": _find_last_float(
            rf"(?:[Nn]ew\s*[Hh]core|Hcore_after)\s*[:=]\s*{num}", txt),
        "iteration2_wall2": _find_last_float(
            rf"(?:[Nn]ew\s*wall2|wall2)\s*[:=]\s*{num}", txt),
    }


def parse_hf_outputs(case_subdir: str, keffs) -> dict:
    out = {col: None for col in ALL_OUTPUT_COLS}

    if len(keffs) > 0:
        try:
            if not np.isnan(float(keffs[0])):
                out["iteration2_keff"] = float(keffs[0])
        except Exception:
            pass

    fenics_json = os.path.join(case_subdir, "fenics_results.json")
    if os.path.exists(fenics_json):
        with open(fenics_json, "r", encoding="utf-8") as f:
            fdata = json.load(f)

        out["iteration2_max_fuel_temp"] = _first_not_none(
            _safe_nested(fdata, "temperature", "max_fuel_temp"),
            fdata.get("max_fuel_temp"),
            fdata.get("max_temp"),
        )
        out["iteration2_avg_fuel_temp"] = _first_not_none(
            _safe_nested(fdata, "temperature", "average_fuel_temp"),
            fdata.get("average_fuel_temp"),
        )
        out["iteration2_max_monolith_temp"] = _first_not_none(
            _safe_nested(fdata, "temperature", "max_monolith_temp"),
            fdata.get("max_monolith_temp"),
        )
        out["iteration2_monolith_new_temperature"] = _first_not_none(
            _safe_nested(fdata, "temperature", "average_monolith_temp"),
            fdata.get("average_monolith_temp"),
        )
        out["iteration2_max_global_stress"] = _first_not_none(
            _safe_nested(fdata, "stress", "global_max_stress"),
            fdata.get("global_max_stress"),
        )
        out["iteration2_wall2"] = _first_not_none(
            _safe_nested(fdata, "expansion", "max_2d_expansion_x"),
            fdata.get("newwall2"),
            fdata.get("wall2"),
        )
        out["iteration2_Hcore_after"] = _first_not_none(
            _safe_nested(fdata, "expansion", "max_3d_expansion_z"),
            fdata.get("height"),
            fdata.get("new_height"),
            fdata.get("Hcore_after"),
        )

    log_file = os.path.join(case_subdir, "out_fenicsdata_coupled.txt")
    if os.path.exists(log_file):
        with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        iter1_fields = _parse_iteration1_from_log(content)
        for k, v in iter1_fields.items():
            out[k] = v

        iter2_fields = _parse_iteration2_from_log(content)
        for k, v in iter2_fields.items():
            if out.get(k) is None:
                out[k] = v

    return out


def run_hf_case(case_i: int, theta9: np.ndarray, label: str):
    import generater

    inputs = theta9.reshape(1, -1)

    print(f"\n[HF RUN] case {case_i:02d} | label={label}")
    print("  " + "  ".join(f"{k}={theta9[i]:.4g}" for i, k in enumerate(MATERIAL_KEYS)))
    print("  Starting coupled calculation...")

    ret = generater.start_generater(inputs=inputs, counts=1)

    # 待核实接口，先兼容几种常见返回
    if isinstance(ret, tuple) and len(ret) == 2:
        keffs, run_dir = ret
    elif isinstance(ret, dict):
        keffs = ret.get("keffs", [])
        run_dir = ret.get("run_dir", ret.get("output_dir", None))
        if run_dir is None:
            raise ValueError("generater.start_generater returned dict but no run_dir/output_dir found")
    else:
        raise ValueError(
            f"Unsupported return type from generater.start_generater: {type(ret)}; value={ret}"
        )

    case_subdir = os.path.join(run_dir, "0")
    results = parse_hf_outputs(case_subdir, keffs)
    results["output_dir"] = run_dir
    results["case_i"] = case_i
    results["label"] = label

    dest = os.path.join(RERUN_OUT_DIR, f"case{case_i:03d}_{label}")
    if os.path.exists(dest):
        shutil.rmtree(dest)

    src_to_copy = case_subdir if os.path.exists(case_subdir) else run_dir
    shutil.copytree(src_to_copy, dest)
    results["archived_dir"] = dest

    return results


# -------------------------------------------------------
# Main
# -------------------------------------------------------
def main():
    global RERUN_OUT_DIR, INPUT_CSV

    ap = argparse.ArgumentParser(description="Posterior HF rerun executor")
    ap.add_argument("--input", default=None,
                    help="Override input CSV path (default: "
                         "RERUN_OUT_DIR/posterior_hf_rerun_inputs.csv)")
    ap.add_argument("--out-dir", default=None,
                    help="Override output directory (default: RERUN_OUT_DIR). "
                         "Use a dated subdirectory to avoid overwriting previous runs.")
    args = ap.parse_args()

    if args.out_dir:
        RERUN_OUT_DIR = Path(args.out_dir)
        RERUN_OUT_DIR.mkdir(parents=True, exist_ok=True)
    if args.input:
        INPUT_CSV = Path(args.input)

    if not INPUT_CSV.exists():
        raise FileNotFoundError(f"Missing input csv: {INPUT_CSV}")

    df_in = pd.read_csv(INPUT_CSV)
    summary_rows = []
    per_output_rows = []

    print("=" * 60)
    print("POSTERIOR HF RERUN ONLY")
    print(f"Input:   {INPUT_CSV}")
    print(f"Out dir: {RERUN_OUT_DIR}")
    print("=" * 60)

    for _, row in df_in.iterrows():
        case_i = int(row["case_i"])

        def _theta_val(k):
            col = f"theta9_post__{k}"
            if col in df_in.columns and not pd.isna(row[col]):
                return float(row[col])
            if k == "SS316_scale":
                return 1.0  # legacy material param not part of 0404 design
            raise KeyError(f"Missing required input column: {col}")

        theta9 = np.array([_theta_val(k) for k in MATERIAL_KEYS], dtype=float)
        hf_results = run_hf_case(case_i, theta9, label="post_mean")

        true_stress = float(row["y_true__iteration2_max_global_stress"])
        true_keff = float(row["y_true__iteration2_keff"])
        surr_prior_stress = float(row["surr_prior__iteration2_max_global_stress"])
        surr_post_stress = float(row["surr_post__iteration2_max_global_stress"])
        hf_post_stress = hf_results.get("iteration2_max_global_stress")
        hf_post_keff = hf_results.get("iteration2_keff")

        def _err(pred, true):
            if pred is None:
                return None
            return abs(float(pred) - float(true))

        out_row = {
            "case_i": case_i,
            "pool_case_index": int(row["pool_case_index"]),
            "true_stress_MPa": true_stress,
            "true_keff": true_keff,
            "surr_prior_stress": surr_prior_stress,
            "surr_post_stress": surr_post_stress,
            "hf_post_stress": hf_post_stress,
            "hf_post_keff": hf_post_keff,
            "err_surr_prior": _err(surr_prior_stress, true_stress),
            "err_surr_post": _err(surr_post_stress, true_stress),
            "err_hf_post": _err(hf_post_stress, true_stress),
            "archived_dir": hf_results.get("archived_dir", ""),
        }

        for col in ["E_intercept", "alpha_base", "alpha_slope", "nu"]:
            out_row[f"post_mean_{col}"] = float(row[f"theta8_post__{col}"])

        summary_rows.append(out_row)

        for col in ALL_OUTPUT_COLS:
            per_output_rows.append({
                "case_i": case_i,
                "output": col,
                "true_val": float(row[f"y_true__{col}"]),
                "surr_prior": float(row[f"surr_prior__{col}"]),
                "surr_post": float(row[f"surr_post__{col}"]),
                "hf_post": hf_results.get(col),
            })

        print(
            f"[OK] case {case_i}: "
            f"true_stress={true_stress:.2f}, "
            f"surr_post={surr_post_stress:.2f}, "
            f"hf_post={hf_post_stress if hf_post_stress is not None else 'N/A'}"
        )

    df_summary = pd.DataFrame(summary_rows)
    df_per = pd.DataFrame(per_output_rows)

    df_summary.to_csv(
        RERUN_OUT_DIR / "posterior_hf_rerun_summary.csv",
        index=False,
        encoding="utf-8-sig",
    )
    df_per.to_csv(
        RERUN_OUT_DIR / "posterior_hf_rerun_per_output.csv",
        index=False,
        encoding="utf-8-sig",
    )

    meta = {
        "input_csv": str(INPUT_CSV),
        "n_cases": len(df_summary),
        "material_keys": MATERIAL_KEYS,
        "all_output_cols": ALL_OUTPUT_COLS,
        "timestamp": datetime.datetime.now().isoformat(),
    }
    with open(RERUN_OUT_DIR / "posterior_hf_rerun_meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)

    print("=" * 60)
    print(f"DONE. Results saved to: {RERUN_OUT_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()