# config_server.py
# ============================================================
# BNN 0414 服务器端路径覆盖
#
# 在服务器上运行前，执行：
#   export HPR_ENV=server
# ============================================================

import os

# ── 数据路径 ─────────────────────────────────────────────────
CSV_PATH_SERVER = "/home/tjzs/Documents/fenics_data/fenics_data/txt_extract/dataset_v3.csv"
CSV_PATH_LOCAL  = ""

# ── 旧实验产物路径（仅用于 fixed_split，不复用 checkpoint）────
EXPR_ROOT_OLD_SERVER = "/home/tjzs/Documents/fenics_data/hpr_surrogate/code/0310/experiments_phys_levels"

# ── 设备设置 ─────────────────────────────────────────────────
DEVICE = "cuda"

# ── Optuna 并行设置 ─────────────────────────────────────────
TRIALS_MAIN     = 40   # BNN 训练更慢，40 trial
TRIALS_ABLATION = 30

# ── 运行方式 ─────────────────────────────────────────────────
# 服务器上执行（conda 环境 nn_env）：
#   cd /path/to/code/bnn0414/code/experiments_0404
#   export HPR_ENV=server
#   export HPR_LEGACY_DIR=/home/tjzs/.../code/0310
#   conda run -n nn_env python run_0404.py
