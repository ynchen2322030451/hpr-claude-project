# run_sensitivity_0404.py
# ============================================================
# BNN 0414 敏感性分析脚本（基于 0411 版本改写）
#
# 与 0411 的差异：
#   - 模型：BayesianMLP 替代 HeteroMLP
#   - Sobol 样本评估：对每个输入矩阵取 MC 均值（BNN_N_MC_SOBOL 次权重采样的平均）
#   - Spearman / PRCC 完全不变（仅依赖训练数据）
#
# 实现方法：
#   1) Sobol 指数（Jansen 估计量 + CI，主文主方法）
#   2) Spearman 秩相关（附录，方向信息）
#   3) PRCC——偏秩相关（附录，净效应）
#
# 调用方式:
#   MODEL_ID=bnn-baseline  SA_METHOD=sobol   python run_sensitivity_0404.py
#   MODEL_ID=bnn-data-mono SA_METHOD=all     python run_sensitivity_0404.py
#
# 输出:
#   experiments_0404/experiments/sensitivity/<model_id>/
#     sobol_results.csv        — Sobol S1/ST 主表（主文图源）
#     sobol_full.json          — 每个输出的完整 S1/ST/CI
#     spearman_results.csv     — Spearman ρ 矩阵
#     prcc_results.csv         — PRCC 矩阵
#     sensitivity_manifest.json
# ============================================================

import os, sys, json, pickle, logging
from datetime import datetime

import numpy as np
import pandas as pd
import torch

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Resolve code roots: add config/, bnn code root, and legacy code/0310/ to path
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
        # [BNN0414 FIX] bnn0414 paths go to front (high prio); legacy to back.
        # Without this, HPR_LEGACY_DIR / code/0310 lands at sys.path[0] and
        # shadows bnn0414/experiment_config_0404.py with the pre-BNN version.
        _is_legacy = any(seg in _p for seg in ('/0310', 'hpr_legacy'))
        if _is_legacy:
            if _p not in sys.path:
                sys.path.append(_p)
        else:
            sys.path.insert(0, _p)

from experiment_config_0404 import (
    INPUT_COLS, OUTPUT_COLS, PRIMARY_SA_OUTPUTS,
    SOBOL_N_BASE, SOBOL_BOOTSTRAP, SOBOL_CI_LEVEL,
    BNN_N_MC_SOBOL,
    SEED, DEVICE,
    FIXED_SPLIT_DIR, EXPR_ROOT_OLD, EXPR_ROOT_0404,
    model_artifacts_dir, experiment_dir, ensure_dir,
    OUT1, OUT2,
)
from model_registry_0404 import MODELS
from manifest_utils_0404 import write_manifest, make_experiment_manifest, resolve_output_dir
from bnn_model import BayesianMLP, mc_predict, get_device, seed_all
from bnn_multifidelity import (
    MultiFidelityBNN_Stacked, MultiFidelityBNN_Residual,
    MultiFidelityBNN_Hybrid,
)

# Import MF reorder helper from evaluation module
_EVAL_DIR = os.path.join(_CODE_ROOT, 'experiments_0404', 'evaluation')
if _EVAL_DIR not in sys.path:
    sys.path.insert(0, _EVAL_DIR)
from run_eval_0404 import _attach_mf_reorder

# ────────────────────────────────────────────────────────────
# 日志
# ────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# Sobol 计算的输出集（主文关注 iter2，附录可扩展至全部）
SA_OUTPUTS_MAIN = PRIMARY_SA_OUTPUTS
SA_OUTPUTS_ALL  = OUTPUT_COLS

N_REPEATS = 50     # Jansen 重复估计次数（bootstrap-style）
CI_Z      = 1.645  # 90% CI（SOBOL_CI_LEVEL = 0.90）


# ────────────────────────────────────────────────────────────
# Artifact / model loading (self-contained for BNN)
# ────────────────────────────────────────────────────────────
def _resolve_artifacts(model_id: str):
    """返回 (ckpt_path, scaler_path)。
    兼容 BNN 的 checkpoint_{mid}.pt 与 0411 的 checkpoint_{mid}_fixed.pt。"""
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


