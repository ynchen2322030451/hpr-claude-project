# run_train_0404.py
# ============================================================
# 0404 统一训练脚本
#
# 支持 5 个模型：baseline / data-mono / phy-mono / phy-ineq / data-mono-ineq
# 支持 fixed split 和 repeated split
# 自动检测旧 checkpoint，不重复训练已有模型
#
# 由 run_0404.py 通过环境变量调用：
#   MODEL_ID=baseline python run_train_0404.py
#   MODEL_ID=phy-mono  python run_train_0404.py
#
# 也可以直接设置 MODEL_ID 变量后运行：
#   直接修改底部 __main__ 里的 MODEL_ID_OVERRIDE
# ============================================================

import os, sys, json, pickle, time, shutil, logging
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F
import optuna
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _SCRIPT_DIR)

from experiment_config_0404 import (
    INPUT_COLS, OUTPUT_COLS, SEED, TRIALS_MAIN, TRIALS_ABLATION,
    FIXED_SPLIT_DIR, EXPR_ROOT_0404, EXPR_ROOT_OLD,
    TEST_FRAC, VAL_FRAC, REPEAT_N, REPEAT_SEEDS,
    model_artifacts_dir, model_manifests_dir, model_logs_dir,
    model_fixed_eval_dir, ensure_dir,
    get_csv_path, DEVICE,
)
from model_registry_0404 import (
    MODELS, PHYSICS_IDX_PAIRS_HIGH, INEQUALITY_RULES,
    get_optuna_space,
)
from manifest_utils_0404 import write_manifest, make_training_manifest
from run_phys_levels_main import (
    HeteroMLP, gaussian_nll, seed_all, get_device,
    build_mono_pairs_spearman, loss_level2_monotone_from_mu,
)

# ────────────────────────────────────────────────────────────
# 旧目录 → 新目录 checkpoint 映射（直接复用已有产出）
# ────────────────────────────────────────────────────────────
_OLD_ARTIFACTS = {
    "baseline": {
        "ckpt":   os.path.join(EXPR_ROOT_OLD, "fixed_surrogate_fixed_base",   "checkpoint_level0.pt"),
        "scaler": os.path.join(EXPR_ROOT_OLD, "fixed_surrogate_fixed_base",   "scalers_level0.pkl"),
        "best":   os.path.join(EXPR_ROOT_OLD, "fixed_surrogate_fixed_base",   "best_level0.json"),
        "metrics":os.path.join(EXPR_ROOT_OLD, "fixed_surrogate_fixed_base",   "metrics_level0.json"),
    },
    "data-mono": {
        "ckpt":   os.path.join(EXPR_ROOT_OLD, "fixed_surrogate_fixed_level2", "checkpoint_level2.pt"),
        "scaler": os.path.join(EXPR_ROOT_OLD, "fixed_surrogate_fixed_level2", "scalers_level2.pkl"),
        "best":   os.path.join(EXPR_ROOT_OLD, "fixed_surrogate_fixed_level2", "best_level2.json"),
        "metrics":os.path.join(EXPR_ROOT_OLD, "fixed_surrogate_fixed_level2", "metrics_level2.json"),
    },
}


# ────────────────────────────────────────────────────────────
# 日志
# ────────────────────────────────────────────────────────────
def setup_logger(model_id: str, log_dir: str) -> logging.Logger:
    ensure_dir(log_dir)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"train_{model_id}_{ts}.log")
    logger = logging.getLogger(f"train_{model_id}")
    logger.setLevel(logging.DEBUG)
    if not logger.handlers:
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setLevel(logging.DEBUG)
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.INFO)
        fmt = logging.Formatter("[%(asctime)s %(levelname)s] %(message)s", "%H:%M:%S")
        fh.setFormatter(fmt); ch.setFormatter(fmt)
        logger.addHandler(fh); logger.addHandler(ch)
    return logger


