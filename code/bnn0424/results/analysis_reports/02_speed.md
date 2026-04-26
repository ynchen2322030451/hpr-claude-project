# 02 — Computational speedup

源文件：`experiments/computational_speedup/bnn-baseline/bnn_speed_benchmark.json` + `manifest.json`。
**仅 bnn-baseline** 运行了该实验（_config 约定 speed benchmark 只跑一个代表模型即可，BNN 架构相同）。
设备：CUDA；n_mc_eval=50；n_warmup=30；n_repeat_single=200；batch_size=1024。

## 关键数值

| 指标 | 值 |
|---|---|
| single-sample MC（50 samples） latency | 1.29×10⁻² s |
| single-sample deterministic latency | 6.81×10⁻⁵ s |
| batch（1024）per-sample latency | 1.34×10⁻⁵ s |
| batch throughput | 7.47×10⁴ samples/s |
| HF reference per case (3-run benchmark) | **2.27×10³ s** (= 2266 s, AMD EPYC 9654) |
| HF reference per case (54-case rerun mean) | 2.36×10³ s (= 2357 s, same hardware) |
| **speedup, single-sample MC vs HF** (@ 2266 s) | **1.76×10⁵** |
| speedup, single-sample det vs HF | 3.33×10⁷ |
| speedup, batch/sample vs HF | 1.69×10⁸ |

## 解读与写作建议
- **正文应引用** single-sample MC 加速（2.8×10⁵），这是实际 UQ 推理代价，下述其余两项作为补充。deterministic 加速假设零 MC 样本，与不确定性量化场景不符。
- HF 单次耗时已更新：3-run dedicated benchmark 均值 2266 s（std 1.34 s），54-case HF rerun 均值 2357 s（std 297 s）。`bnn_speed_benchmark.json` 仍保留旧 3600 s 占位（canonical artifact 不修改），但 `budget_matched_manifest.json` 和论文正文均使用 2266 s。
- 输入为合成随机张量（非真实测试集），仅测时间，不影响 FLOP 估计。

## 可进入正文的一句话
> "A single 50-sample Monte Carlo predictive draw of the BNN surrogate completes in 12.9 ms on a single GPU, yielding a ~1.76×10⁵ speedup over the FEniCS high-fidelity coupled-physics evaluation (2266 s per case, AMD EPYC 9654)."
