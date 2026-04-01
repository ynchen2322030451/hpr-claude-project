# 导入必要的库
import numpy as np
import xml.etree.ElementTree as ET
import os
import sys
import matplotlib.pyplot as plt
from subprocess import call

'''
Fenics 有限元计算几何与网格生成工具
核心用途：为 Fenics 框架生成 2D/3D 几何文件（.geo）及对应的网格文件（.msh），支撑后续有限元分析
关键功能：
1. 基于参数字典（parameters_dic）自动替换模板文件（mega_new.geo）占位符，生成定制化 2D 几何文件
2. 调用 Gmsh 工具生成 msh2 格式网格（支持 2D/3D），并处理文件覆盖逻辑
3. 提供快捷网格更新函数（Update2D/Update3D），简化 2D/3D 网格重建流程
依赖说明：需提前安装 Gmsh（用于网格生成），且确保模板文件 mega_new.geo 存在于执行目录
核心参数来源：parameters_dic 需包含 wall_1（燃料棒半径）、wall_2（块宽度）、P_unit_fuel（燃料单元间距）等几何参数
'''

# ================================== Nektar++ ================================== #
def create2dGeo4fenics(file_name, parameters_dic):
    """
    根据提供的参数字典，生成 2D 几何文件（.geo）用于 Fenics。
    
    参数:
        file_name (str): 输出几何文件的名称（不带扩展名）。
        parameters_dic (dict): 包含几何参数的字典。
            - wall_1: 燃料棒半径。
            - wall_2: 块的宽度。
            - P_unit_fuel: 燃料单元的间距。
    """
    # 从参数字典中获取几何参数
    wall_1 = parameters_dic['wall_1']  # 燃料棒半径
    wall_2 = parameters_dic['wall_2']  # 块的宽度
    fuel_P = parameters_dic['P_unit_fuel']  # 燃料单元的间距

    # 读取模板文件内容
    with open('mega_new.geo', 'r') as file:
        text_lines = file.read().splitlines()

    # 如果目标文件已存在，先删除
    if os.path.exists(file_name + '.geo'):
        os.remove(file_name + '.geo')

    # 替换模板文件中的占位符
    word_1 = '//3'
    index = text_lines.index(word_1)
    text_lines[index + 1] = f'Rod_R = {wall_1} *cm;'

    word_2 = '//4'
    index = text_lines.index(word_2)
    text_lines[index + 1] = f'Block_x = {wall_2} *cm;'

    word_3 = '//1'
    index = text_lines.index(word_3)
    text_lines[index + 1] = f'Pipe_P = {fuel_P}*Sqrt(3) * cm ;'

    word_4 = '//2'
    index = text_lines.index(word_4)
    text_lines[index + 1] = f'Fuel_P = {fuel_P} * cm ;'

    # 写入新的几何文件
    with open(file_name + '.geo', 'w') as file:
        file.write('\n'.join(text_lines))

def generateMesh4Fenics2d(file_name):
    """
    使用 Gmsh 生成 2D 网格文件（.msh）。
    
    参数:
        file_name (str): 输入几何文件的名称（不带扩展名）。
    """
    # 如果目标网格文件已存在，先删除
    if os.path.exists(file_name + '.msh'):
        os.remove(file_name + '.msh')

    # 调用 Gmsh 命令生成 2D 网格
    call(f'gmsh {file_name}.geo -format msh2 -2', shell=True)

def generateMesh4Fenics3d(file_name):
    """
    使用 Gmsh 生成 3D 网格文件（.msh）。
    
    参数:
        file_name (str): 输入几何文件的名称（不带扩展名）。
    """
    # 如果目标网格文件已存在，先删除
    if os.path.exists(file_name + '.msh'):
        os.remove(file_name + '.msh')

    # 调用 Gmsh 命令生成 3D 网格
    call(f'gmsh {file_name}.geo -format msh2 -3', shell=True)

def Update2D(file_name):
    """
    更新 2D 网格文件。
    
    参数:
        file_name (str): 输入几何文件的名称（不带扩展名）。
    """
    # 生成 2D 网格
    generateMesh4Fenics2d(file_name)

def Update3D(file_name):
    """
    更新 3D 网格文件。
    
    参数:
        file_name (str): 输入几何文件的名称（不带扩展名）。
    """
    # 生成 3D 网格
    generateMesh4Fenics3d(file_name)

# 示例调用（取消注释以运行）
# Update3D('Thermal_expansion_z')
# Update2D('Thermal_conduction')