def _load_model(ckpt_path: str, device):
    ckpt = torch.load(ckpt_path, map_location=device)
    hp = ckpt.get("best_params", ckpt.get("hp", {}))
    cls_name = ckpt.get("model_class", "BayesianMLP")

    if cls_name == "MultiFidelityBNN_Stacked":
        model = MultiFidelityBNN_Stacked(
            in_dim=len(INPUT_COLS),
            n_iter1=len(OUT1), n_iter2=len(OUT2),
            width1=int(hp["width1"]), depth1=int(hp["depth1"]),
            width2=int(hp["width2"]), depth2=int(hp["depth2"]),
            prior_sigma=float(hp.get("prior_sigma", 1.0)),
        ).to(device)
    elif cls_name == "MultiFidelityBNN_Residual":
        model = MultiFidelityBNN_Residual(
            in_dim=len(INPUT_COLS),
            n_iter1=len(OUT1),
            width1=int(hp["width1"]), depth1=int(hp["depth1"]),
            width_delta=int(hp["width2"]), depth_delta=int(hp["depth2"]),
            prior_sigma=float(hp.get("prior_sigma", 1.0)),
        ).to(device)
    elif cls_name == "MultiFidelityBNN_Hybrid":
        model = MultiFidelityBNN_Hybrid(
            in_dim=len(INPUT_COLS),
            n_iter1=len(OUT1),
            width1=int(hp["width1"]), depth1=int(hp["depth1"]),
            width_delta=int(hp.get("width2", 64)),
            depth_delta=int(hp.get("depth2", 2)),
            width_direct=int(hp["width2"]), depth_direct=int(hp["depth2"]),
            prior_sigma=float(hp.get("prior_sigma", 1.0)),
        ).to(device)
    else:
        model = BayesianMLP(
            in_dim=len(INPUT_COLS), out_dim=len(OUTPUT_COLS),
            width=int(hp["width"]), depth=int(hp["depth"]),
            prior_sigma=float(hp.get("prior_sigma", 1.0)),
            homoscedastic=ckpt.get("homoscedastic", False),
        ).to(device)

    model.load_state_dict(ckpt["model_state_dict"])
    model.eval()
    return model


def _load_scalers(scaler_path: str):
    with open(scaler_path, "rb") as f:
        return pickle.load(f)


# ────────────────────────────────────────────────────────────
# 工具：输入采样范围（从 meta_stats.json 读取）
# ────────────────────────────────────────────────────────────
def _load_input_bounds() -> list:
    """从 fixed_level2 meta_stats 读取输入范围。"""
    candidates = [
        os.path.join(EXPR_ROOT_0404, "meta_stats.json"),
        os.path.join(EXPR_ROOT_OLD, "fixed_surrogate_fixed_level2", "meta_stats.json"),
        os.path.join(EXPR_ROOT_OLD, "fixed_surrogate_fixed_base",   "meta_stats.json"),
        os.path.join(EXPR_ROOT_OLD, "meta_stats.json"),
    ]
    meta_path = next((p for p in candidates if os.path.exists(p)), None)
    if meta_path is None:
        raise FileNotFoundError("Cannot find meta_stats.json for Sobol input bounds.")

    with open(meta_path) as f:
        meta = json.load(f)

    bounds = []
    for c in INPUT_COLS:
        st = meta["input_stats"][c]
        lo, hi = float(st["min"]), float(st["max"])
        if not np.isfinite(lo) or not np.isfinite(hi) or hi <= lo:
            raise ValueError(f"Invalid bound for {c}: ({lo}, {hi})")
        bounds.append((lo, hi))
    return bounds


# ────────────────────────────────────────────────────────────
# 工具：BNN MC 均值预测（原始量纲）
# ────────────────────────────────────────────────────────────
def _bnn_predict_mean(model, X_np: np.ndarray, sx, sy, device) -> np.ndarray:
    """对每个输入点，返回 BNN 预测均值（MC 平均后），shape (N, n_out)。"""
    mu_mean, _, _, _, _ = mc_predict(
        model, X_np, sx, sy, device, n_mc=BNN_N_MC_SOBOL
    )
    return mu_mean


