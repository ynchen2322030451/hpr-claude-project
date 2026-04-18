import numpy as np
from scipy.interpolate import interp1d
import ast
import importlib.util
import uuid
from typing import Dict, Any, List, Union, Callable
import json
import logging
from scipy.stats.qmc import Sobol
import os

# 初始化日志记录
if not os.path.exists('/home/tjzs/Documents/fenics_data/fenics_data/output'):
    os.makedirs('/home/tjzs/Documents/fenics_data/fenics_data/output')
    if not os.path.exists('/home/tjzs/Documents/fenics_data/fenics_data/output/parameter_perturbation.log'):
        with open('/home/tjzs/Documents/fenics_data/fenics_data/output/parameter_perturbation.log', 'w') as f:
            f.write("日志文件已创建。\n")
logging.basicConfig(filename='/home/tjzs/Documents/fenics_data/fenics_data/output/parameter_perturbation.log', level=logging.INFO, format='%(asctime)s - %(message)s')

def build_perturber_config(settings_dic, use_percentage=False, percentage=0.1):
    keys = ['E_slope', 'E_intercept', 'nu', 'alpha_base', 'alpha_slope']
    config = {"parameters": {}}

    for key in keys:
        disturb = settings_dic.get(f"{key}_disturb", False)
        mean = settings_dic.get(f"{key}_mean", 0.0)
        std = settings_dic.get(f"{key}_std", 0.0)

        if disturb:
            if use_percentage:
                std = mean * percentage
            perturbation = {
                "mode": "distribution",
                "type": "normal",
                "params": {"mean": mean, "std": std}
            }
        else:
            perturbation = {
                "mode": "manual",
                "value": mean
            }

        config["parameters"][key] = {
            "perturbation": perturbation
        }

    return config

