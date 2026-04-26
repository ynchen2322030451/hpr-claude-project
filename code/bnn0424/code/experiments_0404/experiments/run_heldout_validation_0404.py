# run_heldout_validation_0404.py
# ============================================================
# Held-out posterior validation: tests calibration robustness on
# DIFFERENT test cases (excluding the canonical 18 benchmark)
# and across multiple observation noise levels (1%, 2%, 5%).
#
# Reuses MCMC infrastructure from run_posterior_0404.py.
#
# 调用方式:
#   MODEL_ID=bnn-phy-mono python run_heldout_validation_0404.py
#   MODEL_ID=bnn-baseline  python run_heldout_validation_0404.py
#
# 输出:
#   experiments_0404/experiments/posterior/<model_id>/heldout_validation/
#     heldout_summary.csv          — per-param recovery for each (case, noise)
#     heldout_aggregate.csv        — coverage by (category, noise_frac)
#     heldout_case_meta.json       — case metadata
#     heldout_manifest.json
# ============================================================

import os, sys, json, logging
from datetime import datetime

import numpy as np
import pandas as pd

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_CODE_ROOT = _SCRIPT_DIR
while _CODE_ROOT and not os.path.basename(_CODE_ROOT) == 'code':
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
    INPUT_COLS, OUTPUT_COLS, PRIMARY_OUTPUTS,
    PRIMARY_STRESS_OUTPUT, PRIMARY_STRESS_THRESHOLD,
    INVERSE_CALIB_PARAMS, BNN_N_MC_POSTERIOR,
    SEED, DEVICE, FIXED_SPLIT_DIR,
    experiment_dir, ensure_dir,
)
from model_registry_0404 import MODELS
from manifest_utils_0404 import write_manifest, make_experiment_manifest, resolve_output_dir
from bnn_model import get_device, seed_all

from run_posterior_0404 import (
    _resolve_artifacts, _load_model, _load_scalers,
    _get_prior_stats, _log_prior, _log_likelihood,
    _reflect_bounds, _expand_to_full,
    run_mcmc_multi_chain, compute_rhat,
    OBS_COLS, N_TOTAL, BURN_IN, THIN, PROPOSAL_SCALE,
)

_EVAL_DIR = os.path.join(_CODE_ROOT, 'experiments_0404', 'evaluation')
if _EVAL_DIR not in sys.path:
    sys.path.insert(0, _EVAL_DIR)
from run_eval_0404 import _attach_mf_reorder

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ────────────────────────────────────────────────────────────
# Canonical benchmark row indices to EXCLUDE
# (from rerun_4chain/benchmark_case_meta.json)
# ────────────────────────────────────────────────────────────
CANONICAL_BENCHMARK_ROWS = {46, 35, 139, 63, 144, 6,
                            381, 78, 225, 105, 187, 31,
                            415, 436, 219, 222, 43, 124}

# ────────────────────────────────────────────────────────────
# Held-out validation config
# ────────────────────────────────────────────────────────────
HELDOUT_SEED = SEED + 7777
N_CASES_PER_CAT = 6
NOISE_FRACS = [0.01, 0.02, 0.05]
N_CHAINS = 4
TAU = PRIMARY_STRESS_THRESHOLD


def select_heldout_cases(test_df: pd.DataFrame) -> list:
    """Select held-out test cases excluding the canonical 18 benchmark cases."""
    s = test_df[PRIMARY_STRESS_OUTPUT].values
    low_idx = np.where(s < 0.92 * TAU)[0]
    near_idx = np.where((s >= 0.92 * TAU) & (s < TAU))[0]
    high_idx = np.where(s >= TAU)[0]

    low_idx = np.array([i for i in low_idx if i not in CANONICAL_BENCHMARK_ROWS])
    near_idx = np.array([i for i in near_idx if i not in CANONICAL_BENCHMARK_ROWS])
    high_idx = np.array([i for i in high_idx if i not in CANONICAL_BENCHMARK_ROWS])

    rng = np.random.RandomState(HELDOUT_SEED)
    selected = []
    for cat_idx, label in [(low_idx, "low"), (near_idx, "near"), (high_idx, "high")]:
        n_cat = min(N_CASES_PER_CAT, len(cat_idx))
        if n_cat > 0:
            chosen = rng.choice(cat_idx, n_cat, replace=False)
            selected.extend([(int(i), label) for i in chosen])

    return selected


