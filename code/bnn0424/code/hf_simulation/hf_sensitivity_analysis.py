"""
HF data sensitivity analysis: SRC and PRCC.

Computes Standardized Regression Coefficients (SRC) and Partial Rank
Correlation Coefficients (PRCC) from the full HF dataset as an
independent validation of the BNN-based Sobol sensitivity indices.

Usage:
    python hf_sensitivity_analysis.py [--csv PATH]

Output:
    hf_sensitivity_results/
        src_results.csv
        prcc_results.csv
        hf_vs_bnn_sensitivity_comparison.png
        hf_sensitivity_bar.png
"""

import argparse
import os
import sys
import numpy as np
import pandas as pd
from scipy import stats
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

PRIMARY_OUTPUTS = [
    "iteration2_max_global_stress",
    "iteration2_keff",
    "iteration2_max_fuel_temp",
    "iteration2_max_monolith_temp",
    "iteration2_wall2",
]

OUTPUT_LABELS = {
    "iteration2_max_global_stress": "Coupled peak stress",
    "iteration2_keff": r"$k_\mathrm{eff}$ (coupled)",
    "iteration2_max_fuel_temp": "Max fuel temp",
    "iteration2_max_monolith_temp": "Max monolith temp",
    "iteration2_wall2": "Wall expansion",
}


def compute_src(X, y):
    """Standardized Regression Coefficients via OLS."""
    mask = ~np.isnan(y)
    X_c = X[mask]
    y_c = y[mask]
    x_std = X_c.std(axis=0)
    good = x_std > 1e-15
    X_c = X_c[:, good]
    X_std = (X_c - X_c.mean(axis=0)) / X_c.std(axis=0)
    y_std = (y_c - y_c.mean()) / y_c.std()
    beta_full = np.zeros(X.shape[1])
    se_full = np.full(X.shape[1], np.nan)
    XtX = X_std.T @ X_std
    Xty = X_std.T @ y_std
    beta = np.linalg.lstsq(XtX, Xty, rcond=None)[0]
    y_pred = X_std @ beta
    ss_res = np.sum((y_std - y_pred) ** 2)
    ss_tot = np.sum((y_std - y_std.mean()) ** 2)
    r2 = 1 - ss_res / ss_tot
    n, p = X_std.shape
    XtX_inv = np.linalg.pinv(XtX)
    se = np.sqrt(np.abs(np.diag(XtX_inv)) * ss_res / max(n - p - 1, 1))
    idx = np.where(good)[0]
    for i, gi in enumerate(idx):
        beta_full[gi] = beta[i]
        se_full[gi] = se[i]
    return beta_full, se_full, r2


