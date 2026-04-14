# run_posterior_0404.py
# ============================================================
# BNN 0414 后验推断脚本
#
# BNN adaptation of code/0411/.../run_posterior_0404.py.
#
# 关键 BNN 改动：
#   - MCMC 似然评估使用 MC-averaged predictions
#   - 每次 log_likelihood 调用进行 BNN_N_MC_POSTERIOR (20) 次随机前向
#   - _predict_single_bnn 替代 _predict_single（MC 平均版）
#   - 可行域分析中的后验预测也使用 MC 采样
#   - 其余逻辑（MH 采样器、benchmark case 选取、feasible region）不变
#
# 功能：
#   1) 围绕 test pool 里的代表性 case 做 Metropolis-Hastings MCMC
#   2) 输出参数恢复统计（parameter recovery）
#   3) 输出安全可行域分析（feasible region: P(stress < tau | posterior) > alpha）
#
# 调用方式:
#   MODEL_ID=bnn-baseline  POSTERIOR_MODE=benchmark python run_posterior_0404.py
#   MODEL_ID=bnn-data-mono POSTERIOR_MODE=feasible  python run_posterior_0404.py
#   MODEL_ID=bnn-baseline  POSTERIOR_MODE=all       python run_posterior_0404.py
#
# 输出:
#   bnn0414/code/experiments_0404/experiments/posterior/<model_id>/
#     benchmark_summary.csv       — 参数恢复汇总
#     benchmark_case_meta.json    — 每个 case 的完整信息
#     feasible_region.csv         — 可行域分析结果
#     posterior_manifest.json
#
# 说明：
#   - MCMC 基于 test split（不使用 calibration pool 或 emulator pool 的旧分割）
#   - 观测来自测试样本的真实输出，加上人工噪声（模拟现实观测）
#   - 先验分布由数据集统计推导（与旧脚本一致）
# ============================================================

import os, sys, json, math, logging
from datetime import datetime

import numpy as np
import pandas as pd
import torch

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_CODE_DIR = os.path.dirname(_SCRIPT_DIR)
for _p in [
    os.path.join(_CODE_DIR, 'config'),
    os.path.dirname(_CODE_DIR),  # experiments_0404/
    os.path.dirname(os.path.dirname(_CODE_DIR)),  # bnn0414/code/
    os.path.dirname(os.path.dirname(os.path.dirname(_CODE_DIR))),  # code/0310/
    os.path.join(_CODE_DIR, 'evaluation'),
    os.environ.get('HPR_LEGACY_DIR', ''),
]:
    if _p and os.path.isdir(_p) and _p not in sys.path:
        sys.path.insert(0, _p)

from experiment_config_0404 import (
    INPUT_COLS, OUTPUT_COLS, PRIMARY_OUTPUTS,
    PRIMARY_STRESS_OUTPUT, PRIMARY_STRESS_THRESHOLD,
    INVERSE_N_BENCHMARK, INVERSE_N_EXTREME,
    INVERSE_MCMC_SAMPLES, INVERSE_CALIB_PARAMS, INVERSE_FIXED_PARAMS,
    BNN_N_MC_POSTERIOR, BNN_N_MC_EVAL,
    SEED, DEVICE, FIXED_SPLIT_DIR, EXPR_ROOT_OLD,
    experiment_dir, model_artifacts_dir, ensure_dir,
    DESIGN_NOMINAL, DESIGN_SIGMA,
)
from model_registry_0404 import MODELS
from manifest_utils_0404 import write_manifest, make_experiment_manifest
from run_eval_0404 import _resolve_artifacts, _load_model, _load_scalers, _predict
from bnn_model import get_device, mc_predict

# ────────────────────────────────────────────────────────────
# 日志
# ────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ============================================================
# MCMC configuration
# ============================================================
POSTERIOR_CONFIG = {
    "model_id":   "bnn-baseline",
    "mode":       "all",

    "n_total":        8000,
    "burn_in":        2000,
    "thin":           5,
    "proposal_scale": 0.40,

    "obs_noise_frac": 0.02,

    "n_chains":  1,
}

N_TOTAL        = POSTERIOR_CONFIG["n_total"]
BURN_IN        = POSTERIOR_CONFIG["burn_in"]
THIN           = POSTERIOR_CONFIG["thin"]
OBS_NOISE_FRAC = POSTERIOR_CONFIG["obs_noise_frac"]
PROPOSAL_SCALE = POSTERIOR_CONFIG["proposal_scale"]
N_CHAINS       = POSTERIOR_CONFIG["n_chains"]

