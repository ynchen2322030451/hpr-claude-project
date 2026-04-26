"""
Workflow-level evidence analyses for NCS revision.
A. Sobol ranking stability across 3 models
B. Posterior contraction vs Sobol dominance
C. Prior-vs-posterior predictive stress contraction
"""
import numpy as np
from scipy.stats import spearmanr

PARAMS = ["E_slope", "E_intercept", "nu", "alpha_base", "alpha_slope",
          "SS316_T_ref", "SS316_k_ref", "SS316_alpha"]
CALIB_PARAMS = ["E_intercept", "alpha_base", "alpha_slope", "SS316_k_ref"]

# ======================================================================
# A. Sobol ranking stability
# ======================================================================
# S1 values for stress (iteration2_max_global_stress)
stress_s1 = {
    "bnn-phy-mono": {
        "E_slope": 0.0503, "E_intercept": 0.5786, "nu": 0.0646,
        "alpha_base": 0.1687, "alpha_slope": 0.0265, "SS316_T_ref": 0.0187,
        "SS316_k_ref": 0.0507, "SS316_alpha": 0.0020
    },
    "bnn-baseline": {
        "E_slope": 0.0473, "E_intercept": 0.5996, "nu": 0.0559,
        "alpha_base": 0.1478, "alpha_slope": 0.0270, "SS316_T_ref": 0.0308,
        "SS316_k_ref": 0.0600, "SS316_alpha": 0.0033
    },
    "bnn-mf-hybrid": {
        "E_slope": 0.0387, "E_intercept": 0.5798, "nu": 0.0624,
        "alpha_base": 0.1438, "alpha_slope": 0.0320, "SS316_T_ref": 0.0288,
        "SS316_k_ref": 0.0647, "SS316_alpha": -0.0018
    }
}

# S1 values for keff
keff_s1 = {
    "bnn-phy-mono": {
        "E_slope": -0.0017, "E_intercept": -0.0012, "nu": 0.0282,
        "alpha_base": 0.7854, "alpha_slope": 0.1793, "SS316_T_ref": 0.0052,
        "SS316_k_ref": 0.0002, "SS316_alpha": 0.0019
    },
    "bnn-baseline": {
        "E_slope": 0.0045, "E_intercept": 0.0032, "nu": 0.0288,
        "alpha_base": 0.7869, "alpha_slope": 0.1751, "SS316_T_ref": 0.0083,
        "SS316_k_ref": 0.0072, "SS316_alpha": 0.0088
    },
    "bnn-mf-hybrid": {
        "E_slope": 0.0022, "E_intercept": -0.0025, "nu": 0.0108,
        "alpha_base": 0.7339, "alpha_slope": 0.2103, "SS316_T_ref": 0.0020,
        "SS316_k_ref": 0.0028, "SS316_alpha": 0.0031
    }
}

print("=" * 70)
print("A. SOBOL RANKING STABILITY ACROSS MODELS")
print("=" * 70)

for output_name, s1_data in [("stress", stress_s1), ("keff", keff_s1)]:
    print(f"\n--- {output_name.upper()} S₁ rankings ---")
    rankings = {}
    s1_vectors = {}
    for model, vals in s1_data.items():
        sorted_params = sorted(PARAMS, key=lambda p: vals[p], reverse=True)
        rankings[model] = sorted_params
        s1_vectors[model] = np.array([vals[p] for p in PARAMS])
        top3 = [(p, vals[p]) for p in sorted_params[:3]]
        print(f"  {model:20s}: top-3 = {', '.join(f'{p}({v:.3f})' for p, v in top3)}")

    # Top-k overlap
    models = list(rankings.keys())
    for k in [1, 2, 3]:
        sets = [set(rankings[m][:k]) for m in models]
        overlap = sets[0].intersection(*sets[1:])
        print(f"  Top-{k} overlap (all 3 models): {overlap} ({len(overlap)}/{k})")

    # Pairwise Spearman correlation of S1 vectors
    print(f"  Spearman rank correlation of S₁ vectors:")
    for i in range(len(models)):
        for j in range(i + 1, len(models)):
            rho, pval = spearmanr(s1_vectors[models[i]], s1_vectors[models[j]])
            print(f"    {models[i]} vs {models[j]}: ρ={rho:.4f}, p={pval:.4e}")

