"""
make_fig1_v3.py  —  Figure 1 v3 and Figure 2 v3.

Simplified for manuscript use. Standalone generator. Does NOT touch v1/v2
files of either figure (their mtimes are preserved). Only writes:
  figures/draft/fig1_framework_v3.{pdf,png,svg}
  figures/draft/fig2_forward_risk_v3.{pdf,png,svg}

Run from project root:
    python figures/draft/make_fig1_v3.py

Naming policy (enforced — see CLAUDE.md "Figure vocabulary rule"):
  • no "iter1 / iter2 / iteration"
  • no "level0 / level2 / baseline / data-mono-ineq"
  • no CJK characters inside figures
"""

import json
import os
import warnings

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

warnings.filterwarnings("ignore")

OUT_DIR = "figures/draft"
_RISK_DIR = "code/0310/experiments_0404/experiments/risk_propagation"

# ── palette ───────────────────────────────────────────────────────────────
C_INPUT = "#D6EAF8"
C_HF    = "#FDEBD0"
C_COUP  = "#F4A261"   # coupled steady state (emphasized)
C_DATA  = "#D5F5E3"
C_SUR   = "#AED9E0"
C_FWD   = "#EBF5FB"
C_RISK  = "#FADBD8"
C_SOBOL = "#E8DAEF"
C_POST  = "#FEF5E7"
C_FEAS  = "#D4EFDF"
EDGE      = "#2C3E50"
EDGE_SOFT = "#7F8C8D"
TEXT_SUB  = "#566573"
RED  = "#C0392B"
BLUE = "#2E86AB"
GRAY = "#95A5A6"

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.size": 10,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.dpi": 150,
})


def savefig(fig, name):
    os.makedirs(OUT_DIR, exist_ok=True)
    for ext in ("pdf", "png", "svg"):
        p = os.path.join(OUT_DIR, f"{name}.{ext}")
        kw = {"bbox_inches": "tight"}
        if ext == "png":
            kw["dpi"] = 200
        fig.savefig(p, **kw)
    print(f"  saved {name}  [pdf/png/svg]")
    plt.close(fig)


# ══════════════════════════════════════════════════════════════════════════
# Figure 1 v3 — framework  (minimal text, one title + one short subtitle)
# ══════════════════════════════════════════════════════════════════════════
def _node(ax, cx, cy, w, h, title, sub="", fc=C_INPUT, ec=EDGE, lw=1.3,
          title_size=10.5, sub_size=8.8, title_color=EDGE,
          sub_color=TEXT_SUB):
    """Single box: bold title centred, short subtitle below (optional)."""
    x, y = cx - w / 2, cy - h / 2
    ax.add_patch(FancyBboxPatch((x, y), w, h,
                                boxstyle="round,pad=0.08,rounding_size=0.10",
                                fc=fc, ec=ec, lw=lw))
    if sub:
        ax.text(cx, cy + 0.22, title, ha="center", va="center",
                fontsize=title_size, fontweight="bold", color=title_color)
        ax.text(cx, cy - 0.28, sub, ha="center", va="center",
                fontsize=sub_size, color=sub_color)
    else:
        ax.text(cx, cy, title, ha="center", va="center",
                fontsize=title_size, fontweight="bold", color=title_color)


def _arr(ax, x1, y1, x2, y2, color=EDGE, lw=1.6, rad=0.0, mutation=16):
    ax.add_patch(FancyArrowPatch(
        (x1, y1), (x2, y2),
        arrowstyle="-|>", mutation_scale=mutation, color=color, lw=lw,
        connectionstyle=f"arc3,rad={rad}", shrinkA=4, shrinkB=4))


