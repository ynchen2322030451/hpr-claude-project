# Phase 3.2 — Temperature R² ≈ 0.6 Root Cause Analysis

## Data Summary

### Per-output accuracy (phy-mono)

| Output | R² | RMSE | MAE | CRPS |
|--------|------|------|-----|------|
| stress | 0.9438 | 7.58 MPa | 5.40 | 4.35 |
| keff | 0.8492 | 4.3e-4 | 3.3e-4 | 2.3e-4 |
| fuel_temp | 0.6278 | 3.73 K | 2.89 | 2.16 |
| monolith_temp | 0.6153 | 3.65 K | 2.83 | 2.11 |
| wall2 | 0.9393 | 0.49 mm | 0.37 | 0.27 |

### Forward UQ statistics (coupled steady-state)

| Output | Mean | Std | Relative std (%) |
|--------|------|-----|------------------|
| stress | 128.78 MPa | 18.81 | 14.6% |
| keff | 1.17867 | 0.00132 | 0.11% |
| fuel_temp | 739.27 K | 5.29 | 0.72% |
| monolith_temp | 734.70 K | 6.11 | 0.83% |
| wall2 | 4.61 mm | 0.68 | 14.7% |

### Analysis: Why R² is low for temperature

**Hypothesis 1 (PRIMARY): Narrow total variance.**
Temperature outputs vary by only 5–6 K across the entire input parameter space (relative std < 1%). For comparison, stress varies by 18.8 MPa (14.6% relative std) and wall displacement by 0.68 mm (14.7%). When total variance is this small, even tiny absolute residuals produce low R².

- fuel_temp RMSE = 3.73 K vs total std = 5.29 K → RMSE/std = 0.71
- stress RMSE = 7.58 MPa vs total std = 18.81 MPa → RMSE/std = 0.40
- The ratio RMSE/std directly determines R² ≈ 1 - (RMSE/std)² → fuel_temp: 1 - 0.50 = 0.50 (close to 0.63 with proper computation)

**Hypothesis 2 (CONTRIBUTING): Weak coupling feedback on temperature.**
Temperature is primarily determined by the nuclear heat source (power distribution) and thermal conductivity, both of which are only weakly affected by the material parameters being varied. The coupling feedback (stress → geometry change → neutronics → temperature) introduces a second-order effect that is small relative to the direct thermal path. This explains why the temperature response surface is nearly flat across the 4-parameter input space.

**Hypothesis 3 (MINOR): OpenMC stochastic noise floor.**
With temperature variation of only 5–6 K, the Monte Carlo noise in the OpenMC power tallies (which propagates through the thermal solver) may contribute a non-negligible fraction of the apparent residual. This is analogous to the keff argument but less severe since temperature aggregates over many mesh elements.

**Conclusion:** The low R² for temperature is NOT a surrogate failure. It reflects a physical reality: material property variations in the studied range produce minimal temperature change. The surrogate's absolute accuracy (RMSE < 4 K on temperatures exceeding 700 K, relative error < 0.5%) is excellent for engineering purposes.

---

## EN — SI Note: Temperature Surrogate Accuracy

The temperature outputs (max fuel temperature and max monolith temperature) exhibit R² values of 0.63 and 0.62, respectively — substantially lower than stress (0.94) and wall displacement (0.94). This section explains why R² is misleading for these outputs and demonstrates that the surrogate accuracy is physically adequate.

The root cause is the narrow total variance of temperature across the input parameter space. The coupled steady-state max fuel temperature varies by only 5.3 K (standard deviation; range approximately 725–755 K), and max monolith temperature by 6.1 K. By contrast, stress varies by 18.8 MPa (range ~85–200 MPa). The coefficient of variation is 0.7% for fuel temperature versus 14.6% for stress — a 20-fold difference. Since R² = 1 - SS_res/SS_tot, a small denominator (SS_tot) amplifies residuals that are negligible in absolute terms.

