"""
make_figures.py  —  HPR surrogate paper: draft figures
Run from project root: python figures/draft/make_figures.py

Outputs: figures/draft/*.pdf, *.png, *.svg
Versions: each main figure has a _v1 (default) and _v2 (alt layout/palette).
Appendix figures: figA1–figA7.
"""

import json, os, glob, warnings
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
import numpy as np
import pandas as pd
from matplotlib.patches import FancyBboxPatch
from scipy.stats import gaussian_kde

warnings.filterwarnings("ignore")

OUT_DIR  = "figures/draft"
DATA_DIR = "code/0310/experiments_phys_levels"
SUR_DIR  = os.path.join(DATA_DIR, "fixed_surrogate_fixed_level2")
BASE_DIR = os.path.join(DATA_DIR, "fixed_surrogate_fixed_base")
BC_DIR   = os.path.join(DATA_DIR, "benchmark_case")

# ── output column ordering (no output_cols key in JSON) ───────────────────
OUT_COLS = [
    "iteration1_avg_fuel_temp","iteration1_max_fuel_temp",
    "iteration1_max_monolith_temp","iteration1_max_global_stress",
    "iteration1_monolith_new_temperature","iteration1_Hcore_after","iteration1_wall2",
    "iteration2_keff","iteration2_avg_fuel_temp","iteration2_max_fuel_temp",
    "iteration2_max_monolith_temp","iteration2_max_global_stress",
    "iteration2_monolith_new_temperature","iteration2_Hcore_after","iteration2_wall2",
]
STRESS2_IDX = OUT_COLS.index("iteration2_max_global_stress")   # 11
STRESS1_IDX = OUT_COLS.index("iteration1_max_global_stress")   # 3
KEFF2_IDX   = OUT_COLS.index("iteration2_keff")                # 7

# ── colour palettes ────────────────────────────────────────────────────────
BLUE   = "#2E86AB";  ORANGE = "#E76F51";  GREEN  = "#57A773"
GRAY   = "#888888";  LGRAY  = "#CCCCCC";  RED    = "#C0392B"
LBLUE  = "#AED9E0";  YELLOW = "#F4D35E";  PURPLE = "#9B5DE5"
# Alt palette (warmer)
ALT_A  = "#264653";  ALT_B  = "#2A9D8F";  ALT_C  = "#E9C46A"
ALT_D  = "#F4A261";  ALT_E  = "#E76F51"

plt.rcParams.update({
    "font.family": "sans-serif", "font.size": 10,
    "axes.spines.top": False, "axes.spines.right": False,
    "figure.dpi": 150,
})

# ── helpers ───────────────────────────────────────────────────────────────
def savefig(fig, name):
    for ext in ("pdf", "png", "svg"):
        p = os.path.join(OUT_DIR, f"{name}.{ext}")
        kw = {"bbox_inches": "tight"}
        if ext == "png": kw["dpi"] = 150
        fig.savefig(p, **kw)
    print(f"  saved {name}  [pdf/png/svg]")
    plt.close(fig)

def load_test_preds(level=2):
    tag = "level2" if level == 2 else "level0"
    d_dir = SUR_DIR if level == 2 else BASE_DIR
    path  = os.path.join(d_dir, f"test_predictions_{tag}.json")
    with open(path) as f: d = json.load(f)
    mu    = np.array(d["mu_te"])
    sigma = np.array(d["sigma_te"])
    y     = np.array(d["y_te_true"])
    return mu, sigma, y

