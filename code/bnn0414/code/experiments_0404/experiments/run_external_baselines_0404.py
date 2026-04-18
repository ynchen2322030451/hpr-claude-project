# run_external_baselines_0404.py
# ============================================================
# BNN 0414 — External Baselines: MC-Dropout + Deep Ensemble
# NCS revision P0-#1
#
# SERVER ONLY — requires HPR_ENV=server + pytorch-env conda
#
# 目的：
#   NCS 审稿人的第一反应："你 4 个模型都是 BNN 变体，没有跨族对照"。
#   这里提供两个标准的概率代理做 reference：
#     (a) MC-Dropout MLP（Gal & Ghahramani 2016）
#     (b) 5-member deep ensemble（Lakshminarayanan et al. 2017）
#
# 设计原则：
#   - 架构和容量尽量对齐 BayesianMLP（width/depth/双头 mu+logvar）
#   - 用 BNN canonical 的 best_params 作为起点（width/depth/lr/batch/epochs）
#   - 数据一致：同 FIXED_SPLIT train/val/test
#   - 评估一致：mc_predict-like 接口 → 同一 test_predictions_fixed.json schema
#   - NO optuna：直接用 canonical best_params（只去掉 BNN 特有参数）
#
# 调用：
#   MODEL_ID=mc-dropout  python run_external_baselines_0404.py
#   MODEL_ID=deep-ensemble python run_external_baselines_0404.py
#   MODEL_ID=all         python run_external_baselines_0404.py  # 两个都跑
#
# 输出 (code/models/<model_id>/)：
#   artifacts/ckpt_<model>_fixed.pt, scalers_<model>_fixed.pkl
#   fixed_eval/test_predictions_fixed.json (同 BNN schema: mu, sigma, y_true,
#              epistemic_var, aleatoric_var)
#   manifests/training_manifest_<model>_fixed.json
# ============================================================

import os, sys, json, time, pickle, logging, math
from datetime import datetime

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
from sklearn.preprocessing import StandardScaler

# ── sys.path ────────────────────────────────────────────────
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_CODE_ROOT = _SCRIPT_DIR
while _CODE_ROOT and os.path.basename(_CODE_ROOT) != 'code':
    _CODE_ROOT = os.path.dirname(_CODE_ROOT)
_BNN_CONFIG_DIR = os.path.join(_CODE_ROOT, 'experiments_0404', 'config')
_TRAINING_DIR = os.path.join(_CODE_ROOT, 'experiments_0404', 'training')
_CODE_TOP = os.path.dirname(os.path.dirname(_CODE_ROOT))
_ROOT_0310 = os.path.join(_CODE_TOP, '0310')
for _p in (_SCRIPT_DIR, _CODE_ROOT, _BNN_CONFIG_DIR, _TRAINING_DIR, _ROOT_0310,
           os.environ.get('HPR_LEGACY_DIR', '')):
    if _p and os.path.isdir(_p) and _p not in sys.path:
        if any(seg in _p for seg in ('/0310', 'hpr_legacy')):
            sys.path.append(_p)
        else:
            sys.path.insert(0, _p)

from experiment_config_0404 import (
    INPUT_COLS, OUTPUT_COLS, SEED, DEVICE, FIXED_SPLIT_DIR,
    BNN_N_MC_EVAL, ensure_dir, get_csv_path,
)
from manifest_utils_0404 import write_manifest, make_experiment_manifest
from bnn_model import seed_all, get_device

import run_train_0404 as rt