class ParameterPerturber:
    def __init__(self, config: Dict[str, Any]):
        """
        初始化扰动器，传入配置字典。
        config: 包含参数、来源和扰动规则的字典。
        """
        self.config = config
        self.parameters = {}
        self.load_parameters()

    def load_parameters(self):
        """
        从指定文件加载参数值。
        """
        os.chdir('/home/cyn/文档/jcloudfiles/The_final/modules')
        for param, param_config in self.config['parameters'].items():
            file_path = param_config.get('file_path')
            var_name = param_config.get('var_name', param)
            try:
                # 动态加载模块
                spec = importlib.util.spec_from_file_location(f"module_{uuid.uuid4().hex}", file_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                value = getattr(module, var_name, None)
                if value is None:
                    raise ValueError(f"变量 {var_name} 未在 {file_path} 中找到")
                self.parameters[param] = {
                    'value': value,
                    'shape': self._detect_shape(value),
                    'file_path': file_path,
                    'var_name': var_name
                }
            except Exception as e:
                print(f"加载 {param} 从 {file_path} 时出错: {e}")
                self.parameters[param] = {'value': None, 'shape': None, 'file_path': file_path, 'var_name': var_name}

    def _detect_shape(self, value: Any) -> str:
        """
        检测参数的形状/类型。
        """
        if isinstance(value, (int, float)):
            return 'scalar'
        elif isinstance(value, np.ndarray):
            return f"array_{value.shape}"
        elif isinstance(value, list):
            return f"list_{len(value)}"
        elif isinstance(value, dict):
            return 'table'
        elif callable(value):
            return 'function'
        else:
            return 'unknown'

    def perturb_parameters(self) -> Dict[str, Any]:
        """
        根据配置对参数应用扰动。
        返回扰动后的参数值字典。
        """
        perturbed = {}
        grouped_params = {}

        # 处理参数分组（例如，共享均值或分布）
        for group in self.config.get('groups', []):
            group_name = group.get('name')
            param_list = group.get('parameters')
            group_type = group.get('type')
            group_params = group.get('params', {})
            grouped_params[group_name] = {'parameters': param_list, 'type': group_type, 'params': group_params}

        # 处理每个参数
        for param, param_config in self.config['parameters'].items():
            original_value = self.parameters[param]['value']
            perturbation = param_config.get('perturbation', {})

            if not perturbation or original_value is None:
                perturbed[param] = original_value
                continue

            # 检查参数是否属于某个分组
            group_name = next((g for g, g_config in grouped_params.items() if param in g_config['parameters']), None)
            if group_name:
                perturbed[param] = self._apply_group_perturbation(param, group_name, grouped_params)
            else:
                perturbed[param] = self._perturb_single_parameter(original_value, perturbation, self.parameters[param]['shape'])

        # 在 perturbation 逻辑中自动处理 SS316_T_ref, SS316_k_ref, SS316_alpha, SS316_scale
        for key in ["SS316_T_ref", "SS316_k_ref", "SS316_alpha", "SS316_scale"]:
            if self.config['parameters'].get(f"{key}_disturb", False):
                mean = self.config['parameters'].get(f"{key}_mean")
                std = self.config['parameters'].get(f"{key}_std")
                perturbed[key] = np.random.normal(mean, std)

        return perturbed

    def _perturb_single_parameter(self, value: Any, perturbation: Dict[str, Any], shape: str) -> Any:
        """
        根据扰动配置对单个参数进行扰动。
        """
        mode = perturbation.get('mode', 'ratio')
        if mode == 'manual':
            return perturbation.get('value')
        elif mode == 'ratio':
            ratio = perturbation.get('ratio', 0.1)
            if shape == 'scalar':
                return value * (1 + np.random.uniform(-ratio, ratio))
            elif shape.startswith('array') or shape.startswith('list'):
                return [v * (1 + np.random.uniform(-ratio, ratio)) for v in value] if isinstance(value, list) else value * (1 + np.random.uniform(-ratio, ratio))
            elif shape == 'table':
                return {k: v * (1 + np.random.uniform(-ratio, ratio)) for k, v in value.items()}
        elif mode == 'distribution':
            dist_type = perturbation.get('type', 'normal')
            dist_params = perturbation.get('params', {})
            if shape == 'scalar':
                if dist_type == 'normal':
                    return np.random.normal(dist_params.get('mean', value), dist_params.get('std', value * 0.1))
                elif dist_type == 'uniform':
                    return np.random.uniform(dist_params.get('low', value * 0.9), dist_params.get('high', value * 1.1))
            elif shape.startswith('array') or shape.startswith('list'):
                if dist_type == 'normal':
                    return [np.random.normal(dist_params.get('mean', v), dist_params.get('std', v * 0.1)) for v in value]
                elif dist_type == 'uniform':
                    return [np.random.uniform(dist_params.get('low', v * 0.9), dist_params.get('high', v * 1.1)) for v in value]
        return value

    def _apply_group_perturbation(self, param: str, group_name: str, grouped_params: Dict[str, Any]) -> Any:
        """
        应用基于分组的扰动（例如，共享均值或分布）。
        """
        group = grouped_params[group_name]
        group_type = group['type']
        group_params = group['params']
        original_value = self.parameters[param]['value']
        shape = self.parameters[param]['shape']

        if group_type == 'equal_mean':
            mean_value = group_params.get('mean')
            if mean_value is None:
                # 动态计算分组参数的均值
                values = [self.parameters[p]['value'] for p in group['parameters'] if self.parameters[p]['value'] is not None]
                mean_value = np.mean(values) if values else original_value
            if shape == 'scalar':
                return mean_value + np.random.normal(0, group_params.get('std', mean_value * 0.1))
            elif shape.startswith('array') or shape.startswith('list'):
                return [mean_value + np.random.normal(0, group_params.get('std', mean_value * 0.1)) for _ in original_value]
        return original_value

    def validate_parameters(self, perturbed_params: Dict[str, Any]) -> bool:
        """
        验证扰动后的参数是否符合目标函数的要求。
        """
        for param, value in perturbed_params.items():
            if value is None:
                logging.error(f"参数 {param} 的值为 None，验证失败。")
                return False
            if isinstance(value, (int, float)) and value < 0:
                logging.error(f"参数 {param} 的值 {value} 为负数，验证失败。")
                return False
        logging.info("参数验证通过。")
        return True

    def pass_to_function(self, target_func: Callable, module_path: str, **kwargs) -> Any:
        """
        将扰动后的参数传递给另一个模块中的目标函数。
        """
        try:
            spec = importlib.util.spec_from_file_location(f"target_module_{uuid.uuid4().hex}", module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            target_func = getattr(module, target_func.__name__)
            perturbed_params = self.perturb_parameters()
            return target_func(perturbed_params, **kwargs)
        except Exception as e:
            print(f"执行目标函数时出错: {e}")
            return None

    def pass_to_multiple_functions(self, target_funcs: Dict[str, str], **kwargs) -> Dict[str, Any]:
        """
        将扰动后的参数分别传递给多个模块中的目标函数，并记录日志。
        target_funcs: 字典，键为模块路径，值为目标函数名。
        kwargs: 额外的参数。
        返回每个函数的执行结果。
        """
        results = {}
        perturbed_params = self.perturb_parameters()
        if not self.validate_parameters(perturbed_params):
            logging.error("参数验证失败，终止函数调用。")
            return results

        for module_path, func_name in target_funcs.items():
            try:
                spec = importlib.util.spec_from_file_location(f"target_module_{uuid.uuid4().hex}", module_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                target_func = getattr(module, func_name)
                result = target_func(perturbed_params, **kwargs)
                results[func_name] = result
                logging.info(f"成功调用 {func_name}，返回值: {result}")
            except Exception as e:
                logging.error(f"执行 {func_name} 时出错: {e}")
                results[func_name] = None
        return results

    def generate_sobol_samples(self, num_samples: int, bounds: Dict[str, List[float]]) -> List[Dict[str, float]]:
        """
        使用 Sobol 序列生成扰动样本。
        num_samples: 样本数量。
        bounds: 每个参数的上下界，格式为 {"param_name": [lower, upper]}。
        返回样本列表，每个样本是一个参数字典。
        """
        param_names = list(bounds.keys())
        lower_bounds = [bounds[param][0] for param in param_names]
        upper_bounds = [bounds[param][1] for param in param_names]

        sobol = Sobol(d=len(param_names), scramble=True)
        samples = sobol.random(num_samples)

        # 将 Sobol 样本映射到参数范围
        scaled_samples = [
            {param_names[i]: lower_bounds[i] + (upper_bounds[i] - lower_bounds[i]) * sample[i]
             for i in range(len(param_names))}
            for sample in samples
        ]
        return scaled_samples

    def control_output_parameters(self, outputs: Dict[str, Any], constraints: Dict[str, Dict[str, float]]) -> Dict[str, Any]:
        """
        控制输出参数的范围和分布。
        outputs: 输出参数字典。
        constraints: 每个输出参数的约束条件，格式为 {"param_name": {"mean": x, "std": y, "min": a, "max": b}}。
        返回调整后的输出参数字典。
        """
        adjusted_outputs = {}
        for param, value in outputs.items():
            if param in constraints:
                constraint = constraints[param]
                mean = constraint.get("mean", value)
                std = constraint.get("std", 0)
                min_val = constraint.get("min", float("-inf"))
                max_val = constraint.get("max", float("inf"))

                # 应用正态分布调整
                adjusted_value = np.random.normal(mean, std) if std > 0 else value
                # 限制范围
                adjusted_value = max(min_val, min(max_val, adjusted_value))
                adjusted_outputs[param] = adjusted_value
            else:
                adjusted_outputs[param] = value
        return adjusted_outputs

# 示例配置
if __name__ == "__main__":
    config = {
        "parameters": {
            "alpha": {"file_path": "fenics_thermal_TE.py", "var_name": "alpha", "perturbation": {"mode": "ratio", "ratio": 0.1}},
            "E": {"file_path": "fenics_thermal_TE.py", "var_name": "E", "perturbation": {"mode": "ratio", "ratio": 0.1}},
            "nu": {"file_path": "fenics_thermal_TE.py", "var_name": "nu", "perturbation": {"mode": "ratio", "ratio": 0.1}},
            "hp_temp": {"file_path": "heatpipe.py", "var_name": "hp_temp", "perturbation": {"mode": "ratio", "ratio": 0.1}},
        },
    }

    # 初始化扰动器
    perturber = ParameterPerturber(config)

    # 扰动参数
    perturbed_params = perturber.perturb_parameters()
    print("扰动后的参数:", perturbed_params)

    # 示例目标函数（替换为实际函数）
    def example_target_function(params, **kwargs):
        return sum(params.values()) if all(isinstance(v, (int, float)) for v in params.values()) else params

    # 将参数传递给目标函数
    result = perturber.pass_to_function(example_target_function, "target_module.py")
    print("目标函数返回结果:", result)

    # 扰动参数并传递到多个函数
    target_functions = {
        "/home/tjzs/Documents/fenics_data/fenics_data/heatpipe.py": "getheatpipetemp",
        "/home/tjzs/Documents/fenics_data/fenics_data/fenics_thermal_TE.py": "fenic_conduction_xy",
        "/home/tjzs/Documents/fenics_data/fenics_data/MEGA_OpenMC_test.py": "define_Geo_Mat_Set"
    }
    results = perturber.pass_to_multiple_functions(target_functions, origin_hptemp=[300]*72, loseHp=[1, 2], heatpipe_type=[0]*72)
    print("各函数返回结果:", results)

    # 使用 Sobol 生成样本
    bounds = {
        "alpha": [0.9, 1.1],
        "E": [1.9e5, 2.1e5],
        "nu": [0.3, 0.35],
        "hp_temp": [290, 310],
    }
    sobol_samples = perturber.generate_sobol_samples(num_samples=10, bounds=bounds)
    print("Sobol 样本:", sobol_samples)

    # 控制输出参数
    outputs = {"k_eff": 1.02, "average_temp": 300}
    constraints = {
        "k_eff": {"mean": 1.0, "std": 0.01, "min": 0.95, "max": 1.05},
        "average_temp": {"min": 290, "max": 310},
    }
    adjusted_outputs = perturber.control_output_parameters(outputs, constraints)
    print("调整后的输出参数:", adjusted_outputs)