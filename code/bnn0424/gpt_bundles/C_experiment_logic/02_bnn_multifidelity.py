# bnn_multifidelity.py
# ============================================================
# Multi-fidelity BNN: exploit iter1 (uncoupled) → iter2 (coupled)
# solver hierarchy for improved iter2 prediction.
#
# Three architectures:
#
#   A. Stacked (compositional):
#      Stage 1: BNN_1(x) → ŷ₁  (8→7, predict iter1 outputs)
#      Stage 2: BNN_2(x, ŷ₁) → ŷ₂  (15→8, predict iter2 outputs)
#
#   B. Residual (discrepancy):
#      Stage 1: BNN_1(x) → ŷ₁  (8→7, predict iter1 outputs)
#      Stage 2: BNN_Δ(x, ŷ₁) → Δ̂  (15→7, predict iter2−iter1 delta)
#      keff:    BNN_k(x) → k̂_eff  (8→1, direct — no iter1 pair)
#      Final:   ŷ₂ = [ŷ₁ + Δ̂, k̂_eff]
#
#   C. Hybrid (gate-based routing, RECOMMENDED):
#      Stage 1: BNN_1(x) → ŷ₁  (8→7, predict iter1 outputs)
#      Residual path (stress, wall2): iter2 = iter1 + BNN_Δ(x, ŷ₁)
#      Direct path (temps, Hcore, keff): iter2 = BNN_direct(x)
#      Based on Phase 2.1 gate: only stress (ratio=0.298) and wall2
#      (ratio=0.005) benefit from residual; temperature outputs have
#      Var(Δ)/Var(y₂) > 2.3, making residual counterproductive.
#
# All reuse BayesianLinear and BayesianMLP from bnn_model.py.
# ============================================================

import math
from typing import Dict, List, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn

from bnn_model import BayesianLinear, BayesianMLP, mc_predict


N_ITER1 = 7   # iter1 outputs (no keff)
N_ITER2 = 8   # iter2 outputs (includes keff)
N_INPUTS = 8  # material parameters


