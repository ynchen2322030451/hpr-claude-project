# BNN v4 手稿决策备忘
# =====================================================================
# 对应 draft_paper_0414_v4.txt 末尾 DECISION LOG 的逐条答复。
# 依据：
#   - code/bnn0414/code/bnn_model.py
#   - code/bnn0414/code/experiments_0404/config/model_registry_0404.py
#   - code/bnn0414/code/experiments_0404/training/run_train_0404.py
#   - code/bnn0414/code/experiments_0404/experiments/run_speed_0404.py
#   - code/0411 canonical 结果（未完成前作为基线参考）
# =====================================================================

---

## D1. BNN 近似推断方法 → 已定：**MFVI / Bayes-by-Backprop**

依据 `bnn_model.py` 第 1–28、71–120 行：

- `BayesianLinear` 层采用 **mean-field Gaussian** 变分后验
  `q(w) = N(μ, softplus(ρ)²)`；
- 权重先验为 **各向同性高斯** `p(w) = N(0, prior_sigma²)`，`prior_sigma`
  默认 1.0，可经 Optuna 搜索；
- 训练使用 **ELBO + reparameterization trick**，KL 闭式；
- 参考 Blundell et al. 2015（已写入草稿参考文献 [10]）。

**正文落实**：§4.3 "Inference scheme" 段已按此写就。【待拍板】标签删除。

---

## D2. BNN 先验形式 → 已定：**isotropic Gaussian，σ_p 作 Optuna 超参**

直接由 `BayesianLinear.prior_sigma` 实现。不引入 layer-wise 或
horseshoe，理由：

- 8 维输入、15 维输出、总参数规模小（数十–数百 k），各向同性先验已
  足够；
- 与 0411 HeteroMLP 的 weight-decay 1e-8–1e-3 先验等价区间保持
  可比性；
- 减少审稿人质疑先验敏感性的攻击面。

**正文落实**：§4.3 已写 "isotropic Gaussian N(0, σ²_p I)"。【待拍板】
标签删除。

---

## D3. 是否保留物理约束（单调性+不等式） → **强烈建议保留**，主模型选 `bnn-data-mono-ineq`

### 3.1 现状
`model_registry_0404.py` 已定义 4 个 BNN 变体：

| short_id              | ELBO | Spearman mono | Physics mono | Inequality | 对应 0411 变体        |
|-----------------------|:----:|:-------------:|:------------:|:----------:|----------------------|
| bnn-baseline          | ✓    |               |              |            | baseline             |
| bnn-data-mono         | ✓    | ✓             |              |            | data-mono            |
| bnn-phy-mono          | ✓    |               | ✓            |            | phy-mono             |
| bnn-data-mono-ineq    | ✓    | ✓             |              | ✓          | data-mono-ineq (★)   |

训练脚本 `run_train_0404.py` 第 286–300 行已把 `loss_mono / loss_ineq`
加到 ELBO 之上：

```
total_loss = ELBO + w_mono · L_mono + w_ineq · L_ineq
```

### 3.2 推荐理由

1. **0411 canonical 已证明**：`data-mono-ineq` 在 5 模型对比中取得
   最窄的 MPIW₉₀ (31.96 MPa) 且 PICP₉₀ 在目标带 (0.9471) 内；5 模型
   stress R² 仅差 0.3%，约束几乎不损伤精度。
2. **MCMC 场景至关重要**：posterior calibration 中采样器会走到训练域
   边界，纯 BNN 后验预测在此处退化为宽方差高斯，而约束层强制物理
   不可违反关系（σ ≥ 0、T_peak ≥ T_avg），直接关系到 §2.4 高应力
   案例的 feasibility 判定鲁棒性。
3. **成本为零**：约束作为梯度惩罚项，不改变网络容量，也不改变推断
   流程。

### 3.3 正文叙事建议

- 主模型：`bnn-data-mono-ineq`，正文称 **"constraint-regularized
  BNN"**；
- 附录 B：`bnn-baseline` 作为消融基线（纯 ELBO）；
- 附录 D 展示 4 变体的全量精度/校准比较（与 0411 Table A2 对应）。

**需要等服务器结果**：最终推荐要在 4 变体跑完后用 `metrics_per_output_fixed.csv`
复核——如果新结果出现反转（例如 `bnn-phy-mono` 更好），再切换。

---

## D4. 基线对比策略 → 建议 **三列对比：bnn-baseline / bnn-data-mono-ineq / 0411 HeteroMLP data-mono-ineq**

### 4.1 三个"基线"实际是不同层级的对照

