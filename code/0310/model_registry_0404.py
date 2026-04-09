# model_registry_0404.py
# ============================================================
# 0404 模型体系注册表
# 定义所有模型的命名、loss 组成、来源映射、物理先验
#
# 命名规则（对外）：
#   baseline        — 纯数据异方差基线（NLL only）
#   data-mono       — NLL + 数据推导 Spearman 单调性约束
#   phy-mono        — NLL + 物理先验指定单调性约束
#   phy-ineq        — NLL + 物理不等式约束（温度/应力正性）
#   data-mono-ineq  — NLL + 数据单调性 + 物理不等式
#
# 内部映射（对应原来代码里的 level）：
#   baseline        ← level 0 / fixed_surrogate_fixed_base
#   data-mono       ← level 2 / fixed_surrogate_fixed_level2
#   phy-mono        ← NEW（E4 要求）
#   phy-ineq        ← level 3（partial, 去掉 monotone，只留 inequality）
#   data-mono-ineq  ← level 3（完整）
# ============================================================

from paper_experiment_config import (
    INPUT_COLS, OUTPUT_COLS, SEED, TRIALS,
    PRIMARY_STRESS_THRESHOLD,
)

# ────────────────────────────────────────────────────────────
# A. 输出维度与索引
# ────────────────────────────────────────────────────────────
N_INPUTS  = len(INPUT_COLS)   # 8
N_OUTPUTS = len(OUTPUT_COLS)  # 15

# 输入列索引 {name: idx}
INPUT_IDX  = {c: i for i, c in enumerate(INPUT_COLS)}
# 输出列索引 {name: idx}
OUTPUT_IDX = {c: i for i, c in enumerate(OUTPUT_COLS)}

# ────────────────────────────────────────────────────────────
# B. 物理先验单调性对（用于 phy-mono 和 phy-mono-ineq）
#
# 格式：(input_col, output_col, sign, confidence, rationale)
#   sign: +1 表示正相关（增大 input → 增大 output）
#         -1 表示负相关（增大 input → 减小 output）
#   confidence: "high" / "medium" / "low" / "待核实"
#   rationale: 物理原因简述
#
# 注：这里只列入 high/medium 置信度的关系
# ────────────────────────────────────────────────────────────
PHYSICS_PRIOR_PAIRS_RAW = [
    # ── 应力（iter2_max_global_stress）相关 ──
    # E_intercept（基础弹性模量）↑ → 刚性↑ → 热应力↑
    ("E_intercept", "iteration2_max_global_stress",  +1, "high",
     "Higher base Young's modulus increases stiffness, amplifying thermally-induced stress"),
    # alpha_base（热膨胀系数基准）↑ → 膨胀量↑ → 应力↑
    ("alpha_base",  "iteration2_max_global_stress",  +1, "high",
     "Higher thermal expansion coefficient increases thermal strain and resulting stress"),
    # alpha_slope（热膨胀温度斜率）↑ → 高温下膨胀更大 → 应力↑
    ("alpha_slope", "iteration2_max_global_stress",  +1, "medium",
     "Higher temperature-dependent expansion slope increases expansion at operating temperatures"),
    # SS316_k_ref（参考导热系数）↑ → 温度梯度↓ → 应力↓
    ("SS316_k_ref", "iteration2_max_global_stress",  -1, "high",
     "Higher thermal conductivity reduces temperature gradients, reducing differential thermal expansion"),
    # E_slope（弹性模量温度斜率，值为负）↓（更负）→ 高温 E 降低 → 应力↓
    # 注：E_slope 本身是负值，数据中 mean ≈ -7e7；
    #     更大的 |E_slope|（数值更负）→ 高温刚性更低 → 可能降低应力
    #     但符号关系与具体工况有关，置信度中等
    ("E_slope",     "iteration2_max_global_stress",  +1, "medium",
     "E_slope is negative; larger (less negative) E_slope means less modulus reduction at high T, "
     "higher effective stiffness → higher stress. Sign is +1 in data convention."),
    # iter1 应力类似
    ("E_intercept", "iteration1_max_global_stress",  +1, "high",
     "Same mechanism as iter2: higher base Young's modulus → higher first-pass stress"),
    ("alpha_base",  "iteration1_max_global_stress",  +1, "high",
     "Same mechanism as iter2: higher thermal expansion → higher first-pass stress"),
    ("SS316_k_ref", "iteration1_max_global_stress",  -1, "high",
     "Higher conductivity → lower temperature gradient → lower first-pass stress"),

    # ── 燃料温度（iter2_max_fuel_temp）相关 ──
    # SS316_k_ref↑ → 导热性好 → 热管导热能力强 → 燃料温度↓
    ("SS316_k_ref", "iteration2_max_fuel_temp",      -1, "high",
     "Better thermal conductivity in SS316 shell improves heat transport → lower fuel temperature"),
    ("SS316_alpha", "iteration2_max_fuel_temp",      -1, "medium",
     "Higher conductivity slope (SS316_alpha) generally improves heat transport at high temperatures"),
    ("SS316_k_ref", "iteration1_max_fuel_temp",      -1, "high",
     "Same mechanism: better conductivity → lower first-pass fuel temperature"),

    # ── 单石温度（iter2_max_monolith_temp）相关 ──
    ("SS316_k_ref", "iteration2_max_monolith_temp",  -1, "high",
     "Better SS316 conductivity → more effective heat pipe → lower monolith temperature"),
    ("SS316_k_ref", "iteration1_max_monolith_temp",  -1, "high",
     "Same: better conductivity → lower first-pass monolith temperature"),

    # ── keff（迭代耦合增殖系数）相关 ──
    # keff 在耦合下受热膨胀影响：alpha↑ → 膨胀↑ → 几何尺寸↑ → 中子泄漏↑ → keff↓
    # 但实际 keff 还受到很多因素影响，置信度中等，标记待核实
    ("alpha_base",  "iteration2_keff",               -1, "medium",
     "Higher thermal expansion → larger core geometry → increased neutron leakage → lower keff "
     "(dominant in coupled steady-state; 待核实: depends on reflector geometry)"),
    ("alpha_slope", "iteration2_keff",               -1, "medium",
     "Same mechanism as alpha_base but temperature-dependent; 待核实"),
]