# ────────────────────────────────────────────────────────────
# 数据加载（优先 CSV，回退 fixed split CSV）
# ────────────────────────────────────────────────────────────
def load_full_dataset(logger) -> pd.DataFrame:
    csv_path = get_csv_path()
    if csv_path:
        logger.info(f"Loading CSV from: {csv_path}")
        df = pd.read_csv(csv_path)
    else:
        logger.info("Server CSV not reachable; concatenating fixed_split CSVs")
        parts = []
        for split in ["train", "val", "test"]:
            p = os.path.join(FIXED_SPLIT_DIR, f"{split}.csv")
            if os.path.exists(p):
                parts.append(pd.read_csv(p))
        if not parts:
            raise FileNotFoundError("No data source available (server CSV or fixed_split CSVs)")
        df = pd.concat(parts, ignore_index=True)

    missing = [c for c in INPUT_COLS + OUTPUT_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")
    df = df[INPUT_COLS + OUTPUT_COLS].dropna()
    logger.info(f"Dataset loaded: {len(df)} rows")
    return df


# ────────────────────────────────────────────────────────────
# Fixed split 加载（从已有 frozen split）
# ────────────────────────────────────────────────────────────
def load_fixed_split(df: pd.DataFrame, logger):
    meta_path = os.path.join(FIXED_SPLIT_DIR, "split_meta.json")
    with open(meta_path) as f:
        meta = json.load(f)
    n_expected = meta["n_total"]
    if len(df) != n_expected:
        # 预期：fixed_split 创建时数据集为 2900 行；后续新增样本不参与此 split。
        # 训练仅使用 split 索引内的行，多余行不影响结果。论文中报告 n=2900。
        logger.warning(
            f"Dataset size mismatch: got {len(df)}, split expects {n_expected}. "
            f"Extra {len(df)-n_expected} rows are outside the frozen split and will not be used."
        )

    idx_train = pd.read_csv(os.path.join(FIXED_SPLIT_DIR, "train_indices.csv")).squeeze().tolist()
    idx_val   = pd.read_csv(os.path.join(FIXED_SPLIT_DIR, "val_indices.csv")).squeeze().tolist()
    idx_test  = pd.read_csv(os.path.join(FIXED_SPLIT_DIR, "test_indices.csv")).squeeze().tolist()

    X = df[INPUT_COLS].values.astype(np.float64)
    Y = df[OUTPUT_COLS].values.astype(np.float64)

    return (X[idx_train], Y[idx_train],
            X[idx_val],   Y[idx_val],
            X[idx_test],  Y[idx_test],
            meta["seed"])


def make_repeat_split(df: pd.DataFrame, seed: int):
    X = df[INPUT_COLS].values.astype(np.float64)
    Y = df[OUTPUT_COLS].values.astype(np.float64)
    n = len(X)
    idx = np.arange(n)
    # test split
    idx_trainval, idx_test = train_test_split(idx, test_size=TEST_FRAC, random_state=seed)
    # val split
    idx_train, idx_val = train_test_split(idx_trainval, test_size=VAL_FRAC, random_state=seed + 1)
    return (X[idx_train], Y[idx_train],
            X[idx_val],   Y[idx_val],
            X[idx_test],  Y[idx_test], seed)


# ────────────────────────────────────────────────────────────
# Loss 函数
# ────────────────────────────────────────────────────────────
def loss_phy_monotone(model, X_batch_t: torch.Tensor, phy_pairs: list, w: float) -> torch.Tensor:
    """
    物理先验单调性损失。
    phy_pairs: [(input_idx, output_idx, sign)]
    使用与 loss_level2_monotone_from_mu 相同的梯度惩罚机制。
    """
    if not phy_pairs or w == 0.0:
        return torch.tensor(0.0, device=X_batch_t.device)

    X_batch_t = X_batch_t.detach().requires_grad_(True)
    mu, _ = model(X_batch_t)   # (B, n_out)
    total = torch.tensor(0.0, device=X_batch_t.device)

    for (inp_idx, out_idx, sign) in phy_pairs:
        # 计算 ∂μ_j / ∂x_i，使用 autograd
        grad_out = torch.zeros_like(mu)
        grad_out[:, out_idx] = 1.0
        grads = torch.autograd.grad(
            mu, X_batch_t, grad_outputs=grad_out,
            retain_graph=True, create_graph=True,
        )[0]   # (B, n_in)
        g = grads[:, inp_idx]   # (B,)
        # 惩罚：如果梯度方向与 sign 相反
        violation = F.relu(-sign * g)
        total = total + violation.mean()

    return w * total / max(len(phy_pairs), 1)


def loss_inequality(mu_raw: torch.Tensor, sy, w: float, device) -> torch.Tensor:
    """
    物理不等式约束损失（在标准化空间 or 原始量纲空间）。
    这里在标准化空间中操作（mu 是 sy.transform 后的）。
    """
    if w == 0.0:
        return torch.tensor(0.0, device=device)

    total = torch.tensor(0.0, device=device)
    for rule in INEQUALITY_RULES:
        rtype = rule["type"]
        if rtype == "greater_equal":
            j_big   = rule["j_big"]
            j_small = rule["j_small"]
            viol = F.relu(mu_raw[:, j_small] - mu_raw[:, j_big])
            total = total + viol.mean()
        elif rtype == "nonneg":
            # 标准化空间中，0 对应 -mean/std，需要逆变换
            # 用原始量纲：0 → (0 - mean) / std = -mean/std
            j_val = rule["j_val"]
            if hasattr(sy, "mean_") and hasattr(sy, "scale_"):
                zero_scaled = torch.tensor(
                    float(-sy.mean_[j_val] / sy.scale_[j_val]),
                    dtype=torch.float32, device=device
                )
            else:
                zero_scaled = torch.tensor(0.0, device=device)
            viol = F.relu(zero_scaled - mu_raw[:, j_val])
            total = total + viol.mean()

    return w * total / max(len(INEQUALITY_RULES), 1)


# ────────────────────────────────────────────────────────────
# Optuna 目标函数（通用，按 model_id 分支）
# ────────────────────────────────────────────────────────────
def make_objective(model_id, X_train, Y_train, X_val, Y_val, device, sy, logger):
    minfo = MODELS[model_id]
    space = get_optuna_space(model_id)

    def objective(trial):
        # ── 采样超参 ──
        def s(key):
            sp = space[key]
            t = sp["type"]
            if t == "int":
                return trial.suggest_int(key, sp["low"], sp["high"])
            elif t == "float":
                return trial.suggest_float(key, sp["low"], sp["high"], log=sp.get("log", False))
            elif t == "cat":
                return trial.suggest_categorical(key, sp["choices"])

        width   = s("width")
        depth   = s("depth")
        dropout = s("dropout")
        lr      = s("lr")
        wd      = s("wd")
        batch   = s("batch")
        epochs  = s("epochs")
        clip    = s("clip")
        w_data  = s("w_data")

        w_mono = s("w_mono")  if "w_mono" in space else 0.0
        w_ineq = s("w_ineq") if "w_ineq" in space else 0.0
        rho_abs_min = s("rho_abs_min") if "rho_abs_min" in space else 0.25
        mono_topk   = s("mono_topk")   if "mono_topk"   in space else 40

        seed_all(SEED + trial.number)
        model = HeteroMLP(
            in_dim=len(INPUT_COLS), out_dim=len(OUTPUT_COLS),
            width=width, depth=depth, dropout=dropout,
        ).to(device)
        optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=wd)

        # Spearman pairs（仅 data-mono, data-mono-ineq）
        mono_pairs = []
        if minfo["loss_mono_data"]:
            mono_pairs = build_mono_pairs_spearman(
                X_train, Y_train,
                rho_abs_min=rho_abs_min, topk=mono_topk,
            )

        # 数据张量
        Xt  = torch.tensor(sy["sx"].transform(X_train), dtype=torch.float32, device=device)
        Yt  = torch.tensor(sy["sy_"].transform(Y_train), dtype=torch.float32, device=device)
        Xv  = torch.tensor(sy["sx"].transform(X_val),   dtype=torch.float32, device=device)
        Yv  = torch.tensor(sy["sy_"].transform(Y_val),  dtype=torch.float32, device=device)
        N   = len(Xt)

        best_val, patience, patience_max = float("inf"), 0, 25

        for ep in range(epochs):
            model.train()
            perm  = torch.randperm(N, device=device)
            n_bat = max(1, N // batch)
            ep_loss = 0.0
            for i in range(n_bat):
                idx  = perm[i * batch:(i + 1) * batch]
                xb   = Xt[idx]; yb = Yt[idx]
                optimizer.zero_grad()
                mu, logvar = model(xb)

                loss = w_data * gaussian_nll(yb, mu, logvar)

                # data-derived monotone
                if minfo["loss_mono_data"] and mono_pairs and w_mono > 0:
                    loss = loss + loss_level2_monotone_from_mu(
                        model, xb, mono_pairs, w_mono)

                # physics-prior monotone
                if minfo["loss_mono_phy"] and w_mono > 0:
                    loss = loss + loss_phy_monotone(
                        model, xb, PHYSICS_IDX_PAIRS_HIGH, w_mono)

                # inequality
                if minfo["loss_ineq"] and w_ineq > 0:
                    loss = loss + loss_inequality(mu, sy["sy_"], w_ineq, device)

                loss.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(), clip)
                optimizer.step()
                ep_loss += loss.item()

            # 验证
            model.eval()
            with torch.no_grad():
                mu_v, lv_v = model(Xv)
                val_nll = gaussian_nll(Yv, mu_v, lv_v).item()

            trial.report(val_nll, ep)
            if trial.should_prune():
                raise optuna.exceptions.TrialPruned()

            if val_nll < best_val - 1e-6:
                best_val = val_nll; patience = 0
            else:
                patience += 1
                if patience >= patience_max:
                    break

        return best_val

    return objective


