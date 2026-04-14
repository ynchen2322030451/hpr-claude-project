# bnn_model.py
# ============================================================
# Bayesian Neural Network (BNN) implementation for HPR surrogate
#
# Replaces HeteroMLP with weight-space uncertainty via
# linear reparameterization (Blundell et al. 2015,
# "Weight Uncertainty in Neural Networks").
#
# Design:
#   - BayesianLinear: reparameterized linear layer with
#     Gaussian variational posterior q(w) = N(mu, softplus(rho)^2)
#     and isotropic Gaussian prior p(w) = N(0, prior_sigma^2).
#   - BayesianMLP: drop-in replacement for HeteroMLP with
#     identical forward signature: (mu, logvar) = model(x).
#   - Epistemic uncertainty via MC forward passes (weight sampling).
#   - Aleatoric uncertainty via heteroscedastic logvar head.
#
# Compatibility notes:
#   - in_dim=8, out_dim=15 (same as HeteroMLP)
#   - logvar clamped to [-20, 5] (same as HeteroMLP)
#   - SiLU activation, no dropout (BNN has built-in regularization)
#   - forward(x, sample=True) for training/MC inference
#   - forward(x, sample=False) for deterministic mean-weight inference
#   - kl_divergence() returns total KL for ELBO
#
# Source reference:
#   HeteroMLP defined in code/0310/run_phys_levels_main.py lines 210-237
#   Physics constraints from code/0411/.../model_registry_0404.py
# ============================================================

import os
import math
import random
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

import torch
import torch.nn as nn
import torch.nn.functional as F

from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split


# ============================================================
# Utilities
# ============================================================

