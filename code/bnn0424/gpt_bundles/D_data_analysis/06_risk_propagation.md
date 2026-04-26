# 05 — Risk propagation

源：`experiments/risk_propagation/<model>/{D1_nominal_risk, D2_case_risk, D3_coupling}.{csv,json}` + `risk_manifest.json`。
config：N=20000 蒙特卡洛；阈值扫描 {110, 120, 131} MPa；σ_k 倍数 {0.5, 1.0, 1.5, 2.0}；预测包含 aleatoric + epistemic。

## D1 — 标称设计点 (σ_k=1.0)

| 模型 | stress_mean | stress_std | P>110 | P>120 | **P>131** |
|---|---|---|---|---|---|
| bnn-baseline | 164.21 | 33.75 | 0.957 | 0.913 | **0.841** |
| bnn-data-mono | 163.73 | 33.45 | 0.958 | 0.918 | 0.845 |
| bnn-phy-mono | 163.55 | 33.62 | 0.959 | 0.917 | 0.840 |
| bnn-data-mono-ineq | 162.53 | **35.53** | 0.941 | 0.893 | **0.816** |

## σ_k 扫描 @ τ=131 MPa

| 模型 | σk=0.5 | σk=1.0 | σk=1.5 | σk=2.0 |
|---|---|---|---|---|
| bnn-baseline | 0.946 | 0.841 | 0.765 | 0.708 |
| bnn-data-mono | 0.952 | 0.845 | 0.767 | 0.685 |
| bnn-phy-mono | 0.960 | 0.840 | 0.741 | 0.683 |
| bnn-data-mono-ineq | 0.901 | **0.816** | 0.759 | **0.725** |

## 解读

- **P(σ>131) 在四模型间相差仅 0.03**，data-mono-ineq 最保守（0.816），三者（baseline/data-mono/phy-mono）几乎并列（0.840–0.845）。
- **data-mono-ineq 的 stress_std 最大**（35.5 vs ~33.6），说明它把更多 epistemic 不确定性推进了预测分布 —— 与 fixed_eval 的 MPIW 结果一致。
- **σ_k 扫描**：当人为把 aleatoric 放大 2×，data-mono-ineq 仍能保持 P_exceed = 0.725，**下降最慢**（斜率最小）；baseline 从 0.946→0.708；phy-mono 降到 0.683 最低。这支持"data-mono-ineq 在 noise 误设下更鲁棒"的定性叙述。
- `D1_nominal_risk.json` **不保存 P_exceed 的 bootstrap CI**；若正文要报误差棒，需要重跑或事后 bootstrap（20000 样本下 0.84 附近的 ±3σ 约 ±0.007，可在报告中手算写作"误差 <1 个百分点"）。

## 写作建议
- 正文主图：四阈值对四模型的堆叠柱状图 —— 推荐 `baseline` 与 `data-mono-ineq` 放前景，另外两个放附录 E。
- 主文用"Reference surrogate" / "Physics-regularized surrogate" 标签（CLAUDE.md 术语）。
- 不要写"P_exceed 统计显著差异"：在没有 bootstrap CI 的情况下这种断言没有证据。可写为"P(σ>131) 下降约 2.5 个百分点（0.841 → 0.816），其中 Physics-regularized surrogate 呈现更宽预测区间（MPIW +30%）。"