# ────────────────────────────────────────────────────────────
# 最终训练（用 best_params 重训）
# ────────────────────────────────────────────────────────────
def final_train(model_id, best_params, X_train, Y_train, X_val, Y_val, device, sy, logger):
    minfo = MODELS[model_id]
    seed_all(SEED)

    width   = int(best_params["width"])
    depth   = int(best_params["depth"])
    dropout = float(best_params.get("dropout", 0.0))
    lr      = float(best_params["lr"])
    wd      = float(best_params.get("wd", 1e-5))
    batch   = int(best_params.get("batch", 64))
    epochs  = int(best_params["epochs"])
    clip    = float(best_params.get("clip", 1.0))
    w_data  = float(best_params.get("w_data", 1.0))
    w_mono  = float(best_params.get("w_mono", 0.0))
    w_ineq  = float(best_params.get("w_ineq", 0.0))
    rho_abs_min = float(best_params.get("rho_abs_min", 0.25))
    mono_topk   = int(best_params.get("mono_topk", 40))

    model = HeteroMLP(
        in_dim=len(INPUT_COLS), out_dim=len(OUTPUT_COLS),
        width=width, depth=depth, dropout=dropout,
    ).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=wd)

    mono_pairs = []
    if minfo["loss_mono_data"]:
        mono_pairs = build_mono_pairs_spearman(
            X_train, Y_train, rho_abs_min=rho_abs_min, topk=mono_topk)
        logger.info(f"  Spearman mono pairs: {len(mono_pairs)}")

    if minfo["loss_mono_phy"]:
        logger.info(f"  Physics prior pairs: {len(PHYSICS_IDX_PAIRS_HIGH)}")

    Xt = torch.tensor(sy["sx"].transform(X_train), dtype=torch.float32, device=device)
    Yt = torch.tensor(sy["sy_"].transform(Y_train), dtype=torch.float32, device=device)
    Xv = torch.tensor(sy["sx"].transform(X_val),   dtype=torch.float32, device=device)
    Yv = torch.tensor(sy["sy_"].transform(Y_val),  dtype=torch.float32, device=device)
    N  = len(Xt)

    best_val, patience, patience_max = float("inf"), 0, 30
    best_state = None
    history = []

    for ep in range(epochs):
        model.train()
        perm  = torch.randperm(N, device=device)
        n_bat = max(1, N // batch)
        ep_loss = 0.0
        for i in range(n_bat):
            idx = perm[i * batch:(i + 1) * batch]
            xb  = Xt[idx]; yb = Yt[idx]
            optimizer.zero_grad()
            mu, logvar = model(xb)
            loss = w_data * gaussian_nll(yb, mu, logvar)
            if minfo["loss_mono_data"] and mono_pairs and w_mono > 0:
                xb_g = xb.detach().requires_grad_(True)
                mu_g, _ = model(xb_g)
                loss = loss + w_mono * loss_level2_monotone_from_mu(mu_g, xb_g, mono_pairs)
            if minfo["loss_mono_phy"] and w_mono > 0:
                loss = loss + loss_phy_monotone(model, xb, PHYSICS_IDX_PAIRS_HIGH, w_mono)
            if minfo["loss_ineq"] and w_ineq > 0:
                loss = loss + loss_inequality(mu, sy["sy_"], w_ineq, device)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), clip)
            optimizer.step()
            ep_loss += loss.item()

        model.eval()
        with torch.no_grad():
            mu_v, lv_v = model(Xv)
            val_nll = gaussian_nll(Yv, mu_v, lv_v).item()

        history.append({"epoch": ep, "train_loss": ep_loss / n_bat, "val_nll": val_nll})

        if val_nll < best_val - 1e-6:
            best_val  = val_nll
            best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}
            patience  = 0
        else:
            patience += 1
            if patience >= patience_max:
                logger.info(f"  Early stop at epoch {ep}")
                break

        if ep % 50 == 0:
            logger.info(f"  ep {ep:4d} | train={ep_loss/n_bat:.4f} | val={val_nll:.4f} | best={best_val:.4f}")

    if best_state:
        model.load_state_dict(best_state)

    return model, best_val, history


