#!/usr/bin/env python3
# run_0404.py
# ============================================================
# 0404 总控脚本
#
# 使用方式（不用 --arg 参数，直接修改下面的 RUN_CONFIG）：
#
#   1. 默认全跑主线：
#      python run_0404.py
#      （按 RUN_CONFIG 中 "preset": "main" 的默认行为）
#
#   2. 只重新训练某模型：
#      把 RUN_CONFIG["preset"] 改成 "custom"，
#      在 custom_models 里写模型名，modules 只开 "train"
#
#   3. 只重画图：
#      把 modules 里只开 "figures": True，其他全关
#
#   4. 跑附录模块：
#      把 "preset" 改成 "appendix"
#
# ──────────────────────────────────────────────────────────
# ★ 唯一需要修改的地方就是下面的 RUN_CONFIG ★
# ============================================================

# ============================================================
# ★ 修改这里来控制运行行为 ★
# ============================================================
RUN_CONFIG = {
    # preset 选项：
    #   "main"     — 主文主线（baseline + data-mono，主文实验全跑）
    #   "appendix" — 附录模型（phy-mono + phy-ineq + data-mono-ineq + 附录实验）
    #   "all"      — 全部模型 + 全部实验（时间很长）
    #   "custom"   — 完全按 custom_models 和 modules 手动控制
    #
    # ★ 0406 补跑：phy-mono 的 Sobol 敏感性 + MCMC 后验推断
    #   phy-mono 已训练完成，不需要重跑训练和评估
    "preset": "custom",

    # ── custom 模式下才生效 ──
    "custom_models": [
        "phy-mono",   # 只补跑 phy-mono 的缺失实验
    ],

    # ── 模块开关 ──
    "modules": {
        "train":               False,  # 已有 checkpoint，不重训
        "eval_fixed":          False,  # 已完成
        "eval_repeat":         False,
        "risk_propagation":    False,  # 已完成
        "sensitivity":         True,   # ★ 补跑 phy-mono Sobol
        "posterior_inference": True,   # ★ 补跑 phy-mono MCMC 后验推断
        "generalization":      False,
        "computational_speedup": False,
        "physics_consistency": False,
        "figures_main":        False,
        "figures_appendix":    False,
    },

    # ── 其他选项 ──
    "force_retrain":   False,   # 绝对不重训
    "dry_run":         False,   # True = 只打印计划，不实际运行
    "log_level":       "INFO",
}
# ============================================================


import os
import sys
import json
import logging
import subprocess
from datetime import datetime
from pathlib import Path

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Resolve code roots: add config/ and legacy code/0310/ to path
_CODE_ROOT = _SCRIPT_DIR
while _CODE_ROOT and not os.path.basename(_CODE_ROOT) == 'code':
    _CODE_ROOT = os.path.dirname(_CODE_ROOT)
for _p in (_SCRIPT_DIR,
           os.path.join(_CODE_ROOT, 'config'),
           os.path.dirname(_CODE_ROOT),        # experiments_0404/
           os.path.dirname(os.path.dirname(_CODE_ROOT)),  # code/0310/
           os.environ.get('HPR_LEGACY_DIR', '')):
    if _p and os.path.isdir(_p) and _p not in sys.path:
        sys.path.insert(0, _p)
del _CODE_ROOT, _p

from experiment_config_0404 import EXPR_ROOT_0404, RUN_DATE, ensure_dir
from model_registry_0404 import MODELS, EXPERIMENT_MATRIX

