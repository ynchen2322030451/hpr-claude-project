# _path_setup.py
# ============================================================
# BNN 0414 路径引导模块
#
# 确保能找到：
#   1. bnn0414/code/ 下的 bnn_model.py
#   2. bnn0414/code/experiments_0404/config/ 下的配置
#   3. code/0310/ 下的共享工具（paper_experiment_config 等）
# ============================================================

import os
import sys


def setup_paths():
    """
    将必要路径加入 sys.path。
    自动兼容 local（Mac）和 server（Linux）两种环境。
    """
    this_file = os.path.abspath(__file__)
    expr_0404 = os.path.dirname(this_file)        # experiments_0404/
    bnn_code  = os.path.dirname(expr_0404)        # bnn0414/code/
    bnn_root  = os.path.dirname(bnn_code)         # bnn0414/
    code_top  = os.path.dirname(bnn_root)         # code/
    root_0310 = os.path.join(code_top, "0310")    # code/0310/

    # IMPORTANT: _add() does sys.path.insert(0, ...), so the LAST added path
    # ends up at sys.path[0] (highest priority). bnn0414 paths must be added
    # LAST, otherwise 0310's top-level experiment_config_0404.py shadows the
    # bnn0414 one and child scripts fail with "cannot import name BNN_N_MC_*".

    # 1. HPR_LEGACY_DIR (lowest priority — only for genuinely legacy helpers)
    legacy = os.environ.get("HPR_LEGACY_DIR", "")
    if legacy and os.path.isdir(legacy):
        _add(legacy)

    # 2. code/0310/ — for paper_experiment_config etc
    _add(root_0310)

    # 3. bnn0414/code/ — for bnn_model.py
    _add(bnn_code)

    # 4. experiments_0404/config/ — HIGHEST priority, must come last so that
    # bnn0414's experiment_config_0404 / model_registry_0404 win over 0310's
    _add(os.path.join(expr_0404, "config"))


def _add(path: str):
    if path and os.path.isdir(path) and path not in sys.path:
        sys.path.insert(0, path)
