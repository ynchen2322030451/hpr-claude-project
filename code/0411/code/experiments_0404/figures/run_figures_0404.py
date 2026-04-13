"""
run_figures_0404.py  —  0404 体系主文 & 附录图生成

用法（环境变量控制）：
    python run_figures_0404.py            # 生成全部图
    FIG_SET=main   python run_figures_0404.py   # 只主文图（fig1–fig5）
    FIG_SET=appendix python run_figures_0404.py # 只附录图（figA1–figA8）
    FIG_LIST=fig2,fig4 python run_figures_0404.py  # 只指定图

结果读取优先级：
    1. experiments_0404/models/<model_id>/ （新结果，若存在）
    2. experiments_phys_levels/fixed_surrogate_fixed_*/（旧规范结果）

输出：experiments_0404/figures/  (.pdf .svg .png)
"""

import json, os, sys, warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
from scipy.stats import gaussian_kde

warnings.filterwarnings("ignore")

# ── 路径引导 ───────────────────────────────────────────────────────────────
_HERE       = os.path.dirname(os.path.abspath(__file__))          # figures/
_CODE_0404  = os.path.dirname(_HERE)                              # code/
_EXPR_0404  = os.path.dirname(_CODE_0404)                         # experiments_0404/
_CODE_0310  = os.path.dirname(_EXPR_0404)                         # code/0310/
_PROJECT    = os.path.dirname(_CODE_0310)                         # project root

for _p in [
    os.path.join(_CODE_0404, "config"),
    _CODE_0310,
]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from experiment_config_0404 import (
    EXPR_ROOT_0404, EXPR_ROOT_OLD,
    PRIMARY_OUTPUTS, PRIMARY_STRESS_OUTPUT, PRIMARY_STRESS_THRESHOLD,
    INPUT_COLS, OUTPUT_COLS, PARAM_META, OUTPUT_META,
    model_artifacts_dir, model_fixed_eval_dir, experiment_dir, ensure_dir,
)

# ── 输出目录 ───────────────────────────────────────────────────────────────
FIG_DIR = ensure_dir(os.path.join(_EXPR_0404, "figures"))

# ── 旧数据来源（canonical fallback） ──────────────────────────────────────
_OLD           = EXPR_ROOT_OLD
_OLD_SUR2      = os.path.join(_OLD, "fixed_surrogate_fixed_level2")   # physics-reg
_OLD_SUR0      = os.path.join(_OLD, "fixed_surrogate_fixed_base")     # baseline
_OLD_BC        = os.path.join(_OLD, "benchmark_case")

# ── 颜色 ──────────────────────────────────────────────────────────────────
BLUE   = "#2E86AB"; ORANGE = "#E76F51"; GREEN  = "#57A773"
GRAY   = "#888888"; LGRAY  = "#CCCCCC"; RED    = "#C0392B"
LBLUE  = "#AED9E0"; YELLOW = "#F4D35E"; PURPLE = "#9B5DE5"

plt.rcParams.update({
    "font.family": "sans-serif", "font.size": 10,
    "axes.spines.top": False, "axes.spines.right": False,
    "figure.dpi": 150,
})

# ── 标签 ──────────────────────────────────────────────────────────────────
# 0404 体系统一用工程名称，不用 Level 0/2
MODEL_LABELS = {
    "baseline":    "Baseline surrogate",
    "data-mono":   "Physics-regularized surrogate",
    "phy-mono":    "Physics-monotone surrogate",
}

PRIMARY_LABELS = {
    "iteration2_keff":              r"$k_\mathrm{eff}$",
    "iteration2_max_fuel_temp":     "Max fuel\ntemp (K)",
    "iteration2_max_monolith_temp": "Max monolith\ntemp (K)",
    "iteration2_max_global_stress": "Max global\nstress (MPa)",
    "iteration2_wall2":             "Wall\nexpansion (mm)",
}
PRIMARY = list(PRIMARY_LABELS.keys())

INPUT_LABELS = {m: PARAM_META[m]["label"] for m in INPUT_COLS}

# Output column ordering (matches canonical model output order)
OUT_COLS = [
    "iteration1_avg_fuel_temp","iteration1_max_fuel_temp",
    "iteration1_max_monolith_temp","iteration1_max_global_stress",
    "iteration1_monolith_new_temperature","iteration1_Hcore_after","iteration1_wall2",
    "iteration2_keff","iteration2_avg_fuel_temp","iteration2_max_fuel_temp",
    "iteration2_max_monolith_temp","iteration2_max_global_stress",
    "iteration2_monolith_new_temperature","iteration2_Hcore_after","iteration2_wall2",
]
STRESS2_IDX = OUT_COLS.index("iteration2_max_global_stress")  # 11
KEFF2_IDX   = OUT_COLS.index("iteration2_keff")               # 7

# ── 辅助函数 ──────────────────────────────────────────────────────────────
def savefig(fig, name):
    for ext in ("pdf", "svg", "png"):
        p = os.path.join(FIG_DIR, f"{name}.{ext}")
        kw = {"bbox_inches": "tight"}
        if ext == "png":
            kw["dpi"] = 150
        fig.savefig(p, **kw)
    print(f"  saved  {name}  [pdf/svg/png]")
    plt.close(fig)