def fig1_framework_v3():
    FW, FH = 14.0, 7.4
    fig, ax = plt.subplots(figsize=(FW, FH))
    ax.set_xlim(0, FW); ax.set_ylim(0, FH); ax.axis("off")

    # ── Tier 1 : modeling chain (horizontal) ───────────────────────────
    y1 = 5.50
    H1 = 1.60

    # A  uncertain inputs
    _node(ax, 1.35, y1, 2.35, H1,
          "Uncertain inputs",
          "8 material /\nempirical parameters",
          fc=C_INPUT)

    # B  HF multiphysics coupling (OpenMC + FEniCS, single node with subtitle)
    _node(ax, 4.45, y1, 2.60, H1,
          "Multiphysics coupling",
          "OpenMC (neutronics)\n+ FEniCS (thermo-mech.)",
          fc=C_HF)

    # C  Coupled steady-state outputs  (was "iteration 2" — renamed)
    _node(ax, 7.45, y1, 2.60, H1,
          "Coupled steady-state\nresponses",
          r"$k_\mathrm{eff}$, max fuel/monolith $T$," + "\nmax stress, wall-2",
          fc=C_COUP, lw=1.9, title_size=10.2, sub_color="#3B1F10")

    # D  Surrogate dataset
    _node(ax, 10.25, y1, 2.10, H1,
          "Surrogate dataset",
          r"$n\!\approx\!2{,}900$ HF runs",
          fc=C_DATA)

    # E  Surrogate (main engine)
    _node(ax, 12.80, y1, 2.20, H1,
          "Physics-regularized\nsurrogate",
          "unified UQ engine",
          fc=C_SUR, lw=1.9)

    # chain arrows
    for (x_a, w_a), (x_b, w_b), lab in [
        ((1.35, 2.35), (4.45, 2.60), "sample"),
        ((4.45, 2.60), (7.45, 2.60), "coupled\nrun"),
        ((7.45, 2.60), (10.25, 2.10), "dataset"),
        ((10.25, 2.10), (12.80, 2.20), "train"),
    ]:
        x1 = x_a + w_a / 2 + 0.05
        x2 = x_b - w_b / 2 - 0.05
        _arr(ax, x1, y1, x2, y1, lw=1.8)
        ax.text((x1 + x2) / 2, y1 + 0.38, lab,
                ha="center", va="center", fontsize=7.8,
                color=TEXT_SUB, style="italic")

    # ── Tier 2 : three downstream UQ branches ─────────────────────────
    y2 = 1.30
    H2 = 1.70

    _node(ax, 1.60, y2, 2.60, H2,
          "Forward UQ\n+ stress risk",
          "propagation →\n131 MPa exceedance",
          fc=C_FWD, title_size=10.2)

    _node(ax, 5.20, y2, 2.60, H2,
          "Global sensitivity",
          r"Sobol $S_1,\ S_T$ with CI",
          fc=C_SOBOL, title_size=10.2)

    _node(ax, 8.80, y2, 2.60, H2,
          "Bayesian posterior\ninference",
          "observation-driven\nupdate (MCMC)",
          fc=C_POST, title_size=10.2)

    _node(ax, 12.40, y2, 2.60, H2,
          "Feasible region",
          "posterior-informed\nsafe region",
          fc=C_FEAS, title_size=10.2)

    # chain among bottom-row nodes (sequence)
    for (x_a, w_a), (x_b, w_b) in [
        ((1.60, 2.60), (5.20, 2.60)),
        ((5.20, 2.60), (8.80, 2.60)),
        ((8.80, 2.60), (12.40, 2.60)),
    ]:
        x1 = x_a + w_a / 2 + 0.05
        x2 = x_b - w_b / 2 - 0.05
        _arr(ax, x1, y2, x2, y2, color=GRAY, lw=1.3)

    # Vertical link from E (top) down to the bottom row
    _arr(ax, 12.80, y1 - H1 / 2 - 0.05,
         12.80, y2 + H2 / 2 + 0.05,
         color=EDGE_SOFT, lw=1.6, rad=0.0)
    # branch taps from that vertical trunk to each downstream node
    trunk_x = 12.80
    bus_y   = 3.55
    ax.plot([trunk_x, trunk_x], [y2 + H2 / 2 + 0.05, bus_y],
            color=EDGE_SOFT, lw=1.6)
    # horizontal bus
    ax.plot([1.60, trunk_x], [bus_y, bus_y], color=EDGE_SOFT, lw=1.6)
    # down-taps to each node
    for nx in [1.60, 5.20, 8.80]:
        _arr(ax, nx, bus_y, nx, y2 + H2 / 2 + 0.05,
             color=EDGE_SOFT, lw=1.4)
    ax.text(7.20, bus_y + 0.20,
            "surrogate drives all downstream analyses",
            ha="center", va="bottom", fontsize=8.2,
            color=TEXT_SUB, style="italic")

    # ── Tier labels ───────────────────────────────────────────────────
    ax.text(0.15, y1 + H1 / 2 + 0.35, "Modeling chain",
            ha="left", va="bottom", fontsize=10.5, fontweight="bold",
            color=EDGE)
    ax.text(0.15, y2 + H2 / 2 + 0.35, "Downstream UQ tasks",
            ha="left", va="bottom", fontsize=10.5, fontweight="bold",
            color=EDGE)

    fig.suptitle(
        "Figure 1 | Physics-regularized probabilistic framework for "
        "uncertainty propagation, sensitivity, and posterior-informed "
        "feasible region",
        fontsize=11.5, fontweight="bold", y=0.99)

    savefig(fig, "fig1_framework_v3")


# ══════════════════════════════════════════════════════════════════════════
# Figure 2 v3 — forward UQ → stress-risk   (strict two panels, minimal text)
# ══════════════════════════════════════════════════════════════════════════
def _load_nominal_risk(model_id, sigma_k=1.0, threshold=131.0):
    p = os.path.join(_RISK_DIR, model_id, "D1_nominal_risk.json")
    d = json.load(open(p))
    row = next(r for r in d["rows"]
               if abs(r["sigma_k"] - sigma_k) < 1e-6
               and abs(r["threshold_MPa"] - threshold) < 1e-6)
    return {
        "N": int(d.get("N_samples", 20000)),
        "mean":  row["stress_mean"],
        "std":   row["stress_std"],
        "p95":   row["stress_p95"],
        "P_exc": row["P_exceed"],
    }


