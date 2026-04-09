# experiment_config_0404.py
# ============================================================
# 0404 重构 — 总实验配置
#
# 本文件是 0404 体系的唯一配置源。
# 所有训练脚本、评估脚本、画图脚本均从这里读取路径和参数。
#
# 与 paper_experiment_config.py 的关系：
#   本文件扩展并替代 paper_experiment_config.py，
#   保留原有字段以兼容旧下游脚本（通过 from ... import ...）
# ============================================================

import os
from datetime import date

# ────────────────────────────────────────────────────────────
# 环境检测（local vs server）
# ────────────────────────────────────────────────────────────
# 设置方式：
#   服务器：export HPR_ENV=server
#   本地：  不设置（默认 local）
_ENV = os.environ.get("HPR_ENV", "local").lower()   # "local" | "server"

# ────────────────────────────────────────────────────────────
# 基础路径
# ────────────────────────────────────────────────────────────
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))  # config/
_CODE_DIR   = os.path.dirname(_SCRIPT_DIR)                # experiments_0404/code/
_EXPR_0404  = os.path.dirname(_CODE_DIR)                  # experiments_0404/
_ROOT_0310  = os.path.dirname(_EXPR_0404)                 # code/0310/

# 新实验根目录（结果统一输出到 experiments_0404/）
EXPR_ROOT_0404 = _EXPR_0404

# 旧实验目录（只读参考，不覆盖）
#   服务器路径可通过环境变量 HPR_LEGACY_DIR 覆盖
_LEGACY_ENV = os.environ.get("HPR_LEGACY_DIR", "")
if _LEGACY_ENV and os.path.isdir(_LEGACY_ENV):
    EXPR_ROOT_OLD = os.path.join(_LEGACY_ENV, "experiments_phys_levels")
else:
    EXPR_ROOT_OLD = os.path.join(_ROOT_0310, "experiments_phys_levels")

# 共享 fixed split（直接复用旧 fixed split）
FIXED_SPLIT_DIR = os.path.join(EXPR_ROOT_OLD, "fixed_split")

# 数据路径
_DATA_ROOT_SERVER = "/home/tjzs/Documents/fenics_data/fenics_data/txt_extract"
CSV_PATH_SERVER   = os.path.join(_DATA_ROOT_SERVER, "dataset_v3.csv")
CSV_PATH_LOCAL    = ""   # 本地调试时可指向任意 CSV（留空回退到 fixed_split）


def get_csv_path() -> str:
    """优先用服务器路径，本地不可达时返回 None（调用方用 fixed_split CSV）。"""
    if os.path.exists(CSV_PATH_SERVER):
        return CSV_PATH_SERVER
    if CSV_PATH_LOCAL and os.path.exists(CSV_PATH_LOCAL):
        return CSV_PATH_LOCAL
    return None

# ────────────────────────────────────────────────────────────
# 实验日期标签（用于子目录、manifest 等）
# ────────────────────────────────────────────────────────────
EXPR_DATE = "0404"
RUN_DATE  = str(date.today())   # 实际运行日期（e.g. "2026-04-04"）

# ────────────────────────────────────────────────────────────
# 随机性 / 设备
# ────────────────────────────────────────────────────────────
SEED    = 2026
DEVICE  = "cuda"   # 如 GPU 不可用，训练脚本自动回退到 cpu

# ────────────────────────────────────────────────────────────
# Optuna 搜索设置
# ────────────────────────────────────────────────────────────
TRIALS_MAIN     = 60   # 主文模型（baseline, data-mono）
TRIALS_ABLATION = 40   # 对照/附录模型
OPTUNA_SEED     = SEED

# 关于 trial 数量的说明（详见 docs/repeated_split_rationale.md）：
# 60 trials 对于 8 维连续超参数空间是合理的工程实践。
# Bergstra & Bengio 2012 表明随机搜索在 ~60 trials 时已能
# 覆盖大多数关键超参数子空间。TPE sampler 在 ~30 trials 后
# 进入收益递减阶段。若计算资源充足可增至 100+。【待核实：
# 更大模型族下更多 trials 是否更稳健，建议以 baseline 为参照
# 跑 100 trials 并与 60 trials 对比。】

# ────────────────────────────────────────────────────────────
# 数据划分
# ────────────────────────────────────────────────────────────
TEST_FRAC  = 0.15
VAL_FRAC   = 0.1765   # val 占 train+val 的比例

