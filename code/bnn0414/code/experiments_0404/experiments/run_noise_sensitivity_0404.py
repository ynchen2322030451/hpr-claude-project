# run_noise_sensitivity_0404.py
# ============================================================
# BNN 0414 — Observation noise sensitivity  NCS revision P1-#9
#
# 目的：
#   canonical benchmark 固定 OBS_NOISE_FRAC = 0.02 (2%)。审稿人会质疑：
#   如果真实仪器误差是 5% / 10%，后验宽度/覆盖率会如何变化？
#
# 本脚本扫描 OBS_NOISE_FRAC ∈ NOISE_LEVELS，在同一批 benchmark case 上
# 重跑 MCMC（n_chains=2, 短链），记录：
#   - 后验 CI 宽度 vs noise_level
#   - 90%CI 覆盖率 vs noise_level
#   - 后验预测（stress 方向）的 P(σ>131) 变化
#
# 对 paper 贡献：证明后验结论对 noise_level 的响应是单调可解释的，
# 不是"刚好调参到 2% 才显得覆盖率好"。
#
# 调用（服务器）：
#   MODEL_ID=bnn-phy-mono python run_noise_sensitivity_0404.py
#   MODEL_ID=all        python run_noise_sensitivity_0404.py
#
# 输出 (experiments_0404/experiments/posterior/<model>/noise_sensitivity/)：
#   noise_sensitivity_per_case.csv
#   noise_sensitivity_summary.csv
#   noise_sensitivity_<model>.png
#   noise_sensitivity_manifest.json
# ============================================================

import os, sys, json, logging
from datetime import datetime

import numpy as np
import pandas as pd

# ── sys.path ────────────────────────────────────────────────
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_CODE_ROOT = _SCRIPT_DIR
while _CODE_ROOT and os.path.basename(_CODE_ROOT) != 'code':
    _CODE_ROOT = os.path.dirname(_CODE_ROOT)
_BNN_CONFIG_DIR = os.path.join(_CODE_ROOT, 'experiments_0404', 'config')
_CODE_TOP = os.path.dirname(os.path.dirname(_CODE_ROOT))
_ROOT_0310 = os.path.join(_CODE_TOP, '0310')
for _p in (_SCRIPT_DIR, _CODE_ROOT, _BNN_CONFIG_DIR, _ROOT_0310,
           os.environ.get('HPR_LEGACY_DIR', '')):
    if _p and os.path.isdir(_p) and _p not in sys.path:
        if any(seg in _p for seg in ('/0310', 'hpr_legacy')):
            sys.path.append(_p)
        else:
            sys.path.insert(0, _p)

from experiment_config_0404 import (
    INPUT_COLS, OUTPUT_COLS, PRIMARY_STRESS_OUTPUT,
    INVERSE_CALIB_PARAMS, SEED, DEVICE, FIXED_SPLIT_DIR,
    experiment_dir, ensure_dir,
)
from model_registry_0404 import MODELS
from manifest_utils_0404 import make_experiment_manifest, write_manifest

import run_posterior_0404 as rp
from bnn_model import get_device, seed_all

