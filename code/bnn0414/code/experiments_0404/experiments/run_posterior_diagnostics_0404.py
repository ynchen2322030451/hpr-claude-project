# run_posterior_diagnostics_0404.py
# ============================================================
# BNN 0414 — 后验 MCMC 诊断脚本（NCS revision P0-#3）
#
# 目的：
#   canonical run_posterior_0404.py 跑的是单链 MCMC，
#   benchmark_summary.csv 的 rhat 列因此为空。
#   本脚本独立跑 N_CHAINS ≥ 2 的多链 benchmark，
#   产出：
#     - rhat（Gelman-Rubin，每 case 每 param）
#     - split-rhat（rank-normalized, Vehtari 2021）
#     - ESS（Geyer initial positive sequence）
#     - per-chain acceptance rate
#     - 完整 chain .npz（供 PPC / prior sensitivity 复用）
#
# 不碰 canonical benchmark_summary.csv；写到 <model>/diagnostics/。
#
# 调用：
#   MODEL_ID=bnn-phy-mono DIAG_N_CHAINS=4 python run_posterior_diagnostics_0404.py
#   MODEL_ID=all DIAG_N_CHAINS=4 python run_posterior_diagnostics_0404.py   # 循环 4 个模型
#
# 输出:
#   experiments_0404/experiments/posterior/<model_id>/diagnostics/
#     mcmc_diagnostics.csv       — rhat / split_rhat / ESS / per-chain accept
#     chains/<case_idx>.npz      — 完整 chains (N_CHAINS, N_TOTAL-BURN//THIN, 4 params)
#     diagnostics_manifest.json
# ============================================================

import os, sys, json, logging
from datetime import datetime

import numpy as np
import pandas as pd

# ── sys.path: bnn0414 优先 ───────────────────────────────────
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
        _is_legacy = any(seg in _p for seg in ('/0310', 'hpr_legacy'))
        if _is_legacy:
            sys.path.append(_p)
        else:
            sys.path.insert(0, _p)

from experiment_config_0404 import (
    INPUT_COLS, OUTPUT_COLS, PRIMARY_STRESS_OUTPUT,
    INVERSE_CALIB_PARAMS, INVERSE_N_BENCHMARK,
    SEED, DEVICE, FIXED_SPLIT_DIR,
    experiment_dir, ensure_dir,
)
from model_registry_0404 import MODELS
from manifest_utils_0404 import make_experiment_manifest, write_manifest, resolve_output_dir

# 复用 canonical 的 MCMC 基础设施
import run_posterior_0404 as rp
from bnn_model import get_device, seed_all

# ────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger(__name__)

# ============================================================
# 诊断配置（可 env 覆盖）
# ============================================================
DIAG_N_CHAINS = int(os.environ.get("DIAG_N_CHAINS", 4))
# 不改 N_TOTAL / BURN_IN / THIN，直接复用 rp 的模块级变量（与 canonical 一致）


# ────────────────────────────────────────────────────────────
# ESS — Geyer initial positive sequence (IPS)
# 参考 Geyer (1992) / Vehtari et al. (2021)
# ────────────────────────────────────────────────────────────
def _autocorr(x: np.ndarray) -> np.ndarray:
    """单链 1D autocorrelation，FFT 实现。"""
    n = len(x)
    x = x - np.mean(x)
    f = np.fft.fft(x, n=2 * n)
    acf = np.real(np.fft.ifft(f * np.conj(f)))[:n]
    if acf[0] == 0:
        return np.zeros(n)
    return acf / acf[0]