# ────────────────────────────────────────────────────────────
# Sobol — Jansen 估计量
# ────────────────────────────────────────────────────────────
def _jansen(YA: np.ndarray, YB: np.ndarray, YABi: np.ndarray):
    VY = np.var(np.concatenate([YA, YB]), ddof=1)
    if VY <= 1e-15:
        return 0.0, 0.0
    ST = np.mean((YA - YABi) ** 2) / (2.0 * VY)
    S1 = 1.0 - np.mean((YB - YABi) ** 2) / (2.0 * VY)
    return float(S1), float(ST)


def _sobol_one_output(
    model, sx, sy, out_idx: int, bounds: list, device, base_seed: int
):
    """对单个输出重复估计 N_REPEATS 次 Sobol S1/ST。"""
    d = len(bounds)
    s1_all, st_all = [], []

    for r in range(N_REPEATS):
        rng = np.random.RandomState(base_seed + 1000 * r + out_idx)

        A = np.column_stack([rng.uniform(lo, hi, SOBOL_N_BASE) for lo, hi in bounds])
        B = np.column_stack([rng.uniform(lo, hi, SOBOL_N_BASE) for lo, hi in bounds])

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


def _summarize(arr: np.ndarray):
    """返回 mean, ci_lo, ci_hi（列方向）。"""
    mean = arr.mean(axis=0)
    std  = arr.std(axis=0, ddof=1) if arr.shape[0] > 1 else np.zeros(arr.shape[1])
    half = CI_Z * std / np.sqrt(max(arr.shape[0], 1))
    return mean, mean - half, mean + half


def run_sobol(model_id: str, model, sx, sy, device, out_dir: str,
              output_list: list = None, verbose: bool = True):
    if output_list is None:
        output_list = SA_OUTPUTS_MAIN

    bounds = _load_input_bounds()
    rows   = []
    full   = {}

    for out_name in output_list:
        if out_name not in OUTPUT_COLS:
            logger.warning(f"[Sobol] 输出 {out_name} 不在 OUTPUT_COLS，跳过")
            continue
        out_idx = OUTPUT_COLS.index(out_name)

        logger.info(
            f"[Sobol][{model_id}] {out_name} "
            f"({N_REPEATS} repeats × {SOBOL_N_BASE} samples × "
            f"{len(INPUT_COLS)+2} matrices × n_mc={BNN_N_MC_SOBOL})"
        )

        s1_all, st_all = _sobol_one_output(model, sx, sy, out_idx, bounds, device, SEED)

        s1_mean, s1_lo, s1_hi = _summarize(s1_all)
        st_mean, st_lo, st_hi = _summarize(st_all)

        for j, inp in enumerate(INPUT_COLS):
            rows.append({
                "model_id":   model_id,
                "output":     out_name,
                "input":      inp,
                "S1_mean":    float(s1_mean[j]),
                "S1_ci_lo":   float(s1_lo[j]),
                "S1_ci_hi":   float(s1_hi[j]),
                "ST_mean":    float(st_mean[j]),
                "ST_ci_lo":   float(st_lo[j]),
                "ST_ci_hi":   float(st_hi[j]),
                "S1_ci_spans_zero": bool(s1_lo[j] <= 0 <= s1_hi[j]),
                "ST_ci_spans_zero": bool(st_lo[j] <= 0 <= st_hi[j]),
            })

        full[out_name] = {
            "S1": {"mean": s1_mean.tolist(), "lo": s1_lo.tolist(), "hi": s1_hi.tolist()},
            "ST": {"mean": st_mean.tolist(), "lo": st_lo.tolist(), "hi": st_hi.tolist()},
        }

        if verbose:
            logger.info(
                f"  Top S1: {INPUT_COLS[int(np.argmax(s1_mean))]}={s1_mean.max():.3f}, "
                f"Top ST: {INPUT_COLS[int(np.argmax(st_mean))]}={st_mean.max():.3f}"
            )

    df = pd.DataFrame(rows)
    csv_path  = os.path.join(out_dir, "sobol_results.csv")
    json_path = os.path.join(out_dir, "sobol_full.json")
    df.to_csv(csv_path, index=False)

    meta = {
        "model_id":   model_id,
        "N_base":     SOBOL_N_BASE,
        "N_repeats":  N_REPEATS,
        "n_mc_sobol": BNN_N_MC_SOBOL,
        "CI_level":   SOBOL_CI_LEVEL,
        "inputs":     INPUT_COLS,
        "outputs":    output_list,
        "results":    full,
    }
    with open(json_path, "w") as f:
        json.dump(meta, f, indent=2)

    logger.info(f"[Sobol][{model_id}] → {csv_path}")
    return df, meta


