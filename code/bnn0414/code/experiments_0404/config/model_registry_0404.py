# model_registry_0404.py
# ============================================================
# BNN 0414 模型注册表
#
# BNN 版本的模型变体：
#   bnn-baseline       — BNN + ELBO only（纯贝叶斯基线）
#   bnn-data-mono      — BNN + ELBO + 数据 Spearman 单调性
#   bnn-phy-mono       — BNN + ELBO + 物理先验单调性
#   bnn-data-mono-ineq — BNN + ELBO + 数据单调性 + 物理不等式
#
# 对应 0411 的 5 个 HeteroMLP 模型，BNN 版保留 4 个。
# phy-ineq 在 BNN 下与 data-mono-ineq 近似等价（去掉 mono 后约束空间
# 退化到只有 ineq，和 data-mono-ineq 共享相同 ineq 实现），故不单列。
# 如论文需要 5 模型对齐图，可在画图层面用 data-mono-ineq 的曲线兼作
# phy-ineq 的展示，并在图注中注明"BNN 版本合并"。
# ============================================================

from experiment_config_0404 import INPUT_COLS, OUTPUT_COLS, SEED

# ────────────────────────────────────────────────────────────
# A. 输出维度与索引
# ────────────────────────────────────────────────────────────
N_INPUTS  = len(INPUT_COLS)   # 8
N_OUTPUTS = len(OUTPUT_COLS)  # 15

INPUT_IDX  = {c: i for i, c in enumerate(INPUT_COLS)}
OUTPUT_IDX = {c: i for i, c in enumerate(OUTPUT_COLS)}

# ────────────────────────────────────────────────────────────
# B. 物理先验单调性对（与 0411 完全一致）
# ────────────────────────────────────────────────────────────
PHYSICS_PRIOR_PAIRS_RAW = [
    ("E_intercept", "iteration2_max_global_stress",  +1, "high",
     "Higher base Young's modulus increases stiffness, amplifying thermally-induced stress"),
    ("alpha_base",  "iteration2_max_global_stress",  +1, "high",
     "Higher thermal expansion coefficient increases thermal strain and resulting stress"),
    ("alpha_slope", "iteration2_max_global_stress",  +1, "medium",
     "Higher temperature-dependent expansion slope increases expansion at operating temperatures"),
    ("SS316_k_ref", "iteration2_max_global_stress",  -1, "high",
     "Higher thermal conductivity reduces temperature gradients, reducing differential thermal expansion"),
    ("E_slope",     "iteration2_max_global_stress",  +1, "medium",
     "E_slope is negative; larger (less negative) E_slope means less modulus reduction at high T, "
     "higher effective stiffness → higher stress. Sign is +1 in data convention."),
    ("E_intercept", "iteration1_max_global_stress",  +1, "high",
     "Same mechanism as iter2"),
    ("alpha_base",  "iteration1_max_global_stress",  +1, "high",
     "Same mechanism as iter2"),
    ("SS316_k_ref", "iteration1_max_global_stress",  -1, "high",
     "Higher conductivity → lower temperature gradient → lower first-pass stress"),
    ("SS316_k_ref", "iteration2_max_fuel_temp",      -1, "high",
     "Better thermal conductivity improves heat transport → lower fuel temperature"),
    ("SS316_alpha", "iteration2_max_fuel_temp",      -1, "medium",
     "Higher conductivity slope generally improves heat transport at high temperatures"),
    ("SS316_k_ref", "iteration1_max_fuel_temp",      -1, "high",
     "Same mechanism: better conductivity → lower first-pass fuel temperature"),
    ("SS316_k_ref", "iteration2_max_monolith_temp",  -1, "high",
     "Better SS316 conductivity → lower monolith temperature"),
    ("SS316_k_ref", "iteration1_max_monolith_temp",  -1, "high",
     "Same: better conductivity → lower first-pass monolith temperature"),
    ("alpha_base",  "iteration2_keff",               -1, "medium",
     "Higher thermal expansion → increased neutron leakage → lower keff"),
    ("alpha_slope", "iteration2_keff",               -1, "medium",
     "Same mechanism as alpha_base but temperature-dependent"),
]

PHYSICS_PRIOR_PAIRS_HIGH = [
    (inp, out, sign)
    for inp, out, sign, conf, _ in PHYSICS_PRIOR_PAIRS_RAW
    if conf == "high"
]