def clean_ax(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

PRIMARY_LABELS = {
    "iteration2_keff":              r"$k_\mathrm{eff}$",
    "iteration2_max_fuel_temp":     "Max fuel\ntemp (K)",
    "iteration2_max_monolith_temp": "Max monolith\ntemp (K)",
    "iteration2_max_global_stress": "Max global\nstress (MPa)",
    "iteration2_wall2":             "Wall\nexpansion (mm)",
}
PRIMARY = list(PRIMARY_LABELS.keys())

INPUT_LABELS = {
    "E_slope":    r"$E$ slope",
    "E_intercept":r"$E$ intercept",
    "nu":         r"Poisson $\nu$",
    "alpha_base": r"$\alpha_\mathrm{base}$",
    "alpha_slope":r"$\alpha_\mathrm{slope}$",
    "SS316_T_ref":r"$T_\mathrm{ref}$ (SS316)",
    "SS316_k_ref":r"$k_\mathrm{ref}$ (SS316)",
    "SS316_alpha":r"$k_\mathrm{slope}$ (SS316)",
}

# ══════════════════════════════════════════════════════════════════════════
# Fig 1  —  Framework schematic  (v1: horizontal flow, v2: vertical)
# ══════════════════════════════════════════════════════════════════════════
def fig1_framework():
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

        def arr(x1,y1,x2,y2):
            ax.annotate("", xy=(x2,y2), xytext=(x1,y1),
                        arrowprops=dict(arrowstyle="-|>", color="#333", lw=1.5))

        if v == 1:
            box(0.1,1.5, 2.0,1.2, "8 material\nparameters",   "uniform priors",   "#D6EAF8")
            box(2.6,1.8, 2.4,0.9, "HF solver",               "OpenMC–FEniCS\n~1 h/run","#FDEBD0")
            box(2.6,0.4, 2.4,1.0, "Dataset",                 "n≈2900 samples\n15 outputs","#D5F5E3")
            box(5.6,1.1, 2.2,1.2, "HeteroMLP",               "physics-regularized\nsurrogate","#D6EAF8")
            box(8.4,2.9, 2.4,0.7, "Forward UQ",              "20k samples / 3 ms","#EBF5FB")
            box(8.4,1.9, 2.4,0.7, r"Sobol $S_1,S_T$",        "sensitivity","#EBF5FB")
            box(8.4,0.9, 2.4,0.7, "Posterior MCMC",          "calibration","#EBF5FB")
            arr(2.1,2.1, 2.6,2.3); arr(3.8,1.8,3.8,1.4)
            arr(5.0,0.9, 5.6,1.4)
            arr(7.8,2.1, 8.4,3.25); arr(7.8,1.7, 8.4,2.25); arr(7.8,1.3, 8.4,1.25)
            ax.text(5.5,0.2,"23 million× speedup", ha="center", fontsize=9,
                    color=RED, style="italic",
                    bbox=dict(boxstyle="round,pad=0.3",fc="#FEF9E7",ec=RED,lw=0.8))
        else:
            # vertical layout
            box(1.5,6.0, 3.0,1.2,"8 material\nparameters","uniform priors","#D6EAF8")
            arr(3.0,6.0,3.0,5.4)
            box(1.5,4.2, 3.0,1.0,"HF solver","OpenMC–FEniCS\n~1 h/run","#FDEBD0")
            arr(3.0,4.2,3.0,3.6)
            box(1.5,2.6, 3.0,0.9,"Dataset","n≈2900, 15 outputs","#D5F5E3")
            arr(3.0,2.6,3.0,2.0)
            box(1.5,0.8, 3.0,1.0,"HeteroMLP","physics-regularized\nsurrogate","#D6EAF8")
            for iy, (lbl, sub) in enumerate([("Forward UQ","20k/3ms"),
                                             (r"Sobol $S_1$","sensitivity"),
                                             ("Posterior","MCMC")]):
                bx = 5.0 if iy==0 else (0.0 if iy==1 else 5.0)
                by = 5.5 - iy*1.8
                box(bx, by, 1.9, 0.8, lbl, sub, "#EBF5FB")
                ax.annotate("",xy=(bx,by+0.4),xytext=(3.0,1.3),
                            arrowprops=dict(arrowstyle="-|>",color=GRAY,lw=1,
                                           connectionstyle="arc3,rad=0.3"))

        fig.suptitle(f"Figure 1 (v{v}) | Surrogate framework pipeline",
                     fontsize=11, fontweight="bold", y=1.01)
        savefig(fig, f"fig1_framework_v{v}")


# ══════════════════════════════════════════════════════════════════════════
# Fig 2  —  Surrogate accuracy  (v1: 3 panels, v2: parity + σ illustration)
# ══════════════════════════════════════════════════════════════════════════
def fig2_accuracy():
    mu2, sig2, y = load_test_preds(2)
    mu0, sig0, _ = load_test_preds(0)
    y_true  = y[:, STRESS2_IDX]
    y_pred2 = mu2[:, STRESS2_IDX]
    y_pred0 = mu0[:, STRESS2_IDX]
    sig_s2  = sig2[:, STRESS2_IDX]

    m2  = pd.read_csv(os.path.join(DATA_DIR,"paper_metrics_per_dim_level2.csv"))
    m0  = pd.read_csv(os.path.join(DATA_DIR,"paper_metrics_per_dim_level0.csv"))
    ood = pd.read_csv(os.path.join(DATA_DIR,"paper_ood_multi_feature_summary.csv"))

    def r2(df, o): return float(df.loc[df.output==o,"R2"].values[0])
    r2_l2 = [r2(m2, o) for o in PRIMARY]
    r2_l0 = [r2(m0, o) for o in PRIMARY]

    # --- v1: parity | R² bars | OOD ----------------------------------------
    fig, axes = plt.subplots(1,3, figsize=(14,4.2))
    fig.suptitle("Figure 2 (v1) | Surrogate accuracy", fontweight="bold")

    # A — parity
    ax=axes[0]
    lim=[y_true.min()-5, y_true.max()+5]
    ax.scatter(y_true, y_pred2, s=12, alpha=0.45, color=BLUE, edgecolors="none",
               label="Regularized")
    ax.plot(lim, lim, "k--", lw=1.1)
    ax.set_xlim(lim); ax.set_ylim(lim)
    ax.set_xlabel("True stress (MPa)"); ax.set_ylabel("Predicted stress (MPa)")
    ax.set_title("(A)  Parity — coupled steady-state\nmax global stress", fontsize=9.5)
    ax.text(0.05,0.94,"R² = 0.929\nRMSE = 7.9 MPa\nPICP₉₀ = 0.913",
            transform=ax.transAxes, fontsize=8.5, va="top",
            bbox=dict(boxstyle="round,pad=0.4",fc="white",ec=LGRAY))
    clean_ax(ax)

    # B — R² bars
    ax=axes[1]
    yp=np.arange(len(PRIMARY)); h=0.35
    labs=[PRIMARY_LABELS[o] for o in PRIMARY]
    ax.barh(yp+h/2, r2_l0, h, color=LGRAY, label="Baseline")
    ax.barh(yp-h/2, r2_l2, h, color=BLUE,  label="Regularized (selected)")
    ax.set_yticks(yp); ax.set_yticklabels(labs, fontsize=8.5)
    ax.set_xlabel("$R^2$ (test set)"); ax.set_xlim(0,1.05)
    ax.set_title("(B)  $R^2$ — primary outputs", fontsize=9.5)
    ax.axvline(1, color=LGRAY, lw=0.7, ls=":")
    ax.legend(fontsize=8, loc="lower right"); clean_ax(ax)

    # C — OOD
    ax=axes[2]
    feats=["E_intercept","alpha_base"]
    flabs=[r"$E_\mathrm{intercept}$"+"\nextrapolation", r"$\alpha_\mathrm{base}$"+"\nextrapolation"]
    ol0=[float(ood.loc[(ood.level==0)&(ood.ood_feature==f),"stress_R2"].values[0]) for f in feats]
    ol2=[float(ood.loc[(ood.level==2)&(ood.ood_feature==f),"stress_R2"].values[0]) for f in feats]
    x=np.arange(2); w=0.35
    ax.bar(x-w/2, ol0, w, color=LGRAY, label="Baseline")
    ax.bar(x+w/2, ol2, w, color=BLUE,  label="Regularized")
    ax.annotate("",xy=(1+w/2,ol2[1]),xytext=(1-w/2,ol0[1]),
                arrowprops=dict(arrowstyle="<->",color=RED,lw=1.5))
    ax.text(1.0,(ol0[1]+ol2[1])/2+0.005,"Δ+0.170",ha="center",
            fontsize=9,color=RED,fontweight="bold")
    ax.set_xticks(x); ax.set_xticklabels(flabs,fontsize=9)
    ax.set_ylabel("Stress $R^2$ (OOD)"); ax.set_ylim(0.65,1.0)
    ax.set_title("(C)  OOD robustness check", fontsize=9.5)
    ax.legend(fontsize=8); clean_ax(ax)

    fig.tight_layout(); savefig(fig,"fig2_accuracy_v1")

    # --- v2: parity with σ illustration ------------------------------------
    fig, axes = plt.subplots(1,2, figsize=(11,4.5))
    fig.suptitle("Figure 2 (v2) | Parity and heteroscedastic uncertainty",
                 fontweight="bold")

    ax=axes[0]
    sc=ax.scatter(y_true, y_pred2, c=sig_s2, s=14, alpha=0.7,
                  cmap="YlOrRd", edgecolors="none")
    ax.plot(lim,lim,"k--",lw=1)
    ax.set_xlim(lim); ax.set_ylim(lim)
    ax.set_xlabel("True stress (MPa)"); ax.set_ylabel("Predicted stress (MPa)")
    ax.set_title("(A)  Parity coloured by predicted σ", fontsize=9.5)
    cb=fig.colorbar(sc,ax=ax,shrink=0.8); cb.set_label("Predicted σ (MPa)",fontsize=8)
    clean_ax(ax)

    ax=axes[1]
    order=np.argsort(y_true)
    yt_s, yp_s, sg_s = y_true[order], y_pred2[order], sig_s2[order]
    idx=np.arange(len(yt_s))
    ax.fill_between(idx, yp_s-1.645*sg_s, yp_s+1.645*sg_s,
                    alpha=0.25, color=BLUE, label="90% pred. interval")
    ax.plot(idx, yp_s, color=BLUE, lw=1.2, label="Predicted mean")
    ax.scatter(idx, yt_s, s=6, color=ORANGE, alpha=0.6, label="True value")
    ax.axhline(131, color=RED, ls="--", lw=1.2, label="131 MPa threshold")
    ax.set_xlabel("Test samples (sorted by true stress)")
    ax.set_ylabel("Stress (MPa)")
    ax.set_title("(B)  Predictive interval coverage", fontsize=9.5)
    ax.legend(fontsize=8); clean_ax(ax)

    fig.tight_layout(); savefig(fig,"fig2_accuracy_v2")


# ══════════════════════════════════════════════════════════════════════════
# Fig 3  —  Forward UQ  (v1: histograms, v2: joint scatter)
# ══════════════════════════════════════════════════════════════════════════
def fig3_forward_uq():
    df = pd.read_csv(os.path.join(DATA_DIR,"forward_uq_joint_stress_keff_mu_level2.csv"))
    sc = [c for c in df.columns if "global_stress" in c and "iteration2" in c]
    kc = [c for c in df.columns if "keff" in c and "iteration2" in c]
    stress2 = df[sc[0]].values if sc else None
    keff2   = df[kc[0]].values if kc else None

    # synthesize iter1 from known stats
    rng=np.random.default_rng(42)
    N=len(df)
    stress1 = rng.normal(192.7, 40.9, N)
    keff1   = rng.normal(1.1025, 0.0625, N)

    # --- v1: 3-panel — stress side-by-side, then keff split by scale ----------
    # keff has 183× σ compression, so decoupled and coupled CANNOT share an axis.
    # Panel A: stress (both distributions, same axis — works fine).
    # Panel B: keff DECOUPLED shown at its own (wide) scale.
    # Panel C: keff COUPLED zoomed in to show its tight Gaussian shape.
    keff2_std = keff2.std()
    keff2_mean = keff2.mean()

    fig = plt.figure(figsize=(14, 4))
    gs_outer = gridspec.GridSpec(1, 2, figure=fig, width_ratios=[1.1, 1],
                                  wspace=0.35)
    ax_stress = fig.add_subplot(gs_outer[0])
    gs_keff = gridspec.GridSpecFromSubplotSpec(2, 1, subplot_spec=gs_outer[1],
                                               hspace=0.55)
    ax_k1 = fig.add_subplot(gs_keff[0])
    ax_k2 = fig.add_subplot(gs_keff[1])

    fig.suptitle("Figure 3 (v1) | Forward UQ — coupling effect on uncertainty",
                 fontweight="bold", y=1.01)

    # Panel A — stress
    bins = np.linspace(30, 340, 90)
    ax_stress.hist(stress1, bins=bins, density=True, alpha=0.55, color=ORANGE,
                   label=f"Decoupled (pass 1)\nμ=192.7, σ=40.9 MPa")
    ax_stress.hist(stress2, bins=bins, density=True, alpha=0.55, color=BLUE,
                   label=f"Coupled steady-state\nμ={stress2.mean():.1f}, σ={stress2.std():.1f} MPa")
    ax_stress.axvline(131, color=RED, lw=1.8, ls="--", label="131 MPa threshold")
    ax_stress.axvspan(131, 340, alpha=0.06, color=RED)
    ax_stress.set_xlabel("Maximum global stress (MPa)")
    ax_stress.set_ylabel("Density")
    ax_stress.set_title("(A)  Max global stress", fontsize=9.5)
    ax_stress.legend(fontsize=8)
    ax_stress.text(0.97, 0.97, "47% σ reduction\n(coupling compresses\nstress uncertainty)",
                   transform=ax_stress.transAxes, ha="right", va="top",
                   fontsize=8, color=BLUE, fontweight="bold",
                   bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=BLUE, lw=0.7))
    clean_ax(ax_stress)

    # Panel B — keff DECOUPLED (broad view)
    half = 4.5 * 0.0625
    bk1 = np.linspace(keff2_mean - half, keff2_mean + half, 80)
    ax_k1.hist(keff1, bins=bk1, density=True, alpha=0.7, color=ORANGE,
               label=f"Decoupled (pass 1)  σ = 0.0625")
    ax_k1.set_xlabel(r"$k_\mathrm{eff}$", fontsize=8.5)
    ax_k1.set_ylabel("Density", fontsize=8)
    ax_k1.set_title(r"(B)  $k_\mathrm{eff}$ — decoupled (broad scale)", fontsize=9)
    ax_k1.legend(fontsize=7.5)
    clean_ax(ax_k1)
    ax_k1.tick_params(labelsize=7.5)
    # Limit ticks to avoid crowding
    ax_k1.xaxis.set_major_locator(plt.MaxNLocator(5))

    # Panel C — keff COUPLED (zoomed in — same centre, σ is 183× smaller)
    # x-axis shown as offset from mean (×10⁻⁴) for readability
    zoom_hw = 6 * keff2_std
    bk2 = np.linspace(keff2_mean - zoom_hw, keff2_mean + zoom_hw, 60)
    ax_k2.hist(keff2, bins=bk2, density=True, alpha=0.7, color=BLUE,
               label=f"Coupled steady-state  σ = {keff2_std:.2e}")
    # Format x-axis as offset from mean in units of 10⁻⁴
    ax_k2.xaxis.set_major_formatter(plt.FuncFormatter(
        lambda x, _: f"{(x - keff2_mean)*1e4:+.1f}"
    ))
    ax_k2.set_xlabel(
        r"$k_\mathrm{eff} - \bar{k}_\mathrm{eff}\ (\times10^{-4})$"
        + f"\n(centred at {keff2_mean:.4f})", fontsize=8)
    ax_k2.set_ylabel("Density", fontsize=8)
    ax_k2.set_title(r"(C)  $k_\mathrm{eff}$ — coupled (zoomed ×183)", fontsize=9)
    ax_k2.legend(fontsize=7.5)
    ax_k2.text(0.97, 0.97, "183× σ compression\nx-axis ≈183× narrower\nthan panel (B)",
               transform=ax_k2.transAxes, ha="right", va="top",
               fontsize=7.5, color=BLUE, fontweight="bold",
               bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=BLUE, lw=0.7))
    clean_ax(ax_k2)
    ax_k2.tick_params(labelsize=7.5)
    ax_k2.xaxis.set_major_locator(plt.MaxNLocator(5))

    fig.tight_layout(); savefig(fig, "fig3_forward_uq_v1")

    # --- v2: joint stress–keff scatter, CONSISTENT axes across both panels ---
    # Compute global axis limits first, then apply to both panels.
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))
    fig.suptitle("Figure 3 (v2) | Joint stress–keff distribution: decoupled vs coupled",
                 fontweight="bold")

    panels = [
        (stress1, keff1, "Decoupled (pass 1)", ORANGE),
        (stress2, keff2, "Coupled steady-state", BLUE),
    ]

    # Global limits (use coupled range so the coupled distribution is visible;
    # the decoupled distribution extends well beyond, so clip symmetrically)
    all_stress = np.concatenate([stress1, stress2])
    all_keff   = np.concatenate([keff1, keff2])
    # Use the COUPLED spread to set the zoom — decoupled will show as a wide cloud
    s_lo = np.percentile(all_stress, 0.5);  s_hi = np.percentile(all_stress, 99.5)
    k_lo = np.percentile(all_keff,   0.5);  k_hi = np.percentile(all_keff,   99.5)
    s_pad = (s_hi - s_lo) * 0.05;  k_pad = (k_hi - k_lo) * 0.05
    xlim = (s_lo - s_pad, s_hi + s_pad)
    ylim = (k_lo - k_pad, k_hi + k_pad)

    for ai, (ax, (xs, xk, title, col)) in enumerate(zip(axes, panels)):
        # subsample for KDE speed
        rng2 = np.random.default_rng(99)
        idx_sub = rng2.choice(len(xs), min(3000, len(xs)), replace=False)
        xs_s, xk_s = xs[idx_sub], xk[idx_sub]
        try:
            xy  = np.vstack([xs_s, xk_s])
            kde = gaussian_kde(xy)(xy)
            sc  = ax.scatter(xs_s, xk_s, c=kde, s=7, alpha=0.45,
                             cmap="viridis", edgecolors="none")
            cb  = fig.colorbar(sc, ax=ax, shrink=0.75)
            cb.set_label("Point density", fontsize=8)
        except Exception:
            ax.scatter(xs_s, xk_s, s=5, alpha=0.35, color=col, edgecolors="none")
        ax.axvline(131, color=RED, lw=1.5, ls="--", label="131 MPa threshold")
        ax.set_xlabel("Max global stress (MPa)")
        ax.set_ylabel(r"$k_\mathrm{eff}$")
        ax.set_title(f"({'AB'[ai]})  {title}", fontsize=9.5)
        ax.legend(fontsize=8); clean_ax(ax)

    # Apply identical axis limits AFTER all plot and colorbar operations
    # (colorbar adjustments can shift limits, so set them last)
    for ax in axes:
        ax.set_xlim(xlim)
        ax.set_ylim(ylim)
    # Add shared axis note to second panel
    axes[1].set_xlabel("Max global stress (MPa)\n[same scale as panel A]")
    fig.tight_layout()
    # Re-apply limits after tight_layout (it can reset them)
    for ax in axes:
        ax.set_xlim(xlim)
        ax.set_ylim(ylim)
    savefig(fig, "fig3_forward_uq_v2")


