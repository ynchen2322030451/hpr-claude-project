# 服务器端部署说明

## 目录说明

```
experiments_0404/
  code/                    ← 本目录（所有 0404 脚本的服务器端版本）
    config/                ← 配置、注册表、工具函数
    training/              ← 训练脚本
    evaluation/            ← 评估脚本
    experiments/           ← 各实验脚本（risk, sensitivity, posterior, ...）
    figures/               ← 画图脚本（待补充）
    run_0404.py            ← 总控入口
    SERVER_SETUP.md        ← 本文件
```

## 运行前配置（只需一次）

```bash
# 1. 激活 conda 环境
conda activate nn_env

# 2. 设置环境变量
export HPR_ENV=server

# 3. 指定旧代码目录（baseline/data-mono checkpoint 在那里）
export HPR_LEGACY_DIR=/home/tjzs/Documents/fenics_data/hpr_surrogate/code/0310
#   ↑ 根据实际路径修改

# 4. 进入本目录
cd /path/to/experiments_0404/code
```

## 运行方式

### 默认全跑主线（baseline + data-mono）

```bash
# 先设置好环境变量（见上），然后：
python run_0404.py
```

### 只训练 phy-mono（新模型）

打开 `run_0404.py`，修改顶部 `RUN_CONFIG`：
```python
RUN_CONFIG = {
    "preset": "custom",
    "custom_models": ["phy-mono"],
    "modules": {
        "train": True,
        "eval_fixed": True,
        # 其他全设 False
    },
    ...
}
```
然后运行 `python run_0404.py`

### 只重跑某个实验（例如 Sobol）

```bash
MODEL_ID=baseline SA_METHOD=sobol python experiments/run_sensitivity_0404.py
```

### 只重画图

打开 `run_0404.py`，设置：
```python
RUN_CONFIG = {
    "preset": "custom",
    "custom_models": ["baseline", "data-mono"],
    "modules": {
        "figures_main": True,
        # 其他全设 False
    }
}
```

## 各脚本对应功能

| 脚本 | 功能 |
|------|------|
| `training/run_train_0404.py` | 训练 5 个模型，含 Optuna + manifest |
| `evaluation/run_eval_0404.py` | fixed/repeat split 评估，输出指标 CSV |
| `experiments/run_risk_propagation_0404.py` | D1 标称风险曲线 / D2 case 扰动 / D3 耦合分析 |
| `experiments/run_sensitivity_0404.py` | Sobol + Spearman + PRCC |
| `experiments/run_posterior_0404.py` | MCMC 参数恢复 + 可行域分析 |
| `experiments/run_physics_consistency_0404.py` | 梯度方向一致性验证 |
| `experiments/run_generalization_0404.py` | OOD 泛化评估（4个特征） |

## 环境变量一览

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `HPR_ENV` | 运行环境，`local` 或 `server` | `local` |
| `HPR_LEGACY_DIR` | 旧 code/0310/ 路径（用于找 checkpoint 和共享工具） | 自动推断 |
| `MODEL_ID` | 各子脚本的模型 ID | 脚本内 `_OVERRIDE` 变量 |
| `EVAL_MODE` | eval 脚本的模式（fixed/repeat/both） | `fixed` |
| `SA_METHOD` | 敏感性方法（sobol/spearman/prcc/all） | `all` |
| `POSTERIOR_MODE` | 后验模式（benchmark/feasible/all） | `all` |
| `RISK_EXP` | 风险实验（D1/D2/D3/all） | `all` |

## 输出位置

所有结果写入 `experiments_0404/`（即本 code/ 目录的父目录）：
```
experiments_0404/
  models/
    baseline/
      artifacts/    ← checkpoint, scaler
      fixed_eval/   ← metrics, predictions
      repeat_eval/  ← 5-seed stability
      manifests/    ← 自动生成的 manifest JSON
      logs/
    data-mono/
    phy-mono/
    ...
  experiments/
    risk_propagation/
    sensitivity/
    posterior/
    physics_consistency/
    generalization/
```
