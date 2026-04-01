# extract_dataset_v3.py
import os
import re
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, Optional, List, Tuple

# ===================== 只改这里 =====================
INPUT_ROOT = "/home/tjzs/Documents/fenics_data/fenics_data/new_output"
OUTPUT_CSV = "/home/tjzs/Documents/fenics_data/fenics_data/txt_extract/dataset_v3.csv"

READ_AUX = True
AUX_FILES = {
    "fuel_nearby_avestress": "fuel_nearby_avestress.txt",
    "fuel_nearby_maxstress": "fuel_nearby_maxstress.txt",
    "hp_nearby_avestress": "hp_nearby_avestress.txt",
    "hp_nearby_maxstress": "hp_nearby_maxstress.txt",
    "fuel_T_list": "fuel_T_list.txt",
    # "thermal_output_data": "thermal_output_data.npy",
    "out_fenicsdata_coupled": "out_fenicsdata_coupled.txt",  # ✅你这份日志也当作aux解析
}
# ====================================================


def _fnum(x: Optional[str]) -> float:
    try:
        return float(x)
    except Exception:
        return float("nan")

def _find_one(pattern: str, text: str) -> float:
    m = re.search(pattern, text, re.DOTALL)
    return _fnum(m.group(1)) if m else float("nan")

def _find_all(pattern: str, text: str) -> List[str]:
    return re.findall(pattern, text, re.DOTALL)

def _parse_numbers_from_line(line: str) -> List[float]:
    line = line.strip().replace(",", " ")
    if not line:
        return []
    vals = []
    for p in line.split():
        try:
            vals.append(float(p))
        except Exception:
            pass
    return vals

def load_txt_array(path: str) -> Optional[np.ndarray]:
    if not os.path.exists(path):
        return None
    rows = []
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            v = _parse_numbers_from_line(line)
            if v:
                rows.append(v)
    if not rows:
        return None
    m = max(len(r) for r in rows)
    arr = np.full((len(rows), m), np.nan, dtype=float)
    for i, r in enumerate(rows):
        arr[i, :len(r)] = r
    return arr

def summarize_array(arr: np.ndarray) -> Dict[str, float]:
    flat = arr.reshape(-1)
    flat = flat[~np.isnan(flat)]
    if flat.size == 0:
        return {"mean": np.nan, "max": np.nan, "p95": np.nan}
    return {
        "mean": float(np.mean(flat)),
        "max": float(np.max(flat)),
        "p95": float(np.quantile(flat, 0.95)),
    }

# ---------- 1) 材料参数 ----------
MAT_PATTERNS = {
    "E_slope":      r"E_slope_values:\s*\[([-\d.eE+]+)\]",
    "E_intercept":  r"E_intercept_values:\s*\[([-\d.eE+]+)\]",
    "nu":           r"nu_values:\s*\[([-\d.eE+]+)\]",
    "alpha_base":   r"alpha_base_values:\s*\[([-\d.eE+]+)\]",
    "alpha_slope":  r"alpha_slope_values:\s*\[([-\d.eE+]+)\]",
    "SS316_T_ref":  r"SS316_T_ref_values:\s*\[([-\d.eE+]+)\]",
    "SS316_k_ref":  r"SS316_k_ref_values:\s*\[([-\d.eE+]+)\]",
    "SS316_alpha":  r"SS316_alpha_values:\s*\[([-\d.eE+]+)\]",  # 你已澄清= k_slope
}

def extract_material(content: str) -> Dict[str, float]:
    return {k: _find_one(pat, content) for k, pat in MAT_PATTERNS.items()}

# ---------- 2) iter块解析（更稳健：按Iteration begin切块） ----------
ITER_BEGIN = re.compile(r"=+Iteration\s+(\d+)\s+begins=+", re.IGNORECASE)

def split_iterations(content: str) -> Dict[int, str]:
    iters = {}
    matches = list(ITER_BEGIN.finditer(content))
    if not matches:
        return iters
    for idx, m in enumerate(matches):
        i = int(m.group(1))
        start = m.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(content)
        iters[i] = content[start:end]
    return iters