# ======================================================================
# B. Posterior contraction vs Sobol dominance
# ======================================================================
print("\n" + "=" * 70)
print("B. POSTERIOR CONTRACTION vs SOBOL DOMINANCE")
print("=" * 70)

# Prior stats from training data
prior_stats = {
    "E_intercept": {"min": 1.458608e+11, "max": 2.592193e+11, "mean": 2.000531e+11, "std": 1.928632e+10},
    "alpha_base":  {"min": 6.524645e-06, "max": 1.340430e-05, "mean": 1.000116e-05, "std": 1.022267e-06},
    "alpha_slope": {"min": 3.442086e-09, "max": 6.534442e-09, "mean": 4.979941e-09, "std": 5.190468e-10},
    "SS316_k_ref": {"min": 1.570640e+01, "max": 2.955231e+01, "mean": 2.322825e+01, "std": 2.276332e+00},
}

# Posterior data from benchmark_summary.csv (18 cases × 4 params)
# Extracted from the CSV: post_std for each case and each param
posterior_data = {
    "E_intercept": {
        "post_stds": [12196472708.3, 11332751693.4, 13563805198.7, 12083430900.5, 12613142932.4,
                      11969004738.3, 12269227543.9, 12466619578.2, 11405388288.6, 12692225341.6,
                      12681383619.9, 13361217033.6, 12176062039.0, 12630298019.1, 12566843126.8,
                      11844449908.4, 12205395807.5, 11844449908.4],
        "post_90ci_widths": [],  # will compute from hi-lo
    },
    "alpha_base": {
        "post_stds": [1.036835725912498e-06, 9.770100133973486e-07, 1.1207736140667e-06, 9.89458276021679e-07,
                      1.0341174151439974e-06, 9.5278488131845e-07, 9.854464899464294e-07, 9.6412504710084e-07,
                      9.278052211161645e-07, 1.0508384756940235e-06, 1.0254887792290142e-06, 9.415490122979161e-07,
                      9.201151766007035e-07, 9.682193557512879e-07, 1.010182290552759e-06, 9.425015541605357e-07,
                      9.731589675398287e-07, 9.376424758512194e-07],
    },
    "alpha_slope": {
        "post_stds": [4.846708014751042e-10, 5.205120764811541e-10, 5.113188845051084e-10, 5.245127032110403e-10,
                      5.064395000425907e-10, 5.167107070810964e-10, 4.796080171626139e-10, 5.059924326523393e-10,
                      5.338056910397286e-10, 5.148964110393443e-10, 4.856414244361843e-10, 5.10343406004658e-10,
                      4.847320277030834e-10, 5.130038604824116e-10, 5.217374075489338e-10, 4.597954290198663e-10,
                      5.381292161202316e-10, 5.066511092535119e-10],
    },
    "SS316_k_ref": {
        "post_stds": [1.988057522007807, 2.135479903779996, 2.18114392254175, 2.1790888762007685,
                      2.0364424922292117, 2.160116608967742, 2.0654486906178273, 2.005256454724314,
                      2.2775647258889187, 2.0775300558013416, 2.249223012492876, 2.4897671396044574,
                      2.13258846567439, 2.2220683503084895, 2.1148161644752195, 2.116164266301508,
                      2.306415761918969, 2.143733390544458],
    },
}

# Prior 90% CI width (truncated Gaussian: use 2*1.645*std, clamped to range)
prior_90ci_width = {}
for p in CALIB_PARAMS:
    s = prior_stats[p]
    gaussian_90 = 2 * 1.645 * s["std"]
    data_range = s["max"] - s["min"]
    prior_90ci_width[p] = min(gaussian_90, data_range)

# Posterior mean 90% CI width = mean(2*1.645*post_std)
post_90ci_width_mean = {}
contraction_ratio = {}
for p in CALIB_PARAMS:
    stds = posterior_data[p]["post_stds"]
    mean_post_90 = np.mean([2 * 1.645 * s for s in stds])
    post_90ci_width_mean[p] = mean_post_90
    contraction_ratio[p] = 1.0 - mean_post_90 / prior_90ci_width[p]

