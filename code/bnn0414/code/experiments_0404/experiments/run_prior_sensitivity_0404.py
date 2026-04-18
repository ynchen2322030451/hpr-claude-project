# run_prior_sensitivity_0404.py
# ============================================================
# BNN 0414 — Prior Sensitivity Sweep  NCS revision P1-#7
#
# 目的：
#   审稿人通常会要求："换个先验，结论会不会崩？"
#   本脚本对同一批 benchmark case 在若干替代先验下重跑 MCMC，
#   报告后验均值/CI 的偏移量 + KL(post_canonical || post_alt)。
#
# Prior variants（都以 canonical train.csv 拟合的 Gaussian 为基线）：
#   canonical  — 保留 benchmark 的原先验（μ, σ, [min,max]）
#   diffuse    — σ → 2σ
#   tight      — σ → 0.5σ
#   flat       — Uniform[min,max]（log-prior 去 Gaussian 项）
#   shift_pos  — μ → μ + 0.5σ
#   shift_neg  — μ → μ - 0.5σ
#
# 为控制成本：
#   - 只跑 PRIOR_SENS_N_CASES（默认 6）：每类别 2 个
#   - N_CHAINS = 2, N_TOTAL = PRIOR_SENS_N_TOTAL (default 4000)
#
# 调用（服务器）：
#   MODEL_ID=bnn-phy-mono python run_prior_sensitivity_0404.py
#   MODEL_ID=all        python run_prior_sensitivity_0404.py
#
# 输出 (experiments_0404/experiments/posterior/<model>/prior_sensitivity/)：
#   prior_sensitivity_per_case.csv
#   prior_sensitivity_summary.csv
#   prior_sensitivity_<model>.png
#   prior_sensitivity_manifest.json
# ============================================================

import os, sys, json, math, logging
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
PRIOR_SENS_N_CASES = int(os.environ.get("PRIOR_SENS_N_CASES", 6))
PRIOR_SENS_N_TOTAL = int(os.environ.get("PRIOR_SENS_N_TOTAL", 4000))
PRIOR_SENS_N_CHAINS = int(os.environ.get("PRIOR_SENS_N_CHAINS", 2))
PRIOR_SENS_BURN = int(os.environ.get("PRIOR_SENS_BURN", 1000))
PRIOR_SENS_THIN = int(os.environ.get("PRIOR_SENS_THIN", 5))

PRIOR_VARIANTS = ["canonical", "diffuse", "tight", "flat", "shift_pos", "shift_neg"]


def _perturb_prior(prior_stats: dict, variant: str) -> dict:
    """返回一份改造后的 prior_stats；shape 相同。"""
    out = {}
    for c, st in prior_stats.items():
        mu, sd = st["mean"], st["std"]
        lo, hi = st["min"], st["max"]
        if variant == "canonical":
            out[c] = dict(st)
        elif variant == "diffuse":
            out[c] = {"mean": mu, "std": 2.0 * sd, "min": lo, "max": hi}
        elif variant == "tight":
            out[c] = {"mean": mu, "std": 0.5 * sd, "min": lo, "max": hi}
        elif variant == "flat":
            # 标 std 为 +inf → log_prior_gaussian 项为常数；实现上在 _log_prior_alt
            # 里用 std=None 触发 flat 分支
            out[c] = {"mean": mu, "std": None, "min": lo, "max": hi}
        elif variant == "shift_pos":
            out[c] = {"mean": mu + 0.5 * sd, "std": sd, "min": lo, "max": hi}
        elif variant == "shift_neg":
            out[c] = {"mean": mu - 0.5 * sd, "std": sd, "min": lo, "max": hi}
        else:
            raise ValueError(f"unknown prior variant: {variant}")
    return out