def run_heldout_validation(
    model_id: str, model, sx, sy, device,
    train_df: pd.DataFrame, test_df: pd.DataFrame,
    out_dir: str,
):
    prior_stats = _get_prior_stats(train_df)
    selected = select_heldout_cases(test_df)
    obs_idx = [OUTPUT_COLS.index(c) for c in OBS_COLS]

    logger.info(f"[heldout][{model_id}] {len(selected)} cases × {len(NOISE_FRACS)} noise levels")
    logger.info(f"  Cases: {[(ri, cat) for ri, cat in selected]}")

    recovery_rows = []
    case_meta = []

    for ci, (row_idx, cat) in enumerate(selected):
        case_row = test_df.iloc[row_idx]
        x_true = case_row[INPUT_COLS].values.astype(float)
        y_true_all = case_row[OUTPUT_COLS].values.astype(float)
        y_obs_full = y_true_all[obs_idx]
        stress_true = float(case_row[PRIMARY_STRESS_OUTPUT]) if PRIMARY_STRESS_OUTPUT in case_row.index else float('nan')

        case_info = {
            "case_idx": ci, "row_idx": row_idx, "category": cat,
            "stress_true": stress_true,
        }

        for nf in NOISE_FRACS:
            noise = np.abs(y_obs_full) * nf + 1e-10
            y_obs_noisy = y_obs_full + np.random.RandomState(HELDOUT_SEED + ci * 100 + int(nf * 1000)).normal(0, noise)

            base_seed = HELDOUT_SEED + 5000 + ci * 300 + int(nf * 10000)
            posterior, accept_rate, rhat, _ = run_mcmc_multi_chain(
                ref_x_full=x_true,
                y_obs=y_obs_noisy,
                obs_noise=noise,
                prior_stats=prior_stats,
                model=model, sx=sx, sy=sy, device=device,
                base_seed=base_seed,
                n_chains=N_CHAINS,
            )

            rhat_dict = {p: float(rhat[pi]) for pi, p in enumerate(INVERSE_CALIB_PARAMS)}
            n_post = len(posterior)

            for pi, param in enumerate(INVERSE_CALIB_PARAMS):
                p_true = float(x_true[INPUT_COLS.index(param)])
                post_mean = float(np.mean(posterior[:, pi]))
                post_std = float(np.std(posterior[:, pi]))
                post_lo = float(np.percentile(posterior[:, pi], 5))
                post_hi = float(np.percentile(posterior[:, pi], 95))
                in_ci = bool(post_lo <= p_true <= post_hi)

                recovery_rows.append({
                    "case_idx": ci,
                    "row_idx": row_idx,
                    "category": cat,
                    "noise_frac": nf,
                    "param": param,
                    "true_value": p_true,
                    "post_mean": post_mean,
                    "post_std": post_std,
                    "post_lo_5": post_lo,
                    "post_hi_95": post_hi,
                    "in_90ci": in_ci,
                    "bias": post_mean - p_true,
                    "rel_bias": (post_mean - p_true) / (abs(p_true) + 1e-30),
                    "accept_rate": accept_rate,
                    "n_posterior": n_post,
                    "stress_true_MPa": stress_true,
                    "rhat": rhat_dict[param],
                })

            rhat_ok = all(v < 1.1 for v in rhat_dict.values())
            logger.info(
                f"  case {ci+1}/{len(selected)} noise={nf:.0%}: "
                f"accept={accept_rate:.3f}, "
                f"max_Rhat={max(rhat_dict.values()):.4f}"
                f"{' OK' if rhat_ok else ' NOT CONVERGED'}"
            )

        case_meta.append(case_info)

    df_rec = pd.DataFrame(recovery_rows)
    df_rec.to_csv(os.path.join(out_dir, "heldout_summary.csv"), index=False)

    with open(os.path.join(out_dir, "heldout_case_meta.json"), "w") as f:
        json.dump(case_meta, f, indent=2)

    agg = df_rec.groupby(["category", "noise_frac", "param"])["in_90ci"].agg(
        ["mean", "sum", "count"]
    ).reset_index()
    agg.columns = ["category", "noise_frac", "param", "coverage", "n_covered", "n_total"]
    agg.to_csv(os.path.join(out_dir, "heldout_aggregate.csv"), index=False)

    logger.info(f"\n[heldout][{model_id}] Coverage summary:")
    for nf in NOISE_FRACS:
        sub = df_rec[df_rec["noise_frac"] == nf]
        cov = sub["in_90ci"].mean()
        logger.info(f"  noise={nf:.0%}: overall 90CI coverage = {cov:.3f} ({int(sub['in_90ci'].sum())}/{len(sub)})")

    for cat in ["low", "near", "high"]:
        sub = df_rec[df_rec["category"] == cat]
        if len(sub) > 0:
            cov = sub["in_90ci"].mean()
            logger.info(f"  {cat}: coverage = {cov:.3f} (across all noise levels)")

    return df_rec, case_meta


