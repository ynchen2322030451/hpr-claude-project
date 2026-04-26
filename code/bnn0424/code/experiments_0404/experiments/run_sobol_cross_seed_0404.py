# run_sobol_cross_seed_0404.py
# ============================================================
# Cross-seed Sobol validation: tests whether Sobol index
# RANKINGS are stable across different quasi-random Saltelli
# sample seeds, using the SAME canonical model checkpoint.
#
# This validates that the sensitivity analysis conclusion
# (which parameters dominate) is not an artifact of a
# particular random draw.
#
# Approach:
#   For each seed in CROSS_SEEDS, generate independent
#   Saltelli (A, B, AB_j) matrices, compute Jansen S1/ST
#   with N_REPEATS bootstrap replicates, and record per-seed
#   point estimates + CI.  Then aggregate across seeds to
#   report mean/std/min/max and flag any rank changes.
#
# Usage (on server, pytorch-env):
#   MODEL_ID=bnn-phy-mono python run_sobol_cross_seed_0404.py
#   MODEL_ID=bnn-baseline  python run_sobol_cross_seed_0404.py
#
# Output:
#   experiments/sobol/<model_id>/cross_seed_validation/
#     cross_seed_sobol_summary.csv      — per-(seed, output, param) indices
#     cross_seed_sobol_stability.csv    — aggregated stability metrics
#     cross_seed_manifest.json
# ============================================================

import os, sys, json, logging
from datetime import datetime

import numpy as np
import pandas as pd

# ────────────────────────────────────────────────────────────
# sys.path setup (same pattern as run_heldout_validation_0404.py)
# ────────────────────────────────────────────────────────────
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_CODE_ROOT = _SCRIPT_DIR
while _CODE_ROOT and os.path.basename(_CODE_ROOT) != 'code':
    _CODE_ROOT = os.path.dirname(_CODE_ROOT)
_BNN_CODE_DIR = _CODE_ROOT
_BNN_CONFIG_DIR = os.path.join(_CODE_ROOT, 'experiments_0404', 'config')
_CODE_TOP = os.path.dirname(os.path.dirname(_CODE_ROOT))
_ROOT_0310 = os.path.join(_CODE_TOP, '0310')
for _p in (_SCRIPT_DIR, _BNN_CODE_DIR, _BNN_CONFIG_DIR, _ROOT_0310,
           os.environ.get('HPR_LEGACY_DIR', '')):
    if _p and os.path.isdir(_p) and _p not in sys.path:
        _is_legacy = any(seg in _p for seg in ('/0310', 'hpr_legacy'))
        if _is_legacy:
            if _p not in sys.path:
                sys.path.append(_p)
        else:
            sys.path.insert(0, _p)

from experiment_config_0404 import (
    INPUT_COLS, OUTPUT_COLS, PRIMARY_SA_OUTPUTS,
    SOBOL_N_BASE, SOBOL_CI_LEVEL,
    BNN_N_MC_SOBOL,
    SEED, DEVICE,
    experiment_dir, ensure_dir,
)
from model_registry_0404 import MODELS
from manifest_utils_0404 import write_manifest, make_experiment_manifest, resolve_output_dir

# Import Sobol engine components from run_sensitivity_0404.py
from run_sensitivity_0404 import (
    _resolve_artifacts, _load_model, _load_scalers,
    _bnn_predict_mean, _jansen, _load_input_bounds, _summarize,
)
from bnn_model import get_device, seed_all

# MF reorder helper
_EVAL_DIR = os.path.join(_CODE_ROOT, 'experiments_0404', 'evaluation')
if _EVAL_DIR not in sys.path:
    sys.path.insert(0, _EVAL_DIR)
from run_eval_0404 import _attach_mf_reorder

# ────────────────────────────────────────────────────────────
# Logging
# ────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ────────────────────────────────────────────────────────────
# Cross-seed validation parameters
# ────────────────────────────────────────────────────────────
CROSS_SEEDS = [2026, 2027, 2028, 2029, 2030]

# N_REPEATS per seed — use same value as run_sensitivity_0404.py
# (50 bootstrap repeats per seed for CI estimation)
N_REPEATS = 50
CI_Z = 1.645  # 90% CI


