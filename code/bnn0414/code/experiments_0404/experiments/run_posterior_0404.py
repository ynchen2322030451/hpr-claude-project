# run_posterior_0404.py
# ============================================================
# BNN 0414 后验推断脚本（基于 0411 版本改写）
#
# 与 0411 的差异：
#   - 模型：BayesianMLP 替代 HeteroMLP
#   - MCMC 似然中每次前向用 mc_predict() 取 BNN_N_MC_POSTERIOR 次权重
#     采样的均值；不确定度通过 MC 结果的 total_var 估计
#   - feasible region 内的预测采样也走 mc_predict，每后验点抽一次
#
# 功能：
#   1) 围绕 test pool 里的代表性 case 做 Metropolis-Hastings MCMC
#   2) 输出参数恢复统计（parameter recovery）
#   3) 输出安全可行域分析（feasible region: P(stress < τ | posterior) > α）
#
# 调用方式:
#   MODEL_ID=bnn-baseline  POSTERIOR_MODE=benchmark python run_posterior_0404.py
#   MODEL_ID=bnn-data-mono POSTERIOR_MODE=feasible  python run_posterior_0404.py
#   MODEL_ID=bnn-baseline  POSTERIOR_MODE=all       python run_posterior_0404.py
#
# 输出:
#   experiments_0404/experiments/posterior/<model_id>/
#     benchmark_summary.csv       — 参数恢复汇总
#     benchmark_case_meta.json    — 每个 case 的完整信息
#     feasible_region.csv         — 可行域分析结果
#     posterior_manifest.json
# ============================================================

import os, sys, json, math, pickle, logging
from datetime import datetime

import numpy as np
import pandas as pd
import torch

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
        sys.path.insert(0, _p)

from experiment_config_0404 import (
    INPUT_COLS, OUTPUT_COLS, PRIMARY_OUTPUTS,
    PRIMARY_STRESS_OUTPUT, PRIMARY_STRESS_THRESHOLD,
    INVERSE_N_BENCHMARK, INVERSE_N_EXTREME,
    INVERSE_MCMC_SAMPLES, INVERSE_CALIB_PARAMS, INVERSE_FIXED_PARAMS,
    BNN_N_MC_POSTERIOR,
    SEED, DEVICE, FIXED_SPLIT_DIR, EXPR_ROOT_OLD,
    experiment_dir, model_artifacts_dir, ensure_dir,
    DESIGN_NOMINAL, DESIGN_SIGMA,
)
from model_registry_0404 import MODELS
from manifest_utils_0404 import write_manifest, make_experiment_manifest, resolve_output_dir
from bnn_model import BayesianMLP, mc_predict, get_device, seed_all

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
# ★ MCMC 控制配置 ★
# ============================================================
POSTERIOR_CONFIG = {
    "model_id":       "bnn-baseline",
    "mode":           "all",
    "n_total":        8000,
    "burn_in":        2000,
    "thin":           5,
    "proposal_scale": 0.40,
    "obs_noise_frac": 0.02,
    "n_chains":       1,
}

N_TOTAL        = POSTERIOR_CONFIG["n_total"]
BURN_IN        = POSTERIOR_CONFIG["burn_in"]
THIN           = POSTERIOR_CONFIG["thin"]
OBS_NOISE_FRAC = POSTERIOR_CONFIG["obs_noise_frac"]
PROPOSAL_SCALE = POSTERIOR_CONFIG["proposal_scale"]
N_CHAINS       = POSTERIOR_CONFIG["n_chains"]

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
# Artifact / model loading (self-contained for BNN)
# ────────────────────────────────────────────────────────────
def _resolve_artifacts(model_id: str):
    art_dir = model_artifacts_dir(model_id)
    candidates = [
        (os.path.join(art_dir, f"checkpoint_{model_id}.pt"),
         os.path.join(art_dir, f"scalers_{model_id}.pkl")),
        (os.path.join(art_dir, f"checkpoint_{model_id}_fixed.pt"),
         os.path.join(art_dir, f"scalers_{model_id}_fixed.pkl")),
    ]
    for ckpt, sca in candidates:
        if os.path.exists(ckpt) and os.path.exists(sca):
            return ckpt, sca
    raise FileNotFoundError(
        f"[{model_id}] 找不到 BNN checkpoint/scaler，尝试过：{candidates}"
    )


