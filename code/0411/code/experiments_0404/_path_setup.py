# _path_setup.py
# ============================================================
# 路径引导模块
#
# 所有 experiments_0404/code/ 下的脚本在最顶部 import 本文件，
# 以确保能找到：
#   1. 本目录下的 config/ 子目录（experiment_config_0404 等）
#   2. code/0310/ 下的共享工具（run_phys_levels_main 等）
#
# 使用方式（每个脚本顶部）：
#   import sys, os
#   sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
#   from _path_setup import setup_paths
#   setup_paths()
# ============================================================

import os
import sys


def setup_paths():
    """
    将必要路径加入 sys.path。
    自动兼容 local（Mac）和 server（Linux）两种环境。
    """
    # 本脚本位于 experiments_0404/code/（不论在哪个子目录调用）
    this_file = os.path.abspath(__file__)
    code_dir  = os.path.dirname(this_file)           # experiments_0404/code/
    expr_dir  = os.path.dirname(code_dir)            # experiments_0404/
    proj_0310 = os.path.dirname(expr_dir)            # code/0310/

    # 1. experiments_0404/code/  —— 找本地的 config、utils
    _add(code_dir)
    _add(os.path.join(code_dir, "config"))

    # 2. code/0310/  —— 找 run_phys_levels_main, paper_experiment_config 等共享工具
    _add(proj_0310)

    # 3. 服务器端：如果上面的 proj_0310 路径不存在（路径结构不同），
    #    尝试环境变量 HPR_LEGACY_DIR
    legacy = os.environ.get("HPR_LEGACY_DIR", "")
    if legacy and os.path.isdir(legacy):
        _add(legacy)


def _add(path: str):
    if path and os.path.isdir(path) and path not in sys.path:
        sys.path.insert(0, path)