PHYSICS_PRIOR_PAIRS_ALL = [
    (inp, out, sign)
    for inp, out, sign, conf, _ in PHYSICS_PRIOR_PAIRS_RAW
    if conf in ("high", "medium")
]

def _to_idx_pairs(raw_triples):
    pairs = []
    for inp, out, sign in raw_triples:
        if inp not in INPUT_IDX or out not in OUTPUT_IDX:
            continue
        pairs.append((INPUT_IDX[inp], OUTPUT_IDX[out], sign))
    return pairs

PHYSICS_IDX_PAIRS_HIGH = _to_idx_pairs(PHYSICS_PRIOR_PAIRS_HIGH)
PHYSICS_IDX_PAIRS_ALL  = _to_idx_pairs(PHYSICS_PRIOR_PAIRS_ALL)

# ────────────────────────────────────────────────────────────
# C. 物理不等式约束（与 0411 完全一致）
# ────────────────────────────────────────────────────────────
INEQUALITY_RULES = [
    {
        "name": "iter1_max_fuel_temp >= iter1_avg_fuel_temp",
        "j_big": OUTPUT_IDX["iteration1_max_fuel_temp"],
        "j_small": OUTPUT_IDX["iteration1_avg_fuel_temp"],
        "type": "greater_equal",
    },
    {
        "name": "iter2_max_fuel_temp >= iter2_avg_fuel_temp",
        "j_big": OUTPUT_IDX["iteration2_max_fuel_temp"],
        "j_small": OUTPUT_IDX["iteration2_avg_fuel_temp"],
        "type": "greater_equal",
    },
    {
        "name": "iter1_max_global_stress >= 0",
        "j_val": OUTPUT_IDX["iteration1_max_global_stress"],
        "bound": 0.0,
        "type": "nonneg",
    },
    {
        "name": "iter2_max_global_stress >= 0",
        "j_val": OUTPUT_IDX["iteration2_max_global_stress"],
        "bound": 0.0,
        "type": "nonneg",
    },
]

# ────────────────────────────────────────────────────────────
# D. BNN 模型定义
# ────────────────────────────────────────────────────────────
MODELS = {
    "bnn-baseline": {
        "short_id":       "bnn-baseline",
        "full_name":      "BNN Baseline (ELBO only)",
        "paper_role":     "BNN baseline comparison",
        "loss_nll":       True,
        "loss_kl":        True,
        "loss_mono_data": False,
        "loss_mono_phy":  False,
        "loss_ineq":      False,
        "n_outputs":      15,
        "fixed_split":    True,
        "repeat_split":   True,
        "optuna_trials":  40,
        "notes": "Pure BNN with ELBO loss. No physics constraints.",
    },

    "bnn-data-mono": {
        "short_id":       "bnn-data-mono",
        "full_name":      "BNN + Data-Monotone (ELBO + Spearman)",
        "paper_role":     "BNN with data-driven monotonicity",
        "loss_nll":       True,
        "loss_kl":        True,
        "loss_mono_data": True,
        "loss_mono_phy":  False,
        "loss_ineq":      False,
        "mono_method":    "spearman_rank_from_train",
        "n_outputs":      15,
        "fixed_split":    True,
        "repeat_split":   True,
        "optuna_trials":  40,
        "notes": "BNN + Spearman-rank monotonicity constraint on mean predictions.",
    },

    "bnn-phy-mono": {
        "short_id":       "bnn-phy-mono",
        "full_name":      "BNN + Physics-Prior Monotone (ELBO + physics-sign)",
        "paper_role":     "BNN with physics-prior monotonicity",
        "loss_nll":       True,
        "loss_kl":        True,
        "loss_mono_data": False,
        "loss_mono_phy":  True,
        "loss_ineq":      False,
        "mono_method":    "physics_prior_fixed_pairs",
        "n_outputs":      15,
        "fixed_split":    True,
        "repeat_split":   False,
        "optuna_trials":  30,
        "notes": "BNN + physics-prior monotonicity (high confidence pairs only).",
    },

    "bnn-data-mono-ineq": {
        "short_id":       "bnn-data-mono-ineq",
        "full_name":      "BNN + Data-Monotone + Inequality (ELBO + Spearman + physics bounds)",
        "paper_role":     "BNN full constraint model",
        "loss_nll":       True,
        "loss_kl":        True,
        "loss_mono_data": True,
        "loss_mono_phy":  False,
        "loss_ineq":      True,
        "mono_method":    "spearman_rank_from_train",
        "n_outputs":      15,
        "fixed_split":    True,
        "repeat_split":   False,
        "optuna_trials":  30,
        "notes": "BNN with full constraints: Spearman monotonicity + physics inequality.",
    },

    "bnn-baseline-homo": {
        "short_id":       "bnn-baseline-homo",
        "full_name":      "BNN Baseline Homoscedastic (ELBO, fixed noise)",
        "paper_role":     "Homoscedastic ablation",
        "loss_nll":       True,
        "loss_kl":        True,
        "loss_mono_data": False,
        "loss_mono_phy":  False,
        "loss_ineq":      False,
        "homoscedastic":  True,
        "n_outputs":      15,
        "fixed_split":    True,
        "repeat_split":   False,
        "optuna_trials":  30,
        "notes": "Homoscedastic BNN ablation: learnable log_noise parameter instead of input-dependent logvar head.",
    },

    "bnn-mf-stacked": {
        "short_id":       "bnn-mf-stacked",
        "full_name":      "Multi-Fidelity BNN (Stacked iter1→iter2)",
        "paper_role":     "Multi-fidelity compositional surrogate",
        "model_class":    "MultiFidelityBNN_Stacked",
        "loss_nll":       True,
        "loss_kl":        True,
        "loss_mono_data": False,
        "loss_mono_phy":  False,
        "loss_ineq":      False,
        "multifidelity":  True,
        "n_outputs":      15,
        "fixed_split":    True,
        "repeat_split":   False,
        "optuna_trials":  30,
        "notes": "Stage1: BNN(x→iter1). Stage2: BNN(x,iter1_pred→iter2). Joint or frozen-stage1 training.",
    },

    "bnn-mf-residual": {
        "short_id":       "bnn-mf-residual",
        "full_name":      "Multi-Fidelity BNN (Residual iter2−iter1)",
        "paper_role":     "Multi-fidelity discrepancy surrogate",
        "model_class":    "MultiFidelityBNN_Residual",
        "loss_nll":       True,
        "loss_kl":        True,
        "loss_mono_data": False,
        "loss_mono_phy":  False,
        "loss_ineq":      False,
        "multifidelity":  True,
        "n_outputs":      15,
        "fixed_split":    True,
        "repeat_split":   False,
        "optuna_trials":  30,
        "notes": "Stage1: BNN(x→iter1). Delta: BNN(x,iter1_pred→delta). keff: BNN(x→keff). iter2=iter1+delta.",
    },
}