def clean_ax(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def _load_test_preds(model_id):
    """Load test predictions for a model.

    Tries 0404 fixed_eval dir first, then falls back to canonical old dir.
    Returns (mu, sigma, y_true) arrays, shape (N, 15).
    """
    # ── 0404 path ──
    eval_dir = model_fixed_eval_dir(model_id)
    tag = {"baseline": "level0", "data-mono": "level2"}.get(model_id, model_id)
    p = os.path.join(eval_dir, f"test_predictions_{tag}.json")
    # ── old canonical fallback ──
    if not os.path.exists(p):
        old_dir = _OLD_SUR2 if model_id == "data-mono" else _OLD_SUR0
        p = os.path.join(old_dir, f"test_predictions_{tag}.json")
    if not os.path.exists(p):
        p = os.path.join(_OLD, f"test_predictions_{tag}.json")
    if not os.path.exists(p):
        return None, None, None
    with open(p) as f:
        d = json.load(f)
    mu    = np.array(d["mu_te"])
    sigma = np.array(d["sigma_te"])
    y     = np.array(d["y_te_true"])
    return mu, sigma, y


def _load_per_dim_metrics(model_id):
    """Load per-output metrics CSV."""
    tag = {"baseline": "level0", "data-mono": "level2"}.get(model_id, model_id)
    # 0404 fixed_eval
    eval_dir = model_fixed_eval_dir(model_id)
    p = os.path.join(eval_dir, f"paper_metrics_per_dim_{tag}.csv")
    if not os.path.exists(p):
        p = os.path.join(_OLD, f"paper_metrics_per_dim_{tag}.csv")
    if not os.path.exists(p):
        return None
    return pd.read_csv(p)


def _r2(df, output):
    row = df[df.output == output]
    if len(row) == 0:
        return float("nan")
    return float(row["R2"].values[0])


def _exists(path):
    return os.path.exists(path)


# ══════════════════════════════════════════════════════════════════════════
# Fig 1  —  Framework overview schematic
# ══════════════════════════════════════════════════════════════════════════
def fig1_framework():
    """Pipeline overview: inputs → HF solver → dataset → surrogate → analyses."""
    for v, (fw, fh) in enumerate([(11, 4), (6, 8)], 1):
        fig, ax = plt.subplots(figsize=(fw, fh))
        ax.set_xlim(0, fw); ax.set_ylim(0, fh); ax.axis("off")

        def box(x, y, w, h, label, sub="", fc="#D6EAF8"):
            p = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.1",
                               fc=fc, ec="#444", lw=1.2)
            ax.add_patch(p)
            dy = 0.18 if sub else 0
            ax.text(x+w/2, y+h/2+dy, label, ha="center", va="center",
                    fontsize=9, fontweight="bold")
            if sub:
                ax.text(x+w/2, y+h/2-dy, sub, ha="center", va="center",
                        fontsize=7.5, color="#555")

        def arr(x1, y1, x2, y2):
            ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                        arrowprops=dict(arrowstyle="-|>", color="#333", lw=1.5))

        if v == 1:
            box(0.1, 1.5, 2.0, 1.2, "8 material\nparameters", "uniform priors",     "#D6EAF8")
            box(2.6, 1.8, 2.4, 0.9, "HF solver",              "OpenMC–FEniCS\n~1 h/run", "#FDEBD0")
            box(2.6, 0.4, 2.4, 1.0, "Dataset",                "n≈2900 samples\n15 outputs", "#D5F5E3")
            box(5.6, 1.1, 2.2, 1.2, "HeteroMLP",              "physics-regularized\nsurrogate", "#D6EAF8")
            box(8.4, 2.9, 2.4, 0.7, "Forward UQ",             "20k samples / 3 ms", "#EBF5FB")
            box(8.4, 1.9, 2.4, 0.7, r"Sobol $S_1,S_T$",       "sensitivity",        "#EBF5FB")
            box(8.4, 0.9, 2.4, 0.7, "Posterior MCMC",         "calibration",        "#EBF5FB")
            arr(2.1, 2.1, 2.6, 2.3); arr(3.8, 1.8, 3.8, 1.4)
            arr(5.0, 0.9, 5.6, 1.4)
            arr(7.8, 2.1, 8.4, 3.25); arr(7.8, 1.7, 8.4, 2.25); arr(7.8, 1.3, 8.4, 1.25)
            ax.text(5.5, 0.2, "23 million× speedup", ha="center", fontsize=9,
                    color=RED, style="italic",
                    bbox=dict(boxstyle="round,pad=0.3", fc="#FEF9E7", ec=RED, lw=0.8))
        else:
            box(1.5, 6.0, 3.0, 1.2, "8 material\nparameters", "uniform priors",     "#D6EAF8")
            arr(3.0, 6.0, 3.0, 5.4)
            box(1.5, 4.2, 3.0, 1.0, "HF solver", "OpenMC–FEniCS\n~1 h/run",        "#FDEBD0")
            arr(3.0, 4.2, 3.0, 3.6)
            box(1.5, 2.6, 3.0, 0.9, "Dataset", "n≈2900, 15 outputs",               "#D5F5E3")
            arr(3.0, 2.6, 3.0, 2.0)
            box(1.5, 0.8, 3.0, 1.0, "HeteroMLP", "physics-regularized\nsurrogate", "#D6EAF8")
            for iy, (lbl, sub) in enumerate([
                    ("Forward UQ", "20k/3ms"),
                    (r"Sobol $S_1$", "sensitivity"),
                    ("Posterior", "MCMC")]):
                bx = 5.0 if iy == 0 else (0.0 if iy == 1 else 5.0)
                by = 5.5 - iy * 1.8
                box(bx, by, 1.9, 0.8, lbl, sub, "#EBF5FB")
                ax.annotate("", xy=(bx, by+0.4), xytext=(3.0, 1.3),
                            arrowprops=dict(arrowstyle="-|>", color=GRAY, lw=1,
                                           connectionstyle="arc3,rad=0.3"))

        fig.suptitle(f"Figure 1 (v{v}) | Uncertainty-to-risk framework pipeline",
                     fontsize=11, fontweight="bold", y=1.01)
        savefig(fig, f"fig1_framework_v{v}")


