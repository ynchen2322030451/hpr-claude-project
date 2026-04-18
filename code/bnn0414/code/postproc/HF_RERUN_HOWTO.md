# BNN Posterior HF Rerun — 服务器操作手册

## 目的

在 BNN 后验推断得到的参数点上重新跑 OpenMC+FEniCS 高保真仿真，验证代理后验对真实物理响应的校准质量。对应论文 §2.5。

## 产出 54 个 HF runs 的来历

- **18 cases**：从 `fixed_split/test.csv`（435 行冻结测试集）按真值 `iteration2_max_global_stress` 三档分层（low / near / high），每档 6 例。来源 `experiment_config_0404.py` 的 `INVERSE_N_BENCHMARK = 20`，代码里 `// 3` 截到 18。
- **3 labels per case**：对每例在其后验上取三档代表点：
  - `post_mean`  — 后验均值，点估计校准
  - `post_lo_5`  — 每维后验边际 5% 分位，低端 envelope
  - `post_hi_95` — 每维后验边际 95% 分位，高端 envelope
- **Caveat**：`post_lo_5 / post_hi_95` 是**边际**分位点，不是联合 90% tail；作为保守 envelope 使用。

```
18 (cases)  ×  3 (labels)  =  54 HF runs
```

## 先决条件

1. `run_0404.py` 已跑完，`experiments/posterior/<model_id>/` 下有：
   - `benchmark_summary.csv`
   - `benchmark_case_meta.json`
2. `generater.py` 在以下位置之一（脚本会自动找）：
   - `/home/tjzs/Documents/fenics_data/hpr_surrogate/hpr-claude-project/code/generater.py`
   - `/home/tjzs/Documents/fenics_data/fenics_data/generater.py`
3. Conda 环境 `pytorch-env`（或你习惯的 HF 环境，能 `import generater`）

## 文件位置

```
bnn0414/code/postproc/
├── build_bnn_hf_rerun_manifest.py    # 读 posterior 产物，写输入 CSV
├── run_posterior_hf_rerun_0404.py    # 跑 HF、归档、对比、resume
└── HF_RERUN_HOWTO.md                 # 本文
```

## 运行流程

### 第一步：造 HF 输入 CSV

```bash
cd /home/tjzs/Documents/fenics_data/hpr_surrogate/hpr-claude-project/code/bnn0414/code/postproc

# 默认：18 cases × 3 labels = 54 行
python build_bnn_hf_rerun_manifest.py --model bnn-phy-mono
```

输出：
```
bnn0414/code/experiments/posterior/bnn-phy-mono/hf_rerun/
├── posterior_hf_rerun_inputs.csv        # 54 行，theta9 + y_true + label
└── posterior_hf_rerun_manifest.json     # 说明 + caveat
```

**快速闭环模式**（只跑 18 点 post_mean，先打通管线）：
```bash
python build_bnn_hf_rerun_manifest.py --model bnn-phy-mono --labels post_mean
```

**换模型**（主文 / 附录分别跑一次）：
```bash
python build_bnn_hf_rerun_manifest.py --model bnn-data-mono-ineq
python build_bnn_hf_rerun_manifest.py --model bnn-baseline
```

### 第二步：dry-run 检查

```bash
MODEL_ID=bnn-phy-mono python run_posterior_hf_rerun_0404.py --dry-run --limit 3
```

会打印每例的 θ9 但不调用 HF。确认列名正确、数值合理。

### 第三步：正式跑 HF

**前台跑**（看着跑，CTRL-C 可中断，再起同一条命令会续跑）：
```bash
MODEL_ID=bnn-phy-mono python run_posterior_hf_rerun_0404.py
```

**后台跑**（推荐；HF 一例几分钟~几十分钟，54 例可能跑几个小时）：
```bash
nohup env MODEL_ID=bnn-phy-mono python -u run_posterior_hf_rerun_0404.py \
    > hf_rerun_phy-mono.log 2>&1 &
echo $! > hf_rerun_phy-mono.pid
tail -f hf_rerun_phy-mono.log
```

或用 `screen` / `tmux`：
```bash
screen -S hf
MODEL_ID=bnn-phy-mono python run_posterior_hf_rerun_0404.py
# Ctrl-A D 脱离；screen -r hf 重连
```

### 第四步：中断后续跑

直接再跑同一条命令即可，`progress.csv` 会让脚本跳过已成功的 (case, label)：
```bash
MODEL_ID=bnn-phy-mono python run_posterior_hf_rerun_0404.py
```

如果想强制重跑某几例，删掉 `progress.csv` 里对应行，或 `--no-skip-existing`。

