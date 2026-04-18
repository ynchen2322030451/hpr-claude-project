import datetime
from multiprocessing import Pool
import numpy as np
import matplotlib.pyplot as plt
import os
import change_geo_file
from pyDOE import lhs
from scipy.stats import norm
from material_config import MATERIAL_KEYS, MATERIAL_MEAN_VALUES, MATERIAL_STD_DEV_VALUES

from parameter_perturber import ParameterPerturber, build_perturber_config  # 你可能需要合并这两个文件



def createFolder():
    """
    在当前脚本所在目录下的 output 文件夹中创建一个以当前日期时间命名的子文件夹。
    如果 output 文件夹或子文件夹不存在，则自动创建。
    
    返回:
        str: 创建的子文件夹路径。
    """
    # 获取当前脚本所在目录
    base_path = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(base_path, 'new_output')

    # 确保 output 文件夹存在
    if not os.path.exists(output_path):
        os.mkdir(output_path)

    # 创建以日期时间命名的子文件夹
    now_time = datetime.datetime.now()
    folder_name = datetime.datetime.strftime(now_time, '%Y_%m_%d_%H_%M_%S')
    full_path = os.path.join(output_path, folder_name)

    if not os.path.exists(full_path):
        os.mkdir(full_path)

    return base_path, full_path

def generate_uncertainty_samples(settings_dic):
    """
    根据设置字典生成不确定性样本。
    使用拉丁超立方采样（LHS）方法生成扰动值。
    即使 disturb 为 False，也会传递均值。

    参数:
        settings_dic (dict): 包含参数名称、均值、标准差等信息的设置字典。

    返回:
        dict: 包含每个参数扰动值的字典。
    """
    name_list = settings_dic['name_list']
    samples_dict = {}
    total_count = settings_dic['total_count']

    for param_name in name_list:
        disturb_key = f"{param_name}_disturb"
        mean_key = f"{param_name}_mean"

        mean_value = settings_dic.get(mean_key, 0)
        if settings_dic.get(disturb_key, False):
            std_key = f"{param_name}_std"
            std_value = settings_dic.get(std_key, 1)
            lhs_samples = lhs(1, samples=total_count, criterion='maximin')
            disturbed_values = norm.ppf(lhs_samples, loc=mean_value, scale=std_value).tolist()
            samples_dict[param_name] = disturbed_values
        else:
            # 如果不扰动，直接传递均值
            samples_dict[param_name] = [mean_value] * total_count

    return samples_dict

# 保留 generate_material_params_samples 作为工具函数，但主流程不再调用
def generate_material_params_samples(settings_dic, use_percentage=False, percentage=0.1):
    """
    根据设置字典生成材料参数的扰动样本，支持绝对数值扰动和百分比扰动。
    即使 disturb 为 False，也会传递均值。

    参数:
        settings_dic (dict): 包含材料参数名称、均值、标准差等信息的设置字典。
        use_percentage (bool): 是否使用百分比扰动，默认为 False。
        percentage (float): 如果使用百分比扰动，指定扰动百分比（如 0.1 表示 10%）。

    返回:
        dict: 包含材料参数扰动值的字典。
    """
    material_params = {}
    # 使用全局唯一 MATERIAL_KEYS
    total_count = settings_dic['total_count']

    for key in MATERIAL_KEYS:
        disturb_key = f"{key}_disturb"
        mean_key = f"{key}_mean"

        mean_value = settings_dic.get(mean_key, 0)
        if settings_dic.get(disturb_key, False):
            if use_percentage:
                std_value = mean_value * percentage
            else:
                std_key = f"{key}_std"
                std_value = settings_dic.get(std_key, 1)
            lhs_samples = lhs(1, samples=total_count, criterion='maximin')
            disturbed_values = norm.ppf(lhs_samples, loc=mean_value, scale=std_value).tolist()
            material_params[key] = disturbed_values
        else:
            # 如果不扰动，直接传递均值
            material_params[key] = [mean_value] * total_count

    return material_params

def visualize_uncertainty_samples(samples_result):
    """
    可视化不确定性样本的分布。
    使用 3D 散点图展示 fuel、fuel_D_outer 和 HP_D_outer 的分布。
    
    参数:
        samples_result (dict): 包含样本数据的字典。
    """
    fuel_values = samples_result['fuel']
    fuel_D_outer_values = samples_result['fuel_D_outer']
    HP_D_outer_values = samples_result['HP_D_outer']

    fig = plt.figure(figsize=(10, 6))
    ax = fig.add_subplot(111, projection='3d')

    ax.scatter(fuel_values, fuel_D_outer_values, HP_D_outer_values, c='b', marker='o')

    ax.set_xlabel('Fuel Enrichment')
    ax.set_ylabel('Fuel D outer')
    ax.set_zlabel('HP D outer')

    plt.title('Latin Hypercube Sampling of Uncertainty Parameters')
    plt.savefig('Latin Hypercube Sampling of Uncertainty Parameters.png')
    plt.show()