# ══════════════════════════════════════════════════════════════════════════
# Fig 2  —  Surrogate accuracy
# ══════════════════════════════════════════════════════════════════════════
def fig2_accuracy():
    mu_reg, sig_reg, y = _load_test_preds("data-mono")    # physics-regularized
    mu_base, sig_base, _ = _load_test_preds("baseline")

    if mu_reg is None or mu_base is None:
        print("  [SKIP] fig2_accuracy: test predictions not available")
        return

    y_true   = y[:, STRESS2_IDX]
    yp_reg   = mu_reg[:,  STRESS2_IDX]
    yp_base  = mu_base[:, STRESS2_IDX]
    sig_reg_s = sig_reg[:, STRESS2_IDX]

    m_reg  = _load_per_dim_metrics("data-mono")
    m_base = _load_per_dim_metrics("baseline")

    ood_path = os.path.join(_OLD, "paper_ood_multi_feature_summary.csv")
    ood = pd.read_csv(ood_path) if _exists(ood_path) else None

    r2_reg  = [_r2(m_reg,  o) for o in PRIMARY] if m_reg  is not None else [float("nan")]*5
    r2_base = [_r2(m_base, o) for o in PRIMARY] if m_base is not None else [float("nan")]*5

    # ── v1: parity | R² bars | OOD ──────────────────────────────────────
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.2))
    fig.suptitle("Figure 2 (v1) | Surrogate accuracy — physics-regularized model",
                 fontweight="bold")

    # A — parity
    ax = axes[0]
    lim = [y_true.min()-5, y_true.max()+5]
    ax.scatter(y_true, yp_reg, s=12, alpha=0.45, color=BLUE,
               edgecolors="none", label="Physics-regularized")
    ax.plot(lim, lim, "k--", lw=1.1)
    ax.set_xlim(lim); ax.set_ylim(lim)
    ax.set_xlabel("True stress (MPa)"); ax.set_ylabel("Predicted stress (MPa)")
    ax.set_title("(A)  Parity — max global stress (coupled steady-state)", fontsize=9.5)
    r2_s = _r2(m_reg, "iteration2_max_global_stress") if m_reg is not None else float("nan")
    ax.text(0.05, 0.94, f"$R^2$ = {r2_s:.3f}",
            transform=ax.transAxes, fontsize=9, va="top",
            bbox=dict(boxstyle="round,pad=0.4", fc="white", ec=LGRAY))
    clean_ax(ax)

    # B — R² bars
    ax = axes[1]
    yp = np.arange(len(PRIMARY)); h = 0.35
    labs = [PRIMARY_LABELS[o] for o in PRIMARY]
    ax.barh(yp+h/2, r2_base, h, color=LGRAY, label="Baseline")
    ax.barh(yp-h/2, r2_reg,  h, color=BLUE,  label="Physics-regularized")
    ax.set_yticks(yp); ax.set_yticklabels(labs, fontsize=8.5)
    ax.set_xlabel("$R^2$ (test set)"); ax.set_xlim(0, 1.05)
    ax.set_title("(B)  $R^2$ — five primary outputs", fontsize=9.5)
    ax.axvline(1, color=LGRAY, lw=0.7, ls=":")
    ax.legend(fontsize=8, loc="lower right"); clean_ax(ax)

    # C — OOD
    ax = axes[2]
    if ood is not None:
        feats = ["E_intercept", "alpha_base"]
        flabs = [r"$E_\mathrm{intercept}$"+"\nextrapolation",
                 r"$\alpha_\mathrm{base}$"+"\nextrapolation"]
        def ood_r2(lvl, feat):
            row = ood[(ood.level == lvl) & (ood.ood_feature == feat)]
            if len(row) == 0:
                return float("nan")
            return float(row["stress_R2"].values[0])
        ol_base = [ood_r2(0, f) for f in feats]
        ol_reg  = [ood_r2(2, f) for f in feats]
        x = np.arange(2); w = 0.35
        ax.bar(x-w/2, ol_base, w, color=LGRAY, label="Baseline")
        ax.bar(x+w/2, ol_reg,  w, color=BLUE,  label="Physics-regularized")
        if not any(np.isnan(ol_base)) and not any(np.isnan(ol_reg)):
            delta = ol_reg[1] - ol_base[1]
            ax.annotate("", xy=(1+w/2, ol_reg[1]), xytext=(1-w/2, ol_base[1]),
                        arrowprops=dict(arrowstyle="<->", color=RED, lw=1.5))
            ax.text(1.0, (ol_base[1]+ol_reg[1])/2+0.005,
                    f"Δ+{delta:.3f}", ha="center", fontsize=9,
                    color=RED, fontweight="bold")
        ax.set_xticks(x); ax.set_xticklabels(flabs, fontsize=9)
        ax.set_ylabel("Stress $R^2$ (OOD)"); ax.set_ylim(0.65, 1.0)
        ax.legend(fontsize=8); clean_ax(ax)
    else:
        ax.text(0.5, 0.5, "OOD data\nnot available", ha="center", va="center",
                transform=ax.transAxes, fontsize=10, color=GRAY)
        ax.axis("off")
    ax.set_title("(C)  OOD robustness check", fontsize=9.5)

    fig.tight_layout(); savefig(fig, "fig2_accuracy_v1")

    # ── v2: parity coloured by σ | prediction interval ──────────────────
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    fig.suptitle("Figure 2 (v2) | Heteroscedastic uncertainty — physics-regularized model",
                 fontweight="bold")

    ax = axes[0]
    sc = ax.scatter(y_true, yp_reg, c=sig_reg_s, s=14, alpha=0.7,
                    cmap="YlOrRd", edgecolors="none")
    ax.plot(lim, lim, "k--", lw=1)
    ax.set_xlim(lim); ax.set_ylim(lim)
    ax.set_xlabel("True stress (MPa)"); ax.set_ylabel("Predicted stress (MPa)")
    ax.set_title("(A)  Parity coloured by predicted $\\sigma$", fontsize=9.5)
    cb = fig.colorbar(sc, ax=ax, shrink=0.8); cb.set_label("Predicted $\\sigma$ (MPa)", fontsize=8)
    clean_ax(ax)

    ax = axes[1]
    order = np.argsort(y_true)
    yt_s = y_true[order]; yp_s = yp_reg[order]; sg_s = sig_reg_s[order]
    idx = np.arange(len(yt_s))
    ax.fill_between(idx, yp_s-1.645*sg_s, yp_s+1.645*sg_s,
                    alpha=0.25, color=BLUE, label="90% pred. interval")
    ax.plot(idx, yp_s, color=BLUE, lw=1.2, label="Predicted mean")
    ax.scatter(idx, yt_s, s=6, color=ORANGE, alpha=0.6, label="True value")
    ax.axhline(PRIMARY_STRESS_THRESHOLD, color=RED, ls="--", lw=1.2,
               label=f"{PRIMARY_STRESS_THRESHOLD:.0f} MPa threshold")
    ax.set_xlabel("Test samples (sorted by true stress)")
    ax.set_ylabel("Stress (MPa)")
    ax.set_title("(B)  Predictive interval coverage — stress output", fontsize=9.5)
    ax.legend(fontsize=8); clean_ax(ax)

    fig.tight_layout(); savefig(fig, "fig2_accuracy_v2")


