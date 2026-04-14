# experiment_config_0404.py
# ============================================================
# BNN 0414 — 实验配置
#
# 基于 code/0411 的 experiment_config_0404.py，
# 适配 BNN 模型（BayesianMLP 替代 HeteroMLP）。
#
# 与 0411 版本的区别：
#   - 路径指向 bnn0414/
#   - LEGACY 路径用于复用 fixed_split 和数据集
#   - BNN 特有的超参设置（MC 采样数、KL 权重等）
# ============================================================

import os
from datetime import date

# ────────────────────────────────────────────────────────────
# 环境检测
# ────────────────────────────────────────────────────────────
_ENV = os.environ.get("HPR_ENV", "local").lower()

# ────────────────────────────────────────────────────────────
# 基础路径
# ────────────────────────────────────────────────────────────
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))  # config/
_CODE_DIR   = os.path.dirname(_SCRIPT_DIR)                # experiments_0404/code/
_EXPR_BNN   = os.path.dirname(_CODE_DIR)                  # experiments_0404/
_BNN_ROOT   = os.path.dirname(_EXPR_BNN)                  # bnn0414/
_CODE_TOP   = os.path.dirname(_BNN_ROOT)                  # code/
_ROOT_0310  = os.path.join(_CODE_TOP, "0310")             # code/0310/

# 本实验根目录
EXPR_ROOT_0404 = _EXPR_BNN

# 旧实验目录（只读：复用 fixed_split、meta_stats 等）
_LEGACY_ENV = os.environ.get("HPR_LEGACY_DIR", "")
if _LEGACY_ENV and os.path.isdir(_LEGACY_ENV):
    EXPR_ROOT_OLD = os.path.join(_LEGACY_ENV, "experiments_phys_levels")
else:
    EXPR_ROOT_OLD = os.path.join(_ROOT_0310, "experiments_phys_levels")

# 共享 fixed split（直接复用 0310 的冻结划分）
FIXED_SPLIT_DIR = os.path.join(EXPR_ROOT_OLD, "fixed_split")

# 数据路径
_DATA_ROOT_SERVER = "/home/tjzs/Documents/fenics_data/fenics_data/txt_extract"
CSV_PATH_SERVER   = os.path.join(_DATA_ROOT_SERVER, "dataset_v3.csv")
CSV_PATH_LOCAL    = ""


def get_csv_path() -> str:
    if os.path.exists(CSV_PATH_SERVER):
        return CSV_PATH_SERVER
    if CSV_PATH_LOCAL and os.path.exists(CSV_PATH_LOCAL):
        return CSV_PATH_LOCAL
    return None

# ────────────────────────────────────────────────────────────
# 实验日期标签
# ────────────────────────────────────────────────────────────
EXPR_DATE = "bnn0414"
RUN_DATE  = str(date.today())

# ────────────────────────────────────────────────────────────
# 随机性 / 设备
# ────────────────────────────────────────────────────────────
SEED   = 2026
DEVICE = "cuda"

# ────────────────────────────────────────────────────────────
# Optuna 搜索设置
# ────────────────────────────────────────────────────────────
TRIALS_MAIN     = 40   # BNN 训练更慢，适当减少 trial
TRIALS_ABLATION = 30
OPTUNA_SEED     = SEED

# ────────────────────────────────────────────────────────────
# 数据划分
# ────────────────────────────────────────────────────────────
TEST_FRAC  = 0.15
VAL_FRAC   = 0.1765
REPEAT_N   = 5
REPEAT_SEEDS = [2026, 2027, 2028, 2029, 2030]

# ────────────────────────────────────────────────────────────
# 输入 / 输出列（与 0411 完全一致）
# ────────────────────────────────────────────────────────────
INPUT_COLS = [
    "E_slope", "E_intercept", "nu", "alpha_base",
    "alpha_slope", "SS316_T_ref", "SS316_k_ref", "SS316_alpha"
]

OUT1 = [
    "iteration1_avg_fuel_temp",
    "iteration1_max_fuel_temp",
    "iteration1_max_monolith_temp",
    "iteration1_max_global_stress",
    "iteration1_monolith_new_temperature",
    "iteration1_Hcore_after",
    "iteration1_wall2",
]

