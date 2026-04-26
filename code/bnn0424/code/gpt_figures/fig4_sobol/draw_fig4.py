"""
Figure 4: Sobol sensitivity — dominant-factor separation between stress and keff.
Style matches gpt样板图: horizontal bars with S1 (points) and ST (shaded bands),
90% CI error bars. Panel C = summary box.
Colors: orange for thermal-expansion params, teal for elastic/structural, dark for conductivity.
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
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

df = pd.read_csv(HERE / "sobol_stress_keff.csv")

PARAM_LABELS = {
    "E_intercept": r"$E_\mathrm{intercept}$",
    "E_slope": r"$E_\mathrm{slope}$",
    "nu": r"$\nu$",
    "alpha_base": r"$\alpha_\mathrm{base}$",
    "alpha_slope": r"$\alpha_\mathrm{slope}$",
    "SS316_T_ref": r"$T_\mathrm{ref}$",
    "SS316_k_ref": r"$k_\mathrm{ref}$",
    "SS316_alpha": r"$\alpha_\mathrm{SS316}$",
}

PARAM_GROUP = {
    "E_intercept": "elastic", "E_slope": "elastic", "nu": "elastic",
    "alpha_base": "thermal_exp", "alpha_slope": "thermal_exp",
    "SS316_T_ref": "conductivity", "SS316_k_ref": "conductivity",
    "SS316_alpha": "conductivity",
}

GROUP_COLORS = {
    "elastic": "#2b8c6e",
    "thermal_exp": "#e8883a",
    "conductivity": "#7b5ea7",
}

STRESS_ORDER = ["E_intercept", "alpha_base", "SS316_k_ref", "nu",
                "E_slope", "alpha_slope", "SS316_T_ref", "SS316_alpha"]
KEFF_ORDER = ["alpha_base", "alpha_slope", "nu", "SS316_T_ref",
              "E_intercept", "E_slope", "SS316_k_ref", "SS316_alpha"]


def draw_sobol_panel(ax, data, param_order, title):
    n = len(param_order)
    y_pos = np.arange(n)[::-1]

    for i, param in enumerate(param_order):
        row = data[data["input"] == param]
        if row.empty:
            continue
        row = row.iloc[0]
        y = y_pos[i]
        grp = PARAM_GROUP[param]
        col = GROUP_COLORS[grp]

        st_lo = row["ST_ci_lo"]
        st_hi = row["ST_ci_hi"]
        ax.barh(y, row["ST_mean"], height=0.55, color=col, alpha=0.25,
                edgecolor="none", zorder=1)
        ax.barh(y, row["ST_mean"], height=0.55, color="none",
                edgecolor=col, linewidth=0.8, linestyle="--", zorder=2)

        s1 = row["S1_mean"]
        s1_lo = row["S1_ci_lo"]
        s1_hi = row["S1_ci_hi"]
        ax.plot(s1, y, "o", color=col, markersize=5, zorder=4)
        ax.plot([s1_lo, s1_hi], [y, y], "-", color=col, lw=1.2, zorder=3)

        spans_zero = row.get("S1_ci_spans_zero", False)
        if spans_zero:
            ax.plot(s1, y, "o", color="white", markersize=3, zorder=5)

    ax.set_yticks(y_pos)
    ax.set_yticklabels([PARAM_LABELS.get(p, p) for p in param_order])
    ax.set_xlabel("Sobol index")
    ax.set_title(title, fontsize=10, fontweight="bold", pad=8)
    ax.axvline(0, color="gray", lw=0.5, ls="-", alpha=0.3)
    ax.set_xlim(-0.05, None)


fig = plt.figure(figsize=(12, 5.5))
gs = fig.add_gridspec(1, 3, width_ratios=[1, 1, 0.65], wspace=0.40)

stress_data = df[df["output"] == "iteration2_max_global_stress"]
keff_data = df[df["output"] == "iteration2_keff"]

ax_A = fig.add_subplot(gs[0])
draw_sobol_panel(ax_A, stress_data, STRESS_ORDER, "Coupled maximum stress")
ax_A.text(-0.15, 1.05, "A", transform=ax_A.transAxes,
          fontsize=14, fontweight="bold", va="bottom")

ax_B = fig.add_subplot(gs[1])
draw_sobol_panel(ax_B, keff_data, KEFF_ORDER,
                 r"$k_\mathrm{eff}$ (coupled)")
ax_B.text(-0.15, 1.05, "B", transform=ax_B.transAxes,
          fontsize=14, fontweight="bold", va="bottom")

# --- Panel C: Summary ---
ax_C = fig.add_subplot(gs[2])
ax_C.axis("off")

stress_top = stress_data.nlargest(2, "S1_mean")
keff_top = keff_data.nlargest(2, "S1_mean")

summary_text = (
    "Dominant-factor separation\n"
    "━━━━━━━━━━━━━━━━━━━━━━\n\n"
    "Stress — top 2 (by $S_1$):\n"
)
for _, r in stress_top.iterrows():
    lab = PARAM_LABELS.get(r["input"], r["input"])
    summary_text += f"  {lab}: {r['S1_mean']:.3f}\n"

summary_text += (
    f"\n$k_\\mathrm{{eff}}$ — top 2 (by $S_1$):\n"
)
for _, r in keff_top.iterrows():
    lab = PARAM_LABELS.get(r["input"], r["input"])
    summary_text += f"  {lab}: {r['S1_mean']:.3f}\n"

summary_text += (
    "\nDistinct dominant\n"
    "pathways for two\n"
    "key outputs"
)

ax_C.text(0.05, 0.95, summary_text, transform=ax_C.transAxes,
          fontsize=8, va="top", ha="left", family="monospace",
          bbox=dict(facecolor="#fafafa", edgecolor="#cccccc",
                    boxstyle="round,pad=0.5"))
ax_C.text(-0.05, 1.05, "C", transform=ax_C.transAxes,
          fontsize=14, fontweight="bold", va="bottom")

legend_patches = [
    mpatches.Patch(color=GROUP_COLORS["elastic"], label="Elastic / structural"),
    mpatches.Patch(color=GROUP_COLORS["thermal_exp"], label="Thermal expansion"),
    mpatches.Patch(color=GROUP_COLORS["conductivity"], label="Conductivity"),
]
fig.legend(handles=legend_patches, loc="lower center", ncol=3,
           fontsize=8, framealpha=0.9, bbox_to_anchor=(0.42, -0.02))

for fmt in ["svg", "png", "pdf"]:
    fig.savefig(OUT / f"fig4_sobol.{fmt}", format=fmt)
plt.close()
print("Done: fig4_sobol saved to", OUT)