# ────────────────────────────────────────────────────────────
# 评估（测试集）
# ────────────────────────────────────────────────────────────
def evaluate_on_test(model, sx, sy_, X_test, Y_test, device):
    from sklearn.metrics import r2_score, mean_squared_error
    model.eval()
    Xt = torch.tensor(sx.transform(X_test), dtype=torch.float32, device=device)
    with torch.no_grad():
        mu_s, logvar_s = model(Xt)
    mu_raw    = sy_.inverse_transform(mu_s.cpu().numpy())
    sigma_raw = np.sqrt(np.exp(logvar_s.cpu().numpy())) * sy_.scale_

    per_output = []
    for j, col in enumerate(OUTPUT_COLS):
        y_true = Y_test[:, j]
        y_pred = mu_raw[:, j]
        rmse   = float(np.sqrt(mean_squared_error(y_true, y_pred)))
        r2     = float(r2_score(y_true, y_pred))
        per_output.append({"output": col, "rmse": rmse, "r2": r2})

    r2_mean   = float(np.mean([r["r2"]   for r in per_output]))
    rmse_mean = float(np.mean([r["rmse"] for r in per_output]))
    Yt_s = torch.tensor(sy_.transform(Y_test), dtype=torch.float32, device=device)
    with torch.no_grad():
        mu_s2, lv_s2 = model(Xt)
        nll = float(gaussian_nll(Yt_s, mu_s2, lv_s2).item())

    return {
        "test_nll":      nll,
        "r2_mean":       r2_mean,
        "rmse_mean":     rmse_mean,
        "per_output":    per_output,
    }, mu_raw, sigma_raw


