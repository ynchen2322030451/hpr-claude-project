# 06 — Generalization / OOD

源：`experiments/generalization/<model>/{ood_summary.csv, ood_per_output.csv, generalization_manifest.json}`。
OOD 定义：在 {E_intercept, alpha_base, nu, alpha_slope} 的尾部分位作为 OOD 子集（约 600 样本），其余 ~2450 样本为 in-dist。

## 表（E_intercept 拆分为例；其余 3 个 OOD 特征走势一致）

| 模型 | in-dist MAE | OOD MAE | in-dist PICP | OOD PICP | in-dist R² | OOD R² |
|---|---|---|---|---|---|---|
| bnn-baseline | 2.632 | 2.721 | 0.974 | 0.988 | 0.668 | 0.769 |
| bnn-data-mono | 2.604 | 2.917 | 0.973 | 0.986 | 0.670 | 0.768 |
| bnn-phy-mono | 2.596 | 2.741 | 0.967 | 0.983 | 0.672 | 0.766 |
| bnn-data-mono-ineq | 2.709 | 2.849 | 0.986 | 0.988 | 0.659 | 0.750 |

## 解读

- **OOD 下 PICP 全部 ≥0.98**，覆盖在 OOD 上反而更高 —— 说明 BNN 的 epistemic 成分在尾部增大，区间扩张足以吸收分布外样本。
- **OOD R² > in-dist R²** 不是"在 OOD 上更准"的证据。可能的原因：OOD 子集在目标方向上方差更大，R²=1−SSE/SST 的分母 SST 大，对同量级 MAE 抬高 R²。正文**不应**写"OOD 泛化更好"。推荐表达：
  > "Even on out-of-distribution subsets along the four input features, the predictive interval coverage remains above 98%, and the point error (MAE) increases modestly by 3–12%, suggesting that the BNN's epistemic variance correctly inflates beyond the training envelope."
- **data-mono-ineq**：in-dist MAE 最高，但 PICP 最高 —— 与 fixed_eval 一致的保守结论。
- 四个 OOD 特征拆分的相对次序一致，建议正文只放一个（最典型的 E_intercept），其余三个入附录。

## 写作建议
- 主图：四个模型在"in-dist vs OOD"的 MAE 与 PICP 对比柱状，OOD 维度选 E_intercept；正文说明"其余三个输入方向在附录 E.3 提供"。
- 不要把"OOD 子集"叫 "extrapolation" —— 这里只是单维度的尾部 10–20%，不是真正的外推。用 "tail subsets" / "尾部子集" 更准确。