def _log_prior_alt(theta_sub: np.ndarray, prior_alt: dict) -> float:
    """变体先验下的 log-prior；支持 flat (std=None)。"""
    lp = 0.0
    for i, c in enumerate(INVERSE_CALIB_PARAMS):
        xi = theta_sub[i]
        lo = prior_alt[c]["min"]
        hi = prior_alt[c]["max"]
        if xi < lo or xi > hi:
            return -np.inf
        sd = prior_alt[c]["std"]
        if sd is None:
            lp += -math.log(hi - lo + 1e-30)  # uniform
        else:
            mu = prior_alt[c]["mean"]
            z = (xi - mu) / sd
            lp += -0.5 * z * z - math.log(sd)
    return float(lp)


def _run_mcmc_variant(
    ref_x_full, y_obs, obs_noise, prior_alt,
    model, sx, sy, device, base_seed, n_chains,
    n_total, burn_in, thin,
):
    """类似 diagnostics 的 run_multi_chain_with_chains，但用 prior_alt。"""
    n_params = len(INVERSE_CALIB_PARAMS)
    # proposal_scale 用 canonical 的 std（保持接受率稳定）
    prop_scales = np.array(
        [max(prior_alt[c].get("std") or 0.0,
             (prior_alt[c]["max"] - prior_alt[c]["min"]) / 6.0)
         for c in INVERSE_CALIB_PARAMS]
    ) * rp.PROPOSAL_SCALE

    chains = []
    accepts = []
    for k in range(n_chains):
        rng_k = np.random.RandomState(base_seed + k * 7919)
        # 初始点：截断到 [lo, hi]
        theta_curr = np.array([
            float(np.clip(
                rng_k.uniform(prior_alt[c]["min"], prior_alt[c]["max"]),
                prior_alt[c]["min"], prior_alt[c]["max"]))
            for c in INVERSE_CALIB_PARAMS
        ])
        samples = np.zeros((n_total, n_params), float)
        lp_curr = _log_prior_alt(theta_curr, prior_alt)
        if not np.isfinite(lp_curr):
            # 兜底：回到 canonical 均值
            theta_curr = np.array([prior_alt[c]["mean"]
                                    for c in INVERSE_CALIB_PARAMS])
            lp_curr = _log_prior_alt(theta_curr, prior_alt)
        ll_curr = rp._log_likelihood(theta_curr, ref_x_full, y_obs,
                                      obs_noise, model, sx, sy, device)
        lpost_curr = lp_curr + ll_curr
        n_acc = 0
        for t in range(n_total):
            theta_prop = theta_curr + rng_k.normal(0, prop_scales)
            theta_prop = rp._reflect_bounds(theta_prop, prior_alt)
            lp_prop = _log_prior_alt(theta_prop, prior_alt)
            if not np.isfinite(lp_prop):
                samples[t] = theta_curr
                continue
            ll_prop = rp._log_likelihood(theta_prop, ref_x_full, y_obs,
                                          obs_noise, model, sx, sy, device)
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


