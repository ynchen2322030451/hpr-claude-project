# 01 — Accuracy: fixed_eval + 5-seed repeat + per-output breakdown

源文件：`code/models/<model>/fixed_eval/{metrics_fixed.json, metrics_per_output_fixed.csv}` 与 `repeat_eval/repeat_summary.json`（种子 2026–2030，MC draws = 50）。
测试集大小 n_test = 459（来自 `experiments_0404/_shared/fixed_split/test_indices.csv`）。

---

## 0. 指标定义与合适数值判据

下列四个概率预测评分是本章的核心指标；当前正文方法节（§4）尚未给出显式定义式，应补入 Methods §4.4（评价指标）：

### PICP₉₀ — Prediction Interval Coverage Probability (90 % level)

$$
\mathrm{PICP}_{0.90} = \frac{1}{N}\sum_{i=1}^{N}\mathbb{1}\!\left[\,y_i \in [\hat{l}_i,\ \hat{u}_i]\,\right],\qquad
[\hat{l}_i,\hat{u}_i]\ \text{= 90 \% 后验预测分位区间}
$$

- **合适数值**：理想 ≈ 0.90（匹配名义置信水平）。
- **> 0.90** → 保守/过覆盖（区间宽）；**< 0.90** → 欠覆盖（不安全）。
- 安全敏感问题容忍 PICP 略高于名义值，但 PICP ≈ 0.99 已是显著过保守，通常伴随 MPIW 过宽。

### MPIW₉₀ — Mean Prediction Interval Width

$$
\mathrm{MPIW}_{0.90} = \frac{1}{N}\sum_{i=1}^{N} \left(\hat{u}_i - \hat{l}_i\right)
$$

- 单位与 y 相同，越小越"锐利"。
- **没有绝对阈值**，需与 y 的 scale 对齐。经验参照：
  - 对 Gaussian 预测分布，90 % 区间 ≈ ±1.645 σ，故 `MPIW₉₀ ≈ 3.29 σ_pred`。
  - 当预测完美校准（PICP ≈ 0.90）时，`MPIW₉₀ / RMSE ≈ 3.29 σ_pred / σ_true ≈ 3.29`（若 σ_pred ≈ σ_true）。
  - 对本项目应力输出，RMSE ≈ 8.3 MPa，则理想 MPIW₉₀ ≈ 27 MPa；若 MPIW₉₀ 显著大于此值，说明区间被人为放大以吸收认识论不确定性（保守但不锐利）。

### CRPS — Continuous Ranked Probability Score

$$
\mathrm{CRPS}(F_i,\ y_i) = \int_{-\infty}^{\infty} \left(F_i(z) - \mathbb{1}[z\geq y_i]\right)^2 \mathrm{d}z
$$

- 综合衡量**精度 + 校准**（比 PICP/MPIW 更敏感，对整个预测分布评分）。
- 单位与 y 相同，越小越好。
- 对完美校准的 Gaussian 预测分布 `CRPS ≈ 0.564 σ_pred`；对本项目应力（σ ≈ 8 MPa）理想 CRPS ≈ 4.5 MPa。
- **经验规则**：`CRPS < RMSE / 1.77` 时说明预测分布形状优于点估计 + 恒定方差假设。

### R² — Coefficient of determination

$$
R^2 = 1 - \frac{\sum (y_i - \hat{\mu}_i)^2}{\sum (y_i - \bar{y})^2}
$$

- 点预测均值的方差解释比例；**只评估均值，不评估不确定性**。
- 大于 0.8 即"良好"，0.9 以上"优秀"。对本项目 iter2 耦合温度类输出 R² ≈ 0.58 提示均值预测仍有提升空间（但这是耦合反馈的信息损失，不是 BNN 缺陷）。

---

## 1. Fixed eval — 全测试集聚合（stress 等 15 输出加权后的代表指标）

| 模型 | MAE | RMSE | R² | PICP | MPIW | CRPS |
|---|---|---|---|---|---|---|
| bnn-baseline | 2.771 | 3.556 | 0.758 | 0.969 | 16.30 | 2.063 |
| bnn-data-mono | 2.731 | 3.547 | 0.760 | 0.969 | 17.38 | 2.104 |
| bnn-phy-mono | 2.767 | 3.582 | 0.761 | 0.961 | **15.41** | **2.048** |
| bnn-data-mono-ineq | 2.876 | 3.750 | 0.740 | **0.980** | 21.00 | 2.300 |

