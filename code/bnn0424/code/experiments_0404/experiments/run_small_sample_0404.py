# run_small_sample_0404.py
# ============================================================
# Phase 2.4: Small-sample regime test
#
# Retrain baseline, phy-mono, and mf-hybrid with 20%, 40%, 60% of
# training data to test sample-efficiency advantage.
#
# Usage:
#   MODEL_ID=bnn-baseline  FRAC=0.2 python run_small_sample_0404.py
#   MODEL_ID=bnn-phy-mono  FRAC=0.4 python run_small_sample_0404.py
#   MODEL_ID=bnn-mf-hybrid FRAC=0.4 python run_small_sample_0404.py
#
# Output:
#   <EXPR_ROOT>/experiments/small_sample/<model_id>/frac_<frac>/
#     metrics.json, checkpoint.pt, scalers.pkl
# ============================================================

import os, sys, json, pickle, time, logging
import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F
import optuna
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score, mean_squared_error

os.environ.setdefault("PYTHONUNBUFFERED", "1")

_THIS = os.path.dirname(os.path.abspath(__file__))
_EXPR_DIR = os.path.dirname(_THIS)
sys.path.insert(0, _EXPR_DIR)
from _path_setup import setup_paths
setup_paths()

from experiment_config_0404 import (
    INPUT_COLS, OUTPUT_COLS, SEED,
    BNN_N_MC_EVAL, FIXED_SPLIT_DIR,
    EXPR_ROOT_0404, ensure_dir, get_csv_path, DEVICE,
    OUT1, OUT2,
)
from model_registry_0404 import MODELS, PHYSICS_IDX_PAIRS_HIGH
from bnn_model import BayesianMLP, gaussian_nll, seed_all, mc_predict