# ────────────────────────────────────────────────────────────
# Spearman 秩相关（与 0411 完全一致）
# ────────────────────────────────────────────────────────────
def run_spearman(model_id: str, out_dir: str, output_list: list = None):
    from scipy.stats import spearmanr

    if output_list is None:
        output_list = SA_OUTPUTS_MAIN

    train_df = pd.read_csv(os.path.join(FIXED_SPLIT_DIR, "train.csv"))
    X_train = train_df[INPUT_COLS].values
    rows = []

    for out_name in output_list:
        if out_name not in train_df.columns:
            logger.warning(f"[Spearman] {out_name} 不在 train.csv，跳过")
            continue
        y = train_df[out_name].values

        for j, inp in enumerate(INPUT_COLS):
            x = X_train[:, j]
            rho, p = spearmanr(x, y)
            rows.append({
                "model_id": model_id,
                "output":   out_name,
                "input":    inp,
                "rho":      float(rho),
                "p_value":  float(p),
                "abs_rho":  float(abs(rho)),
                "sign":     "+" if rho >= 0 else "-",
                "data_source": "train_split",
            })

    df = pd.DataFrame(rows)
    csv_path = os.path.join(out_dir, "spearman_results.csv")
    df.to_csv(csv_path, index=False)
    logger.info(f"[Spearman][{model_id}] → {csv_path}")
    return df


# ────────────────────────────────────────────────────────────
# PRCC（与 0411 完全一致）
# ────────────────────────────────────────────────────────────
def run_prcc(model_id: str, out_dir: str, output_list: list = None):
    from scipy.stats import spearmanr, rankdata
    from sklearn.linear_model import LinearRegression

    if output_list is None:
        output_list = SA_OUTPUTS_MAIN

    train_df = pd.read_csv(os.path.join(FIXED_SPLIT_DIR, "train.csv"))
    X_all = train_df[INPUT_COLS].values.astype(float)
    n, d  = X_all.shape

    X_rank = np.column_stack([rankdata(X_all[:, j]) for j in range(d)])

    rows = []

    for out_name in output_list:
        if out_name not in train_df.columns:
            logger.warning(f"[PRCC] {out_name} 不在 train.csv，跳过")
            continue
        y      = train_df[out_name].values.astype(float)
        y_rank = rankdata(y)

        for i, inp in enumerate(INPUT_COLS):
            others_idx = [j for j in range(d) if j != i]
            Z_rank = X_rank[:, others_idx]

            reg_x = LinearRegression().fit(Z_rank, X_rank[:, i])
            resid_x = X_rank[:, i] - reg_x.predict(Z_rank)

            reg_y = LinearRegression().fit(Z_rank, y_rank)
            resid_y = y_rank - reg_y.predict(Z_rank)

            rho_prcc, p_prcc = spearmanr(resid_x, resid_y)
            rows.append({
                "model_id": model_id,
                "output":   out_name,
                "input":    inp,
                "prcc":     float(rho_prcc),
                "p_value":  float(p_prcc),
                "abs_prcc": float(abs(rho_prcc)),
                "sign":     "+" if rho_prcc >= 0 else "-",
            })

    df = pd.DataFrame(rows)
    csv_path = os.path.join(out_dir, "prcc_results.csv")
    df.to_csv(csv_path, index=False)
    logger.info(f"[PRCC][{model_id}] → {csv_path}")
    return df