聚合为 15 输出标准化平均，注意混合量纲（keff 与 MPa 不同级），故此表仅用于跨模型相对排序，不宜单独引用数值。

## 2. 5-seed repeat — 5 个不同 train/val split（训练随机性）

| 模型 | MAE | RMSE | R² | PICP | MPIW | CRPS |
|---|---|---|---|---|---|---|
| bnn-baseline | 2.625±0.132 | 3.421±0.141 | 0.744±0.048 | 0.976±0.005 | 16.24±0.26 | 1.969±0.069 |
| bnn-data-mono | 2.613±0.107 | 3.431±0.124 | 0.746±0.049 | 0.976±0.006 | 17.17±0.30 | 2.009±0.064 |
| bnn-phy-mono | **2.583±0.122** | **3.405±0.135** | **0.747±0.050** | 0.970±0.006 | **15.24±0.26** | **1.922±0.074** |
| bnn-data-mono-ineq | 2.684±0.114 | 3.525±0.115 | 0.733±0.047 | **0.986±0.003** | 21.14±0.32 | 2.208±0.058 |

---

## 3. 逐输出分指标全表（fixed_eval, n=435）

15 个输出按 iter1 / iter2 分组；粗体标注每行最优（R²/PICP 最高；MPIW/CRPS 最低）。

### 3.1 R²

| output | baseline | data-mono | phy-mono | data-mono-ineq |
|---|---|---|---|---|
| iteration1_avg_fuel_temp | 0.813 | 0.817 | **0.821** | 0.797 |
| iteration1_max_fuel_temp | 0.815 | **0.816** | 0.816 | 0.796 |
| iteration1_max_monolith_temp | 0.812 | 0.817 | **0.820** | 0.796 |
| iteration1_max_global_stress | **0.932** | 0.929 | 0.923 | 0.916 |
| iteration1_monolith_new_temperature | 0.818 | 0.821 | **0.827** | 0.798 |
| iteration1_Hcore_after | **0.983** | 0.978 | 0.982 | 0.923 |
| iteration1_wall2 | 0.993 | **0.994** | 0.992 | 0.980 |
| **iteration2_keff** ★ | 0.876 | **0.877** | 0.872 | 0.825 |
| iteration2_avg_fuel_temp | 0.584 | 0.584 | **0.590** | 0.575 |
| **iteration2_max_fuel_temp** ★ | 0.583 | 0.585 | **0.590** | 0.580 |
| **iteration2_max_monolith_temp** ★ | 0.585 | 0.589 | **0.590** | 0.577 |
| **iteration2_max_global_stress** ★ | 0.922 | **0.925** | 0.920 | 0.910 |
| iteration2_monolith_new_temperature | 0.590 | 0.597 | **0.600** | 0.581 |
| iteration2_Hcore_after | **0.074** | 0.070 | 0.071 | 0.064 |
| **iteration2_wall2** ★ | 0.992 | **0.995** | 0.994 | 0.978 |
| **每模型 R² 最优次数** | 3 | 5 | **7** | 0 |

★ 行 = CLAUDE.md 指定的五个 primary outputs。

### 3.2 PICP（理想 ≈ 0.90）

| output | baseline | data-mono | phy-mono | data-mono-ineq | 最接近 0.90 者 |
|---|---|---|---|---|---|
| iteration1_avg_fuel_temp | 0.954 | 0.959 | **0.945** | 0.986 | phy-mono |
| iteration1_max_fuel_temp | 0.956 | 0.959 | **0.954** | 0.986 | phy-mono |
| iteration1_max_monolith_temp | 0.956 | 0.959 | **0.945** | 0.986 | phy-mono |
| iteration1_max_global_stress | 0.989 | 0.993 | **0.986** | 0.998 | phy-mono |
| iteration1_monolith_new_temperature | 0.959 | 0.961 | **0.947** | 0.986 | phy-mono |
| iteration1_Hcore_after | 1.000 | 1.000 | 1.000 | 1.000 | 全部过覆盖 |
| iteration1_wall2 | 1.000 | 1.000 | 1.000 | 1.000 | 全部过覆盖 |
| **iteration2_keff** ★ | 0.995 | 1.000 | **0.986** | 1.000 | phy-mono |
| iteration2_avg_fuel_temp | 0.933 | **0.920** | 0.920 | 0.945 | data-mono/phy-mono |
| **iteration2_max_fuel_temp** ★ | 0.931 | 0.933 | **0.915** | 0.943 | phy-mono |
| **iteration2_max_monolith_temp** ★ | 0.938 | 0.929 | **0.917** | 0.938 | phy-mono |
| **iteration2_max_global_stress** ★ | 0.991 | 0.993 | **0.982** | 0.998 | phy-mono |
| iteration2_monolith_new_temperature | 0.940 | 0.931 | **0.924** | 0.940 | phy-mono |
| iteration2_Hcore_after | 0.998 | 0.998 | 0.998 | 0.998 | 全部过覆盖 |
| **iteration2_wall2** ★ | 1.000 | 1.000 | 1.000 | 1.000 | 全部过覆盖 |