def _sobol_one_output_seeded(
    model, sx, sy, out_idx: int, bounds: list, device,
    base_seed: int, n_base: int = SOBOL_N_BASE, n_repeats: int = N_REPEATS,
):
    """Compute Sobol S1/ST for one output, one seed.

    Identical to run_sensitivity_0404._sobol_one_output except
    base_seed is an explicit argument (not hardcoded to SEED).

    Returns
    -------
    s1_all : ndarray, shape (n_repeats, d)
    st_all : ndarray, shape (n_repeats, d)
    """
    d = len(bounds)
    s1_all, st_all = [], []

    for r in range(n_repeats):
        rng = np.random.RandomState(base_seed + 1000 * r + out_idx)

        A = np.column_stack([rng.uniform(lo, hi, n_base) for lo, hi in bounds])
        B = np.column_stack([rng.uniform(lo, hi, n_base) for lo, hi in bounds])

        YA = _bnn_predict_mean(model, A, sx, sy, device)[:, out_idx]
        YB = _bnn_predict_mean(model, B, sx, sy, device)[:, out_idx]

        s1_r, st_r = [], []
        for j in range(d):
            ABj = A.copy()
            ABj[:, j] = B[:, j]
            YABj = _bnn_predict_mean(model, ABj, sx, sy, device)[:, out_idx]
            s1, st = _jansen(YA, YB, YABj)
            s1_r.append(s1)
            st_r.append(st)

        s1_all.append(s1_r)
        st_all.append(st_r)

    return np.array(s1_all, float), np.array(st_all, float)