FENICS_PAT = {
    "avg_fuel_temp":      r"平均燃料温度:\s*([-\d.]+)\s*K",
    "max_fuel_temp":      r"燃料最高温度:\s*([-\d.]+)\s*K",
    "max_monolith_temp":  r"单体最高温度:\s*([-\d.]+)\s*K",
    "max_global_stress":  r"全局最大应力:\s*([-\d.]+)\s*MPa",
}
POST_PAT = {
    "monolith_new_temperature": r"monolith new temperature:\s*([-\d.]+)",
    "Hcore_after":              r"更新后的 Hcore:\s*([-\d.]+)",
    "wall2":                    r"New wall2:\s*([-\d.]+)\s*cm",
}

def extract_iteration_fields(iter_text: str) -> Dict[str, float]:
    d = {}
    for k, pat in FENICS_PAT.items():
        d[k] = _find_one(pat, iter_text)
    for k, pat in POST_PAT.items():
        d[k] = _find_one(pat, iter_text)
    return d

# ---------- 3) keff/std ----------
def extract_keff_std(content: str) -> Tuple[List[float], List[float]]:
    keffs = [_fnum(s) for s in _find_all(r"k-eff:\s*([-\d.]+)", content)]
    stds  = [_fnum(s) for s in _find_all(r"std:\s*([-\d.]+)", content)]
    keffs = [x for x in keffs if not np.isnan(x)]
    stds  = [x for x in stds if not np.isnan(x)]
    return keffs, stds

# ---------- 4) 解析 out_fenicsdata_coupled.txt ----------
DT_PAT_BEGIN = re.compile(r"time_begin_fenics\s*=\s*(.+)")
DT_PAT_END   = re.compile(r"time_end_fenics\s*=\s*(.+)")
HP_STEP_PAT  = re.compile(r"all_HP_step\s*=\s*(\d+)")

def parse_datetime(s: str) -> Optional[datetime]:
    s = s.strip()
    # 你的格式像：2026-02-13 04:05:37.724332
    for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(s, fmt)
        except Exception:
            pass
    return None

def extract_fenics_log_features(path: str) -> Dict[str, float]:
    """
    从日志里抽取：
      - duration per segment (end-begin)
      - total/mean/max duration
      - all_HP_step（如果多次出现，取众数/最后一次都行；这里取最后一次）
      - segment_count
    """
    if not os.path.exists(path):
        return {}

    begins: List[datetime] = []
    ends: List[datetime] = []
    hp_steps: List[int] = []

    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            mb = DT_PAT_BEGIN.search(line)
            if mb:
                dt = parse_datetime(mb.group(1))
                if dt: begins.append(dt)
                continue
            me = DT_PAT_END.search(line)
            if me:
                dt = parse_datetime(me.group(1))
                if dt: ends.append(dt)
                continue
            ms = HP_STEP_PAT.search(line)
            if ms:
                try:
                    hp_steps.append(int(ms.group(1)))
                except Exception:
                    pass

    # pair begins/ends in order
    n = min(len(begins), len(ends))
    durations = []
    for i in range(n):
        dur = (ends[i] - begins[i]).total_seconds()
        if dur >= 0:
            durations.append(dur)

    out = {}
    out["fenics_segment_count"] = float(len(durations))
    if durations:
        out["fenics_duration_sum_sec"] = float(np.sum(durations))
        out["fenics_duration_mean_sec"] = float(np.mean(durations))
        out["fenics_duration_max_sec"] = float(np.max(durations))
    else:
        out["fenics_duration_sum_sec"] = np.nan
        out["fenics_duration_mean_sec"] = np.nan
        out["fenics_duration_max_sec"] = np.nan

    out["all_HP_step"] = float(hp_steps[-1]) if hp_steps else np.nan
    return out