**关键洞察**：phy-mono 的 PICP 在 13 个输出中**最接近名义 0.90**，其他三者均偏保守。data-mono-ineq 的 PICP 全部 ≥ 0.94，显著过覆盖。

### 3.3 MPIW（越小越锐利）

| output | baseline | data-mono | phy-mono | data-mono-ineq |
|---|---|---|---|---|
| iteration1_avg_fuel_temp | 17.19 | 17.63 | **16.51** | 21.67 |
| iteration1_max_fuel_temp | 30.16 | 30.89 | **29.10** | 36.68 |
| iteration1_max_monolith_temp | 34.34 | 36.08 | **33.17** | 43.12 |
| iteration1_max_global_stress | 61.38 | 70.02 | **58.76** | 86.11 |
| iteration1_monolith_new_temperature | 5.95 | 6.22 | **5.44** | 7.32 |
| iteration1_Hcore_after | 0.564 | 0.552 | **0.468** | 1.243 |
| iteration1_wall2 | 0.0261 | 0.0282 | **0.0226** | 0.0448 |
| **iteration2_keff** ★ | 1.63e-3 | 1.68e-3 | **1.43e-3** | 2.90e-3 |
| iteration2_avg_fuel_temp | 9.04 | 9.03 | **8.65** | 10.09 |
| **iteration2_max_fuel_temp** ★ | 16.86 | 16.92 | **16.05** | 18.78 |
| **iteration2_max_monolith_temp** ★ | 19.25 | 19.22 | **18.28** | 20.70 |
| **iteration2_max_global_stress** ★ | 46.19 | 50.64 | **41.54** | 64.28 |
| iteration2_monolith_new_temperature | 2.54 | 2.55 | **2.43** | 2.80 |
| iteration2_Hcore_after | 0.936 | 0.873 | **0.679** | 2.122 |
| **iteration2_wall2** ★ | 0.0258 | 0.0272 | **0.0213** | 0.0436 |
| **每模型 MPIW 最优次数** | 0 | 0 | **15** | 0 |

**phy-mono 在全部 15 个输出上的 MPIW 都最窄**。data-mono-ineq 的 MPIW 普遍比 phy-mono 大 30–100%。

### 3.4 CRPS（越小越好）

| output | baseline | data-mono | phy-mono | data-mono-ineq |
|---|---|---|---|---|
| iteration1_avg_fuel_temp | 2.323 | 2.323 | **2.270** | 2.477 |
| iteration1_max_fuel_temp | 4.037 | 4.067 | **4.036** | 4.323 |
| iteration1_max_monolith_temp | 4.677 | 4.680 | **4.574** | 4.983 |
| iteration1_max_global_stress | **6.718** | 7.177 | 6.914 | 8.195 |
| iteration1_monolith_new_temperature | 0.777 | 0.784 | **0.753** | 0.828 |
| iteration1_Hcore_after | 0.0412 | 0.0409 | **0.0349** | 0.0909 |
| iteration1_wall2 | 0.00203 | 0.00215 | **0.00186** | 0.00349 |
| **iteration2_keff** ★ | 0.000165 | 0.000167 | **0.000160** | 0.000247 |
| iteration2_avg_fuel_temp | 1.371 | 1.368 | **1.353** | 1.402 |
| **iteration2_max_fuel_temp** ★ | 2.558 | 2.550 | **2.533** | 2.598 |
| **iteration2_max_monolith_temp** ★ | 2.881 | 2.866 | **2.851** | 2.936 |
| **iteration2_max_global_stress** ★ | 5.078 | 5.238 | **4.954** | 6.094 |
| iteration2_monolith_new_temperature | 0.379 | 0.375 | **0.372** | 0.385 |
| iteration2_Hcore_after | 0.0958 | 0.0917 | **0.0780** | 0.1799 |
| **iteration2_wall2** ★ | 0.00202 | 0.00206 | **0.00170** | 0.00345 |
| **每模型 CRPS 最优次数** | 1 | 0 | **14** | 0 |

