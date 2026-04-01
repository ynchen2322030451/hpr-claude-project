import os
import numpy as np
import matplotlib.pyplot as plt
import Mega_new_compling
# from generater import generate_combinations
# import generater

# parameters_dic = generater.parameters_dic
# settings_dic = generater.settings_dic

def generate_random_array(mean_value, std_dev, total_num):
    """
    生成正态分布的随机数组。

    参数:
        mean_value (float): 均值。
        std_dev (float): 标准差。
        total_num (int): 生成的随机数数量。

    返回:
        numpy.ndarray: 随机数组。
    """
    random_data = np.random.normal(mean_value, std_dev, total_num)
    return random_data

def random_array_to_list(random_data):
    """
    将随机数组转换为列表。

    参数:
        random_data (numpy.ndarray): 随机数组。

    返回:
        list: 随机数据列表。
    """
    random_data_list = random_data.tolist()
    return random_data_list

def random_array_plt(random_data, x_value, y_value='Frequency'):
    """
    绘制随机数据的直方图并保存为图片。

    参数:
        random_data (numpy.ndarray): 随机数据。
        x_value (str): x 轴标签。
        y_value (str): y 轴标签，默认为 'Frequency'。

    返回:
        numpy.ndarray: 输入的随机数据。
    """
    # 创建直方图
    plt.hist(random_data, bins=20, density=True, alpha=0.6, color='red', edgecolor='black')
    plt.title(f'{x_value} distribution')
    plt.xlabel(x_value)
    plt.ylabel(y_value)

    # 保存图片
    folder_name = 'random_diagram'
    original_path = os.getcwd()
    new_path = os.path.join(original_path, folder_name)
    file_path = os.path.join(new_path, f'{x_value}_distribution.jpg')
    plt.savefig(file_path)
    print("Plotting done!")
    return random_data

def generate_loop_in_dic(settings_dic, parameters_dic, name_list, index, true_index_list=[]):
    """
    遍历字典中的参数并生成随机扰动列表。

    参数:
        settings_dic (dict): 设置字典。
        parameters_dic (dict): 参数字典。
        name_list (list): 参数名称列表。
        index (int): 当前索引。
        true_index_list (list): 存储有效索引的列表，默认为空。

    返回:
        dict: 更新后的 settings_uctt_ptb_dic。
    """
    name = name_list[index]
    settings_uctt_ptb_dic = settings_dic['settings_uctt_ptb_dic']

    # 如果参数需要扰动，生成随机数据
    if settings_uctt_ptb_dic.get(f'{name}_disturb', False):
        mean_value = settings_uctt_ptb_dic[f'{name}_mean']
        std_dev = settings_uctt_ptb_dic[f'{name}_std']
        total_num = settings_uctt_ptb_dic[f'{name}_total_count']

        current_array = generate_random_array(mean_value, std_dev, total_num)
        current_list = random_array_to_list(current_array)
        random_array_plt(current_array, f'{name} disturb')
        settings_uctt_ptb_dic[f'{name}_disturb_list'] = current_list
        true_index_list.append(index)

    # 递归处理下一个参数
    if index < len(name_list) - 1:
        index += 1
        settings_uctt_ptb_dic = generate_loop_in_dic(settings_dic, parameters_dic, name_list, index, true_index_list)
        return settings_uctt_ptb_dic
    else:
        settings_uctt_ptb_dic['true_index_list'] = true_index_list
        return settings_uctt_ptb_dic

folder_counter = 0

# def generate_combinations(lists, true_name_list, settings_dic, parameters_dic, current=[]):
#     """
#     递归生成参数组合并启动计算。
#     """
#     if not lists:
#         print(tuple(current))
#         for index, current_num in enumerate(current):
#             name = true_name_list[index]
#             global folder_counter
#             if name != 'fuel':  # 可能需要更改
#                 parameters_dic[name] = current_num
#             else:
#                 settings_dic[name] = current_num

#             folder_name = f"folder_{folder_counter}_{name}_{str(current_num)}"
#             original_path = os.getcwd()
#             new_path = os.path.join(original_path, folder_name)
#             if not os.path.exists(new_path):
#                 os.mkdir(new_path)
#             os.chdir(new_path)
#         folder_counter += 1
#         with open(folder_name, 'w') as file:
#             MEGA = Mega_new_compling.coupling_Computation(parameters_dic, settings_dic)
#             MEGA.transportnew()
#     else:
#         for item in lists[0]:
#             generate_combinations(lists[1:], true_name_list, settings_dic, parameters_dic, current + [item])

def update_dic_and_starting(settings_dic, parameters_dic):
    """
    更新字典并启动参数组合生成。

    参数:
        settings_dic (dict): 设置字典。
        parameters_dic (dict): 参数字典。
    """
    name_list = settings_dic['settings_uctt_ptb_dic']['name_list']
    true_name_list = []
    lists = []

    # 遍历有效索引并生成参数列表
    for true_index in settings_dic['settings_uctt_ptb_dic']['true_index_list']:
        name = name_list[true_index]
        current_list = settings_dic['settings_uctt_ptb_dic'][f'{name}_disturb_list']
        lists.append(current_list)
        true_name_list.append(name)

    generate_combinations(lists, true_name_list)  # 启动迭代