# ────────────────────────────────────────────────────────────
# 主训练流程（单个 model_id，单次 split）
# ────────────────────────────────────────────────────────────
def train_one(model_id: str, split_type: str, split_seed: int,
              df: pd.DataFrame, logger, force: bool = False) -> dict:
    """
    训练一个模型。
    split_type: "fixed" | "repeat"
    返回：{ckpt_path, scaler_path, metrics, ...}
    """
    minfo = MODELS[model_id]
    art_dir = model_artifacts_dir(model_id)
    mfst_dir = model_manifests_dir(model_id)
    ensure_dir(art_dir); ensure_dir(mfst_dir)

    suffix = "fixed" if split_type == "fixed" else f"repeat_{split_seed}"
    ckpt_path   = os.path.join(art_dir, f"checkpoint_{model_id}_{suffix}.pt")
    scaler_path = os.path.join(art_dir, f"scalers_{model_id}_{suffix}.pkl")

    logger.info(f"\n{'='*60}")
    logger.info(f"  Model: {model_id}  |  Split: {suffix}")
    logger.info(f"{'='*60}")

    # ── 旧目录 checkpoint 复用（仅 fixed split）──────────
    if split_type == "fixed" and model_id in _OLD_ARTIFACTS and not force:
        old = _OLD_ARTIFACTS[model_id]
        if os.path.exists(old["ckpt"]) and not os.path.exists(ckpt_path):
            logger.info(f"  复用旧 checkpoint: {old['ckpt']}")
            shutil.copy2(old["ckpt"],   ckpt_path)
            shutil.copy2(old["scaler"], scaler_path)
            # 读取旧 metrics 写入新目录
            if os.path.exists(old["metrics"]):
                with open(old["metrics"]) as f:
                    old_metrics = json.load(f)
                shutil.copy2(old["metrics"],
                             os.path.join(art_dir, f"metrics_{model_id}_fixed.json"))
            logger.info(f"  → checkpoint 已复制到新目录")

    # ── 检查是否已存在，跳过训练 ──────────────────────
    if os.path.exists(ckpt_path) and not force:
        logger.info(f"  checkpoint 已存在，跳过训练: {ckpt_path}")
        return {"ckpt_path": ckpt_path, "scaler_path": scaler_path, "skipped": True}

    # ── 准备数据 ──────────────────────────────────────
    if split_type == "fixed":
        X_train, Y_train, X_val, Y_val, X_test, Y_test, s_seed = load_fixed_split(df, logger)
    else:
        X_train, Y_train, X_val, Y_val, X_test, Y_test, s_seed = make_repeat_split(df, split_seed)

    # ── 标准化 ────────────────────────────────────────
    sx  = StandardScaler().fit(X_train)
    sy_ = StandardScaler().fit(Y_train)
    scalers_obj = {"sx": sx, "sy": sy_, "sy_": sy_}

    device = get_device()
    trials = TRIALS_MAIN if model_id in ("baseline", "data-mono") else TRIALS_ABLATION

    # ── Optuna ────────────────────────────────────────
    logger.info(f"  Optuna ({trials} trials)...")
    t0 = time.time()

    sampler = optuna.samplers.TPESampler(seed=SEED)
    pruner  = optuna.pruners.MedianPruner(n_startup_trials=10, n_warmup_steps=40)
    study   = optuna.create_study(
        direction="minimize",
        sampler=sampler,
        pruner=pruner,
    )
    optuna.logging.set_verbosity(optuna.logging.WARNING)

    obj = make_objective(model_id, X_train, Y_train, X_val, Y_val, device, scalers_obj, logger)
    study.optimize(obj, n_trials=trials, show_progress_bar=False)

    best_params = study.best_trial.params
    best_val    = study.best_value
    logger.info(f"  Best val NLL: {best_val:.4f}")
    logger.info(f"  Best params: {best_params}")

    # ── 最终训练 ──────────────────────────────────────
    logger.info(f"  最终训练 (best params)...")
    model, final_val, history = final_train(
        model_id, best_params, X_train, Y_train, X_val, Y_val,
        device, scalers_obj, logger
    )
    t_total = time.time() - t0
    logger.info(f"  总训练时间: {t_total:.0f}s")

    # ── 测试评估 ──────────────────────────────────────
    metrics, mu_test, sigma_test = evaluate_on_test(model, sx, sy_, X_test, Y_test, device)
    logger.info(f"  Test NLL: {metrics['test_nll']:.4f}  R2: {metrics['r2_mean']:.4f}  RMSE: {metrics['rmse_mean']:.4f}")

    # ── 保存 ──────────────────────────────────────────
    # checkpoint
    ckpt_obj = {
        "model_state_dict": model.state_dict(),
        "best_params":      best_params,
        "best_val_nll":     final_val,
        "model_id":         model_id,
        "split_type":       suffix,
        "n_outputs":        len(OUTPUT_COLS),
        "n_inputs":         len(INPUT_COLS),
    }
    torch.save(ckpt_obj, ckpt_path)

    # scalers
    with open(scaler_path, "wb") as f:
        pickle.dump({"sx": sx, "sy": sy_}, f)

    # metrics JSON
    metrics_path = os.path.join(art_dir, f"metrics_{model_id}_{suffix}.json")
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)

    # training history
    hist_path = os.path.join(art_dir, f"training_history_{model_id}_{suffix}.json")
    with open(hist_path, "w") as f:
        json.dump(history, f, indent=2)

    # test predictions
    pred_path = os.path.join(model_fixed_eval_dir(model_id),
                              f"test_predictions_{model_id}_{suffix}.json")
    ensure_dir(os.path.dirname(pred_path))
    pred_obj = {
        "mu_test":    mu_test.tolist(),
        "sigma_test": sigma_test.tolist(),
        "Y_test":     Y_test.tolist(),
        "output_cols": OUTPUT_COLS,
    }
    with open(pred_path, "w") as f:
        json.dump(pred_obj, f)

    # manifest
    losses = []
    if minfo["loss_nll"]:       losses.append("NLL")
    if minfo["loss_mono_data"]: losses.append(f"Mono-Data(Spearman, topk={best_params.get('mono_topk',40)})")
    if minfo["loss_mono_phy"]:  losses.append(f"Mono-Phy(N={len(PHYSICS_IDX_PAIRS_HIGH)} pairs)")
    if minfo["loss_ineq"]:      losses.append(f"Ineq(N={len(INEQUALITY_RULES)} rules)")

    mfst = make_training_manifest(
        model_id=model_id,
        full_name=minfo["full_name"],
        loss_components=losses,
        n_outputs=len(OUTPUT_COLS),
        split_type=suffix,
        split_seed=s_seed,
        n_train=len(X_train),
        n_val=len(X_val),
        n_test=len(X_test),
        best_params=best_params,
        best_val_nll=float(final_val),
        training_time_sec=t_total,
        ckpt_path=ckpt_path,
        scaler_path=scaler_path,
        split_source=FIXED_SPLIT_DIR if split_type == "fixed" else "dynamic",
        optuna_trials=trials,
        source_script=__file__,
        extra={
            "test_metrics":   metrics,
            "optuna_best_val": float(best_val),
        },
    )
    mfst_path = os.path.join(mfst_dir, f"training_manifest_{model_id}_{suffix}.json")
    write_manifest(mfst_path, mfst)

    logger.info(f"  [OK] {model_id} ({suffix}) 完成")
    return {
        "ckpt_path":    ckpt_path,
        "scaler_path":  scaler_path,
        "metrics":      metrics,
        "skipped":      False,
    }