def compute_prcc(X, y):
    """Partial Rank Correlation Coefficients."""
    n, p = X.shape
    mask = ~np.isnan(y)
    X_r = X[mask]
    y_r = y[mask]

    ranks_X = np.apply_along_axis(stats.rankdata, 0, X_r)
    ranks_y = stats.rankdata(y_r)

    prcc_vals = np.zeros(p)
    pvals = np.zeros(p)

    for j in range(p):
        other_cols = [i for i in range(p) if i != j]
        Z = ranks_X[:, other_cols]
        Z_aug = np.column_stack([np.ones(Z.shape[0]), Z])

        res_x = ranks_X[:, j] - Z_aug @ np.linalg.lstsq(Z_aug, ranks_X[:, j], rcond=None)[0]
        res_y = ranks_y - Z_aug @ np.linalg.lstsq(Z_aug, ranks_y, rcond=None)[0]

        r, pv = stats.pearsonr(res_x, res_y)
        prcc_vals[j] = r
        pvals[j] = pv

    return prcc_vals, pvals


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", default=None)
    parser.add_argument("--outdir", default=None)
    args = parser.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    bnn_root = os.path.dirname(os.path.dirname(script_dir))

    if args.csv:
        csv_path = args.csv
    else:
        candidates = [
            os.path.join(os.path.dirname(bnn_root), "dataset_v3_updated.csv"),
            os.path.join(os.path.dirname(bnn_root), "dataset_v3.csv"),
            "/home/tjzs/Documents/fenics_data/fenics_data/txt_extract/dataset_v3.csv",
        ]
        csv_path = next((c for c in candidates if os.path.exists(c)), None)
        if csv_path is None:
            print("ERROR: dataset_v3.csv not found. Use --csv to specify path.")
            sys.exit(1)

    if args.outdir:
        out_dir = args.outdir
    else:
        out_dir = os.path.join(bnn_root, "results", "hf_sensitivity")

    os.makedirs(out_dir, exist_ok=True)

    print(f"Loading {csv_path}")
    df = pd.read_csv(csv_path, encoding="utf-8-sig")
    df = df[INPUT_COLS + PRIMARY_OUTPUTS].dropna(subset=INPUT_COLS)
    print(f"Samples after dropping NaN inputs: {len(df)}")

    X = df[INPUT_COLS].values.astype(np.float64)

    src_rows = []
    prcc_rows = []

    for out_col in PRIMARY_OUTPUTS:
        y = df[out_col].values.astype(np.float64)
        valid = ~np.isnan(y)
        n_valid = valid.sum()

        beta, se, r2 = compute_src(X, y)
        prcc_vals, pvals = compute_prcc(X, y)

        for j, inp in enumerate(INPUT_COLS):
            src_rows.append({
                "output": out_col,
                "input": inp,
                "SRC": beta[j],
                "SRC_se": se[j],
                "OLS_R2": r2,
                "n_samples": n_valid,
            })
            prcc_rows.append({
                "output": out_col,
                "input": inp,
                "PRCC": prcc_vals[j],
                "p_value": pvals[j],
                "n_samples": n_valid,
            })

    df_src = pd.DataFrame(src_rows)
    df_prcc = pd.DataFrame(prcc_rows)

    df_src.to_csv(os.path.join(out_dir, "src_results.csv"), index=False)
    df_prcc.to_csv(os.path.join(out_dir, "prcc_results.csv"), index=False)
    print(f"\nSaved src_results.csv and prcc_results.csv to {out_dir}")

    print("\n=== SRC (Standardized Regression Coefficients) ===")
    for out_col in PRIMARY_OUTPUTS:
        sub = df_src[df_src["output"] == out_col].sort_values("SRC", key=abs, ascending=False)
        r2 = sub["OLS_R2"].iloc[0]
        print(f"\n  {OUTPUT_LABELS.get(out_col, out_col)}  (OLS R² = {r2:.4f})")
        for _, row in sub.iterrows():
            sig = "*" if abs(row["SRC"]) > 2 * row["SRC_se"] else " "
            print(f"    {row['input']:15s}  SRC = {row['SRC']:+.4f}  (±{row['SRC_se']:.4f}) {sig}")

    print("\n=== PRCC (Partial Rank Correlation) ===")
    for out_col in PRIMARY_OUTPUTS:
        sub = df_prcc[df_prcc["output"] == out_col].sort_values("PRCC", key=abs, ascending=False)
        print(f"\n  {OUTPUT_LABELS.get(out_col, out_col)}")
        for _, row in sub.iterrows():
            sig = "***" if row["p_value"] < 0.001 else ("**" if row["p_value"] < 0.01 else ("*" if row["p_value"] < 0.05 else ""))
            print(f"    {row['input']:15s}  PRCC = {row['PRCC']:+.4f}  (p = {row['p_value']:.2e}) {sig}")

    # --- Bar chart: SRC for stress and keff side by side ---
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharey=True)
    focus = ["iteration2_max_global_stress", "iteration2_keff"]
    titles = ["Coupled peak stress", r"$k_\mathrm{eff}$ (coupled)"]

    for ax, out_col, title in zip(axes, focus, titles):
        sub = df_src[df_src["output"] == out_col]
        vals = sub["SRC"].values
        errs = sub["SRC_se"].values
        labels = [PAPER_NAMES[c] for c in sub["input"]]
        colors = ["#d62728" if v > 0 else "#1f77b4" for v in vals]

        y_pos = np.arange(len(labels))
        ax.barh(y_pos, vals, xerr=errs, color=colors, edgecolor="k", linewidth=0.5, height=0.6, capsize=3)
        ax.set_yticks(y_pos)
        ax.set_yticklabels(labels, fontsize=10)
        ax.axvline(0, color="k", linewidth=0.5)
        ax.set_xlabel("SRC", fontsize=11)
        ax.set_title(f"{title}\n(OLS $R^2$ = {sub['OLS_R2'].iloc[0]:.3f})", fontsize=11)

    fig.suptitle(f"HF data sensitivity (SRC), n = {len(df)}", fontsize=13, y=1.02)
    plt.tight_layout()
    fig.savefig(os.path.join(out_dir, "hf_sensitivity_bar.png"), dpi=200, bbox_inches="tight")
    print(f"\nSaved hf_sensitivity_bar.png")

    # --- Comparison with BNN Sobol if available ---
    sobol_csv = os.path.join(bnn_root, "results", "sensitivity", "sobol_results.csv")
    if not os.path.exists(sobol_csv):
        sobol_csv = os.path.join(bnn_root, "results", "sensitivity",
                                 "sobol_convergence_bnn-phy-mono.csv")
    if os.path.exists(sobol_csv):
        try:
            df_sobol = pd.read_csv(sobol_csv)
            _make_comparison_plot(df_src, df_sobol, out_dir, len(df))
        except Exception as e:
            print(f"Could not load BNN Sobol results for comparison: {e}")
    else:
        print(f"\nBNN Sobol CSV not found at {sobol_csv}, skipping comparison plot.")

    print("\nDone.")


