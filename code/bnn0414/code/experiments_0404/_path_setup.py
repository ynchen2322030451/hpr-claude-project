# _path_setup.py
# ============================================================
# 路径引导模块（bnn0414 版本）
#
# 所有 bnn0414/code/experiments_0404/ 下的脚本在最顶部 import 本文件，
# 以确保能找到：
#   1. 本目录下的 config/ 子目录（experiment_config_0404 等）
#   2. bnn0414/code/  下的 bnn_model.py（BNN 核心模型）
#   3. code/0310/ 下的共享工具（run_phys_levels_main 等）
#
# 目录层级：
#   this_file   → code/bnn0414/code/experiments_0404/_path_setup.py
#   code_dir    → code/bnn0414/code/experiments_0404/
#   bnn_code    → code/bnn0414/code/
#   bnn_root    → code/bnn0414/
#   code_top    → code/
#   proj_0310   → code/0310/
#
# 使用方式（每个脚本顶部）：
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
    # 本脚本位于 bnn0414/code/experiments_0404/
    this_file = os.path.abspath(__file__)
    code_dir  = os.path.dirname(this_file)              # bnn0414/code/experiments_0404/
    bnn_code  = os.path.dirname(code_dir)               # bnn0414/code/
    bnn_root  = os.path.dirname(bnn_code)               # bnn0414/
    code_top  = os.path.dirname(bnn_root)               # code/
    proj_0310 = os.path.join(code_top, "0310")          # code/0310/

    # 1. experiments_0404/  —— 找本地的 config、utils
    _add(code_dir)
    _add(os.path.join(code_dir, "config"))

    # 2. bnn0414/code/  —— 找 bnn_model.py 等 BNN 核心模块
    _add(bnn_code)

    # 3. code/0310/  —— 找 run_phys_levels_main, paper_experiment_config 等共享工具
    _add(proj_0310)

    # 4. 服务器端：如果上面的 proj_0310 路径不存在（路径结构不同），
    #    尝试环境变量 HPR_LEGACY_DIR
    legacy = os.environ.get("HPR_LEGACY_DIR", "")
    if legacy and os.path.isdir(legacy):
        _add(legacy)


def _add(path: str):
    if path and os.path.isdir(path) and path not in sys.path:
        sys.path.insert(0, path)