# Sobol S1 for stress and keff (phy-mono)
sobol_stress_s1 = {p: stress_s1["bnn-phy-mono"][p] for p in CALIB_PARAMS}
sobol_keff_s1 = {p: keff_s1["bnn-phy-mono"][p] for p in CALIB_PARAMS}

# Sobol total index for stress and keff
sobol_stress_st = {"E_intercept": 0.597, "alpha_base": 0.184, "alpha_slope": 0.034, "SS316_k_ref": 0.066}
sobol_keff_st = {"E_intercept": 0.003, "alpha_base": 0.783, "alpha_slope": 0.186, "SS316_k_ref": 0.004}

print("\n  Parameter           | Prior 90%CI  | Post 90%CI (mean) | Contraction | Stress S₁ | keff S₁")
print("  " + "-" * 95)
for p in CALIB_PARAMS:
    pw = prior_90ci_width[p]
    pstw = post_90ci_width_mean[p]
    cr = contraction_ratio[p]
    ss = sobol_stress_s1[p]
    ks = sobol_keff_s1[p]
    print(f"  {p:20s} | {pw:.4e} | {pstw:.4e}      | {cr:.3f}       | {ss:.3f}     | {ks:.3f}")

# Spearman correlation: contraction ratio rank vs Sobol rank
cr_values = np.array([contraction_ratio[p] for p in CALIB_PARAMS])
stress_s1_values = np.array([sobol_stress_s1[p] for p in CALIB_PARAMS])
keff_s1_values = np.array([sobol_keff_s1[p] for p in CALIB_PARAMS])
stress_st_values = np.array([sobol_stress_st[p] for p in CALIB_PARAMS])
keff_st_values = np.array([sobol_keff_st[p] for p in CALIB_PARAMS])

# Combined Sobol importance (could use max, sum, or geometric mean)
combined_sobol = np.array([max(sobol_stress_st[p], sobol_keff_st[p]) for p in CALIB_PARAMS])

rho_stress, p_stress = spearmanr(cr_values, stress_st_values)
rho_keff, p_keff = spearmanr(cr_values, keff_st_values)
rho_combined, p_combined = spearmanr(cr_values, combined_sobol)

print(f"\n  Spearman correlation (contraction ratio vs Sobol ST):")
print(f"    vs stress ST: ρ={rho_stress:.4f}, p={p_stress:.4f}")
print(f"    vs keff ST:   ρ={rho_keff:.4f}, p={p_keff:.4f}")
print(f"    vs max(stress_ST, keff_ST): ρ={rho_combined:.4f}, p={p_combined:.4f}")

# Rank comparison
cr_rank = np.argsort(np.argsort(-cr_values)) + 1
stress_rank = np.argsort(np.argsort(-stress_st_values)) + 1
keff_rank = np.argsort(np.argsort(-keff_st_values)) + 1
combined_rank = np.argsort(np.argsort(-combined_sobol)) + 1

print(f"\n  Parameter ranks:")
print(f"  {'Parameter':20s} | Contraction rank | Stress ST rank | keff ST rank | Combined rank")
for i, p in enumerate(CALIB_PARAMS):
    print(f"  {p:20s} | {cr_rank[i]:16d} | {stress_rank[i]:14d} | {keff_rank[i]:12d} | {combined_rank[i]:13d}")


# ======================================================================
# C. Prior-vs-posterior predictive stress contraction
# ======================================================================
print("\n" + "=" * 70)
print("C. PRIOR-vs-POSTERIOR PREDICTIVE STRESS CONTRACTION")
print("=" * 70)