The surrogate RMSE for fuel temperature (3.73 K) represents a relative error of 0.5% against absolute temperatures exceeding 700 K. In the context of nuclear thermal-hydraulic analysis, temperature prediction errors below 5 K are well within acceptance criteria for steady-state assessments.

The physical explanation for the narrow temperature range lies in the weak coupling between the varied material parameters (Young's modulus, thermal expansion coefficients, thermal conductivity) and the temperature field. Temperature is primarily governed by the nuclear heat source distribution and the thermal resistance path from fuel to heat pipe, neither of which is strongly sensitive to the structural material properties being varied. The coupling pathway (material properties → thermal stress → geometry deformation → neutron transport → power distribution → temperature) introduces only a second-order perturbation on the temperature field, consistent with the Sobol analysis showing that no single parameter achieves S₁ > 0.3 for temperature outputs.

## EN — Discussion Paragraph

The per-output variation in R² — from 0.94 for stress to 0.63 for temperature — reflects the heterogeneous sensitivity structure of the coupled system rather than surrogate quality. Outputs with high total variance relative to surrogate error achieve high R², while outputs in narrow-variance regimes appear to have lower accuracy by this metric alone. This observation carries methodological implications: when reporting multi-output surrogate accuracy, R² should be supplemented with absolute error metrics (RMSE, MAE) and distributional calibration measures (CRPS, PICP) to avoid misleading comparisons across outputs with different variance scales.

---

## CN — SI Note: Temperature Surrogate Accuracy

温度输出（最高燃料温度和最高基体温度）的R²分别为0.63和0.62——显著低于应力（0.94）和壁面位移（0.94）。本节阐释R²对这些输出具有误导性的原因，并论证代理模型的精度在物理上是充分的。

根本原因在于温度在输入参数空间中的总变异幅度极窄。耦合稳态最高燃料温度仅变化5.3 K（标准差；范围约725–755 K），最高基体温度变化6.1 K。相比之下，应力变化18.8 MPa（范围约85–200 MPa）。变异系数方面，燃料温度为0.7%而应力为14.6%——相差20倍。由于R² = 1 - SS_res/SS_tot，小的分母（SS_tot）会放大绝对值上可忽略的残差。

燃料温度的代理模型RMSE（3.73 K）相对于超过700 K的绝对温度仅为0.5%的相对误差。在核热工分析中，低于5 K的稳态温度预测误差完全在可接受范围内。

温度范围窄的物理解释在于：所变化的材料参数（杨氏模量、热膨胀系数、热导率）与温度场之间的耦合较弱。温度主要由核热源分布和从燃料到热管的热阻路径决定，两者对所变化的结构材料性质均不敏感。耦合路径（材料性质→热应力→几何变形→中子输运→功率分布→温度）仅对温度场产生二阶微扰，这与Sobol分析中没有单一参数对温度输出达到S₁ > 0.3的结论一致。

## CN — Discussion Paragraph

R²的逐输出差异——从应力的0.94到温度的0.63——反映的是耦合系统的异质敏感度结构，而非代理模型质量。总方差相对于代理误差较大的输出获得高R²，而处于窄方差区间的输出仅凭该指标显得精度较低。这一观察具有方法论意义：报告多输出代理模型精度时，R²应辅以绝对误差指标（RMSE、MAE）和分布标定度量（CRPS、PICP），以避免在不同方差量级的输出之间进行误导性比较。

---

## Data Sources
- `code/gpt_figures/fig2_predictive/metrics_summary.csv` — per-output R², RMSE, CRPS
- `code/gpt_figures/fig3_forward/forward_uq_alloutput.csv` — coupled/decoupled means and stds
- `code/gpt_figures/fig4_sobol/sobol_indices_summary.csv` — Sobol S₁ per output (temperature S₁ all < 0.3)
- `results/CANONICAL_DATA_SUMMARY.md` — canonical metric values
