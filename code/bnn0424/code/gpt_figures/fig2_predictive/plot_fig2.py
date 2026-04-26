#!/usr/bin/env python3
"""Figure 2: Posterior predictive behaviour of the selected Bayesian surrogate.

Panels A-C: parity hexbin with per-panel color schemes (blue/purple/orange).
Panel D: interval-quality summary strip (PICP90, BNN vs baselines).

Style: NCS unified via _shared/ncs_style.
"""

import sys
import pathlib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, hex2color
import matplotlib.gridspec as gridspec

# ── shared style ──
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "_shared"))
import ncs_style
ncs_style.apply_style()

OUT = HERE / "outputs"
OUT.mkdir(exist_ok=True)

# ── data ──
df = pd.read_csv(HERE / "parity_data_phy_mono.csv")
iq = pd.read_csv(HERE / "interval_quality_data.csv")

# ── per-panel colormaps (white → dark gradient) ──
def _make_cmap(hex_dark, name):
    r, g, b = hex2color(hex_dark)
    colors = [(1, 1, 1, 0), (r, g, b, 0.25), (r, g, b, 0.6), (r, g, b, 1.0)]
    return LinearSegmentedColormap.from_list(name, colors, N=256)

CMAP_BLUE   = _make_cmap("#1B3A5C", "blue_mono")    # stress
CMAP_PURPLE = _make_cmap("#4A2C6B", "purple_mono")   # keff
CMAP_ORANGE = _make_cmap("#8B4513", "orange_mono")   # fuel temp

PI_BLUE   = ncs_style.BLUE_PALE       # "#C5DAE9"
PI_PURPLE = "#D4C5E8"
PI_ORANGE = "#F2D6BC"

# ── output configs with per-panel color scheme ──
PANELS = {
    "iteration2_max_global_stress": dict(
        label="Max global stress", unit="MPa",
        cmap=CMAP_BLUE, pi_color=PI_BLUE,
    ),
    "iteration2_keff": dict(
        label=r"Effective multiplication factor, $k_\mathrm{eff}$", unit="",
        cmap=CMAP_PURPLE, pi_color=PI_PURPLE,
    ),
    "iteration2_max_fuel_temp": dict(
        label="Max fuel temperature", unit="K",
        cmap=CMAP_ORANGE, pi_color=PI_ORANGE,
    ),
}

# ── layout ──
fig = plt.figure(figsize=(7.1, 8.2), constrained_layout=False)
gs_top = gridspec.GridSpec(1, 2, figure=fig,
                           left=0.10, right=0.96, top=0.95, bottom=0.42,
                           width_ratios=[1.5, 1], wspace=0.42)
gs_br = gridspec.GridSpecFromSubplotSpec(2, 1, subplot_spec=gs_top[1],
                                         hspace=0.50)
gs_bot = gridspec.GridSpec(1, 1, figure=fig,
                           left=0.18, right=0.96, top=0.34, bottom=0.05)

ax_a = fig.add_subplot(gs_top[0])
ax_b = fig.add_subplot(gs_br[0])
ax_c = fig.add_subplot(gs_br[1])
ax_d = fig.add_subplot(gs_bot[0])

# ── helper: parity hexbin with PI ──
def plot_parity(ax, output_key, cfg, panel_letter):
    sub = df[df["output"] == output_key].copy()
    y_true = sub["y_true"].values
    y_pred = sub["y_pred_mean"].values
    y_std  = sub["y_pred_std"].values
    y_lo = y_pred - 1.645 * y_std
    y_hi = y_pred + 1.645 * y_std

    lo = min(y_true.min(), y_pred.min(), y_lo.min())
    hi = max(y_true.max(), y_pred.max(), y_hi.max())
    margin = (hi - lo) * 0.05
    lo -= margin; hi += margin

    # Per-panel color scheme
    panel_cmap = cfg["cmap"]
    panel_pi   = cfg["pi_color"]

    sort_idx = np.argsort(y_true)
    ax.fill_between(y_true[sort_idx], y_lo[sort_idx], y_hi[sort_idx],
                    color=panel_pi, alpha=0.30,
                    label="90% predictive interval", zorder=1)

    gridsize = 30 if panel_letter == "A" else 22
    hb = ax.hexbin(y_true, y_pred, gridsize=gridsize, cmap=panel_cmap,
                   mincnt=1, linewidths=0.2, edgecolors="white", zorder=2)

    ax.plot([lo, hi], [lo, hi], ls="--", lw=ncs_style.LW_SECONDARY,
            color=ncs_style.GRAY_500, zorder=3, label=r"$y = x$")
    ax.set_xlim(lo, hi); ax.set_ylim(lo, hi)
    ax.set_aspect("equal", adjustable="box")

    unit_str = f" ({cfg['unit']})" if cfg["unit"] else ""
    ax.set_xlabel(f"High-fidelity simulation{unit_str}", labelpad=4)
    ax.set_ylabel(f"BNN predictive mean{unit_str}", labelpad=4)

    # Metrics
    r2 = 1 - np.sum((y_true - y_pred)**2) / np.sum((y_true - y_true.mean())**2)
    rmse = np.sqrt(np.mean((y_true - y_pred)**2))
    picp = np.mean((y_true >= y_lo) & (y_true <= y_hi))

    if cfg["unit"]:
        rmse_str = f"RMSE = {rmse:.2f} {cfg['unit']}"
    else:
        rmse_str = f"RMSE = {rmse:.2e}"

    metric_str = f"R\u00b2 = {r2:.3f}\n{rmse_str}\nPICP90 = {picp:.3f}"
    # Metric text with subtle bordered box
    metric_bbox = dict(boxstyle="round,pad=0.3", facecolor="white",
                       edgecolor=ncs_style.GRAY_300, alpha=0.85, linewidth=0.6)
    ax.text(0.04, 0.96, metric_str, transform=ax.transAxes,
            fontsize=ncs_style.FONT_METRIC, va="top", ha="left",
            fontfamily="monospace", color=ncs_style.GRAY_900,
            bbox=metric_bbox)

    # Bold uppercase panel label (A, B, C)
    ax.text(-0.08, 1.06, panel_letter, transform=ax.transAxes,
            fontsize=ncs_style.FONT_PANEL_LABEL, fontweight="bold",
            va="bottom", ha="right", color=ncs_style.GRAY_900)
    ax.set_title(cfg["label"], fontsize=ncs_style.FONT_AXIS_LABEL,
                 fontweight="bold", loc="left", pad=6)

    return hb