def ess_single_chain(chain: np.ndarray) -> float:
    """Geyer IPS ESS for one chain, one param. chain: 1D array."""
    n = len(chain)
    if n < 4:
        return float(n)
    rho = _autocorr(chain)
    # pair sums ρ_{2k} + ρ_{2k+1}，取第一个非正之前的和
    pair_sum = rho[0::2][: n // 2] + rho[1::2][: n // 2]
    # 截断：第一个 pair_sum <= 0 的位置
    neg = np.where(pair_sum <= 0)[0]
    if len(neg) == 0:
        k_stop = len(pair_sum)
    else:
        k_stop = int(neg[0])
    if k_stop == 0:
        # 全部负，说明 chain 高度反相关（不常见）
        return float(n)
    tau = -1.0 + 2.0 * np.sum(pair_sum[:k_stop])
    if tau < 1.0:
        tau = 1.0
    return float(n / tau)


def ess_multi_chain(chains: list, param_idx: int) -> float:
    """多链 ESS：各链独立算 ESS 再加总。与 Stan 的保守近似一致。"""
    per_chain = [ess_single_chain(c[:, param_idx]) for c in chains]
    return float(np.sum(per_chain))


# ────────────────────────────────────────────────────────────
# split-rhat with rank normalization (Vehtari 2021)
# ────────────────────────────────────────────────────────────
def _rank_normalize(x: np.ndarray) -> np.ndarray:
    """将 (m*n,) 向量做 rank → normal CDF inverse。"""
    from scipy.stats import norm, rankdata
    r = rankdata(x)
    p = (r - 3.0 / 8.0) / (len(x) + 0.25)
    return norm.ppf(p)


def split_rhat(chains: list, param_idx: int) -> float:
    """
    Split-rhat：每条链对半切，当作 2m 条链算 Gelman-Rubin；
    再用 rank-normalized 值算一次，取较大者（Vehtari 2021）。
    """
    try:
        from scipy.stats import norm, rankdata  # noqa
    except ImportError:
        # 没 scipy 时退化到朴素 split rhat
        return _split_rhat_naive(chains, param_idx)

    flat = np.concatenate([c[:, param_idx] for c in chains])
    n_per = chains[0].shape[0]

    def _gr(chains_1d):
        m = len(chains_1d)
        n = len(chains_1d[0])
        means = np.array([np.mean(c) for c in chains_1d])
        grand = means.mean()
        B = n / (m - 1) * np.sum((means - grand) ** 2)
        W = np.mean([np.var(c, ddof=1) for c in chains_1d])
        var_hat = (1.0 - 1.0 / n) * W + B / n
        return float(np.sqrt(var_hat / (W + 1e-30)))

    # split: 每链切两半
    split_chains = []
    for c in chains:
        half = n_per // 2
        split_chains.append(c[:half, param_idx])
        split_chains.append(c[half:2 * half, param_idx])

    rhat_raw = _gr(split_chains)

    # rank-normalized
    rn = _rank_normalize(flat)
    # 还原成 split chains 形状
    rn_chunks = np.split(rn, len(chains))
    rn_split = []
    for ck in rn_chunks:
        half = len(ck) // 2
        rn_split.append(ck[:half])
        rn_split.append(ck[half:2 * half])
    rhat_rn = _gr(rn_split)

    return max(rhat_raw, rhat_rn)


def _split_rhat_naive(chains: list, param_idx: int) -> float:
    n_per = chains[0].shape[0]
    split_chains = []
    for c in chains:
        half = n_per // 2
        split_chains.append(c[:half, param_idx])
        split_chains.append(c[half:2 * half, param_idx])
    m = len(split_chains)
    n = len(split_chains[0])
    means = np.array([np.mean(c) for c in split_chains])
    grand = means.mean()
    B = n / (m - 1) * np.sum((means - grand) ** 2)
    W = np.mean([np.var(c, ddof=1) for c in split_chains])
    var_hat = (1.0 - 1.0 / n) * W + B / n
    return float(np.sqrt(var_hat / (W + 1e-30)))


# ────────────────────────────────────────────────────────────
# 多链 MCMC + 完整链保存
# ────────────────────────────────────────────────────────────
def run_multi_chain_with_chains(
    ref_x_full, y_obs, obs_noise, prior_stats,
    model, sx, sy, device, base_seed: int, n_chains: int,
):
    """魔改版 run_mcmc_multi_chain：保留 per-chain accept 与完整链。"""
    n_params = len(INVERSE_CALIB_PARAMS)
    prop_scales = np.array(
        [prior_stats[c]["std"] for c in INVERSE_CALIB_PARAMS]
    ) * rp.PROPOSAL_SCALE

    chains = []
    per_chain_accept = []

    for k in range(n_chains):
        rng_k = np.random.RandomState(base_seed + k * 7919)
        theta0_k = np.array([
            rng_k.uniform(prior_stats[c]["mean"] - prior_stats[c]["std"],
                          prior_stats[c]["mean"] + prior_stats[c]["std"])
            for c in INVERSE_CALIB_PARAMS
        ])

        samples = np.zeros((rp.N_TOTAL, n_params), float)
        theta_curr = theta0_k.copy()
        lp_curr = rp._log_prior(theta_curr, prior_stats)
        ll_curr = rp._log_likelihood(theta_curr, ref_x_full, y_obs, obs_noise,
                                      model, sx, sy, device)
        lpost_curr = lp_curr + ll_curr
        n_accept_sampling = 0

        for t in range(rp.N_TOTAL):
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
                if t >= rp.BURN_IN:
                    n_accept_sampling += 1
            samples[t] = theta_curr

        n_samp = rp.N_TOTAL - rp.BURN_IN
        per_chain_accept.append(n_accept_sampling / n_samp if n_samp > 0 else 0.0)
        # thin 后存（与 canonical 一致）
        chains.append(samples[rp.BURN_IN::rp.THIN])

    return chains, per_chain_accept


# ────────────────────────────────────────────────────────────
# 对单模型跑完整诊断
# ────────────────────────────────────────────────────────────
def run_diagnostics_for_model(model_id: str, n_chains: int):
    logger.info(f"[{model_id}] diagnostics: n_chains={n_chains}, "
                f"N_TOTAL={rp.N_TOTAL}, BURN={rp.BURN_IN}, THIN={rp.THIN}")

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

    # 同 canonical 的 case 选择（同一 SEED+42 的 rng，保证与 benchmark_summary 对齐）
    tau = rp.TAU
    s = test_df[PRIMARY_STRESS_OUTPUT].values
    low_idx  = np.where(s < 0.92 * tau)[0]
    near_idx = np.where((s >= 0.92 * tau) & (s < tau))[0]
    high_idx = np.where(s >= tau)[0]
    rng0 = np.random.RandomState(SEED + 42)
    n_cases = INVERSE_N_BENCHMARK
    selected = []
    for cat_idx, label in [(low_idx, "low"), (near_idx, "near"), (high_idx, "high")]:
        n_cat = max(1, n_cases // 3)
        chosen = rng0.choice(cat_idx, min(n_cat, len(cat_idx)), replace=False)
        selected.extend([(int(i), label) for i in chosen])

    # 输出目录
    base_out = os.path.join(experiment_dir("posterior"), model_id, "diagnostics")
    ensure_dir(base_out)
    chains_dir = ensure_dir(os.path.join(base_out, "chains"))

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    fh = logging.FileHandler(os.path.join(base_out, f"diagnostics_{ts}.log"))
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

        base_seed_ci = SEED + 1000 + ci
        chains, per_chain_accept = run_multi_chain_with_chains(
            x_true, y_obs_noisy, noise, prior_stats,
            model, sx, sy, device, base_seed_ci, n_chains,
        )

        # 保存完整 chains
        np.savez_compressed(
            os.path.join(chains_dir, f"case_{ci:02d}.npz"),
            chains=np.stack(chains, axis=0),
            per_chain_accept=np.array(per_chain_accept),
            row_idx=row_idx, category=cat,
            param_names=np.array(INVERSE_CALIB_PARAMS),
            obs_cols=np.array(rp.OBS_COLS),
            y_obs_noisy=y_obs_noisy, obs_noise=noise,
            x_true=x_true,
        )

        # rhat / split-rhat / ESS per param
        rhat_vec = rp.compute_rhat(chains)
        for pi, param in enumerate(INVERSE_CALIB_PARAMS):
            rhat_split = split_rhat(chains, pi)
            ess_total = ess_multi_chain(chains, pi)
            p_true = float(x_true[INPUT_COLS.index(param)])
            # 聚合后验用于均值/CI（与 canonical 一致）
            pooled = np.concatenate([c[:, pi] for c in chains])
            rows.append({
                "case_idx": ci,
                "row_idx": row_idx,
                "category": cat,
                "param": param,
                "true_value": p_true,
                "post_mean_pooled": float(np.mean(pooled)),
                "post_std_pooled": float(np.std(pooled)),
                "rhat_classic": float(rhat_vec[pi]),
                "rhat_split_rank": float(rhat_split),
                "ESS_total": ess_total,
                "ESS_per_chain_mean": ess_total / n_chains,
                "n_chains": n_chains,
                "n_per_chain": chains[0].shape[0],
                "mean_accept_rate": float(np.mean(per_chain_accept)),
                "min_accept_rate": float(np.min(per_chain_accept)),
                "max_accept_rate": float(np.max(per_chain_accept)),
                "per_chain_accept": ";".join(f"{a:.4f}" for a in per_chain_accept),
            })
        logger.info(
            f"  case {ci+1}/{len(selected)}: "
            f"rhat_max={rhat_vec.max():.3f}, "
            f"ESS_min={min(ess_multi_chain(chains, pi) for pi in range(len(INVERSE_CALIB_PARAMS))):.0f}, "
            f"accept={np.mean(per_chain_accept):.3f}"
        )

    df = pd.DataFrame(rows)
    out_csv = os.path.join(base_out, "mcmc_diagnostics.csv")
    df.to_csv(out_csv, index=False)
    logger.info(f"[{model_id}] 写入 {out_csv} ({len(df)} 行)")

    # 汇总报告
    summary = {
        "model_id": model_id,
        "n_cases": len(selected),
        "n_chains": n_chains,
        "n_per_chain": chains[0].shape[0],
        "rhat_classic_max": float(df["rhat_classic"].max()),
        "rhat_classic_mean": float(df["rhat_classic"].mean()),
        "rhat_split_rank_max": float(df["rhat_split_rank"].max()),
        "rhat_split_rank_mean": float(df["rhat_split_rank"].mean()),
        "ESS_total_min": float(df["ESS_total"].min()),
        "ESS_total_mean": float(df["ESS_total"].mean()),
        "mean_accept_rate": float(df["mean_accept_rate"].mean()),
        "fraction_converged_rhat_lt_1p1": float((df["rhat_split_rank"] < 1.1).mean()),
        "fraction_converged_rhat_lt_1p01": float((df["rhat_split_rank"] < 1.01).mean()),
    }

    mf = make_experiment_manifest(
        experiment_id = "posterior_mcmc_diagnostics",
        model_id      = model_id,
        input_source  = f"fixed_split test.csv + {model_id} checkpoint",
        outputs_saved = [out_csv, chains_dir],
        key_results   = summary,
        source_script = os.path.abspath(__file__),
        extra         = {"mcmc_config": {
            "N_TOTAL": rp.N_TOTAL, "BURN_IN": rp.BURN_IN, "THIN": rp.THIN,
            "PROPOSAL_SCALE": rp.PROPOSAL_SCALE,
            "OBS_NOISE_FRAC": rp.OBS_NOISE_FRAC,
            "OBS_COLS": rp.OBS_COLS, "N_CHAINS": n_chains,
        }},
    )
    write_manifest(os.path.join(base_out, "diagnostics_manifest.json"), mf)

    logger.info(f"[{model_id}] SUMMARY: {json.dumps(summary, indent=2)}")
    logger.removeHandler(fh)
    return summary


# ────────────────────────────────────────────────────────────
# 入口
# ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    model_id_env = os.environ.get("MODEL_ID", "all")
    model_ids = list(MODELS.keys()) if model_id_env == "all" else [model_id_env]

    all_summaries = {}
    for mid in model_ids:
        if mid not in MODELS:
            logger.error(f"未知 MODEL_ID: {mid}")
            continue
        logger.info("=" * 60)
        logger.info(f"DIAGNOSTICS — {mid}")
        logger.info("=" * 60)
        all_summaries[mid] = run_diagnostics_for_model(mid, DIAG_N_CHAINS)

    # 跨模型汇总
    if len(all_summaries) > 1:
        top_out = os.path.join(experiment_dir("posterior"), "diagnostics_all_models.json")
        with open(top_out, "w") as f:
            json.dump(all_summaries, f, indent=2)
        logger.info(f"跨模型汇总写入 {top_out}")
