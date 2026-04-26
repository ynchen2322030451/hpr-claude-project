# run_train_mf_0404.py
# ============================================================
# Multi-fidelity BNN training script.
#
# Supports two MF architectures:
#   bnn-mf-stacked   — Stage1: BNN(x→iter1), Stage2: BNN(x,ŷ₁→iter2)
#   bnn-mf-residual  — Stage1: BNN(x→iter1), Delta: BNN(x,ŷ₁→Δ), keff: BNN(x→keff)
#
# Reuses infrastructure from run_train_0404.py (data loading, scalers,
# Optuna framework, evaluation) but swaps in MultiFidelityBNN models.
#
# Usage:
#   MODEL_ID=bnn-mf-stacked python run_train_mf_0404.py
#   MODEL_ID=bnn-mf-residual python run_train_mf_0404.py
# ============================================================

import os, sys, json, pickle, time, logging
os.environ.setdefault("PYTHONUNBUFFERED", "1")
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F
import optuna
from sklearn.preprocessing import StandardScaler

# ── Path setup (same as run_train_0404.py) ──
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_BNN_CODE_DIR = _SCRIPT_DIR
while _BNN_CODE_DIR and os.path.basename(_BNN_CODE_DIR) != 'code':
    _BNN_CODE_DIR = os.path.dirname(_BNN_CODE_DIR)
_BNN_CONFIG_DIR = os.path.join(_BNN_CODE_DIR, 'experiments_0404', 'config')
_ROOT_0310 = os.path.join(os.path.dirname(os.path.dirname(_BNN_CODE_DIR)), '0310')

for _p in (_SCRIPT_DIR, _BNN_CODE_DIR, _BNN_CONFIG_DIR, _ROOT_0310,
           os.environ.get('HPR_LEGACY_DIR', '')):
    if _p and os.path.isdir(_p) and _p not in sys.path:
        _is_legacy = any(seg in _p for seg in ('/0310', 'hpr_legacy'))
        if _is_legacy:
            if _p not in sys.path:
                sys.path.append(_p)
        else:
            sys.path.insert(0, _p)
del _p

from experiment_config_0404 import (
    INPUT_COLS, OUTPUT_COLS, OUT1, OUT2, DELTA_PAIRS,
    ITER1_IDX, ITER2_IDX,
    SEED, TRIALS_ABLATION,
    FIXED_SPLIT_DIR, EXPR_ROOT_0404,
    model_artifacts_dir, model_manifests_dir, model_logs_dir,
    model_fixed_eval_dir, ensure_dir,
    get_csv_path, DEVICE,
    BNN_N_MC_EVAL,
)
from model_registry_0404 import MODELS, get_optuna_space
from bnn_model import (
    gaussian_nll, seed_all, get_device, mc_predict,
)
from bnn_multifidelity import (
    MultiFidelityBNN_Stacked, MultiFidelityBNN_Residual,
    MultiFidelityBNN_Hybrid,
    get_mf_output_mapping, reorder_mf_to_canonical,
    RESIDUAL_IDX, DIRECT_IDX, N_RESIDUAL, N_DIRECT_ITER2,
)

# Reuse helpers from standard training
from run_train_0404 import (
    setup_logger, load_full_dataset, load_fixed_split,
    evaluate_on_test,
)
from manifest_utils_0404 import resolve_output_dir


# ────────────────────────────────────────────────────────────
# MF output column ordering
# ────────────────────────────────────────────────────────────
# MF model outputs in order: [iter1(7), iter2_paired(7), keff(1)] = 15
# We need separate scalers for this ordering vs the canonical ordering.

def _build_mf_output_order(cls_name: str) -> list:
    """Build the MF output column ordering based on model class."""
    order = list(OUT1)  # iter1 (7)

    if cls_name == "MultiFidelityBNN_Hybrid":
        # iter2 residual: stress, wall2 (in RESIDUAL_IDX order)
        for ri in RESIDUAL_IDX:
            order.append(DELTA_PAIRS[ri][1])
        # iter2 direct: remaining temps/Hcore (DIRECT_IDX order) + keff
        for di in DIRECT_IDX:
            order.append(DELTA_PAIRS[di][1])
        order.append("iteration2_keff")
    else:
        # Stacked / Residual: iter2 paired (7) + keff (1)
        for _, i2_col in DELTA_PAIRS:
            order.append(i2_col)
        order.append("iteration2_keff")

    assert len(order) == 15
    assert set(order) == set(OUTPUT_COLS)
    return order