# 观测输出集（用于似然）
OBS_COLS = [
    "iteration2_max_global_stress",
    "iteration2_max_fuel_temp",
    "iteration2_max_monolith_temp",
    "iteration2_wall2",
    "iteration2_keff",
]

STRESS_IDX_IN_OBS = OBS_COLS.index("iteration2_max_global_stress")
TAU = PRIMARY_STRESS_THRESHOLD


# ────────────────────────────────────────────────────────────
# BNN MC-averaged single-point prediction
# ────────────────────────────────────────────────────────────
@torch.no_grad()
def _predict_single_bnn(model, sx, sy, x_raw: np.ndarray, device,
                        n_mc: int = None):
    """
    BNN MC-averaged prediction for a single input point.
    返回 (mu_raw, sigma_raw)，shape (n_out,)。

    mu_raw = mean of MC-sampled means (original scale)
    sigma_raw = sqrt(epistemic_var + aleatoric_var) (original scale)
    """
    if n_mc is None:
        n_mc = BNN_N_MC_POSTERIOR

    x_s = sx.transform(x_raw.reshape(1, -1))
    x_t = torch.tensor(x_s, dtype=torch.float32, device=device)

    # MC forward passes
    mus_scaled, logvars_scaled = model.predict_mc(x_t, n_mc=n_mc)
    # mus_scaled: (n_mc, 1, n_out), logvars_scaled: (n_mc, 1, n_out)

    mus_np = mus_scaled.cpu().numpy()[:, 0, :]        # (n_mc, n_out)
    logvars_np = logvars_scaled.cpu().numpy()[:, 0, :]  # (n_mc, n_out)

    sy_mean = sy.mean_
    sy_scale = sy.scale_

    # Convert to original scale
    mus_orig = mus_np * sy_scale + sy_mean  # (n_mc, n_out)
    vars_scaled = np.exp(logvars_np)
    vars_orig = vars_scaled * (sy_scale ** 2)  # (n_mc, n_out)

    # Decompose
    mu_mean = np.mean(mus_orig, axis=0)            # (n_out,)
    epistemic_var = np.var(mus_orig, axis=0)        # (n_out,)
    aleatoric_var = np.mean(vars_orig, axis=0)      # (n_out,)
    total_var = epistemic_var + aleatoric_var
    sigma_raw = np.sqrt(total_var)                  # (n_out,)

    return mu_mean, sigma_raw


# ────────────────────────────────────────────────────────────
# 工具函数
# ────────────────────────────────────────────────────────────
def _get_prior_stats(train_df: pd.DataFrame) -> dict:
    """从训练集统计得到先验分布参数（截断高斯）。"""
    stats = {}
    for c in INVERSE_CALIB_PARAMS:
        col = train_df[c].values.astype(float)
        stats[c] = {
            "mean": float(np.mean(col)),
            "std":  float(np.std(col) + 1e-12),
            "min":  float(np.min(col)),
            "max":  float(np.max(col)),
        }
    return stats


def _log_prior(theta_sub: np.ndarray, prior_stats: dict) -> float:
    """截断高斯先验的对数概率。"""
    lp = 0.0
    for i, c in enumerate(INVERSE_CALIB_PARAMS):
        xi = theta_sub[i]
        lo = prior_stats[c]["min"]
        hi = prior_stats[c]["max"]
        if xi < lo or xi > hi:
            return -np.inf
        mu = prior_stats[c]["mean"]
        sd = prior_stats[c]["std"]
        z  = (xi - mu) / sd
        lp += -0.5 * z * z - math.log(sd)
    return float(lp)


def _expand_to_full(theta_sub: np.ndarray, ref_x_full: np.ndarray) -> np.ndarray:
    """
    将标定参数子集扩展回全维输入向量。
    固定参数使用 ref_x_full 中的值（即测试 case 的原始输入值）。
    """
    x_full = ref_x_full.copy()
    for i, c in enumerate(INVERSE_CALIB_PARAMS):
        j = INPUT_COLS.index(c)
        x_full[j] = theta_sub[i]
    return x_full