logging.basicConfig(level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger(__name__)

# ============================================================
# 配置
# ============================================================
NOISE_LEVELS = [0.005, 0.01, 0.02, 0.03, 0.05, 0.10]  # fraction of |y_obs|
NOISE_SENS_N_CASES = int(os.environ.get("NOISE_SENS_N_CASES", 6))
NOISE_SENS_N_TOTAL = int(os.environ.get("NOISE_SENS_N_TOTAL", 4000))
NOISE_SENS_N_CHAINS = int(os.environ.get("NOISE_SENS_N_CHAINS", 2))
NOISE_SENS_BURN = int(os.environ.get("NOISE_SENS_BURN", 1000))
NOISE_SENS_THIN = int(os.environ.get("NOISE_SENS_THIN", 5))


def _run_mcmc_multi(
    ref_x_full, y_obs, obs_noise, prior_stats,
    model, sx, sy, device, base_seed, n_chains,
    n_total, burn_in, thin,
):
    n_params = len(INVERSE_CALIB_PARAMS)
    prop_scales = np.array(
        [prior_stats[c]["std"] for c in INVERSE_CALIB_PARAMS]
    ) * rp.PROPOSAL_SCALE
    chains = []
    accepts = []
    for k in range(n_chains):
        rng_k = np.random.RandomState(base_seed + k * 7919)
        theta_curr = np.array([
            rng_k.uniform(prior_stats[c]["mean"] - prior_stats[c]["std"],
                          prior_stats[c]["mean"] + prior_stats[c]["std"])
            for c in INVERSE_CALIB_PARAMS
        ])
        samples = np.zeros((n_total, n_params), float)
        lp_curr = rp._log_prior(theta_curr, prior_stats)
        ll_curr = rp._log_likelihood(theta_curr, ref_x_full, y_obs, obs_noise,
                                      model, sx, sy, device)
        lpost_curr = lp_curr + ll_curr
        n_acc = 0
        for t in range(n_total):
            theta_prop = theta_curr + rng_k.normal(0, prop_scales)
            theta_prop = rp._reflect_bounds(theta_prop, prior_stats)
            lp_prop = rp._log_prior(theta_prop, prior_stats)
            if not np.isfinite(lp_prop):
                samples[t] = theta_curr
                continue
            ll_prop = rp._log_likelihood(theta_prop, ref_x_full, y_obs, obs_noise,
                                          model, sx, sy, device)
            lpost_prop = lp_prop + ll_prop
            if np.log(rng_k.uniform()) < lpost_prop - lpost_curr:
                theta_curr = theta_prop
                lpost_curr = lpost_prop
                if t >= burn_in:
                    n_acc += 1
            samples[t] = theta_curr
        chains.append(samples[burn_in::thin])
        n_s = n_total - burn_in
        accepts.append(n_acc / n_s if n_s > 0 else 0.0)
    return np.stack(chains, axis=0), np.array(accepts)


def _select_cases(test_df, tau, n_cases, rng0):
    s = test_df[PRIMARY_STRESS_OUTPUT].values
    low_idx = np.where(s < 0.92 * tau)[0]
    near_idx = np.where((s >= 0.92 * tau) & (s < tau))[0]
    high_idx = np.where(s >= tau)[0]
    n_per_cat = max(1, n_cases // 3)
    selected = []
    for cat_idx, label in [(low_idx, "low"), (near_idx, "near"), (high_idx, "high")]:
        chosen = rng0.choice(cat_idx, min(n_per_cat, len(cat_idx)), replace=False)
        selected.extend([(int(i), label) for i in chosen])
    return selected[:n_cases]


def run_for_model(model_id: str):
    logger.info(f"[{model_id}] noise sensitivity: levels={NOISE_LEVELS}, "
                f"n_cases={NOISE_SENS_N_CASES}, n_chains={NOISE_SENS_N_CHAINS}, "
                f"n_total={NOISE_SENS_N_TOTAL}")

    device = get_device(DEVICE)
    seed_all(SEED)
    ckpt, scapath = rp._resolve_artifacts(model_id)
    model = rp._load_model(ckpt, device)
    scalers = rp._load_scalers(scapath)
    sx, sy = scalers["sx"], scalers["sy"]
    model.eval()

    train_df = pd.read_csv(os.path.join(FIXED_SPLIT_DIR, "train.csv"))
    test_df = pd.read_csv(os.path.join(FIXED_SPLIT_DIR, "test.csv"))
    prior_stats = rp._get_prior_stats(train_df)

    rng0 = np.random.RandomState(SEED + 42)
    tau = rp.TAU
    selected = _select_cases(test_df, tau, NOISE_SENS_N_CASES, rng0)

    out_dir = ensure_dir(os.path.join(experiment_dir("posterior"),
                                       model_id, "noise_sensitivity"))
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    fh = logging.FileHandler(os.path.join(out_dir, f"noise_sens_{ts}.log"))
    fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(fh)

    obs_idx = [OUTPUT_COLS.index(c) for c in rp.OBS_COLS]
    rows = []

    for ci, (row_idx, cat) in enumerate(selected):
        case_row = test_df.iloc[row_idx]
        x_true = case_row[INPUT_COLS].values.astype(float)
        y_true_all = case_row[OUTPUT_COLS].values.astype(float)
        y_obs_full = y_true_all[obs_idx]

        for lvl in NOISE_LEVELS:
            noise = np.abs(y_obs_full) * lvl + 1e-10
            # 固定 noise realization per case (独立于 level) — 但 scale 随 level 变
            unit = np.random.RandomState(SEED + ci).normal(0, 1, size=noise.shape)
            y_obs_noisy = y_obs_full + unit * np.abs(y_obs_full) * lvl

            base_seed = SEED + 4000 + ci * 100 + NOISE_LEVELS.index(lvl)
            chains, accepts = _run_mcmc_multi(
                x_true, y_obs_noisy, noise, prior_stats,
                model, sx, sy, device, base_seed,
                NOISE_SENS_N_CHAINS, NOISE_SENS_N_TOTAL,
                NOISE_SENS_BURN, NOISE_SENS_THIN,
            )
            pooled = chains.reshape(-1, chains.shape[-1])
            for pi, param in enumerate(INVERSE_CALIB_PARAMS):
                m = float(np.mean(pooled[:, pi]))
                s = float(np.std(pooled[:, pi]))
                p5 = float(np.percentile(pooled[:, pi], 5))
                p95 = float(np.percentile(pooled[:, pi], 95))
                p_true = float(x_true[INPUT_COLS.index(param)])
                rows.append({
                    "case_idx": ci,
                    "row_idx": row_idx,
                    "category": cat,
                    "param": param,
                    "noise_frac": lvl,
                    "true_value": p_true,
                    "post_mean": m,
                    "post_std": s,
                    "ci90_half_width": 0.5 * (p95 - p5),
                    "rel_ci90_half_width": 0.5 * (p95 - p5) / max(prior_stats[param]["std"], 1e-12),
                    "post_p5": p5,
                    "post_p95": p95,
                    "in_90ci_true": bool(p5 <= p_true <= p95),
                    "mean_accept_rate": float(np.mean(accepts)),
                })
            logger.info(f"  [{model_id}] case {ci+1}/{len(selected)} "
                        f"noise={lvl*100:.1f}% done, accept={np.mean(accepts):.3f}")

    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(out_dir, "noise_sensitivity_per_case.csv"), index=False)
    logger.info(f"[{model_id}] per-case 写入 ({len(df)} 行)")

    # summary: noise × param
    agg_rows = []
    for lvl in NOISE_LEVELS:
        for param in INVERSE_CALIB_PARAMS:
            sub = df[(df["noise_frac"] == lvl) & (df["param"] == param)]
            agg_rows.append({
                "model_id": model_id,
                "noise_frac": lvl,
                "param": param,
                "n_cases": len(sub),
                "mean_post_std": float(sub["post_std"].mean()),
                "mean_ci90_half_width": float(sub["ci90_half_width"].mean()),
                "mean_rel_ci90_half_width": float(sub["rel_ci90_half_width"].mean()),
                "coverage_90ci_true": float(sub["in_90ci_true"].mean()),
                "mean_accept_rate": float(sub["mean_accept_rate"].mean()),
            })
    sdf = pd.DataFrame(agg_rows)
    sdf.to_csv(os.path.join(out_dir, "noise_sensitivity_summary.csv"), index=False)
    logger.info(f"[{model_id}] summary 写入 ({len(sdf)} 行)")

    # 图: CI 宽度 vs noise level, per param
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, axes = plt.subplots(1, 2, figsize=(9, 3.5))
        ax = axes[0]
        for param in INVERSE_CALIB_PARAMS:
            sub = sdf[sdf["param"] == param]
            ax.plot(sub["noise_frac"] * 100, sub["mean_rel_ci90_half_width"],
                    "o-", label=param)
        ax.set_xlabel("Observation noise (% of |y|)")
        ax.set_ylabel("Mean rel. 90%-CI half-width\n(post vs prior σ)")
        ax.set_xscale("log")
        ax.legend(fontsize=7)
        ax.grid(True, which="both", alpha=0.3)

        ax = axes[1]
        for param in INVERSE_CALIB_PARAMS:
            sub = sdf[sdf["param"] == param]
            ax.plot(sub["noise_frac"] * 100, sub["coverage_90ci_true"],
                    "o-", label=param)
        ax.axhline(0.9, color="red", ls="--", lw=1, label="Nominal 0.90")
        ax.set_xlabel("Observation noise (% of |y|)")
        ax.set_ylabel("Coverage of true value in 90%-CI")
        ax.set_xscale("log")
        ax.set_ylim(0, 1.05)
        ax.legend(fontsize=7)
        ax.grid(True, which="both", alpha=0.3)

        fig.suptitle(f"Noise sensitivity — {model_id}", fontsize=10)
        fig.tight_layout()
        fig.savefig(os.path.join(out_dir, f"noise_sensitivity_{model_id}.png"),
                    dpi=150)
        plt.close(fig)
    except Exception as e:
        logger.warning(f"[{model_id}] 绘图失败 (non-fatal): {e}")

    summary = {
        "model_id": model_id,
        "noise_levels": NOISE_LEVELS,
        "n_cases": len(selected),
        "monotonic_width_growth": bool(all(
            (sdf[sdf["param"] == p].sort_values("noise_frac")
                ["mean_ci90_half_width"].diff().dropna() >= -1e-6).all()
            for p in INVERSE_CALIB_PARAMS)),
    }
    mf = make_experiment_manifest(
        experiment_id="posterior_noise_sensitivity",
        model_id=model_id,
        input_source=f"{FIXED_SPLIT_DIR} (train/test) + {model_id} checkpoint",
        outputs_saved=[os.path.join(out_dir, "noise_sensitivity_per_case.csv"),
                       os.path.join(out_dir, "noise_sensitivity_summary.csv")],
        key_results=summary,
        source_script=os.path.abspath(__file__),
        extra={"mcmc_config": {
            "N_TOTAL": NOISE_SENS_N_TOTAL,
            "BURN_IN": NOISE_SENS_BURN,
            "THIN": NOISE_SENS_THIN,
            "N_CHAINS": NOISE_SENS_N_CHAINS,
            "PROPOSAL_SCALE": rp.PROPOSAL_SCALE,
            "NOISE_LEVELS": NOISE_LEVELS,
        }},
    )
    write_manifest(os.path.join(out_dir, "noise_sensitivity_manifest.json"), mf)

    logger.info(f"[{model_id}] SUMMARY: {json.dumps(summary, indent=2)}")
    logger.removeHandler(fh)
    return summary


if __name__ == "__main__":
    model_id_env = os.environ.get("MODEL_ID", "all")
    model_ids = list(MODELS.keys()) if model_id_env == "all" else [model_id_env]

    all_summaries = {}
    for mid in model_ids:
        if mid not in MODELS:
            logger.error(f"unknown MODEL_ID: {mid}")
            continue
        logger.info("=" * 60)
        logger.info(f"NOISE SENSITIVITY — {mid}")
        logger.info("=" * 60)
        all_summaries[mid] = run_for_model(mid)

    if all_summaries:
        all_out = os.path.join(experiment_dir("posterior"),
                               "noise_sensitivity_all_models.json")
        with open(all_out, "w") as f:
            json.dump(all_summaries, f, indent=2)
        logger.info(f"Cross-model summary -> {all_out}")
    logger.info("NOISE SENSITIVITY DONE")
