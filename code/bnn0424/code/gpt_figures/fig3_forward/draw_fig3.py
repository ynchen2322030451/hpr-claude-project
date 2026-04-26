"""
Figure 3: Forward UQ — coupling reshapes response distributions.
Style matches gpt样板图: 3-panel (stress violin, keff density, fuel temp density).
Colors: blue=coupled, light gray/orange=uncoupled/decoupled.
"""
import pandas as pd
import numpy as np
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
    "axes.labelsize": 10,
    "axes.titlesize": 11,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "figure.dpi": 150,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "axes.linewidth": 0.8,
})

uq = pd.read_csv(HERE / "forward_uq_alloutput.csv")
pred = pd.read_csv(HERE / "forward_uq_alloutput_predictive.csv")

stress = uq[uq["output"] == "max_global_stress"].iloc[0]
keff_row = uq[uq["output"] == "keff"] if "keff" in uq["output"].values else None

stress_pred = pred[pred["label"].str.contains("stress", case=False)].iloc[0]

fig = plt.figure(figsize=(12, 4.5))
gs = fig.add_gridspec(1, 3, width_ratios=[1.2, 0.9, 0.9], wspace=0.35)

COL_COUPLED = "#3b7dd8"
COL_DECOUPLED = "#b0b0b0"
COL_COUPLED_FILL = "#a8c8f0"
COL_DECOUPLED_FILL = "#d8d8d8"
COL_KEFF = "#e07020"
COL_KEFF_FILL = "#f0c8a0"
COL_TEMP = "#c44e52"
COL_TEMP_FILL = "#f0b0b0"

# --- Panel A: Stress distribution (uncoupled vs coupled) ---
ax_A = fig.add_subplot(gs[0])

c_mean, c_std = stress_pred["coupled_mean"], stress_pred["coupled_std"]
d_mean, d_std = stress_pred["decoupled_mean"], stress_pred["decoupled_std"]

x_lo = min(d_mean - 4*d_std, c_mean - 4*c_std)
x_hi = max(d_mean + 4*d_std, c_mean + 4*c_std)
x = np.linspace(x_lo, x_hi, 500)

pdf_dec = stats.norm.pdf(x, d_mean, d_std)
pdf_cpl = stats.norm.pdf(x, c_mean, c_std)

ax_A.fill_between(x, pdf_dec, alpha=0.25, color=COL_DECOUPLED, zorder=1)
ax_A.plot(x, pdf_dec, color=COL_DECOUPLED, lw=1.5, label="Uncoupled pass", zorder=2)
ax_A.fill_between(x, pdf_cpl, alpha=0.30, color=COL_COUPLED, zorder=3)
ax_A.plot(x, pdf_cpl, color=COL_COUPLED, lw=1.5, label="Coupled steady state", zorder=4)

ax_A.axvline(131, color="#c44e52", ls="--", lw=1.0, alpha=0.7, zorder=5)

p5_c = c_mean - 1.645 * c_std
p95_c = c_mean + 1.645 * c_std
p5_d = d_mean - 1.645 * d_std
p95_d = d_mean + 1.645 * d_std

y_ann = max(pdf_cpl.max(), pdf_dec.max()) * 0.55
ax_A.annotate("", xy=(p5_c, y_ann), xytext=(p95_c, y_ann),
              arrowprops=dict(arrowstyle="<->", color=COL_COUPLED, lw=1.2))
y_ann2 = max(pdf_cpl.max(), pdf_dec.max()) * 0.45
ax_A.annotate("", xy=(p5_d, y_ann2), xytext=(p95_d, y_ann2),
              arrowprops=dict(arrowstyle="<->", color=COL_DECOUPLED, lw=1.2))

delta_mean = c_mean - d_mean
std_red = (1 - c_std / d_std) * 100
ax_A.text(0.03, 0.95,
          f"$\\Delta\\mu$ = {delta_mean:.0f} MPa\nSpread reduced {std_red:.0f}%",
          transform=ax_A.transAxes, fontsize=8, va="top",
          bbox=dict(facecolor="white", alpha=0.8, edgecolor="none"))

ax_A.set_xlabel("Max stress (MPa)")
ax_A.set_ylabel("Probability density")
ax_A.legend(fontsize=7.5, loc="upper right", framealpha=0.9)
ax_A.set_yticks([])
ax_A.text(-0.02, 1.05, "A", transform=ax_A.transAxes,
          fontsize=14, fontweight="bold", va="bottom", ha="right")