logging.basicConfig(level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger(__name__)

# ============================================================
# 配置
# ============================================================
ENSEMBLE_SIZE = int(os.environ.get("ENSEMBLE_SIZE", 5))
MC_DROPOUT_N_MC = int(os.environ.get("MC_DROPOUT_N_MC", BNN_N_MC_EVAL))
DROPOUT_RATE = float(os.environ.get("DROPOUT_RATE", 0.1))

EXTERNAL_MODELS = {
    "mc-dropout": {
        "full_name": "MC-Dropout heteroscedastic MLP (Gal & Ghahramani 2016)",
        "type": "mc_dropout",
    },
    "deep-ensemble": {
        "full_name": f"{ENSEMBLE_SIZE}-member Deep Ensemble (Lakshminarayanan 2017)",
        "type": "ensemble",
    },
}


# ============================================================
# Model: HeteroMLP with Dropout (for MC-Dropout)
# ============================================================
def _init_weights(m):
    if isinstance(m, nn.Linear):
        nn.init.xavier_normal_(m.weight)
        if m.bias is not None:
            nn.init.zeros_(m.bias)


class HeteroMLPDropout(nn.Module):
    def __init__(self, in_dim, out_dim, width, depth, dropout=0.1):
        super().__init__()
        layers = []
        d = in_dim
        for _ in range(depth):
            layers.append(nn.Linear(d, width))
            layers.append(nn.SiLU())
            layers.append(nn.Dropout(dropout))
            d = width
        self.backbone = nn.Sequential(*layers)
        self.mu_head = nn.Linear(d, out_dim)
        self.logvar_head = nn.Linear(d, out_dim)
        self.apply(_init_weights)
        nn.init.constant_(self.logvar_head.bias, -2.0)

    def forward(self, x):
        z = self.backbone(x)
        mu = self.mu_head(z)
        logvar = self.logvar_head(z).clamp(-20, 5)
        return mu, logvar


# ============================================================
# Model: HeteroMLP (no dropout, for ensemble members)
# ============================================================
class HeteroMLP(nn.Module):
    def __init__(self, in_dim, out_dim, width, depth):
        super().__init__()
        layers = []
        d = in_dim
        for _ in range(depth):
            layers.append(nn.Linear(d, width))
            layers.append(nn.SiLU())
            d = width
        self.backbone = nn.Sequential(*layers)
        self.mu_head = nn.Linear(d, out_dim)
        self.logvar_head = nn.Linear(d, out_dim)
        self.apply(_init_weights)
        nn.init.constant_(self.logvar_head.bias, -2.0)

    def forward(self, x):
        z = self.backbone(x)
        mu = self.mu_head(z)
        logvar = self.logvar_head(z).clamp(-20, 5)
        return mu, logvar


# ============================================================
# 通用训练循环（Gaussian NLL, early stopping）
# ============================================================
def gaussian_nll_loss(y, mu, logvar):
    logvar = logvar.clamp(-20, 5)
    var = torch.exp(logvar) + 1e-6
    loss = 0.5 * torch.mean((y - mu)**2 / var + logvar)
    if torch.isnan(loss) or torch.isinf(loss):
        loss = 0.5 * torch.mean((y - mu)**2)
    return loss


MSE_WARMUP_EPOCHS = int(os.environ.get("MSE_WARMUP_EPOCHS", 30))


def train_single_model(model, X_train, Y_train, X_val, Y_val, sx, sy,
                        device, lr, batch, epochs, clip, logger_fn,
                        enable_dropout_train=False):
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    Xt = torch.tensor(sx.transform(X_train), dtype=torch.float32, device=device)
    Yt = torch.tensor(sy.transform(Y_train), dtype=torch.float32, device=device)
    Xv = torch.tensor(sx.transform(X_val), dtype=torch.float32, device=device)
    Yv = torch.tensor(sy.transform(Y_val), dtype=torch.float32, device=device)
    N = len(Xt)

    best_val, patience, patience_max = float("inf"), 0, 30
    best_state = None
    history = []

    for ep in range(epochs):
        model.train()
        perm = torch.randperm(N, device=device)
        n_bat = max(1, N // batch)
        ep_loss = 0.0
        use_nll = (ep >= MSE_WARMUP_EPOCHS)
        for i in range(n_bat):
            idx = perm[i * batch:(i + 1) * batch]
            xb, yb = Xt[idx], Yt[idx]
            optimizer.zero_grad()
            mu, logvar = model(xb)
            if use_nll:
                loss = gaussian_nll_loss(yb, mu, logvar)
            else:
                loss = F.mse_loss(mu, yb)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), clip)
            optimizer.step()
            ep_loss += loss.item()

        model.eval()
        with torch.no_grad():
            mu_v, logvar_v = model(Xv)
        mu_v_np = mu_v.cpu().numpy() * sy.scale_ + sy.mean_
        val_rmse = float(np.sqrt(np.mean((mu_v_np - Y_val) ** 2)))
        history.append({"epoch": ep, "train_loss": ep_loss / n_bat, "val_rmse": val_rmse})

        if val_rmse < best_val - 1e-6:
            best_val = val_rmse
            best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}
            patience = 0
        else:
            patience += 1
            if patience >= patience_max:
                logger_fn(f"  Early stop at epoch {ep}")
                break

        if ep % 50 == 0:
            logger_fn(f"  ep {ep:4d} | train={ep_loss/n_bat:.4f} | val_rmse={val_rmse:.4f}")

    if best_state:
        model.load_state_dict(best_state)
    return model, best_val, history