class MultiFidelityBNN_Stacked(nn.Module):
    """
    Stacked multi-fidelity BNN.

    Stage 1 predicts iter1 (7 outputs) from x (8 inputs).
    Stage 2 predicts iter2 (8 outputs) from [x, iter1_pred] (15 inputs).

    Both stages are heteroscedastic BNNs with independent weight posteriors.
    """

    def __init__(self, in_dim: int = N_INPUTS,
                 n_iter1: int = N_ITER1, n_iter2: int = N_ITER2,
                 width1: int = 128, depth1: int = 3,
                 width2: int = 128, depth2: int = 3,
                 prior_sigma: float = 1.0,
                 freeze_stage1: bool = False):
        super().__init__()
        self.in_dim = in_dim
        self.n_iter1 = n_iter1
        self.n_iter2 = n_iter2
        self.freeze_stage1 = freeze_stage1

        self.stage1 = BayesianMLP(
            in_dim=in_dim, out_dim=n_iter1,
            width=width1, depth=depth1, prior_sigma=prior_sigma,
        )
        self.stage2 = BayesianMLP(
            in_dim=in_dim + n_iter1, out_dim=n_iter2,
            width=width2, depth=depth2, prior_sigma=prior_sigma,
        )

    @property
    def out_dim(self):
        return self.n_iter1 + self.n_iter2  # 15 total

    def forward(self, x: torch.Tensor, sample: bool = True
                ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Returns (mu, logvar) with shape (batch, 15).
        First 7 columns = iter1, last 8 = iter2.
        """
        if self.freeze_stage1:
            with torch.no_grad():
                mu1, logvar1 = self.stage1(x, sample=sample)
        else:
            mu1, logvar1 = self.stage1(x, sample=sample)

        x2 = torch.cat([x, mu1], dim=-1)
        mu2, logvar2 = self.stage2(x2, sample=sample)

        mu = torch.cat([mu1, mu2], dim=-1)
        logvar = torch.cat([logvar1, logvar2], dim=-1)
        return mu, logvar

    def kl_divergence(self) -> torch.Tensor:
        kl = self.stage2.kl_divergence()
        if not self.freeze_stage1:
            kl = kl + self.stage1.kl_divergence()
        return kl

    @torch.no_grad()
    def predict_mc(self, x: torch.Tensor, n_mc: int = 50
                   ) -> Tuple[torch.Tensor, torch.Tensor]:
        mus, logvars = [], []
        for _ in range(n_mc):
            mu, logvar = self.forward(x, sample=True)
            mus.append(mu.unsqueeze(0))
            logvars.append(logvar.unsqueeze(0))
        return torch.cat(mus, dim=0), torch.cat(logvars, dim=0)


class MultiFidelityBNN_Residual(nn.Module):
    """
    Residual (discrepancy) multi-fidelity BNN.

    Stage 1 predicts iter1 (7 outputs) from x.
    Stage delta predicts iter2 - iter1 (7 paired outputs) from [x, iter1_pred].
    Stage keff predicts keff (1 output) directly from x (no iter1 pair).

    Final iter2 = iter1_pred + delta_pred for 7 paired outputs,
    plus direct keff prediction.
    """

    def __init__(self, in_dim: int = N_INPUTS,
                 n_iter1: int = N_ITER1,
                 width1: int = 128, depth1: int = 3,
                 width_delta: int = 128, depth_delta: int = 3,
                 width_keff: int = 64, depth_keff: int = 2,
                 prior_sigma: float = 1.0,
                 freeze_stage1: bool = False):
        super().__init__()
        self.in_dim = in_dim
        self.n_iter1 = n_iter1
        self.freeze_stage1 = freeze_stage1

        self.stage1 = BayesianMLP(
            in_dim=in_dim, out_dim=n_iter1,
            width=width1, depth=depth1, prior_sigma=prior_sigma,
        )
        # Delta head: predicts iter2 - iter1 for 7 paired outputs
        self.stage_delta = BayesianMLP(
            in_dim=in_dim + n_iter1, out_dim=n_iter1,
            width=width_delta, depth=depth_delta, prior_sigma=prior_sigma,
        )
        # keff head: direct x → keff (no iter1 counterpart)
        self.stage_keff = BayesianMLP(
            in_dim=in_dim, out_dim=1,
            width=width_keff, depth=depth_keff, prior_sigma=prior_sigma,
        )

    @property
    def out_dim(self):
        return self.n_iter1 + self.n_iter1 + 1  # 7 iter1 + 7 iter2_paired + 1 keff = 15

    def forward(self, x: torch.Tensor, sample: bool = True
                ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Returns (mu, logvar) with shape (batch, 15).
        Columns: [iter1 (7), iter2_paired (7), keff (1)]

        iter2_paired = iter1_mu + delta_mu (additive composition).
        iter2_paired logvar = log(exp(logvar_iter1) + exp(logvar_delta))
        for proper variance propagation.
        """
        if self.freeze_stage1:
            with torch.no_grad():
                mu1, logvar1 = self.stage1(x, sample=sample)
        else:
            mu1, logvar1 = self.stage1(x, sample=sample)

        x_delta = torch.cat([x, mu1], dim=-1)
        mu_delta, logvar_delta = self.stage_delta(x_delta, sample=sample)

        mu_keff, logvar_keff = self.stage_keff(x, sample=sample)

        # iter2 paired = iter1 + delta
        mu2_paired = mu1 + mu_delta
        # Variance propagation: Var(a+b) = Var(a) + Var(b) when independent
        var1 = torch.exp(logvar1)
        var_delta = torch.exp(logvar_delta)
        logvar2_paired = torch.log(var1 + var_delta + 1e-8)

        mu = torch.cat([mu1, mu2_paired, mu_keff], dim=-1)
        logvar = torch.cat([logvar1, logvar2_paired, logvar_keff], dim=-1)
        return mu, logvar

    def kl_divergence(self) -> torch.Tensor:
        kl = self.stage_delta.kl_divergence() + self.stage_keff.kl_divergence()
        if not self.freeze_stage1:
            kl = kl + self.stage1.kl_divergence()
        return kl

    @torch.no_grad()
    def predict_mc(self, x: torch.Tensor, n_mc: int = 50
                   ) -> Tuple[torch.Tensor, torch.Tensor]:
        mus, logvars = [], []
        for _ in range(n_mc):
            mu, logvar = self.forward(x, sample=True)
            mus.append(mu.unsqueeze(0))
            logvars.append(logvar.unsqueeze(0))
        return torch.cat(mus, dim=0), torch.cat(logvars, dim=0)


# ============================================================
# Gate-based indices for hybrid routing
# ============================================================
# Within the 7 DELTA_PAIRS (iter1 order):
#   0: avg_fuel_temp       → direct
#   1: max_fuel_temp       → direct
#   2: max_monolith_temp   → direct
#   3: max_global_stress   → RESIDUAL (ratio=0.298)
#   4: monolith_new_temp   → direct
#   5: Hcore_after         → direct
#   6: wall2               → RESIDUAL (ratio=0.005)
RESIDUAL_IDX = [3, 6]  # stress, wall2
DIRECT_IDX = [0, 1, 2, 4, 5]  # temps, Hcore
N_RESIDUAL = len(RESIDUAL_IDX)  # 2
N_DIRECT_ITER2 = len(DIRECT_IDX) + 1  # 5 paired direct + keff = 6


class MultiFidelityBNN_Hybrid(nn.Module):
    """
    Hybrid multi-fidelity BNN with per-output routing.

    Based on Phase 2.1 gate analysis:
    - stress + wall2: residual path (iter2 = iter1 + delta)
    - temperatures + Hcore: direct path (iter2 = f(x))
    - keff: direct path (no iter1 counterpart)

    Stage 1: BNN_1(x) → ŷ₁ (7 iter1 outputs, used for residual path)
    Delta head: BNN_Δ(x, ŷ₁) → Δ̂ (2 outputs: stress delta, wall2 delta)
    Direct head: BNN_D(x) → ŷ₂_direct (6 outputs: 5 temps/Hcore + keff)

    Output order: [iter1(7), iter2_residual(2), iter2_direct(6)] = 15

    Note: the iter2 outputs are NOT in canonical DELTA_PAIRS order.
    Use HYBRID_OUTPUT_ORDER and the reorder functions to map to canonical.
    """

    def __init__(self, in_dim: int = N_INPUTS,
                 n_iter1: int = N_ITER1,
                 width1: int = 128, depth1: int = 3,
                 width_delta: int = 64, depth_delta: int = 2,
                 width_direct: int = 128, depth_direct: int = 3,
                 prior_sigma: float = 1.0,
                 freeze_stage1: bool = False):
        super().__init__()
        self.in_dim = in_dim
        self.n_iter1 = n_iter1
        self.freeze_stage1 = freeze_stage1
        self.residual_idx = RESIDUAL_IDX
        self.direct_idx = DIRECT_IDX

        # Stage 1: iter1 predictor
        self.stage1 = BayesianMLP(
            in_dim=in_dim, out_dim=n_iter1,
            width=width1, depth=depth1, prior_sigma=prior_sigma,
        )
        # Delta head: stress + wall2 residuals (2 outputs)
        self.stage_delta = BayesianMLP(
            in_dim=in_dim + n_iter1, out_dim=N_RESIDUAL,
            width=width_delta, depth=depth_delta, prior_sigma=prior_sigma,
        )
        # Direct head: 5 direct iter2 temps/Hcore + keff = 6 outputs
        self.stage_direct = BayesianMLP(
            in_dim=in_dim, out_dim=N_DIRECT_ITER2,
            width=width_direct, depth=depth_direct, prior_sigma=prior_sigma,
        )

    @property
    def out_dim(self):
        return self.n_iter1 + N_RESIDUAL + N_DIRECT_ITER2  # 7 + 2 + 6 = 15

    def forward(self, x: torch.Tensor, sample: bool = True
                ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Returns (mu, logvar) with shape (batch, 15).
        Output order: [iter1(7), iter2_residual(2), iter2_direct(6)]

        iter2_residual = iter1[residual_idx] + delta.
        """
        if self.freeze_stage1:
            with torch.no_grad():
                mu1, logvar1 = self.stage1(x, sample=sample)
        else:
            mu1, logvar1 = self.stage1(x, sample=sample)

        # Residual path
        x_delta = torch.cat([x, mu1], dim=-1)
        mu_delta, logvar_delta = self.stage_delta(x_delta, sample=sample)

        # iter2 residual = iter1 subset + delta
        mu1_res = mu1[:, self.residual_idx]  # (batch, 2)
        logvar1_res = logvar1[:, self.residual_idx]
        mu2_res = mu1_res + mu_delta
        var1_res = torch.exp(logvar1_res)
        var_delta = torch.exp(logvar_delta)
        logvar2_res = torch.log(var1_res + var_delta + 1e-8)

        # Direct path
        mu_direct, logvar_direct = self.stage_direct(x, sample=sample)

        mu = torch.cat([mu1, mu2_res, mu_direct], dim=-1)
        logvar = torch.cat([logvar1, logvar2_res, logvar_direct], dim=-1)
        return mu, logvar

    def kl_divergence(self) -> torch.Tensor:
        kl = self.stage_delta.kl_divergence() + self.stage_direct.kl_divergence()
        if not self.freeze_stage1:
            kl = kl + self.stage1.kl_divergence()
        return kl

    @torch.no_grad()
    def predict_mc(self, x: torch.Tensor, n_mc: int = 50
                   ) -> Tuple[torch.Tensor, torch.Tensor]:
        mus, logvars = [], []
        for _ in range(n_mc):
            mu, logvar = self.forward(x, sample=True)
            mus.append(mu.unsqueeze(0))
            logvars.append(logvar.unsqueeze(0))
        return torch.cat(mus, dim=0), torch.cat(logvars, dim=0)


# ============================================================
# Output column mapping
# ============================================================

def get_mf_output_mapping(output_cols: List[str], iter1_idx: List[int],
                          iter2_idx: List[int], delta_pairs: List[Tuple[str, str]]
                          ) -> Dict:
    """
    Build index mapping between the MF model's 15-column output
    and the canonical OUTPUT_COLS ordering.

    MF output order: [iter1(7), iter2_paired(7), keff(1)]
    Canonical order: [iter1(7), iter2(8)]  where keff is iter2_idx[0]

    Returns dict with 'mf_to_canonical' permutation array.
    """
    # MF columns: 0..6 = iter1, 7..13 = iter2 paired (same order as iter1), 14 = keff
    # Canonical: 0..6 = iter1, 7 = keff, 8..14 = iter2 paired outputs

    # Find keff position in canonical iter2
    keff_col = "iteration2_keff"
    keff_canonical_idx = output_cols.index(keff_col)

    # iter2 paired outputs in canonical order (excluding keff)
    iter2_paired_canonical = []
    for i1_col, i2_col in delta_pairs:
        iter2_paired_canonical.append(output_cols.index(i2_col))

    # MF index → canonical index
    mf_to_canonical = []
    # First 7: iter1 → iter1 (identity)
    for i in range(7):
        mf_to_canonical.append(iter1_idx[i])
    # Next 7: iter2 paired → iter2 paired positions
    for ci in iter2_paired_canonical:
        mf_to_canonical.append(ci)
    # Last 1: keff
    mf_to_canonical.append(keff_canonical_idx)

    return {
        "mf_to_canonical": np.array(mf_to_canonical),
        "keff_mf_idx": 14,
        "keff_canonical_idx": keff_canonical_idx,
        "iter2_paired_mf_range": (7, 14),
        "iter2_paired_canonical_idx": np.array(iter2_paired_canonical),
    }


def reorder_mf_to_canonical(mu: np.ndarray, mapping: Dict) -> np.ndarray:
    """Reorder MF model output (n, 15) to canonical column order (n, 15)."""
    perm = mapping["mf_to_canonical"]
    out = np.empty_like(mu)
    for mf_i, canon_i in enumerate(perm):
        out[..., canon_i] = mu[..., mf_i]
    return out


# ============================================================
# Smoke test
# ============================================================

if __name__ == "__main__":
    from bnn_model import seed_all
    seed_all(2026)

    print("=" * 60)
    print("  Multi-fidelity BNN smoke test")
    print("=" * 60)

    x = torch.randn(16, 8)

    print("\n--- Stacked ---")
    mf_s = MultiFidelityBNN_Stacked(width1=64, depth1=2, width2=64, depth2=2)
    mu, logvar = mf_s(x)
    print(f"  output shape: mu={mu.shape}, logvar={logvar.shape}")
    print(f"  KL: {mf_s.kl_divergence().item():.2f}")
    mus, lvs = mf_s.predict_mc(x, n_mc=5)
    print(f"  MC predict: mus={mus.shape}")

    print("\n--- Residual ---")
    mf_r = MultiFidelityBNN_Residual(width1=64, depth1=2,
                                      width_delta=64, depth_delta=2,
                                      width_keff=32, depth_keff=2)
    mu, logvar = mf_r(x)
    print(f"  output shape: mu={mu.shape}, logvar={logvar.shape}")
    print(f"  KL: {mf_r.kl_divergence().item():.2f}")
    mus, lvs = mf_r.predict_mc(x, n_mc=5)
    print(f"  MC predict: mus={mus.shape}")

    print("\n--- Output mapping ---")
    from experiments_0404.config.experiment_config_0404 import (
        OUTPUT_COLS, ITER1_IDX, ITER2_IDX, DELTA_PAIRS
    )
    mapping = get_mf_output_mapping(OUTPUT_COLS, ITER1_IDX, ITER2_IDX, DELTA_PAIRS)
    print(f"  mf_to_canonical: {mapping['mf_to_canonical']}")
    print(f"  keff: MF idx {mapping['keff_mf_idx']} → canonical idx {mapping['keff_canonical_idx']}")

    print("\nSmoke test passed.")