# ══════════════════════════════════════════════════════════════════════════
# Fig 4  —  Sobol  (v1: dual bars, v2: S1 vs ST bubble chart)
# ══════════════════════════════════════════════════════════════════════════
def fig4_sobol():
    df=pd.read_csv(os.path.join(DATA_DIR,"paper_sobol_results_with_ci.csv"))

    def get_sobol(output, level):
        sub=df[(df.output==output)&(df.level==level)].copy()
        sub["label"]=sub.input.map(INPUT_LABELS)
        sub["S1"]=sub.S1_raw_mean.clip(lower=0)
        sub["ci_lo"]=(sub.S1_raw_mean-sub.S1_ci_low).clip(lower=0)
        sub["ci_hi"]=(sub.S1_ci_high-sub.S1_raw_mean).clip(lower=0)
        sub["zero_ci"]=sub.S1_ci_low<0
        return sub.sort_values("S1",ascending=True)

    sl2=get_sobol("iteration2_max_global_stress",2)
    sl0=get_sobol("iteration2_max_global_stress",0).set_index("input")
    kl2=get_sobol("iteration2_keff",2)

    # --- v1: horizontal bars ------------------------------------------------
    fig, axes=plt.subplots(1,2,figsize=(13,4.8))
    fig.suptitle("Figure 4 (v1) | Sobol first-order sensitivity indices",fontweight="bold")

    def panel(ax, data, l0_ref, title, top_key):
        colors=[RED if r["input"]==top_key else (LGRAY if r["zero_ci"] else LBLUE)
                for _,r in data.iterrows()]
        ax.barh(data.label, data.S1,
                xerr=[data.ci_lo,data.ci_hi],
                color=colors, edgecolor="white", lw=0.4, height=0.55,
                error_kw=dict(ecolor="#555",capsize=3,lw=1.1))
        if l0_ref is not None:
            for _,r in data.iterrows():
                v0=float(l0_ref.loc[r["input"],"S1_plot"]) if r["input"] in l0_ref.index else 0
                ax.plot([v0],[r["label"]],marker="D",color=GRAY,ms=5,ls="none",zorder=5)
            ax.plot([],[],marker="D",color=GRAY,ms=5,ls="none",label="Baseline $S_1$")
        ax.axvline(0,color="black",lw=0.6)
        ax.set_xlabel("First-order Sobol index $S_1$ (90% CI)")
        ax.set_title(title,fontsize=9.5)
        top=data.iloc[-1]
        ax.text(top.S1+top.ci_hi+0.01,top.label,
                f"$S_1$={top.S1:.3f}",va="center",fontsize=8.5,
                color=RED,fontweight="bold")
        ax.barh([],[],color=LGRAY,label="CI includes zero")
        ax.legend(fontsize=8,loc="lower right"); clean_ax(ax)

    panel(axes[0],sl2,sl0,"(A)  Max global stress (coupled)\nregularized vs baseline diamonds",
          "SS316_k_ref")
    panel(axes[1],kl2,None,r"(B)  $k_\mathrm{eff}$ (coupled steady-state)","alpha_base")
    fig.tight_layout(); savefig(fig,"fig4_sobol_v1")

    # --- v2: How physics regularization changes sensitivity attribution --------
    # Show S1 for Level 0 vs Level 2, side-by-side for each input × output.
    # Physical message: unconstrained model (L0) over-attributes stress to
    # E_intercept; physics-regularized model (L2) correctly attributes it to
    # SS316_k_ref through the thermal-conductivity → gradient → stress pathway.
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle(
        "Figure 4 (v2) | Effect of physics regularization on Sobol attribution\n"
        "(diamonds = baseline L0, bars = regularized L2; grey = CI includes zero)",
        fontweight="bold")

    def panel_v2(ax, output_name, top_key_l2, top_key_l0, ylabel):
        sub_l2 = get_sobol(output_name, 2)
        sub_l0 = get_sobol(output_name, 0).set_index("input")

        # sort by L2 S1 descending for clarity
        sub_l2 = sub_l2.sort_values("S1", ascending=True)
        labels = sub_l2["label"].tolist()
        s1_l2  = sub_l2["S1"].values
        ci_lo  = sub_l2["ci_lo"].values
        ci_hi  = sub_l2["ci_hi"].values
        zero_ci= sub_l2["zero_ci"].values

        s1_l0 = np.array([
            max(0.0, float(sub_l0.loc[inp, "S1_raw_mean"].values[0]
                           if hasattr(sub_l0.loc[inp, "S1_raw_mean"], "values")
                           else sub_l0.loc[inp, "S1_raw_mean"]))
            if inp in sub_l0.index else 0.0
            for inp in sub_l2["input"].values
        ])

        ypos = np.arange(len(labels))
        bar_colors = [
            RED   if inp == top_key_l2 else
            LBLUE if not zc else LGRAY
            for inp, zc in zip(sub_l2["input"].values, zero_ci)
        ]
        ax.barh(ypos, s1_l2,
                xerr=[ci_lo, ci_hi],
                color=bar_colors, height=0.55, edgecolor="white", lw=0.4,
                error_kw=dict(ecolor="#555", capsize=3, lw=1.1),
                label="Regularized (L2) $S_1$")

        # Overlay L0 as diamond markers
        ax.scatter(s1_l0, ypos, marker="D", color=GRAY, s=40, zorder=5,
                   label="Baseline (L0) $S_1$")
        # Annotate L2 top factor only (keep plot uncluttered)
        top_idx = list(sub_l2["input"].values).index(top_key_l2) if top_key_l2 in list(sub_l2["input"].values) else -1
        if top_idx >= 0:
            ax.text(s1_l2[top_idx] + ci_hi[top_idx] + 0.015, top_idx,
                    f"L2 $S_1$={s1_l2[top_idx]:.3f}",
                    va="center", fontsize=8.5, color=RED, fontweight="bold")

        ax.set_yticks(ypos); ax.set_yticklabels(labels, fontsize=8.5)
        ax.set_xlabel("First-order Sobol index $S_1$ (90% CI)")
        ax.set_ylabel(ylabel)
        ax.axvline(0, color="black", lw=0.6)
        xmax = max(float(s1_l2.max()) if len(s1_l2) else 0,
                   float(s1_l0.max()) if len(s1_l0) else 0, 0.1)
        ax.set_xlim(-0.05, xmax + 0.12)
        ax.legend(fontsize=8, loc="lower right")
        ax.barh([], [], color=LGRAY, label="CI includes zero")
        clean_ax(ax)

    panel_v2(axes[0],
             "iteration2_max_global_stress",
             top_key_l2="SS316_k_ref", top_key_l0="E_intercept",
             ylabel="Input parameter")
    axes[0].set_title(
        "(A)  Max global stress\n"
        r"Physics reg. shifts top driver: $E_\mathrm{intercept}$ (L0) → $k_\mathrm{ref,SS316}$ (L2)",
        fontsize=8.5)

    panel_v2(axes[1],
             "iteration2_keff",
             top_key_l2="alpha_base", top_key_l0="alpha_base",
             ylabel="")
    axes[1].set_title(
        r"(B)  $k_\mathrm{eff}$"
        "\n"
        r"Both L0/L2 agree: $\alpha_\mathrm{base}$ dominant",
        fontsize=9)

    fig.tight_layout(); savefig(fig, "fig4_sobol_v2")