# ============================================================
# MC-Dropout 预测
# ============================================================
def mc_predict_dropout(model, X_np, sx, sy, device, n_mc=50):
    model.train()  # keep dropout active
    X_scaled = sx.transform(X_np)
    x_t = torch.tensor(X_scaled, dtype=torch.float32, device=device)

    mus_list, logvars_list = [], []
    with torch.no_grad():
        for _ in range(n_mc):
            mu, logvar = model(x_t)
            mus_list.append(mu.cpu().numpy())
            logvars_list.append(logvar.cpu().numpy())

    mus = np.stack(mus_list)       # (n_mc, N, D)
    logvars = np.stack(logvars_list)

    sy_mean = sy.mean_[np.newaxis, :]
    sy_scale = sy.scale_[np.newaxis, :]
    mus_orig = mus * sy_scale + sy_mean
    vars_scaled = np.exp(logvars)
    vars_orig = vars_scaled * (sy_scale ** 2)

    mu_mean = mus_orig.mean(axis=0)
    epistemic_var = mus_orig.var(axis=0)
    aleatoric_var = vars_orig.mean(axis=0)
    total_var = epistemic_var + aleatoric_var
    mu_std = np.sqrt(epistemic_var)

    model.eval()
    return mu_mean, mu_std, aleatoric_var, epistemic_var, total_var


# ============================================================
# Deep Ensemble 预测
# ============================================================
def ensemble_predict(models, X_np, sx, sy, device):
    X_scaled = sx.transform(X_np)
    x_t = torch.tensor(X_scaled, dtype=torch.float32, device=device)

    mus_list, logvars_list = [], []
    for m in models:
        m.eval()
        with torch.no_grad():
            mu, logvar = m(x_t)
            mus_list.append(mu.cpu().numpy())
            logvars_list.append(logvar.cpu().numpy())

    mus = np.stack(mus_list)       # (M, N, D)
    logvars = np.stack(logvars_list)

    sy_mean = sy.mean_[np.newaxis, :]
    sy_scale = sy.scale_[np.newaxis, :]
    mus_orig = mus * sy_scale + sy_mean
    vars_scaled = np.exp(logvars)
    vars_orig = vars_scaled * (sy_scale ** 2)

    mu_mean = mus_orig.mean(axis=0)
    epistemic_var = mus_orig.var(axis=0)
    aleatoric_var = vars_orig.mean(axis=0)
    total_var = epistemic_var + aleatoric_var
    mu_std = np.sqrt(epistemic_var)

    return mu_mean, mu_std, aleatoric_var, epistemic_var, total_var


