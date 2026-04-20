# run_speed_0404.py
# ============================================================
# BNN 0414 — 计算速度基准
#
# 测量内容：
#   - single-sample MC 推断延迟（N_MC_EVAL 次权重采样后取均值）
#   - single-sample deterministic（sample=False）延迟
#   - batch throughput（batch × MC 次数）
#   - 与 high-fidelity (openmc+FEniCS) 单次模拟时间的加速比
#
# 用法：
#   MODEL_ID=bnn-baseline python run_speed_0404.py
#
# 输出：
#   <EXPR_ROOT_0404>/experiments/computational_speedup/<model_id>/
#     bnn_speed_benchmark.json
#     manifest.json
# ============================================================

import os
import sys
import json
import time
import pickle

import numpy as np
import torch

_THIS = os.path.dirname(os.path.abspath(__file__))
_EXPR_DIR = os.path.dirname(_THIS)
sys.path.insert(0, _EXPR_DIR)
from _path_setup import setup_paths
setup_paths()

from experiment_config_0404 import (
    EXPR_ROOT_0404,
    INPUT_COLS,
    OUTPUT_COLS,
    SEED,
    BNN_N_MC_EVAL,
    model_artifacts_dir,
    experiment_dir,
    ensure_dir,
)
from model_registry_0404 import MODELS
from manifest_utils_0404 import (
    resolve_output_dir,
    write_manifest,
    make_experiment_manifest,
)
from bnn_model import BayesianMLP
from bnn_multifidelity import (
    MultiFidelityBNN_Stacked, MultiFidelityBNN_Residual,
    MultiFidelityBNN_Hybrid,
)

# ────────────────────────────────────────────────────────────
# 参考 HF 时间（秒/case）
#
# ⚠️ TODO / PLACEHOLDER — 待 BNN 分支的真实 HF 基准统计完成后替换。
#
# - 当前值 3600.0 s 仅作为快速估算占位，延续 0310/0411 早期脚本；
# - canonical_values.json 已将 3600 s 列入 retired_numbers，
#   论文 §3.4 正式数字为 2266 s（0411 HeteroMLP HF 基准）；
# - 真实基准应从 results/speed/paper_speed_benchmark_detailed.json
#   读取，由 postproc/parse_speed_benchmark.py 解析后写入
#   hf_runtime_final.json；本脚本读取 JSON 后再计算 speedup；
# - 若 BNN 分支重新在同一硬件上统计 HF 时间，得到新数字后
#   （1）更新下方常量 或 （2）改为从 JSON 读取（推荐），
#       并同步修改 canonical_values.json 与论文 §3.4。
# ────────────────────────────────────────────────────────────
HIGH_FIDELITY_SECONDS_PER_CASE = 2266.0   # 0411 HeteroMLP canonical HF baseline (same hardware, same HF pipeline); no re-measurement needed for the BNN branch

# 基准参数
N_WARMUP        = 30
N_REPEAT_SINGLE = 200     # BNN 每次要跑 MC 次前向，节奏比 HeteroMLP 慢
N_REPEAT_BATCH  = 50
BATCH_SIZE      = 1024


def get_device():
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def sync_if_needed(device):
    if device.type == "cuda":
        torch.cuda.synchronize()


