# Material property configuration for FEniCS simulations
# 0916：10% TO 30%
MATERIAL_KEYS = [
    'E_slope', 'E_intercept', 'nu', 'alpha_base', 'alpha_slope',
    'SS316_T_ref', 'SS316_k_ref', 'SS316_alpha', 'SS316_scale'
]
MATERIAL_MEAN_VALUES = {
    'E_slope': -7e7,
    'E_intercept': 2e11,
    'nu': 0.31,
    'alpha_base': 1e-5,
    'alpha_slope': 5e-9,
    'SS316_T_ref': 923.15,
    'SS316_k_ref': 23.2,
    'SS316_alpha': 1/75,
    'SS316_scale': 1/100
}
MATERIAL_STD_DEV_VALUES = {
    'E_slope': 7e6,
    'E_intercept': 2e10,
    'nu': 0.031,
    'alpha_base': 1e-6,
    'alpha_slope': 5e-10,
    'SS316_T_ref': 92.315,
    'SS316_k_ref': 2.32,
    'SS316_alpha': 1/750,
    'SS316_scale': 0.001
}
