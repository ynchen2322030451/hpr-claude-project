# BNN 0414 -- 服务器端部署说明

## 目录结构

```
code/bnn0414/
  code/
    bnn_model.py               <- BayesianMLP 模型定义
    experiments_0404/
      config/                  <- 配置、注册表（experiment_config_0404, model_registry_0404）
        experiment_config_0404.py
        model_registry_0404.py
        config_server.py
        manifest_utils_0404.py
      training/                <- 训练脚本（Optuna + BNN ELBO 训练）
      evaluation/              <- 评估脚本（MC 采样推断）
      experiments/             <- 各实验脚本（risk, sensitivity, posterior, ...）
      figures/                 <- 画图脚本
        run_figures_0404.py
      SERVER_SETUP.md          <- 本文件
    plots/                     <- 辅助画图工具
    postproc/                  <- 后处理工具
  models/                      <- 训练输出：checkpoint, scaler, eval 结果
  experiments/                 <- 实验输出：risk, sensitivity, posterior
  figures/                     <- 图片输出
```

## 与 0411 (HeteroMLP) 的关键区别

1. **所有模型从头训练**：BNN 不复用 0411/0310 的 HeteroMLP checkpoint。
   旧目录 (`HPR_LEGACY_DIR`) 仅用于复用 `fixed_split` 划分和数据集路径。
2. **BNN 模型 4 个变体**（0411 有 5 个）：去掉 `phy-ineq`，合并入 `data-mono-ineq`。
3. **训练速度更慢**：BNN 由于权重采样和 KL 散度计算，训练时间约为 HeteroMLP 的 2-3 倍。
4. **推断需要 MC 采样**：评估时默认 50 次 MC forward pass（`BNN_N_MC_EVAL=50`），
   推断速度也慢于 HeteroMLP 的单次前向。

## 环境要求

```bash
# BNN 需要 CUDA 支持的 PyTorch
# GPU 显存需求比 HeteroMLP 大（权重的均值和方差各一份参数）
# 建议最低 8 GB 显存，推荐 16 GB+（用于 Optuna 并行 trial）

conda activate nn_env     # 或项目专用环境
python -c "import torch; print(torch.cuda.is_available())"  # 应输出 True
```

## 模型列表

| Model ID             | 描述                                       | Loss 组成                          |
|----------------------|--------------------------------------------|------------------------------------|
| `bnn-baseline`       | 纯 BNN 基线（ELBO only）                   | NLL + KL                           |
| `bnn-data-mono`      | BNN + 数据 Spearman 单调性                  | NLL + KL + Mono-Data               |
| `bnn-phy-mono`       | BNN + 物理先验单调性                         | NLL + KL + Mono-Phy                |
| `bnn-data-mono-ineq` | BNN + 数据单调性 + 物理不等式（全约束）       | NLL + KL + Mono-Data + Ineq        |

## 运行前配置（只需一次）

```bash
# 1. 激活 conda 环境
conda activate nn_env

# 2. 设置环境变量
export HPR_ENV=server

# 3. 指定旧代码目录（仅用于 fixed_split 和数据路径，不复用 checkpoint）
export HPR_LEGACY_DIR=/home/tjzs/Documents/fenics_data/hpr_surrogate/code/0310
#   ^ 根据实际路径修改

# 4. 进入脚本目录
cd /home/tjzs/Documents/fenics_data/hpr_surrogate/hpr-claude-project/code/bnn0414/code/experiments_0404
```

## 运行方式

### 训练单个模型

```bash
export MODEL_ID=bnn-baseline
python training/run_train_0404.py
```

### 评估（MC 采样推断）

```bash
export MODEL_ID=bnn-baseline
export EVAL_MODE=fixed    # fixed / repeat / both
python evaluation/run_eval_0404.py
```

### 训练全部 4 个模型（按顺序）

```bash
for mid in bnn-baseline bnn-data-mono bnn-phy-mono bnn-data-mono-ineq; do
    echo "=== Training $mid ==="
    MODEL_ID=$mid python training/run_train_0404.py
    MODEL_ID=$mid EVAL_MODE=fixed python evaluation/run_eval_0404.py
done
```

### 只重跑某个实验（例如 Sobol）

```bash
MODEL_ID=bnn-baseline SA_METHOD=sobol python experiments/run_sensitivity_0404.py
```

### 只重画图

```bash
FIG_SET=main python figures/run_figures_0404.py
# 或指定单张
FIG_LIST=fig1,fig5 python figures/run_figures_0404.py
```

## 各脚本对应功能

| 脚本                                          | 功能                                              |
|-----------------------------------------------|---------------------------------------------------|
| `training/run_train_0404.py`                  | BNN 训练，含 Optuna 超参搜索 + manifest 生成       |
| `evaluation/run_eval_0404.py`                 | MC 采样评估（fixed/repeat split），输出指标 CSV     |
| `experiments/run_risk_propagation_0404.py`    | D1 标称风险曲线 / D2 case 扰动 / D3 耦合分析       |
| `experiments/run_sensitivity_0404.py`         | Sobol + Spearman + PRCC                           |
| `experiments/run_posterior_0404.py`           | MCMC 参数恢复 + 可行域分析                         |
| `experiments/run_physics_consistency_0404.py` | 梯度方向一致性验证                                 |
| `experiments/run_generalization_0404.py`      | OOD 泛化评估                                      |
| `figures/run_figures_0404.py`                 | 主文 + 附录图生成（skeleton，待 BNN 结果后填充）    |

## 环境变量一览