## 输出布局

```
bnn0414/code/experiments/posterior/<model_id>/hf_rerun/results/
├── posterior_hf_rerun_summary.csv       # 每 (case_i, label) 一行；y_true / y_hf / abs_err / rel_err
├── posterior_hf_rerun_per_output.csv    # 长格式，全 15 个 output
├── posterior_hf_rerun_meta.json         # 运行元数据 + 起止时间 + 总耗时
├── progress.csv                         # 每例完成状态（resume 用）
└── archive/case<ci>_<label>/            # 每例 HF 原始产物归档（fenics_results.json + 日志）
```

## 常用 CLI 参数

### `build_bnn_hf_rerun_manifest.py`

| 参数 | 作用 | 默认 |
|---|---|---|
| `--model` | BNN 模型 id | 必填 |
| `--labels` | 要发的 label 子集，从 `{post_mean, post_lo_5, post_hi_95}` 选 | 全部三个 |
| `--posterior-dir` | 指定 posterior 目录（默认自动找） | 自动 |
| `--test-csv` | 指定 test.csv（默认自动找 0310/fixed_split/test.csv） | 自动 |
| `--out` | 指定输出 CSV 路径 | `hf_rerun/posterior_hf_rerun_inputs.csv` |

### `run_posterior_hf_rerun_0404.py`

| 参数 | 作用 | 默认 |
|---|---|---|
| `--input` | 输入 CSV 路径 | 根据 `MODEL_ID` 推断 |
| `--out-dir` | 输出目录 | `dirname(input)/results` |
| `--model-id` / `$MODEL_ID` | BNN 模型 id | 无默认 |
| `--dry-run` | 不调用 HF，打印计划 | 关 |
| `--limit N` | 只跑前 N 行（smoke test） | 0（全跑） |
| `--skip-existing` | 从 `progress.csv` 跳过已成功 | 开（默认） |
| `--no-skip-existing` | 关闭 skip | 关 |

## 扩容（想更多 HF 样本）

**场景 A：只扩 label，不动 case**  
默认就是 3 label。想加 joint 联合样本需先改 `run_posterior_0404.py` 落盘 MCMC chain，再给 manifest builder 加 `--joint-samples K`（后续版本，暂未实现）。

**场景 B：扩 case 数**  
改 `experiment_config_0404.py` 的 `INVERSE_N_BENCHMARK = 20 → 30`，然后重跑 posterior（MCMC 便宜）：
```bash
# 在 bnn0414/code/experiments_0404/
# 打开 run_0404.py，只开 posterior_inference
python run_0404.py
```
posterior 会产出 30 cases × 3 labels = 90 HF runs。

**场景 C：降载**  
只要 post_mean：
```bash
python build_bnn_hf_rerun_manifest.py --model bnn-phy-mono --labels post_mean
# 18 HF runs
```

## 故障排查

| 症状 | 原因 | 处置 |
|---|---|---|
| `ModuleNotFoundError: generater` | 脚本没找到 generater.py | 检查两个候选路径；或手动 `export PYTHONPATH=/home/tjzs/Documents/fenics_data/fenics_data:$PYTHONPATH` |
| `benchmark_summary.csv not found` | posterior 还没跑 / 路径错 | `ls .../experiments/posterior/<model_id>/`；否则 `--posterior-dir` 手动指 |
| `theta9_post__SS316_scale` 不合理 | 默认 1.0 nominal，不是真实训练值 | 如果你的 HF 管线要别的值，改 manifest builder 的 `SS316_SCALE_NOMINAL` |
| 某例 FAIL（non-convergence 等） | HF 在这组 θ 下物理不稳定 | `progress.csv` 会记录 fail 和错误摘要；下次不会重试 fail 的，可 `--no-skip-existing` 强制重试 |
| 整个 batch 中断 | 服务器重启 / OOM / SSH 掉线 | 直接再起同一条命令即可 resume |

## 本次设计的主要改动（相对旧 0310 版）

1. `__file__`-relative 路径（不再硬编码 `/home/tjzs/Documents/0310`）
2. `generater.py` 两处 fallback 自动搜
3. 支持多 `label`（每 case 3 个 HF runs）
4. 9 维 `MATERIAL_KEYS` 显式 nominal `SS316_scale = 1.0`
5. 非标定 4 参从 test 真值取（偏差完全归因于标定的 4 参）
6. `progress.csv` resume
7. 逐例 try/except 错误隔离
8. 5 个 primary output 全部记录
9. 每例实时 flush summary + ETA