# 过滤出高置信度（用于 phy-mono 主版本）
PHYSICS_PRIOR_PAIRS_HIGH = [
    (inp, out, sign)
    for inp, out, sign, conf, _ in PHYSICS_PRIOR_PAIRS_RAW
    if conf == "high"
]

# 全置信度（high + medium，用于附录模型或消融）
PHYSICS_PRIOR_PAIRS_ALL = [
    (inp, out, sign)
    for inp, out, sign, conf, _ in PHYSICS_PRIOR_PAIRS_RAW
    if conf in ("high", "medium")
]

# 转成索引格式：(input_idx, output_idx, sign)
def _to_idx_pairs(raw_triples):
    pairs = []
    for inp, out, sign in raw_triples:
        if inp not in INPUT_IDX:
            print(f"[WARN] Unknown input col: {inp}")
            continue
        if out not in OUTPUT_IDX:
            print(f"[WARN] Unknown output col: {out}")
            continue
        pairs.append((INPUT_IDX[inp], OUTPUT_IDX[out], sign))
    return pairs

PHYSICS_IDX_PAIRS_HIGH = _to_idx_pairs(PHYSICS_PRIOR_PAIRS_HIGH)
PHYSICS_IDX_PAIRS_ALL  = _to_idx_pairs(PHYSICS_PRIOR_PAIRS_ALL)