def _log_likelihood(
    theta_sub: np.ndarray, ref_x_full: np.ndarray,
    y_obs: np.ndarray, obs_noise: np.ndarray,
    model, sx, sy, device,
    n_mc: int = None,
) -> float:
    """
    BNN MC-averaged Gaussian likelihood.

    ll = sum_j [ -0.5 * ((y_obs[j] - mu_pred[j])/(noise_j + sigma_pred[j]))^2 ]

    Uses BNN MC-averaged predictions (n_mc forward passes per evaluation).
    """
    if n_mc is None:
        n_mc = BNN_N_MC_POSTERIOR

    x_full = _expand_to_full(theta_sub, ref_x_full)
    mu_raw, sigma_raw = _predict_single_bnn(model, sx, sy, x_full, device, n_mc=n_mc)

    # 只使用 OBS_COLS 对应的输出
    obs_idx = [OUTPUT_COLS.index(c) for c in OBS_COLS]
    mu_obs  = mu_raw[obs_idx]
    sig_obs = sigma_raw[obs_idx]

    total_noise = np.sqrt(obs_noise**2 + sig_obs**2)
    z   = (y_obs - mu_obs) / (total_noise + 1e-30)
    ll  = float(-0.5 * np.sum(z**2))
    return ll


def _reflect_bounds(theta_sub: np.ndarray, prior_stats: dict) -> np.ndarray:
    """反弹回边界内。"""
    y = theta_sub.copy()
    for i, c in enumerate(INVERSE_CALIB_PARAMS):
        lo, hi = prior_stats[c]["min"], prior_stats[c]["max"]
        if y[i] < lo:
            y[i] = lo + (lo - y[i])
        if y[i] > hi:
            y[i] = hi - (y[i] - hi)
        y[i] = min(max(y[i], lo), hi)
    return y


# ────────────────────────────────────────────────────────────
# Metropolis-Hastings MCMC
# ────────────────────────────────────────────────────────────
def run_mcmc(
    ref_x_full: np.ndarray,
    y_obs: np.ndarray,
    obs_noise: np.ndarray,
    prior_stats: dict,
    model, sx, sy, device,
    rng: np.random.RandomState,
) -> np.ndarray:
    """
    返回 thin 后的后验样本，shape (INVERSE_MCMC_SAMPLES, n_calib)。
    """
    d = len(INVERSE_CALIB_PARAMS)

    # 初始化：从先验均值开始
    theta0 = np.array([prior_stats[c]["mean"] for c in INVERSE_CALIB_PARAMS])

    # 提议分布的尺度：先验 std * PROPOSAL_SCALE
    prop_scales = np.array([prior_stats[c]["std"] for c in INVERSE_CALIB_PARAMS]) * PROPOSAL_SCALE

    samples = np.zeros((N_TOTAL, d), float)
    theta_curr = theta0.copy()
    lp_curr   = _log_prior(theta_curr, prior_stats)
    ll_curr   = _log_likelihood(theta_curr, ref_x_full, y_obs, obs_noise, model, sx, sy, device)
    lpost_curr = lp_curr + ll_curr

    n_accept_burnin   = 0
    n_accept_sampling = 0
    for t in range(N_TOTAL):
        theta_prop = theta_curr + rng.normal(0, prop_scales)
        theta_prop = _reflect_bounds(theta_prop, prior_stats)

        lp_prop = _log_prior(theta_prop, prior_stats)
        if not np.isfinite(lp_prop):
            samples[t] = theta_curr
            continue

        ll_prop   = _log_likelihood(theta_prop, ref_x_full, y_obs, obs_noise, model, sx, sy, device)
        lpost_prop = lp_prop + ll_prop

        log_alpha = lpost_prop - lpost_curr
        if np.log(rng.uniform()) < log_alpha:
            theta_curr  = theta_prop
            lpost_curr  = lpost_prop
            if t < BURN_IN:
                n_accept_burnin += 1
            else:
                n_accept_sampling += 1

        samples[t] = theta_curr

    # 仅统计采样期接受率（burn-in 后）
    n_sampling_steps = N_TOTAL - BURN_IN
    accept_rate = n_accept_sampling / n_sampling_steps if n_sampling_steps > 0 else 0.0

    # 烧入 + 稀疏化
    posterior = samples[BURN_IN::THIN]

    return posterior, float(accept_rate)