if __name__ == "__main__":
    model_id = os.environ.get("MODEL_ID", "bnn-phy-mono")

    if model_id not in MODELS:
        raise ValueError(f"Unknown MODEL_ID: {model_id}. Available: {list(MODELS.keys())}")

    base_dir = os.path.join(experiment_dir("posterior"), model_id, "heldout_validation")
    out_dir = resolve_output_dir(
        base_dir,
        script_name=os.path.basename(__file__),
    )

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    fh = logging.FileHandler(os.path.join(out_dir, f"heldout_{ts}.log"))
    fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(fh)

    logger.info(f"heldout_validation | model={model_id}")
    logger.info(f"  N_CASES_PER_CAT={N_CASES_PER_CAT}, NOISE_FRACS={NOISE_FRACS}")
    logger.info(f"  N_CHAINS={N_CHAINS}, N_TOTAL={N_TOTAL}, BURN_IN={BURN_IN}")
    logger.info(f"  Excluded canonical rows: {sorted(CANONICAL_BENCHMARK_ROWS)}")

    device = get_device(DEVICE)
    seed_all(HELDOUT_SEED)
    ckpt_path, scaler_path = _resolve_artifacts(model_id)
    model = _load_model(ckpt_path, device)
    scalers = _load_scalers(scaler_path)
    _attach_mf_reorder(model, scalers)
    sx, sy = scalers["sx"], scalers["sy"]
    model.eval()

    train_df = pd.read_csv(os.path.join(FIXED_SPLIT_DIR, "train.csv"))
    test_df = pd.read_csv(os.path.join(FIXED_SPLIT_DIR, "test.csv"))

    logger.info(f"  train: {len(train_df)}, test: {len(test_df)}")

    df_rec, case_meta = run_heldout_validation(
        model_id, model, sx, sy, device, train_df, test_df, out_dir
    )

    overall_cov = float(df_rec["in_90ci"].mean())
    outputs_saved = [
        os.path.join(out_dir, f)
        for f in ["heldout_summary.csv", "heldout_aggregate.csv", "heldout_case_meta.json"]
        if os.path.exists(os.path.join(out_dir, f))
    ]
    mf = make_experiment_manifest(
        experiment_id=f"heldout_validation",
        model_id=model_id,
        input_source=FIXED_SPLIT_DIR,
        outputs_saved=outputs_saved,
        key_results={
            "n_cases": len(case_meta),
            "noise_fracs": NOISE_FRACS,
            "n_chains": N_CHAINS,
            "overall_90ci_coverage": overall_cov,
            "excluded_canonical_rows": sorted(CANONICAL_BENCHMARK_ROWS),
        },
        source_script=__file__,
        extra={
            "N_total_mcmc": N_TOTAL,
            "burn_in": BURN_IN,
            "thin": THIN,
            "obs_noise_fracs": NOISE_FRACS,
            "calib_params": INVERSE_CALIB_PARAMS,
            "obs_cols": OBS_COLS,
            "n_mc_posterior": BNN_N_MC_POSTERIOR,
            "heldout_seed": HELDOUT_SEED,
        },
    )
    write_manifest(os.path.join(out_dir, "heldout_manifest.json"), mf)
    logger.info(f"[{model_id}] heldout validation done — overall coverage: {overall_cov:.3f}")