def _load_model(ckpt_path: str, device) -> BayesianMLP:
    ckpt = torch.load(ckpt_path, map_location=device)
    hp = ckpt.get("best_params", ckpt.get("hp", {}))
    model = BayesianMLP(
        in_dim=len(INPUT_COLS), out_dim=len(OUTPUT_COLS),
        width=int(hp["width"]), depth=int(hp["depth"]),
        prior_sigma=float(hp.get("prior_sigma", 1.0)),
    ).to(device)
    model.load_state_dict(ckpt["model_state_dict"])
    model.eval()
    return model


def _load_scalers(scaler_path: str):
    with open(scaler_path, "rb") as f:
        return pickle.load(f)


# ────────────────────────────────────────────────────────────
# BNN 单点预测（替代 0411 的 _predict_single）
# ────────────────────────────────────────────────────────────
def _predict_single_bnn(model, sx, sy, x_full: np.ndarray, device):
    """
    对单个原始输入点 x_full（shape (n_in,)）返回 (mu_raw, sigma_raw)，
    shape (n_out,)，原始量纲。

    使用 BNN_N_MC_POSTERIOR 次 MC 采样估计均值与总标准差
    （total_std = sqrt(epistemic_var + aleatoric_var)）。
    """
    mu_mean, _, aleatoric_var, epistemic_var, total_var = mc_predict(
        model, x_full.reshape(1, -1), sx, sy, device, n_mc=BNN_N_MC_POSTERIOR
    )
    mu_raw = mu_mean.flatten()
    sigma_raw = np.sqrt(total_var).flatten()
    return mu_raw, sigma_raw


# ────────────────────────────────────────────────────────────
# 先验
# ────────────────────────────────────────────────────────────
def _get_prior_stats(train_df: pd.DataFrame) -> dict:
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
    x_full = ref_x_full.copy()
    for i, c in enumerate(INVERSE_CALIB_PARAMS):
        j = INPUT_COLS.index(c)
        x_full[j] = theta_sub[i]
    return x_full


def _log_likelihood(
    theta_sub: np.ndarray, ref_x_full: np.ndarray,
    y_obs: np.ndarray, obs_noise: np.ndarray,
    model, sx, sy, device,
) -> float:
    x_full = _expand_to_full(theta_sub, ref_x_full)
    mu_raw, sigma_raw = _predict_single_bnn(model, sx, sy, x_full, device)

    obs_idx = [OUTPUT_COLS.index(c) for c in OBS_COLS]
    mu_obs  = mu_raw[obs_idx]
    sig_obs = sigma_raw[obs_idx]

    total_noise = np.sqrt(obs_noise**2 + sig_obs**2)
    z   = (y_obs - mu_obs) / (total_noise + 1e-30)
    ll  = float(-0.5 * np.sum(z**2))
    return ll


def _reflect_bounds(theta_sub: np.ndarray, prior_stats: dict) -> np.ndarray:
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
):
    d = len(INVERSE_CALIB_PARAMS)

    theta0 = np.array([prior_stats[c]["mean"] for c in INVERSE_CALIB_PARAMS])
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

    n_sampling_steps = N_TOTAL - BURN_IN
    accept_rate = n_accept_sampling / n_sampling_steps if n_sampling_steps > 0 else 0.0

    posterior = samples[BURN_IN::THIN]
    return posterior, float(accept_rate)


# ────────────────────────────────────────────────────────────
# Gelman-Rubin 收敛诊断
# ────────────────────────────────────────────────────────────
def compute_rhat(chains: list) -> np.ndarray:
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
):
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

    rhat        = compute_rhat(chains)
    posterior   = np.concatenate(chains, axis=0)
    mean_accept = float(np.mean(accept_rates))
    return posterior, mean_accept, rhat, chains


