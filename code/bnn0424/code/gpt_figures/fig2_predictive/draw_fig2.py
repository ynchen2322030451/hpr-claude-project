"""
Figure 2: Posterior predictive behavior — parity plots for stress, keff, fuel temp.
Style matches gpt样板图: hexbin scatter, 90% PI band, y=x dashed line.
Colors: blue for stress, teal for keff, purple for fuel temp.
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
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
    "xtick.major.width": 0.6,
    "ytick.major.width": 0.6,
})

df = pd.read_csv(HERE / "parity_data_phy_mono.csv")
met = pd.read_csv(HERE / "metrics_summary.csv")
met = met[met["model_id"] == "bnn-phy-mono"]

outputs = {
    "iteration2_max_global_stress": {"label": "Max stress", "unit": "MPa",
                                      "cmap": "Blues", "accent": "#2166ac"},
    "iteration2_keff": {"label": r"$k_\mathrm{eff}$", "unit": "",
                        "cmap": "GnBu", "accent": "#1b7837"},
    "iteration2_max_fuel_temp": {"label": "Max fuel temp", "unit": "K",
                                  "cmap": "Purples", "accent": "#762a83"},
}

fig = plt.figure(figsize=(10, 7.5))
gs = fig.add_gridspec(2, 2, width_ratios=[1.4, 1], height_ratios=[1, 1],
                      hspace=0.30, wspace=0.30)
ax_A = fig.add_subplot(gs[:, 0])
ax_B = fig.add_subplot(gs[0, 1])
ax_C = fig.add_subplot(gs[1, 1])
axes = [ax_A, ax_B, ax_C]
labels_panel = ["A", "B", "C"]

for ax, (out_key, cfg), panel_label in zip(axes, outputs.items(), labels_panel):
    sub = df[df["output"] == out_key].copy()
    m = met[met["output"] == out_key].iloc[0]

    y_true = sub["y_true"].values
    y_pred = sub["y_pred_mean"].values
    y_std = sub["y_pred_std"].values

    lo = y_pred - 1.645 * y_std
    hi = y_pred + 1.645 * y_std

    sort_idx = np.argsort(y_true)
    yt_s = y_true[sort_idx]
    lo_s = lo[sort_idx]
    hi_s = hi[sort_idx]

    # Smooth PI bands with rolling window to remove jaggedness
    win = max(len(yt_s) // 25, 5)
    lo_smooth = pd.Series(lo_s).rolling(win, center=True, min_periods=1).mean().values
    hi_smooth = pd.Series(hi_s).rolling(win, center=True, min_periods=1).mean().values

    ax.fill_between(yt_s, lo_smooth, hi_smooth, alpha=0.18, color=cfg["accent"],
                     label="90% predictive interval", zorder=1)

    cmap = plt.get_cmap(cfg["cmap"])
    norm_cmap = mcolors.Normalize(vmin=0, vmax=1)
    hb = ax.hexbin(y_true, y_pred, gridsize=30, cmap=cmap, mincnt=1,
                   linewidths=0.2, edgecolors="white", zorder=2)

    rng = [min(y_true.min(), y_pred.min()), max(y_true.max(), y_pred.max())]
    margin = (rng[1] - rng[0]) * 0.05
    rng = [rng[0] - margin, rng[1] + margin]
    ax.plot(rng, rng, "k--", lw=0.8, alpha=0.6, zorder=3)

    ax.set_xlim(rng)
    ax.set_ylim(rng)

    unit_str = f" ({cfg['unit']})" if cfg["unit"] else ""
    ax.set_xlabel(f"High-fidelity simulation{unit_str}")
    ax.set_ylabel(f"BNN predictive mean{unit_str}")

    info = (f"$R^2$ = {m['R2']:.3f}\n"
            f"RMSE = {m['RMSE']:.2e}\n"
            f"PICP$_{{90}}$ = {m['PICP']*100:.1f}%")
    if out_key == "iteration2_max_global_stress":
        info = (f"$R^2$ = {m['R2']:.3f}\n"
                f"RMSE = {m['RMSE']:.2f} MPa\n"
                f"PICP$_{{90}}$ = {m['PICP']*100:.1f}%")
    elif out_key == "iteration2_max_fuel_temp":
        info = (f"$R^2$ = {m['R2']:.3f}\n"
                f"RMSE = {m['RMSE']:.2f} K\n"
                f"PICP$_{{90}}$ = {m['PICP']*100:.1f}%")

    anchor = (0.97, 0.03) if panel_label == "A" else (0.97, 0.03)
    ax.text(anchor[0], anchor[1], info, transform=ax.transAxes,
            fontsize=7.5, va="bottom", ha="right",
            bbox=dict(facecolor="white", alpha=0.85, edgecolor="none", pad=2))

    ax.text(-0.02, 1.05, panel_label, transform=ax.transAxes,
            fontsize=14, fontweight="bold", va="bottom", ha="right")

for fmt in ["svg", "png", "pdf"]:
    fig.savefig(OUT / f"fig2_predictive.{fmt}", format=fmt)
plt.close()
print("Done: fig2_predictive saved to", OUT)
