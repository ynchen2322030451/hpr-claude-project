# run_posterior_hf_rerun_0404.py
# ============================================================
# Execute HF reruns (openmc + FEniCS) at BNN posterior θ points.
#
# Inputs (CSV built by build_bnn_hf_rerun_manifest.py):
#   case_i, pool_case_index, label, category, row_idx, stress_true_MPa
#   theta9_post__<MATERIAL_KEYS[0..8]>
#   y_true__<OUTPUT_COL>                       (15 cols)
#   [optional] surr_post__<OUTPUT_COL>         (if manifest adds it)
#
# Outputs:
#   <out_dir>/posterior_hf_rerun_summary.csv   one row per (case_i, label)
#   <out_dir>/posterior_hf_rerun_per_output.csv  (case_i, label, output, ...)
#   <out_dir>/posterior_hf_rerun_meta.json
#   <out_dir>/progress.csv                      resume index
#   <out_dir>/case<ci>_<label>/                 archived HF run dir
#
# Designed for long jobs:
#   • resume-safe (skip cases already archived)
#   • per-case try/except (one failing case does not kill the batch)
#   • progress + ETA to stdout and log file
#   • generater.py auto-located in two known places
#
# Typical usage (server):
#   MODEL_ID=bnn-data-mono-ineq python run_posterior_hf_rerun_0404.py
#   python run_posterior_hf_rerun_0404.py \
#       --input <...>/posterior_hf_rerun_inputs.csv \
#       --out-dir <...>/hf_rerun_run1
# ============================================================

import argparse
import datetime
import json
import os
import re
import shutil
import sys
import time
import traceback
from pathlib import Path

import numpy as np
import pandas as pd


# ------------------------------------------------------------
# Path setup — resilient to moves
# ------------------------------------------------------------
THIS_FILE = Path(__file__).resolve()
BNN_CODE  = THIS_FILE.parent.parent         # .../bnn0414/code
BNN_ROOT  = BNN_CODE.parent                  # .../bnn0414
HPR_ROOT  = BNN_ROOT.parent.parent           # .../hpr-claude-project

# generater.py 可能在两处之一；顺序找
_GEN_CANDIDATES = [
    HPR_ROOT / "code" / "generater.py",
    Path("/home/tjzs/Documents/fenics_data/fenics_data/generater.py"),
]
for _gc in _GEN_CANDIDATES:
    if _gc.exists():
        if str(_gc.parent) not in sys.path:
            sys.path.insert(0, str(_gc.parent))
        break
else:
    print("[warn] generater.py not found in known locations; HF calls will fail", file=sys.stderr)


# ------------------------------------------------------------
# Schema (must match build_bnn_hf_rerun_manifest.py)
# ------------------------------------------------------------
MATERIAL_KEYS = [
    "E_slope", "E_intercept", "nu",
    "alpha_base", "alpha_slope",
    "SS316_T_ref", "SS316_k_ref", "SS316_alpha",
    "SS316_scale",
]