logging.basicConfig(level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger(__name__)


def load_fixed_split_subsample(df, frac, seed=SEED):
    """Load fixed split, subsample training data to `frac` fraction."""
    meta_path = os.path.join(FIXED_SPLIT_DIR, "split_meta.json")
    with open(meta_path) as f:
        meta = json.load(f)

    idx_train = pd.read_csv(os.path.join(FIXED_SPLIT_DIR, "train_indices.csv")).squeeze().tolist()
    idx_val   = pd.read_csv(os.path.join(FIXED_SPLIT_DIR, "val_indices.csv")).squeeze().tolist()
    idx_test  = pd.read_csv(os.path.join(FIXED_SPLIT_DIR, "test_indices.csv")).squeeze().tolist()

    X = df[INPUT_COLS].values.astype(np.float64)
    Y = df[OUTPUT_COLS].values.astype(np.float64)

    X_train_full, Y_train_full = X[idx_train], Y[idx_train]

    # Subsample training data
    rng = np.random.RandomState(seed)
    n_full = len(X_train_full)
    n_sub = max(10, int(n_full * frac))
    sub_idx = rng.choice(n_full, size=n_sub, replace=False)
    sub_idx.sort()

    logger.info(f"  Subsample: {n_sub}/{n_full} training samples (frac={frac})")
    return (X_train_full[sub_idx], Y_train_full[sub_idx],
            X[idx_val], Y[idx_val],
            X[idx_test], Y[idx_test])


def loss_phy_monotone(model, X_batch_t, phy_pairs, w):
    """Physics-prior monotonicity loss (gradient-based penalty)."""
    if not phy_pairs or w == 0.0:
        return torch.tensor(0.0, device=X_batch_t.device)
    X_batch_t = X_batch_t.detach().requires_grad_(True)
    mu, _ = model(X_batch_t, sample=False)
    total = torch.tensor(0.0, device=X_batch_t.device)
    for (inp_idx, out_idx, sign) in phy_pairs:
        grad_out = torch.zeros_like(mu)
        grad_out[:, out_idx] = 1.0
        grads = torch.autograd.grad(
            mu, X_batch_t, grad_outputs=grad_out,
            retain_graph=True, create_graph=True,
        )[0]
        g = grads[:, inp_idx]
        violation = F.relu(-sign * g)
        total = total + violation.mean()
    return w * total / max(len(phy_pairs), 1)


def train_bnn_simple(model_id, X_train, Y_train, X_val, Y_val, device, n_trials=20):
    """Simplified BNN training with Optuna for small-sample experiments."""
    minfo = MODELS[model_id]
    homoscedastic = minfo.get("homoscedastic", False)

    sx = StandardScaler().fit(X_train)
    sy = StandardScaler().fit(Y_train)

    Xt = torch.tensor(sx.transform(X_train), dtype=torch.float32, device=device)
    Yt = torch.tensor(sy.transform(Y_train), dtype=torch.float32, device=device)
    Xv = torch.tensor(sx.transform(X_val), dtype=torch.float32, device=device)

    in_dim = Xt.shape[1]
    out_dim = Yt.shape[1]

    use_mono = minfo.get("loss_mono_phy", False)
    phy_pairs = PHYSICS_IDX_PAIRS_HIGH if use_mono else []

    def objective(trial):
        width = trial.suggest_int("width", 64, 256)
        depth = trial.suggest_int("depth", 2, 4)
        lr = trial.suggest_float("lr", 1e-4, 1e-3, log=True)
        batch = trial.suggest_categorical("batch", [32, 64, 128])
        epochs = trial.suggest_int("epochs", 100, 300)
        w_mono = trial.suggest_float("w_mono", 1e-3, 10.0, log=True) if use_mono else 0.0

        model = BayesianMLP(in_dim=in_dim, out_dim=out_dim,
                            width=width, depth=depth, prior_sigma=1.0,
                            homoscedastic=homoscedastic).to(device)
        opt = torch.optim.Adam(model.parameters(), lr=lr)
        N = len(Xt)
        best_val = float("inf")
        patience, patience_max = 0, 20

        for ep in range(epochs):
            model.train()
            perm = torch.randperm(N, device=device)
            n_bat = max(1, N // batch)
            for i in range(n_bat):
                idx = perm[i*batch:(i+1)*batch]
                mu, logvar = model(Xt[idx], sample=True)
                kl = model.kl_divergence()
                loss = gaussian_nll(Yt[idx], mu, logvar) + 1e-3 * kl / N
                if use_mono:
                    loss = loss + loss_phy_monotone(model, Xt[idx], phy_pairs, w_mono)
                opt.zero_grad(); loss.backward(); opt.step()

            model.eval()
            with torch.no_grad():
                mu_v, _ = model(Xv, sample=False)
            mu_v_np = mu_v.cpu().numpy() * sy.scale_ + sy.mean_
            val_rmse = float(np.sqrt(np.mean((mu_v_np - Y_val) ** 2)))

            if val_rmse < best_val - 1e-6:
                best_val = val_rmse
                patience = 0
            else:
                patience += 1
                if patience >= patience_max:
                    break

            trial.report(val_rmse, ep)
            if trial.should_prune():
                raise optuna.TrialPruned()

        return best_val

    sampler = optuna.samplers.TPESampler(seed=SEED)
    pruner = optuna.pruners.MedianPruner(n_startup_trials=5, n_warmup_steps=30)
    study = optuna.create_study(direction="minimize", sampler=sampler, pruner=pruner)
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    study.optimize(objective, n_trials=n_trials, show_progress_bar=False)

    bp = study.best_trial.params
    w_mono_final = bp.get("w_mono", 0.0)
    logger.info(f"  Best params: width={bp['width']} depth={bp['depth']} lr={bp['lr']:.2e}"
                + (f" w_mono={w_mono_final:.3e}" if use_mono else ""))

    # Final training with best params
    model = BayesianMLP(in_dim=in_dim, out_dim=out_dim,
                        width=int(bp["width"]), depth=int(bp["depth"]),
                        prior_sigma=1.0, homoscedastic=homoscedastic).to(device)
    opt = torch.optim.Adam(model.parameters(), lr=bp["lr"])
    N = len(Xt)
    best_val, best_state = float("inf"), None
    patience, patience_max = 0, 30

    for ep in range(bp["epochs"]):
        model.train()
        perm = torch.randperm(N, device=device)
        n_bat = max(1, N // int(bp["batch"]))
        for i in range(n_bat):
            idx = perm[i*int(bp["batch"]):(i+1)*int(bp["batch"])]
            mu, logvar = model(Xt[idx], sample=True)
            kl = model.kl_divergence()
            loss = gaussian_nll(Yt[idx], mu, logvar) + 1e-3 * kl / N
            if use_mono:
                loss = loss + loss_phy_monotone(model, Xt[idx], phy_pairs, w_mono_final)
            opt.zero_grad(); loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 2.0)
            opt.step()

        model.eval()
        with torch.no_grad():
            mu_v, _ = model(Xv, sample=False)
        mu_v_np = mu_v.cpu().numpy() * sy.scale_ + sy.mean_
        val_rmse = float(np.sqrt(np.mean((mu_v_np - Y_val) ** 2)))

        if val_rmse < best_val - 1e-6:
            best_val = val_rmse
            best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}
            patience = 0
        else:
            patience += 1
            if patience >= patience_max:
                break

    if best_state:
        model.load_state_dict(best_state)
    model.eval()

    return model, sx, sy, bp


def train_mf_simple(model_id, X_train, Y_train, X_val, Y_val, device, n_trials=20):
    """Simplified MF hybrid training for small-sample experiments."""
    from bnn_multifidelity import MultiFidelityBNN_Hybrid, RESIDUAL_IDX, DIRECT_IDX
    from experiment_config_0404 import DELTA_PAIRS

    # Build MF output order (same as run_train_mf_0404.py)
    mf_order = list(OUT1)
    for ri in RESIDUAL_IDX:
        mf_order.append(DELTA_PAIRS[ri][1])
    for di in DIRECT_IDX:
        mf_order.append(DELTA_PAIRS[di][1])
    mf_order.append("iteration2_keff")

    canonical_to_mf = [mf_order.index(c) for c in OUTPUT_COLS]
    mf_to_canonical = [OUTPUT_COLS.index(c) for c in mf_order]

    Y_train_mf = Y_train[:, canonical_to_mf]
    Y_val_orig = Y_val.copy()

    sx = StandardScaler().fit(X_train)
    sy_mf = StandardScaler().fit(Y_train_mf)

    in_dim = len(INPUT_COLS)
    n_iter1 = len(OUT1)

    Xt = torch.tensor(sx.transform(X_train), dtype=torch.float32, device=device)
    Yt = torch.tensor(sy_mf.transform(Y_train_mf), dtype=torch.float32, device=device)

    def objective(trial):
        w1 = trial.suggest_int("width1", 64, 256)
        d1 = trial.suggest_int("depth1", 2, 4)
        w2 = trial.suggest_int("width2", 64, 256)
        d2 = trial.suggest_int("depth2", 2, 4)
        lr = trial.suggest_float("lr", 1e-4, 1e-3, log=True)
        batch = trial.suggest_categorical("batch", [32, 64, 128])
        epochs = trial.suggest_int("epochs", 100, 300)

        model = MultiFidelityBNN_Hybrid(
            in_dim=in_dim, n_iter1=n_iter1,
            width1=w1, depth1=d1,
            width_delta=w2, depth_delta=d2,
            width_direct=w2, depth_direct=d2,
        ).to(device)
        opt = torch.optim.Adam(model.parameters(), lr=lr)
        N = len(Xt)
        best_val = float("inf")
        patience, patience_max = 0, 20

        for ep in range(epochs):
            model.train()
            perm_idx = torch.randperm(N, device=device)
            n_bat = max(1, N // batch)
            for i in range(n_bat):
                idx = perm_idx[i*batch:(i+1)*batch]
                mu, logvar = model(Xt[idx], sample=True)
                kl = model.kl_divergence()
                loss = gaussian_nll(Yt[idx], mu, logvar) + 1e-3 * kl / N
                opt.zero_grad(); loss.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(), 2.0)
                opt.step()

            model.eval()
            mu_mean, _, _, _, _ = _mc_predict_mf_simple(
                model, X_val, sx, sy_mf, mf_to_canonical, device)
            val_rmse = float(np.sqrt(np.mean((mu_mean - Y_val_orig) ** 2)))

            if val_rmse < best_val - 1e-6:
                best_val = val_rmse
                patience = 0
            else:
                patience += 1
                if patience >= patience_max:
                    break

            trial.report(val_rmse, ep)
            if trial.should_prune():
                raise optuna.TrialPruned()

        return best_val

    sampler = optuna.samplers.TPESampler(seed=SEED)
    pruner = optuna.pruners.MedianPruner(n_startup_trials=5, n_warmup_steps=30)
    study = optuna.create_study(direction="minimize", sampler=sampler, pruner=pruner)
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    study.optimize(objective, n_trials=n_trials, show_progress_bar=False)

    bp = study.best_trial.params
    logger.info(f"  Best params: w1={bp['width1']} d1={bp['depth1']} w2={bp['width2']} d2={bp['depth2']}")

    # Final training
    model = MultiFidelityBNN_Hybrid(
        in_dim=in_dim, n_iter1=n_iter1,
        width1=int(bp["width1"]), depth1=int(bp["depth1"]),
        width_delta=int(bp.get("width2", 64)),
        depth_delta=int(bp.get("depth2", 2)),
        width_direct=int(bp["width2"]), depth_direct=int(bp["depth2"]),
    ).to(device)
    opt = torch.optim.Adam(model.parameters(), lr=bp["lr"])
    N = len(Xt)
    best_val, best_state = float("inf"), None
    patience, patience_max = 0, 30

    for ep in range(bp["epochs"]):
        model.train()
        perm_idx = torch.randperm(N, device=device)
        n_bat = max(1, N // int(bp["batch"]))
        for i in range(n_bat):
            idx = perm_idx[i*int(bp["batch"]):(i+1)*int(bp["batch"])]
            mu, logvar = model(Xt[idx], sample=True)
            kl = model.kl_divergence()
            loss = gaussian_nll(Yt[idx], mu, logvar) + 1e-3 * kl / N
            opt.zero_grad(); loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 2.0)
            opt.step()

        model.eval()
        mu_mean, _, _, _, _ = _mc_predict_mf_simple(
            model, X_val, sx, sy_mf, mf_to_canonical, device)
        val_rmse = float(np.sqrt(np.mean((mu_mean - Y_val_orig) ** 2)))

        if val_rmse < best_val - 1e-6:
            best_val = val_rmse
            best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}
            patience = 0
        else:
            patience += 1
            if patience >= patience_max:
                break

    if best_state:
        model.load_state_dict(best_state)
    model.eval()

    # Attach reorder perm for mc_predict
    perm = np.array([OUTPUT_COLS.index(c) for c in mf_order])
    model._mf_to_canonical = perm

    return model, sx, sy_mf, bp


