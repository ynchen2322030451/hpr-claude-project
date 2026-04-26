# run_external_baseline_uq_0404.py
# ============================================================
# LOCAL ONLY — Full UQ pipeline for external baselines
# (MC-Dropout, Deep Ensemble)
#
# Computes: multi-α calibration, scoring rules (CRPS, NLL, IS,
# ECE), PIT, reliability diagrams — same metrics as BNN models.
# Also computes stress risk P(σ > 131 MPa) for comparison.
#
# Input:  code/models/{mc-dropout,deep-ensemble}/fixed_eval/
#           test_predictions_fixed.json
# Output: results/accuracy/external_baseline_calibration.csv
#         results/accuracy/external_baseline_scoring.csv
#         results/accuracy/external_baseline_risk.csv
#         results/accuracy/reliability_*.png (per baseline)
#         results/accuracy/pit_*.png (per baseline)
# ============================================================

import os, sys, json, logging
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import norm

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_CODE_ROOT = _SCRIPT_DIR
while _CODE_ROOT and os.path.basename(_CODE_ROOT) != 'code':
    _CODE_ROOT = os.path.dirname(_CODE_ROOT)
_BNN_CONFIG_DIR = os.path.join(_CODE_ROOT, 'experiments_0404', 'config')
for _p in (_SCRIPT_DIR, _CODE_ROOT, _BNN_CONFIG_DIR):
    if _p and os.path.isdir(_p) and _p not in sys.path:
        sys.path.insert(0, _p)

from experiment_config_0404 import (
    OUTPUT_COLS, PRIMARY_OUTPUTS, PRIMARY_STRESS_OUTPUT,
    PRIMARY_STRESS_THRESHOLD, ensure_dir,
)