# ────────────────────────────────────────────────────────────
# E. 重复划分设置
# ────────────────────────────────────────────────────────────
REPEAT_SPLIT_CONFIG = {
    "n_repeats":    5,
    "seeds":        [2026, 2027, 2028, 2029, 2030],
    "test_frac":    0.15,
    "val_frac":     0.1765,
    "use_best_hp_from_fixed": True,
}

# ────────────────────────────────────────────────────────────
# F. Optuna 搜索空间（BNN 版本）
# ────────────────────────────────────────────────────────────
OPTUNA_SPACE_BASE = {
    "width":       {"type": "int",   "low": 64,   "high": 256,  "log": True},
    "depth":       {"type": "int",   "low": 2,    "high": 6},      # BNN 更深容易不稳定
    "lr":          {"type": "float", "low": 1e-4, "high": 1e-3, "log": True},  # BNN 需要更小 lr
    "wd":          {"type": "float", "low": 1e-8, "high": 1e-4, "log": True},
    "batch":       {"type": "cat",   "choices": [32, 64, 128]},
    "epochs":      {"type": "int",   "low": 150,  "high": 400},    # BNN 需要更多 epochs
    "clip":        {"type": "float", "low": 0.5,  "high": 5.0,  "log": True},
    "w_data":      {"type": "float", "low": 0.5,  "high": 5.0,  "log": True},
    # BNN 特有超参
    "prior_sigma": {"type": "float", "low": 0.1,  "high": 2.0,  "log": True},
    "kl_weight":   {"type": "float", "low": 1e-4, "high": 1.0,  "log": True},
}

OPTUNA_SPACE_MONO = {
    "w_mono":       {"type": "float", "low": 1e-3, "high": 10.0, "log": True},
    "rho_abs_min":  {"type": "float", "low": 0.10, "high": 0.55},
    "mono_topk":    {"type": "int",   "low": 10,   "high": 120},
}

OPTUNA_SPACE_INEQ = {
    "w_ineq": {"type": "float", "low": 1e-4, "high": 5.0, "log": True},
}

