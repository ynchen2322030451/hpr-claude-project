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
    artifact_origin: str = "trained_in_0404",   # "trained_in_0404" | "reused_legacy"
    extra: dict = None,
) -> dict:
    """构建训练 manifest 字典。

    artifact_origin 说明：
      "trained_in_0404"  — 在 0404 框架下从头训练的模型
      "reused_legacy"    — 直接复用 experiments_phys_levels/ 旧 checkpoint，未重训
    """
    m = {
        "manifest_type":             "training",
        "model_id":                  model_id,
        "full_name":                 full_name,
        "artifact_origin":           artifact_origin,
        "training_protocol":         "0404_fixed" if artifact_origin == "trained_in_0404" else "legacy_fixed",
        "output_definition_version": "15col_v1",   # 15 输出，无 iter1_keff
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
    artifact_origin: str = "trained_in_0404",   # "trained_in_0404" | "reused_legacy"
    inference_method: str = "rerun_inference",   # "saved_predictions" | "rerun_inference"
    column_alignment_verified: bool = False,
    n_test: int = None,
    extra: dict = None,
) -> dict:
    """构建评估 manifest 字典。

    inference_method 说明：
      "saved_predictions"  — 直接读取训练时保存的 test_predictions JSON，列对齐有保证
      "rerun_inference"    — 重新加载模型推断，需要 column_alignment_verified=True 才可信

    ⚠️  column_alignment_verified=False 且 inference_method="rerun_inference" 时，
       结果应标注为不可信（参考 RESULT_LINEAGE_AUDIT.md §1.1）。
    """
    m = {
        "manifest_type":                "evaluation",
        "model_id":                     model_id,
        "artifact_origin":              artifact_origin,
        "training_protocol":            "0404_fixed" if artifact_origin == "trained_in_0404" else "legacy_fixed",
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