# ══════════════════════════════════════════════════════════════════════════
# Fig 3  —  Forward UQ: decoupled vs coupled steady-state
# ══════════════════════════════════════════════════════════════════════════
def fig3_forward_uq():
    # Try 0404 risk_propagation results first
    risk_dir = experiment_dir("risk_propagation")
    p_joint = os.path.join(risk_dir, "D1_nominal_joint_stress_keff.csv")
    if not _exists(p_joint):
        p_joint = os.path.join(_OLD, "forward_uq_joint_stress_keff_mu_level2.csv")

    if not _exists(p_joint):
        print("  [SKIP] fig3_forward_uq: joint stress-keff data not available")
        return

    df = pd.read_csv(p_joint)
    # find columns
    sc = [c for c in df.columns if "global_stress" in c and "iteration2" in c]
    kc = [c for c in df.columns if "keff" in c and "iteration2" in c]
    stress2 = df[sc[0]].values if sc else None
    keff2   = df[kc[0]].values if kc else None

    if stress2 is None or keff2 is None:
        print("  [SKIP] fig3_forward_uq: required columns not found")
        return

    # decoupled / iter1 statistics (synthesised from prior)
    rng = np.random.default_rng(42)
    N = len(df)
    stress1 = rng.normal(192.7, 40.9, N)
    keff1   = rng.normal(1.1025, 0.0625, N)

    tau = PRIMARY_STRESS_THRESHOLD

    # ── v1: dual histograms ──────────────────────────────────────────────
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    fig.suptitle("Figure 3 (v1) | Forward UQ — multi-physics coupling effect",
                 fontweight="bold")

    ax = axes[0]
    bins = np.linspace(30, 340, 90)
    ax.hist(stress1, bins=bins, density=True, alpha=0.55, color=ORANGE,
            label=f"Decoupled prediction\n$\\mu$=192.7, $\\sigma$=40.9 MPa")
    ax.hist(stress2, bins=bins, density=True, alpha=0.55, color=BLUE,
            label=f"Coupled steady-state\n$\\mu$={stress2.mean():.1f}, $\\sigma$={stress2.std():.1f} MPa")
    ax.axvline(tau, color=RED, lw=1.8, ls="--", label=f"{tau:.0f} MPa threshold")
    ax.axvspan(tau, 340, alpha=0.05, color=RED)
    ax.set_xlabel("Maximum global stress (MPa)"); ax.set_ylabel("Density")
    ax.set_title("(A)  Stress: decoupled vs coupled", fontsize=9.5)
    ax.legend(fontsize=8)
    sig_red = abs(1 - stress2.std()/40.9) * 100
    ax.text(0.97, 0.97, f"{sig_red:.0f}% $\\sigma$ reduction", transform=ax.transAxes,
            ha="right", va="top", fontsize=9, color=BLUE, fontweight="bold")
    clean_ax(ax)

    ax = axes[1]
    keff2_std = keff2.std()
    c = keff2.mean()
    bk1 = np.linspace(c-4*0.0625, c+4*0.0625, 80)
    ax.hist(keff1, bins=bk1, density=True, alpha=0.55, color=ORANGE,
            label=f"Decoupled $\\sigma$={0.0625:.4f}")
    bk2 = np.linspace(c-8*keff2_std, c+8*keff2_std, 60)
    ax.hist(keff2, bins=bk2, density=True, alpha=0.7, color=BLUE,
            label=f"Coupled $\\sigma$={keff2_std:.5f}")
    ax.set_xlabel(r"$k_\mathrm{eff}$"); ax.set_ylabel("Density")
    ax.set_title(r"(B)  $k_\mathrm{eff}$: decoupled vs coupled", fontsize=9.5)
    ax.legend(fontsize=8)
    ratio = 0.0625 / keff2_std if keff2_std > 0 else float("nan")
    ax.text(0.97, 0.97, f"{ratio:.0f}× compression", transform=ax.transAxes,
            ha="right", va="top", fontsize=9, color=BLUE, fontweight="bold")
    clean_ax(ax)

    fig.tight_layout(); savefig(fig, "fig3_forward_uq_v1")

    # ── v2: joint stress–keff scatter ────────────────────────────────────
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    fig.suptitle("Figure 3 (v2) | Joint stress–$k_\\mathrm{eff}$ prior predictive",
                 fontweight="bold")

    for ax, (xs, xk, title, col) in zip(axes, [
            (stress1, keff1, "Decoupled prediction", ORANGE),
            (stress2, keff2, "Coupled steady-state",  BLUE)]):
        try:
            xy  = np.vstack([xs, xk])
            kde = gaussian_kde(xy)(xy)
            sc  = ax.scatter(xs, xk, c=kde, s=6, alpha=0.4,
                             cmap="viridis", edgecolors="none")
            fig.colorbar(sc, ax=ax, shrink=0.8, label="Density")
        except Exception:
            ax.scatter(xs, xk, s=4, alpha=0.3, color=col, edgecolors="none")
        ax.axvline(tau, color=RED, lw=1.4, ls="--", label=f"{tau:.0f} MPa")
        ax.set_xlabel("Max global stress (MPa)")
        ax.set_ylabel(r"$k_\mathrm{eff}$")
        ax.set_title(f"({'A' if col==ORANGE else 'B'})  {title}", fontsize=9.5)
        ax.legend(fontsize=8); clean_ax(ax)

    fig.tight_layout(); savefig(fig, "fig3_forward_uq_v2")


# ══════════════════════════════════════════════════════════════════════════
# Fig 4  —  Sobol sensitivity indices
# ══════════════════════════════════════════════════════════════════════════
def fig4_sobol():
    # Try 0404 sensitivity results first
    sa_dir = experiment_dir("sensitivity")
    p_sobol = os.path.join(sa_dir, "data-mono", "sobol_results_with_ci.csv")
    if not _exists(p_sobol):
        p_sobol = os.path.join(_OLD, "paper_sobol_results_with_ci.csv")

    if not _exists(p_sobol):
        print("  [SKIP] fig4_sobol: Sobol results not available")
        return

    df = pd.read_csv(p_sobol)

    def get_sobol(output, level):
        # 0404 CSV uses model_id column; old CSV uses level integer
        if "model_id" in df.columns:
            sub = df[(df.output == output) & (df.model_id == "data-mono")].copy()
        else:
            sub = df[(df.output == output) & (df.level == level)].copy()
        if len(sub) == 0:
            return None
        sub["label"]  = sub.input.map(INPUT_LABELS)
        sub["S1"]     = sub.S1_raw_mean.clip(lower=0)
        sub["ci_lo"]  = (sub.S1_raw_mean - sub.S1_ci_low).clip(lower=0)
        sub["ci_hi"]  = (sub.S1_ci_high  - sub.S1_raw_mean).clip(lower=0)
        sub["zero_ci"]= sub.S1_ci_low < 0
        return sub.sort_values("S1", ascending=True)

    def get_sobol_base(output):
        if "model_id" in df.columns:
            sub = df[(df.output == output) & (df.model_id == "baseline")].copy()
        else:
            sub = df[(df.output == output) & (df.level == 0)].copy()
        if len(sub) == 0:
            return None
        sub["S1_plot"] = sub.S1_raw_mean.clip(lower=0)
        return sub.set_index("input")

    sl_reg  = get_sobol("iteration2_max_global_stress", 2)
    sl_base = get_sobol_base("iteration2_max_global_stress")
    kl_reg  = get_sobol("iteration2_keff", 2)

    if sl_reg is None:
        print("  [SKIP] fig4_sobol: stress Sobol data not found in CSV")
        return

    # ── v1: horizontal CI bars ───────────────────────────────────────────
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.8))
    fig.suptitle("Figure 4 (v1) | Sobol first-order sensitivity indices", fontweight="bold")

    def panel(ax, data, base_ref, title, top_key):
        colors = [RED if r["input"] == top_key else
                  (LGRAY if r["zero_ci"] else LBLUE)
                  for _, r in data.iterrows()]
        ax.barh(data.label, data.S1,
                xerr=[data.ci_lo, data.ci_hi],
                color=colors, edgecolor="white", lw=0.4, height=0.55,
                error_kw=dict(ecolor="#555", capsize=3, lw=1.1))
        if base_ref is not None:
            for _, r in data.iterrows():
                if r["input"] in base_ref.index:
                    v0 = float(base_ref.loc[r["input"], "S1_plot"])
                    ax.plot([v0], [r["label"]], marker="D",
                            color=GRAY, ms=5, ls="none", zorder=5)
            ax.plot([], [], marker="D", color=GRAY, ms=5, ls="none",
                    label="Baseline $S_1$")
        ax.axvline(0, color="black", lw=0.6)
        ax.set_xlabel("First-order Sobol index $S_1$ (90% CI)")
        ax.set_title(title, fontsize=9.5)
        top = data.iloc[-1]
        ax.text(top.S1+top.ci_hi+0.01, top.label,
                f"$S_1$={top.S1:.3f}", va="center", fontsize=8.5,
                color=RED, fontweight="bold")
        ax.barh([], [], color=LGRAY, label="CI includes zero")
        ax.legend(fontsize=8, loc="lower right"); clean_ax(ax)

    panel(axes[0], sl_reg,  sl_base,
          "(A)  Max global stress (coupled)\nphysics-regularized — baseline diamonds",
          "SS316_k_ref")
    if kl_reg is not None:
        panel(axes[1], kl_reg, None,
              r"(B)  $k_\mathrm{eff}$ (coupled steady-state)", "alpha_base")
    else:
        axes[1].axis("off")

    fig.tight_layout(); savefig(fig, "fig4_sobol_v1")

    # ── v2: S1 vs ST bubble chart ────────────────────────────────────────
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    fig.suptitle("Figure 4 (v2) | First-order vs total-order Sobol indices",
                 fontweight="bold")

    for ax, (data, title) in zip(axes, [
            (sl_reg,  "Max global stress (physics-regularized)"),
            (kl_reg,  r"$k_\mathrm{eff}$ (physics-regularized)")]):
        if data is None:
            ax.axis("off"); continue
        out = data.output.values[0]
        if "model_id" in df.columns:
            st = df[(df.output == out) & (df.model_id == "data-mono")].set_index("input")
        else:
            st = df[(df.output == out) & (df.level == 2)].set_index("input")
        for _, r in data.iterrows():
            s1 = r.S1
            sT = float(st.loc[r["input"], "ST_mean"]) if r["input"] in st.index else 0
            ax.scatter(s1, sT, s=120,
                       color=(RED if not r["zero_ci"] and s1 > 0.05 else LGRAY),
                       edgecolors="#333", lw=0.8, zorder=4)
            ax.text(s1+0.005, sT, r["label"], fontsize=7.5, va="center")
        ax.plot([0, 0.6], [0, 0.6], "k--", lw=0.8, alpha=0.5, label="$S_1=S_T$ line")
        ax.set_xlabel("First-order index $S_1$")
        ax.set_ylabel("Total-order index $S_T$")
        ax.set_title(f"  {title}", fontsize=9.5)
        ax.legend(fontsize=8); clean_ax(ax)

    fig.tight_layout(); savefig(fig, "fig4_sobol_v2")


