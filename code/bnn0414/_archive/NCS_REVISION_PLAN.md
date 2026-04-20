# NCS Revision Plan — bnn0414

> **作者**: 机器审计 + 严格审稿人意见综合
> **日期**: 2026-04-16
> **目标**: 把 bnn0414 提升到 *Nature Computational Science* 证据门槛
> **HF rerun 状态**: 已在跑（posterior §2.5），不在本计划内重复

---

## 0. 审稿人清单 vs. 代码库实情（再核对）

reviewer agent 最初的 10 项"缺失"里，**有 6 项其实已经存在**，只需在写作中明确引用；只有 3 项**真正缺失**，另 5 项**部分存在需要补**。本节说明为什么有些不补。

### 已存在，**不需要再做**
| reviewer 声称缺失 | 实际位置 | 说明 |
|---|---|---|
| Epistemic/aleatoric 分解 | `code/experiments/risk_propagation/*/D1_nominal_risk.csv`（列 `stress_pred_epistemic_mean`, `stress_pred_aleatoric_mean`），`code/experiments/generalization/*/ood_per_output.csv`（`epistemic_std_mean`, `aleatoric_std_mean`） | 已有全 4 模型 × 全 output |
| Sobol bootstrap CI | `code/experiments/sensitivity/*/sobol_results.csv`（列 `S1_ci_lo/hi`, `ST_ci_lo/hi`, `S1_ci_spans_zero`） | 已有；写作中显式引用 spans_zero 标注即可 |
| 多 seed 训练 | `code/models/*/repeat_eval/seed_2026..2030/` | 已有 5 seed |
| OOD 协议 | config 中 `OOD_FEATURE="alpha_slope"`, `OOD_KEEP_MIDDLE_RATIO=0.80`；`ood_summary.csv`, `ood_per_output.csv` | 已有正式定义 |
| 阈值扫描 110/120/131 MPa | `D1_nominal_risk.csv`（`threshold_MPa ∈ {110, 120, 131, 150, 180, 200}`, `P_exceed`） | 已有全扫描 |
| HF rerun | `code/postproc/run_posterior_hf_rerun_0404.py` + `code/experiments/posterior/*/hf_rerun/` | 已在跑 |

### 部分存在，**需要补齐**
| 项目 | 现状 | 需要补什么 |
|---|---|---|
| 多 α calibration | 只有 95% PICP + 单 α CRPS | 多 α（6 档）coverage + reliability + PIT + NLL + interval score |
| MCMC 诊断 | rhat 列有但值为空；只有 `accept_rate` | 2-chain rhat 数值、ESS、per-chain acceptance |
| Monotonicity 检验 | `gradient_sign_check.csv`（连续性梯度符号） | 离散扰动违反率（counterexample rate） |
| Compute-budget 对比 | 只有单样本速度比（`speedup_single_mc_vs_hf = 3600s/call`） | 等 CI 半宽下 wall-clock 对比 |
| Manifest 完整性 | 现有 manifest 有 timestamps 但无 git_sha / config_hash / dataset_hash | 3 个 hash 字段 + retrofit pass |

### 真正缺失，**必须补**
| 项目 | 为什么必须 |
|---|---|
| 外部 baseline（MC-dropout + deep ensemble） | "四个同族 BNN 变体"在 NCS 眼中不是 ablation，是同一个方法的四个口味；必须有跨族对照 |
| Prior sensitivity | BNN 后验对先验敏感，不做即被视作隐瞒 |
| Posterior predictive check (PPC) | 后验覆盖率 ≠ 后验预测合理性 |

### reviewer 遗漏、我要加
| 项目 | 为什么加 |
|---|---|
| 数据效率曲线 | NCS 审稿人几乎必问"如果数据更少呢" |
| 观测噪声敏感性（σ_obs ∈ {1%, 2%, 5%}） | "为什么是 2%" 是必答题 |

### reviewer 要求但**不打算做**（会在 rebuttal 里解释）
- GP baseline：输入维度 8，15 输出，N=2029，GP 训练/推断成本 O(N³)=8.4e9，即使用 sparse GP 也是重工程；MC-dropout + ensemble 已覆盖"非 BNN 概率代理"的对照轴。
- Laplace approximation / SWAG：与 MC-dropout 在方法族上高度相关，补 LA/SWAG 边际价值低。若审稿人坚持，再说。
- SBC (simulation-based calibration)：需要重跑 N=500+ 场景的完整 posterior，计算成本不成比例。

---

## 1. 任务清单与优先级（执行顺序 = 重要性顺序）

每一项都对应 TaskList 中的一个 task ID，见右列。

### **P0 — NCS blocking**（必须做，任何一项缺都会被拒）