def extract_sample_values(samples_result, settings_uctt_ptb_dic):
    """
    从样本结果中提取各参数的值，仅提取 material_params_samples 相关的参数。
    
    参数:
        samples_result (numpy.ndarray): Sobol 样本数组，形状为 (n_samples, n_material_params)。
        settings_uctt_ptb_dic (dict): 参数字典，包含 disturb 标志。
    
    返回:
        dict: 包含各参数值的字典（仅包含 material_params_samples 的参数）。
    """
    result = {}
    material_params = ['E_slope', 'E_intercept', 'nu', 'alpha_base', 'alpha_slope']
    
    for i, param_name in enumerate(material_params):
        disturb_key = f"{param_name}_disturb"
        if settings_uctt_ptb_dic.get(disturb_key, False):
            result[f"{param_name}_values"] = samples_result[:, i].tolist()
            print(f"提取的样本值 {param_name}_values: {result[f'{param_name}_values']}")  # 添加打印语句
    
    return result

class ParameterUpdater:
    """
    用于更新参数字典和替换文件值的类。
    """
    def __init__(self, settings_dic, parameters_dic, sample_values, count):
        """
        初始化参数更新器。

        参数:
            settings_dic (dict): 设置字典。
            parameters_dic (dict): 参数字典。
            sample_values (dict): 样本值字典。
            count (int): 当前样本索引。
        """
        self.settings_dic = settings_dic
        self.parameters_dic = parameters_dic
        self.sample_values = sample_values
        self.count = count

    def update_fuel(self):
        """
        更新燃料相关参数。
        """
        if self.settings_dic['settings_uctt_ptb_dic']['fuel_disturb']:
            fuel_value = float(self.sample_values['fuel_values'][self.count])
            self.settings_dic['fuel'] = fuel_value

    def update_fuel_dimensions(self):
        """
        更新燃料内外径参数，并替换文件中的值。
        """
        if self.settings_dic['settings_uctt_ptb_dic']['fuel_D_outer_disturb']:
            fuel_D_outer_value = float(self.sample_values['fuel_D_outer_values'][self.count])
            fuel_D_inner_value = float(self.sample_values['fuel_D_inner_values'][self.count])
            self.parameters_dic['fuel_D_outer'] = fuel_D_outer_value
            self.parameters_dic['fuel_D_inner'] = fuel_D_inner_value
            change_geo_file.replace_value_in_file(name='fuel_D_outer', new_value=fuel_D_outer_value)

            if fuel_D_outer_value <= fuel_D_inner_value:
                fuel_D_inner_value = fuel_D_outer_value - 0.013
                self.parameters_dic['fuel_D_inner'] = fuel_D_inner_value

    def update_heat_pipe(self):
        """
        更新热管外径参数，并替换文件中的值。
        """
        if self.settings_dic['settings_uctt_ptb_dic']['HP_D_outer_disturb']:
            HP_D_outer_value = float(self.sample_values['HP_D_outer_values'][self.count])
            self.parameters_dic['HP_D_outer'] = HP_D_outer_value
            change_geo_file.replace_value_in_file(name='HP_D_outer', new_value=HP_D_outer_value)

    def update_temperatures(self):
        """
        更新温度相关参数。
        """
        if self.settings_dic['settings_uctt_ptb_dic']['fuel_T_disturb']:
            fuel_T_value = float(self.sample_values['fuel_T_values'][self.count])
            self.settings_dic['fuel_T'] = fuel_T_value
            self.parameters_dic['fuel_T'] = fuel_T_value

        if self.settings_dic['settings_uctt_ptb_dic']['monolith_T_disturb']:
            monolith_T_value = float(self.sample_values['monolith_T_values'][self.count])
            self.settings_dic['monolith_T'] = monolith_T_value
            self.parameters_dic['monolith_T'] = monolith_T_value

        if self.settings_dic['settings_uctt_ptb_dic']['temp_pipe_disturb']:
            temp_pipe_value = float(self.sample_values['temp_pipe_values'][self.count])
            self.settings_dic['temp_pipe'] = temp_pipe_value
            self.parameters_dic['temp_pipe'] = temp_pipe_value

    def update_core_height(self):
        """
        更新核心高度参数，并替换文件中的值。
        """
        if self.settings_dic['settings_uctt_ptb_dic']['H_core_disturb']:
            H_core_value = float(self.sample_values['H_core_values'][self.count])
            self.settings_dic['H_core'] = H_core_value
            self.parameters_dic['H_core'] = H_core_value
            change_geo_file.replace_value_in_file(name='150', new_value=H_core_value, file_path='Thermal_expansion_z.geo')

    def update_material_params(self):
        """
        更新材料参数，包括 SS316 热导率经验参数。
        """
        # 支持所有 material_params 的自动更新
        material_keys = [
            'E_slope', 'E_intercept', 'nu', 'alpha_base', 'alpha_slope',
            'SS316_T_ref', 'SS316_k_ref', 'SS316_alpha', 'SS316_scale'
        ]
        for key in material_keys:
            value_key = f"{key}_values"
            if value_key in self.sample_values:
                self.parameters_dic[key] = float(self.sample_values[value_key][self.count])

        # 同步到 settings_dic 以便后续传递
        self.settings_dic['material_params'] = {k: self.parameters_dic[k] for k in material_keys if k in self.parameters_dic}

    def update_all(self):
        """
        更新所有参数。
        """
        self.update_fuel()
        self.update_fuel_dimensions()
        self.update_heat_pipe()
        self.update_temperatures()
        self.update_core_height()
        self.update_material_params()  # 新增：确保 material_params 被正确更新