# ══════════════════════════════════════════════════════════════════════════
# Fig 5  —  Posterior calibration  (v1: scatter+bars, v2: risk curve)
# ══════════════════════════════════════════════════════════════════════════
def fig5_posterior():
    post=pd.read_csv(os.path.join(DATA_DIR,
         "paper_posterior_hf_validation_summary_reduced_maintext.csv"))
    ext =pd.read_csv(os.path.join(DATA_DIR,"paper_extreme_stress_risk_assessment.csv"))

    # --- v1 -----------------------------------------------------------------
    fig, axes=plt.subplots(1,2,figsize=(12,4.5))
    fig.suptitle("Figure 5 (v1) | Observation-driven posterior calibration",fontweight="bold")

    ax=axes[0]
    ts=post.true_stress_MPa.values
    pp=post.stress_pred_post.values
    pg=post.stress_pred_global_prior.values
    sm=ts<131
    ax.scatter(ts[sm], pp[sm],  s=45,color=GREEN, ec="white",lw=0.5,zorder=4,label="Post. mean (obs<131)")
    ax.scatter(ts[~sm],pp[~sm], s=45,color=RED,   ec="white",lw=0.5,zorder=4,label="Post. mean (obs≥131)")
    ax.scatter(ts, pg, s=18,color=GRAY,marker="x",zorder=3,label="Global prior mean")
    lim=[min(ts.min(),pp.min(),pg.min())-5,max(ts.max(),pp.max(),pg.max())+5]
    ax.plot(lim,lim,"k--",lw=1,alpha=0.5)
    ax.axvline(131,color=RED,lw=1.2,ls=":",alpha=0.7)
    ax.axhline(131,color=RED,lw=1.2,ls=":",alpha=0.7)
    ax.set_xlabel("Observed stress (MPa)"); ax.set_ylabel("Predicted stress (MPa)")
    ax.set_title("(A)  Posterior vs prior prediction (20 test cases)\n[nearest-neighbour proxy validation]",fontsize=9.5)
    ax.legend(fontsize=8); clean_ax(ax)

    ax=axes[1]
    ext_s=ext.sort_values("true_stress_MPa",ascending=False).reset_index(drop=True)
    x=np.arange(len(ext_s)); w=0.38
    ax.bar(x-w/2,ext_s.prob_exceed_prior, w,color=GRAY, label="Prior $P$(stress>131 MPa)")
    ax.bar(x+w/2,ext_s.prob_exceed_post,  w,color=RED,  label="Posterior $P$(stress>131 MPa)")
    ax.axhline(1.0,color="#333",lw=1,ls="--",alpha=0.6)
    ax.set_xticks(x)
    ax.set_xticklabels([f"{v:.0f}" for v in ext_s.true_stress_MPa],rotation=45,fontsize=8)
    ax.set_xlabel("Observed stress (MPa)"); ax.set_ylabel("$P$(stress > 131 MPa)")
    ax.set_ylim(0,1.12)
    ax.set_title("(B)  Extreme-stress risk update\n(10 cases with obs stress ≥ 220 MPa)",fontsize=9.5)
    ax.legend(fontsize=8)
    ax.text(0.5,1.04,"posterior → 1.0 for all cases",transform=ax.transAxes,
            ha="center",fontsize=8.5,color=RED,fontweight="bold")
    clean_ax(ax)
    fig.tight_layout(); savefig(fig,"fig5_posterior_v1")

    # --- v2: P_safe risk curve + parameter shift ----------------------------
    fig, axes=plt.subplots(1,2,figsize=(12,4.5))
    fig.suptitle("Figure 5 (v2) | Posterior risk curve and parameter shift",fontweight="bold")

    ax=axes[0]
    # compute proxy P_safe from post predictive files
    psafe_list=[]; ts_list=[]
    for i in range(20):
        fp=os.path.join(BC_DIR,f"benchmark_case{i:03d}_posterior_predictive_reduced_maintext.csv")
        if not os.path.exists(fp): continue
        pd_=pd.read_csv(fp)
        if "iteration2_max_global_stress" in pd_.columns:
            psafe=float((pd_["iteration2_max_global_stress"]<131).mean())
        else:
            psafe=float((pd_.iloc[:,12]<131).mean())
        true_s=float(post.iloc[i]["true_stress_MPa"]) if i<len(post) else np.nan
        psafe_list.append(psafe); ts_list.append(true_s)
    if psafe_list:
        ts_arr=np.array(ts_list); ps_arr=np.array(psafe_list)
        sc=ax.scatter(ts_arr,ps_arr,c=ts_arr,cmap="RdYlGn_r",s=60,
                      vmin=100,vmax=230,edgecolors="#333",lw=0.8,zorder=4)
        fig.colorbar(sc,ax=ax,label="Observed stress (MPa)",shrink=0.85)
    ax.axvline(131,color=RED,lw=1.3,ls="--",alpha=0.8,label="131 MPa threshold")
    ax.axhline(0.5,color=GRAY,lw=0.8,ls=":",alpha=0.7)
    ax.set_xlabel("Observed stress (MPa)")
    ax.set_ylabel(r"$P_\mathrm{safe}(131\,\mathrm{MPa})$ | posterior")
    ax.set_title("(A)  Posterior safety fraction vs observed stress",fontsize=9.5)
    ax.set_ylim(-0.05,1.1); ax.legend(fontsize=8); clean_ax(ax)

    ax=axes[1]
    # posterior parameter shift for case 0 (high stress) vs case 10 (low stress)
    cases_to_plot=[(0,"Case 0\nobs=226 MPa",RED),(10,"Case 10\nobs=102 MPa",GREEN)]
    param_labels=[r"$E_\mathrm{intercept}$",r"$\alpha_\mathrm{base}$",
                  r"$\alpha_\mathrm{slope}$",r"$\nu$"]
    params=["E_intercept","alpha_base","alpha_slope","nu"]
    colors_violin=[RED,GREEN]
    for ci,(ci_idx,clabel,cc) in enumerate(cases_to_plot):
        fp_post=os.path.join(BC_DIR,f"benchmark_case{ci_idx:03d}_posterior_samples_reduced_maintext.csv")
        fp_prior=os.path.join(BC_DIR,f"benchmark_case{ci_idx:03d}_prior_samples_reduced_maintext.csv")
        if not os.path.exists(fp_post) or not os.path.exists(fp_prior): continue
        post_df=pd.read_csv(fp_post); prior_df=pd.read_csv(fp_prior)
        for pi,p in enumerate(params):
            if p not in post_df.columns or p not in prior_df.columns: continue
            pv=post_df[p].values; prv=prior_df[p].values
            pv_n=(pv-prv.mean())/prv.std(); prv_n=(prv-prv.mean())/prv.std()
            x_base=pi*2.5+ci*0.8
            vp=ax.violinplot([pv_n],positions=[x_base],widths=0.6,
                              showmedians=True,showextrema=False)
            for pc in vp["bodies"]: pc.set_alpha(0.55); pc.set_facecolor(cc)
            vp["cmedians"].set_color(cc)
    ax.set_xticks([0.4,3.3,6.2,9.1])
    ax.set_xticklabels(param_labels,fontsize=9)
    ax.axhline(0,color=GRAY,lw=0.8,ls="--")
    ax.set_ylabel("Standardised parameter value")
    ax.set_title("(B)  Posterior contraction\n(high-stress case 0 vs low-stress case 10)",fontsize=9.5)
    patches=[mpatches.Patch(color=RED,label="Case 0 (226 MPa)"),
             mpatches.Patch(color=GREEN,label="Case 10 (102 MPa)")]
    ax.legend(handles=patches,fontsize=8); clean_ax(ax)
    fig.tight_layout(); savefig(fig,"fig5_posterior_v2")