| # | 任务 | Task ID | 服务器？ | 产物 | 状态 |
|---|---|---|---|---|---|
| 1 | **MCMC 诊断补全**（rhat / ESS / per-chain accept） | #3 | 是（benchmark 重跑，2+ chain） | `benchmark_summary.csv`（rhat 填充）+ `mcmc_diagnostics.csv` + `chains/*.npz` | 🟡 脚本就绪（`run_posterior_diagnostics_0404.py` + `deploy/p0_3_mcmc_diagnostics.sh`），等 SSH |
| 2 | **多 α calibration + PIT + NLL + interval score** | #2 | 否（本地后处理） | `results/accuracy/calibration_multi_alpha.csv`, `scoring_rules.csv`, `reliability_*.png`, `pit_*.png` | ✅ 完成（48 行 calibration × 6 α × 4 模型；data-mono-ineq ECE=0.135 > baseline 0.109 → 诚实报告） |
| 3 | **External baseline (MC-dropout + 5-member deep ensemble)** | #1 | 是（训练） | `code/models/mc-dropout/`, `code/models/deep-ensemble/` + 同 BNN 一致的 metrics | ⏳ 待服务器（尚未写训练脚本） |
| 4 | **单调性违反率（离散扰动）** | #4 | 是（需要 torch 前向） | `results/physics_consistency/monotonicity_violation_rate.csv` + `inequality_violation_rate.csv` + figure | 🟡 脚本就绪（`run_monotonicity_violation_0404.py` + `deploy/p0_4_monotonicity.sh`），等 SSH |
| 5 | **Compute-budget matched risk 对比** | #5 | 否（分析） | `results/speed/budget_matched_risk.csv` + figure | ✅ 完成（48 行 × 4 模型 × 6 CI 半宽；headline: N=20627 at CI=0.005, surrogate 0.28s vs HF 859d *fallback*; HF 真实时间等 rerun 完成后复跑，复跑只需重新 `python run_budget_matched_risk_0404.py`） |

### **P1 — important**（审稿人会问，答不上会要 major）

| # | 任务 | Task ID | 服务器？ | 产物 |
|---|---|---|---|---|
| 6 | **Posterior predictive check (PPC)** | #6 | 是（需要 torch forward） | `posterior/<model>/ppc/ppc_summary.csv` + `ppc_*.png` | ✅ 脚本就绪（`run_posterior_predictive_check_0404.py` + `deploy/p1_6_ppc.sh`），依赖 #3 chains |
| 7 | **Prior sensitivity**（6 variants × 6 cases × 4000-step MCMC） | #7 | 是 | `posterior/<model>/prior_sensitivity/` | ✅ 脚本就绪（`run_prior_sensitivity_0404.py` + `deploy/p1_7_prior_sensitivity.sh`）|
| 8 | **Data efficiency curve**（frac ∈ {0.25,0.5,0.75,1.0} × 2 seeds） | #8 | 是（16 次训练） | `results/data_efficiency/` | ✅ 脚本就绪（`run_data_efficiency_0404.py` + `deploy/p1_8_data_efficiency.sh`）|
| 9 | **Observation noise sensitivity**（σ_obs ∈ {0.5%,1%,2%,3%,5%,10%}） | #9 | 是 | `posterior/<model>/noise_sensitivity/` | ✅ 脚本就绪（`run_noise_sensitivity_0404.py` + `deploy/p1_9_noise_sensitivity.sh`）|

### **P2 — polish / discipline**（投稿前清理）

| # | 任务 | Task ID | 服务器？ |
|---|---|---|---|
| 10 | Manifest hash retrofit（git SHA / config SHA / dataset SHA） | #10 | 否 |
| 11 | Figure vocabulary + CJK audit | #11 | 否 |

---

## 2. 服务器对接约定

### 远端路径
```
tjzs@100.68.18.55:/home/tjzs/Documents/fenics_data/hpr_surrogate/hpr-claude-project/code/bnn0414/
```
数据：`/home/tjzs/Documents/fenics_data/fenics_data/txt_extract/dataset_v3.csv`
LEGACY：`/home/tjzs/Documents/fenics_data/hpr_surrogate/code/0310/`
Conda env：`nn_env`
Env flags：`HPR_ENV=server`, `HPR_LEGACY_DIR=/home/tjzs/.../code/0310`

### Push 流程（我为每个任务单独提供）
```bash
# 示例（每个任务的脚本各自具体化）
rsync -avz --exclude '__pycache__' \
    /Users/yinuo/Projects/hpr-claude-project/code/bnn0414/code/experiments_0404/experiments/<NEW_SCRIPT>.py \
    tjzs@100.68.18.55:/home/tjzs/Documents/fenics_data/hpr_surrogate/hpr-claude-project/code/bnn0414/code/experiments_0404/experiments/

ssh tjzs@100.68.18.55 <<'EOF'
cd /home/tjzs/Documents/fenics_data/hpr_surrogate/hpr-claude-project/code/bnn0414/code/experiments_0404
export HPR_ENV=server
export HPR_LEGACY_DIR=/home/tjzs/Documents/fenics_data/hpr_surrogate/code/0310
conda run -n nn_env python experiments/<NEW_SCRIPT>.py
EOF
```

### Pull 流程
```bash
rsync -avz tjzs@100.68.18.55:<REMOTE_RESULTS_DIR>/ <LOCAL_RESULTS_DIR>/
```