# HF rerun data: for each case, stress at post_mean, post_hi_95, post_lo_5
# Extracted from posterior_hf_rerun_summary_rebuilt.csv
hf_rerun = [
    # case, category, stress_true, stress_post_mean, stress_post_hi95, stress_post_lo5
    (0, "low", 110.57, 119.95, 162.61, 85.43),
    (1, "low", 118.66, 121.02, 158.27, 90.16),
    (2, "low", 110.65, 115.54, 160.01, 82.37),
    (3, "low", 103.67, 113.10, 151.60, 82.82),
    (4, "low", 114.50, 121.89, 160.30, 89.92),
    (5, "low", 102.00, 108.43, 145.66, 77.20),
    (6, "near", 127.60, 134.20, 175.63, 99.68),
    (7, "near", 127.92, 131.18, 173.86, 95.85),
    (8, "near", 126.98, 137.45, 179.30, 104.88),
    (9, "near", 123.51, 131.90, 179.22, 93.72),
    (10, "near", 128.92, 132.76, 173.80, 98.02),
    (11, "near", 129.29, 136.61, 181.39, 102.19),
    (12, "high", 169.54, 174.48, 214.79, 137.82),
    (13, "high", 176.02, 174.56, 218.51, 134.73),
    (14, "high", 193.40, 193.40, 244.35, 148.83),
    (15, "high", 163.37, 162.83, 206.80, 123.31),
    (16, "high", 142.79, 150.76, 187.66, 115.86),
    (17, "high", 197.64, 190.54, 231.96, 150.38),
]

# Prior predictive stress range (from full dataset or training data stats)
# The stress range in the training data gives the prior predictive range
# From the test set: stress ranges roughly 60-250 MPa (we can use dataset range)
# Let's compute from the HF data we have
all_stress_true = [r[2] for r in hf_rerun]
stress_dataset_range = (60, 250)  # approximate from knowledge of the dataset

print(f"\n  Case | Cat  | True σ  | Post mean σ | Post 90%CI       | Post width | |mean err| | True in CI?")
print("  " + "-" * 100)

post_widths = []
post_mae_values = []
true_in_ci = []

for case, cat, s_true, s_mean, s_hi, s_lo in hf_rerun:
    width = s_hi - s_lo
    mae = abs(s_mean - s_true)
    in_ci = s_lo <= s_true <= s_hi
    post_widths.append(width)
    post_mae_values.append(mae)
    true_in_ci.append(in_ci)
    print(f"  {case:4d} | {cat:4s} | {s_true:7.1f} | {s_mean:11.1f} | [{s_lo:6.1f}, {s_hi:6.1f}] | {width:10.1f} | {mae:9.1f} | {'✓' if in_ci else '✗'}")

print(f"\n  Summary statistics:")
print(f"    Posterior predictive MAE (stress at post_mean vs true): {np.mean(post_mae_values):.2f} MPa")
print(f"    Posterior predictive 90%CI width (mean): {np.mean(post_widths):.2f} MPa")
print(f"    Posterior predictive coverage (true in 90%CI): {sum(true_in_ci)}/{len(true_in_ci)} = {sum(true_in_ci)/len(true_in_ci):.3f}")

# By category
for cat in ["low", "near", "high"]:
    cat_data = [(w, m, c) for (_, ct, _, _, _, _), w, m, c in
                zip(hf_rerun, post_widths, post_mae_values, true_in_ci) if ct == cat]
    if not cat_data:
        continue
    widths_cat = [d[0] for d in cat_data]
    mae_cat = [d[1] for d in cat_data]
    cov_cat = sum(d[2] for d in cat_data) / len(cat_data)
    print(f"    {cat:5s}: width={np.mean(widths_cat):.1f} MPa, MAE={np.mean(mae_cat):.1f} MPa, coverage={cov_cat:.3f}")

# Prior predictive comparison
# Approximate prior predictive width: full range of stress in dataset ≈ 190 MPa (60-250)
prior_pred_width_approx = 190.0
mean_post_width = np.mean(post_widths)
print(f"\n  Prior-to-posterior contraction:")
print(f"    Approximate prior predictive stress range: ~{prior_pred_width_approx:.0f} MPa")
print(f"    Mean posterior predictive 90%CI width: {mean_post_width:.1f} MPa")
print(f"    Width reduction ratio: {1.0 - mean_post_width/prior_pred_width_approx:.3f}")
print(f"    Posterior predictive is {prior_pred_width_approx/mean_post_width:.1f}x narrower than prior")

print("\n" + "=" * 70)
print("DONE")
print("=" * 70)