# ---------- 5) 单样本提取 ----------
def extract_case(case_dir: str) -> Optional[Dict[str, object]]:
    printout = os.path.join(case_dir, "PrintOut.txt")
    if not os.path.exists(printout):
        return None

    try:
        with open(printout, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        row: Dict[str, object] = {}
        row["case_dir"] = case_dir
        row.update(extract_material(content))

        keffs, stds = extract_keff_std(content)
        row["iteration1_keff"] = keffs[0] if len(keffs) > 0 else np.nan
        row["iteration2_keff"] = keffs[1] if len(keffs) > 1 else np.nan
        row["iteration1_keff_std"] = stds[0] if len(stds) > 0 else np.nan
        row["iteration2_keff_std"] = stds[1] if len(stds) > 1 else np.nan

        iters = split_iterations(content)
        row["total_iterations"] = int(len(iters))

        for it in [1, 2]:
            fields = extract_iteration_fields(iters.get(it, ""))
            if it == 1:
                row["iteration1_avg_fuel_temp"] = fields.get("avg_fuel_temp", np.nan)
                row["iteration1_max_fuel_temp"] = fields.get("max_fuel_temp", np.nan)
                row["iteration1_max_monolith_temp"] = fields.get("max_monolith_temp", np.nan)
                row["iteration1_max_global_stress"] = fields.get("max_global_stress", np.nan)
                row["iteration1_monolith_new_temperature"] = fields.get("monolith_new_temperature", np.nan)
                row["iteration1_Hcore_after"] = fields.get("Hcore_after", np.nan)
                row["iteration1_wall2"] = fields.get("wall2", np.nan)
            else:
                row["iteration2_avg_fuel_temp"] = fields.get("avg_fuel_temp", np.nan)
                row["iteration2_max_fuel_temp"] = fields.get("max_fuel_temp", np.nan)
                row["iteration2_max_monolith_temp"] = fields.get("max_monolith_temp", np.nan)
                row["iteration2_max_global_stress"] = fields.get("max_global_stress", np.nan)
                row["iteration2_monolith_new_temperature"] = fields.get("monolith_new_temperature", np.nan)
                row["iteration2_Hcore_after"] = fields.get("Hcore_after", np.nan)
                row["iteration2_wall2"] = fields.get("wall2", np.nan)

        # aux摘要（包括日志 out_fenicsdata_coupled.txt）
        if READ_AUX:
            for key, fname in AUX_FILES.items():
                p = os.path.join(case_dir, fname)
                if not os.path.exists(p):
                    continue

                if key == "out_fenicsdata_coupled":
                    feats = extract_fenics_log_features(p)
                    for kk, vv in feats.items():
                        row[f"aux_{kk}"] = vv
                    continue

                if p.endswith(".npy"):
                    try:
                        arr = np.load(p)
                        flat = arr.reshape(-1)
                        row[f"aux_{key}_mean"] = float(np.mean(flat))
                        row[f"aux_{key}_max"]  = float(np.max(flat))
                        row[f"aux_{key}_p95"]  = float(np.quantile(flat, 0.95))
                    except Exception:
                        row[f"aux_{key}_mean"] = np.nan
                        row[f"aux_{key}_max"]  = np.nan
                        row[f"aux_{key}_p95"]  = np.nan
                else:
                    arr = load_txt_array(p)
                    if arr is None:
                        continue
                    summ = summarize_array(arr)
                    row[f"aux_{key}_mean"] = summ["mean"]
                    row[f"aux_{key}_max"]  = summ["max"]
                    row[f"aux_{key}_p95"]  = summ["p95"]

        return row

    except Exception as e:
        print(f"[ERROR] {case_dir}: {e}")
        return None


def build_dataset(input_root: str, output_csv: str) -> pd.DataFrame:
    rows = []
    total_seen = 0

    for folder in os.listdir(input_root):
        folder_path_0 = os.path.join(input_root, folder)
        if not os.path.isdir(folder_path_0):
            continue

        for folder_count in os.listdir(folder_path_0):
            case_dir = os.path.join(folder_path_0, folder_count)
            if not os.path.isdir(case_dir):
                continue

            printout = os.path.join(case_dir, "PrintOut.txt")
            if not os.path.exists(printout):
                continue

            total_seen += 1
            case_id = f"{folder}_{folder_count}"
            print(f"Processing: {case_id}")

            row = extract_case(case_dir)
            if row is None:
                continue
            row["case_id"] = case_id
            rows.append(row)

    if not rows:
        raise RuntimeError("No valid cases found. Check INPUT_ROOT and PrintOut.txt existence.")

    df = pd.DataFrame(rows)

    # 强制数值列为float，避免'N/A'污染
    for c in df.columns:
        if c in ("case_id", "case_dir"):
            continue
        df[c] = pd.to_numeric(df[c], errors="coerce")

    df.to_csv(output_csv, index=False, encoding="utf-8-sig")

    print("\n================ SUMMARY ================")
    print(f"Total PrintOut.txt found: {total_seen}")
    print(f"Total rows saved: {len(df)}")
    miss = df.isna().mean().sort_values(ascending=False).head(25)
    print("\nTop-25 missing-rate columns:")
    print(miss)
    print(f"\nSaved to: {output_csv}")
    return df


if __name__ == "__main__":
    print("Extractor v3: PrintOut + aux(txt/npy/log) -> one clean CSV")
    build_dataset(INPUT_ROOT, OUTPUT_CSV)