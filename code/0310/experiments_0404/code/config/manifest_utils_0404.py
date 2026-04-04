# manifest_utils_0404.py
# ============================================================
# Manifest 生成工具
# 所有训练/评估/实验脚本都调用这里来生成标准化的 manifest JSON
# ============================================================

import json
import os
from datetime import datetime
from typing import Any


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
    extra: dict = None,
) -> dict:
    """构建训练 manifest 字典。"""
    m = {
        "manifest_type":    "training",
        "model_id":         model_id,
        "full_name":        full_name,
        "loss_components":  loss_components,
        "n_outputs":        n_outputs,
        "split_type":       split_type,
        "split_seed":       split_seed,
        "n_train":          n_train,
        "n_val":            n_val,
        "n_test":           n_test,
        "best_params":      best_params,
        "best_val_nll":     float(best_val_nll),
        "training_time_sec": float(training_time_sec),
        "checkpoint_path":  ckpt_path,
        "scaler_path":      scaler_path,
        "split_source":     split_source,
        "optuna_trials":    optuna_trials,
        "source_script":    source_script,
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
    extra: dict = None,
) -> dict:
    m = {
        "manifest_type":    "evaluation",
        "model_id":         model_id,
        "split_type":       split_type,
        "split_seed":       split_seed,
        "metrics_overall":  metrics_overall,
        "metrics_per_output": metrics_per_output,
        "checkpoint_path":  ckpt_path,
        "scaler_path":      scaler_path,
        "source_script":    source_script,
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