# ────────────────────────────────────────────────────────────
# 汇总比较表
# ────────────────────────────────────────────────────────────
def make_sensitivity_comparison(sobol_df: pd.DataFrame, spearman_df: pd.DataFrame,
                                prcc_df: pd.DataFrame, out_dir: str, model_id: str):
    rows = []
    for out_name in SA_OUTPUTS_MAIN:
        s_sub  = sobol_df[sobol_df["output"] == out_name][["input","ST_mean"]].set_index("input")
        sp_sub = spearman_df[spearman_df["output"] == out_name][["input","abs_rho"]].set_index("input")
        pr_sub = prcc_df[prcc_df["output"] == out_name][["input","abs_prcc"]].set_index("input") if prcc_df is not None else None

        for inp in INPUT_COLS:
            row = {
                "model_id": model_id,
                "output":   out_name,
                "input":    inp,
                "Sobol_ST":     float(s_sub.loc[inp, "ST_mean"])  if inp in s_sub.index  else np.nan,
                "Spearman_rho": float(sp_sub.loc[inp, "abs_rho"]) if inp in sp_sub.index else np.nan,
                "PRCC":         float(pr_sub.loc[inp, "abs_prcc"]) if (pr_sub is not None and inp in pr_sub.index) else np.nan,
            }
            rows.append(row)

    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(out_dir, "sensitivity_comparison.csv"), index=False)
    logger.info(f"[compare] 多方法比较 → sensitivity_comparison.csv")
    return df


# ────────────────────────────────────────────────────────────
# 入口
# ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    MODEL_ID_OVERRIDE  = "bnn-baseline"
    SA_METHOD_OVERRIDE = "all"   # "sobol" | "spearman" | "prcc" | "all"
    SA_OUTPUT_OVERRIDE = "main"  # "main" | "all"

    model_id  = os.environ.get("MODEL_ID",  MODEL_ID_OVERRIDE)
    sa_method = os.environ.get("SA_METHOD", SA_METHOD_OVERRIDE)
    sa_output = os.environ.get("SA_OUTPUT", SA_OUTPUT_OVERRIDE)
    force     = os.environ.get("SA_FORCE",  "0") == "1"

    if model_id not in MODELS:
        raise ValueError(f"未知 MODEL_ID: {model_id}。可选: {list(MODELS.keys())}")

    output_list = SA_OUTPUTS_MAIN if sa_output == "main" else SA_OUTPUTS_ALL

    out_dir = resolve_output_dir(
        os.path.join(experiment_dir("sensitivity"), model_id),
        script_name=os.path.basename(__file__),
    )

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    fh = logging.FileHandler(os.path.join(out_dir, f"sensitivity_{ts}.log"))
    fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(fh)

    logger.info(f"sensitivity_0404 (BNN) | model={model_id} | method={sa_method} | outputs={sa_output}")

    # 加载模型（Sobol 需要）
    device  = get_device(DEVICE)
    seed_all(SEED)
    ckpt_path, scaler_path = _resolve_artifacts(model_id)
    model   = _load_model(ckpt_path, device)
    scalers = _load_scalers(scaler_path)
    _attach_mf_reorder(model, scalers)
    sx, sy  = scalers["sx"], scalers["sy"]
    model.eval()

    sobol_df = spearman_df = prcc_df = None

    if sa_method in ("sobol", "all"):
        sobol_df, sobol_meta = run_sobol(model_id, model, sx, sy, device, out_dir, output_list)

    if sa_method in ("spearman", "all"):
        spearman_df = run_spearman(model_id, out_dir, output_list)

    if sa_method in ("prcc", "all"):
        prcc_df = run_prcc(model_id, out_dir, output_list)

    if sa_method == "all" and sobol_df is not None and spearman_df is not None:
        make_sensitivity_comparison(sobol_df, spearman_df, prcc_df, out_dir, model_id)

    outputs_saved = [
        os.path.join(out_dir, f)
        for f in ["sobol_results.csv", "spearman_results.csv", "prcc_results.csv",
                  "sensitivity_comparison.csv"]
        if os.path.exists(os.path.join(out_dir, f))
    ]
    mf = make_experiment_manifest(
        experiment_id = f"sensitivity_{sa_method}",
        model_id      = model_id,
        input_source  = FIXED_SPLIT_DIR,
        outputs_saved = outputs_saved,
        key_results   = {"sa_method": sa_method, "output_list": output_list},
        source_script = __file__,
        extra = {
            "N_repeats": N_REPEATS, "N_base": SOBOL_N_BASE,
            "CI_level": SOBOL_CI_LEVEL, "n_mc_sobol": BNN_N_MC_SOBOL,
            "model_class": "BayesianMLP",
        },
    )
    write_manifest(os.path.join(out_dir, "sensitivity_manifest.json"), mf)
    logger.info(f"[{model_id}] sensitivity 完成")