OPTUNA_SPACE_MF = {
    "width1":       {"type": "int",   "low": 64,   "high": 256,  "log": True},
    "depth1":       {"type": "int",   "low": 2,    "high": 5},
    "width2":       {"type": "int",   "low": 64,   "high": 256,  "log": True},
    "depth2":       {"type": "int",   "low": 2,    "high": 5},
    "lr":           {"type": "float", "low": 1e-4, "high": 1e-3, "log": True},
    "batch":        {"type": "cat",   "choices": [32, 64, 128]},
    "epochs":       {"type": "int",   "low": 150,  "high": 400},
    "clip":         {"type": "float", "low": 0.5,  "high": 5.0,  "log": True},
    "w_data":       {"type": "float", "low": 0.5,  "high": 5.0,  "log": True},
    "prior_sigma":  {"type": "float", "low": 0.1,  "high": 2.0,  "log": True},
    "kl_weight":    {"type": "float", "low": 1e-4, "high": 1.0,  "log": True},
}

def get_optuna_space(model_id: str) -> dict:
    m = MODELS[model_id]
    if m.get("multifidelity"):
        return dict(OPTUNA_SPACE_MF)
    base = dict(OPTUNA_SPACE_BASE)
    if m.get("loss_mono_data") or m.get("loss_mono_phy"):
        base.update(OPTUNA_SPACE_MONO)
    if m.get("loss_ineq"):
        base.update(OPTUNA_SPACE_INEQ)
    return base


# ────────────────────────────────────────────────────────────
# G. 模型-实验矩阵
# ────────────────────────────────────────────────────────────
EXPERIMENT_MATRIX = {
    "risk_propagation": {
        "bnn-baseline":        True,
        "bnn-data-mono":       True,
        "bnn-phy-mono":        True,
        "bnn-data-mono-ineq":  True,
        "bnn-baseline-homo":   True,
        "bnn-mf-stacked":      True,
        "bnn-mf-residual":     True,
    },
    "sensitivity": {
        "bnn-baseline":        True,
        "bnn-data-mono":       True,
        "bnn-phy-mono":        True,
        "bnn-data-mono-ineq":  True,
        "bnn-mf-stacked":      True,
        "bnn-mf-residual":     True,
    },
    "posterior_inference": {
        "bnn-baseline":        True,
        "bnn-data-mono":       True,
        "bnn-phy-mono":        True,
        "bnn-data-mono-ineq":  True,
    },
    "computational_speedup": {
        "bnn-baseline":        True,
        "bnn-data-mono":       False,
        "bnn-phy-mono":        False,
        "bnn-data-mono-ineq":  False,
    },
    "generalization": {
        "bnn-baseline":        True,
        "bnn-data-mono":       True,
        "bnn-phy-mono":        True,
        "bnn-data-mono-ineq":  True,
        "bnn-mf-stacked":      True,
        "bnn-mf-residual":     True,
    },
}


# ────────────────────────────────────────────────────────────
# 工具函数
# ────────────────────────────────────────────────────────────
def list_models(role_filter=None):
    result = []
    for mid, m in MODELS.items():
        if role_filter is None or role_filter in m["paper_role"]:
            result.append(mid)
    return result

def get_model(model_id: str) -> dict:
    if model_id not in MODELS:
        raise KeyError(f"Unknown model_id: {model_id!r}. Available: {list(MODELS)}")
    return MODELS[model_id]

def get_physics_pairs_idx(confidence="high") -> list:
    if confidence == "high":
        return PHYSICS_IDX_PAIRS_HIGH
    return PHYSICS_IDX_PAIRS_ALL


if __name__ == "__main__":
    print("=" * 60)
    print("  BNN 0414 模型注册表")
    print("=" * 60)
    for mid, m in MODELS.items():
        print(f"  [{mid:25s}] {m['full_name']}")
        losses = []
        if m["loss_nll"]:       losses.append("NLL")
        if m["loss_kl"]:        losses.append("KL")
        if m.get("loss_mono_data"): losses.append("Mono-Data")
        if m.get("loss_mono_phy"):  losses.append("Mono-Phy")
        if m.get("loss_ineq"):      losses.append("Ineq")
        print(f"               loss: {' + '.join(losses)}")
    print(f"\n物理先验对（high）: {len(PHYSICS_IDX_PAIRS_HIGH)} 条")
    print(f"物理先验对（all）:  {len(PHYSICS_IDX_PAIRS_ALL)} 条")