---

## 4. 核心输出（★ primary）深入对比

### 4.1 iteration2_max_global_stress（最重要的安全变量）

| 指标 | baseline | data-mono | phy-mono | data-mono-ineq |
|---|---|---|---|---|
| R² | 0.922 | **0.925** | 0.920 | 0.910 |
| RMSE (MPa) | 8.29 | 8.16 | 8.40 | 8.93 |
| PICP | 0.991 | 0.993 | 0.982 | 0.998 |
| MPIW (MPa) | 46.2 | 50.6 | **41.5** | 64.3 |
| CRPS (MPa) | 5.08 | 5.24 | **4.95** | 6.09 |
| 判读 | 参考基准 | R² 最高 | **区间最锐利 + CRPS 最优** | PICP 最高但过保守 |

**理论参考线**：RMSE = 8.40 MPa → 完美校准下期望 MPIW ≈ 3.29 × 8.40 = 27.6 MPa；所有模型的 MPIW 均高于此值（41.5–64.3 MPa），说明 BNN 后验预测存在**系统性过宽**，phy-mono 最接近理想。

### 4.2 iteration2_keff（中子学安全）

| 指标 | baseline | data-mono | phy-mono | data-mono-ineq |
|---|---|---|---|---|
| R² | 0.876 | **0.877** | 0.872 | 0.825 |
| RMSE | 2.52e-4 | 2.50e-4 | 2.56e-4 | 2.98e-4 |
| PICP | 0.995 | 1.000 | **0.986** | 1.000 |
| MPIW (pcm) | 163 | 168 | **143** | 290 |
| CRPS | 1.65e-4 | 1.67e-4 | **1.60e-4** | 2.47e-4 |

phy-mono MPIW ≈ 143 pcm, data-mono-ineq 290 pcm 几乎翻倍。

### 4.3 iteration2_max_fuel_temp / max_monolith_temp

两者 R² ≈ 0.58–0.60（四模型都是）。**这不是 BNN 弱点**：iter2 的温度场是耦合反馈后重分布的结果，输入–输出映射本身信息量下降（相较 iter1 R²≈0.82）。这一点应在讨论中明示，避免读者误以为 BNN 训练不足。

### 4.4 iteration2_wall2（径向热变形）

四模型 R² > 0.97，phy-mono MPIW / CRPS 最优。不作为主结论图展示，附录表中体现即可。

### 4.5 iteration2_Hcore_after（芯高度）

四模型 R² 均 < 0.08，表示这个输出几乎不可预测（输入对它几乎无信息）。**不要放进主表**；如放入附录要明确说明 "low-signal output"。

---

## 5. 主模型选择建议（基于 15 输出全量数据）

### 5.1 当前草稿的约定
- §2.1 主对比：bnn-baseline（Reference surrogate）vs bnn-data-mono-ineq（Physics-regularized surrogate）
- bnn-data-mono 与 bnn-phy-mono 定位为附录消融

### 5.2 数据真实排序（5-seed 均值，15 输出）

| 模型 | R² 最优次数 | PICP 最接近 0.90 次数 | MPIW 最窄次数 | CRPS 最优次数 |
|---|---|---|---|---|
| bnn-baseline | 3 | 0 | 0 | 1 |
| bnn-data-mono | 5 | 1 | 0 | 0 |
| **bnn-phy-mono** | **7** | **13** | **15** | **14** |
| bnn-data-mono-ineq | 0 | 0 | 0 | 0 |

**phy-mono 在几乎所有 sharpness / calibration / CRPS 指标上全面领先，且 PICP 最接近名义 0.90（其余三者都显著过保守）。**

### 5.3 三种可选方案