def _build_permutations(mf_order: list):
    canonical_to_mf = [mf_order.index(c) for c in OUTPUT_COLS]
    mf_to_canonical = [OUTPUT_COLS.index(c) for c in mf_order]
    return canonical_to_mf, mf_to_canonical


def reorder_Y_to_mf(Y_canonical: np.ndarray, perm) -> np.ndarray:
    return Y_canonical[:, perm]


def reorder_Y_to_canonical(Y_mf: np.ndarray, perm) -> np.ndarray:
    return Y_mf[:, perm]


# ────────────────────────────────────────────────────────────
# Model creation
# ────────────────────────────────────────────────────────────
def create_mf_model(model_id: str, params: dict, device) -> torch.nn.Module:
    minfo = MODELS[model_id]
    cls_name = minfo.get("model_class", "MultiFidelityBNN_Stacked")
    prior_sigma = float(params.get("prior_sigma", 1.0))

    if cls_name == "MultiFidelityBNN_Stacked":
        model = MultiFidelityBNN_Stacked(
            in_dim=len(INPUT_COLS),
            n_iter1=len(OUT1), n_iter2=len(OUT2),
            width1=int(params["width1"]), depth1=int(params["depth1"]),
            width2=int(params["width2"]), depth2=int(params["depth2"]),
            prior_sigma=prior_sigma,
        )
    elif cls_name == "MultiFidelityBNN_Residual":
        model = MultiFidelityBNN_Residual(
            in_dim=len(INPUT_COLS),
            n_iter1=len(OUT1),
            width1=int(params["width1"]), depth1=int(params["depth1"]),
            width_delta=int(params["width2"]), depth_delta=int(params["depth2"]),
            prior_sigma=prior_sigma,
        )
    elif cls_name == "MultiFidelityBNN_Hybrid":
        model = MultiFidelityBNN_Hybrid(
            in_dim=len(INPUT_COLS),
            n_iter1=len(OUT1),
            width1=int(params["width1"]), depth1=int(params["depth1"]),
            width_delta=int(params.get("width2", 64)),
            depth_delta=int(params.get("depth2", 2)),
            width_direct=int(params["width2"]), depth_direct=int(params["depth2"]),
            prior_sigma=prior_sigma,
        )
    else:
        raise ValueError(f"Unknown MF model class: {cls_name}")

    return model.to(device)


# ────────────────────────────────────────────────────────────
# MC predict for MF model (reorder output to canonical)
# ────────────────────────────────────────────────────────────
@torch.no_grad()
def mc_predict_mf(model, X_np, sx, sy_mf, device, mf_to_canonical, n_mc=50):
    """
    MC prediction for MF model. Returns in canonical OUTPUT_COLS order.

    sy_mf: StandardScaler fitted on MF-ordered Y.
    mf_to_canonical: permutation array to reorder MF output → canonical.
    """
    model.eval()
    X_scaled = sx.transform(X_np)
    x_t = torch.tensor(X_scaled, dtype=torch.float32, device=device)

    mus_scaled, logvars_scaled = model.predict_mc(x_t, n_mc=n_mc)
    mus_np = mus_scaled.cpu().numpy()
    logvars_np = logvars_scaled.cpu().numpy()

    sy_mean = sy_mf.mean_[np.newaxis, :]
    sy_scale = sy_mf.scale_[np.newaxis, :]

    mus_orig = mus_np * sy_scale + sy_mean
    vars_scaled = np.exp(logvars_np)
    vars_orig = vars_scaled * (sy_scale ** 2)

    mu_mean = np.mean(mus_orig, axis=0)
    epistemic_var = np.var(mus_orig, axis=0)
    aleatoric_var = np.mean(vars_orig, axis=0)
    total_var = epistemic_var + aleatoric_var
    mu_std = np.sqrt(epistemic_var)

    # Reorder from MF order to canonical
    mu_mean = reorder_Y_to_canonical(mu_mean, mf_to_canonical)
    mu_std = reorder_Y_to_canonical(mu_std, mf_to_canonical)
    aleatoric_var = reorder_Y_to_canonical(aleatoric_var, mf_to_canonical)
    epistemic_var = reorder_Y_to_canonical(epistemic_var, mf_to_canonical)
    total_var = reorder_Y_to_canonical(total_var, mf_to_canonical)

    return mu_mean, mu_std, aleatoric_var, epistemic_var, total_var


