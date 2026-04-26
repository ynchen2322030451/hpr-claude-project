# 04 — Physics consistency (gradient sign)

源：`experiments/physics_consistency/<model>/{gradient_sign_check.csv, gradient_sign_summary.json, physics_vs_data_direction.csv, physics_consistency_manifest.json}`。
实验规模：10 对 (input, output) × 435 评估点；推理模式为 mean-weight deterministic。
(input, output) 对覆盖 {E_intercept, alpha_base, SS316_k_ref} × {iter1, iter2}_{max_global_stress, max_fuel_temp, max_monolith_temp}。

## 结果

| 模型 | n_pairs | frac_gradient_correct | frac_phy_data_agree | n_eval_points |
|---|---|---|---|---|
| bnn-baseline | 10 | 1.000 | 1.000 | 435 |
| bnn-data-mono | 10 | 1.000 | 1.000 | 435 |
| bnn-phy-mono | 10 | 1.000 | 1.000 | 435 |
| bnn-data-mono-ineq | 10 | 1.000 | 1.000 | 435 |

## 解读

- 四模型**全部通过**梯度符号检查（100% / 10 对 / 435 点）。
- **注意**：`_config/run_record_20260415_235341.json` 将 `physics_consistency` 模块对 4 个模型都标为 `fail`。但实际 CSV/JSON 产物都完整且给出 frac_correct = 1.0。最可能的解释：run_record 的 fail 指该模块下游的"出图"或"manifest 校验"步失败，不是梯度检查本身失败。**若要在正文引用，数值结论可信**，但建议先看 `models/<model>/logs/` 或 `logs/` 目录确认 run_record 的 fail 标记来源。
- 因为 4 模型都 100% 通过，**该实验不能区分模型**，只能作为"四个 BNN 变体都不违反物理方向"的背书。若主文要"突出物理正则化的物理合规性"，该指标不足以支撑差异性主张。

## 写作建议
- 进附录：作为 sanity check。
- 正文**不**建议用它来论证"physics-regularized surrogate 比 baseline 更物理"——数据不支持这个差异。