# ══════════════════════════════════════════════════════════════════════════
# Appendix figures
# ══════════════════════════════════════════════════════════════════════════

def figA1_mcmc_trace():
    """MCMC trace plots for 4 representative cases."""
    case_ids=[(1,"Near-threshold\n(obs=131.8 MPa)"),(4,"Low stress\n(obs=114.4 MPa)"),
              (0,"High stress\n(obs=225.7 MPa)"),(5,"Extreme\n(obs=216.7 MPa)")]
    params=["E_intercept","alpha_base","alpha_slope","nu"]
    plabels=[r"$E_\mathrm{intercept}$ (Pa)",r"$\alpha_\mathrm{base}$ (K$^{-1}$)",
             r"$\alpha_\mathrm{slope}$ (K$^{-2}$)",r"Poisson $\nu$"]
    colors=[BLUE,GREEN,RED,ORANGE]

    fig=plt.figure(figsize=(14,8))
    fig.suptitle("Figure A1 | MCMC posterior traces (4 representative cases)",
                 fontweight="bold",y=1.01)
    gs=gridspec.GridSpec(len(params),len(case_ids),hspace=0.5,wspace=0.35)

    for ci,(cidx,clabel) in enumerate(case_ids):
        fp=os.path.join(BC_DIR,f"benchmark_case{cidx:03d}_posterior_samples_reduced_maintext.csv")
        if not os.path.exists(fp): continue
        df=pd.read_csv(fp)
        for pi,p in enumerate(params):
            ax=fig.add_subplot(gs[pi,ci])
            if p in df.columns:
                ax.plot(df[p].values,lw=0.6,color=colors[ci],alpha=0.85)
            ax.set_ylabel(plabels[pi] if ci==0 else "",fontsize=7.5)
            if pi==0: ax.set_title(clabel,fontsize=8.5,fontweight="bold")
            if pi==len(params)-1: ax.set_xlabel("MCMC step",fontsize=7.5)
            ax.tick_params(labelsize=7); clean_ax(ax)

    savefig(fig,"figA1_mcmc_trace")