# ────────────────────────────────────────────────────────────
# Optuna objective
# ────────────────────────────────────────────────────────────
def make_mf_objective(model_id, X_train, Y_train_mf, X_val, Y_val,
                      device, sx, sy_mf, mf_to_canonical, logger):
    minfo = MODELS[model_id]
    space = get_optuna_space(model_id)

    def objective(trial):
        def s(key):
            sp = space[key]
            t = sp["type"]
            if t == "int":
                return trial.suggest_int(key, sp["low"], sp["high"])
            elif t == "float":
                return trial.suggest_float(key, sp["low"], sp["high"], log=sp.get("log", False))
            elif t == "cat":
                return trial.suggest_categorical(key, sp["choices"])

        params = {k: s(k) for k in space}

        logger.info(f"  Trial {trial.number}: w1={params.get('width1','-')} d1={params.get('depth1','-')} "
                    f"w2={params.get('width2','-')} d2={params.get('depth2','-')} "
                    f"lr={params['lr']:.2e} batch={params['batch']} epochs={params['epochs']}")
        sys.stdout.flush()
        seed_all(SEED + trial.number)
        model = create_mf_model(model_id, params, device)
        optimizer = torch.optim.Adam(model.parameters(), lr=float(params["lr"]))

        Xt = torch.tensor(sx.transform(X_train), dtype=torch.float32, device=device)
        Yt = torch.tensor(sy_mf.transform(Y_train_mf), dtype=torch.float32, device=device)
        N = len(Xt)
        batch = int(params["batch"])
        epochs = int(params["epochs"])
        clip = float(params["clip"])
        w_data = float(params["w_data"])
        kl_weight = float(params["kl_weight"])

        best_val, patience, patience_max = float("inf"), 0, 30

        for ep in range(epochs):
            model.train()
            perm = torch.randperm(N, device=device)
            n_bat = max(1, N // batch)
            for i in range(n_bat):
                idx = perm[i * batch:(i + 1) * batch]
                xb, yb = Xt[idx], Yt[idx]
                optimizer.zero_grad()

                mu, logvar = model(xb, sample=True)
                kl = model.kl_divergence()
                loss_data = gaussian_nll(yb, mu, logvar)
                loss = w_data * loss_data + kl_weight * kl / N

                loss.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(), clip)
                optimizer.step()

            # Validation
            model.eval()
            mu_mean, _, _, _, _ = mc_predict_mf(
                model, X_val, sx, sy_mf, device, mf_to_canonical, n_mc=BNN_N_MC_EVAL)
            val_rmse = float(np.sqrt(np.mean((mu_mean - Y_val) ** 2)))

            trial.report(val_rmse, ep)
            if trial.should_prune():
                raise optuna.exceptions.TrialPruned()

            if val_rmse < best_val - 1e-6:
                best_val = val_rmse
                patience = 0
            else:
                patience += 1
                if patience >= patience_max:
                    break

        logger.info(f"  Trial {trial.number} done: val_rmse={best_val:.4f} epochs_run={ep+1}")
        sys.stdout.flush()
        return best_val

    return objective


