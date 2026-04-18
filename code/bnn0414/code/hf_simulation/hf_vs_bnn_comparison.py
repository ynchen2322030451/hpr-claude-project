"""
Compare HF-based sensitivity (SRC²) with BNN-based Sobol S₁.

SRC² approximates the first-order variance contribution for linear models,
making it comparable to Sobol S₁ when the input-output mapping is
approximately additive.
"""

import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

INPUT_COLS = [
    "E_slope", "E_intercept", "nu", "alpha_base",
    "alpha_slope", "SS316_T_ref", "SS316_k_ref", "SS316_alpha",
]

PAPER_NAMES = {
    "E_slope": r"$E_\mathrm{slope}$",
    "E_intercept": r"$E_\mathrm{intercept}$",
    "nu": r"$\nu$",
    "alpha_base": r"$\alpha_\mathrm{base}$",
    "alpha_slope": r"$\alpha_\mathrm{slope}$",
    "SS316_T_ref": r"$T_\mathrm{ref}$",
    "SS316_k_ref": r"$k_\mathrm{ref}$",
    "SS316_alpha": r"$k_\mathrm{slope}$",
}

def main():
    base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    src_csv = os.path.join(base, "results", "hf_sensitivity", "src_results.csv")
    sobol_csv = os.path.join(base, "results", "sensitivity", "sobol_convergence.csv")
    out_dir = os.path.join(base, "results", "hf_sensitivity")

    df_src = pd.read_csv(src_csv)
    df_sobol = pd.read_csv(sobol_csv)

    df_sobol = df_sobol[(df_sobol["model_id"] == "bnn-phy-mono") &
                        (df_sobol["N_base"] == df_sobol[df_sobol["model_id"]=="bnn-phy-mono"]["N_base"].max())]

    focus = [
        ("iteration2_max_global_stress", "Coupled peak stress"),
        ("iteration2_keff", r"$k_\mathrm{eff}$ (coupled)"),
    ]

    fig, axes = plt.subplots(1, 2, figsize=(12, 5.5))

    for ax, (out_col, title) in zip(axes, focus):
        src_sub = df_src[df_src["output"] == out_col]
        sobol_sub = df_sobol[df_sobol["output"] == out_col]

        r2_ols = src_sub["OLS_R2"].iloc[0]

        x_src2 = []
        y_s1 = []
        y_lo = []
        y_hi = []
        labels = []

        for inp in INPUT_COLS:
            src_row = src_sub[src_sub["input"] == inp].iloc[0]
            sobol_row = sobol_sub[sobol_sub["input"] == inp].iloc[0]

            src2 = src_row["SRC"] ** 2
            s1 = max(sobol_row["S1_mean"], 0)

            x_src2.append(src2)
            y_s1.append(s1)
            y_lo.append(max(sobol_row["S1_ci_lo"], 0))
            y_hi.append(sobol_row["S1_ci_hi"])
            labels.append(PAPER_NAMES[inp])

        x_src2 = np.array(x_src2)
        y_s1 = np.array(y_s1)
        y_lo = np.array(y_lo)
        y_hi = np.array(y_hi)

        yerr = np.array([y_s1 - y_lo, y_hi - y_s1])
        yerr = np.clip(yerr, 0, None)

        ax.errorbar(x_src2, y_s1, yerr=yerr, fmt="o", markersize=7,
                     capsize=4, color="#2c7fb8", ecolor="#999999", zorder=3)

        for i, lab in enumerate(labels):
            offset = (6, 6)
            if x_src2[i] < 0.01 and y_s1[i] < 0.05:
                offset = (4, -10)
            ax.annotate(lab, (x_src2[i], y_s1[i]), fontsize=9,
                        textcoords="offset points", xytext=offset)

        lim = max(max(x_src2), max(y_hi)) * 1.2
        ax.plot([0, lim], [0, lim], "k--", alpha=0.3, linewidth=0.8, label="1:1 line")
        ax.set_xlabel(r"HF data: SRC$^2$ (n = 3418)", fontsize=11)
        ax.set_ylabel(r"BNN Sobol $S_1$ (N = 8192, 20 reps)", fontsize=11)
        ax.set_title(f"{title}\n(OLS $R^2$ = {r2_ols:.3f})", fontsize=11)
        ax.set_xlim(-0.02, lim)
        ax.set_ylim(-0.02, lim)
        ax.set_aspect("equal")
        ax.legend(fontsize=9, loc="lower right")

    fig.suptitle(r"Independent validation: HF SRC$^2$ vs BNN Sobol $S_1$",
                 fontsize=13, y=1.02)
    plt.tight_layout()

    for ext in ["png", "pdf"]:
        fig.savefig(os.path.join(out_dir, f"hf_vs_bnn_sensitivity_comparison.{ext}"),
                    dpi=200, bbox_inches="tight")
    print(f"Saved to {out_dir}")

    # Print ranking comparison
    print("\n=== Ranking comparison ===")
    for out_col, title in focus:
        src_sub = df_src[df_src["output"] == out_col].copy()
        sobol_sub = df_sobol[df_sobol["output"] == out_col].copy()

        src_sub["SRC2"] = src_sub["SRC"] ** 2
        src_sub = src_sub.sort_values("SRC2", ascending=False)
        src_rank = {r["input"]: i+1 for i, (_, r) in enumerate(src_sub.iterrows())}

        sobol_sub = sobol_sub.sort_values("S1_mean", ascending=False)
        sobol_rank = {r["input"]: i+1 for i, (_, r) in enumerate(sobol_sub.iterrows())}

        print(f"\n  {title}")
        print(f"  {'Parameter':15s}  {'HF rank':>8s}  {'BNN rank':>8s}")
        for inp in INPUT_COLS:
            print(f"  {inp:15s}  {src_rank.get(inp, '-'):>8d}  {sobol_rank.get(inp, '-'):>8d}")

        from scipy.stats import spearmanr
        ranks_hf = [src_rank[inp] for inp in INPUT_COLS]
        ranks_bnn = [sobol_rank[inp] for inp in INPUT_COLS]
        rho, pval = spearmanr(ranks_hf, ranks_bnn)
        print(f"  Spearman rank correlation: rho = {rho:.3f}, p = {pval:.3e}")


if __name__ == "__main__":
    main()