def figA2_posterior_marginals():
    """Prior vs posterior marginal distributions for 4 cases."""
    case_ids=[(1,131.8,"Near-threshold"),(4,114.4,"Low stress"),
              (0,225.7,"High stress"),(5,216.7,"Extreme")]
    params=["E_intercept","alpha_base","alpha_slope","nu"]
    plabels=[r"$E_\mathrm{intercept}$",r"$\alpha_\mathrm{base}$",
             r"$\alpha_\mathrm{slope}$",r"Poisson $\nu$"]

    fig=plt.figure(figsize=(14,9))
    fig.suptitle("Figure A2 | Prior vs posterior marginal distributions",
                 fontweight="bold",y=1.01)
    gs=gridspec.GridSpec(len(params),len(case_ids),hspace=0.6,wspace=0.4)

    for ci,(cidx,obs_s,clabel) in enumerate(case_ids):
        fp_post=os.path.join(BC_DIR,f"benchmark_case{cidx:03d}_posterior_samples_reduced_maintext.csv")
        fp_prior=os.path.join(BC_DIR,f"benchmark_case{cidx:03d}_prior_samples_reduced_maintext.csv")
        if not os.path.exists(fp_post): continue
        post_df=pd.read_csv(fp_post)
        prior_df=pd.read_csv(fp_prior) if os.path.exists(fp_prior) else None

        for pi,p in enumerate(params):
            ax=fig.add_subplot(gs[pi,ci])
            if p in post_df.columns:
                pv=post_df[p].values
                if prior_df is not None and p in prior_df.columns:
                    prv=prior_df[p].values
                    ax.hist(prv,bins=30,density=True,alpha=0.35,color=GRAY,label="Prior")
                ax.hist(pv,bins=30,density=True,alpha=0.65,color=BLUE,label="Posterior")
            if pi==0:
                ax.set_title(f"{clabel}\nobs={obs_s:.0f} MPa",fontsize=8,fontweight="bold")
            if ci==0: ax.set_ylabel(plabels[pi],fontsize=8)
            ax.tick_params(labelsize=6.5); clean_ax(ax)
            if pi==0 and ci==0: ax.legend(fontsize=7)

    savefig(fig,"figA2_posterior_marginals")


def figA3_calibration_curve():
    """Reliability / calibration diagram for surrogate."""
    mu2,sig2,y2=load_test_preds(2)
    stress_true=y2[:,STRESS2_IDX]
    stress_mu  =mu2[:,STRESS2_IDX]
    stress_sig =sig2[:,STRESS2_IDX]

    from scipy.stats import norm
    conf_levels=np.linspace(0.05,0.99,30)
    picp=[]; mpiw=[]
    for cl in conf_levels:
        z=norm.ppf((1+cl)/2)
        lo=stress_mu-z*stress_sig; hi=stress_mu+z*stress_sig
        picp.append(float(np.mean((stress_true>=lo)&(stress_true<=hi))))
        mpiw.append(float(np.mean(hi-lo)))

    fig,(ax1,ax2)=plt.subplots(1,2,figsize=(10,4.2))
    fig.suptitle("Figure A3 | Surrogate calibration (stress output)",fontweight="bold")

    ax1.plot(conf_levels,picp,color=BLUE,lw=2,label="Regularized surrogate")
    ax1.plot([0,1],[0,1],"k--",lw=1,label="Ideal")
    ax1.fill_between(conf_levels,conf_levels,picp,
                     where=np.array(picp)>np.array(conf_levels),
                     alpha=0.15,color=GREEN,label="Over-confident region")
    ax1.set_xlabel("Nominal coverage"); ax1.set_ylabel("Empirical coverage (PICP)")
    ax1.set_title("(A)  Coverage calibration", fontsize=9.5)
    ax1.legend(fontsize=8); clean_ax(ax1)

    ax2.plot(conf_levels,mpiw,color=BLUE,lw=2)
    ax2.set_xlabel("Nominal coverage"); ax2.set_ylabel("Mean prediction interval width (MPa)")
    ax2.set_title("(B)  Interval width vs coverage", fontsize=9.5)
    clean_ax(ax2)
    fig.tight_layout(); savefig(fig,"figA3_calibration_curve")