| 对象                             | 作用                                           | 训练位置      |
|----------------------------------|-----------------------------------------------|--------------|
| bnn-baseline                     | 纯 BNN 消融（无物理约束）                         | bnn0414     |
| bnn-data-mono-ineq（主模型）       | 本文提出的全模型                                  | bnn0414     |
| 0411 HeteroMLP data-mono-ineq    | 已发表确定性代理，作 BNN 相对前作的增益证据          | 0411 canonical|

### 4.2 拟用于 Table 2 的模板（等 BNN 训练完填数）

| Model                           | R² (stress) | RMSE (MPa) | PICP₉₀ | MPIW₉₀ (MPa) | 认识论分量 |
|---------------------------------|:-----------:|:----------:|:------:|:------------:|:---------:|
| HeteroMLP data-mono-ineq (0411) | 0.929       | 7.918      | 0.947  | 31.96        | —（无）   |
| BNN baseline (ELBO only)        | x           | x          | x      | x            | ✓         |
| **BNN data-mono-ineq (本文)**   | x           | x          | x      | x            | ✓         |

### 4.3 推荐

**全部三列都列。** 理由：

1. **(BNN baseline vs BNN full)** 证明约束对 BNN 的价值（即 D3 的支持
   证据）；
2. **(BNN full vs 0411 HeteroMLP)** 证明引入贝叶斯的价值——关键是
   "认识论分量"一列只有 BNN 能给出，这是 §3.2 的主叙事；
3. 对审稿人显示 BNN **没有付出 in-distribution 精度代价**（如果 R²
   与 HeteroMLP 相近或更好的话）。如果 BNN R² 明显低于 HeteroMLP，
   这个对比反而会给审稿人攻击点，届时可再商议是否退成"两列"。

### 4.4 风险

如果 `bnn-data-mono-ineq` 的 stress R² 比 HeteroMLP canonical (0.929)
低超过 0.02，叙事可能要从"替换"调整为"互补"——需要结果出来后再决定。
**[不确定]** 目前不能预判 MFVI + constraints 的 R² 能否达到 0.929。

---

## D5. 速度叙事 → 脚本已就位：`run_speed_0404.py`

### 5.1 现状
`experiments_0404/experiments/run_speed_0404.py` 已经支持
multi-sample MC 推断（第 113–164 行）：
- `mc_forward(model, x, n_mc, sample=True)` 对 `n_mc` 次权重采样后
  取均值；
- `BNN_N_MC_EVAL` 从 `experiment_config_0404.py` 读取。

**【不确定】** `BNN_N_MC_EVAL` 的当前值。需要你确认或
在 `experiment_config_0404.py` 中查一下——通常 M=30–100
是 MFVI BNN 推断的合理范围。

### 5.2 HF 参考时间占位
脚本第 54–60 行注释：

```
参考 HF 时间 3600.0 s 是早期占位；canonical 应为 2266 s（0411 HeteroMLP
HF 基准）。
```

→ 你需要在跑 speed benchmark 之前把 `HF_T_BASELINE` 改为 2266.0；或
让脚本从 0411 canonical_values.json 的 speed 段读入。**建议保持
0411 的 HF 基准**（同一台机器、同一 HF 流程），不必为 BNN 分支再跑
一次 HF——HF 时间与代理本身无关。

### 5.3 预期数字量级（仅供你校对）
BNN 单样本推断 ≈ M × HeteroMLP 单样本推断；
- HeteroMLP 1.553e-4 s × (假设 M=50) ≈ 7.8e-3 s → 加速比退到 ~2.9e5；
- 批处理 1.709e-7 s × 50 ≈ 8.5e-6 s → 加速比 ~2.7e8。

仍是"orders of magnitude faster"，叙事不破。**如果 M 较大
(如 200)**，单样本加速比将降到 ~10⁵；仍可接受。

### 5.4 无需新脚本，但建议你在服务器端做两件事

1. 确认 `experiment_config_0404.py::BNN_N_MC_EVAL` 与 §4.3 "M 个权重
   样本"一致，否则论文写 M=x 时会混乱；
2. 跑 `MODEL_ID=bnn-data-mono-ineq python run_speed_0404.py` 并把
   `bnn_speed_benchmark.json` 拷回本地；我来回填 §3.4。

---

## D6. 标题 → 已定改：**Bayesian Neural Network Surrogates**

用户确认采纳。建议最终版本：

> **Bayesian Neural Network Surrogates for Uncertainty-to-Risk Analysis
> in Coupled Multi-Physics Systems: Application to a Heat-Pipe-Cooled
> Reactor**
>
> 贝叶斯神经网络代理模型在耦合多物理场系统不确定性–风险分析中的应用
> ——以热管冷却反应堆为例

**正文落实**：下一轮 Edit 会把 draft_paper_0414_v4.txt 第 2 行和第 5
行的标题改掉。

---

## D8. HF 抽查 → ✅ 已定：**用 BNN 后验均值重跑，全部 18 个 benchmark 案例**

