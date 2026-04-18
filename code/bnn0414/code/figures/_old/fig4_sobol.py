"""Figure 4 — Variance-based dominant-factor separation across outputs.

Two-panel horizontal bar chart: (A) stress first-order indices S1 with
90% CI, (B) keff S1 with 90% CI.  Inputs whose CI crosses zero are
visually flagged with gray hatching.

Phase-1 rulings enforced:
  * All 8 inputs listed.
  * CI-crosses-zero flagged in legend + gray hatch.
  * No "proves mechanism" / "guides engineering control" language.
  * No PRCC / Spearman in main figure (appendix only).

Output: code/bnn0414/manuscript/0414_v4/figures/fig4_sobol.{pdf,svg,png}
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from figure_io import savefig
from figure_style import (
    COLORS, FONT_SIZES, LINEWIDTHS,
    apply_rc, clean_ax, panel_label,
)

_BNN0414    = _HERE.parents[1]
_SOBOL_JSON = (_BNN0414 / "code" / "experiments" / "sensitivity" /
               "bnn-phy-mono" / "sobol_full.json")
_FIG_DIR    = _BNN0414 / "manuscript" / "0414_v4" / "figures"

PARAM_LABELS = {
    "E_slope":     r"$E_\mathrm{slope}$",
    "E_intercept": r"$E_\mathrm{intercept}$",
    "nu":          r"$\nu$",
    "alpha_base":  r"$\alpha_\mathrm{base}$",
    "alpha_slope": r"$\alpha_\mathrm{slope}$",
    "SS316_T_ref": r"$T_\mathrm{ref}$ (SS316)",
    "SS316_k_ref": r"$k_\mathrm{ref}$ (SS316)",
    "SS316_alpha": r"$\alpha_\mathrm{CTE}$ (SS316)",
}


def _load():
    with open(_SOBOL_JSON) as f:
        d = json.load(f)
    inputs = d["inputs"]
    results = d["results"]
    return inputs, results


def _draw_panel(ax, inputs, s1_data, title, panel_lbl):
    means = np.array(s1_data["mean"])
    lo    = np.array(s1_data["lo"])
    hi    = np.array(s1_data["hi"])
    errs  = np.column_stack([means - lo, hi - means]).T

    n = len(inputs)
    y_pos = np.arange(n)[::-1]
    labels = [PARAM_LABELS.get(p, p) for p in inputs]

    crosses_zero = (lo < 0) & (hi > 0)

    colors = [COLORS["ci_crosses_zero"] if cz else COLORS["bnn_main"]
              for cz in crosses_zero]
    hatches = ["///" if cz else "" for cz in crosses_zero]

    for i in range(n):
        ax.barh(
            y_pos[i], means[i], xerr=[[errs[0, i]], [errs[1, i]]],
            height=0.6, color=colors[i], edgecolor="#444444", lw=0.5,
            hatch=hatches[i], capsize=2, error_kw=dict(lw=0.8),
            zorder=3,
        )

    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels)
    ax.set_xlabel(r"First-order Sobol index $S_1$")
    ax.set_title(title, fontsize=FONT_SIZES["panel"], pad=6)
    ax.axvline(0, color="#999999", lw=0.4, zorder=1)
    clean_ax(ax)
    panel_label(ax, panel_lbl)


def main() -> None:
    apply_rc()
    inputs, results = _load()

    stress_s1 = results["iteration2_max_global_stress"]["S1"]
    keff_s1   = results["iteration2_keff"]["S1"]

    fig, (ax_s, ax_k) = plt.subplots(
        1, 2, figsize=(7.1, 3.4), constrained_layout=True,
    )

    _draw_panel(ax_s, inputs, stress_s1,
                "Coupled steady-state\nmax stress", "(A)")
    _draw_panel(ax_k, inputs, keff_s1,
                r"Coupled $k_\mathrm{eff}$", "(B)")

    import matplotlib.patches as mpatches
    h_main = mpatches.Patch(fc=COLORS["bnn_main"], ec="#444", lw=0.5,
                             label="CI excludes zero")
    h_gray = mpatches.Patch(fc=COLORS["ci_crosses_zero"], ec="#444",
                             lw=0.5, hatch="///",
                             label="CI crosses zero")
    ax_k.legend(handles=[h_main, h_gray], fontsize=6, loc="lower right",
                frameon=True, fancybox=False, edgecolor="#cccccc")

    written = savefig(fig, "fig4_sobol", _FIG_DIR)
    for w in written:
        print("wrote", w)


if __name__ == "__main__":
    main()