def _gaussian_kl(m1, s1, m2, s2) -> float:
    """KL(N(m1,s1) || N(m2,s2))."""
    s1 = max(s1, 1e-12)
    s2 = max(s2, 1e-12)
    return math.log(s2 / s1) + (s1 ** 2 + (m1 - m2) ** 2) / (2 * s2 ** 2) - 0.5


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
    logger.info(f"[{model_id}] prior sensitivity: variants={PRIOR_VARIANTS}, "
                f"n_cases={PRIOR_SENS_N_CASES}, n_chains={PRIOR_SENS_N_CHAINS}, "
                f"n_total={PRIOR_SENS_N_TOTAL}")

    device = get_device(DEVICE)
    seed_all(SEED)
    ckpt, scapath = rp._resolve_artifacts(model_id)
    model = rp._load_model(ckpt, device)
    scalers = rp._load_scalers(scapath)
    sx, sy = scalers["sx"], scalers["sy"]
    model.eval()

    train_df = pd.read_csv(os.path.join(FIXED_SPLIT_DIR, "train.csv"))
    test_df = pd.read_csv(os.path.join(FIXED_SPLIT_DIR, "test.csv"))
    prior_canonical = rp._get_prior_stats(train_df)

    rng0 = np.random.RandomState(SEED + 42)
    tau = rp.TAU
    selected = _select_cases(test_df, tau, PRIOR_SENS_N_CASES, rng0)

    out_dir = ensure_dir(os.path.join(experiment_dir("posterior"),
                                       model_id, "prior_sensitivity"))
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    fh = logging.FileHandler(os.path.join(out_dir, f"prior_sens_{ts}.log"))
    fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(fh)

    obs_idx = [OUTPUT_COLS.index(c) for c in rp.OBS_COLS]
    rows = []

    for ci, (row_idx, cat) in enumerate(selected):
        case_row = test_df.iloc[row_idx]
        x_true = case_row[INPUT_COLS].values.astype(float)
        y_true_all = case_row[OUTPUT_COLS].values.astype(float)
        y_obs_full = y_true_all[obs_idx]
        noise = np.abs(y_obs_full) * rp.OBS_NOISE_FRAC + 1e-10
        y_obs_noisy = y_obs_full + np.random.RandomState(SEED + ci).normal(0, noise)

        logger.info(f"  [{model_id}] case {ci+1}/{len(selected)} "
                    f"(row={row_idx}, cat={cat})")

        # canonical 先跑一次，后面做对比 baseline
        canonical_post = {}  # param -> (mean, std)

        for variant in PRIOR_VARIANTS:
            prior_alt = _perturb_prior(prior_canonical, variant)
            base_seed_ci = SEED + 3000 + ci * 100 + PRIOR_VARIANTS.index(variant)
            chains, accepts = _run_mcmc_variant(
                x_true, y_obs_noisy, noise, prior_alt,
                model, sx, sy, device, base_seed_ci,
                PRIOR_SENS_N_CHAINS, PRIOR_SENS_N_TOTAL,
                PRIOR_SENS_BURN, PRIOR_SENS_THIN,
            )
            # chains: (n_chains, n_per, n_params)
            pooled = chains.reshape(-1, chains.shape[-1])
            for pi, param in enumerate(INVERSE_CALIB_PARAMS):
                m = float(np.mean(pooled[:, pi]))
                s = float(np.std(pooled[:, pi]))
                p5 = float(np.percentile(pooled[:, pi], 5))
                p95 = float(np.percentile(pooled[:, pi], 95))
                p_true = float(x_true[INPUT_COLS.index(param)])

                if variant == "canonical":
                    canonical_post[param] = (m, s)
                    kl_vs_canonical = 0.0
                    mean_shift_over_std = 0.0
                else:
                    m0, s0 = canonical_post[param]
                    kl_vs_canonical = _gaussian_kl(m0, s0, m, s)
                    mean_shift_over_std = (m - m0) / max(s0, 1e-12)

                rows.append({
                    "case_idx": ci,
                    "row_idx": row_idx,
                    "category": cat,
                    "param": param,
                    "prior_variant": variant,
                    "true_value": p_true,
                    "post_mean": m,
                    "post_std": s,
                    "post_p5": p5,
                    "post_p95": p95,
                    "rel_bias": (m - p_true) / max(abs(p_true), 1e-12),
                    "in_90ci_true": bool(p5 <= p_true <= p95),
                    "mean_accept_rate": float(np.mean(accepts)),
                    "kl_vs_canonical": kl_vs_canonical,
                    "mean_shift_over_canonical_std": mean_shift_over_std,
                })

    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(out_dir, "prior_sensitivity_per_case.csv"), index=False)
    logger.info(f"[{model_id}] per-case 写入 ({len(df)} 行)")

    # Summary: 对每 variant × param 聚合
    agg_rows = []
    for variant in PRIOR_VARIANTS:
        for param in INVERSE_CALIB_PARAMS:
            sub = df[(df["prior_variant"] == variant) & (df["param"] == param)]
            agg_rows.append({
                "model_id": model_id,
                "prior_variant": variant,
                "param": param,
                "n_cases": len(sub),
                "mean_post_mean": float(sub["post_mean"].mean()),
                "mean_post_std": float(sub["post_std"].mean()),
                "coverage_90ci_true": float(sub["in_90ci_true"].mean()),
                "median_abs_rel_bias": float(sub["rel_bias"].abs().median()),
                "max_kl_vs_canonical": float(sub["kl_vs_canonical"].max()),
                "mean_kl_vs_canonical": float(sub["kl_vs_canonical"].mean()),
                "max_abs_mean_shift_sigma": float(
                    sub["mean_shift_over_canonical_std"].abs().max()),
                "mean_accept_rate": float(sub["mean_accept_rate"].mean()),
            })
    sdf = pd.DataFrame(agg_rows)
    sdf.to_csv(os.path.join(out_dir, "prior_sensitivity_summary.csv"), index=False)
    logger.info(f"[{model_id}] summary 写入 ({len(sdf)} 行)")

    # 图
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        alt_variants = [v for v in PRIOR_VARIANTS if v != "canonical"]
        fig, axes = plt.subplots(1, len(INVERSE_CALIB_PARAMS),
                                 figsize=(3.2 * len(INVERSE_CALIB_PARAMS), 3.5),
                                 sharey=True)
        axes = np.atleast_1d(axes)
        for pi, param in enumerate(INVERSE_CALIB_PARAMS):
            ax = axes[pi]
            vals = []
            for v in alt_variants:
                sub = df[(df["prior_variant"] == v) & (df["param"] == param)]
                vals.append(sub["mean_shift_over_canonical_std"].abs().values)
            ax.boxplot(vals, labels=alt_variants)
            ax.axhline(0.5, color="red", ls="--", lw=0.8, label="0.5σ")
            ax.set_title(param, fontsize=9)
            ax.set_ylabel(r"|Δμ| / σ_canonical")
            ax.tick_params(axis="x", labelrotation=25, labelsize=7)
        fig.suptitle(f"Prior sensitivity — {model_id}", fontsize=10)
        fig.tight_layout()
        fig.savefig(os.path.join(out_dir, f"prior_sensitivity_{model_id}.png"),
                    dpi=150)
        plt.close(fig)
    except Exception as e:
        logger.warning(f"[{model_id}] 绘图失败 (non-fatal): {e}")

    summary = {
        "model_id": model_id,
        "n_cases": len(selected),
        "variants": PRIOR_VARIANTS,
        "max_abs_mean_shift_sigma_any_variant": float(
            sdf["max_abs_mean_shift_sigma"].max()),
        "max_kl_any_variant": float(sdf["max_kl_vs_canonical"].max()),
        "mean_accept_rate": float(sdf["mean_accept_rate"].mean()),
    }
    mf = make_experiment_manifest(
        experiment_id="posterior_prior_sensitivity",
        model_id=model_id,
        input_source=f"{FIXED_SPLIT_DIR} (train/test) + {model_id} checkpoint",
        outputs_saved=[os.path.join(out_dir, "prior_sensitivity_per_case.csv"),
                       os.path.join(out_dir, "prior_sensitivity_summary.csv")],
        key_results=summary,
        source_script=os.path.abspath(__file__),
        extra={"mcmc_config": {
            "N_TOTAL": PRIOR_SENS_N_TOTAL,
            "BURN_IN": PRIOR_SENS_BURN,
            "THIN": PRIOR_SENS_THIN,
            "N_CHAINS": PRIOR_SENS_N_CHAINS,
            "PROPOSAL_SCALE": rp.PROPOSAL_SCALE,
            "OBS_NOISE_FRAC": rp.OBS_NOISE_FRAC,
        }},
    )
    write_manifest(os.path.join(out_dir, "prior_sensitivity_manifest.json"), mf)

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
        logger.info(f"PRIOR SENSITIVITY — {mid}")
        logger.info("=" * 60)
        all_summaries[mid] = run_for_model(mid)

    if all_summaries:
        all_out = os.path.join(experiment_dir("posterior"),
                               "prior_sensitivity_all_models.json")
        with open(all_out, "w") as f:
            json.dump(all_summaries, f, indent=2)
        logger.info(f"Cross-model summary -> {all_out}")
    logger.info("PRIOR SENSITIVITY DONE")