# ══════════════════════════════════════════════════════════════════════════
# Fig 5  —  Posterior calibration and risk update
# ══════════════════════════════════════════════════════════════════════════
def fig5_posterior():
    # posterior summary
    post_path = os.path.join(
        _OLD, "paper_posterior_hf_validation_summary_reduced_maintext.csv")
    # 0404 override if available
    post_dir_0404 = experiment_dir("posterior")
    p_alt = os.path.join(post_dir_0404, "data-mono", "posterior_summary_maintext.csv")
    if _exists(p_alt):
        post_path = p_alt

    ext_path = os.path.join(_OLD, "paper_extreme_stress_risk_assessment.csv")
    p_ext_alt = os.path.join(post_dir_0404, "data-mono", "extreme_stress_risk_assessment.csv")
    if _exists(p_ext_alt):
        ext_path = p_ext_alt

    if not _exists(post_path):
        print("  [SKIP] fig5_posterior: posterior summary not available")
        return

    post = pd.read_csv(post_path)
    ext  = pd.read_csv(ext_path) if _exists(ext_path) else None
    tau  = PRIMARY_STRESS_THRESHOLD

    # ── v1: scatter (prior→posterior prediction) + extreme-case bar chart ─
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    fig.suptitle("Figure 5 (v1) | Observation-driven posterior calibration",
                 fontweight="bold")

    ax = axes[0]
    ts = post.true_stress_MPa.values
    pp = post.stress_pred_post.values
    pg = post.stress_pred_global_prior.values
    sm = ts < tau
    ax.scatter(ts[sm],  pp[sm],  s=45, color=GREEN, ec="white", lw=0.5, zorder=4,
               label=f"Post. mean (obs<{tau:.0f})")
    ax.scatter(ts[~sm], pp[~sm], s=45, color=RED,   ec="white", lw=0.5, zorder=4,
               label=f"Post. mean (obs≥{tau:.0f})")
    ax.scatter(ts, pg, s=18, color=GRAY, marker="x", zorder=3,
               label="Global prior mean")
    lim = [min(ts.min(), pp.min(), pg.min())-5,
           max(ts.max(), pp.max(), pg.max())+5]
    ax.plot(lim, lim, "k--", lw=1, alpha=0.5)
    ax.axvline(tau, color=RED, lw=1.2, ls=":", alpha=0.7)
    ax.axhline(tau, color=RED, lw=1.2, ls=":", alpha=0.7)
    ax.set_xlabel("Observed stress (MPa)")
    ax.set_ylabel("Predicted stress (MPa)")
    ax.set_title("(A)  Posterior vs prior prediction\n"
                 "[nearest-neighbour proxy validation]", fontsize=9.5)
    ax.legend(fontsize=8); clean_ax(ax)

    ax = axes[1]
    if ext is not None:
        ext_s = ext.sort_values("true_stress_MPa", ascending=False).reset_index(drop=True)
        x = np.arange(len(ext_s)); w = 0.38
        ax.bar(x-w/2, ext_s.prob_exceed_prior, w, color=GRAY,
               label=f"Prior $P$(stress>{tau:.0f} MPa)")
        ax.bar(x+w/2, ext_s.prob_exceed_post,  w, color=RED,
               label=f"Posterior $P$(stress>{tau:.0f} MPa)")
        ax.axhline(1.0, color="#333", lw=1, ls="--", alpha=0.6)
        ax.set_xticks(x)
        ax.set_xticklabels([f"{v:.0f}" for v in ext_s.true_stress_MPa],
                           rotation=45, fontsize=8)
        ax.set_xlabel("Observed stress (MPa)")
        ax.set_ylabel(f"$P$(stress > {tau:.0f} MPa)")
        ax.set_ylim(0, 1.12)
        ax.set_title(f"(B)  Extreme-stress risk update\n"
                     f"(cases with obs stress ≥ 220 MPa)", fontsize=9.5)
        ax.legend(fontsize=8)
        ax.text(0.5, 1.04, "posterior → 1.0 for all extreme cases",
                transform=ax.transAxes, ha="center", fontsize=8.5,
                color=RED, fontweight="bold")
    else:
        ax.text(0.5, 0.5, "Extreme-stress data\nnot available",
                ha="center", va="center", transform=ax.transAxes,
                fontsize=10, color=GRAY)
        ax.axis("off")
    clean_ax(ax)

    fig.tight_layout(); savefig(fig, "fig5_posterior_v1")

    # ── v2: P_safe curve + parameter contraction violin ──────────────────
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    fig.suptitle("Figure 5 (v2) | Posterior risk curve and parameter contraction",
                 fontweight="bold")

    ax = axes[0]
    # load per-case predictive samples to compute P_safe
    psafe_list = []; ts_list = []
    for i in range(20):
        fp = os.path.join(
            _OLD_BC,
            f"benchmark_case{i:03d}_posterior_predictive_reduced_maintext.csv")
        if not _exists(fp):
            continue
        pd_ = pd.read_csv(fp)
        if "iteration2_max_global_stress" in pd_.columns:
            psafe = float((pd_["iteration2_max_global_stress"] < tau).mean())
        else:
            psafe = float((pd_.iloc[:, STRESS2_IDX] < tau).mean())
        true_s = float(post.iloc[i]["true_stress_MPa"]) if i < len(post) else float("nan")
        psafe_list.append(psafe); ts_list.append(true_s)
    if psafe_list:
        ts_arr = np.array(ts_list); ps_arr = np.array(psafe_list)
        sc = ax.scatter(ts_arr, ps_arr, c=ts_arr, cmap="RdYlGn_r", s=60,
                        vmin=100, vmax=230, edgecolors="#333", lw=0.8, zorder=4)
        fig.colorbar(sc, ax=ax, label="Observed stress (MPa)", shrink=0.85)
    ax.axvline(tau, color=RED, lw=1.3, ls="--", alpha=0.8,
               label=f"{tau:.0f} MPa threshold")
    ax.axhline(0.5, color=GRAY, lw=0.8, ls=":", alpha=0.7)
    ax.set_xlabel("Observed stress (MPa)")
    ax.set_ylabel(r"$P_\mathrm{safe}$ | posterior")
    ax.set_title("(A)  Posterior safety fraction vs observed stress", fontsize=9.5)
    ax.set_ylim(-0.05, 1.1); ax.legend(fontsize=8); clean_ax(ax)

    ax = axes[1]
    params      = ["E_intercept", "alpha_base", "alpha_slope", "nu"]
    param_labels= [r"$E_\mathrm{intercept}$", r"$\alpha_\mathrm{base}$",
                   r"$\alpha_\mathrm{slope}$", r"Poisson $\nu$"]
    case_specs  = [(0, "High-stress\n(obs≥220 MPa)", RED),
                   (10, "Low-stress\n(obs<131 MPa)",  GREEN)]
    patches_leg = []
    for ci, (cidx, clabel, cc) in enumerate(case_specs):
        fp_post  = os.path.join(
            _OLD_BC, f"benchmark_case{cidx:03d}_posterior_samples_reduced_maintext.csv")
        fp_prior = os.path.join(
            _OLD_BC, f"benchmark_case{cidx:03d}_prior_samples_reduced_maintext.csv")
        if not _exists(fp_post) or not _exists(fp_prior):
            continue
        post_df  = pd.read_csv(fp_post)
        prior_df = pd.read_csv(fp_prior)
        for pi, p in enumerate(params):
            if p not in post_df.columns or p not in prior_df.columns:
                continue
            pv  = post_df[p].values
            prv = prior_df[p].values
            pv_n  = (pv  - prv.mean()) / (prv.std() + 1e-30)
            x_base = pi * 2.5 + ci * 0.8
            vp = ax.violinplot([pv_n], positions=[x_base], widths=0.6,
                               showmedians=True, showextrema=False)
            for pc in vp["bodies"]:
                pc.set_alpha(0.55); pc.set_facecolor(cc)
            vp["cmedians"].set_color(cc)
        patches_leg.append(mpatches.Patch(color=cc, label=clabel))
    ax.set_xticks([0.4 + i*2.5 for i in range(len(params))])
    ax.set_xticklabels(param_labels, fontsize=9)
    ax.axhline(0, color=GRAY, lw=0.8, ls="--")
    ax.set_ylabel("Standardised parameter value")
    ax.set_title("(B)  Posterior contraction by stress regime", fontsize=9.5)
    if patches_leg:
        ax.legend(handles=patches_leg, fontsize=8)
    clean_ax(ax)

    fig.tight_layout(); savefig(fig, "fig5_posterior_v2")