# --- Panel B: keff distribution (coupled only) ---
ax_B = fig.add_subplot(gs[1])

keff_mean = 1.10354
keff_std = 0.000773

x_k = np.linspace(keff_mean - 4*keff_std, keff_mean + 4*keff_std, 500)
pdf_k = stats.norm.pdf(x_k, keff_mean, keff_std)

ax_B.fill_between(x_k, pdf_k, alpha=0.30, color=COL_KEFF, zorder=1)
ax_B.plot(x_k, pdf_k, color=COL_KEFF, lw=1.5, zorder=2)

ax_B.text(0.95, 0.90,
          f"Mean = {keff_mean:.4f}\nStd = {keff_std:.1e}\n(approximately\nGaussian)",
          transform=ax_B.transAxes, fontsize=7.5, va="top", ha="right",
          bbox=dict(facecolor="white", alpha=0.8, edgecolor="none"))

p5_k = keff_mean - 1.645 * keff_std
p95_k = keff_mean + 1.645 * keff_std
ax_B.axvline(p5_k, color=COL_KEFF, ls=":", lw=0.8, alpha=0.5)
ax_B.axvline(p95_k, color=COL_KEFF, ls=":", lw=0.8, alpha=0.5)

locs = ax_B.get_xticks()
ax_B.set_xlabel(r"$k_\mathrm{eff}$: coupled steady state")
ax_B.set_ylabel("Probability density")
ax_B.set_yticks([])
ax_B.text(-0.02, 1.05, "B", transform=ax_B.transAxes,
          fontsize=14, fontweight="bold", va="bottom", ha="right")

# --- Panel C: Fuel temperature distribution (coupled) ---
ax_C = fig.add_subplot(gs[2])

ft_row = pred[pred["label"].str.contains("fuel temp", case=False)].iloc[0]
ft_c_mean = ft_row["coupled_mean"]
ft_c_std = ft_row["coupled_std"]
ft_d_mean = ft_row["decoupled_mean"]
ft_d_std = ft_row["decoupled_std"]

x_lo_t = min(ft_d_mean - 4*ft_d_std, ft_c_mean - 4*ft_c_std)
x_hi_t = max(ft_d_mean + 4*ft_d_std, ft_c_mean + 4*ft_c_std)
x_t = np.linspace(x_lo_t, x_hi_t, 500)

pdf_t_dec = stats.norm.pdf(x_t, ft_d_mean, ft_d_std)
pdf_t_cpl = stats.norm.pdf(x_t, ft_c_mean, ft_c_std)

ax_C.fill_between(x_t, pdf_t_dec, alpha=0.20, color=COL_DECOUPLED, zorder=1)
ax_C.plot(x_t, pdf_t_dec, color=COL_DECOUPLED, lw=1.5, label="Uncoupled pass", zorder=2)
ax_C.fill_between(x_t, pdf_t_cpl, alpha=0.30, color=COL_TEMP, zorder=3)
ax_C.plot(x_t, pdf_t_cpl, color=COL_TEMP, lw=1.5, label="Coupled steady state", zorder=4)

p5_tc = ft_c_mean - 1.645 * ft_c_std
p95_tc = ft_c_mean + 1.645 * ft_c_std
ax_C.axvline(p5_tc, color=COL_TEMP, ls=":", lw=0.8, alpha=0.5)
ax_C.axvline(p95_tc, color=COL_TEMP, ls=":", lw=0.8, alpha=0.5)

ax_C.text(0.95, 0.90,
          f"Mean = {ft_c_mean:.1f} K\nStd = {ft_c_std:.2f} K\nP5–P95 = {p5_tc:.0f}–{p95_tc:.0f} K",
          transform=ax_C.transAxes, fontsize=7.5, va="top", ha="right",
          bbox=dict(facecolor="white", alpha=0.8, edgecolor="none"))

ax_C.set_xlabel("Max fuel temperature (K)")
ax_C.set_ylabel("Probability density")
ax_C.legend(fontsize=7.5, loc="upper left", framealpha=0.9)
ax_C.set_yticks([])
ax_C.text(-0.02, 1.05, "C", transform=ax_C.transAxes,
          fontsize=14, fontweight="bold", va="bottom", ha="right")

for fmt in ["svg", "png", "pdf"]:
    fig.savefig(OUT / f"fig3_forward.{fmt}", format=fmt)
plt.close()
print("Done: fig3_forward saved to", OUT)