# ────────────────────────────────────────────────────────────
# 参数恢复分析
# ────────────────────────────────────────────────────────────
def run_benchmark(
    model_id: str, model, sx, sy, device,
    train_df: pd.DataFrame, test_df: pd.DataFrame,
    out_dir: str, n_cases: int = None,
):
    if n_cases is None:
        n_cases = INVERSE_N_BENCHMARK

    prior_stats = _get_prior_stats(train_df)

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

    logger.info(f"[benchmark][{model_id}] 共 {len(selected)} 个 case（low/near/high）")

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
    if n_extreme_cases is None:
        n_extreme_cases = INVERSE_N_EXTREME

    prior_stats = _get_prior_stats(train_df)

    s = test_df[PRIMARY_STRESS_OUTPUT].values
    extreme_idx = np.where(s >= TAU)[0]
    rng0 = np.random.RandomState(SEED + 99)
    if len(extreme_idx) >= n_extreme_cases:
        chosen_idx = rng0.choice(extreme_idx, n_extreme_cases, replace=False)
    else:
        chosen_idx = extreme_idx
        logger.warning(f"[feasible] 高应力 case 不足 {n_extreme_cases}，使用全部 {len(extreme_idx)} 个")

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

        # 对后验样本预测应力分布（批处理 BNN MC 预测）
        n_post = len(posterior)
        stress_post = []
        batch_sz = 256
        rng_draw = np.random.default_rng(SEED + int(row_idx))
        for b_start in range(0, n_post, batch_sz):
            batch = posterior[b_start: b_start + batch_sz]
            x_batch = np.array([
                _expand_to_full(th, x_true) for th in batch
            ])
            mu_mean_b, _, ale_var_b, epi_var_b, total_var_b = mc_predict(
                model, x_batch, sx, sy, device, n_mc=BNN_N_MC_POSTERIOR
            )
            sigma_b = np.sqrt(total_var_b)

            eps = rng_draw.standard_normal(mu_mean_b.shape)
            y_draw = mu_mean_b + sigma_b * eps
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
        })

        logger.info(
            f"  [feasible] case {ci+1}: stress_true={stress_true:.1f} MPa, "
            f"P(below {TAU})={p_below:.3f}, feasible={rows[-1]['feasible_alpha90']}"
        )

    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(out_dir, "feasible_region.csv"), index=False)

    frac_feasible = float(df["feasible_alpha90"].mean())
    logger.info(f"[feasible][{model_id}] {frac_feasible:.1%} 的高应力 case 后验可行（P(safe)>{alpha_safe}）")

    return df


# ────────────────────────────────────────────────────────────
# 入口
# ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    model_id  = os.environ.get("MODEL_ID",       POSTERIOR_CONFIG["model_id"])
    post_mode = os.environ.get("POSTERIOR_MODE", POSTERIOR_CONFIG["mode"])
    force     = False

    if model_id not in MODELS:
        raise ValueError(f"未知 MODEL_ID: {model_id}。可选: {list(MODELS.keys())}")

    out_dir = resolve_output_dir(
        os.path.join(experiment_dir("posterior"), model_id),
        script_name=os.path.basename(__file__),
    )

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    fh = logging.FileHandler(os.path.join(out_dir, f"posterior_{ts}.log"))
    fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(fh)

    logger.info(f"posterior_0404 (BNN) | model={model_id} | mode={post_mode}")

    device = get_device(DEVICE)
    seed_all(SEED)
    ckpt_path, scaler_path = _resolve_artifacts(model_id)
    model   = _load_model(ckpt_path, device)
    scalers = _load_scalers(scaler_path)
    sx, sy  = scalers["sx"], scalers["sy"]
    model.eval()

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
            "N_total_mcmc":  N_TOTAL,
            "burn_in":       BURN_IN,
            "thin":          THIN,
            "obs_noise_frac": OBS_NOISE_FRAC,
            "calib_params":  INVERSE_CALIB_PARAMS,
            "obs_cols":      OBS_COLS,
            "n_mc_posterior": BNN_N_MC_POSTERIOR,
            "model_class":   "BayesianMLP",
        },
    )
    write_manifest(os.path.join(out_dir, "posterior_manifest.json"), mf)
    logger.info(f"[{model_id}] posterior 完成")