| 变量              | 说明                                           | 默认值      |
|-------------------|------------------------------------------------|-------------|
| `HPR_ENV`         | 运行环境，`local` 或 `server`                   | `local`     |
| `HPR_LEGACY_DIR`  | 旧 code/0310/ 路径（仅复用 fixed_split 和数据） | 自动推断    |
| `MODEL_ID`        | 模型 ID（见上表）                               | 脚本内默认  |
| `EVAL_MODE`       | 评估模式（fixed / repeat / both）               | `fixed`     |
| `SA_METHOD`       | 敏感性方法（sobol / spearman / prcc / all）     | `all`       |
| `POSTERIOR_MODE`  | 后验模式（benchmark / feasible / all）          | `all`       |
| `RISK_EXP`        | 风险实验（D1 / D2 / D3 / all）                  | `all`       |
| `FIG_SET`         | 图集（main / appendix / all）                   | `all`       |
| `FIG_LIST`        | 指定图（逗号分隔，如 fig1,fig5）                 | 空 = 全部   |

## 输出位置

所有结果写入 `code/bnn0414/`（即 code/ 目录下的 BNN 分支根目录）：

```
code/bnn0414/
  models/
    bnn-baseline/
      artifacts/     <- checkpoint (.pt), scaler (.pkl), Optuna study
      fixed_eval/    <- metrics CSV, test_predictions JSON
      repeat_eval/   <- 5-seed stability
      manifests/     <- 自动生成的 manifest JSON
      logs/
    bnn-data-mono/
    bnn-phy-mono/
    bnn-data-mono-ineq/
  experiments/
    risk_propagation/
    sensitivity/
    posterior/
    physics_consistency/
    generalization/
  figures/
    fig1_bnn_accuracy.pdf / .svg / .png
    fig2_risk_comparison.pdf / ...
    ...
```

## 注意事项

- BNN checkpoint 格式与 HeteroMLP 不兼容，不能交叉加载。
- Optuna trial 数已从 HeteroMLP 的 50 减至 40（baseline/data-mono）和 30（phy-mono/data-mono-ineq），
  因为每个 trial 的训练时间更长。
- 评估时 MC 采样次数可通过 `BNN_N_MC_EVAL` 调整（默认 50），更高值更稳定但更慢。
- 后验推断中 BNN 的 MC 采样次数为 `BNN_N_MC_POSTERIOR=20`，低于评估值以保证 MCMC 效率。

## 覆盖保护机制（Output Overwrite Guard）

为避免脚本在已有结果目录上静默覆盖，`config/manifest_utils_0404.py` 提供了
`resolve_output_dir(base_dir, ...)`。所有会写产物的脚本在 `ensure_dir` 之前
先调用它来决定真实写入路径。

### 触发规则

目录被视为"已有产物"（populated）当且仅当其中出现以下任一：

- 以 `.csv / .json / .pt / .pkl / .pdf / .png / .svg` 为后缀的文件
- 名字包含 `_manifest`、`manifest.json`、`summary.csv` 的文件（哨兵）

（隐藏文件、`.log` 文件不计入。）

### 环境变量行为

| 变量              | 行为                                                                 |
|-------------------|----------------------------------------------------------------------|
| (都未设置)         | 目录非空 → 抛 `FileExistsError` 并给出提示；目录空或不存在 → 正常写入 |
| `RERUN_TAG=<tag>` | 写入 `base_dir/rerun_<tag>/`，原结果不动；打印 `[OVERWRITE-GUARD]`    |
| `FORCE=1`         | 在 `base_dir` 上直接覆盖；打印 `[OVERWRITE-GUARD] FORCE=1 强制覆盖`    |

`RERUN_TAG` 优先级高于 `FORCE`（两者同时设置时仅 `RERUN_TAG` 生效）。

### 使用示例

```bash
# 第一次跑 — OK
MODEL_ID=bnn-baseline python experiments/run_risk_propagation_0404.py

# 第二次跑相同命令 — 会被守卫拦截
MODEL_ID=bnn-baseline python experiments/run_risk_propagation_0404.py
# → FileExistsError: [OVERWRITE-GUARD] ... 已存在产物；拒绝覆盖。

# 想保留旧结果，把新跑结果写到子目录
RERUN_TAG=20260414b MODEL_ID=bnn-baseline python experiments/run_risk_propagation_0404.py
# → 写到 .../risk_propagation/bnn-baseline/rerun_20260414b/

# 确认要覆盖旧结果
FORCE=1 MODEL_ID=bnn-baseline python experiments/run_risk_propagation_0404.py
```

### 已接入守卫的脚本（10 个）

- `training/run_train_0404.py`
- `experiments/run_risk_propagation_0404.py`
- `experiments/run_sensitivity_0404.py`
- `experiments/run_posterior_0404.py`
- `experiments/run_physics_consistency_0404.py`（子目录级别）
- `experiments/run_generalization_0404.py`
- `experiments/run_lognormal_risk_postprocess.py`
- `experiments/run_risk_muonly_0410.py`
- `figures/run_figures_0404.py`
- `postproc/parse_speed_benchmark.py`

### 例外说明

- **`evaluation/run_eval_0404.py`** 未接入守卫：其内部已有幂等跳过逻辑
  （检测到 manifest 即跳过），覆盖风险低，不再叠加 guard。
- **`run_physics_consistency_0404.py`** 仅对当前 `model_id` 子目录守卫，
  其父目录（`experiments/physics_consistency/`）为多模型共享，不守卫整棵树。

### 可选：备份而非拦截

`manifest_utils_0404.backup_then_prepare(base_dir)` 会把已有产物移到
`base_dir.bak_<timestamp>/` 然后返回干净的 `base_dir`。该函数不接入环境变量，
仅在脚本显式调用时生效，适合需要保留旧结果但又不想手动改 tag 的场景。