def run_cross_seed_validation(
    model_id: str, model, sx, sy, device, out_dir: str,
    output_list: list = None,
    cross_seeds: list = None,
):
    """Run Sobol analysis across multiple Saltelli seeds and aggregate."""
    if output_list is None:
        output_list = PRIMARY_SA_OUTPUTS
    if cross_seeds is None:
        cross_seeds = CROSS_SEEDS

    bounds = _load_input_bounds()
    d = len(bounds)

    # ── Per-seed results ──
    per_seed_rows = []

    for seed_val in cross_seeds:
        logger.info(f"[cross-seed] Saltelli seed={seed_val}")

        for out_name in output_list:
            if out_name not in OUTPUT_COLS:
                logger.warning(f"  Output {out_name} not in OUTPUT_COLS, skipping")
                continue
            out_idx = OUTPUT_COLS.index(out_name)

            logger.info(
                f"  {out_name}: {N_REPEATS} reps x {SOBOL_N_BASE} samples "
                f"x {d+2} matrices x n_mc={BNN_N_MC_SOBOL}"
            )

            s1_all, st_all = _sobol_one_output_seeded(
                model, sx, sy, out_idx, bounds, device,
                base_seed=seed_val,
                n_base=SOBOL_N_BASE,
                n_repeats=N_REPEATS,
            )

            s1_mean, s1_lo, s1_hi = _summarize(s1_all)
            st_mean, st_lo, st_hi = _summarize(st_all)

            for j, inp in enumerate(INPUT_COLS):
                per_seed_rows.append({
                    "seed":       seed_val,
                    "output":     out_name,
                    "input":      inp,
                    "S1_mean":    float(s1_mean[j]),
                    "S1_ci_lo":   float(s1_lo[j]),
                    "S1_ci_hi":   float(s1_hi[j]),
                    "ST_mean":    float(st_mean[j]),
                    "ST_ci_lo":   float(st_lo[j]),
                    "ST_ci_hi":   float(st_hi[j]),
                })

            logger.info(
                f"    Top S1: {INPUT_COLS[int(np.argmax(s1_mean))]}="
                f"{s1_mean.max():.4f}"
            )

    df_per_seed = pd.DataFrame(per_seed_rows)
    csv_per_seed = os.path.join(out_dir, "cross_seed_sobol_summary.csv")
    df_per_seed.to_csv(csv_per_seed, index=False)
    logger.info(f"[cross-seed] Per-seed summary -> {csv_per_seed}")

    # ── Cross-seed aggregation ──
    stability_rows = []

    for out_name in output_list:
        sub = df_per_seed[df_per_seed["output"] == out_name]
        if sub.empty:
            continue

        for inp in INPUT_COLS:
            inp_sub = sub[sub["input"] == inp]
            s1_vals = inp_sub["S1_mean"].values
            st_vals = inp_sub["ST_mean"].values

            stability_rows.append({
                "output":     out_name,
                "input":      inp,
                "S1_cross_mean": float(np.mean(s1_vals)),
                "S1_cross_std":  float(np.std(s1_vals, ddof=1)) if len(s1_vals) > 1 else 0.0,
                "S1_cross_min":  float(np.min(s1_vals)),
                "S1_cross_max":  float(np.max(s1_vals)),
                "ST_cross_mean": float(np.mean(st_vals)),
                "ST_cross_std":  float(np.std(st_vals, ddof=1)) if len(st_vals) > 1 else 0.0,
                "ST_cross_min":  float(np.min(st_vals)),
                "ST_cross_max":  float(np.max(st_vals)),
                "n_seeds":       len(s1_vals),
            })

    df_stability = pd.DataFrame(stability_rows)

    # ── Rank stability detection ──
    # For each (output, seed), rank parameters by S1 descending.
    # Then check whether rank differs across seeds.
    rank_records = []

    for out_name in output_list:
        sub = df_per_seed[df_per_seed["output"] == out_name]
        if sub.empty:
            continue

        # Compute rank per seed
        seed_ranks = {}  # seed -> {input: rank}
        for seed_val in cross_seeds:
            seed_sub = sub[sub["seed"] == seed_val].sort_values(
                "S1_mean", ascending=False
            )
            if seed_sub.empty:
                continue
            rank_map = {
                row["input"]: rank + 1
                for rank, (_, row) in enumerate(seed_sub.iterrows())
            }
            seed_ranks[seed_val] = rank_map

        if not seed_ranks:
            continue

        for inp in INPUT_COLS:
            ranks = [seed_ranks[s][inp] for s in seed_ranks if inp in seed_ranks[s]]
            if not ranks:
                continue
            rank_records.append({
                "output": out_name,
                "input":  inp,
                "rank_mean": float(np.mean(ranks)),
                "rank_std":  float(np.std(ranks, ddof=1)) if len(ranks) > 1 else 0.0,
                "rank_min":  int(np.min(ranks)),
                "rank_max":  int(np.max(ranks)),
                "rank_range": int(np.max(ranks) - np.min(ranks)),
                "rank_stable": bool(np.max(ranks) - np.min(ranks) <= 1),
            })

    df_ranks = pd.DataFrame(rank_records)

    # Merge rank info into stability df
    if not df_ranks.empty:
        df_stability = df_stability.merge(
            df_ranks[["output", "input", "rank_mean", "rank_std",
                       "rank_min", "rank_max", "rank_range", "rank_stable"]],
            on=["output", "input"],
            how="left",
        )

    csv_stability = os.path.join(out_dir, "cross_seed_sobol_stability.csv")
    df_stability.to_csv(csv_stability, index=False)
    logger.info(f"[cross-seed] Stability summary -> {csv_stability}")

    # ── Console summary ──
    print("\n" + "=" * 70)
    print("  Cross-seed Sobol Stability Summary")
    print("=" * 70)

    for out_name in output_list:
        print(f"\n--- {out_name} ---")
        out_stab = df_stability[df_stability["output"] == out_name].sort_values(
            "S1_cross_mean", ascending=False
        )
        for _, row in out_stab.iterrows():
            stable_flag = "OK" if row.get("rank_stable", False) else "UNSTABLE"
            rank_info = ""
            if "rank_mean" in row:
                rank_info = (
                    f"  rank={row['rank_mean']:.1f}"
                    f" [{row['rank_min']}-{row['rank_max']}]"
                )
            print(
                f"  {row['input']:16s}  "
                f"S1={row['S1_cross_mean']:.4f} +/- {row['S1_cross_std']:.4f}  "
                f"ST={row['ST_cross_mean']:.4f} +/- {row['ST_cross_std']:.4f}"
                f"{rank_info}  [{stable_flag}]"
            )

    # Flag unstable parameters
    if "rank_stable" in df_stability.columns:
        unstable = df_stability[~df_stability["rank_stable"]]
        if not unstable.empty:
            print(f"\n*** {len(unstable)} parameter-output pairs have rank instability ***")
            for _, row in unstable.iterrows():
                print(
                    f"  {row['output']} / {row['input']}: "
                    f"rank range {row['rank_min']}-{row['rank_max']} "
                    f"(mean S1={row['S1_cross_mean']:.4f})"
                )
        else:
            print("\nAll parameter rankings are stable across seeds (rank range <= 1).")

    return df_per_seed, df_stability