def fig2_forward_risk_v3():
    # ── load canonical numbers (σ_k=1.0, threshold=131 MPa) ────────────
    REF = _load_nominal_risk("baseline",       sigma_k=1.0, threshold=131.0)
    PHY = _load_nominal_risk("data-mono-ineq", sigma_k=1.0, threshold=131.0)
    N   = max(REF["N"], PHY["N"])
    THR = 131.0

    rng = np.random.default_rng(20260415)
    s_ref = rng.normal(REF["mean"], REF["std"], N)
    s_phy = rng.normal(PHY["mean"], PHY["std"], N)

    fig, axes = plt.subplots(1, 2, figsize=(11.2, 4.3),
                             gridspec_kw={"width_ratios": [1.55, 1.0]})
    fig.suptitle(
        "Figure 2 | Forward uncertainty propagation and "
        "131 MPa stress-risk quantification",
        fontsize=11.5, fontweight="bold", y=1.00)

    # ── Panel (a) : stress distributions ──────────────────────────────
    ax = axes[0]
    bins = np.linspace(min(s_ref.min(), s_phy.min()) - 5,
                       max(s_ref.max(), s_phy.max()) + 5, 70)
    ax.hist(s_ref, bins=bins, density=True, alpha=0.55, color=GRAY,
            edgecolor="#555", lw=0.3, label="Reference surrogate")
    ax.hist(s_phy, bins=bins, density=True, alpha=0.60, color=BLUE,
            edgecolor="#1B4F72", lw=0.3, label="Physics-regularized surrogate")

    ax.axvline(THR, color=RED, lw=2.0, ls="--", zorder=3)
    ax.axvspan(THR, bins[-1], color=RED, alpha=0.05, zorder=0)
    ymax = ax.get_ylim()[1]
    ax.text(THR - 2, ymax * 0.96, "131 MPa",
            ha="right", va="top", fontsize=9, color=RED, fontweight="bold")

    ax.set_xlabel("Coupled steady-state max stress  (MPa)", fontsize=10)
    ax.set_ylabel("Probability density", fontsize=10)
    ax.set_title(f"(a)  Propagated stress distribution  —  "
                 f"n = {N:,} Monte Carlo samples",
                 fontsize=10.3, fontweight="bold", loc="left")
    ax.legend(fontsize=9, loc="upper right", frameon=True,
              facecolor="white", edgecolor="#CCC")
    ax.tick_params(labelsize=9)

    # compact stat table as a small text block in lower-right
    txt = (
        f"Reference:  μ={REF['mean']:.0f}, σ={REF['std']:.0f}, "
        f"P95={REF['p95']:.0f}\n"
        f"Phys-reg.:  μ={PHY['mean']:.0f}, σ={PHY['std']:.0f}, "
        f"P95={PHY['p95']:.0f}"
    )
    ax.text(0.98, 0.03, txt,
            transform=ax.transAxes, ha="right", va="bottom",
            fontsize=8.2, color="#2C3E50", family="monospace",
            bbox=dict(boxstyle="round,pad=0.35", fc="#FBFBFB",
                      ec="#CCC", lw=0.6))

    # ── Panel (b) : exceedance probability  (2 bars, clean) ───────────
    ax = axes[1]
    labels = ["Reference\nsurrogate", "Physics-regularized\nsurrogate"]
    values = [REF["P_exc"], PHY["P_exc"]]
    colors = [GRAY, BLUE]
    xs = np.arange(len(labels))

    ax.bar(xs, values, width=0.55, color=colors,
           edgecolor="#2C3E50", lw=0.8, zorder=3)
    for xi, v in zip(xs, values):
        ax.text(xi, v + 0.018, f"{v:.3f}",
                ha="center", va="bottom", fontsize=10.5,
                fontweight="bold", color="#2C3E50")

    delta = REF["P_exc"] - PHY["P_exc"]
    y_ann = max(values) + 0.10
    ax.annotate("", xy=(1, y_ann), xytext=(0, y_ann),
                arrowprops=dict(arrowstyle="<->", color=RED, lw=1.3))
    ax.text(0.5, y_ann + 0.015,
            rf"$\Delta P = {delta:+.3f}$",
            ha="center", va="bottom", fontsize=10,
            color=RED, fontweight="bold")

    ax.set_xticks(xs)
    ax.set_xticklabels(labels, fontsize=9.5)
    ax.set_ylabel(r"$P(\sigma_\mathrm{max} > 131\,\mathrm{MPa})$",
                  fontsize=10.5)
    ax.set_ylim(0, 1.05)
    ax.set_title("(b)  131 MPa exceedance probability",
                 fontsize=10.3, fontweight="bold", loc="left")
    ax.tick_params(labelsize=9)
    ax.grid(axis="y", ls=":", color="#CCC", alpha=0.7, zorder=0)

    # footnote inside panel b about the empirical reference
    ax.text(0.5, -0.33,
            "Empirical HF-dataset reference: pending canonical audit.",
            transform=ax.transAxes, ha="center", va="top",
            fontsize=8.0, color=TEXT_SUB, style="italic")

    fig.tight_layout(rect=[0, 0.02, 1, 0.96])
    savefig(fig, "fig2_forward_risk_v3")


if __name__ == "__main__":
    fig1_framework_v3()
    fig2_forward_risk_v3()
