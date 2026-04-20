# BNN Surrogate 实验结论总览

> 生成日期: 2026-04-18
> 涵盖: bnn0414 全部 P0/P1 实验 + 补充实验 A-F
> 主线对比: baseline (无约束 BNN) vs phy-mono (物理先验单调性 BNN)

---

## 一、核心结论

### 1. 预测精度：BNN 四模型精度相当，物理约束未降精度
- 四模型 RMSE 均在 3.40–3.53 范围，R2 在 0.73–0.75
- **phy-mono 略优**: RMSE=3.41, CRPS=1.92 (全模型最低)
- data-mono-ineq 精度最差 (RMSE=3.53, CRPS=2.21)，但 PICP 最高 (0.986)
- 5-seed 重复实验显示 RMSE std ~0.12–0.14，结果稳定

### 2. 不确定性校准：BNN 显著优于传统方法
- **BNN ECE**: stress 0.13, 温度/keff 0.04–0.15
- **MC-Dropout ECE**: 0.12–0.20; **Deep Ensemble ECE**: 0.11–0.20
- BNN 在温度输出 R2 ~0.75 vs 外部基线 ~0.59，优势显著
- BNN 在 stress 上 R2 差距不大 (0.93 vs 0.93)，但校准明显更好

### 3. 物理一致性：所有模型 high-confidence 单调性完美满足
- 高置信度物理单调对: **全部 4 模型 0% 违反率**
- 中等置信度 SS316_alpha → fuel_temp 存在 ~36-54% 违反 (所有模型共有，物理约束弱)
- 不等式约束: 全部 4 模型 0% 违反

### 4. 不确定性分解：aleatoric 主导，stress 和 wall 的 epistemic 最高
- 温度输出: epistemic 仅占 10–13%
- Stress: epistemic 占 28–34%
- Wall expansion: epistemic 占 34–42%
- phy-mono 相比 baseline 在温度上 epistemic 降低 ~2%，在 stress 上略升

### 5. 计算加速：~1.7×10⁸ 倍 (batch 模式)
- HF 单次 2266s; BNN batch 0.013ms/sample
- 以 CI=0.005 精度计: N~20,627 样本, BNN 0.28s vs HF 541 天
- 即便 single-MC 模式 (0.013s/sample), speedup 仍有 ~1.76×10⁵

### 6. 后验推断 MCMC 诊断：收敛性优良
- 4 chains × 18 cases × 4 models
- **rhat_split_rank ≤ 1.017** (远低于 1.1 阈值)
- **ESS_min ≥ 352** (可接受)
- **acceptance rate 0.59–0.64** (MH 理想范围)

### 7. Sobol 敏感性已收敛
- Stress: E_intercept S₁ = 0.54–0.57 (主导), alpha_base S₁ ~0.15–0.19
- keff: alpha_base S₁ = 0.77–0.78 (主导), alpha_slope S₁ ~0.19–0.20
- N_base=2048 起 S₁ 已基本稳定，8192 处 std < 0.04

### 8. OOD 校准：epistemic 正确膨胀，覆盖率维持
- OOD 区域 epistemic 标准差增加 7–21%
- 90% PICP: in-dist 0.97 → OOD 0.98 (甚至略增，因为区间同时变宽)
- BNN 的 OOD 行为符合贝叶斯预期

### 9. 先验敏感性：canonical prior 适中，tight 过强
- diffuse (σ→2σ): 后验基本不变 (KL ~0.15–0.22)，coverage 100%
- tight (σ→0.5σ): coverage 降至 50–83%，KL 升至 0.64–1.28，先验过强
- flat uniform: coverage 100%，但后验更宽 (KL ~0.24–0.38)
- shift_pos/neg: 中等 KL (0.06–0.36)，coverage 67–100%

### 10. 数据效率：25% 训练数据即可达到 >96% 的完整精度
- 25% (507 samples): RMSE ~4.93, R2 ~0.77
- 100% (2029 samples): RMSE ~4.62, R2 ~0.78
- 精度提升主要在 25%→50%，之后趋于饱和

---

## 二、需要特别注意的点

### 与论文可能不一致之处

1. **R2 值偏低**: 全局 R2 ~0.75 看似不高，但这是跨 15 个输出的平均值。个别输出 (wall, keff) R2 > 0.99，stress R2 ~0.93，温度 R2 ~0.59 拉低了均值。**论文中如引用 R2，应区分 per-output 还是 global average。**

2. **SS316_alpha → fuel_temp 单调性违反 ~36-54%**: 这是标注为 "medium confidence" 的物理对，所有模型都违反。如果论文声称"物理约束全部满足"，需要加限定词 "high-confidence pairs"。

3. **data-mono-ineq 校准不佳**: ECE 高于 baseline (stress ECE: ineq 0.15 vs baseline 0.13)。如果论文推 data-mono-ineq 为"最佳模型"，需要重新定位。 **已按之前决定 demote 到附录。**

4. **外部基线在 stress 上 R2~0.93 与 BNN 差距不大**: BNN 的优势主要体现在温度预测和校准质量，而非 stress 预测精度。论文叙述应侧重 "well-calibrated UQ" 而非 "dramatically better point prediction"。

5. **Data efficiency 曲线比较平坦**: 25% 数据就达到 96% 精度，这可以正面解读 (robust)，但也意味着 BNN 对大量数据的利用不够充分。

6. **Prior sensitivity 的 tight 变体 coverage 50–83%**: 说明先验选择确实重要，canonical prior 是合理的但 tight prior 会过度约束。论文应讨论先验选择的敏感性。

### 论文支撑强的结论

- 物理约束不损精度 (phy-mono ≈ baseline RMSE)
- BNN 优于 MC-Dropout / Deep Ensemble 在温度预测和校准
- MCMC 收敛性优良 (rhat, ESS, acceptance)
- OOD epistemic 正确膨胀
- 计算加速 ~10⁸ 倍
- Sobol 收敛性充分

---

## 三、实验完成状态

| 编号 | 实验 | 状态 | 产出位置 |
|------|------|------|----------|
| P0-1 | External baselines (MC-Dropout, Deep Ensemble) | Done | code/models/{mc-dropout,deep-ensemble}/ |
| P0-2 | Multi-α calibration + PIT + NLL + IS | Done | results/accuracy/ |
| P0-3 | MCMC diagnostics (4-chain rhat + ESS) | Done | posterior/*/diagnostics/ |
| P0-4 | Monotonicity violation rate | Done | results/physics_consistency/ |
| P0-5 | Budget-matched risk comparison | Done | results/speed/ |
| P1-6 | Posterior predictive check (PPC) | Done | (on server) |
| P1-7 | Prior sensitivity sweep | Done (phy-mono) | posterior/bnn-phy-mono/prior_sensitivity/ |
| P1-8 | Data efficiency curve | Done | results/data_efficiency/ |
| P1-9 | Noise sensitivity | Done (phy-mono) | posterior/bnn-phy-mono/noise_sensitivity/ |
| A | External baseline full UQ pipeline | Done | results/accuracy/external_baseline_*.csv |
| B | MCMC trace + rank plots | Done | results/posterior/trace_*.png, rank_*.png |
| C | Sobol convergence curve | Done | results/sensitivity/sobol_convergence.csv |
| D | Multi-seed repeat eval summary | Done | results/accuracy/repeat_eval_*.csv |
| E | Epistemic vs aleatoric decomposition | Done | results/uncertainty_decomposition/ |
| F | OOD calibration check | Done | results/ood/ |