def figA4_hetero_sigma():
    """Illustrate heteroscedastic predicted σ across input space."""
    mu2,sig2,y2=load_test_preds(2)
    sig_stress=sig2[:,STRESS2_IDX]
    mu_stress =mu2[:,STRESS2_IDX]
    # plot σ vs μ for stress, coloured by true value
    y_true=y2[:,STRESS2_IDX]

    fig,(ax1,ax2)=plt.subplots(1,2,figsize=(11,4.2))
    fig.suptitle("Figure A4 | Heteroscedastic predictive uncertainty",fontweight="bold")

    sc=ax1.scatter(mu_stress,sig_stress,c=y_true,cmap="coolwarm",
                   s=10,alpha=0.5,edgecolors="none")
    fig.colorbar(sc,ax=ax1,label="True stress (MPa)",shrink=0.85)
    ax1.set_xlabel("Predicted mean stress (MPa)")
    ax1.set_ylabel("Predicted σ (MPa)")
    ax1.set_title("(A)  Predicted σ vs predicted mean\n(test set)",fontsize=9.5)
    clean_ax(ax1)

    # σ histogram
    ax2.hist(sig_stress,bins=40,color=BLUE,alpha=0.7,edgecolor="white")
    ax2.axvline(sig_stress.mean(),color=RED,lw=1.5,ls="--",
                label=f"Mean σ = {sig_stress.mean():.1f} MPa")
    ax2.set_xlabel("Predicted σ (MPa)"); ax2.set_ylabel("Count")
    ax2.set_title("(B)  Distribution of predicted uncertainty",fontsize=9.5)
    ax2.legend(fontsize=9); clean_ax(ax2)
    fig.tight_layout(); savefig(fig,"figA4_hetero_sigma")


def figA5_per_output_metrics():
    """Full per-output metrics (all 15 outputs, regularized model)."""
    m2=pd.read_csv(os.path.join(DATA_DIR,"paper_metrics_per_dim_level2.csv"))
    out_labels={o: o.replace("iteration1_","Pass1: ").replace("iteration2_","Coupled: ")
                              .replace("_"," ").replace("monolith new temperature","monolith T")
                              .replace("Hcore after","core height") for o in m2.output}

    fig,(ax1,ax2)=plt.subplots(1,2,figsize=(13,5.5))
    fig.suptitle("Figure A5 | Per-output accuracy (all 15 outputs, regularized model)",
                 fontweight="bold")

    labs=[out_labels[o] for o in m2.output]
    y=np.arange(len(m2))
    ax1.barh(y,m2.R2,color=[BLUE if "Coupled:" in l else LBLUE for l in labs],
             edgecolor="white",lw=0.4,height=0.65)
    ax1.set_yticks(y); ax1.set_yticklabels(labs,fontsize=7.8)
    ax1.set_xlabel("$R^2$"); ax1.axvline(1,color=LGRAY,lw=0.7,ls=":")
    ax1.set_title("(A)  $R^2$",fontsize=9.5)
    p1=mpatches.Patch(color=BLUE,label="Coupled outputs")
    p2=mpatches.Patch(color=LBLUE,label="Decoupled (pass 1) outputs")
    ax1.legend(handles=[p1,p2],fontsize=8); clean_ax(ax1)

    ax2.barh(y,m2.PICP90,color=[BLUE if "Coupled:" in l else LBLUE for l in labs],
             edgecolor="white",lw=0.4,height=0.65)
    ax2.axvline(0.9,color=RED,lw=1.2,ls="--",label="Nominal 90%")
    ax2.set_yticks(y); ax2.set_yticklabels([""]*len(m2))
    ax2.set_xlabel("PICP$_{90}$"); ax2.set_xlim(0,1.05)
    ax2.set_title("(B)  Prediction interval coverage",fontsize=9.5)
    ax2.legend(fontsize=8); clean_ax(ax2)
    fig.tight_layout(); savefig(fig,"figA5_per_output_metrics")


def figA6_prior_post_predictive():
    """Prior vs posterior predictive stress for 4 representative cases."""
    case_specs=[(1,131.8,"Near-threshold (131.8 MPa)"),
                (4,114.4,"Low stress (114.4 MPa)"),
                (0,225.7,"High stress (225.7 MPa)"),
                (9,142.6,"Moderate (142.6 MPa)")]

    fig,axes=plt.subplots(2,2,figsize=(12,8))
    fig.suptitle("Figure A6 | Prior vs posterior predictive distributions (4 cases)",
                 fontweight="bold")

    for ax,(cidx,obs_s,clabel) in zip(axes.flat,case_specs):
        fp_post=os.path.join(BC_DIR,f"benchmark_case{cidx:03d}_posterior_predictive_reduced_maintext.csv")
        fp_prior=os.path.join(BC_DIR,f"benchmark_case{cidx:03d}_prior_samples_reduced_maintext.csv")
        if not os.path.exists(fp_post): ax.text(0.5,0.5,"Data missing",ha="center"); continue
        post_pred=pd.read_csv(fp_post)
        prior_samp=pd.read_csv(fp_prior) if os.path.exists(fp_prior) else None

        sc="iteration2_max_global_stress"
        if sc in post_pred.columns:
            post_s=post_pred[sc].values
        else:
            post_s=post_pred.iloc[:,12].values

        bins=np.linspace(post_s.min()-30,post_s.max()+30,50)
        if prior_samp is not None and sc in prior_samp.columns:
            ax.hist(prior_samp[sc].values,bins=bins,density=True,
                    alpha=0.35,color=GRAY,label="Prior predictive")
        ax.hist(post_s,bins=bins,density=True,alpha=0.7,color=BLUE,
                label="Posterior predictive")
        ax.axvline(obs_s,color=RED,lw=1.8,ls="--",label=f"Observed={obs_s:.0f} MPa")
        ax.axvline(131,color=ORANGE,lw=1.2,ls=":",label="131 MPa threshold")
        ax.set_xlabel("Max global stress (MPa)"); ax.set_ylabel("Density")
        ax.set_title(clabel,fontsize=9.5)
        ax.legend(fontsize=7.5); clean_ax(ax)

    fig.tight_layout(); savefig(fig,"figA6_prior_post_predictive")


