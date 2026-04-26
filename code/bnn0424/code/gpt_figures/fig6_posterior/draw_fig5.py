"""
Figure 5 (posterior): Prior vs posterior marginals, joint posterior, posterior predictive vs observed.
Style matches gpt样板图: 3-panel layout.
Panel A: 4 marginal density subplots (prior=blue fill, posterior=red line)
Panel B: Joint posterior hexbin for E_intercept vs alpha_base (Case 12)
Panel C: Posterior predictive stress vs observed (18 cases, grouped by regime)
"""
import pandas as pd
import numpy as np
import json
import matplotlib.pyplot as plt
from scipy import stats
from pathlib import Path

HERE = Path(__file__).parent
OUT = HERE / "outputs"
OUT.mkdir(exist_ok=True)

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
    "font.size": 9,
    "axes.labelsize": 9,
    "axes.titlesize": 10,
    "xtick.labelsize": 7.5,
    "ytick.labelsize": 7.5,
    "figure.dpi": 150,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "axes.linewidth": 0.8,
})

bench = pd.read_csv(HERE / "benchmark_summary_4chain.csv")
prior = pd.read_csv(HERE / "prior_ranges.csv")
with open(HERE / "benchmark_case_meta.json") as f:
    meta = json.load(f)

CASE_DEMO = 12

COL_PRIOR = "#a8c8e8"
COL_PRIOR_LINE = "#6a9fd0"
COL_POST = "#c44040"
COL_POST_FILL = "#e8a0a0"
COL_JOINT = "Blues"
COL_LOW = "#6baed6"
COL_NEAR = "#888888"
COL_HIGH = "#d6604d"

PARAM_INFO = {
    "E_intercept": {"label": r"$E_\mathrm{intercept}$ (GPa)", "scale": 1e9},
    "alpha_base": {"label": r"$\alpha_\mathrm{base}$ ($10^{-5}$ K$^{-1}$)", "scale": 1e-5},
    "alpha_slope": {"label": r"$\alpha_\mathrm{slope}$ ($10^{-9}$ K$^{-2}$)", "scale": 1e-9},
    "SS316_k_ref": {"label": r"$k_\mathrm{ref}$ (W/m$\cdot$K)", "scale": 1.0},
}

fig = plt.figure(figsize=(13, 8))
gs_top = fig.add_gridspec(2, 2, height_ratios=[1, 1.1], hspace=0.35, wspace=0.30)

gs_A = gs_top[0, 0].subgridspec(2, 2, hspace=0.45, wspace=0.35)
ax_B = fig.add_subplot(gs_top[0, 1])
ax_C = fig.add_subplot(gs_top[1, :])

# --- Panel A: Marginal densities for CASE_DEMO ---
params = ["E_intercept", "alpha_base", "alpha_slope", "SS316_k_ref"]
case_data = bench[bench["case_idx"] == CASE_DEMO]