# ────────────────────────────────────────────────────────────
# Final training
# ────────────────────────────────────────────────────────────
def final_train_mf(model_id, best_params, X_train, Y_train_mf, X_val, Y_val,
                   device, sx, sy_mf, mf_to_canonical, logger):
    seed_all(SEED)
    model = create_mf_model(model_id, best_params, device)
    optimizer = torch.optim.Adam(model.parameters(), lr=float(best_params["lr"]))

    Xt = torch.tensor(sx.transform(X_train), dtype=torch.float32, device=device)
    Yt = torch.tensor(sy_mf.transform(Y_train_mf), dtype=torch.float32, device=device)
    N = len(Xt)
    batch = int(best_params.get("batch", 64))
    epochs = int(best_params["epochs"])
    clip = float(best_params.get("clip", 1.0))
    w_data = float(best_params.get("w_data", 1.0))
    kl_weight = float(best_params.get("kl_weight", 1e-2))

    best_val, patience, patience_max = float("inf"), 0, 30
    best_state = None
    history = []

    for ep in range(epochs):
        model.train()
        perm = torch.randperm(N, device=device)
        n_bat = max(1, N // batch)
        ep_loss = 0.0
        for i in range(n_bat):
            idx = perm[i * batch:(i + 1) * batch]
            xb, yb = Xt[idx], Yt[idx]
            optimizer.zero_grad()

            mu, logvar = model(xb, sample=True)
            kl = model.kl_divergence()
            loss_data = gaussian_nll(yb, mu, logvar)
            loss = w_data * loss_data + kl_weight * kl / N

            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), clip)
            optimizer.step()
            ep_loss += loss.item()

        model.eval()
        mu_mean, _, _, _, _ = mc_predict_mf(
            model, X_val, sx, sy_mf, device, mf_to_canonical, n_mc=BNN_N_MC_EVAL)
        val_rmse = float(np.sqrt(np.mean((mu_mean - Y_val) ** 2)))
        history.append({"epoch": ep, "train_loss": ep_loss / n_bat, "val_rmse": val_rmse})

        if val_rmse < best_val - 1e-6:
            best_val = val_rmse
            best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}
            patience = 0
        else:
            patience += 1
            if patience >= patience_max:
                logger.info(f"  Early stop at epoch {ep}")
                break

        if ep % 50 == 0:
            logger.info(f"  ep {ep:4d} | train={ep_loss/n_bat:.4f} | val_rmse={val_rmse:.4f} | best={best_val:.4f}")

    if best_state:
        model.load_state_dict(best_state)

    return model, best_val, history