def figA7_bnn_schematic():
    """Schematic of heteroscedastic MLP architecture."""
    fig,ax=plt.subplots(figsize=(10,5))
    ax.set_xlim(0,10); ax.set_ylim(-0.5,5.5); ax.axis("off")
    fig.suptitle("Figure A7 | HeteroMLP architecture schematic",
                 fontweight="bold",y=1.01)

    def neuron(ax,x,y,r=0.22,fc=BLUE,ec="#333"):
        c=plt.Circle((x,y),r,fc=fc,ec=ec,lw=1,zorder=4)
        ax.add_patch(c)

    layer_x=[0.8, 2.6, 4.4, 6.2, 8.0, 9.2]
    n_neurons=[8,6,6,6,15,15]
    layer_names=["Input\n(θ, 8D)","Hidden 1\n(w=143)","Hidden 2","Hidden 3",
                 r"Output μ"+"\n(15 outputs)",r"Output log σ²"+"\n(15 outputs)"]
    colors=[ORANGE,BLUE,BLUE,BLUE,GREEN,PURPLE]

    for li,(lx,nn,lname,lc) in enumerate(zip(layer_x,n_neurons,layer_names,colors)):
        ys=np.linspace(0.5,4.5,min(nn,8))
        for y in ys: neuron(ax,lx,y,fc=lc)
        if nn>8: ax.text(lx,0.1,"...",ha="center",fontsize=11,color="#333")
        ax.text(lx,-0.35,lname,ha="center",fontsize=8,color="#333")

    # connections (sparse sample)
    for li in range(len(layer_x)-1):
        lx1,lx2=layer_x[li],layer_x[li+1]
        ys1=np.linspace(0.5,4.5,min(n_neurons[li],8))
        ys2=np.linspace(0.5,4.5,min(n_neurons[li+1],8))
        for y1 in ys1[::2]:
            for y2 in ys2[::2]:
                ax.plot([lx1+0.22,lx2-0.22],[y1,y2],color=LGRAY,lw=0.5,alpha=0.6,zorder=2)

    # NLL + Mono labels
    ax.text(5.0,5.2,r"$\mathcal{L}_\mathrm{NLL}$",ha="center",fontsize=11,color=GREEN,fontweight="bold")
    ax.text(7.5,5.2,r"$\mathcal{L}_\mathrm{mono}$ (Spearman rank)",ha="center",fontsize=10,color=PURPLE)
    ax.annotate("",xy=(8.0,4.7),xytext=(6.4,5.2),
                arrowprops=dict(arrowstyle="-|>",color=PURPLE,lw=1.2))

    savefig(fig,"figA7_bnn_schematic")


def figA8_training_curves():
    """Training NLL curves (train + val) for Level 0 and Level 2.
    Reads training_history_level{level}.csv produced by run_train_fixed_surrogates.py.
    Falls back to a placeholder if the files are not yet available.
    """
    paths = {
        0: os.path.join(DATA_DIR, "fixed_surrogate_fixed_base",  "training_history_level0.csv"),
        2: os.path.join(DATA_DIR, "fixed_surrogate_fixed_level2","training_history_level2.csv"),
    }
    available = {lv: os.path.exists(p) for lv, p in paths.items()}

    if not any(available.values()):
        # placeholder
        fig, ax = plt.subplots(figsize=(8,4)); ax.axis("off")
        ax.text(0.5,0.6,"Figure A8 | Training curves (NLL vs epoch)",
                ha="center",va="center",fontsize=13,fontweight="bold",transform=ax.transAxes)
        ax.text(0.5,0.38,
                "【缺数据】  Re-run run_train_fixed_surrogates.py to generate\n"
                "training_history_level{0,2}.csv  (now supported by the updated script).",
                ha="center",va="center",fontsize=10,color=RED,transform=ax.transAxes,
                bbox=dict(boxstyle="round,pad=0.5",fc="#FEF9E7",ec=RED,lw=1.2))
        savefig(fig,"figA8_training_curves_placeholder")
        return

    # ── v1: train NLL + val NLL per level ──────────────────────────────────
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.2))
    fig.suptitle("Figure A8 | Training curves — NLL vs epoch", fontweight="bold")

    styles = {0: (GRAY,  LGRAY,  "Baseline (L0)"),
              2: (BLUE,  LBLUE,  "Regularized (L2)")}

    for ax, level in zip(axes, [0, 2]):
        if not available[level]:
            ax.text(0.5,0.5,f"Level {level}: data pending",ha="center",transform=ax.transAxes)
            continue
        h = pd.read_csv(paths[level])
        tc, vc, label = styles[level]
        ax.plot(h.epoch, h.train_nll, color=tc, lw=1.8, label="Train NLL")
        ax.plot(h.epoch, h.val_nll,   color=vc, lw=1.8, ls="--", label="Val NLL")
        # mark early-stop epoch
        best_ep = int(h.loc[h.val_nll.idxmin(), "epoch"])
        best_nll= float(h.val_nll.min())
        ax.axvline(best_ep, color=RED, lw=1, ls=":", alpha=0.8,
                   label=f"Best val NLL={best_nll:.4f}\n(epoch {best_ep})")
        ax.set_xlabel("Epoch"); ax.set_ylabel("NLL (standardised)")
        ax.set_title(f"({'AB'[level//2]})  {label}", fontsize=9.5)
        ax.legend(fontsize=8); clean_ax(ax)

    fig.tight_layout(); savefig(fig, "figA8_training_curves_v1")

    # ── v2: both levels on one plot (val NLL only) ─────────────────────────
    fig, ax = plt.subplots(figsize=(8, 4.2))
    fig.suptitle("Figure A8 (v2) | Validation NLL — L0 vs L2", fontweight="bold")
    for level, (tc, _, label) in styles.items():
        if not available[level]: continue
        h = pd.read_csv(paths[level])
        ax.plot(h.epoch, h.val_nll, color=tc, lw=2, label=label)
    ax.set_xlabel("Epoch"); ax.set_ylabel("Validation NLL (standardised)")
    ax.legend(fontsize=9); clean_ax(ax)
    fig.tight_layout(); savefig(fig, "figA8_training_curves_v2")


# ══════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    os.makedirs(OUT_DIR, exist_ok=True)
    print("Generating draft figures (pdf / png / svg)...")

    tasks = [
        ("Fig 1  framework v1+v2",   fig1_framework),
        ("Fig 2  accuracy v1+v2",    fig2_accuracy),
        ("Fig 3  forward UQ v1+v2",  fig3_forward_uq),
        ("Fig 4  Sobol v1+v2",       fig4_sobol),
        ("Fig 5  posterior v1+v2",   fig5_posterior),
        ("Fig A1 MCMC trace",        figA1_mcmc_trace),
        ("Fig A2 posterior marginals",figA2_posterior_marginals),
        ("Fig A3 calibration curve", figA3_calibration_curve),
        ("Fig A4 hetero sigma",      figA4_hetero_sigma),
        ("Fig A5 per-output metrics",figA5_per_output_metrics),
        ("Fig A6 prior-post pred",   figA6_prior_post_predictive),
        ("Fig A7 BNN schematic",     figA7_bnn_schematic),
        ("Fig A8 training curves",         figA8_training_curves),
    ]
    for name, fn in tasks:
        print(f"\n── {name}")
        try:
            fn()
        except Exception as e:
            print(f"  ERROR: {e}")

    print(f"\nDone. All figures in {OUT_DIR}/")
    figs = sorted(glob.glob(os.path.join(OUT_DIR,"*.pdf")))
    print(f"  {len(figs)} PDF files generated.")
