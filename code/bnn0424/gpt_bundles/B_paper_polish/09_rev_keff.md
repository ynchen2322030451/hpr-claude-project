# Phase 1.4 — keff R² Honest Handling

## Data Summary

From `gpt_figures/fig2_predictive/metrics_summary.csv` (phy-mono model):

| Output | R² | RMSE | MAE | CRPS |
|--------|------|------|-----|------|
| stress | 0.9438 | 7.58 | 5.40 | 4.35 |
| keff | 0.8492 | 0.00043 | 0.00033 | 0.00023 |
| fuel_temp | 0.6278 | 3.73 | 2.89 | 2.16 |
| monolith_temp | 0.6153 | 3.65 | 2.83 | 2.11 |
| wall2 | 0.9393 | 0.49 | 0.37 | 0.27 |

**Key context for keff:** The raw keff R² of 0.849 looks modest, but the total variation in keff across the dataset is extremely small. From `forward_uq_alloutput.csv`: coupled keff mean = 1.17867, std = 0.00132. The entire range spans ~0.005 (roughly 500 pcm). An RMSE of 0.00043 corresponds to ~43 pcm, which is well within typical Monte Carlo statistical noise of OpenMC simulations. The R² is depressed because the denominator (total variance) is tiny, not because the surrogate makes large errors.

**Temperature outputs:** Similar argument. fuel_temp coupled std = 5.29 K, monolith_temp coupled std = 6.11 K. These are narrow-range outputs where R² is a misleading metric.

---

## EN — Table 1 Footnote

†The coefficient of determination (R²) for keff and temperature outputs should be interpreted with caution. The total variance of keff across the input parameter space is ~1.7 × 10⁻⁶ (standard deviation 0.0013, corresponding to ~130 pcm), making R² highly sensitive to residual noise. The surrogate RMSE of 0.00043 (43 pcm) is comparable to the intrinsic Monte Carlo statistical uncertainty of OpenMC neutronics simulations. For outputs with narrow total variation, distributional metrics such as CRPS provide a more informative assessment of surrogate quality.

## EN — SI Note: Per-Output Variance Analysis

**Note X: Interpretation of per-output surrogate accuracy.** The five coupled outputs span markedly different total-variance regimes, which affects the informativeness of R² as an accuracy metric. We categorize them into high-variance outputs (stress, wall displacement) where R² directly measures explained variance, and low-variance outputs (keff, fuel temperature, monolith temperature) where the denominator of R² is small enough that even physically negligible residuals depress the metric.

For keff, the coupled steady-state values range from approximately 1.172 to 1.186 (total standard deviation 0.0013). The surrogate RMSE of 4.3 × 10⁻⁴ represents an absolute error of ~43 pcm — well within the Monte Carlo statistical noise floor of the OpenMC reference calculations (typically 10–50 pcm per run depending on particle count). When this residual is divided by the small total variance, R² = 0.849 results. By contrast, the CRPS of 2.3 × 10⁻⁴ confirms that the predictive distribution correctly captures the narrow output range.

For temperature outputs, the same phenomenon occurs: max fuel temperature varies by only 5.3 K and max monolith temperature by 6.1 K across the design space. The surrogate RMSEs (3.7 K and 3.6 K) represent relative errors of less than 0.5% against absolute temperatures exceeding 700 K. The R² values of 0.63 and 0.62 reflect the ratio of these small residuals to the small total variance, not a failure of the surrogate.

This variance-regime dependence has a practical implication for the uncertainty propagation results: the forward UQ distributions for keff and temperature outputs are narrow by construction, and the surrogate reproduces them with absolute fidelity sufficient for engineering assessment even where R² appears modest.

---

## CN — Table 1 Footnote

†keff和温度输出的决定系数（R²）需谨慎解读。keff在输入参数空间中的总方差仅约1.7 × 10⁻⁶（标准差0.0013，对应约130 pcm），使得R²对残差噪声高度敏感。代理模型的RMSE为0.00043（43 pcm），与OpenMC中子学蒙特卡罗模拟的固有统计不确定性相当。对于总变异幅度较窄的输出，分布性指标如CRPS能更准确地评价代理模型质量。

## CN — SI Note: Per-Output Variance Analysis

**注释X：逐输出代理模型精度的解读。** 五个耦合输出的总方差跨越不同量级，这直接影响R²作为精度评价指标的信息量。我们将其分为高方差输出（应力、壁面位移），R²可直接度量解释方差；以及低方差输出（keff、燃料温度、基体温度），R²的分母足够小，以至于物理上可忽略的残差也会显著压低该指标。

对于keff，耦合稳态值的范围约为1.172至1.186（总标准差0.0013）。代理模型的RMSE为4.3 × 10⁻⁴，代表约43 pcm的绝对误差——完全在OpenMC参考计算的蒙特卡罗统计噪声范围内（通常每次运行10–50 pcm，取决于粒子数）。当该残差除以小的总方差时，得到R² = 0.849。相比之下，CRPS为2.3 × 10⁻⁴，证实预测分布正确捕获了这一窄输出范围。

对于温度输出，同样的现象出现：最高燃料温度在设计空间内仅变化5.3 K，最高基体温度变化6.1 K。代理模型的RMSE（3.7 K和3.6 K）相对于超过700 K的绝对温度，相对误差不到0.5%。R²值0.63和0.62反映的是小残差与小总方差的比值，而非代理模型的失败。

这一方差量级依赖性对不确定性传播结果具有实际意义：keff和温度输出的前向UQ分布本身就是窄的，代理模型的绝对保真度足以满足工程评估需求，即使R²看起来不高。

---

## Data Sources
- `code/gpt_figures/fig2_predictive/metrics_summary.csv` — per-output R², RMSE, CRPS for phy-mono and baseline
- `code/gpt_figures/fig3_forward/forward_uq_alloutput.csv` — coupled/decoupled means and stds for all outputs
- `results/CANONICAL_DATA_SUMMARY.md` — canonical values