# ============================================================
# 评估 + 保存
# ============================================================
def evaluate_and_save(mu_mean, mu_std, aleatoric_var, epistemic_var, total_var,
                      Y_test, model_id, out_dir):
    from sklearn.metrics import r2_score
    sigma = np.sqrt(total_var)
    rmse = float(np.sqrt(np.mean((mu_mean - Y_test) ** 2)))
    r2_per = [float(r2_score(Y_test[:, j], mu_mean[:, j])) for j in range(Y_test.shape[1])]
    var_t = np.maximum(total_var, 1e-12)
    nll = 0.5 * ((Y_test - mu_mean) ** 2 / var_t + np.log(2 * np.pi * var_t))
    nll_mean = float(nll.mean())

    metrics = {
        "rmse_mean": rmse,
        "r2_mean": float(np.mean(r2_per)),
        "r2_per_output": r2_per,
        "test_nll": nll_mean,
        "output_cols": OUTPUT_COLS,
    }

    # test_predictions_fixed.json — 与 BNN schema 完全一致
    pred_dir = ensure_dir(os.path.join(out_dir, "fixed_eval"))
    pred = {
        "mu": mu_mean.tolist(),
        "sigma": sigma.tolist(),
        "y_true": Y_test.tolist(),
        "epistemic_var": epistemic_var.tolist(),
        "aleatoric_var": aleatoric_var.tolist(),
        "output_cols": OUTPUT_COLS,
        "n_mc_eval": MC_DROPOUT_N_MC,
    }
    with open(os.path.join(pred_dir, "test_predictions_fixed.json"), "w") as f:
        json.dump(pred, f)

    metrics_path = os.path.join(pred_dir, "metrics_fixed.json")
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)

    logger.info(f"  [{model_id}] RMSE={rmse:.4f}, R2={np.mean(r2_per):.4f}, NLL={nll_mean:.4f}")
    return metrics


# ============================================================
# 加载 BNN canonical best_params
# ============================================================
def _load_bnn_hparams(ref_model="bnn-phy-mono"):
    mf_path = os.path.join(
        _CODE_ROOT, "models", ref_model, "manifests",
        f"training_manifest_{ref_model}_fixed.json",
    )
    if not os.path.exists(mf_path):
        raise FileNotFoundError(f"Reference training manifest not found: {mf_path}")
    with open(mf_path) as f:
        return json.load(f)["best_params"]


# ============================================================
# Main: MC-Dropout
# ============================================================
def run_mc_dropout(X_tr, Y_tr, X_val, Y_val, X_test, Y_test, device):
    model_id = "mc-dropout"
    logger.info(f"[{model_id}] Training MC-Dropout MLP")
    bp = _load_bnn_hparams()
    width = int(bp["width"])
    depth = int(bp["depth"])
    lr = min(float(bp["lr"]), 5e-4)
    batch = int(bp.get("batch", 64))
    epochs = int(bp["epochs"])
    clip = float(bp.get("clip", 1.0))

    out_dir = ensure_dir(os.path.join(_CODE_ROOT, "models", model_id))
    art_dir = ensure_dir(os.path.join(out_dir, "artifacts"))

    sx = StandardScaler().fit(X_tr)
    sy = StandardScaler().fit(Y_tr)

    seed_all(SEED)
    model = HeteroMLPDropout(len(INPUT_COLS), len(OUTPUT_COLS),
                              width, depth, dropout=DROPOUT_RATE).to(device)
    t0 = time.time()
    model, best_val, history = train_single_model(
        model, X_tr, Y_tr, X_val, Y_val, sx, sy,
        device, lr, batch, epochs, clip, logger.info,
        enable_dropout_train=True,
    )
    t_train = time.time() - t0
    logger.info(f"  [{model_id}] Training done in {t_train:.0f}s, best_val_rmse={best_val:.4f}")

    # save checkpoint
    ckpt_path = os.path.join(art_dir, f"ckpt_{model_id}_fixed.pt")
    torch.save({
        "model_state_dict": model.state_dict(),
        "model_id": model_id,
        "model_class": "HeteroMLPDropout",
        "width": width, "depth": depth, "dropout": DROPOUT_RATE,
        "n_inputs": len(INPUT_COLS), "n_outputs": len(OUTPUT_COLS),
    }, ckpt_path)
    scaler_path = os.path.join(art_dir, f"scalers_{model_id}_fixed.pkl")
    with open(scaler_path, "wb") as f:
        pickle.dump({"sx": sx, "sy": sy}, f)

    # MC predict
    mu_mean, mu_std, aleatoric_var, epistemic_var, total_var = mc_predict_dropout(
        model, X_test, sx, sy, device, n_mc=MC_DROPOUT_N_MC)
    metrics = evaluate_and_save(mu_mean, mu_std, aleatoric_var, epistemic_var,
                                total_var, Y_test, model_id, out_dir)

    # manifest
    mf = make_experiment_manifest(
        experiment_id="external_baseline_training",
        model_id=model_id,
        input_source=FIXED_SPLIT_DIR,
        outputs_saved=[ckpt_path, scaler_path],
        key_results={"test_metrics": metrics, "training_time_sec": t_train,
                     "best_val_rmse": best_val, "dropout_rate": DROPOUT_RATE,
                     "n_mc_eval": MC_DROPOUT_N_MC},
        source_script=os.path.abspath(__file__),
        extra={"hparams_from": "bnn-phy-mono canonical best_params",
               "width": width, "depth": depth},
    )
    write_manifest(os.path.join(ensure_dir(os.path.join(out_dir, "manifests")),
                                f"training_manifest_{model_id}_fixed.json"), mf)

    hist_path = os.path.join(art_dir, f"training_history_{model_id}_fixed.json")
    with open(hist_path, "w") as f:
        json.dump(history, f, indent=2)

    return metrics