@torch.no_grad()
def _mc_predict_mf_simple(model, X_np, sx, sy_mf, mf_to_canonical, device, n_mc=30):
    """Quick MC predict for MF model, returns canonical order."""
    model.eval()
    X_sc = torch.tensor(sx.transform(X_np), dtype=torch.float32, device=device)
    mus, logvars = [], []
    for _ in range(n_mc):
        mu, lv = model(X_sc, sample=True)
        mus.append(mu.cpu().numpy())
        logvars.append(lv.cpu().numpy())

    mus_np = np.stack(mus)
    logvars_np = np.stack(logvars)
    sy_mean = sy_mf.mean_[np.newaxis, :]
    sy_scale = sy_mf.scale_[np.newaxis, :]
    mus_orig = mus_np * sy_scale + sy_mean
    vars_orig = np.exp(logvars_np) * (sy_scale ** 2)

    mu_mean = np.mean(mus_orig, axis=0)
    epi_var = np.var(mus_orig, axis=0)
    ale_var = np.mean(vars_orig, axis=0)
    total_var = epi_var + ale_var

    # Reorder to canonical
    mu_mean = mu_mean[:, mf_to_canonical]
    mu_std = np.sqrt(epi_var)[:, mf_to_canonical]
    ale_var = ale_var[:, mf_to_canonical]
    epi_var = epi_var[:, mf_to_canonical]
    total_var = total_var[:, mf_to_canonical]

    return mu_mean, mu_std, ale_var, epi_var, total_var