# ────────────────────────────────────────────────────────────
# Entry point
# ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    model_id = os.environ.get("MODEL_ID", "bnn-phy-mono")

    if model_id not in MODELS:
        raise ValueError(
            f"Unknown MODEL_ID: {model_id}. Available: {list(MODELS.keys())}"
        )

    base_dir = os.path.join(
        experiment_dir("sobol"), model_id, "cross_seed_validation"
    )
    out_dir = resolve_output_dir(
        base_dir,
        script_name=os.path.basename(__file__),
    )

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    fh = logging.FileHandler(os.path.join(out_dir, f"cross_seed_{ts}.log"))
    fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(fh)

    logger.info(f"cross_seed_sobol | model={model_id}")
    logger.info(f"  CROSS_SEEDS={CROSS_SEEDS}")
    logger.info(f"  N_BASE={SOBOL_N_BASE}, N_REPEATS={N_REPEATS}, n_mc={BNN_N_MC_SOBOL}")
    logger.info(f"  PRIMARY_SA_OUTPUTS={PRIMARY_SA_OUTPUTS}")

    device = get_device(DEVICE)
    seed_all(SEED)

    ckpt_path, scaler_path = _resolve_artifacts(model_id)
    model = _load_model(ckpt_path, device)
    scalers = _load_scalers(scaler_path)
    _attach_mf_reorder(model, scalers)
    sx, sy = scalers["sx"], scalers["sy"]
    model.eval()

    logger.info(f"  checkpoint: {ckpt_path}")
    logger.info(f"  scalers:    {scaler_path}")

    df_per_seed, df_stability = run_cross_seed_validation(
        model_id, model, sx, sy, device, out_dir,
        output_list=PRIMARY_SA_OUTPUTS,
        cross_seeds=CROSS_SEEDS,
    )

    # ── Manifest ──
    outputs_saved = [
        os.path.join(out_dir, f)
        for f in [
            "cross_seed_sobol_summary.csv",
            "cross_seed_sobol_stability.csv",
        ]
        if os.path.exists(os.path.join(out_dir, f))
    ]

    # Key results for manifest
    key_results = {
        "cross_seeds": CROSS_SEEDS,
        "n_repeats_per_seed": N_REPEATS,
        "N_base": SOBOL_N_BASE,
        "n_mc_sobol": BNN_N_MC_SOBOL,
        "outputs_analyzed": PRIMARY_SA_OUTPUTS,
    }

    if "rank_stable" in df_stability.columns:
        n_unstable = int((~df_stability["rank_stable"]).sum())
        n_total_pairs = len(df_stability)
        key_results["n_unstable_pairs"] = n_unstable
        key_results["n_total_pairs"] = n_total_pairs
        key_results["all_ranks_stable"] = bool(n_unstable == 0)

    mf = make_experiment_manifest(
        experiment_id="cross_seed_sobol_validation",
        model_id=model_id,
        input_source="meta_stats.json (input bounds)",
        outputs_saved=outputs_saved,
        key_results=key_results,
        source_script=__file__,
        extra={
            "CI_level": SOBOL_CI_LEVEL,
            "CI_z": CI_Z,
        },
    )
    write_manifest(os.path.join(out_dir, "cross_seed_manifest.json"), mf)
    logger.info(f"[{model_id}] cross-seed Sobol validation done")