每个任务的 push/pull 一键化脚本会随任务交付，放在 `code/bnn0414/deploy/<task_tag>.sh`。

---

## 3. 每个脚本的落盘规则（不可违反）

1. **不覆盖 canonical 产物**：新脚本一律写到新 `OUT_DIR`，不得动 `bnn-baseline/fixed_eval/` 等已冻结产物。
2. **新产物放在 `results/<subsystem>/` 下**，与既有约定（`results/accuracy/`, `results/posterior/`, `results/speed/` 等）保持一致。
3. **manifest 必写**：用 `manifest_utils_0404.write_manifest`，包含 `script_sha`、`config_hash`、`dataset_hash`、`git_sha`、`seed`、`timestamp`。
4. **配置单一来源**：所有常量从 `experiment_config_0404` 读，禁止在脚本里硬编码阈值 / α / seed。
5. **日志**：`results/logs/<task_tag>_<timestamp>.log`。
6. **图**：遵守图内词汇规则（无 `iter1/iter2/level0/baseline/data-mono-ineq` 原名、无 CJK）。
7. **本地 only 的脚本**：脚本头显式注明 `# LOCAL ONLY — does not depend on server`。
8. **服务器 only 的脚本**：脚本头注明 `# SERVER ONLY — requires HPR_ENV=server`，并在 `if __name__ == "__main__"` 前检查 env 变量。

---

## 4. 验收标准（按任务）

| 任务 | Pass 标准 |
|---|---|
| MCMC 诊断 | `benchmark_summary.csv.rhat` 非空，mean rhat < 1.1 跨 4 model；ESS mean > 200 |
| 多 α calibration | 6 个 α 的 coverage 表 + ECE；NLL 与 interval score 写入 `scoring_rules.csv` |
| 外部 baseline | MC-dropout + deep ensemble 都跑完并在主 metrics 表里；test CRPS 可与 BNN 对齐比较 |
| 单调性违反率 | 每 {model, input, output} 配对有 violation rate；bnn-data-mono-ineq 应 < 5%，baseline 允许更高，差距写入正文 |
| Budget-matched risk | 单一图：横轴 wall-clock，纵轴 tail risk CI 半宽；surrogate 的线应显著左下 |
| PPC | Bayesian p-value ∈ [0.05, 0.95] 为合格（非过拟合也非 miscalibrated） |
| Prior sensitivity | 后验均值随 prior × 0.5 / 1.0 / 2.0 的相对漂移 < 10% 可声称"低敏感"，否则诚实报告 |
| Data efficiency | N_train = {256, 512, 1024, full} 下 CRPS 曲线；NCS 正文 Fig. |
| Noise sensitivity | σ_obs ∈ {1%, 2%, 5%} 下 coverage 与 feasible region 面积变化 |

---

## 5. 依赖与顺序（看图可跳）

```
任务 #3 (MCMC 诊断)     ──┐
任务 #2 (多 α calibration)──┼─→ 表进入 manuscript §2.3 calibration 主表
任务 #1 (外部 baseline)   ──┘

任务 #4 (单调性违反率)    ──→ manuscript §2.4 物理正则化证据
任务 #5 (budget-matched) ──→ manuscript §1 motivation + §3 enabling claim
任务 #6 (PPC)            ──→ manuscript §2.5 posterior validity（与 HF rerun 并列）
任务 #7 (prior sens.)    ──→ manuscript §App. posterior robustness
任务 #8 (data eff.)      ──→ manuscript §App. data efficiency（reviewer Q. 必答）
任务 #9 (noise sens.)    ──→ manuscript §App. noise robustness
任务 #10 (manifest)      ──→ 投稿前 reproducibility
任务 #11 (figure audit)  ──→ 投稿前视觉纪律
```

---

## 6. 风险与提示

- **服务器资源**：若 GPU 冲突（HF rerun 占用），P0-3 / P0-1 要排队。建议：HF rerun 跑完 → MCMC 诊断 → baseline 训练。
- **冻结 split**：所有新脚本必须用 `FIXED_SPLIT_DIR`，禁止重新划分。
- **后验可重现性**：多 α / PPC / prior sensitivity 共用一套 posterior 链；建议任务 #3 跑完并保存完整 chain（而非只 summary），#6 和 #7 直接复用。
- **HF 真机时间源**：#5 的 HF wall-clock 不要硬编码 3600s，用 HF rerun 实际 log 聚合的分布。

---

## 7. 不做的事（显式 rebuttal 候选）

- 不补 GP baseline（O(N³) 成本、工程量不成比例）。
- 不补 Laplace / SWAG（与 MC-dropout 同族，边际信息量低）。
- 不做 full SBC（单个 case 后验计算已 1200 样本，全 N=500+ 不现实）。
- 不改 posterior 的 proposal kernel（审稿人若质疑 MH 选择再补 HMC 对照）。

如果审稿人坚持要这些，再在第二轮补。本轮按上面 11 项交付。