OUT2 = [
    "iteration2_keff",
    "iteration2_avg_fuel_temp",
    "iteration2_max_fuel_temp",
    "iteration2_max_monolith_temp",
    "iteration2_max_global_stress",
    "iteration2_monolith_new_temperature",
    "iteration2_Hcore_after",
    "iteration2_wall2",
]

OUTPUT_COLS = OUT1 + OUT2  # 15 outputs
ITER1_IDX   = list(range(0, 7))
ITER2_IDX   = list(range(7, 15))

DELTA_PAIRS = [
    ("iteration1_avg_fuel_temp",          "iteration2_avg_fuel_temp"),
    ("iteration1_max_fuel_temp",          "iteration2_max_fuel_temp"),
    ("iteration1_max_monolith_temp",      "iteration2_max_monolith_temp"),
    ("iteration1_max_global_stress",      "iteration2_max_global_stress"),
    ("iteration1_monolith_new_temperature","iteration2_monolith_new_temperature"),
    ("iteration1_Hcore_after",            "iteration2_Hcore_after"),
    ("iteration1_wall2",                  "iteration2_wall2"),
]

# ────────────────────────────────────────────────────────────
# 主要输出与阈值
# ────────────────────────────────────────────────────────────
PRIMARY_OUTPUTS = [
    "iteration2_keff",
    "iteration2_max_fuel_temp",
    "iteration2_max_monolith_temp",
    "iteration2_max_global_stress",
    "iteration2_wall2",
]
PRIMARY_STRESS_OUTPUT    = "iteration2_max_global_stress"
PRIMARY_AUXILIARY_OUTPUT = "iteration2_keff"
PRIMARY_SA_OUTPUTS       = ["iteration2_max_global_stress", "iteration2_keff"]

PRIMARY_STRESS_THRESHOLD = 131.0
THRESHOLD_SWEEP          = [110.0, 120.0, 131.0]

# ────────────────────────────────────────────────────────────
# 设计标称值
# ────────────────────────────────────────────────────────────
DESIGN_NOMINAL = {
    "E_slope":      -7e7,
    "E_intercept":   2e11,
    "nu":            0.31,
    "alpha_base":    1e-5,
    "alpha_slope":   5e-9,
    "SS316_T_ref":   923.15,
    "SS316_k_ref":   23.2,
    "SS316_alpha":   1/75,
}
DESIGN_SIGMA = {
    "E_slope":       7e6,
    "E_intercept":   2e10,
    "nu":            0.031,
    "alpha_base":    1e-6,
    "alpha_slope":   5e-10,
    "SS316_T_ref":   92.315,
    "SS316_k_ref":   2.32,
    "SS316_alpha":   1/750,
}

# ────────────────────────────────────────────────────────────
# BNN 特有设置
# ────────────────────────────────────────────────────────────
BNN_N_MC_TRAIN   = 1     # 训练时每 batch 采样次数（1 = 标准 ELBO）
BNN_N_MC_EVAL    = 50    # 评估/推断时 MC 采样次数
BNN_N_MC_SOBOL   = 30    # Sobol 分析时 MC 采样次数
BNN_N_MC_POSTERIOR = 20  # 后验 MCMC 内循环 MC 采样次数

# ────────────────────────────────────────────────────────────
# risk propagation 实验
# ────────────────────────────────────────────────────────────
RISK_PROP_N_SAMPLES      = 20000
RISK_PROP_SIGMA_K        = [0.5, 1.0, 1.5, 2.0]
RISK_PROP_SIGMA_K_MAIN   = 1.0
RISK_PROP_DRAW_PRED      = True

RISK_PROP_CASE_SIGMA_K = [0.5, 1.0, 1.5]
RISK_PROP_CASE_CATEGORIES = ["low_stress", "near_threshold", "above_threshold", "extreme_stress"]

# ────────────────────────────────────────────────────────────
# 敏感性分析设置
# ────────────────────────────────────────────────────────────
SOBOL_N_BASE     = 4096
SOBOL_BOOTSTRAP  = 512
SOBOL_CI_LEVEL   = 0.90
RANK_CORR_METHOD = ["spearman", "prcc"]
MORRIS_N_TRAJ    = 50