# ────────────────────────────────────────────────────────────
# Preset 展开
# ────────────────────────────────────────────────────────────
_PRESETS = {
    "main": {
        # 第一批闭环：只跑主线必要模块
        # eval → risk D1 → sobol → posterior benchmark
        # generalization / physics_consistency 移到 "extended" preset 后再做
        "models": ["baseline", "data-mono"],
        "modules": {
            "train":               True,
            "eval_fixed":          True,
            "eval_repeat":         False,
            "risk_propagation":    True,   # D1 only（run_risk_propagation 内部控制）
            "sensitivity":         True,   # sobol only（SA_METHOD env var 控制）
            "posterior_inference": True,   # benchmark only（POSTERIOR_MODE env var 控制）
            "generalization":      False,  # 闭环验通后再开
            "computational_speedup": False,
            "physics_consistency": False,  # 闭环验通后再开
            "figures_main":        True,
            "figures_appendix":    False,
        },
    },
    "extended": {
        # 闭环验通后的第二批：OOD + 物理一致性 + 附录图
        "models": ["baseline", "data-mono"],
        "modules": {
            "train":               False,
            "eval_fixed":          False,
            "eval_repeat":         True,
            "risk_propagation":    False,
            "sensitivity":         False,
            "posterior_inference": False,
            "generalization":      True,
            "computational_speedup": False,
            "physics_consistency": True,
            "figures_main":        False,
            "figures_appendix":    True,
        },
    },
    "appendix": {
        "models": ["phy-mono", "phy-ineq", "data-mono-ineq"],
        "modules": {
            "train":               True,
            "eval_fixed":          True,
            "eval_repeat":         False,
            "risk_propagation":    True,
            "sensitivity":         False,
            "posterior_inference": False,
            "generalization":      False,
            "computational_speedup": False,
            "physics_consistency": False,
            "figures_main":        False,
            "figures_appendix":    True,
        },
    },
    "all": {
        "models": list(MODELS.keys()),
        "modules": {k: True for k in [
            "train", "eval_fixed", "eval_repeat",
            "risk_propagation", "sensitivity", "posterior_inference",
            "generalization", "computational_speedup", "physics_consistency",
            "figures_main", "figures_appendix",
        ]},
    },
    "custom": None,   # 直接读 RUN_CONFIG["custom_models"] 和 ["modules"]
    # "extended": 见上方定义
}


def resolve_config(cfg: dict) -> dict:
    """将 preset 展开成最终的 {models, modules} 字典。"""
    preset = cfg.get("preset", "main")
    if preset == "custom":
        models  = cfg["custom_models"]
        modules = cfg["modules"]
    else:
        p = _PRESETS[preset]
        models  = p["models"]
        modules = dict(p["modules"])
        # 允许 custom modules 覆盖 preset（只覆盖显式设置的）
        for k, v in cfg.get("modules", {}).items():
            modules[k] = v
    return {"models": models, "modules": modules}


# ────────────────────────────────────────────────────────────
# 日志设置
# ────────────────────────────────────────────────────────────
def setup_logging(level_str="INFO") -> logging.Logger:
    level = getattr(logging, level_str.upper(), logging.INFO)
    log_dir = ensure_dir(os.path.join(EXPR_ROOT_0404, "_config"))
    log_file = os.path.join(log_dir, f"run_0404_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    handlers = [
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_file, encoding="utf-8"),
    ]
    logging.basicConfig(
        level=level,
        format="[%(asctime)s %(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
        handlers=handlers,
    )
    return logging.getLogger("run_0404")


# ────────────────────────────────────────────────────────────
# 子脚本调用辅助
# ────────────────────────────────────────────────────────────
def _find_script(name: str):
    """Search for a script by filename in _SCRIPT_DIR and its immediate subdirectories."""
    # direct hit
    p = os.path.join(_SCRIPT_DIR, name)
    if os.path.exists(p):
        return p
    # search one level of subdirs
    for sub in ("training", "evaluation", "experiments", "figures", "config"):
        p = os.path.join(_SCRIPT_DIR, sub, name)
        if os.path.exists(p):
            return p
    return None


def run_script(script_name: str, env_overrides: dict, logger: logging.Logger,
               dry_run: bool = False) -> bool:
    """
    运行 _SCRIPT_DIR 下（或其子目录中）的某个 Python 脚本。
    env_overrides 里的 key=value 通过环境变量传递（无 --arg 风格）。
    返回 True 表示成功。
    """
    script_path = _find_script(script_name)
    if script_path is None:
        logger.warning(f"[SKIP] 脚本不存在（尚未实现）: {script_name}")
        return False

    env = os.environ.copy()
    for k, v in env_overrides.items():
        env[k] = str(v)

    cmd = [sys.executable, script_path]
    logger.info(f"[RUN ] {script_name}")
    if env_overrides:
        logger.info(f"       env: {env_overrides}")

    if dry_run:
        logger.info(f"       [DRY RUN — 不实际执行]")
        return True

    result = subprocess.run(cmd, env=env, cwd=_SCRIPT_DIR)
    if result.returncode != 0:
        logger.error(f"[FAIL] {script_name} 返回码 {result.returncode}")
        return False
    logger.info(f"[OK  ] {script_name} 完成")
    return True