# ============================================================
# Main: Deep Ensemble
# ============================================================
def run_deep_ensemble(X_tr, Y_tr, X_val, Y_val, X_test, Y_test, device):
    model_id = "deep-ensemble"
    logger.info(f"[{model_id}] Training {ENSEMBLE_SIZE}-member ensemble")
    bp = _load_bnn_hparams()
    width = int(bp["width"])
    depth = int(bp["depth"])
    lr = min(float(bp["lr"]), 5e-4)
    batch = int(bp.get("batch", 64))
    epochs = int(bp["epochs"])
    clip = float(bp.get("clip", 1.0))

    out_dir = ensure_dir(os.path.join(_CODE_ROOT, "models", model_id))
    art_dir = ensure_dir(os.path.join(out_dir, "artifacts"))

    sx = StandardScaler().fit(X_tr)
    sy = StandardScaler().fit(Y_tr)

    models = []
    all_histories = []
    t0_total = time.time()
    for k in range(ENSEMBLE_SIZE):
        seed_k = SEED + k * 137
        seed_all(seed_k)
        logger.info(f"  [{model_id}] member {k+1}/{ENSEMBLE_SIZE} seed={seed_k}")
        m = HeteroMLP(len(INPUT_COLS), len(OUTPUT_COLS), width, depth).to(device)
        m, best_val, hist = train_single_model(
            m, X_tr, Y_tr, X_val, Y_val, sx, sy,
            device, lr, batch, epochs, clip, logger.info,
        )
        models.append(m)
        all_histories.append(hist)
        logger.info(f"    member {k+1} best_val_rmse={best_val:.4f}")

        # save individual member
        torch.save({
            "model_state_dict": m.state_dict(),
            "model_id": f"{model_id}_member_{k}",
            "model_class": "HeteroMLP",
            "width": width, "depth": depth, "member_seed": seed_k,
            "n_inputs": len(INPUT_COLS), "n_outputs": len(OUTPUT_COLS),
        }, os.path.join(art_dir, f"ckpt_{model_id}_member_{k}_fixed.pt"))

    t_total = time.time() - t0_total
    logger.info(f"  [{model_id}] All {ENSEMBLE_SIZE} members trained in {t_total:.0f}s")

    scaler_path = os.path.join(art_dir, f"scalers_{model_id}_fixed.pkl")
    with open(scaler_path, "wb") as f:
        pickle.dump({"sx": sx, "sy": sy}, f)

    # ensemble predict
    mu_mean, mu_std, aleatoric_var, epistemic_var, total_var = ensemble_predict(
        models, X_test, sx, sy, device)
    metrics = evaluate_and_save(mu_mean, mu_std, aleatoric_var, epistemic_var,
                                total_var, Y_test, model_id, out_dir)

    mf = make_experiment_manifest(
        experiment_id="external_baseline_training",
        model_id=model_id,
        input_source=FIXED_SPLIT_DIR,
        outputs_saved=[art_dir, scaler_path],
        key_results={"test_metrics": metrics, "training_time_sec": t_total,
                     "ensemble_size": ENSEMBLE_SIZE},
        source_script=os.path.abspath(__file__),
        extra={"hparams_from": "bnn-phy-mono canonical best_params",
               "width": width, "depth": depth, "ensemble_size": ENSEMBLE_SIZE},
    )
    write_manifest(os.path.join(ensure_dir(os.path.join(out_dir, "manifests")),
                                f"training_manifest_{model_id}_fixed.json"), mf)

    for k, hist in enumerate(all_histories):
        hp = os.path.join(art_dir, f"training_history_{model_id}_member_{k}_fixed.json")
        with open(hp, "w") as f:
            json.dump(hist, f, indent=2)

    return metrics