def load_bnn(model_id: str, device):
    art_dir = model_artifacts_dir(model_id)
    ckpt_path   = os.path.join(art_dir, f"checkpoint_{model_id}_fixed.pt")
    scaler_path = os.path.join(art_dir, f"scalers_{model_id}_fixed.pkl")
    if not os.path.exists(ckpt_path):
        raise FileNotFoundError(f"Missing checkpoint: {ckpt_path}")
    if not os.path.exists(scaler_path):
        raise FileNotFoundError(f"Missing scaler: {scaler_path}")

    ckpt = torch.load(ckpt_path, map_location=device)
    bp = ckpt["best_params"]
    cls_name = ckpt.get("model_class", "BayesianMLP")

    if cls_name == "MultiFidelityBNN_Stacked":
        from experiment_config_0404 import OUT1, OUT2
        model = MultiFidelityBNN_Stacked(
            in_dim=len(INPUT_COLS),
            n_iter1=len(OUT1), n_iter2=len(OUT2),
            width1=int(bp["width1"]), depth1=int(bp["depth1"]),
            width2=int(bp["width2"]), depth2=int(bp["depth2"]),
            prior_sigma=float(bp.get("prior_sigma", 1.0)),
        ).to(device)
    elif cls_name == "MultiFidelityBNN_Residual":
        from experiment_config_0404 import OUT1
        model = MultiFidelityBNN_Residual(
            in_dim=len(INPUT_COLS),
            n_iter1=len(OUT1),
            width1=int(bp["width1"]), depth1=int(bp["depth1"]),
            width_delta=int(bp["width2"]), depth_delta=int(bp["depth2"]),
            prior_sigma=float(bp.get("prior_sigma", 1.0)),
        ).to(device)
    elif cls_name == "MultiFidelityBNN_Hybrid":
        from experiment_config_0404 import OUT1
        model = MultiFidelityBNN_Hybrid(
            in_dim=len(INPUT_COLS),
            n_iter1=len(OUT1),
            width1=int(bp["width1"]), depth1=int(bp["depth1"]),
            width_delta=int(bp.get("width2", 64)),
            depth_delta=int(bp.get("depth2", 2)),
            width_direct=int(bp["width2"]), depth_direct=int(bp["depth2"]),
            prior_sigma=float(bp.get("prior_sigma", 1.0)),
        ).to(device)
    else:
        model = BayesianMLP(
            in_dim=len(INPUT_COLS),
            out_dim=len(OUTPUT_COLS),
            width=int(bp["width"]),
            depth=int(bp["depth"]),
            prior_sigma=float(bp.get("prior_sigma", 1.0)),
            homoscedastic=ckpt.get("homoscedastic", False),
        ).to(device)

    model.load_state_dict(ckpt["model_state_dict"], strict=False)
    model.eval()

    with open(scaler_path, "rb") as f:
        sc = pickle.load(f)

    if "mf_output_order" in sc:
        mf_order = sc["mf_output_order"]
        perm = np.array([mf_order.index(c) for c in OUTPUT_COLS])
        model._mf_to_canonical = perm

    return model, sc["sx"], sc["sy"], ckpt_path, scaler_path, ckpt


@torch.no_grad()
def mc_forward(model, x, n_mc: int, sample: bool):
    """N_MC 次前向，取 mu 的平均。返回一次完整推断耗时的代表结果。"""
    mus = []
    for _ in range(n_mc):
        mu, _ = model(x, sample=sample)
        mus.append(mu)
    return torch.stack(mus, dim=0).mean(dim=0)