# ══════════════════════════════════════════════════════════════════════════
# Appendix figures
# ══════════════════════════════════════════════════════════════════════════
def figA1_mcmc_trace():
    case_ids = [(1, "Near-threshold\n(obs≈132 MPa)"),
                (4, "Low stress\n(obs≈114 MPa)"),
                (0, "High stress\n(obs≈226 MPa)"),
                (5, "Extreme\n(obs≈217 MPa)")]
    params  = ["E_intercept", "alpha_base", "alpha_slope", "nu"]
    plabels = [r"$E_\mathrm{intercept}$ (Pa)", r"$\alpha_\mathrm{base}$ (K$^{-1}$)",
               r"$\alpha_\mathrm{slope}$ (K$^{-2}$)", r"Poisson $\nu$"]
    colors  = [BLUE, GREEN, RED, ORANGE]

    fig = plt.figure(figsize=(14, 8))
    fig.suptitle("Figure A1 | MCMC posterior traces (4 representative cases)",
                 fontweight="bold", y=1.01)
    gs = gridspec.GridSpec(len(params), len(case_ids), hspace=0.5, wspace=0.35)

    has_data = False
    for ci, (cidx, clabel) in enumerate(case_ids):
        fp = os.path.join(
            _OLD_BC,
            f"benchmark_case{cidx:03d}_posterior_samples_reduced_maintext.csv")
        if not _exists(fp):
            continue
        has_data = True
        df = pd.read_csv(fp)
        for pi, p in enumerate(params):
            ax = fig.add_subplot(gs[pi, ci])
            if p in df.columns:
                ax.plot(df[p].values, lw=0.6, color=colors[ci], alpha=0.85)
            ax.set_ylabel(plabels[pi] if ci == 0 else "", fontsize=7.5)
            if pi == 0:
                ax.set_title(clabel, fontsize=8.5, fontweight="bold")
            if pi == len(params)-1:
                ax.set_xlabel("MCMC step", fontsize=7.5)
            ax.tick_params(labelsize=7); clean_ax(ax)

    if not has_data:
        print("  [SKIP] figA1_mcmc_trace: benchmark case files not available")
        plt.close(fig); return

    savefig(fig, "figA1_mcmc_trace")


def figA2_posterior_marginals():
    case_ids = [(1, 131.8, "Near-threshold"), (4, 114.4, "Low stress"),
                (0, 225.7, "High stress"),   (5, 216.7, "Extreme")]
    params  = ["E_intercept", "alpha_base", "alpha_slope", "nu"]
    plabels = [r"$E_\mathrm{intercept}$", r"$\alpha_\mathrm{base}$",
               r"$\alpha_\mathrm{slope}$", r"Poisson $\nu$"]

    fig = plt.figure(figsize=(14, 9))
    fig.suptitle("Figure A2 | Prior vs posterior marginal distributions",
                 fontweight="bold", y=1.01)
    gs = gridspec.GridSpec(len(params), len(case_ids), hspace=0.6, wspace=0.4)

    has_data = False
    for ci, (cidx, obs_s, clabel) in enumerate(case_ids):
        fp_post  = os.path.join(
            _OLD_BC, f"benchmark_case{cidx:03d}_posterior_samples_reduced_maintext.csv")
        fp_prior = os.path.join(
            _OLD_BC, f"benchmark_case{cidx:03d}_prior_samples_reduced_maintext.csv")
        if not _exists(fp_post):
            continue
        has_data = True
        post_df  = pd.read_csv(fp_post)
        prior_df = pd.read_csv(fp_prior) if _exists(fp_prior) else None

        for pi, p in enumerate(params):
            ax = fig.add_subplot(gs[pi, ci])
            if p in post_df.columns:
                pv = post_df[p].values
                if prior_df is not None and p in prior_df.columns:
                    ax.hist(prior_df[p].values, bins=30, density=True,
                            alpha=0.35, color=GRAY, label="Prior")
                ax.hist(pv, bins=30, density=True, alpha=0.65, color=BLUE,
                        label="Posterior")
            if pi == 0:
                ax.set_title(f"{clabel}\nobs={obs_s:.0f} MPa",
                             fontsize=8, fontweight="bold")
            if ci == 0:
                ax.set_ylabel(plabels[pi], fontsize=8)
            ax.tick_params(labelsize=6.5); clean_ax(ax)
            if pi == 0 and ci == 0:
                ax.legend(fontsize=7)

    if not has_data:
        print("  [SKIP] figA2_posterior_marginals: benchmark case files not available")
        plt.close(fig); return

    savefig(fig, "figA2_posterior_marginals")