# ────────────────────────────────────────────────────────────
# Gelman-Rubin 收敛诊断
# ────────────────────────────────────────────────────────────
def compute_rhat(chains: list) -> np.ndarray:
    """
    计算 Gelman-Rubin Rhat 统计量（单变量版本）。
    Rhat < 1.1 表示收敛；< 1.05 为严格标准。
    """
    m = len(chains)
    n = chains[0].shape[0]

    chain_means = np.array([c.mean(axis=0) for c in chains])
    grand_mean  = chain_means.mean(axis=0)

    B = n / (m - 1) * np.sum((chain_means - grand_mean) ** 2, axis=0)

    chain_vars = np.array([c.var(axis=0, ddof=1) for c in chains])
    W = chain_vars.mean(axis=0)

    var_hat = (1.0 - 1.0 / n) * W + B / n

    rhat = np.sqrt(var_hat / (W + 1e-30))
    return rhat


def run_mcmc_multi_chain(
    ref_x_full: np.ndarray,
    y_obs: np.ndarray,
    obs_noise: np.ndarray,
    prior_stats: dict,
    model, sx, sy, device,
    base_seed: int,
    n_chains: int = 4,
) -> tuple:
    """
    运行 n_chains 条独立 MCMC 链，返回合并后验样本和收敛诊断。
    """
    n_params = len(INVERSE_CALIB_PARAMS)
    prop_scales = np.array([prior_stats[c]["std"] for c in INVERSE_CALIB_PARAMS]) * PROPOSAL_SCALE

    chains = []
    accept_rates = []
    for k in range(n_chains):
        rng_k = np.random.RandomState(base_seed + k * 7919)
        theta0_k = np.array([
            rng_k.uniform(prior_stats[c]["mean"] - prior_stats[c]["std"],
                           prior_stats[c]["mean"] + prior_stats[c]["std"])
            for c in INVERSE_CALIB_PARAMS
        ])

        samples = np.zeros((N_TOTAL, n_params), float)
        theta_curr = theta0_k.copy()
        lp_curr    = _log_prior(theta_curr, prior_stats)
        ll_curr    = _log_likelihood(theta_curr, ref_x_full, y_obs, obs_noise, model, sx, sy, device)
        lpost_curr = lp_curr + ll_curr
        n_accept_sampling = 0

        for t in range(N_TOTAL):
            theta_prop = theta_curr + rng_k.normal(0, prop_scales)
            theta_prop = _reflect_bounds(theta_prop, prior_stats)
            lp_prop    = _log_prior(theta_prop, prior_stats)
            if not np.isfinite(lp_prop):
                samples[t] = theta_curr
                continue
            ll_prop    = _log_likelihood(theta_prop, ref_x_full, y_obs, obs_noise, model, sx, sy, device)
            lpost_prop = lp_prop + ll_prop
            if np.log(rng_k.uniform()) < lpost_prop - lpost_curr:
                theta_curr  = theta_prop
                lpost_curr  = lpost_prop
                if t >= BURN_IN:
                    n_accept_sampling += 1
            samples[t] = theta_curr

        n_sampling = N_TOTAL - BURN_IN
        accept_rates.append(n_accept_sampling / n_sampling if n_sampling > 0 else 0.0)
        chains.append(samples[BURN_IN::THIN])

    rhat         = compute_rhat(chains)
    posterior    = np.concatenate(chains, axis=0)
    mean_accept  = float(np.mean(accept_rates))
    return posterior, mean_accept, rhat, chains