# ────────────────────────────────────────────────────────────
# 主流程
# ────────────────────────────────────────────────────────────
def main():
    cfg     = resolve_config(RUN_CONFIG)
    models  = cfg["models"]
    modules = cfg["modules"]
    dry_run = RUN_CONFIG.get("dry_run", False)
    force   = RUN_CONFIG.get("force_retrain", False)

    logger = setup_logging(RUN_CONFIG.get("log_level", "INFO"))

    # ── 打印最终生效配置（preset 展开后）──────────────────
    # 注意：这是 preset 展开 + modules 覆盖后的最终结果，
    # 与 RUN_CONFIG["modules"] 顶部显示的内容可能不同。
    logger.info("=" * 65)
    logger.info(f"  HPR 0404 总控脚本  [{RUN_DATE}]")
    logger.info(f"  preset        : {RUN_CONFIG['preset']}")
    logger.info(f"  force_retrain : {force}")
    logger.info(f"  dry_run       : {dry_run}")
    logger.info("-" * 65)
    logger.info("  ★ 最终生效 models（preset 展开后）:")
    for m in models:
        logger.info(f"      {m}")
    logger.info("  ★ 最终生效 modules（preset 展开后）:")
    for k, v in modules.items():
        mark = "ON " if v else "off"
        logger.info(f"      [{mark}]  {k}")
    logger.info("-" * 65)
    logger.info("  artifact 来源说明：baseline / data-mono 使用旧")
    logger.info("  experiments_phys_levels/ 的 checkpoint（reused_legacy）。")
    logger.info("  phy-mono 等新模型会在 0404 框架下重新训练。")
    logger.info("=" * 65)

    results = {}

    # ── 1. 训练 ──────────────────────────────────────────
    if modules.get("train"):
        logger.info("\n[PHASE] 训练")
        for mid in models:
            minfo = MODELS.get(mid)
            if minfo is None:
                logger.warning(f"  [SKIP] 未知模型: {mid}")
                continue

            ckpt = os.path.join(EXPR_ROOT_0404, "models", mid, "artifacts",
                                f"checkpoint_{mid}.pt")
            if os.path.exists(ckpt) and not force:
                logger.info(f"  [SKIP] {mid}: checkpoint 已存在 ({ckpt})")
                continue

            ok = run_script(
                "run_train_0404.py",
                {"MODEL_ID": mid, "FORCE_RETRAIN": "1" if force else "0"},
                logger, dry_run,
            )
            results[f"train:{mid}"] = ok

    # ── 2. 评估（fixed split）──────────────────────────
    if modules.get("eval_fixed"):
        logger.info("\n[PHASE] 评估（fixed split）")
        for mid in models:
            ok = run_script(
                "run_eval_0404.py",
                {"MODEL_ID": mid, "EVAL_MODE": "fixed",
                 "EVAL_FORCE": "1" if force else "0"},
                logger, dry_run,
            )
            results[f"eval_fixed:{mid}"] = ok

    # ── 3. 评估（repeated split）──────────────────────
    if modules.get("eval_repeat"):
        logger.info("\n[PHASE] 评估（repeated splits）")
        for mid in models:
            ok = run_script(
                "run_eval_0404.py",
                {"MODEL_ID": mid, "EVAL_MODE": "repeat",
                 "EVAL_FORCE": "1" if force else "0"},
                logger, dry_run,
            )
            results[f"eval_repeat:{mid}"] = ok

    # ── 4. 正向传播与风险实验 ───────────────────────────
    if modules.get("risk_propagation"):
        logger.info("\n[PHASE] 正向传播 + 风险实验")
        for mid in models:
            if not EXPERIMENT_MATRIX.get("risk_propagation", {}).get(mid, False):
                logger.info(f"  [SKIP] {mid}: 不在 risk_propagation 实验矩阵中")
                continue
            ok = run_script(
                "run_risk_propagation_0404.py",
                {"MODEL_ID": mid},
                logger, dry_run,
            )
            results[f"risk:{mid}"] = ok

    # ── 5. 敏感性分析 ──────────────────────────────────
    if modules.get("sensitivity"):
        logger.info("\n[PHASE] 敏感性分析")
        for mid in models:
            if not EXPERIMENT_MATRIX.get("sensitivity", {}).get(mid, False):
                logger.info(f"  [SKIP] {mid}: 不在 sensitivity 实验矩阵中")
                continue
            ok = run_script(
                "run_sensitivity_0404.py",
                {"MODEL_ID": mid},
                logger, dry_run,
            )
            results[f"sensitivity:{mid}"] = ok

    # ── 6. 后验推断 ────────────────────────────────────
    if modules.get("posterior_inference"):
        logger.info("\n[PHASE] 后验推断（MCMC）")
        for mid in models:
            if not EXPERIMENT_MATRIX.get("posterior_inference", {}).get(mid, False):
                logger.info(f"  [SKIP] {mid}: 不在 posterior_inference 实验矩阵中")
                continue
            ok = run_script(
                "run_posterior_0404.py",
                {"MODEL_ID": mid},
                logger, dry_run,
            )
            results[f"inverse:{mid}"] = ok

    # ── 7. OOD 泛化 ────────────────────────────────────
    if modules.get("generalization"):
        logger.info("\n[PHASE] OOD 泛化实验")
        for mid in models:
            if not EXPERIMENT_MATRIX.get("generalization", {}).get(mid, False):
                continue
            ok = run_script(
                "run_generalization_0404.py",
                {"MODEL_ID": mid},
                logger, dry_run,
            )
            results[f"ood:{mid}"] = ok

    # ── 8. 速度对比 ────────────────────────────────────
    if modules.get("computational_speedup"):
        logger.info("\n[PHASE] 计算速度对比")
        for mid in models:
            if not EXPERIMENT_MATRIX.get("computational_speedup", {}).get(mid, False):
                continue
            ok = run_script(
                "run_speed_0404.py",
                {"MODEL_ID": mid},
                logger, dry_run,
            )
            results[f"speed:{mid}"] = ok

    # ── 9. 物理一致性分析 ──────────────────────────────
    if modules.get("physics_consistency"):
        logger.info("\n[PHASE] 物理先验一致性分析")
        # 对所有已选模型分别运行（特别是 phy-mono 系列）
        phy_models = [m for m in models if m in ("phy-mono", "phy-ineq", "data-mono-ineq")]
        # 始终也对主文模型跑一次作为基线对比
        all_phy = phy_models + [m for m in models if m not in phy_models]
        for mid in all_phy:
            ok = run_script(
                "run_physics_consistency_0404.py",
                {"MODEL_ID": mid},
                logger, dry_run,
            )
            results[f"physics_consistency:{mid}"] = ok

    # ── 10. 画图 ───────────────────────────────────────
    if modules.get("figures_main") or modules.get("figures_appendix"):
        logger.info("\n[PHASE] 自动画图")
        want_main   = modules.get("figures_main",     False)
        want_app    = modules.get("figures_appendix", False)
        if want_main and want_app:
            fig_set = "all"
        elif want_app:
            fig_set = "appendix"
        else:
            fig_set = "main"
        ok = run_script("run_figures_0404.py",
                        {"FIG_SET": fig_set},
                        logger, dry_run)
        results["figures"] = ok

    # ── 结果汇报 ───────────────────────────────────────
    logger.info("\n" + "=" * 65)
    logger.info("  运行结果汇总")
    logger.info("=" * 65)
    failed = []
    for k, v in results.items():
        status = "OK  " if v else "FAIL"
        logger.info(f"  [{status}] {k}")
        if not v:
            failed.append(k)

    if failed:
        logger.warning(f"\n失败模块: {failed}")
    else:
        logger.info("\n所有模块运行完成")

    # 保存运行记录
    run_log = {
        "run_date":    RUN_DATE,
        "run_time":    datetime.now().isoformat(),
        "preset":      RUN_CONFIG["preset"],
        "models":      models,
        "modules":     modules,
        "results":     {k: ("ok" if v else "fail") for k, v in results.items()},
        "failed":      failed,
    }
    log_path = os.path.join(EXPR_ROOT_0404, "_config",
                            f"run_record_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(run_log, f, indent=2, ensure_ascii=False)
    logger.info(f"\n运行记录保存至: {log_path}")


# ============================================================
# 快速入口说明（打印到终端）
# ============================================================
_USAGE = """
╔══════════════════════════════════════════════════════════════╗
║  HPR 0404 总控脚本 — 使用说明                                ║
╠══════════════════════════════════════════════════════════════╣
║  默认全跑主线：                                              ║
║    python run_0404.py                                        ║
║    （RUN_CONFIG["preset"] = "main" 时跑 baseline + data-mono）║
║                                                              ║
║  跑附录模型：                                                ║
║    修改 RUN_CONFIG["preset"] = "appendix"，然后运行          ║
║                                                              ║
║  只重训某个模型（不跑其他实验）：                             ║
║    修改 RUN_CONFIG["preset"] = "custom"                      ║
║    RUN_CONFIG["custom_models"] = ["phy-mono"]                ║
║    RUN_CONFIG["modules"]["train"] = True                     ║
║    （其他 modules 全设 False）                               ║
║                                                              ║
║  只重画图：                                                  ║
║    修改 modules，只开 "figures_main": True                   ║
║    其他 modules 全设 False                                   ║
║                                                              ║
║  预演（不实际运行）：                                        ║
║    RUN_CONFIG["dry_run"] = True                              ║
╚══════════════════════════════════════════════════════════════╝
"""

if __name__ == "__main__":
    if "--help" in sys.argv or "-h" in sys.argv:
        print(_USAGE)
        sys.exit(0)
    main()