def _make_comparison_plot(df_src, df_sobol, out_dir, n_hf):
    """Side-by-side comparison of HF SRC vs BNN Sobol S1."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    for ax, out_col, title in zip(axes,
            ["iteration2_max_global_stress", "iteration2_keff"],
            ["Coupled peak stress", r"$k_\mathrm{eff}$ (coupled)"]):

        src_sub = df_src[df_src["output"] == out_col]
        src_vals = dict(zip(src_sub["input"], src_sub["SRC"].abs()))

        sobol_sub = df_sobol[(df_sobol["output"] == out_col) if "output" in df_sobol.columns
                             else df_sobol.index == df_sobol.index]
        if "parameter" in sobol_sub.columns and "S1" in sobol_sub.columns:
            sobol_vals = dict(zip(sobol_sub["parameter"], sobol_sub["S1"]))
        else:
            print(f"  Sobol CSV format not recognized, skipping comparison.")
            plt.close(fig)
            return

        x_hf = []
        x_bnn = []
        labels = []
        for inp in INPUT_COLS:
            if inp in src_vals and inp in sobol_vals:
                x_hf.append(src_vals[inp])
                x_bnn.append(sobol_vals[inp])
                labels.append(PAPER_NAMES[inp])

        ax.scatter(x_hf, x_bnn, s=60, zorder=3)
        for i, lab in enumerate(labels):
            ax.annotate(lab, (x_hf[i], x_bnn[i]), fontsize=8, textcoords="offset points",
                        xytext=(5, 5))
        lim = max(max(x_hf), max(x_bnn)) * 1.15
        ax.plot([0, lim], [0, lim], "k--", alpha=0.3, linewidth=0.8)
        ax.set_xlabel("|SRC| (HF data)", fontsize=11)
        ax.set_ylabel("Sobol $S_1$ (BNN)", fontsize=11)
        ax.set_title(title, fontsize=11)
        ax.set_xlim(0, lim)
        ax.set_ylim(0, lim)

    fig.suptitle(f"HF sensitivity (|SRC|, n={n_hf}) vs BNN Sobol $S_1$", fontsize=13, y=1.02)
    plt.tight_layout()
    fig.savefig(os.path.join(out_dir, "hf_vs_bnn_sensitivity_comparison.png"),
                dpi=200, bbox_inches="tight")
    print("Saved hf_vs_bnn_sensitivity_comparison.png")


if __name__ == "__main__":
    main()