# ────────────────────────────────────────────────────────────
# 参数恢复分析
# ────────────────────────────────────────────────────────────
def run_benchmark(
    model_id: str, model, sx, sy, device,
    train_df: pd.DataFrame, test_df: pd.DataFrame,
    out_dir: str, n_cases: int = None,
):
    """
    合成逆问题：以测试集 case 的真实输入为 ground truth，
    从其真实输出（加噪声）出发做后验推断，检验参数恢复能力。
    """
    if n_cases is None:
        n_cases = INVERSE_N_BENCHMARK

    prior_stats = _get_prior_stats(train_df)

    # 按应力分层选取代表性 case
    tau = TAU
    s = test_df[PRIMARY_STRESS_OUTPUT].values
    low_idx  = np.where(s < 0.92 * tau)[0]
    near_idx = np.where((s >= 0.92*tau) & (s < tau))[0]
    high_idx = np.where(s >= tau)[0]

    rng0 = np.random.RandomState(SEED + 42)
    selected = []
    for cat_idx, label in [(low_idx, "low"), (near_idx, "near"), (high_idx, "high")]:
        n_cat = max(1, n_cases // 3)
        if len(cat_idx) >= n_cat:
            chosen = rng0.choice(cat_idx, n_cat, replace=False)
        else:
            chosen = cat_idx
        selected.extend([(int(i), label) for i in chosen])

    logger.info(f"[benchmark][{model_id}] {len(selected)} cases (low/near/high)")

    obs_idx = [OUTPUT_COLS.index(c) for c in OBS_COLS]

    recovery_rows = []
    case_meta     = []

    for ci, (row_idx, cat) in enumerate(selected):
        case_row  = test_df.iloc[row_idx]
        x_true    = case_row[INPUT_COLS].values.astype(float)
        y_true_all= case_row[OUTPUT_COLS].values.astype(float)
        y_obs_full= y_true_all[obs_idx]
        noise     = np.abs(y_obs_full) * OBS_NOISE_FRAC + 1e-10

        y_obs_noisy = y_obs_full + np.random.RandomState(SEED + ci).normal(0, noise)

        base_seed_ci = SEED + 1000 + ci
        if N_CHAINS > 1:
            posterior, accept_rate, rhat, _ = run_mcmc_multi_chain(
                ref_x_full  = x_true,
                y_obs       = y_obs_noisy,
                obs_noise   = noise,
                prior_stats = prior_stats,
                model=model, sx=sx, sy=sy, device=device,
                base_seed   = base_seed_ci,
                n_chains    = N_CHAINS,
            )
            rhat_dict = {p: float(rhat[pi]) for pi, p in enumerate(INVERSE_CALIB_PARAMS)}
            logger.info(
                f"  case {ci+1}: Rhat = "
                + ", ".join(f"{p}={rhat_dict[p]:.4f}" for p in INVERSE_CALIB_PARAMS)
                + (" OK" if all(v < 1.1 for v in rhat_dict.values()) else " NOT CONVERGED")
            )
        else:
            rng_mcmc = np.random.RandomState(base_seed_ci)
            posterior, accept_rate = run_mcmc(
                ref_x_full = x_true,
                y_obs      = y_obs_noisy,
                obs_noise  = noise,
                prior_stats= prior_stats,
                model=model, sx=sx, sy=sy, device=device,
                rng=rng_mcmc,
            )
            rhat_dict = {p: float("nan") for p in INVERSE_CALIB_PARAMS}

        n_post = len(posterior)
        stress_true = float(case_row[PRIMARY_STRESS_OUTPUT]) if PRIMARY_STRESS_OUTPUT in case_row.index else np.nan

        for pi, param in enumerate(INVERSE_CALIB_PARAMS):
            p_true = float(x_true[INPUT_COLS.index(param)])
            post_mean = float(np.mean(posterior[:, pi]))
            post_std  = float(np.std(posterior[:, pi]))
            post_lo   = float(np.percentile(posterior[:, pi], 5))
            post_hi   = float(np.percentile(posterior[:, pi], 95))
            in_ci     = bool(post_lo <= p_true <= post_hi)

            recovery_rows.append({
                "case_idx":   ci,
                "row_idx":    row_idx,
                "category":   cat,
                "param":      param,
                "true_value": p_true,
                "post_mean":  post_mean,
                "post_std":   post_std,
                "post_lo_5":  post_lo,
                "post_hi_95": post_hi,
                "in_90ci":    in_ci,
                "bias":       post_mean - p_true,
                "rel_bias":   (post_mean - p_true) / (abs(p_true) + 1e-30),
                "accept_rate":accept_rate,
                "n_posterior":n_post,
                "stress_true_MPa": stress_true,
                "rhat":       rhat_dict[param],
                "n_mc_posterior": BNN_N_MC_POSTERIOR,
            })

        case_meta.append({
            "case_idx": ci, "row_idx": row_idx, "category": cat,
            "stress_true": stress_true, "accept_rate": accept_rate,
            "n_posterior": n_post,
        })

        if ci % 5 == 0:
            logger.info(f"  case {ci+1}/{len(selected)}, accept={accept_rate:.3f}")

    df_rec = pd.DataFrame(recovery_rows)
    df_rec.to_csv(os.path.join(out_dir, "benchmark_summary.csv"), index=False)

    with open(os.path.join(out_dir, "benchmark_case_meta.json"), "w") as f:
        json.dump(case_meta, f, indent=2)

    # 聚合覆盖率
    coverage = df_rec.groupby("param")["in_90ci"].mean()
    logger.info(f"[benchmark][{model_id}] 90% CI coverage:\n{coverage.to_string()}")

    return df_rec, case_meta


# ────────────────────────────────────────────────────────────
# 安全可行域分析
# ────────────────────────────────────────────────────────────
def run_feasible_region(
    model_id: str, model, sx, sy, device,
    train_df: pd.DataFrame, test_df: pd.DataFrame,
    out_dir: str,
    n_extreme_cases: int = None,
    alpha_safe: float = 0.90,
):
    """
    对高应力 case（ground truth stress > tau）做后验推断。
    问题：给定观测输出 y_obs，后验样本中有多大比例满足 P(stress < tau) > alpha？
    可行域定义：{theta : P(stress(theta) < tau | theta) > alpha}

    BNN 版本：后验预测使用 MC 采样（mc_predict）。
    """
    if n_extreme_cases is None:
        n_extreme_cases = INVERSE_N_EXTREME

    prior_stats = _get_prior_stats(train_df)

    # 选高应力 case
    s = test_df[PRIMARY_STRESS_OUTPUT].values
    extreme_idx = np.where(s >= TAU)[0]
    rng0 = np.random.RandomState(SEED + 99)
    if len(extreme_idx) >= n_extreme_cases:
        chosen_idx = rng0.choice(extreme_idx, n_extreme_cases, replace=False)
    else:
        chosen_idx = extreme_idx
        logger.warning(f"[feasible] high-stress cases < {n_extreme_cases}, using all {len(extreme_idx)}")

    obs_idx = [OUTPUT_COLS.index(c) for c in OBS_COLS]
    stress_out_idx = OUTPUT_COLS.index(PRIMARY_STRESS_OUTPUT)

    rows = []

    for ci, row_idx in enumerate(chosen_idx):
        case_row  = test_df.iloc[row_idx]
        x_true    = case_row[INPUT_COLS].values.astype(float)
        y_true_all= case_row[OUTPUT_COLS].values.astype(float)
        y_obs_full= y_true_all[obs_idx]
        noise     = np.abs(y_obs_full) * OBS_NOISE_FRAC + 1e-10
        y_obs_noisy = y_obs_full + np.random.RandomState(SEED + 200 + ci).normal(0, noise)

        base_seed_feas = SEED + 3000 + ci
        if N_CHAINS > 1:
            posterior, accept_rate, _, _ = run_mcmc_multi_chain(
                ref_x_full  = x_true,
                y_obs       = y_obs_noisy,
                obs_noise   = noise,
                prior_stats = prior_stats,
                model=model, sx=sx, sy=sy, device=device,
                base_seed   = base_seed_feas,
                n_chains    = N_CHAINS,
            )
        else:
            rng_mcmc = np.random.RandomState(base_seed_feas)
            posterior, accept_rate = run_mcmc(
                ref_x_full = x_true,
                y_obs      = y_obs_noisy,
                obs_noise  = noise,
                prior_stats= prior_stats,
                model=model, sx=sx, sy=sy, device=device,
                rng=rng_mcmc,
            )

        # 对后验样本预测应力分布（BNN MC-averaged）
        n_post = len(posterior)
        stress_post = []
        batch_sz = 256
        for b_start in range(0, n_post, batch_sz):
            batch = posterior[b_start: b_start + batch_sz]
            x_batch = np.array([
                _expand_to_full(th, x_true) for th in batch
            ])

            # BNN MC prediction for this batch
            mu_mean, _, aleatoric_var, _, total_var = mc_predict(
                model, x_batch, sx, sy, device, n_mc=BNN_N_MC_EVAL
            )
            sigma_total = np.sqrt(total_var)

            # 对每个后验点：从预测分布抽一个样
            rng_draw = np.random.default_rng(SEED + b_start)
            eps = rng_draw.standard_normal(mu_mean.shape)
            y_draw = mu_mean + sigma_total * eps
            stress_post.extend(y_draw[:, stress_out_idx].tolist())

        stress_post = np.array(stress_post)
        p_below = float(np.mean(stress_post < TAU))
        p_above = float(np.mean(stress_post >= TAU))

        stress_true = float(y_true_all[stress_out_idx])

        rows.append({
            "case_idx":          ci,
            "row_idx":           int(row_idx),
            "stress_true_MPa":   stress_true,
            "P_below_tau_posterior": p_below,
            "P_above_tau_posterior": p_above,
            "feasible_alpha90":  bool(p_below >= alpha_safe),
            "tau_MPa":           TAU,
            "alpha_safe":        alpha_safe,
            "accept_rate":       accept_rate,
            "n_posterior":       n_post,
            "stress_post_mean":  float(np.mean(stress_post)),
            "stress_post_p5":    float(np.percentile(stress_post, 5)),
            "stress_post_p95":   float(np.percentile(stress_post, 95)),
            "n_mc_eval":         BNN_N_MC_EVAL,
        })

        logger.info(
            f"  [feasible] case {ci+1}: stress_true={stress_true:.1f} MPa, "
            f"P(below {TAU})={p_below:.3f}, feasible={rows[-1]['feasible_alpha90']}"
        )

    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(out_dir, "feasible_region.csv"), index=False)

    frac_feasible = float(df["feasible_alpha90"].mean())
    logger.info(f"[feasible][{model_id}] {frac_feasible:.1%} of high-stress cases posterior-feasible (P(safe)>{alpha_safe})")

    return df