# ────────────────────────────────────────────────────────────
# 后验推断设置
# ────────────────────────────────────────────────────────────
INVERSE_N_BENCHMARK    = 20
INVERSE_N_EXTREME      = 10
INVERSE_MCMC_SAMPLES   = 1200
INVERSE_OBS_NOISE_STD  = {"default": 1.0}
INVERSE_CALIB_PARAMS   = ["E_intercept", "alpha_base", "alpha_slope", "SS316_k_ref"]
INVERSE_FIXED_PARAMS   = ["E_slope", "SS316_T_ref", "SS316_alpha", "nu"]

# ────────────────────────────────────────────────────────────
# OOD 设置
# ────────────────────────────────────────────────────────────
OOD_FEATURE             = "alpha_slope"
OOD_KEEP_MIDDLE_RATIO   = 0.80

# ────────────────────────────────────────────────────────────
# 参数元信息
# ────────────────────────────────────────────────────────────
PARAM_META = {
    "E_slope":      {"unit": "Pa/K",      "label": r"$E_\mathrm{slope}$",      "meaning": "Young's modulus temp. slope"},
    "E_intercept":  {"unit": "Pa",        "label": r"$E_\mathrm{intercept}$",  "meaning": "Young's modulus intercept"},
    "nu":           {"unit": "-",         "label": r"$\nu$",                   "meaning": "Poisson's ratio"},
    "alpha_base":   {"unit": "1/K",       "label": r"$\alpha_\mathrm{base}$",  "meaning": "Thermal expansion (base)"},
    "alpha_slope":  {"unit": "1/K^2",     "label": r"$\alpha_\mathrm{slope}$", "meaning": "Thermal expansion (slope)"},
    "SS316_T_ref":  {"unit": "K",         "label": r"$T_\mathrm{ref}$",        "meaning": "SS316 reference temperature"},
    "SS316_k_ref":  {"unit": "W/(m·K)",   "label": r"$k_\mathrm{ref}$",        "meaning": "SS316 thermal conductivity"},
    "SS316_alpha":  {"unit": "W/(m·K^2)", "label": r"$k_\mathrm{slope}$",      "meaning": "SS316 conductivity slope"},
}

OUTPUT_META = {
    "iteration2_max_global_stress":    {"unit": "MPa",  "label": "Max. global stress (iter2)",      "primary": True},
    "iteration2_keff":                 {"unit": "-",    "label": r"$k_\mathrm{eff}$ (iter2)",       "primary": True},
    "iteration2_max_fuel_temp":        {"unit": "K",    "label": "Max. fuel temp. (iter2)",          "primary": True},
    "iteration2_max_monolith_temp":    {"unit": "K",    "label": "Max. monolith temp. (iter2)",      "primary": True},
    "iteration2_wall2":                {"unit": "mm",   "label": "Wall expansion (iter2)",           "primary": True},
    "iteration1_max_global_stress":    {"unit": "MPa",  "label": "Max. global stress (iter1)",      "primary": False},
    "iteration1_max_fuel_temp":        {"unit": "K",    "label": "Max. fuel temp. (iter1)",          "primary": False},
    "iteration1_max_monolith_temp":    {"unit": "K",    "label": "Max. monolith temp. (iter1)",      "primary": False},
}

# ────────────────────────────────────────────────────────────
# 子目录辅助函数
# ────────────────────────────────────────────────────────────
def model_dir(model_id: str) -> str:
    return os.path.join(EXPR_ROOT_0404, "models", model_id)

def model_artifacts_dir(model_id: str) -> str:
    return os.path.join(model_dir(model_id), "artifacts")

def model_fixed_eval_dir(model_id: str) -> str:
    return os.path.join(model_dir(model_id), "fixed_eval")

def model_repeat_eval_dir(model_id: str) -> str:
    return os.path.join(model_dir(model_id), "repeat_eval")

def model_manifests_dir(model_id: str) -> str:
    return os.path.join(model_dir(model_id), "manifests")

def model_logs_dir(model_id: str) -> str:
    return os.path.join(model_dir(model_id), "logs")

def experiment_dir(exp_name: str) -> str:
    return os.path.join(EXPR_ROOT_0404, "experiments", exp_name)

def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)
    return path