# ── panels A-C ──
outputs = list(PANELS.keys())
letters = ["A", "B", "C"]
axes = [ax_a, ax_b, ax_c]
for ax, out, letter in zip(axes, outputs, letters):
    hb = plot_parity(ax, out, PANELS[out], letter)

# legend only on panel A
ax_a.legend(loc="lower right", fontsize=ncs_style.FONT_LEGEND, frameon=False)

# ── panel (d): interval-quality strip ──
OUTPUT_ORDER = [
    "iteration2_max_global_stress",
    "iteration2_keff",
    "iteration2_max_fuel_temp",
    "iteration2_max_monolith_temp",
    "iteration2_wall2",
]
OUTPUT_SHORT = {
    "iteration2_max_global_stress": "Max stress",
    "iteration2_keff": r"$k_\mathrm{eff}$",
    "iteration2_max_fuel_temp": "Max fuel temp",
    "iteration2_max_monolith_temp": "Max monolith temp",
    "iteration2_wall2": "Wall expansion",
}
MODELS = [
    ("bnn-phy-mono",   "Physics-reg. BNN",  ncs_style.BLUE_DARK,  "o"),
    ("mc-dropout",     "MC-Dropout",         ncs_style.GRAY_500,   "s"),
    ("deep-ensemble",  "Deep Ensemble",      ncs_style.GRAY_300,   "D"),
]

y_positions = np.arange(len(OUTPUT_ORDER))

ax_d.axvspan(0.58, 0.90, color=ncs_style.BLUE_WASH, alpha=0.45, zorder=0)
ax_d.axvline(0.90, color=ncs_style.GRAY_500, ls="--",
             lw=ncs_style.LW_SECONDARY, zorder=1)

for i, (mid, mlabel, mcolor, mmarker) in enumerate(MODELS):
    sub = iq[iq["model_id"] == mid]
    picp_vals = []
    for out in OUTPUT_ORDER:
        row = sub[sub["output"] == out]
        if len(row) > 0:
            picp_vals.append(row["PICP90"].values[0])
        else:
            picp_vals.append(np.nan)
    offset = (i - 1) * 0.24
    ax_d.scatter(picp_vals, y_positions + offset, marker=mmarker,
                 s=36, color=mcolor, edgecolors="white", linewidths=0.4,
                 label=mlabel, zorder=3)

ax_d.set_yticks(y_positions)
ax_d.set_yticklabels([OUTPUT_SHORT[o] for o in OUTPUT_ORDER])
ax_d.set_xlabel("PICP90 (empirical coverage at 90% nominal level)",
                labelpad=4)
ax_d.set_xlim(0.58, 1.03)
ax_d.set_ylim(len(OUTPUT_ORDER) - 0.6, -0.6)

ax_d.legend(loc="lower left", fontsize=ncs_style.FONT_LEGEND, frameon=False,
            ncol=3, columnspacing=1.0, handletextpad=0.4)

ax_d.text(-0.14, 1.06, "D", transform=ax_d.transAxes,
          fontsize=ncs_style.FONT_PANEL_LABEL, fontweight="bold",
          va="bottom", ha="right", color=ncs_style.GRAY_900)
ax_d.set_title("Interval calibration across five coupled outputs",
               fontsize=ncs_style.FONT_AXIS_LABEL, fontweight="bold",
               loc="left", pad=6)

ax_d.annotate("", xy=(0.90, -0.35), xytext=(0.58, -0.35),
              arrowprops=dict(arrowstyle="<->", color=ncs_style.GRAY_300, lw=0.7))
ax_d.text(0.74, -0.42, "under-covered", fontsize=6.5,
          color=ncs_style.GRAY_500, ha="center", va="top", fontstyle="italic")
ax_d.text(0.893, 2.0, "nominal 90%", fontsize=6.5,
          color=ncs_style.GRAY_500, ha="right", va="center", rotation=90)

# ── save ──
ncs_style.save_all(fig, "fig2_surrogate_selection", OUT)
plt.close(fig)