def update_dic_and_starting(settings_dic, parameters_dic, initial_path):
    """
    更新设置字典并启动计算流程。
    根据样本结果更新参数字典，并调用外部模块进行计算。
    
    参数:
        settings_dic (dict): 设置字典。
        parameters_dic (dict): 参数字典。
        initial_path (str): 初始路径。
    
    返回:
        tuple: 包含 keff 值数组和原始路径的元组。
    """
    total_count = settings_dic['settings_uctt_ptb_dic']['total_count']
    
    # 检查 settings_dic 中是否包含 'samples_result'
    if 'samples_result' in settings_dic:
        samples_result = settings_dic['samples_result']
        # 使用封装的函数提取样本数据
        sample_values = extract_sample_values(samples_result, settings_dic['settings_uctt_ptb_dic'])
    elif 'material_params_samples' in settings_dic:
        # 直接使用 material_params_samples
        sample_values = settings_dic['material_params_samples']
    else:
        raise KeyError("settings_dic 中缺少 'samples_result' 或 'material_params_samples'")
    
    original_path = os.getcwd()
    for count in range(total_count):
        # 创建子文件夹
        path = os.path.join(original_path, str(count))
        if not os.path.exists(path):
            os.mkdir(path)
        os.chdir(path)
        # 复制必要的文件
        source_path1 = os.path.join(initial_path, 'Thermal_conduction.geo')
        destination_path1 = os.path.join(path, 'Thermal_conduction.geo')
        source_path2 = os.path.join(initial_path, 'Thermal_expansion_z.geo')
        destination_path2 = os.path.join(path, 'Thermal_expansion_z.geo')
        source_path3 = os.path.join(initial_path, 'settings.xml')
        destination_path3 = os.path.join(path, 'settings.xml')
        source_path4 = os.path.join(initial_path, 'geometry.xml')
        destination_path4 = os.path.join(path, 'geometry.xml')
        source_path5 = os.path.join(initial_path, 'materials.xml')
        destination_path5 = os.path.join(path, 'materials.xml')
        
        import Mega_new_compling  # 延迟导入，避免循环依赖
        Mega_new_compling.copy_file(source_path1, destination_path1)
        Mega_new_compling.copy_file(source_path2, destination_path2)
        Mega_new_compling.copy_file(source_path3, destination_path3)
        Mega_new_compling.copy_file(source_path4, destination_path4)
        Mega_new_compling.copy_file(source_path5, destination_path5)
        # 使用 ParameterUpdater 更新参数
        updater = ParameterUpdater(settings_dic, parameters_dic, sample_values, count)
        current_input = {key: [sample_values[key][count]] for key in sample_values}
        
        updater.update_all()
        MEGA = Mega_new_compling.coupling_Computation(parameters_dic, settings_dic)
        MEGA.transportnew(current_input)
    # 获取 keff 值
    keffs = get_keff(original_path, total_count)
    return keffs, original_path