### 8.1 必须重跑的理由
- HeteroMLP 后验均值 ≠ BNN 后验均值（后者对权重也边缘化，E_w[μ_w(θ)]
  自然与 MAP 权重的 μ(θ) 不同）；
- 沿用 0411 的 5 例 HF 结果会被审稿人直接指出 "不是你这篇论文的
  代理的验证"。

### 8.2 推荐规模：3 分层 × 5 例 = 15 例

| 分层               | 真实应力范围         | 例数 | 理由                               |
|-------------------|-------------------|:----:|----------------------------------|
| 低应力             | < 120 MPa         | 5    | 覆盖 feasible 区域                |
| 近阈值             | 120–140 MPa       | 5    | 应力筛选阈值最敏感区               |
| 高应力             | > 140 MPa         | 5    | feasibility-check / 超阈叙事锚点   |

> 另可选：全部 18 benchmark 案例都重跑 → 最稳；但 HF ~38 min/case ×
> 18 ≈ 11.4 小时，一次 GPU 节点夜跑即可。**[不确定]** 服务器排队成本；
> 你若能承担就直接上 18 例，叙事最完整。

### 8.3 推荐流程
1. `run_posterior_0404.py` 对每个选定 case 导出后验均值参数 →
   `posterior_hf_rerun_inputs.csv`；
2. 在 HF 环境跑 `code/openmc-fenics代码/run_posterior_hf_rerun.py`
   （此脚本已存在，读入 CSV 返回 15 输出）；
3. `postproc/parse_hf_rerun_bnn.py` 合并 HF 结果与 BNN 预测，产出
   `hf_rerun_summary.json` 和 `hf_rerun_vs_bnn_comparison.csv`；
4. §2.5 和附录用新的 MAE/RMSE 回填。

我已起草了 step 1 的 selector 骨架，见
`code/bnn0414/code/postproc/build_bnn_hf_rerun_manifest.py`（
**待补**，见下节）。

---

## 附加：你可能还需要的脚本与文件

### A. `build_bnn_hf_rerun_manifest.py` — 新建

**位置**：`code/bnn0414/code/postproc/build_bnn_hf_rerun_manifest.py`
**作用**：从 `results/posterior/<model>/<case>/posterior_samples.csv`
读入后验样本，计算后验均值，写出 `posterior_hf_rerun_inputs.csv`。
我会用下一个 tool call 写一个骨架版本，【不确定】的行标出。

### B. `code/bnn0414/code/postproc/parse_hf_rerun_bnn.py` — 新建

**作用**：合并 HF rerun 输出（15 scalar outputs）与 BNN
`(μ̂, σ̂_epistemic, σ̂_aleatoric)` 预测，产出 per-case 对比和
aggregate MAE/RMSE。
**建议**：直接从 `code/0411/code/postproc/build_rerun_manifest.py`
派生；主要差别是加载 BNN 而不是 HeteroMLP，并保存 epistemic/aleatoric
拆分。

### C. `canonical_values_v4.json` — 待生成

待 BNN 全部结果出来后，照 0411 模板建立一份新的 canonical；这是 v4
论文所有数字的唯一 source of truth。

### D. `source_notes/phase1_evidence_v4.md` — 待生成

对应 0411 phase1_evidence.md 的新版本，列出每条正文数字的出处。

---

## 未定事项清单（供你拍板）

| 编号 | 事项                                                   | 我的建议                      | 需要你决定                       |
|:---:|--------------------------------------------------------|------------------------------|--------------------------------|
| E1  | BNN 主模型                                              | bnn-data-mono-ineq           | 等结果后复核是否保持            |
| E2  | 基线列是否包含 0411 HeteroMLP                           | 是（三列）                   | 如果 BNN R² 显著低则退成两列     |
| E3  | M（推断权重样本数）                                      | ✅ 已定：50（Sobol=30, MCMC=20） | —                              |
| E4  | HF 抽查案例数                                           | ✅ 已定：18 全部（与 §2.4 1-对-1） | —                              |
| E5  | w_mono / w_ineq 是否 Optuna 搜还是固定                    | 按 0411 做法 Optuna 搜         | 服务器已跑方式待你确认          |
| E6  | Optuna 试验次数（40 for baseline/data-mono，30 其余）     | 沿用 0411 (60/40) 或现设 (40/30) | 服务器已跑方式待你确认         |
| E7  | 是否用多链 MCMC（n_chains=4）给 Rhat 诊断                 | ✅ 已定：n_chains = 4            | —                              |
| E8  | OOD 评估是否进正文                                       | 附录即可（沿用 0411 决策）     | 若 BNN OOD 明显优于 HeteroMLP   |
|     |                                                        |                              | 可考虑提到正文                  |

=====================================================================