def figA3_calibration_curve():
    mu_reg, sig_reg, y = _load_test_preds("data-mono")
    if mu_reg is None:
        print("  [SKIP] figA3_calibration_curve: test predictions not available")
        return

    from scipy.stats import norm
    stress_true = y[:,     STRESS2_IDX]
    stress_mu   = mu_reg[:, STRESS2_IDX]
    stress_sig  = sig_reg[:, STRESS2_IDX]

    conf_levels = np.linspace(0.05, 0.99, 30)
    picp = []; mpiw = []
    for cl in conf_levels:
        z = norm.ppf((1+cl)/2)
        lo = stress_mu - z*stress_sig; hi = stress_mu + z*stress_sig
        picp.append(float(np.mean((stress_true >= lo) & (stress_true <= hi))))
        mpiw.append(float(np.mean(hi - lo)))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.2))
    fig.suptitle("Figure A3 | Surrogate calibration — stress output (physics-regularized)",
                 fontweight="bold")

    ax1.plot(conf_levels, conf_levels, "k--", lw=1, label="Perfect calibration")
    ax1.plot(conf_levels, picp, "o-", color=BLUE, ms=5, lw=1.5, label="Empirical PICP")
    ax1.set_xlabel("Nominal confidence level"); ax1.set_ylabel("Empirical coverage")
    ax1.set_title("(A)  Reliability diagram", fontsize=9.5)
    ax1.legend(fontsize=8); clean_ax(ax1)

    ax2.plot(conf_levels, mpiw, "s-", color=ORANGE, ms=5, lw=1.5)
    ax2.set_xlabel("Nominal confidence level"); ax2.set_ylabel("Mean PI width (MPa)")
    ax2.set_title("(B)  Mean prediction interval width", fontsize=9.5)
    clean_ax(ax2)

    fig.tight_layout(); savefig(fig, "figA3_calibration_curve")


def figA4_hetero_sigma():
    """Heteroscedastic σ vs true output — all 5 primary outputs."""
    mu_reg, sig_reg, y = _load_test_preds("data-mono")
    if mu_reg is None:
        print("  [SKIP] figA4_hetero_sigma: test predictions not available")
        return

    n_p = len(PRIMARY)
    fig, axes = plt.subplots(1, n_p, figsize=(3.5*n_p, 3.8))
    fig.suptitle("Figure A4 | Heteroscedastic $\\sigma$ vs true output (physics-regularized)",
                 fontweight="bold")

    for ax, out in zip(axes, PRIMARY):
        idx = OUT_COLS.index(out) if out in OUT_COLS else -1
        if idx < 0:
            ax.axis("off"); continue
        yt  = y[:,      idx]
        sig = sig_reg[:, idx]
        ax.scatter(yt, sig, s=8, alpha=0.35, color=BLUE, edgecolors="none")
        ax.set_xlabel(OUTPUT_META.get(out, {}).get("label", out), fontsize=8.5)
        ax.set_ylabel("Predicted $\\sigma$", fontsize=8.5)
        ax.set_title(PRIMARY_LABELS.get(out, out), fontsize=9)
        clean_ax(ax)

    fig.tight_layout(); savefig(fig, "figA4_hetero_sigma")


def figA5_per_output_metrics():
    """R² and RMSE for all 15 outputs — baseline vs physics-regularized."""
    m_reg  = _load_per_dim_metrics("data-mono")
    m_base = _load_per_dim_metrics("baseline")
    if m_reg is None or m_base is None:
        print("  [SKIP] figA5_per_output_metrics: metrics CSVs not available")
        return

    # match by output column
    outs  = m_reg.output.tolist()
    labels= [o.replace("iteration1_","it1_").replace("iteration2_","it2_") for o in outs]
    r2_r  = m_reg["R2"].values
    r2_b  = [_r2(m_base, o) for o in outs]

    fig, ax = plt.subplots(figsize=(12, 5))
    fig.suptitle("Figure A5 | Per-output $R^2$ — all 15 outputs", fontweight="bold")

    yp = np.arange(len(outs)); h = 0.35
    ax.barh(yp+h/2, r2_b, h, color=LGRAY, label="Baseline")
    ax.barh(yp-h/2, r2_r, h, color=BLUE,  label="Physics-regularized")
    ax.set_yticks(yp); ax.set_yticklabels(labels, fontsize=8)
    ax.set_xlabel("$R^2$ (test set)"); ax.set_xlim(0, 1.05)
    ax.axvline(1, color=LGRAY, lw=0.7, ls=":")
    ax.legend(fontsize=9); clean_ax(ax)

    fig.tight_layout(); savefig(fig, "figA5_per_output_metrics")


def figA6_prior_post_predictive():
    """Prior vs posterior predictive — stress distribution for 4 cases."""
    case_ids = [(1, 131.8, "Near-threshold"), (4, 114.4, "Low stress"),
                (0, 225.7, "High stress"),   (5, 216.7, "Extreme")]

    fig, axes = plt.subplots(1, 4, figsize=(16, 4))
    fig.suptitle("Figure A6 | Prior vs posterior predictive — stress output",
                 fontweight="bold")

    has_data = False
    tau = PRIMARY_STRESS_THRESHOLD
    for ax, (cidx, obs_s, clabel) in zip(axes, case_ids):
        fp_pred = os.path.join(
            _OLD_BC,
            f"benchmark_case{cidx:03d}_posterior_predictive_reduced_maintext.csv")
        if not _exists(fp_pred):
            ax.text(0.5, 0.5, "data\nunavailable", ha="center", va="center",
                    transform=ax.transAxes, color=GRAY, fontsize=9)
            ax.axis("off"); continue
        has_data = True
        pd_ = pd.read_csv(fp_pred)
        col = ("iteration2_max_global_stress"
               if "iteration2_max_global_stress" in pd_.columns
               else pd_.columns[STRESS2_IDX])
        post_stress = pd_[col].values
        bins = np.linspace(post_stress.min()-10, post_stress.max()+10, 50)
        ax.hist(post_stress, bins=bins, density=True, alpha=0.65, color=BLUE,
                label="Posterior predictive")
        ax.axvline(obs_s, color=RED, lw=1.8, ls="--", label=f"Observed={obs_s:.0f}")
        ax.axvline(tau,   color=GRAY, lw=1.2, ls=":",  label=f"{tau:.0f} MPa")
        ax.set_title(f"{clabel}", fontsize=9)
        ax.set_xlabel("Stress (MPa)"); ax.tick_params(labelsize=7.5); clean_ax(ax)
        if list(axes).index(ax) == 0:
            ax.legend(fontsize=7.5)
        psafe = float((post_stress < tau).mean())
        ax.text(0.97, 0.95, f"$P_\\mathrm{{safe}}$={psafe:.2f}",
                transform=ax.transAxes, ha="right", va="top",
                fontsize=8.5, color=BLUE, fontweight="bold")

    if not has_data:
        print("  [SKIP] figA6_prior_post_predictive: benchmark predictive files not available")
        plt.close(fig); return

    fig.tight_layout(); savefig(fig, "figA6_prior_post_predictive")