def bench_single(model, x_single, device, n_mc: int):
    # warmup
    with torch.no_grad():
        for _ in range(N_WARMUP):
            _ = mc_forward(model, x_single, n_mc=max(1, n_mc // 10), sample=True)
    sync_if_needed(device)

    t0 = time.perf_counter()
    with torch.no_grad():
        for _ in range(N_REPEAT_SINGLE):
            _ = mc_forward(model, x_single, n_mc=n_mc, sample=True)
    sync_if_needed(device)
    t1 = time.perf_counter()
    return (t1 - t0) / N_REPEAT_SINGLE


def bench_single_deterministic(model, x_single, device):
    # warmup
    with torch.no_grad():
        for _ in range(N_WARMUP):
            mu, _ = model(x_single, sample=False)
    sync_if_needed(device)

    t0 = time.perf_counter()
    with torch.no_grad():
        for _ in range(N_REPEAT_SINGLE):
            mu, _ = model(x_single, sample=False)
    sync_if_needed(device)
    t1 = time.perf_counter()
    return (t1 - t0) / N_REPEAT_SINGLE


def bench_batch(model, x_batch, device, n_mc: int):
    # warmup
    with torch.no_grad():
        for _ in range(N_WARMUP // 2):
            _ = mc_forward(model, x_batch, n_mc=max(1, n_mc // 10), sample=True)
    sync_if_needed(device)

    t0 = time.perf_counter()
    with torch.no_grad():
        for _ in range(N_REPEAT_BATCH):
            _ = mc_forward(model, x_batch, n_mc=n_mc, sample=True)
    sync_if_needed(device)
    t1 = time.perf_counter()
    return (t1 - t0) / N_REPEAT_BATCH


def main():
    model_id = os.environ.get("MODEL_ID", "bnn-baseline")
    if model_id not in MODELS:
        raise KeyError(f"Unknown MODEL_ID={model_id!r}. Choices: {list(MODELS)}")

    np.random.seed(SEED)
    torch.manual_seed(SEED)

    device = get_device()
    print(f"[speed] MODEL_ID={model_id}  device={device}  N_MC_EVAL={BNN_N_MC_EVAL}")

    model, sx, sy, ckpt_path, scaler_path, ckpt = load_bnn(model_id, device)

    # 输出目录（含 overwrite guard）
    base_out = os.path.join(experiment_dir("computational_speedup"), model_id)
    out_dir = resolve_output_dir(base_out, script_name=os.path.basename(__file__))

    x_single = torch.randn(1, len(INPUT_COLS), dtype=torch.float32, device=device)
    x_batch  = torch.randn(BATCH_SIZE, len(INPUT_COLS), dtype=torch.float32, device=device)

    # 三种延迟
    single_mc    = bench_single(model, x_single, device, n_mc=BNN_N_MC_EVAL)
    single_det   = bench_single_deterministic(model, x_single, device)
    batch_time   = bench_batch(model, x_batch, device, n_mc=BNN_N_MC_EVAL)
    per_sample_b = batch_time / BATCH_SIZE
    throughput   = BATCH_SIZE / batch_time

    result = {
        "model_id":                          model_id,
        "device":                            str(device),
        "n_mc_eval":                         int(BNN_N_MC_EVAL),
        "n_warmup":                          N_WARMUP,
        "n_repeat_single":                   N_REPEAT_SINGLE,
        "n_repeat_batch":                    N_REPEAT_BATCH,
        "batch_size":                        BATCH_SIZE,
        "single_sample_latency_sec":         float(single_mc),
        "single_sample_deterministic_sec":   float(single_det),
        "batch_time_sec":                    float(batch_time),
        "per_sample_batch_latency_sec":      float(per_sample_b),
        "batch_throughput_samples_per_sec":  float(throughput),
        "high_fidelity_seconds_per_case":    HIGH_FIDELITY_SECONDS_PER_CASE,
        "speedup_single_mc_vs_hf":           float(HIGH_FIDELITY_SECONDS_PER_CASE / single_mc),
        "speedup_single_det_vs_hf":          float(HIGH_FIDELITY_SECONDS_PER_CASE / single_det),
        "speedup_batch_per_sample_vs_hf":    float(HIGH_FIDELITY_SECONDS_PER_CASE / per_sample_b),
        "checkpoint_path":                   ckpt_path,
        "scaler_path":                       scaler_path,
    }

    out_json = os.path.join(out_dir, "bnn_speed_benchmark.json")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"[speed] wrote {out_json}")

    # manifest
    mfst = make_experiment_manifest(
        experiment_id="computational_speedup",
        model_id=model_id,
        input_source="synthetic random tensors",
        outputs_saved=["bnn_speed_benchmark.json"],
        key_results={
            "single_sample_latency_sec":        result["single_sample_latency_sec"],
            "per_sample_batch_latency_sec":     result["per_sample_batch_latency_sec"],
            "speedup_batch_per_sample_vs_hf":   result["speedup_batch_per_sample_vs_hf"],
        },
        source_script=os.path.basename(__file__),
        extra={
            "n_mc_eval":                     int(BNN_N_MC_EVAL),
            "high_fidelity_seconds_per_case": HIGH_FIDELITY_SECONDS_PER_CASE,
            "device":                         str(device),
        },
    )
    write_manifest(os.path.join(out_dir, "manifest.json"), mfst)

    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