def evaluate(model, X_test, Y_test, sx, sy, device, is_mf=False):
    """Evaluate model on test set, return per-output metrics."""
    if is_mf:
        from bnn_multifidelity import RESIDUAL_IDX, DIRECT_IDX
        from experiment_config_0404 import DELTA_PAIRS
        mf_order = list(OUT1)
        for ri in RESIDUAL_IDX:
            mf_order.append(DELTA_PAIRS[ri][1])
        for di in DIRECT_IDX:
            mf_order.append(DELTA_PAIRS[di][1])
        mf_order.append("iteration2_keff")
        mf_to_canonical = [OUTPUT_COLS.index(c) for c in mf_order]
        mu_mean, mu_std, ale_var, epi_var, total_var = _mc_predict_mf_simple(
            model, X_test, sx, sy, mf_to_canonical, device, n_mc=BNN_N_MC_EVAL)
    else:
        mu_mean, mu_std, ale_var, epi_var, total_var = mc_predict(
            model, X_test, sx, sy, device, n_mc=BNN_N_MC_EVAL)

    results = {}
    for j, col in enumerate(OUTPUT_COLS):
        y_true = Y_test[:, j]
        y_pred = mu_mean[:, j]
        r2 = float(r2_score(y_true, y_pred))
        rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
        results[col] = {"R2": r2, "RMSE": rmse}

    r2_mean = np.mean([v["R2"] for v in results.values()])
    rmse_mean = np.mean([v["RMSE"] for v in results.values()])
    return results, float(r2_mean), float(rmse_mean)