# ────────────────────────────────────────────────────────────
# C. 物理不等式约束（用于 phy-ineq 和 data-mono-ineq）
#
# 每条：lambda mu_raw → violation_tensor（正数 = 违约，0 = 满足）
# 仅记录约束规则，loss 计算在训练脚本中
# ────────────────────────────────────────────────────────────
# 规则（在原始量纲空间或标准化空间均可，具体看实现）：
# 1. iter1_max_fuel_temp >= iter1_avg_fuel_temp
# 2. iter2_max_fuel_temp >= iter2_avg_fuel_temp （数据集中确认存在此关系）
# 3. iter1_max_global_stress >= 0
# 4. iter2_max_global_stress >= 0
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
# D. 模型定义字典
# ────────────────────────────────────────────────────────────
MODELS = {

    # ── 主线基线 ──────────────────────────────────────────
    "baseline": {
        "short_id":       "baseline",
        "full_name":      "Heteroscedastic Baseline (NLL only)",
        "paper_role":     "main-text: baseline comparison",
        "source_level":   0,
        "source_dir":     "fixed_surrogate_fixed_base",
        "source_script":  "run_train_fixed_surrogates.py (TRAIN_LEVELS=[0])",
        "loss_nll":       True,
        "loss_mono_data": False,
        "loss_mono_phy":  False,
        "loss_ineq":      False,
        "mono_method":    None,
        "n_outputs":      15,
        "fixed_split":    True,
        "repeat_split":   True,
        "optuna_trials":  40,
        "deprecated":     False,
        "notes": (
            "Pure data-driven heteroscedastic MLP. "
            "Canonical reference for all downstream comparisons. "
            "Already trained; artifacts in experiments_phys_levels/fixed_surrogate_fixed_base/."
        ),
    },

    # ── 主线提升模型 ──────────────────────────────────────
    "data-mono": {
        "short_id":       "data-mono",
        "full_name":      "Data-Monotone Regularized (NLL + Spearman)",
        "paper_role":     "main-text: proposed regularized model",
        "source_level":   2,
        "source_dir":     "fixed_surrogate_fixed_level2",
        "source_script":  "run_train_fixed_surrogates.py (TRAIN_LEVELS=[2])",
        "loss_nll":       True,
        "loss_mono_data": True,
        "loss_mono_phy":  False,
        "loss_ineq":      False,
        "mono_method":    "spearman_rank_from_train",
        "mono_topk":      40,
        "mono_rho_min":   0.25,
        "n_outputs":      15,
        "fixed_split":    True,
        "repeat_split":   True,
        "optuna_trials":  40,
        "deprecated":     False,
        "notes": (
            "Augments NLL with Spearman-rank-derived monotonicity gradient penalty. "
            "Monotone pairs extracted from training data at each Optuna trial. "
            "Key distinction from phy-mono: direction information comes from data, not physics. "
            "Already trained; artifacts in experiments_phys_levels/fixed_surrogate_fixed_level2/."
        ),
    },

    # ── 物理先验单调性（新增 E4）────────────────────────
    "phy-mono": {
        "short_id":       "phy-mono",
        "full_name":      "Physics-Prior Monotone (NLL + physics-sign constraints)",
        "paper_role":     "ablation/comparison: disentangle data-derived vs physics-prior",
        "source_level":   None,
        "source_dir":     None,
        "source_script":  "run_train_0404.py (model='phy-mono')  [待训练]",
        "loss_nll":       True,
        "loss_mono_data": False,
        "loss_mono_phy":  True,
        "loss_ineq":      False,
        "mono_method":    "physics_prior_fixed_pairs",
        "mono_pairs_conf": "high",   # 只使用 high confidence 物理对
        "n_outputs":      15,
        "fixed_split":    True,
        "repeat_split":   True,
        "optuna_trials":  40,
        "deprecated":     False,
        "notes": (
            "Key design choice: monotonicity directions specified by physical reasoning BEFORE "
            "seeing data, not derived from data statistics. "
            "Pairs defined in PHYSICS_PRIOR_PAIRS_HIGH. "
            "Allows disentangling 'data-consistent physics' from 'purely data-driven'. "
            "Methodologically important: if phy-mono ≈ data-mono in performance, "
            "it suggests the Spearman pairs do capture genuine physics. "
            "New model; needs training via run_train_0404.py."
        ),
    },

    # ── 不等式约束（附录对照）──────────────────────────
    "phy-ineq": {
        "short_id":       "phy-ineq",
        "full_name":      "Physics-Inequality Constrained (NLL + physical bounds)",
        "paper_role":     "appendix: ablation of inequality constraint alone",
        "source_level":   3,   # partial: 去掉 monotone，只留 ineq
        "source_dir":     None,
        "source_script":  "run_train_0404.py (model='phy-ineq')  [待训练]",
        "loss_nll":       True,
        "loss_mono_data": False,
        "loss_mono_phy":  False,
        "loss_ineq":      True,
        "mono_method":    None,
        "n_outputs":      15,
        "fixed_split":    True,
        "repeat_split":   False,   # 附录用，只做 fixed
        "optuna_trials":  40,
        "deprecated":     False,
        "notes": (
            "Enforces physical inequalities (max_fuel_temp >= avg_fuel_temp, stress >= 0) "
            "without any monotonicity constraint. "
            "Serves as ablation to isolate contribution of inequality constraints. "
            "In original code, level3 intended to combine monotone+ineq; this model uses ineq only. "
            "New model; needs training."
        ),
    },

    # ── 全约束模型（附录完整版）────────────────────────
    "data-mono-ineq": {
        "short_id":       "data-mono-ineq",
        "full_name":      "Data-Monotone + Inequality (NLL + Spearman + physics bounds)",
        "paper_role":     "appendix: combined regularization (original level3 intent)",
        "source_level":   3,   # complete level3 as intended
        "source_dir":     None,
        "source_script":  "run_train_0404.py (model='data-mono-ineq')  [待训练]",
        "loss_nll":       True,
        "loss_mono_data": True,
        "loss_mono_phy":  False,
        "loss_ineq":      True,
        "mono_method":    "spearman_rank_from_train",
        "mono_topk":      40,
        "mono_rho_min":   0.25,
        "n_outputs":      15,
        "fixed_split":    True,
        "repeat_split":   False,
        "optuna_trials":  40,
        "deprecated":     False,
        "notes": (
            "Full combination of data-mono + phy-ineq. "
            "Original level3 design in run_phys_levels_main.py was this. "
            "Included as upper bound for regularization. "
            "May not outperform data-mono due to constraint conflict or over-regularization. "
            "New model; needs training."
        ),
    },
}