def get_keff(original_path, count):
    """
    从计算结果中提取 keff 值。
    
    参数:
        original_path (str): 原始路径。
        count (int): 样本数量。
    
    返回:
        numpy.ndarray: 包含 keff 值的数组。
    """
    keffs = np.zeros(count)
    index = 0
    with open(os.path.join(original_path, 'keff.txt'), 'w') as output:
        numeric_folders = [folder for folder in os.listdir(original_path) if folder.isdigit()]
        for folder in sorted(numeric_folders, key=lambda x: int(x)):
            folder_path = os.path.join(original_path, folder)
            if os.path.isdir(folder_path):
                NN_keff_distri_path = os.path.join(folder_path, 'NN_keff_distri.txt')
                if os.path.exists(NN_keff_distri_path):
                    with open(NN_keff_distri_path, 'r') as NN_keff_distri:
                        content = NN_keff_distri.read()
                        data_list = content.split(',')
                        keff = data_list[11]
                        keffs[index] = float(keff)
                        index += 1
                        output.write(keff + '\n')
    return keffs

def start_generater(inputs=None, counts=0, use_percentage=False, percentage=0.1):
    """
    主函数，启动生成器流程。
    创建文件夹、生成样本、更新字典并启动计算。
    
    参数:
        inputs (list): 输入样本数据。
        counts (int): 样本数量。
        use_percentage (bool): 是否使用百分比扰动，默认为 False。
        percentage (float): 如果使用百分比扰动，指定扰动百分比（如 0.1 表示 10%）。
    
    返回:
        tuple: 包含 keff 值数组和原始路径的元组。
    """
    base_path, path = createFolder()
    initial_path = os.getcwd()
    initial_date_path = os.path.join(os.getcwd(), path)

    parameters_dic = {
        'fuel_D_inner': 1.412,
        'fuel_D_outer': 1.425,
        'fuel': 0.3053,
        'H_core': 150,
        'H_core_origin': 150,
        'drum_D': 25,
        'controldrum_angle': 0,
        'H_reflector': 15,
        'H_gas_plenum': 20,
        'R_reflector': 55.625,
        'HP_D_outer': 1.575,
        'P_unit_fuel': 1.6,
        'P_unit_heatpipe': 1.6 * np.sqrt(3),
        'P_unit_fuel_origin': 1.6,
        'solid_rod_R': 5.6,
        'annular_R_inner': 6.85,
        'annular_R_outer': 8.85,
        'wall_1': 8.84,
        'wall_2': 29.625,
        'wall_1_origin': 8.84,
        'wall_2_origin': 29.625,
        'heat_power': 5000000,
        'fuel_T': 300,
        'monolith_T': 300,
        'temp_pipe': 897.5,
        'emergency_control_rod': 'no control rod',
        'controlRod_deep': 0,
        'ReflectorM': [[['N', 'Al27', 2.0], ['N', 'O16', 3.0]], 3.9],
        "SS316_T_ref": 923.15,
        "SS316_k_ref": 23.2,
        "SS316_alpha": 1/75,
        "SS316_scale": 1/100,
    }

    settings_MC_dic = {'batches': 600, 'inactive': 250, 'particles': 30000, 'tally_method': 'mesh_tally', 'Output': True}
    settings_nek_dic = {'file_name': 'Thermal_conduction', 'solver_name': 'ADRSolver', 'geometry_update': True, 'size_factor': 0.5}
    settings_sfe_dic = {'file_name': 'Thermal_expansion', 'geometry_update': True, 'size_factor': 5}
    settings_Expansion = {'geometry_update': True, 'Expansion_name_xy': 'Thermal_expansion_xy', 'file_name_Basis_Expansion_Z': 'Thermal_expansion_z'}
    settings_Name_dic = {'Expansion_name_xy': 'Thermal_expansion_xy', 'Expansion_name_z': 'Thermal_expansion_z', 'Conduction_name_xy': 'Thermal_conduction'}

    settings_uctt_ptb_dic = {
        'name_list': ['fuel', 'fuel_D_outer', 'fuel_D_inner', 'HP_D_outer', 'fuel_T', 'monolith_T', 'temp_pipe', 'H_core','E_slope', 'E_intercept', 'nu', 'alpha_base', 'alpha_slope'],
        'total_count': counts,
        'fuel_disturb': False, 'fuel_mean': 0.3053, 'fuel_std': 0.02,
        'fuel_D_outer_disturb': False, 'fuel_D_outer_mean': 1.425, 'fuel_D_outer_std': 0.05,
        'HP_D_outer_disturb': False, 'HP_D_outer_mean': 1.575, 'HP_D_outer_std': 0.05,
        'fuel_T_disturb': False, 'fuel_T_mean': 1001, 'fuel_T_std': 20,
        'monolith_T_disturb': False, 'monolith_T_mean': 951, 'monolith_T_std': 20,
        'temp_pipe_disturb': False, 'temp_pipe_mean': 897.5, 'temp_pipe_std': 20,
        'H_core_disturb': False, 'H_core_mean': 151, 'H_core_std': 2,
        'E_slope_disturb': True, 'E_slope_mean': 200, 'E_slope_std': 10,
        'E_intercept_disturb': True, 'E_intercept_mean': 100, 'E_intercept_std': 5,
        'nu_disturb': True, 'nu_mean': 0.3, 'nu_std': 0.01,
        'alpha_base_disturb': True, 'alpha_base_mean': 1e-5, 'alpha_base_std': 1e-6,
        'alpha_slope_disturb': True, 'alpha_slope_mean': 1e-6, 'alpha_slope_std': 1e-7,
        "SS316_T_ref_disturb": True, "SS316_T_ref_mean": 923.15, "SS316_T_ref_std": 10,
        "SS316_k_ref_disturb": True, "SS316_k_ref_mean": 23.2, "SS316_k_ref_std": 1.0,
        "SS316_alpha_disturb": True, "SS316_alpha_mean": 1/75, "SS316_alpha_std": 0.001,
        "SS316_scale_disturb": False, "SS316_scale_mean": 1/100, "SS316_scale_std": 0.001,
    }

    settings_dic = {
        'settings_MC_dic': settings_MC_dic,
        'settings_Name_dic': settings_Name_dic,
        'settings_nek_dic': settings_nek_dic,
        'settings_sfe_dic': settings_sfe_dic,
        'settings_uctt_ptb_dic': settings_uctt_ptb_dic,
        'Mode': 3,
        'changetheangle': True,
        'Initial_temp': 300,
        'temperature_update': True,
        'iteration': 2,
        'relaxation': 1.0,
        'tolerance': 1e-4,
        'kefftolerance': 1e-4
    }

    inputs = inputs.tolist()
    os.chdir(path)
    os.chdir(path)

    if counts != 0:
        # 只用 MATERIAL_KEYS
        if isinstance(inputs, list):
            if counts != 9:
                material_params_samples = {f"{k}_values": [item[i] for item in inputs] for i, k in enumerate(MATERIAL_KEYS)}
            else:                
                material_params_samples = {f"{k}_values": inputs[i] for i, k in enumerate(MATERIAL_KEYS)}
        else:
            material_params_samples = {f"{k}_values": inputs[:, i].tolist() for i, k in enumerate(MATERIAL_KEYS)}
        settings_dic.update(material_params_samples=material_params_samples)
    else:
        config = build_perturber_config(settings_dic['settings_uctt_ptb_dic'], use_percentage, percentage)
        perturber = ParameterPerturber(config)
        N = settings_dic['settings_uctt_ptb_dic']['total_count']
        bounds = {key: [MATERIAL_MEAN_VALUES[key] - 3*MATERIAL_STD_DEV_VALUES[key],
                        MATERIAL_MEAN_VALUES[key] + 3*MATERIAL_STD_DEV_VALUES[key]]
                  for key in MATERIAL_KEYS}
        samples = perturber.generate_sobol_samples(num_samples=N, bounds=bounds)
        material_params_samples = {f"{key}_values": [s[key] for s in samples] for key in bounds}
        settings_dic.update(material_params_samples=material_params_samples)

    keffs, original_path = update_dic_and_starting(settings_dic, parameters_dic, base_path)
    return keffs, original_path

def generate_material_samples(mean_dict, std_dict, n_samples, as_array=True, random_seed=None):
    """
    简洁高效地生成材料参数扰动样本（正态分布），支持所有参数自动扩展。
    参数:
        mean_dict: dict, 参数名->均值
        std_dict: dict, 参数名->标准差
        n_samples: int, 样本数
        as_array: bool, 是否返回 numpy 数组（否则返回 dict）
        random_seed: int, 随机种子
    返回:
        np.ndarray (n_samples, n_params) 或 dict(param_name: [samples...])
    """
    import numpy as np
    if random_seed is not None:
        np.random.seed(random_seed)
    keys = list(mean_dict.keys())
    means = np.array([mean_dict[k] for k in keys])
    stds = np.array([std_dict[k] for k in keys])
    samples = np.random.normal(loc=means, scale=stds, size=(n_samples, len(keys)))
    if as_array:
        return samples
    else:
        return {k: samples[:, i].tolist() for i, k in enumerate(keys)}

# 用法示例（在主流程或 start_generater 里）：