# ────────────────────────────────────────────────────────────
# 入口
# ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    model_id  = os.environ.get("MODEL_ID",       POSTERIOR_CONFIG["model_id"])
    post_mode = os.environ.get("POSTERIOR_MODE", POSTERIOR_CONFIG["mode"])
    force     = False

    if model_id not in MODELS:
        raise ValueError(f"Unknown MODEL_ID: {model_id}. Available: {list(MODELS.keys())}")

    out_dir = ensure_dir(
        os.path.join(experiment_dir("posterior"), model_id)
    )

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    fh = logging.FileHandler(os.path.join(out_dir, f"posterior_{ts}.log"))
    fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(fh)

    logger.info(f"posterior_0404 (BNN) | model={model_id} | mode={post_mode} | n_mc_posterior={BNN_N_MC_POSTERIOR}")

    # 加载模型
    device = get_device()
    ckpt_path, scaler_path = _resolve_artifacts(model_id)
    model   = _load_model(ckpt_path, device)
    scalers = _load_scalers(scaler_path)
    sx, sy  = scalers["sx"], scalers["sy"]
    model.eval()

    # 加载数据
    train_df = pd.read_csv(os.path.join(FIXED_SPLIT_DIR, "train.csv"))
    test_df  = pd.read_csv(os.path.join(FIXED_SPLIT_DIR, "test.csv"))

    results = {}

    if post_mode in ("benchmark", "all"):
        df_rec, case_meta = run_benchmark(
            model_id, model, sx, sy, device, train_df, test_df, out_dir
        )
        results["benchmark"] = {
            "n_cases": len(case_meta),
            "coverage_90ci_mean": float(df_rec["in_90ci"].mean()),
        }

    if post_mode in ("feasible", "all"):
        df_feas = run_feasible_region(
            model_id, model, sx, sy, device, train_df, test_df, out_dir
        )
        results["feasible"] = {
            "n_extreme_cases": len(df_feas),
            "frac_feasible_alpha90": float(df_feas["feasible_alpha90"].mean()),
        }

    # manifest
    outputs_saved = [
        os.path.join(out_dir, f)
        for f in ["benchmark_summary.csv", "feasible_region.csv"]
        if os.path.exists(os.path.join(out_dir, f))
    ]
    mf = make_experiment_manifest(
        experiment_id = f"posterior_{post_mode}",
        model_id      = model_id,
        input_source  = FIXED_SPLIT_DIR,
        outputs_saved = outputs_saved,
        key_results   = results,
        source_script = __file__,
        extra = {
            "model_type":     "BNN",
            "N_total_mcmc":   N_TOTAL,
            "burn_in":        BURN_IN,
            "thin":           THIN,
            "obs_noise_frac": OBS_NOISE_FRAC,
            "calib_params":   INVERSE_CALIB_PARAMS,
            "obs_cols":       OBS_COLS,
            "n_mc_posterior":  BNN_N_MC_POSTERIOR,
            "n_mc_eval":      BNN_N_MC_EVAL,
        },
    )
    write_manifest(os.path.join(out_dir, "posterior_manifest.json"), mf)
    logger.info(f"[{model_id}] posterior done")