# ── 已废弃/遗留模型记录（不删除，仅归档）────────────────
DEPRECATED_MODELS = {
    "level1": {
        "reason": "Loss function (loss_level1_shifted) returns 0.0 — placeholder, never implemented.",
        "source_script": "run_phys_levels_main.py (level=1)",
    },
    "level4": {
        "reason": "Experimental bootstrap monotone + variance floor + delta head. "
                  "Not included in PAPER_LEVELS. Too many hyperparameters for fair comparison.",
        "source_script": "run_phys_levels_main.py (level=4)",
    },
    "remain_delta": {
        "reason": "Variant with delta head. Experimental. Not used in main paper flow.",
        "source_script": "run_phys_levels_main_remain_delta.py",
    },
    "oldmain": {
        "reason": "Legacy runs before split was frozen. Results not reproducible from current code.",
        "source_script": "early iterations of run_phys_levels_main.py",
    },
}

# ────────────────────────────────────────────────────────────
# E. 重复划分设置
# ────────────────────────────────────────────────────────────
REPEAT_SPLIT_CONFIG = {
    "n_repeats":    5,       # 5次重复随机划分
    "seeds":        [2026, 2027, 2028, 2029, 2030],
    "test_frac":    0.15,
    "val_frac":     0.1765,
    "use_best_hp_from_fixed": True,  # 用 fixed split 的最优超参再训练，不重跑 Optuna
    "rationale": (
        "5 repeats is a standard practice for medium-sized datasets (n~2900). "
        "Re-running Optuna for each repeat would be prohibitively expensive (~5x cost). "
        "Using fixed-split best hyperparameters for re-training provides split sensitivity "
        "estimate without adding hyperparameter noise. "
        "Reference: Raschka 2018 (Model Evaluation, Model Selection, and Algorithm Selection "
        "in Machine Learning) recommends 5-10 repeats for stable variance estimates."
    ),
}


# ────────────────────────────────────────────────────────────
# F. Optuna 搜索空间（统一定义，各模型共用基础空间）
# ────────────────────────────────────────────────────────────
OPTUNA_SPACE_BASE = {
    "width":   {"type": "int",   "low": 64,   "high": 256,  "log": True},
    "depth":   {"type": "int",   "low": 3,    "high": 8},
    "dropout": {"type": "float", "low": 0.0,  "high": 0.2},
    "lr":      {"type": "float", "low": 1e-4, "high": 3e-3, "log": True},
    "wd":      {"type": "float", "low": 1e-8, "high": 1e-3, "log": True},
    "batch":   {"type": "cat",   "choices": [32, 64, 128]},
    "epochs":  {"type": "int",   "low": 120,  "high": 300},
    "clip":    {"type": "float", "low": 0.5,  "high": 5.0,  "log": True},
    "w_data":  {"type": "float", "low": 0.5,  "high": 5.0,  "log": True},
}