def seed_all(seed: int):
    """Set all random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def get_device(device_str: str = "cuda") -> torch.device:
    """Auto-detect device. Falls back to CPU if CUDA unavailable."""
    if device_str == "cuda" and torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


# ============================================================
# BayesianLinear layer
# ============================================================

class BayesianLinear(nn.Module):
    """
    Fully-connected layer with Gaussian variational posterior
    on weights and biases, trained via reparameterization trick.

    Posterior: q(w) = N(weight_mu, softplus(weight_rho)^2)
    Prior:     p(w) = N(0, prior_sigma^2)

    KL divergence is computed in closed form for Gaussian-Gaussian.

    Parameters
    ----------
    in_features : int
        Number of input features.
    out_features : int
        Number of output features.
    prior_sigma : float
        Standard deviation of the isotropic Gaussian prior.
        Default 1.0. Searchable by Optuna.
    """

    def __init__(self, in_features: int, out_features: int,
                 prior_sigma: float = 1.0):
        super().__init__()
        self.in_features = in_features
        self.out_features = out_features

        # Variational posterior parameters for weights
        self.weight_mu = nn.Parameter(
            torch.empty(out_features, in_features)
        )
        self.weight_rho = nn.Parameter(
            torch.empty(out_features, in_features)
        )

        # Variational posterior parameters for biases
        self.bias_mu = nn.Parameter(torch.empty(out_features))
        self.bias_rho = nn.Parameter(torch.empty(out_features))

        # Prior (not learned)
        self.prior_sigma = prior_sigma
        self.prior_log_sigma = math.log(prior_sigma)

        # Initialize
        self._reset_parameters()

    def _reset_parameters(self):
        """
        Initialize mu with Xavier-uniform scale, rho so that
        initial posterior sigma ~ 0.1 (softplus(-2.3) ~ 0.1).
        """
        # Xavier-style initialization for mu
        stdv = 1.0 / math.sqrt(self.in_features)
        nn.init.uniform_(self.weight_mu, -stdv, stdv)
        nn.init.zeros_(self.bias_mu)

        # Initialize rho so softplus(rho) ~ 0.1
        # softplus(x) = log(1 + exp(x)); softplus(-2.3) ~ 0.1
        nn.init.constant_(self.weight_rho, -2.3)
        nn.init.constant_(self.bias_rho, -2.3)

    def forward(self, x: torch.Tensor, sample: bool = True) -> torch.Tensor:
        """
        Forward pass with optional weight sampling.

        Parameters
        ----------
        x : torch.Tensor
            Input tensor of shape (batch, in_features).
        sample : bool
            If True, sample weights from posterior (training / MC inference).
            If False, use posterior mean (deterministic mode).

        Returns
        -------
        torch.Tensor
            Output of shape (batch, out_features).
        """
        if sample:
            # Reparameterization trick: w = mu + softplus(rho) * epsilon
            weight_sigma = F.softplus(self.weight_rho)
            bias_sigma = F.softplus(self.bias_rho)

            weight_eps = torch.randn_like(self.weight_mu)
            bias_eps = torch.randn_like(self.bias_mu)

            weight = self.weight_mu + weight_sigma * weight_eps
            bias = self.bias_mu + bias_sigma * bias_eps
        else:
            weight = self.weight_mu
            bias = self.bias_mu

        return F.linear(x, weight, bias)

    def kl_divergence(self) -> torch.Tensor:
        """
        Closed-form KL(q || p) for Gaussian posterior vs Gaussian prior.

        KL(N(mu, sigma^2) || N(0, sigma_p^2))
          = log(sigma_p / sigma) + (sigma^2 + mu^2) / (2 * sigma_p^2) - 0.5

        Summed over all weight and bias parameters.
        """
        prior_var = self.prior_sigma ** 2

        # Weights
        w_sigma = F.softplus(self.weight_rho)
        w_var = w_sigma ** 2
        kl_w = (
            self.prior_log_sigma - torch.log(w_sigma)
            + (w_var + self.weight_mu ** 2) / (2.0 * prior_var)
            - 0.5
        )

        # Biases
        b_sigma = F.softplus(self.bias_rho)
        b_var = b_sigma ** 2
        kl_b = (
            self.prior_log_sigma - torch.log(b_sigma)
            + (b_var + self.bias_mu ** 2) / (2.0 * prior_var)
            - 0.5
        )

        return kl_w.sum() + kl_b.sum()

    def extra_repr(self) -> str:
        return (
            f"in_features={self.in_features}, "
            f"out_features={self.out_features}, "
            f"prior_sigma={self.prior_sigma:.4f}"
        )


# ============================================================
# BayesianMLP (drop-in replacement for HeteroMLP)
# ============================================================

class BayesianMLP(nn.Module):
    """
    Bayesian heteroscedastic MLP with reparameterized weight posteriors.

    Architecture matches HeteroMLP:
      - Backbone: depth BayesianLinear layers with SiLU activation
      - Two output heads: mu_head (mean) and logvar_head (log-variance)
      - logvar clamped to [-20, 5]

    Differences from HeteroMLP:
      - No dropout (BNN provides built-in regularization via weight uncertainty)
      - forward() accepts sample=True/False flag
      - kl_divergence() returns total KL for ELBO loss
      - predict_mc() runs multiple stochastic forward passes

    Parameters
    ----------
    in_dim : int
        Number of input features (8 for HPR).
    out_dim : int
        Number of output features (15 for HPR).
    width : int
        Hidden layer width.
    depth : int
        Number of hidden layers.
    prior_sigma : float
        Prior standard deviation for BayesianLinear layers.
        Default 1.0. Configurable / searchable by Optuna.
    """

    def __init__(self, in_dim: int, out_dim: int, width: int, depth: int,
                 prior_sigma: float = 1.0):
        super().__init__()
        self.in_dim = in_dim
        self.out_dim = out_dim

        # Build backbone: depth layers of BayesianLinear + SiLU
        layers = nn.ModuleList()
        d = in_dim
        for _ in range(depth):
            layers.append(BayesianLinear(d, width, prior_sigma=prior_sigma))
            d = width
        self.backbone_layers = layers
        self.activation = nn.SiLU()

        # Output heads (also Bayesian)
        self.mu_head = BayesianLinear(d, out_dim, prior_sigma=prior_sigma)
        self.logvar_head = BayesianLinear(d, out_dim, prior_sigma=prior_sigma)

        # For compatibility with downstream code that may check this attribute
        self._delta_head = None

    def forward(self, x: torch.Tensor, sample: bool = True,
                return_z: bool = False) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Forward pass.

        Parameters
        ----------
        x : torch.Tensor
            Input of shape (batch, in_dim).
        sample : bool
            If True, sample weights (training / MC inference).
            If False, use mean weights (deterministic).
        return_z : bool
            If True, also return the backbone representation z.
            Provided for compatibility with HeteroMLP.forward(x, return_z=True).

        Returns
        -------
        mu : torch.Tensor of shape (batch, out_dim)
        logvar : torch.Tensor of shape (batch, out_dim), clamped to [-20, 5]
        z : torch.Tensor of shape (batch, width) [only if return_z=True]
        """
        z = x
        for layer in self.backbone_layers:
            z = self.activation(layer(z, sample=sample))

        mu = self.mu_head(z, sample=sample)
        logvar = self.logvar_head(z, sample=sample).clamp(-20, 5)

        if return_z:
            return mu, logvar, z
        return mu, logvar

    def kl_divergence(self) -> torch.Tensor:
        """
        Total KL divergence summed over all BayesianLinear layers.

        Returns
        -------
        torch.Tensor
            Scalar KL divergence.
        """
        kl = torch.tensor(0.0, device=self.mu_head.weight_mu.device)
        for layer in self.backbone_layers:
            kl = kl + layer.kl_divergence()
        kl = kl + self.mu_head.kl_divergence()
        kl = kl + self.logvar_head.kl_divergence()
        return kl

    @torch.no_grad()
    def predict_mc(self, x: torch.Tensor, n_mc: int = 50
                   ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Run n_mc stochastic forward passes and stack results.

        Parameters
        ----------
        x : torch.Tensor
            Input of shape (batch, in_dim).
        n_mc : int
            Number of Monte Carlo forward passes.

        Returns
        -------
        mus : torch.Tensor of shape (n_mc, batch, out_dim)
        logvars : torch.Tensor of shape (n_mc, batch, out_dim)
        """
        mus = []
        logvars = []
        for _ in range(n_mc):
            mu, logvar = self.forward(x, sample=True)
            mus.append(mu.unsqueeze(0))
            logvars.append(logvar.unsqueeze(0))
        return torch.cat(mus, dim=0), torch.cat(logvars, dim=0)


# ============================================================
# Loss functions
# ============================================================

def gaussian_nll(y: torch.Tensor, mu: torch.Tensor,
                 logvar: torch.Tensor, eps: float = 1e-8) -> torch.Tensor:
    """
    Gaussian negative log-likelihood loss.

    Identical to the version in run_phys_levels_main.py.

    NLL = 0.5 * mean(log(2*pi) + logvar + (y - mu)^2 / var)
    """
    var = torch.exp(logvar).clamp(min=eps)
    return 0.5 * (math.log(2 * math.pi) + logvar + (y - mu) ** 2 / var).mean()


def elbo_loss(y: torch.Tensor, mu: torch.Tensor, logvar: torch.Tensor,
              kl: torch.Tensor, kl_weight: float,
              n_train: int) -> torch.Tensor:
    """
    Evidence Lower Bound (ELBO) loss for BNN training.

    ELBO = -log_likelihood + kl_weight * KL / N_train

    The 1/N_train scaling follows Blundell et al. 2015: the KL term
    is divided by the number of training samples so that the per-minibatch
    loss is comparable across dataset sizes.

    Parameters
    ----------
    y : torch.Tensor
        Target values, shape (batch, out_dim).
    mu : torch.Tensor
        Predicted means, shape (batch, out_dim).
    logvar : torch.Tensor
        Predicted log-variances, shape (batch, out_dim).
    kl : torch.Tensor
        KL divergence from model.kl_divergence().
    kl_weight : float
        Complexity cost weight that scales the KL term.
        Also called beta in beta-ELBO / KL annealing literature.
        Can be tuned by Optuna.
    n_train : int
        Number of training samples, used for 1/N scaling.

    Returns
    -------
    torch.Tensor
        Scalar ELBO loss.
    """
    nll = gaussian_nll(y, mu, logvar)
    return nll + kl_weight * kl / max(n_train, 1)


# ============================================================
# Spearman monotonicity functions
# (copied from code/0310/run_phys_levels_main.py lines 256-301)
# ============================================================

def build_mono_pairs_spearman(Xtr: np.ndarray, Ytr: np.ndarray,
                              rho_abs_min: float, topk: int
                              ) -> List[Tuple[int, int, int, float]]:
    """
    Build monotonicity constraint pairs from Spearman rank correlations.

    For each (input_i, output_j) pair with |rho| >= rho_abs_min,
    record (i, j, sign, |rho|). Return top-k by |rho|.

    Parameters
    ----------
    Xtr : np.ndarray of shape (n, n_inputs)
    Ytr : np.ndarray of shape (n, n_outputs)
    rho_abs_min : float
        Minimum absolute Spearman correlation to include.
    topk : int
        Maximum number of pairs to return.

    Returns
    -------
    List of (input_idx, output_idx, sign, abs_rho)
    """
    Xrk = np.apply_along_axis(lambda v: pd.Series(v).rank().to_numpy(), 0, Xtr)
    Yrk = np.apply_along_axis(lambda v: pd.Series(v).rank().to_numpy(), 0, Ytr)

    pairs = []
    for i in range(Xtr.shape[1]):
        xi = (Xrk[:, i] - Xrk[:, i].mean()) / (Xrk[:, i].std() + 1e-12)
        for j in range(Ytr.shape[1]):
            yj = (Yrk[:, j] - Yrk[:, j].mean()) / (Yrk[:, j].std() + 1e-12)
            rho = float(np.mean(xi * yj))
            if abs(rho) < rho_abs_min:
                continue
            sign = +1 if rho >= 0 else -1
            pairs.append((i, j, sign, abs(rho)))
    pairs.sort(key=lambda t: t[3], reverse=True)
    return pairs[:topk]


def loss_monotone_from_mu(mu: torch.Tensor, x: torch.Tensor,
                          pairs: List[Tuple[int, int, int, float]]
                          ) -> torch.Tensor:
    """
    Gradient-based monotonicity penalty.

    For each (input_i, output_j, sign, weight) pair, compute
    d(output_j) / d(input_i) and penalize violations of the
    expected sign direction.

    Identical to loss_level2_monotone_from_mu in run_phys_levels_main.py.

    Parameters
    ----------
    mu : torch.Tensor of shape (batch, out_dim)
        Mean predictions (from model forward pass).
    x : torch.Tensor of shape (batch, in_dim)
        Input tensor, must have requires_grad=True.
    pairs : list of (input_idx, output_idx, sign, weight)

    Returns
    -------
    torch.Tensor
        Scalar monotonicity loss.
    """
    if not pairs:
        return torch.tensor(0.0, device=x.device)
    terms = []
    for i, j, sign, w in pairs:
        yj = mu[:, j].sum()
        gij = torch.autograd.grad(yj, x, create_graph=True,
                                  retain_graph=True)[0][:, i]
        viol = F.relu(-sign * gij)
        terms.append(float(w) * viol.mean())
    return torch.stack(terms).mean()


def loss_inequality(mu_raw: torch.Tensor, sy, w: float,
                    device: torch.device,
                    rules: List[Dict]) -> torch.Tensor:
    """
    Physics inequality constraint loss (operates in standardized space).

    Supports two rule types:
      - "greater_equal": mu[:, j_big] >= mu[:, j_small]
      - "nonneg": mu[:, j_val] >= 0 (in original scale, mapped to
        standardized space via sy scaler)

    Identical to loss_inequality in run_train_0404.py.

    Parameters
    ----------
    mu_raw : torch.Tensor of shape (batch, out_dim)
        Mean predictions in standardized space.
    sy : sklearn.preprocessing.StandardScaler
        Output scaler (for nonneg threshold mapping).
    w : float
        Weight for the inequality loss term.
    device : torch.device
    rules : list of dict
        Inequality rules, each with keys "type", "name", and
        type-specific keys ("j_big"/"j_small" or "j_val"/"bound").

    Returns
    -------
    torch.Tensor
        Scalar inequality loss.
    """
    if w == 0.0:
        return torch.tensor(0.0, device=device)

    total = torch.tensor(0.0, device=device)
    for rule in rules:
        rtype = rule["type"]
        if rtype == "greater_equal":
            j_big = rule["j_big"]
            j_small = rule["j_small"]
            viol = F.relu(mu_raw[:, j_small] - mu_raw[:, j_big])
            total = total + viol.mean()
        elif rtype == "nonneg":
            j_val = rule["j_val"]
            if hasattr(sy, "mean_") and hasattr(sy, "scale_"):
                zero_scaled = torch.tensor(
                    float(-sy.mean_[j_val] / sy.scale_[j_val]),
                    dtype=torch.float32, device=device
                )
            else:
                zero_scaled = torch.tensor(0.0, device=device)
            viol = F.relu(zero_scaled - mu_raw[:, j_val])
            total = total + viol.mean()

    return w * total / max(len(rules), 1)


# ============================================================
# Data loading and splitting
# ============================================================

def load_dataset(csv_path: str, input_cols: List[str],
                 output_cols: List[str]) -> pd.DataFrame:
    """
    Load and validate the HPR dataset CSV.

    Parameters
    ----------
    csv_path : str
        Path to dataset_v3.csv.
    input_cols : list of str
    output_cols : list of str

    Returns
    -------
    pd.DataFrame
        Cleaned dataframe with NaN rows dropped.
    """
    df = pd.read_csv(csv_path)
    df = df.dropna(subset=input_cols + output_cols).reset_index(drop=True)

    for c in input_cols + output_cols:
        if c not in df.columns:
            raise ValueError(f"Missing column in dataset: {c}")

    return df


def split_and_scale(df: pd.DataFrame, input_cols: List[str],
                    output_cols: List[str], seed: int,
                    test_size: float = 0.15, val_size: float = 0.1765
                    ) -> Dict:
    """
    Split dataset into train/val/test and apply StandardScaler.

    Split ratios match the existing pipeline:
      test_size=0.15, val_size=0.1765 (of trainval)
      -> approx 70% train, 15% val, 15% test

    Parameters
    ----------
    df : pd.DataFrame
    input_cols : list of str
    output_cols : list of str
    seed : int
    test_size : float
    val_size : float
        Fraction of trainval used for validation.

    Returns
    -------
    dict with keys:
        idx_train, idx_val, idx_test,
        X_tr, X_va, X_te, Y_tr, Y_va, Y_te,
        Xtr_s, Xva_s, Xte_s, Ytr_s, Yva_s, Yte_s,
        sx, sy
    """
    idx_all = np.arange(len(df))
    X = df[input_cols].to_numpy(dtype=float)
    Y = df[output_cols].to_numpy(dtype=float)

    idx_trainval, idx_test = train_test_split(
        idx_all, test_size=test_size, random_state=seed, shuffle=True
    )
    idx_train, idx_val = train_test_split(
        idx_trainval, test_size=val_size, random_state=seed, shuffle=True
    )

    idx_train = np.sort(idx_train)
    idx_val = np.sort(idx_val)
    idx_test = np.sort(idx_test)

    X_tr, X_va, X_te = X[idx_train], X[idx_val], X[idx_test]
    Y_tr, Y_va, Y_te = Y[idx_train], Y[idx_val], Y[idx_test]

    sx = StandardScaler().fit(X_tr)
    sy = StandardScaler().fit(Y_tr)

    Xtr_s = sx.transform(X_tr)
    Xva_s = sx.transform(X_va)
    Xte_s = sx.transform(X_te)
    Ytr_s = sy.transform(Y_tr)
    Yva_s = sy.transform(Y_va)
    Yte_s = sy.transform(Y_te)

    return {
        "idx_train": idx_train,
        "idx_val": idx_val,
        "idx_test": idx_test,
        "X_tr": X_tr, "X_va": X_va, "X_te": X_te,
        "Y_tr": Y_tr, "Y_va": Y_va, "Y_te": Y_te,
        "Xtr_s": Xtr_s, "Xva_s": Xva_s, "Xte_s": Xte_s,
        "Ytr_s": Ytr_s, "Yva_s": Yva_s, "Yte_s": Yte_s,
        "sx": sx, "sy": sy,
    }


# ============================================================
# MC prediction utility
# ============================================================

@torch.no_grad()
def mc_predict(model: BayesianMLP, X_np: np.ndarray,
               sx: StandardScaler, sy: StandardScaler,
               device: torch.device, n_mc: int = 50
               ) -> Tuple[np.ndarray, np.ndarray, np.ndarray,
                          np.ndarray, np.ndarray]:
    """
    Monte Carlo prediction with uncertainty decomposition.

    Runs n_mc stochastic forward passes through the BNN, then
    decomposes total predictive uncertainty into epistemic
    (weight uncertainty) and aleatoric (heteroscedastic noise)
    components, all in original (unscaled) output space.

    Parameters
    ----------
    model : BayesianMLP
        Trained BNN model.
    X_np : np.ndarray of shape (n, n_inputs)
        Input data in original (unscaled) space.
    sx : StandardScaler
        Input scaler.
    sy : StandardScaler
        Output scaler.
    device : torch.device
    n_mc : int
        Number of MC forward passes.

    Returns
    -------
    mu_mean : np.ndarray of shape (n, n_outputs)
        Mean of predicted means across MC samples, in original scale.
    mu_std : np.ndarray of shape (n, n_outputs)
        Std of predicted means across MC samples (epistemic std),
        in original scale.
    aleatoric_var : np.ndarray of shape (n, n_outputs)
        Mean predicted variance across MC samples, in original scale.
    epistemic_var : np.ndarray of shape (n, n_outputs)
        Variance of predicted means across MC samples, in original scale.
    total_var : np.ndarray of shape (n, n_outputs)
        aleatoric_var + epistemic_var, in original scale.
    """
    model.eval()

    # Scale inputs
    X_scaled = sx.transform(X_np)
    x_t = torch.tensor(X_scaled, dtype=torch.float32, device=device)

    # Collect MC samples
    mus_scaled, logvars_scaled = model.predict_mc(x_t, n_mc=n_mc)
    # mus_scaled: (n_mc, n, n_outputs) in standardized space
    # logvars_scaled: (n_mc, n, n_outputs) in standardized space

    mus_np = mus_scaled.cpu().numpy()        # (n_mc, n, n_outputs)
    logvars_np = logvars_scaled.cpu().numpy()  # (n_mc, n, n_outputs)

    # Convert means to original scale
    sy_mean = sy.mean_[np.newaxis, :]   # (1, n_outputs)
    sy_scale = sy.scale_[np.newaxis, :]  # (1, n_outputs)

    mus_orig = mus_np * sy_scale + sy_mean  # (n_mc, n, n_outputs)

    # Convert variances to original scale
    # In standardized space, var_scaled = exp(logvar_scaled)
    # In original space, var_orig = var_scaled * sy.scale_^2
    vars_scaled = np.exp(logvars_np)  # (n_mc, n, n_outputs)
    vars_orig = vars_scaled * (sy_scale ** 2)  # (n_mc, n, n_outputs)

    # Decompose uncertainty
    mu_mean = np.mean(mus_orig, axis=0)         # (n, n_outputs)
    epistemic_var = np.var(mus_orig, axis=0)     # (n, n_outputs)
    aleatoric_var = np.mean(vars_orig, axis=0)   # (n, n_outputs)
    total_var = epistemic_var + aleatoric_var     # (n, n_outputs)
    mu_std = np.sqrt(epistemic_var)               # (n, n_outputs)

    return mu_mean, mu_std, aleatoric_var, epistemic_var, total_var


# ============================================================
# Smoke test
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("  BNN model smoke test")
    print("=" * 60)

    seed_all(2026)
    device = get_device("cpu")

    in_dim, out_dim = 8, 15
    batch_size = 32
    n_train = 200

    # Create model
    model = BayesianMLP(in_dim, out_dim, width=128, depth=4,
                        prior_sigma=1.0).to(device)

    # Count parameters
    n_params = sum(p.numel() for p in model.parameters())
    print(f"Model parameters: {n_params}")

    # Test forward (sampling mode)
    x = torch.randn(batch_size, in_dim, device=device)
    mu, logvar = model(x, sample=True)
    print(f"Forward (sample=True):  mu.shape={mu.shape}, "
          f"logvar.shape={logvar.shape}")
    assert mu.shape == (batch_size, out_dim)
    assert logvar.shape == (batch_size, out_dim)

    # Test forward (deterministic mode)
    mu_det, logvar_det = model(x, sample=False)
    print(f"Forward (sample=False): mu.shape={mu_det.shape}")

    # Verify deterministic mode is consistent
    mu_det2, _ = model(x, sample=False)
    assert torch.allclose(mu_det, mu_det2), \
        "Deterministic forward should be identical across calls"
    print("Deterministic consistency: OK")

    # Verify sampling mode produces different outputs
    mu_s1, _ = model(x, sample=True)
    mu_s2, _ = model(x, sample=True)
    assert not torch.allclose(mu_s1, mu_s2), \
        "Sampling forward should differ across calls"
    print("Stochastic variability: OK")

    # Test return_z
    mu_z, logvar_z, z = model(x, sample=False, return_z=True)
    print(f"Forward (return_z=True): z.shape={z.shape}")

    # Test KL divergence
    kl = model.kl_divergence()
    print(f"KL divergence: {kl.item():.4f}")
    assert kl.item() >= 0, "KL divergence must be non-negative"
    assert kl.requires_grad, "KL must be differentiable"

    # Test ELBO loss
    y = torch.randn(batch_size, out_dim, device=device)
    loss = elbo_loss(y, mu, logvar, kl, kl_weight=1.0, n_train=n_train)
    print(f"ELBO loss: {loss.item():.4f}")
    loss.backward()
    print("Backward pass: OK")

    # Test logvar clamping
    assert logvar.min().item() >= -20.0
    assert logvar.max().item() <= 5.0
    print("Logvar clamping [-20, 5]: OK")

    # Test MC prediction
    mus_mc, logvars_mc = model.predict_mc(x, n_mc=10)
    print(f"predict_mc: mus.shape={mus_mc.shape}, "
          f"logvars.shape={logvars_mc.shape}")
    assert mus_mc.shape == (10, batch_size, out_dim)

    # Test mc_predict utility (with dummy scalers)
    from sklearn.preprocessing import StandardScaler as _SC
    sx_dummy = _SC()
    sy_dummy = _SC()
    X_dummy = np.random.randn(20, in_dim)
    Y_dummy = np.random.randn(20, out_dim)
    sx_dummy.fit(X_dummy)
    sy_dummy.fit(Y_dummy)

    mu_mean, mu_std, ale_var, epi_var, tot_var = mc_predict(
        model, X_dummy, sx_dummy, sy_dummy, device, n_mc=10
    )
    print(f"mc_predict: mu_mean.shape={mu_mean.shape}, "
          f"total_var.shape={tot_var.shape}")
    assert mu_mean.shape == (20, out_dim)
    assert np.all(tot_var >= 0), "Total variance must be non-negative"
    assert np.allclose(tot_var, ale_var + epi_var), \
        "Total = aleatoric + epistemic"
    print("Uncertainty decomposition: OK")

    # Test monotonicity loss compatibility
    x_req = x.detach().clone().requires_grad_(True)
    mu_mono, _ = model(x_req, sample=False)
    dummy_pairs = [(0, 3, +1, 0.8), (1, 7, -1, 0.6)]
    mono_loss = loss_monotone_from_mu(mu_mono, x_req, dummy_pairs)
    print(f"Monotonicity loss: {mono_loss.item():.6f}")

    # Test inequality loss compatibility
    ineq_rules = [
        {"name": "test_ge", "type": "greater_equal",
         "j_big": 1, "j_small": 0},
        {"name": "test_nn", "type": "nonneg", "j_val": 3, "bound": 0.0},
    ]
    ineq_loss = loss_inequality(mu_det, sy_dummy, w=1.0,
                                device=device, rules=ineq_rules)
    print(f"Inequality loss: {ineq_loss.item():.6f}")

    print("\n" + "=" * 60)
    print("  All smoke tests passed.")
    print("=" * 60)
