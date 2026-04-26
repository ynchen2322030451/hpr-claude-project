from matplotlib import pyplot as plt
'''
材料参数敏感性分析脚本
功能：通过 Sobol 方法分析各材料参数对输出结果 (keff) 的敏感性
主要步骤：
1. 基于 Sobol 序列生成材料参数的采样样本
2. 调用 generater 模块计算对应样本的输出参数 (keff)
3. 利用 SALib 库计算 Sobol 指数，评估各参数的敏感性
4. 保存输入输出数据及敏感性分析结果
关键设置：
- 样本数量：n_samples = 128*64（基于 Sobol 序列生成）
- 材料参数：从 material_config 导入（包含参数名、均值、标准差）
- 扰动方式：采用百分比扰动（10%）
- 结果保存：输入输出数据保存为 training_data.npy，Sobol 指数保存为 txt 文件
主要方法：
- Sobol 序列采样：用于生成均匀分布的参数样本，适合全局敏感性分析
- Sobol 指数分析：量化各参数及其交互作用对输出的影响程度
'''

import numpy as np
from SALib.sample import sobol as sobolsample
from SALib.analyze import sobol
from scipy.stats import norm
from SALib.plotting.bar import plot as barplot
import generater
from scipy.stats import qmc
import os
from material_config import MATERIAL_KEYS, MATERIAL_MEAN_VALUES, MATERIAL_STD_DEV_VALUES

# os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

# ===== 统一材料参数顺序、均值、标准差，只在此处维护 =====


def output_func(inputs, use_percentage=False, percentage=0.1):
    """
    定义输出参数计算函数，调用 generater 模块进行计算，并保存训练数据。
    """
    shape = inputs.shape
    counts = shape[0]  # 样本数量
    keff, original_path = generater.start_generater(inputs, counts, use_percentage, percentage)

    # 保存输入和输出数据为训练集
    training_data = {
        'inputs': inputs,
        'outputs': keff
    }
    np.save(os.path.join(original_path, 'training_data.npy'), training_data)  # 保存为 NumPy 文件

    return keff, original_path

# 设置蒙特卡洛模拟的样本数量和输入参数个数
n_samples = 128*64 # 样本数量

problem = {
    'num_vars': len(MATERIAL_KEYS),
    'names': MATERIAL_KEYS,
    'bounds': [[MATERIAL_MEAN_VALUES[k], MATERIAL_STD_DEV_VALUES[k]] for k in MATERIAL_KEYS],
    'dists': ['norm'] * len(MATERIAL_KEYS)
}

# 生成 Sobol 序列
param_values = sobolsample.sample(problem, n_samples, calc_second_order=False)

# 可选：将材料参数传递给 fenics_thermal_TE
material_params = {k: param_values[:, i] for i, k in enumerate(MATERIAL_KEYS)}

# 使用百分比扰动方式调用 output_func
output, original_path = output_func(param_values, use_percentage=True, percentage=0.1)



# 计算 Sobol 指数
sobol_indices = sobol.analyze(problem, output.reshape(-1))

# 输出 Sobol 指数结果
for key, value in sobol_indices.items():
    print(f"{key}: {value}")

# 定义保存结果的路径
save_file_path = original_path

# 保存 Sobol 指数和相关数据到文件
for key, value in sobol_indices.items():
    np.savetxt(save_file_path + f'108_{key}.txt', value)