OPTUNA_SPACE_MONO = {
    "w_mono":       {"type": "float", "low": 1e-3, "high": 10.0, "log": True},
    "rho_abs_min":  {"type": "float", "low": 0.10, "high": 0.55},
    "mono_topk":    {"type": "int",   "low": 10,   "high": 120},
}

OPTUNA_SPACE_INEQ = {
    "w_ineq": {"type": "float", "low": 1e-4, "high": 5.0, "log": True},
}

# 每个模型的完整搜索空间
def get_optuna_space(model_id: str) -> dict:
    base = dict(OPTUNA_SPACE_BASE)
    m = MODELS[model_id]
    if m["loss_mono_data"] or m["loss_mono_phy"]:
        base.update(OPTUNA_SPACE_MONO)
    if m["loss_ineq"]:
        base.update(OPTUNA_SPACE_INEQ)
    return base


# ────────────────────────────────────────────────────────────
# G. 模型-实验矩阵（哪些模型跑哪些下游实验）
# ────────────────────────────────────────────────────────────
EXPERIMENT_MATRIX = {
    # 实验名:           {model_id: run?, ...}
    "risk_propagation": {
        "baseline":        True,
        "data-mono":       True,
        "phy-mono":        True,
        "phy-ineq":        False,
        "data-mono-ineq":  True,   # 0409 补跑：性能上界对比
    },
    "sensitivity": {
        "baseline":        True,
        "data-mono":       True,
        "phy-mono":        True,   # 0406 补跑
        "phy-ineq":        False,
        "data-mono-ineq":  True,   # 0409 补跑：性能上界对比
    },
    "posterior_inference": {
        "baseline":        True,
        "data-mono":       True,
        "phy-mono":        True,   # 0406 补跑
        "phy-ineq":        False,
        "data-mono-ineq":  True,   # 0409 补跑：性能上界对比
    },
    "generalization": {
        "baseline":        True,
        "data-mono":       True,
        "phy-mono":        False,
        "phy-ineq":        False,
        "data-mono-ineq":  False,
    },
    "computational_speedup": {
        "baseline":        False,
        "data-mono":       True,
        "phy-mono":        False,
        "phy-ineq":        False,
        "data-mono-ineq":  False,
    },
    "physics_consistency": {
        # 不针对单个模型，全局分析
        "all": True,
    },
}


# ────────────────────────────────────────────────────────────
# 工具函数
# ────────────────────────────────────────────────────────────
def list_models(role_filter=None):
    """列出所有模型，可按 paper_role 过滤。"""
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
    """返回物理先验对的索引格式，按置信度过滤。"""
    if confidence == "high":
        return PHYSICS_IDX_PAIRS_HIGH
    elif confidence in ("all", "medium"):
        return PHYSICS_IDX_PAIRS_ALL
    else:
        raise ValueError(f"Unknown confidence level: {confidence!r}")


if __name__ == "__main__":
    print("=" * 60)
    print("  HPR 0404 模型注册表")
    print("=" * 60)
    print(f"\n已注册模型 ({len(MODELS)}):")
    for mid, m in MODELS.items():
        print(f"  [{mid:20s}] {m['full_name']}")
        print(f"               role: {m['paper_role']}")
        losses = []
        if m["loss_nll"]:       losses.append("NLL")
        if m["loss_mono_data"]: losses.append("Mono-Data")
        if m["loss_mono_phy"]:  losses.append("Mono-Phy")
        if m["loss_ineq"]:      losses.append("Ineq")
        print(f"               loss: {' + '.join(losses)}")
    print(f"\n物理先验对（high confidence）: {len(PHYSICS_IDX_PAIRS_HIGH)} 条")
    print(f"物理先验对（all confidence）: {len(PHYSICS_IDX_PAIRS_ALL)} 条")
    print(f"\n已废弃模型: {list(DEPRECATED_MODELS)}")
