# manifest_utils_0404.py
# ============================================================
# Manifest 生成工具
# 所有训练/评估/实验脚本都调用这里来生成标准化的 manifest JSON
# ============================================================

import json
import os
import shutil
from datetime import datetime
from typing import Any, Optional


# ────────────────────────────────────────────────────────────
# 覆盖保护工具
# ────────────────────────────────────────────────────────────
# 使用约定（环境变量）:
#   RERUN_TAG=<str>   → 写到 <out_dir>/rerun_<tag>/ 子目录，不动原结果
#   FORCE=1           → 允许覆盖原目录（需显式声明）
#   (未设置)          → 若目录非空且含 manifest/csv/json，直接 raise
#
# 任何会写产物的脚本都应在 ensure_dir 之前先调 resolve_output_dir。

_SENTINELS = ("_manifest", "manifest.json", "summary.csv")


def _looks_populated(path: str) -> bool:
    if not os.path.isdir(path):
        return False
    try:
        names = os.listdir(path)
    except OSError:
        return False
    for n in names:
        if n.startswith(".") or n.endswith(".log"):
            continue
        low = n.lower()
        if low.endswith((".csv", ".json", ".pt", ".pkl", ".pdf", ".png", ".svg")):
            return True
        if any(s in low for s in _SENTINELS):
            return True
    return False


def resolve_output_dir(
    base_dir: str,
    *,
    rerun_tag: Optional[str] = None,
    force: Optional[bool] = None,
    script_name: str = "",
) -> str:
    """
    决定最终写入路径。
    - rerun_tag（或 env RERUN_TAG）：返回 base_dir/rerun_<tag>/
    - force（或 env FORCE=1）：返回 base_dir（允许覆盖），打印警告
    - 否则：若 base_dir 已有产物，raise FileExistsError；否则返回 base_dir
    """
    if rerun_tag is None:
        rerun_tag = os.environ.get("RERUN_TAG", "").strip() or None
    if force is None:
        force = os.environ.get("FORCE", "").strip() in ("1", "true", "yes")

    if rerun_tag:
        out = os.path.join(base_dir, f"rerun_{rerun_tag}")
        os.makedirs(out, exist_ok=True)
        print(f"[OVERWRITE-GUARD] {script_name or '?'}: RERUN_TAG={rerun_tag} → {out}")
        return out

    populated = _looks_populated(base_dir)
    if populated and not force:
        raise FileExistsError(
            f"[OVERWRITE-GUARD] {base_dir} 已存在产物；拒绝覆盖。\n"
            f"  • 要保留旧结果并追加新跑：  export RERUN_TAG=<tag>\n"
            f"  • 要显式覆盖：              export FORCE=1\n"
            f"  • 或手动移走/删除该目录。"
        )
    if populated and force:
        print(f"[OVERWRITE-GUARD] {script_name or '?'}: FORCE=1 强制覆盖 {base_dir}")

    os.makedirs(base_dir, exist_ok=True)
    return base_dir


def backup_then_prepare(base_dir: str, script_name: str = "") -> str:
    """
    可选：把已有产物移到 base_dir.bak_<ts>/，然后返回干净的 base_dir。
    仅在显式调用时使用（不接入 env）。
    """
    if _looks_populated(base_dir):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        bak = f"{base_dir}.bak_{ts}"
        shutil.move(base_dir, bak)
        print(f"[OVERWRITE-GUARD] {script_name or '?'}: backed up → {bak}")
    os.makedirs(base_dir, exist_ok=True)
    return base_dir


def _safe(v: Any) -> Any:
    """确保值可以 JSON 序列化。"""
    if isinstance(v, (int, float, str, bool, type(None))):
        return v
    if isinstance(v, dict):
        return {k: _safe(vv) for k, vv in v.items()}
    if isinstance(v, (list, tuple)):
        return [_safe(x) for x in v]
    return str(v)


def write_manifest(path: str, data: dict):
    """写 manifest JSON，自动添加生成时间。"""
    data = dict(data)
    data["_manifest_generated_at"] = datetime.now().isoformat()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(_safe(data), f, indent=2, ensure_ascii=False)
    print(f"[MANIFEST] {path}")
    return path


def make_training_manifest(
    model_id: str,
    full_name: str,
    loss_components: list,
    n_outputs: int,
    split_type: str,           # "fixed" or "repeat_N"
    split_seed: int,
    n_train: int,
    n_val: int,
    n_test: int,
    best_params: dict,
    best_val_nll: float,
    training_time_sec: float,
    ckpt_path: str,
    scaler_path: str,
    split_source: str,
    optuna_trials: int,
    source_script: str,
    artifact_origin: str = "trained_in_bnn0414",
    extra: dict = None,
) -> dict:
    """构建训练 manifest 字典。"""
    m = {
        "manifest_type":             "training",
        "model_id":                  model_id,
        "full_name":                 full_name,
        "artifact_origin":           artifact_origin,
        "training_protocol":         "bnn0414_fixed",
        "output_definition_version": "15col_v1",
        "loss_components":           loss_components,
        "n_outputs":                 n_outputs,
        "split_type":                split_type,
        "split_seed":                split_seed,
        "n_train":                   n_train,
        "n_val":                     n_val,
        "n_test":                    n_test,
        "best_params":               best_params,
        "best_val_nll":              float(best_val_nll),
        "training_time_sec":         float(training_time_sec),
        "checkpoint_path":           ckpt_path,
        "scaler_path":               scaler_path,
        "split_source":              split_source,
        "optuna_trials":             optuna_trials,
        "source_script":             source_script,
    }
    if extra:
        m.update(extra)
    return m


def make_eval_manifest(
    model_id: str,
    split_type: str,
    split_seed: int,
    metrics_overall: dict,
    metrics_per_output: list,
    ckpt_path: str,
    scaler_path: str,
    source_script: str,
    artifact_origin: str = "trained_in_bnn0414",
    inference_method: str = "mc_sampling",
    column_alignment_verified: bool = False,
    n_test: int = None,
    extra: dict = None,
) -> dict:
    """构建评估 manifest 字典。"""
    m = {
        "manifest_type":                "evaluation",
        "model_id":                     model_id,
        "artifact_origin":              artifact_origin,
        "training_protocol":            "bnn0414_fixed",
        "output_definition_version":    "15col_v1",
        "inference_method":             inference_method,
        "column_alignment_verified":    column_alignment_verified,
        "split_type":                   split_type,
        "split_seed":                   split_seed,
        "n_test":                       n_test,
        "metrics_overall":              metrics_overall,
        "metrics_per_output":           metrics_per_output,
        "checkpoint_path":              ckpt_path,
        "scaler_path":                  scaler_path,
        "source_script":                source_script,
    }
    if extra:
        m.update(extra)
    return m


def make_experiment_manifest(
    experiment_id: str,
    model_id: str,
    input_source: str,
    outputs_saved: list,
    key_results: dict,
    source_script: str,
    extra: dict = None,
) -> dict:
    m = {
        "manifest_type":  "experiment",
        "experiment_id":  experiment_id,
        "model_id":       model_id,
        "input_source":   input_source,
        "outputs_saved":  outputs_saved,
        "key_results":    key_results,
        "source_script":  source_script,
    }
    if extra:
        m.update(extra)
    return m