def main():
    model_id = os.environ.get("MODEL_ID", "bnn-baseline")
    frac = float(os.environ.get("FRAC", "0.4"))

    logger.info(f"Small-sample test: model={model_id}, frac={frac}")

    csv_path = get_csv_path()
    df = pd.read_csv(csv_path).dropna()
    logger.info(f"Dataset: {len(df)} rows")

    seed_all(SEED)
    device = torch.device(DEVICE)

    X_train, Y_train, X_val, Y_val, X_test, Y_test = load_fixed_split_subsample(df, frac)

    is_mf = "mf" in model_id
    n_trials = 15

    t0 = time.time()
    if is_mf:
        model, sx, sy, bp = train_mf_simple(model_id, X_train, Y_train, X_val, Y_val, device, n_trials)
    else:
        model, sx, sy, bp = train_bnn_simple(model_id, X_train, Y_train, X_val, Y_val, device, n_trials)
    t_train = time.time() - t0

    per_output, r2_mean, rmse_mean = evaluate(model, X_test, Y_test, sx, sy, device, is_mf)

    logger.info(f"  R2_mean={r2_mean:.4f}  RMSE_mean={rmse_mean:.4f}  time={t_train:.0f}s")

    # Primary outputs
    for col in ["iteration2_max_global_stress", "iteration2_keff",
                "iteration2_max_fuel_temp", "iteration2_wall2"]:
        m = per_output[col]
        logger.info(f"  {col}: R2={m['R2']:.4f}  RMSE={m['RMSE']:.4f}")

    # Save results
    out_dir = os.path.join(EXPR_ROOT_0404, "experiments", "small_sample",
                           model_id, f"frac_{frac:.1f}")
    ensure_dir(out_dir)

    frac_str = f"{frac:.1f}"
    metrics = {
        "model_id": model_id,
        "frac": frac,
        "n_train": len(X_train),
        "n_val": len(X_val),
        "n_test": len(X_test),
        "r2_mean": r2_mean,
        "rmse_mean": rmse_mean,
        "training_time_s": t_train,
        "best_params": bp,
        "per_output": per_output,
    }
    with open(os.path.join(out_dir, "metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2)

    logger.info(f"  Saved → {out_dir}/metrics.json")


if __name__ == "__main__":
    main()