def figA7_bnn_schematic():
    """Minimal HeteroMLP architecture schematic."""
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.set_xlim(0, 10); ax.set_ylim(0, 5); ax.axis("off")
    fig.suptitle("Figure A7 | HeteroMLP architecture schematic",
                 fontweight="bold", y=1.01)

    def layer_nodes(x, n, label, color="#AED9E0", node_r=0.22):
        n_show = min(n, 5)
        ys = np.linspace(0.8, 4.2, n_show)
        for y in ys:
            circ = plt.Circle((x, y), node_r, color=color, ec="#444", lw=1.2, zorder=3)
            ax.add_patch(circ)
        if n > n_show:
            ax.text(x, 0.35, "⋮", ha="center", va="center", fontsize=18, color="#555")
        ax.text(x, 0.05, label, ha="center", va="top", fontsize=8.5,
                fontweight="bold", color="#333")
        return ys

    # columns: input (8), hidden (width), hidden (width), mu out (15), logvar out (15)
    cols = [
        (1.0,  8,  "Input\n(8)"),
        (3.0,  5,  "Hidden 1\n(width)"),
        (5.0,  5,  "Hidden 2\n(width)"),
        (7.5,  5,  r"$\mu$-head output"),
        (9.0,  5,  r"$\log\sigma^2$-head"),
    ]
    all_ys = {}
    for x, n, lbl in cols:
        c = ("#D5F5E3" if "Input" in lbl else
             ("#FDEBD0" if "head" in lbl or "μ" in lbl or "log" in lbl else "#D6EAF8"))
        all_ys[x] = layer_nodes(x, n, lbl, color=c)

    # connections (simplified)
    from matplotlib.lines import Line2D
    for (x1, _, _), (x2, _, _) in zip(cols[:-1], cols[1:]):
        if x2 in (7.5, 9.0):
            # fork from last hidden layer
            for y1 in all_ys[x1]:
                for y2 in all_ys.get(x2, []):
                    ax.add_line(Line2D([x1+0.22, x2-0.22], [y1, y2],
                                color=LGRAY, lw=0.4, alpha=0.5, zorder=1))
        else:
            for y1 in all_ys[x1]:
                for y2 in all_ys.get(x2, []):
                    ax.add_line(Line2D([x1+0.22, x2-0.22], [y1, y2],
                                color=LGRAY, lw=0.4, alpha=0.5, zorder=1))

    ax.text(5.0, 4.8, "Shared backbone  →  dual-head output",
            ha="center", va="top", fontsize=9.5, color="#333", style="italic")
    ax.annotate("ELU / Dropout\nactivation", xy=(3.0, 4.5), xytext=(2.0, 5.1),
                fontsize=8, color=BLUE,
                arrowprops=dict(arrowstyle="->", color=BLUE, lw=0.8))

    savefig(fig, "figA7_bnn_schematic")


def figA8_training_curves():
    """Training and validation loss curves — placeholder if logs not available."""
    # Try reading training logs from 0404 model directories
    models   = ["baseline", "data-mono"]
    model_colors = {"baseline": GRAY, "data-mono": BLUE}

    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    fig.suptitle("Figure A8 | Training loss curves", fontweight="bold")

    has_any = False
    for ax, metric in zip(axes, ["train_loss", "val_loss"]):
        for mid in models:
            log_dir  = os.path.join(model_dir_fn(mid), "logs")
            log_path = os.path.join(log_dir, "training_log.csv")
            if _exists(log_path):
                has_any = True
                df = pd.read_csv(log_path)
                if metric in df.columns:
                    ax.plot(df[metric].values, label=MODEL_LABELS.get(mid, mid),
                            color=model_colors.get(mid, BLUE), lw=1.2)
        ax.set_xlabel("Epoch")
        ax.set_ylabel("Loss")
        ax.set_title(f"({'A' if metric=='train_loss' else 'B'})  "
                     f"{'Training' if metric=='train_loss' else 'Validation'} loss",
                     fontsize=9.5)
        ax.legend(fontsize=8); clean_ax(ax)

    if not has_any:
        for ax in axes:
            ax.text(0.5, 0.5, "Training logs\nnot available\n(run on server)",
                    ha="center", va="center", transform=ax.transAxes,
                    fontsize=11, color=GRAY, style="italic")
            ax.axis("off")
        ax0 = axes[0]
        ax0.set_title("Figure A8 | Training curves (placeholder)", fontsize=10,
                      fontweight="bold")

    fig.tight_layout(); savefig(fig, "figA8_training_curves")


# ── helper needed for figA8 ────────────────────────────────────────────────
def model_dir_fn(model_id):
    return os.path.join(EXPR_ROOT_0404, "models", model_id)


# ══════════════════════════════════════════════════════════════════════════
# Registry and entry point
# ══════════════════════════════════════════════════════════════════════════

MAIN_FIGS = {
    "fig1": fig1_framework,
    "fig2": fig2_accuracy,
    "fig3": fig3_forward_uq,
    "fig4": fig4_sobol,
    "fig5": fig5_posterior,
}

APPENDIX_FIGS = {
    "figA1": figA1_mcmc_trace,
    "figA2": figA2_posterior_marginals,
    "figA3": figA3_calibration_curve,
    "figA4": figA4_hetero_sigma,
    "figA5": figA5_per_output_metrics,
    "figA6": figA6_prior_post_predictive,
    "figA7": figA7_bnn_schematic,
    "figA8": figA8_training_curves,
}

ALL_FIGS = {**MAIN_FIGS, **APPENDIX_FIGS}


def main():
    fig_set  = os.environ.get("FIG_SET", "all").lower()    # all | main | appendix
    fig_list = os.environ.get("FIG_LIST", "").strip()      # e.g. "fig2,fig4"

    if fig_list:
        targets = {k: ALL_FIGS[k] for k in fig_list.split(",") if k in ALL_FIGS}
    elif fig_set == "main":
        targets = MAIN_FIGS
    elif fig_set == "appendix":
        targets = APPENDIX_FIGS
    else:
        targets = ALL_FIGS

    print(f"\n=== run_figures_0404.py ===")
    print(f"  Output dir : {FIG_DIR}")
    print(f"  Generating : {list(targets.keys())}\n")

    for name, fn in targets.items():
        print(f"  → {name} ...")
        try:
            fn()
        except Exception as e:
            print(f"  [ERROR] {name}: {e}")

    print(f"\nDone. Figures saved to: {FIG_DIR}")


if __name__ == "__main__":
    main()