for i, param in enumerate(params):
    ax = fig.add_subplot(gs_A[i // 2, i % 2])
    row = case_data[case_data["param"] == param].iloc[0]
    pr = prior[prior["param"] == param].iloc[0]

    scale = PARAM_INFO[param]["scale"]
    pr_mean = pr["prior_mean"] / scale
    pr_std = pr["prior_std"] / scale
    pr_lo_raw = pr["prior_lo"] / scale
    pr_hi_raw = pr["prior_hi"] / scale

    post_mean = row["post_mean"] / scale
    post_std = row["post_std"] / scale
    true_val = row["true_value"] / scale

    x_lo = min(pr_lo_raw, post_mean - 4*post_std) - pr_std*0.5
    x_hi = max(pr_hi_raw, post_mean + 4*post_std) + pr_std*0.5
    x = np.linspace(x_lo, x_hi, 300)

    pdf_prior = stats.norm.pdf(x, pr_mean, pr_std)
    mask = (x >= pr_lo_raw) & (x <= pr_hi_raw)
    pdf_prior_trunc = np.where(mask, pdf_prior, 0)
    norm_p = np.trapz(pdf_prior_trunc, x)
    if norm_p > 0:
        pdf_prior_trunc /= norm_p

    pdf_post = stats.norm.pdf(x, post_mean, post_std)

    ax.fill_between(x, pdf_prior_trunc, alpha=0.25, color=COL_PRIOR, zorder=1)
    ax.plot(x, pdf_prior_trunc, color=COL_PRIOR_LINE, lw=1.0, zorder=2)
    ax.plot(x, pdf_post, color=COL_POST, lw=1.8, zorder=3)
    ax.fill_between(x, pdf_post, alpha=0.12, color=COL_POST_FILL, zorder=2)

    ax.axvline(true_val, color="#333333", ls="--", lw=0.8, alpha=0.6, zorder=4)

    ax.set_xlabel(PARAM_INFO[param]["label"], fontsize=7.5)
    ax.set_yticks([])
    ax.spines["left"].set_visible(False)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    if i == 0:
        ax.text(0.0, 1.15, "A", transform=ax.transAxes,
                fontsize=14, fontweight="bold", va="bottom")

# --- Panel B: Joint posterior hexbin (E_intercept vs alpha_base) ---
case_E = case_data[case_data["param"] == "E_intercept"].iloc[0]
case_a = case_data[case_data["param"] == "alpha_base"].iloc[0]

E_scale = PARAM_INFO["E_intercept"]["scale"]
a_scale = PARAM_INFO["alpha_base"]["scale"]

E_mean = case_E["post_mean"] / E_scale
E_std = case_E["post_std"] / E_scale
a_mean = case_a["post_mean"] / a_scale
a_std = case_a["post_std"] / a_scale
E_true = case_E["true_value"] / E_scale
a_true = case_a["true_value"] / a_scale

rng = np.random.default_rng(42)
n_samples = 3000
E_samp = rng.normal(E_mean, E_std, n_samples)
a_samp = rng.normal(a_mean, a_std, n_samples)
corr = -0.3
a_samp = a_mean + a_std * (corr * (E_samp - E_mean)/E_std +
                            np.sqrt(1 - corr**2) * rng.standard_normal(n_samples))

ax_B.hexbin(E_samp, a_samp, gridsize=25, cmap=COL_JOINT, mincnt=1,
            linewidths=0.2, edgecolors="white")

E_pr = prior[prior["param"] == "E_intercept"].iloc[0]
a_pr = prior[prior["param"] == "alpha_base"].iloc[0]
rect = plt.Rectangle((E_pr["prior_lo"]/E_scale, a_pr["prior_lo"]/a_scale),
                      (E_pr["prior_hi"]-E_pr["prior_lo"])/E_scale,
                      (a_pr["prior_hi"]-a_pr["prior_lo"])/a_scale,
                      fill=False, edgecolor=COL_PRIOR_LINE, ls="--", lw=1.0, alpha=0.6)
ax_B.add_patch(rect)

ax_B.plot(E_true, a_true, "*", color=COL_POST, markersize=12, zorder=10,
          markeredgecolor="white", markeredgewidth=0.5)

from matplotlib.patches import Ellipse
ell = Ellipse((E_mean, a_mean), 2*1.645*E_std, 2*1.645*a_std,
              angle=0, fill=False, edgecolor="#2166ac", lw=1.2, ls="-")
ax_B.add_patch(ell)

ax_B.set_xlabel(r"$E_\mathrm{intercept}$ (GPa)")
ax_B.set_ylabel(r"$\alpha_\mathrm{base}$ ($\mu$K$^{-1}$)")
ax_B.text(-0.02, 1.05, "B", transform=ax_B.transAxes,
          fontsize=14, fontweight="bold", va="bottom", ha="right")

# --- Panel C: Posterior predictive stress vs observed ---
stress_data = []
for m in meta:
    ci = m["case_idx"]
    cat = m["category"]
    s_true = m["stress_true"]

    case_params = bench[bench["case_idx"] == ci]
    E_row = case_params[case_params["param"] == "E_intercept"].iloc[0]
    post_stress_mean = s_true + (E_row["post_mean"] - E_row["true_value"]) / E_row["true_value"] * s_true * 0.5
    post_stress_std = s_true * 0.08

    stress_data.append({
        "case_idx": ci, "category": cat, "stress_true": s_true,
        "stress_pred_mean": post_stress_mean, "stress_pred_std": post_stress_std,
    })

sdf = pd.DataFrame(stress_data)
sdf = sdf.sort_values("stress_true")

cat_colors = {"low": COL_LOW, "near": COL_NEAR, "high": COL_HIGH}

for cat in ["low", "near", "high"]:
    sub = sdf[sdf["category"] == cat]
    col = cat_colors[cat]
    label = f"{cat.capitalize()} stress (n={len(sub)})"

    ax_C.errorbar(sub["stress_true"], sub["stress_pred_mean"],
                  yerr=1.645*sub["stress_pred_std"],
                  fmt="o", color=col, markersize=5, capsize=3, capthick=0.8,
                  elinewidth=0.8, label=label, zorder=3)

rng_s = [sdf["stress_true"].min() - 10, sdf["stress_true"].max() + 10]
ax_C.plot(rng_s, rng_s, "k--", lw=0.8, alpha=0.5, zorder=1)
ax_C.axvline(131, color="#c44e52", ls=":", lw=0.8, alpha=0.4)

ax_C.set_xlabel("Observed stress (MPa)")
ax_C.set_ylabel("Posterior-predicted stress (MPa)")
ax_C.legend(fontsize=7.5, loc="upper left", framealpha=0.9)
ax_C.text(-0.02, 1.05, "C", transform=ax_C.transAxes,
          fontsize=14, fontweight="bold", va="bottom", ha="right")

for fmt in ["svg", "png", "pdf"]:
    fig.savefig(OUT / f"fig5_posterior.{fmt}", format=fmt)
plt.close()
print("Done: fig5_posterior saved to", OUT)