# ────────────────────────────────────────────────────────────
# 入口
# ────────────────────────────────────────────────────────────
# ★ 直接修改这里来手动运行单个模型（run_0404.py 会通过环境变量覆盖）
MODEL_ID_OVERRIDE  = "baseline"   # 修改这里
SPLIT_TYPE_OVERRIDE = "fixed"     # "fixed" or "repeat"
FORCE_OVERRIDE      = False

if __name__ == "__main__":
    model_id   = os.environ.get("MODEL_ID",       MODEL_ID_OVERRIDE)
    split_type = os.environ.get("SPLIT_TYPE",     SPLIT_TYPE_OVERRIDE)
    force      = os.environ.get("FORCE_RETRAIN", "0") == "1" or FORCE_OVERRIDE

    if model_id not in MODELS:
        print(f"[ERROR] Unknown model_id: {model_id!r}")
        print(f"  Available: {list(MODELS)}")
        sys.exit(1)

    log_dir = model_logs_dir(model_id)
    logger  = setup_logger(model_id, log_dir)

    logger.info(f"MODEL_ID   = {model_id}")
    logger.info(f"SPLIT_TYPE = {split_type}")
    logger.info(f"FORCE      = {force}")

    logger.info("Loading dataset...")
    df = load_full_dataset(logger)

    if split_type == "fixed":
        train_one(model_id, "fixed", SEED, df, logger, force=force)
    elif split_type == "repeat":
        for seed in REPEAT_SEEDS:
            train_one(model_id, "repeat", seed, df, logger, force=force)
    elif split_type == "both":
        train_one(model_id, "fixed", SEED, df, logger, force=force)
        for seed in REPEAT_SEEDS:
            train_one(model_id, "repeat", seed, df, logger, force=force)
    else:
        logger.error(f"Unknown SPLIT_TYPE: {split_type!r}")
        sys.exit(1)

    logger.info("\n[DONE] 训练完成")