# repeated split
REPEAT_N   = 5
REPEAT_SEEDS = [2026, 2027, 2028, 2029, 2030]

# ────────────────────────────────────────────────────────────
# 输入 / 输出列
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

PRIMARY_STRESS_THRESHOLD = 131.0  # MPa — SS316 屈服强度（运行温度）
THRESHOLD_SWEEP          = [110.0, 120.0, 131.0]   # 附录用

# ────────────────────────────────────────────────────────────
# 设计标称值（来自 code/material_config.py）
# 这是 forward UQ 扰动实验的中心点
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
# risk propagation 实验扰动设置（D1/D2）
# ────────────────────────────────────────────────────────────
RISK_PROP_N_SAMPLES      = 20000
RISK_PROP_SIGMA_K        = [0.5, 1.0, 1.5, 2.0]   # 主文风险-扰动曲线（移除3σ）
RISK_PROP_SIGMA_K_MAIN   = 1.0                     # 主文单点标准扰动
RISK_PROP_DRAW_PRED      = True

# D2: 围绕代表性 case 的扰动
RISK_PROP_CASE_SIGMA_K = [0.5, 1.0, 1.5]
RISK_PROP_CASE_CATEGORIES = ["low_stress", "near_threshold", "above_threshold", "extreme_stress"]
# case 选取方法：从 test split 里按应力分位数选代表性 case

# ────────────────────────────────────────────────────────────
# 敏感性分析设置
# ────────────────────────────────────────────────────────────
SOBOL_N_BASE     = 4096
SOBOL_BOOTSTRAP  = 512
SOBOL_CI_LEVEL   = 0.90

RANK_CORR_METHOD = ["spearman", "prcc"]   # 额外敏感性方法
MORRIS_N_TRAJ    = 50    # Morris method 轨迹数

# ────────────────────────────────────────────────────────────
# 后验推断设置
# ────────────────────────────────────────────────────────────
INVERSE_N_BENCHMARK    = 20   # 基准 case 数
INVERSE_N_EXTREME      = 10   # 高应力 case 数
INVERSE_MCMC_SAMPLES   = 1200
INVERSE_OBS_NOISE_STD  = {    # 各输出观测噪声（对数量纲，供 MCMC 使用）
    "default": 1.0,           # 标准化空间中的噪声标准差
}
INVERSE_CALIB_PARAMS   = [    # 标定参数子集（包括应力主控E_intercept、keff主控alpha_base/alpha_slope、应力第三敏感因子SS316_k_ref）
    "E_intercept", "alpha_base", "alpha_slope", "SS316_k_ref"
]
INVERSE_FIXED_PARAMS   = [    # 固定在先验均值的参数（不敏感或低敏感因子）
    "E_slope", "SS316_T_ref", "SS316_alpha", "nu"
]

# ────────────────────────────────────────────────────────────
# OOD 设置
# ────────────────────────────────────────────────────────────
OOD_FEATURE             = "alpha_slope"
OOD_KEEP_MIDDLE_RATIO   = 0.80

# ────────────────────────────────────────────────────────────
# 参数元信息（用于文档和图表标注）
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
# 0404 体系子目录辅助函数
# ────────────────────────────────────────────────────────────
def model_dir(model_id: str) -> str:
    """返回模型根目录。"""
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

# 兼容旧字段（供旧脚本 import）
OUT_DIR      = EXPR_ROOT_0404
PAPER_LEVELS = [0, 2]
TRIALS       = TRIALS_MAIN
FIXED_CKPT_PATH   = os.path.join(EXPR_ROOT_OLD, "fixed_surrogate_fixed_level2", "checkpoint_level2.pt")
FIXED_SCALER_PATH = os.path.join(EXPR_ROOT_OLD, "fixed_surrogate_fixed_level2", "scalers_level2.pkl")
FIXED_SURROGATE_TAG = "fixed_level2"
FIXED_SURROGATE_DIR = os.path.join(EXPR_ROOT_OLD, "fixed_surrogate_fixed_level2")
FIXED_META_PATH     = os.path.join(FIXED_SURROGATE_DIR, "metrics_level2.json")
FIXED_TEST_PRED_PATH= os.path.join(FIXED_SURROGATE_DIR, "test_predictions_level2.json")
FIXED_BEST_PARAM_PATH=os.path.join(FIXED_SURROGATE_DIR, "best_level2.json")