logging.basicConfig(level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger(__name__)

_BNN_ROOT = os.path.dirname(_CODE_ROOT)

EXTERNAL_MODELS = {
    "mc-dropout":    "MC-Dropout (Gal & Ghahramani 2016)",
    "deep-ensemble": "Deep Ensemble (Lakshminarayanan 2017)",
}

OUTPUT_PAPER_LABEL = {
    "iteration2_max_global_stress": "Max stress",
    "iteration2_keff":              r"$k_{\mathrm{eff}}$",
    "iteration2_max_fuel_temp":     "Max fuel temp",
    "iteration2_max_monolith_temp": "Max monolith temp",
    "iteration2_wall2":             "Wall expansion",
}

ALPHA_LEVELS = [0.5, 0.68, 0.8, 0.9, 0.95, 0.99]
PIT_N_BINS = 20
STRESS_IDX = OUTPUT_COLS.index(PRIMARY_STRESS_OUTPUT)


# ── Scoring functions (same as run_calibration_0404.py) ──────

def gaussian_crps(mu, sigma, y):
    sigma = np.maximum(sigma, 1e-10)
    z = (y - mu) / sigma
    return sigma * (z * (2 * norm.cdf(z) - 1) + 2 * norm.pdf(z) - 1.0 / np.sqrt(np.pi))

def gaussian_nll(mu, sigma, y):
    sigma = np.maximum(sigma, 1e-10)
    return 0.5 * (np.log(2 * np.pi * sigma ** 2) + ((y - mu) / sigma) ** 2)

def interval_score(mu, sigma, y, alpha):
    sigma = np.maximum(sigma, 1e-10)
    z = norm.ppf(0.5 + alpha / 2)
    lo, hi = mu - z * sigma, mu + z * sigma
    width = hi - lo
    beta = 1.0 - alpha
    penalty_lo = (2.0 / beta) * np.maximum(lo - y, 0)
    penalty_hi = (2.0 / beta) * np.maximum(y - hi, 0)
    return width + penalty_lo + penalty_hi

def pit_values(mu, sigma, y):
    sigma = np.maximum(sigma, 1e-10)
    return norm.cdf((y - mu) / sigma)

def empirical_coverage(mu, sigma, y, alpha):
    z = norm.ppf(0.5 + alpha / 2)
    lo, hi = mu - z * sigma, mu + z * sigma
    return float(np.mean((y >= lo) & (y <= hi)))


def load_predictions(model_id):
    p = os.path.join(_CODE_ROOT, "models", model_id, "fixed_eval",
                     "test_predictions_fixed.json")
    if not os.path.exists(p):
        raise FileNotFoundError(p)
    with open(p) as f:
        d = json.load(f)
    return {
        "mu": np.asarray(d["mu"]),
        "sigma": np.asarray(d["sigma"]),
        "epistemic_var": np.asarray(d.get("epistemic_var", np.zeros_like(d["mu"]))),
        "aleatoric_var": np.asarray(d.get("aleatoric_var", np.zeros_like(d["mu"]))),
        "y_true": np.asarray(d["y_true"]),
        "output_cols": d.get("output_cols", OUTPUT_COLS),
    }


def run():
    out_dir = ensure_dir(os.path.join(_BNN_ROOT, "results", "accuracy"))

    calib_rows = []
    scoring_rows = []
    risk_rows = []

    for mid, label in EXTERNAL_MODELS.items():
        logger.info(f"Processing {mid}...")
        try:
            pred = load_predictions(mid)
        except FileNotFoundError:
            logger.warning(f"  [{mid}] no predictions found, skip")
            continue

        mu = pred["mu"]
        sigma = pred["sigma"]
        y_true = pred["y_true"]
        cols = pred["output_cols"]

        for oc in PRIMARY_OUTPUTS:
            if oc not in cols:
                continue
            j = cols.index(oc)
            m_j, s_j, y_j = mu[:, j], sigma[:, j], y_true[:, j]

            # Multi-α calibration
            for alpha in ALPHA_LEVELS:
                cov = empirical_coverage(m_j, s_j, y_j, alpha)
                iscore = float(np.mean(interval_score(m_j, s_j, y_j, alpha)))
                z = norm.ppf(0.5 + alpha / 2)
                mpiw = float(np.mean(2 * z * s_j))
                calib_rows.append({
                    "model_id": mid, "model_label": label,
                    "output": oc,
                    "output_label": OUTPUT_PAPER_LABEL.get(oc, oc),
                    "nominal_alpha": alpha,
                    "empirical_coverage": cov,
                    "interval_score": iscore,
                    "MPIW_alpha": mpiw,
                })

            # Scoring rules
            crps = float(np.mean(gaussian_crps(m_j, s_j, y_j)))
            nll = float(np.mean(gaussian_nll(m_j, s_j, y_j)))
            is90 = float(np.mean(interval_score(m_j, s_j, y_j, 0.90)))
            is95 = float(np.mean(interval_score(m_j, s_j, y_j, 0.95)))
            rmse = float(np.sqrt(np.mean((m_j - y_j) ** 2)))
            mae = float(np.mean(np.abs(m_j - y_j)))
            r2 = 1 - np.sum((y_j - m_j) ** 2) / np.sum((y_j - np.mean(y_j)) ** 2)

            covs = [empirical_coverage(m_j, s_j, y_j, a) for a in ALPHA_LEVELS]
            ece = float(np.mean([abs(c - a) for c, a in zip(covs, ALPHA_LEVELS)]))
            sharpness = float(np.mean(s_j))

            scoring_rows.append({
                "model_id": mid, "model_label": label,
                "output": oc,
                "output_label": OUTPUT_PAPER_LABEL.get(oc, oc),
                "RMSE": rmse, "MAE": mae, "R2": float(r2),
                "CRPS": crps, "NLL": nll,
                "IS_90": is90, "IS_95": is95,
                "ECE": ece, "sharpness": sharpness,
            })

        # Stress risk P(σ > threshold)
        stress_mu = mu[:, STRESS_IDX]
        stress_sigma = sigma[:, STRESS_IDX]
        p_exceed = 1.0 - norm.cdf(PRIMARY_STRESS_THRESHOLD, loc=stress_mu, scale=np.maximum(stress_sigma, 1e-10))
        risk_rows.append({
            "model_id": mid, "model_label": label,
            "threshold_MPa": PRIMARY_STRESS_THRESHOLD,
            "P_exceed_mean": float(np.mean(p_exceed)),
            "P_exceed_std": float(np.std(p_exceed)),
            "P_exceed_max": float(np.max(p_exceed)),
            "n_exceed_50pct": int(np.sum(p_exceed > 0.5)),
            "n_test": len(stress_mu),
        })

        # Reliability diagram
        fig, axes = plt.subplots(1, len(PRIMARY_OUTPUTS), figsize=(4 * len(PRIMARY_OUTPUTS), 4))
        if len(PRIMARY_OUTPUTS) == 1:
            axes = [axes]
        for ax, oc in zip(axes, PRIMARY_OUTPUTS):
            if oc not in cols:
                continue
            j = cols.index(oc)
            m_j, s_j, y_j = mu[:, j], sigma[:, j], y_true[:, j]
            emp = [empirical_coverage(m_j, s_j, y_j, a) for a in ALPHA_LEVELS]
            ax.plot([0, 1], [0, 1], "k--", lw=0.8)
            ax.plot(ALPHA_LEVELS, emp, "o-", markersize=4)
            ax.set_xlabel("Nominal coverage")
            ax.set_ylabel("Empirical coverage")
            ax.set_title(OUTPUT_PAPER_LABEL.get(oc, oc), fontsize=9)
            ax.set_xlim(0.4, 1)
            ax.set_ylim(0.4, 1)
            ax.set_aspect("equal")
        fig.suptitle(f"{label} — reliability diagram", fontsize=11)
        plt.tight_layout()
        for ext in ("pdf", "png"):
            fig.savefig(os.path.join(out_dir, f"reliability_{mid}.{ext}"), dpi=200)
        plt.close(fig)

        # PIT histogram
        fig, axes = plt.subplots(1, len(PRIMARY_OUTPUTS), figsize=(4 * len(PRIMARY_OUTPUTS), 3.5))
        if len(PRIMARY_OUTPUTS) == 1:
            axes = [axes]
        for ax, oc in zip(axes, PRIMARY_OUTPUTS):
            if oc not in cols:
                continue
            j = cols.index(oc)
            pvals = pit_values(mu[:, j], sigma[:, j], y_true[:, j])
            ax.hist(pvals, bins=PIT_N_BINS, density=True, alpha=0.7, color="#4CAF50", edgecolor="white")
            ax.axhline(1.0, color="k", ls="--", lw=0.8)
            ax.set_xlabel("PIT value")
            ax.set_ylabel("Density")
            ax.set_title(OUTPUT_PAPER_LABEL.get(oc, oc), fontsize=9)
            ax.set_xlim(0, 1)
        fig.suptitle(f"{label} — PIT histogram", fontsize=11)
        plt.tight_layout()
        for ext in ("pdf", "png"):
            fig.savefig(os.path.join(out_dir, f"pit_{mid}.{ext}"), dpi=200)
        plt.close(fig)

        logger.info(f"  [{mid}] calibration + scoring + figures done")

    # Save CSVs
    cdf = pd.DataFrame(calib_rows)
    cdf.to_csv(os.path.join(out_dir, "external_baseline_calibration.csv"), index=False)
    logger.info(f"Calibration: {len(cdf)} rows")

    sdf = pd.DataFrame(scoring_rows)
    sdf.to_csv(os.path.join(out_dir, "external_baseline_scoring.csv"), index=False)
    logger.info(f"Scoring: {len(sdf)} rows")

    rdf = pd.DataFrame(risk_rows)
    rdf.to_csv(os.path.join(out_dir, "external_baseline_risk.csv"), index=False)
    logger.info(f"Risk: {len(rdf)} rows")

    print("\n=== External Baseline Scoring Summary ===")
    print(sdf[["model_label", "output_label", "RMSE", "R2", "CRPS", "NLL", "ECE"]].to_string(index=False))
    print("\n=== External Baseline Risk ===")
    print(rdf.to_string(index=False))


if __name__ == "__main__":
    run()