# ────────────────────────────────────────────────────────────
# Main training entry
# ────────────────────────────────────────────────────────────
def train_one_mf(model_id: str, df: pd.DataFrame, logger, force: bool = False) -> dict:
    minfo = MODELS[model_id]
    art_dir = resolve_output_dir(
        model_artifacts_dir(model_id),
        script_name=os.path.basename(__file__),
    )
    ensure_dir(art_dir)

    suffix = "fixed"
    ckpt_path = os.path.join(art_dir, f"checkpoint_{model_id}_{suffix}.pt")
    scaler_path = os.path.join(art_dir, f"scalers_{model_id}_{suffix}.pkl")

    logger.info(f"\n{'='*60}")
    logger.info(f"  MF Model: {model_id}  |  Split: {suffix}")
    logger.info(f"{'='*60}")

    if os.path.exists(ckpt_path) and not force:
        logger.info(f"  checkpoint exists, skipping: {ckpt_path}")
        return {"ckpt_path": ckpt_path, "scaler_path": scaler_path, "skipped": True}

    # Load data
    X_train, Y_train, X_val, Y_val, X_test, Y_test, s_seed = load_fixed_split(df, logger)

    # Build MF output ordering for this model class
    cls_name = minfo.get("model_class", "MultiFidelityBNN_Stacked")
    mf_output_order = _build_mf_output_order(cls_name)
    canonical_to_mf, mf_to_canonical = _build_permutations(mf_output_order)

    logger.info(f"  MF output order: {mf_output_order}")
    logger.info(f"  Model class: {cls_name}")

    # Reorder Y to MF order for training
    Y_train_mf = reorder_Y_to_mf(Y_train, canonical_to_mf)
    Y_val_mf = reorder_Y_to_mf(Y_val, canonical_to_mf)

    # Scalers (input scaler on canonical X, output scaler on MF-ordered Y)
    sx = StandardScaler().fit(X_train)
    sy_mf = StandardScaler().fit(Y_train_mf)

    device = get_device()
    trials = minfo.get("optuna_trials", TRIALS_ABLATION)

    # Optuna
    logger.info(f"  Optuna ({trials} trials)...")
    t0 = time.time()

    sampler = optuna.samplers.TPESampler(seed=SEED)
    pruner = optuna.pruners.MedianPruner(n_startup_trials=10, n_warmup_steps=40)
    study = optuna.create_study(direction="minimize", sampler=sampler, pruner=pruner)
    optuna.logging.set_verbosity(optuna.logging.WARNING)

    obj = make_mf_objective(model_id, X_train, Y_train_mf, X_val, Y_val,
                            device, sx, sy_mf, mf_to_canonical, logger)
    study.optimize(obj, n_trials=trials, show_progress_bar=False)

    best_params = study.best_trial.params
    logger.info(f"  Best val RMSE: {study.best_value:.4f}")
    logger.info(f"  Best params: {best_params}")

    # Final training
    logger.info(f"  Final training (best params)...")
    model, final_val, history = final_train_mf(
        model_id, best_params, X_train, Y_train_mf, X_val, Y_val,
        device, sx, sy_mf, mf_to_canonical, logger
    )
    t_total = time.time() - t0
    logger.info(f"  Total training time: {t_total:.0f}s")

    # Test evaluation (Y_test is in canonical order)
    model.eval()
    mu_mean, mu_std, aleatoric_var, epistemic_var, total_var = mc_predict_mf(
        model, X_test, sx, sy_mf, device, mf_to_canonical, n_mc=BNN_N_MC_EVAL)
    sigma_raw = np.sqrt(total_var)

    from sklearn.metrics import r2_score, mean_squared_error
    per_output = []
    for j, col in enumerate(OUTPUT_COLS):
        y_true = Y_test[:, j]
        y_pred = mu_mean[:, j]
        rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
        r2 = float(r2_score(y_true, y_pred))
        per_output.append({"output": col, "rmse": rmse, "r2": r2})

    r2_mean = float(np.mean([r["r2"] for r in per_output]))
    rmse_mean = float(np.mean([r["rmse"] for r in per_output]))

    metrics = {
        "r2_mean": r2_mean,
        "rmse_mean": rmse_mean,
        "per_output": per_output,
        "n_mc_eval": BNN_N_MC_EVAL,
    }
    logger.info(f"  Test R2: {r2_mean:.4f}  RMSE: {rmse_mean:.4f}")

    # Save checkpoint
    ckpt_obj = {
        "model_state_dict": model.state_dict(),
        "best_params": best_params,
        "best_val_rmse": final_val,
        "model_id": model_id,
        "split_type": suffix,
        "n_outputs": 15,
        "n_inputs": len(INPUT_COLS),
        "model_class": minfo.get("model_class", "MultiFidelityBNN_Stacked"),
        "multifidelity": True,
        "mf_output_order": mf_output_order,
        "prior_sigma": float(best_params.get("prior_sigma", 1.0)),
        "kl_weight": float(best_params.get("kl_weight", 1e-2)),
        "n_mc_eval": BNN_N_MC_EVAL,
    }
    torch.save(ckpt_obj, ckpt_path)

    # Save scalers (MF-ordered output scaler)
    with open(scaler_path, "wb") as f:
        pickle.dump({"sx": sx, "sy": sy_mf, "sy_": sy_mf,
                      "mf_output_order": mf_output_order}, f)

    # Metrics JSON
    metrics_path = os.path.join(art_dir, f"metrics_{model_id}_{suffix}.json")
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)

    # Training history
    hist_path = os.path.join(art_dir, f"training_history_{model_id}_{suffix}.json")
    with open(hist_path, "w") as f:
        json.dump(history, f, indent=2)

    logger.info(f"  Saved: {ckpt_path}")
    return {
        "ckpt_path": ckpt_path,
        "scaler_path": scaler_path,
        "metrics": metrics,
        "skipped": False,
    }


# ────────────────────────────────────────────────────────────
# CLI
# ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    MODEL_ID = os.environ.get("MODEL_ID", "bnn-mf-stacked")
    FORCE = os.environ.get("FORCE_RETRAIN", "") == "1"

    if MODEL_ID not in MODELS:
        print(f"Unknown model_id: {MODEL_ID}")
        print(f"Available MF models: bnn-mf-stacked, bnn-mf-residual")
        sys.exit(1)

    logger = setup_logger(MODEL_ID, model_logs_dir(MODEL_ID))
    logger.info(f"Multi-fidelity training: {MODEL_ID}")

    df = load_full_dataset(logger)
    result = train_one_mf(MODEL_ID, df, logger, force=FORCE)

    if result.get("skipped"):
        logger.info("Training skipped (checkpoint exists).")
    else:
        logger.info(f"Training complete. R2={result['metrics']['r2_mean']:.4f}")