PRIMARY_OUTPUTS = [
    "iteration2_keff",
    "iteration2_max_fuel_temp",
    "iteration2_max_monolith_temp",
    "iteration2_max_global_stress",
    "iteration2_wall2",
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
ALL_OUTPUT_COLS = OUTPUT_COLS_ITER1 + OUTPUT_COLS_ITER2   # 15


# ------------------------------------------------------------
# Output parsing (inherited logic, trimmed)
# ------------------------------------------------------------
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


def _parse_iter_from_log(content: str, iter_idx: int) -> dict:
    """iter_idx=1 or 2"""
    num = r"([\d]+(?:\.\d+)?(?:[eE][+\-]?\d+)?)"
    if iter_idx == 1:
        m = re.search(
            r"=+\s*[Ii]teration\s*1\s*[Bb]egins\s*=+(.*?)"
            r"(?:=+\s*[Ii]teration\s*2\s*[Bb]egins\s*=+|$)",
            content, re.DOTALL,
        )
        finder = _find_float
        prefix = "iteration1"
    else:
        m = re.search(
            r"=+\s*[Ii]teration\s*2\s*[Bb]egins\s*=+(.*)$",
            content, re.DOTALL,
        )
        finder = _find_last_float
        prefix = "iteration2"
    txt = m.group(1) if m else content

    return {
        f"{prefix}_avg_fuel_temp": finder(
            rf"(?:平均燃料温度|avg_fuel_temp)\s*[:=]\s*{num}", txt, re.IGNORECASE),
        f"{prefix}_max_fuel_temp": finder(
            rf"(?:燃料最高温度|max_fuel_temp)\s*[:=]\s*{num}", txt, re.IGNORECASE),
        f"{prefix}_max_monolith_temp": finder(
            rf"(?:单体最高温度|max_monolith_temp)\s*[:=]\s*{num}", txt, re.IGNORECASE),
        f"{prefix}_max_global_stress": finder(
            rf"(?:全局最大应力|max_global_stress)\s*[:=]\s*{num}", txt, re.IGNORECASE),
        f"{prefix}_monolith_new_temperature": finder(
            rf"(?:[Mm]onolith\s*[Nn]ew\s*[Tt]emp(?:erature)?|monolith_new_temperature)\s*[:=]\s*{num}", txt),
        f"{prefix}_Hcore_after": finder(
            rf"(?:[Nn]ew\s*[Hh]core|Hcore_after)\s*[:=]\s*{num}", txt),
        f"{prefix}_wall2": finder(
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

    fjson = os.path.join(case_subdir, "fenics_results.json")
    if os.path.exists(fjson):
        with open(fjson, "r", encoding="utf-8") as f:
            fdata = json.load(f)
        out["iteration2_max_fuel_temp"] = _first_not_none(
            _safe_nested(fdata, "temperature", "max_fuel_temp"),
            fdata.get("max_fuel_temp"), fdata.get("max_temp"))
        out["iteration2_avg_fuel_temp"] = _first_not_none(
            _safe_nested(fdata, "temperature", "average_fuel_temp"),
            fdata.get("average_fuel_temp"))
        out["iteration2_max_monolith_temp"] = _first_not_none(
            _safe_nested(fdata, "temperature", "max_monolith_temp"),
            fdata.get("max_monolith_temp"))
        out["iteration2_monolith_new_temperature"] = _first_not_none(
            _safe_nested(fdata, "temperature", "average_monolith_temp"),
            fdata.get("average_monolith_temp"))
        out["iteration2_max_global_stress"] = _first_not_none(
            _safe_nested(fdata, "stress", "global_max_stress"),
            fdata.get("global_max_stress"))
        out["iteration2_wall2"] = _first_not_none(
            _safe_nested(fdata, "expansion", "max_2d_expansion_x"),
            fdata.get("newwall2"), fdata.get("wall2"))
        out["iteration2_Hcore_after"] = _first_not_none(
            _safe_nested(fdata, "expansion", "max_3d_expansion_z"),
            fdata.get("height"), fdata.get("new_height"), fdata.get("Hcore_after"))

    log_file = os.path.join(case_subdir, "out_fenicsdata_coupled.txt")
    if os.path.exists(log_file):
        with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        for k, v in _parse_iter_from_log(content, 1).items():
            out[k] = v
        for k, v in _parse_iter_from_log(content, 2).items():
            if out.get(k) is None:
                out[k] = v

    return out


# ------------------------------------------------------------
# HF execution
# ------------------------------------------------------------
def run_hf_case(case_i: int, label: str, theta9: np.ndarray, archive_dir: Path) -> dict:
    import generater    # noqa: F401  — loaded lazily so --dry-run works without HF env

    inputs = theta9.reshape(1, -1)
    ret = generater.start_generater(inputs=inputs, counts=1)

    if isinstance(ret, tuple) and len(ret) == 2:
        keffs, run_dir = ret
    elif isinstance(ret, dict):
        keffs = ret.get("keffs", [])
        run_dir = ret.get("run_dir") or ret.get("output_dir")
        if run_dir is None:
            raise ValueError("generater returned dict without run_dir/output_dir")
    else:
        raise ValueError(f"Unexpected generater return type: {type(ret)}")

    case_subdir = os.path.join(run_dir, "0")
    results = parse_hf_outputs(case_subdir, keffs)

    # Archive
    archive_dir.mkdir(parents=True, exist_ok=True)
    src = case_subdir if os.path.exists(case_subdir) else run_dir
    dest = archive_dir / f"case{case_i:03d}_{label}"
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(src, dest)
    results["archived_dir"] = str(dest)
    return results


# ------------------------------------------------------------
# Progress / resume
# ------------------------------------------------------------
def _progress_path(out_dir: Path) -> Path:
    return out_dir / "progress.csv"


def _load_progress(out_dir: Path) -> set:
    p = _progress_path(out_dir)
    if not p.exists():
        return set()
    df = pd.read_csv(p)
    return set((int(r.case_i), str(r.label)) for r in df.itertuples() if r.status == "ok")


def _append_progress(out_dir: Path, case_i: int, label: str, status: str,
                     elapsed_s: float, note: str = ""):
    p = _progress_path(out_dir)
    is_new = not p.exists()
    with open(p, "a", encoding="utf-8") as f:
        if is_new:
            f.write("ts,case_i,label,status,elapsed_s,note\n")
        ts = datetime.datetime.now().isoformat(timespec="seconds")
        safe_note = note.replace(",", ";").replace("\n", " | ")
        f.write(f"{ts},{case_i},{label},{status},{elapsed_s:.1f},{safe_note}\n")


def _fmt_eta(done: int, total: int, elapsed: float) -> str:
    if done == 0:
        return "?"
    rate = elapsed / done
    remain = (total - done) * rate
    return f"{remain/60:.1f} min"


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="BNN Posterior HF rerun executor")
    ap.add_argument("--input", default=None,
                    help="Input CSV; default: "
                         "<BNN_CODE>/experiments/posterior/<MODEL_ID>/hf_rerun/posterior_hf_rerun_inputs.csv")
    ap.add_argument("--out-dir", default=None,
                    help="Output dir; default: dirname(input)/results")
    ap.add_argument("--model-id", default=os.environ.get("MODEL_ID", ""),
                    help="BNN model id (needed if --input omitted)")
    ap.add_argument("--skip-existing", action="store_true", default=True,
                    help="(default on) Skip (case_i,label) already ok in progress.csv")
    ap.add_argument("--no-skip-existing", dest="skip_existing", action="store_false")
    ap.add_argument("--dry-run", action="store_true",
                    help="Don't call HF; just print what would run")
    ap.add_argument("--limit", type=int, default=0,
                    help="Run only first N rows (for smoke-test); 0 = all")
    args = ap.parse_args()

    # Resolve input path
    if args.input:
        input_csv = Path(args.input)
    else:
        if not args.model_id:
            sys.exit("[error] need --input or --model-id (or MODEL_ID env)")
        input_csv = (BNN_CODE / "experiments" / "posterior" / args.model_id
                     / "hf_rerun" / "posterior_hf_rerun_inputs.csv")
    if not input_csv.exists():
        sys.exit(f"[error] input CSV not found: {input_csv}")

    # Resolve out dir
    if args.out_dir:
        out_dir = Path(args.out_dir)
    else:
        out_dir = input_csv.parent / "results"
    out_dir.mkdir(parents=True, exist_ok=True)

    df_in = pd.read_csv(input_csv)
    if args.limit > 0:
        df_in = df_in.head(args.limit)

    # Basic schema validation
    required = {"case_i", "label"}
    for k in MATERIAL_KEYS:
        required.add(f"theta9_post__{k}")
    missing = required - set(df_in.columns)
    if missing:
        sys.exit(f"[error] input CSV missing columns: {sorted(missing)}")

    already_done = _load_progress(out_dir) if args.skip_existing else set()

    # Metadata up front
    meta = {
        "input_csv":       str(input_csv),
        "out_dir":         str(out_dir),
        "model_id":        args.model_id,
        "n_total_rows":    len(df_in),
        "n_already_done":  len(already_done),
        "labels_seen":     sorted(df_in["label"].unique().tolist()),
        "dry_run":         args.dry_run,
        "started_at":      datetime.datetime.now().isoformat(timespec="seconds"),
        "material_keys":   MATERIAL_KEYS,
        "all_output_cols": ALL_OUTPUT_COLS,
    }
    with open(out_dir / "posterior_hf_rerun_meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)

    print("=" * 64)
    print(f"BNN POSTERIOR HF RERUN   model={args.model_id or '(from CSV)'}")
    print(f"  input      : {input_csv}")
    print(f"  out_dir    : {out_dir}")
    print(f"  rows total : {len(df_in)}   already_ok: {len(already_done)}")
    print(f"  labels     : {meta['labels_seen']}")
    print(f"  dry_run    : {args.dry_run}")
    print("=" * 64)

    summary_rows = []
    per_output_rows = []
    archive_dir = out_dir / "archive"

    # Optional: append to existing summary if present
    sum_csv = out_dir / "posterior_hf_rerun_summary.csv"
    per_csv = out_dir / "posterior_hf_rerun_per_output.csv"
    if sum_csv.exists() and args.skip_existing:
        prev_sum = pd.read_csv(sum_csv).to_dict(orient="records")
        prev_per = pd.read_csv(per_csv).to_dict(orient="records") if per_csv.exists() else []
        summary_rows.extend(prev_sum)
        per_output_rows.extend(prev_per)

    t0 = time.time()
    done = 0
    for idx, row in df_in.reset_index(drop=True).iterrows():
        ci    = int(row["case_i"])
        label = str(row["label"])
        key   = (ci, label)
        tag   = f"{ci:03d}_{label}"

        if key in already_done:
            print(f"[skip] case {tag}  (already ok in progress.csv)")
            continue

        theta9 = np.array([row[f"theta9_post__{k}"] for k in MATERIAL_KEYS], dtype=float)

        print(f"\n[{idx+1}/{len(df_in)}] case {tag}  "
              f"category={row.get('category','?')}  "
              f"stress_true={row.get('stress_true_MPa', float('nan')):.2f} MPa")
        print("  θ9 = " + "  ".join(
            f"{k}={theta9[i]:.4g}" for i, k in enumerate(MATERIAL_KEYS)))

        if args.dry_run:
            print("  [dry-run] would call generater.start_generater()")
            _append_progress(out_dir, ci, label, "dry-run", 0.0)
            continue

        t_case = time.time()
        try:
            hf_results = run_hf_case(ci, label, theta9, archive_dir)
            dt = time.time() - t_case

            # summary row (primary outputs + errors)
            out_row = {
                "case_i":           ci,
                "label":            label,
                "category":         row.get("category", ""),
                "row_idx":          int(row.get("row_idx", -1)),
                "stress_true_MPa":  float(row.get("stress_true_MPa", float("nan"))),
                "archived_dir":     hf_results.get("archived_dir", ""),
                "elapsed_s":        round(dt, 1),
            }
            for col in PRIMARY_OUTPUTS:
                true_v = float(row[f"y_true__{col}"]) if f"y_true__{col}" in row else float("nan")
                hf_v   = hf_results.get(col)
                out_row[f"y_true__{col}"] = true_v
                out_row[f"y_hf__{col}"]   = hf_v
                if hf_v is not None and not np.isnan(true_v):
                    out_row[f"abs_err__{col}"] = abs(float(hf_v) - true_v)
                    out_row[f"rel_err__{col}"] = (
                        abs(float(hf_v) - true_v) / abs(true_v)
                        if true_v != 0 else float("nan")
                    )
                else:
                    out_row[f"abs_err__{col}"] = float("nan")
                    out_row[f"rel_err__{col}"] = float("nan")
            summary_rows.append(out_row)

            # per-output long format (all 15)
            for col in ALL_OUTPUT_COLS:
                per_output_rows.append({
                    "case_i":   ci,
                    "label":    label,
                    "output":   col,
                    "y_true":   float(row[f"y_true__{col}"]) if f"y_true__{col}" in row else np.nan,
                    "y_hf":     hf_results.get(col),
                })

            # flush after each case (long jobs → crash safety)
            pd.DataFrame(summary_rows).to_csv(sum_csv, index=False, encoding="utf-8-sig")
            pd.DataFrame(per_output_rows).to_csv(per_csv, index=False, encoding="utf-8-sig")

            hf_stress = hf_results.get("iteration2_max_global_stress")
            print(f"  [ok] {dt:.1f}s   hf_stress={hf_stress if hf_stress is not None else 'N/A'}"
                  f"   true={out_row['stress_true_MPa']:.2f}")
            _append_progress(out_dir, ci, label, "ok", dt)
            done += 1

        except Exception as e:
            dt = time.time() - t_case
            tb_short = "".join(traceback.format_exception_only(type(e), e)).strip()
            print(f"  [FAIL] {dt:.1f}s   {tb_short}", file=sys.stderr)
            _append_progress(out_dir, ci, label, "fail", dt, note=tb_short)
            # continue to next case; do not re-raise

        # ETA
        elapsed = time.time() - t0
        remaining = len(df_in) - (idx + 1)
        if done > 0:
            print(f"  [eta] done={done}  remain={remaining}  "
                  f"ETA≈{_fmt_eta(done, len(df_in), elapsed)}")

    # Finalize
    meta["ended_at"] = datetime.datetime.now().isoformat(timespec="seconds")
    meta["total_elapsed_s"] = round(time.time() - t0, 1)
    with open(out_dir / "posterior_hf_rerun_meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 64)
    print(f"DONE. summary: {sum_csv}")
    print(f"      per_out: {per_csv}")
    print(f"      archive: {archive_dir}/case*_*/")
    print(f"      total elapsed: {meta['total_elapsed_s']} s")
    print("=" * 64)


if __name__ == "__main__":
    main()
