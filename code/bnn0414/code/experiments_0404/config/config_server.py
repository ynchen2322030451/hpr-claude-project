# config_server.py
# ============================================================
# 服务器端路径覆盖
#
# 在服务器上运行前，执行：
#   export HPR_ENV=server
# 或者直接在脚本中 import 本文件覆盖路径。
#
# 本文件只需修改服务器上与本地不同的路径/设置。
# ============================================================

import os

# ── 数据路径 ─────────────────────────────────────────────────
CSV_PATH_SERVER = "/home/tjzs/Documents/fenics_data/fenics_data/txt_extract/dataset_v3.csv"
CSV_PATH_LOCAL  = ""   # 本地不可达，留空

# ── 旧实验产物路径（baseline / data-mono checkpoint 在此）─────
EXPR_ROOT_OLD_SERVER = "/home/tjzs/Documents/fenics_data/hpr_surrogate/code/0310/experiments_phys_levels"

# ── 设备设置 ─────────────────────────────────────────────────
DEVICE = "cuda"   # 服务器有 GPU；本地无 GPU 时自动回退 cpu

# ── Optuna 并行设置（服务器可开更多 trial）────────────────────
TRIALS_MAIN     = 60   # 服务器时间允许，60 trial
TRIALS_ABLATION = 40

# ── 运行方式 ─────────────────────────────────────────────────
# 服务器上执行（conda 环境 nn_env）：
#   cd /path/to/experiments_0404/code
#   export HPR_ENV=server
#   export HPR_LEGACY_DIR=/home/tjzs/.../code/0310
#   conda run -n nn_env python run_0404.py