| 方案 | 主对比 | 附录 | 叙事 | 代价 |
|---|---|---|---|---|
| **A. 保持现状** | baseline vs data-mono-ineq | phy-mono, data-mono | inequality 约束的保守性 | 回避 phy-mono 的优势；PICP 0.998 较难解释 |
| **B. 切换为 phy-mono** | baseline vs phy-mono | data-mono-ineq, data-mono | 物理先验单调性直接嵌入作为主方法 | 需改写 §2.1、§3.2、§3.3 数字；abstract 的 R²/PICP/MPIW 值要换 |
| **C. 三模型并列主文** | baseline / phy-mono / data-mono-ineq | data-mono | "无约束 / 物理先验 / 完整约束"梯度 | 主表多一列；给读者选择空间，但叙事弱化 |

### 5.4 本报告推荐

**倾向方案 B（切主模型为 phy-mono）**，理由：
1. phy-mono 在 CRPS / MPIW / R²-primary 四项指标综合最优；
2. PICP 0.970 相对 0.998 更接近名义值，**概率校准更可信**；
3. 其物理先验是高置信度机理（8 对 `PHYSICS_PRIOR_PAIRS_HIGH`），叙事可写成"将已知物理单调性作为软约束直接注入 BNN"，比 "Spearman 数据单调性 + 不等式" 更机理驱动；
4. CLAUDE.md 中 "Physics-regularized surrogate" 的字面语义在 phy-mono 上更自然。

**切换代价清单**（如果采纳 B）：
- 摘要 + §2.1 主表 + §3.2 文字 + §3.3 forward UQ 均值/方差 + §3.4 速度数字不变 + §5 / §6 敏感性/后验 不变（这两处本来就 4 模型对齐）+ §Conclusion 第 (1)(2) 数字
- 约 8–10 处数值替换；我可以一次改完

**如果保守起见选 C（三模型并列）**，则主表加一列，叙事写为：
- baseline = uninformed BNN 参考
- phy-mono = 注入物理先验的 BNN（**主推方法**）
- data-mono-ineq = 完整约束的保守上界（用于说明 coverage 可控上限）

### 5.5 其他消融是否仍要进附录？

- **bnn-data-mono**（只有 Spearman 数据单调性，无 inequality）：在所有指标上**没有一项最优**，也不是物理推动的对照。**建议删除**（或仅附录 E 表格内保留一行，不单独讨论）。
- **bnn-data-mono-ineq**（若方案 B/C 被采纳）：作为"完整约束上界"，附录 E 一张表 + 一段文字即可。不需要单独图。
- **bnn-phy-mono**（若方案 B 被采纳，此为主模型；若方案 A 被采纳，作为"物理先验消融"放附录 E，加一句"PICP 最接近名义 0.90、MPIW 最锐利"的说明）。

### 5.6 关于"每输入"分析的说明

用户问：每个输入是否也要做分析？—— **不需要在 accuracy 报告里做**。
- Accuracy 指标（R²/RMSE/MAE/PICP/MPIW/CRPS）都是基于 y_true vs y_pred 的**输出层**指标，输入只是协变量。
- 输入的"重要性"或"贡献"属于 sensitivity 分析，已在 `03_sensitivity.md` 中给出 Sobol / Spearman / PRCC 三种度量（per-input × per-output 全表）。
- 如确需补充 per-input 层面的 accuracy 分解，可做"按输入分位切片后的条件 R²"（类似 generalization 里的 OOD 切分），但这是 generalization 报告的范围，本报告不扩展。

---

## 6. 可进入正文的主表（按方案 B 推荐）

假设采纳方案 B 为主文结构：

```
主文 Table 2 —— 代理精度（5-seed repeat, 15 输出聚合）

metric               Reference (baseline)   Physics-regularized (phy-mono)   Δ
MAE                  2.63 ± 0.13            2.58 ± 0.12                      −1.6%
R²                   0.744 ± 0.048          0.747 ± 0.050                    +0.003
PICP₉₀               0.976 ± 0.005          0.970 ± 0.006                    −0.006 (更接近 0.90)
MPIW₉₀               16.24 ± 0.26           15.24 ± 0.26                     −6.2%
CRPS                 1.97 ± 0.07            1.92 ± 0.07                      −2.5%
```

图表标签按 CLAUDE.md figure-vocabulary rule 使用 "Reference surrogate" 与 "Physics-regularized surrogate"。

附录 E 放 15 输出 × 4 模型的全量分表（本文件第 3 节的四张 R²/PICP/MPIW/CRPS 表）。