# ============================================================
# 入口
# ============================================================
if __name__ == "__main__":
    model_id_env = os.environ.get("MODEL_ID", "all")
    if model_id_env == "all":
        run_ids = list(EXTERNAL_MODELS.keys())
    else:
        run_ids = [model_id_env]

    device = get_device(DEVICE)
    seed_all(SEED)

    # 加载数据 — 直接从 fixed_split CSVs，避免 dataset_v3.csv 的 NaN 行
    dfs = {}
    for k in ("train", "val", "test"):
        p = os.path.join(FIXED_SPLIT_DIR, f"{k}.csv")
        if not os.path.exists(p):
            raise FileNotFoundError(f"Missing fixed_split/{k}.csv: {p}")
        dfs[k] = pd.read_csv(p)
    X_tr = dfs["train"][INPUT_COLS].values.astype(np.float64)
    Y_tr = dfs["train"][OUTPUT_COLS].values.astype(np.float64)
    X_val = dfs["val"][INPUT_COLS].values.astype(np.float64)
    Y_val = dfs["val"][OUTPUT_COLS].values.astype(np.float64)
    X_test = dfs["test"][INPUT_COLS].values.astype(np.float64)
    Y_test = dfs["test"][OUTPUT_COLS].values.astype(np.float64)
    assert np.isnan(Y_tr).sum() == 0, f"NaN in Y_tr: {np.isnan(Y_tr).sum()}"
    logger.info(f"Data: train={len(X_tr)}, val={len(X_val)}, test={len(X_test)}")

    results = {}
    for rid in run_ids:
        if rid not in EXTERNAL_MODELS:
            logger.error(f"Unknown MODEL_ID: {rid}")
            continue
        logger.info("=" * 60)
        logger.info(f"EXTERNAL BASELINE — {rid}")
        logger.info("=" * 60)
        if rid == "mc-dropout":
            results[rid] = run_mc_dropout(X_tr, Y_tr, X_val, Y_val, X_test, Y_test, device)
        elif rid == "deep-ensemble":
            results[rid] = run_deep_ensemble(X_tr, Y_tr, X_val, Y_val, X_test, Y_test, device)

    if results:
        summary_path = os.path.join(_CODE_ROOT, "models", "external_baselines_summary.json")
        with open(summary_path, "w") as f:
            json.dump(results, f, indent=2)
        logger.info(f"Summary -> {summary_path}")
    logger.info("EXTERNAL BASELINES DONE")
