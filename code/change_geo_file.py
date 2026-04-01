import re

def get_search_line(name, line):
    """
    根据参数名称和行内容，匹配对应的正则表达式。
    
    参数:
        name (str): 参数名称，例如 'fuel_D_outer' 或 'HP_D_outer'。
        line (str): 文件中的一行内容。
    
    返回:
        tuple: 包含两个匹配对象 (match1, match2)，如果没有匹配则为 None。
    """
    if name == 'fuel_D_outer':
        match1 = re.search(r'Fuel_D\s*=\s*([\d.]+)\s*\*\s*cm\s*;\n', line)
        match2 = re.search(r'Fuel_r\s*=\s*([\d./\s]+)\s*\*\s*cm\s*;\n', line)
    elif name == 'HP_D_outer':
        match1 = re.search(r'Pipe_D\s*=\s*([\d.]+)\s*\*\s*cm\s*;\n', line)
        match2 = re.search(r'Pipe_r\s*=\s*([\d./\s]+)\s*\*\s*cm\s*;\n', line)
    else:
        match1, match2 = None, None
    return match1, match2

def replace_value_in_line(name, line, new_value):
    """
    替换行中的数值，根据参数名称匹配对应的正则表达式。
    
    参数:
        name (str): 参数名称，例如 'fuel_D_outer' 或 'HP_D_outer'。
        line (str): 文件中的一行内容。
        new_value (float): 要替换的新数值。
    
    返回:
        str: 替换后的行内容。如果没有匹配，则返回原始行。
    """
    match1, match2 = get_search_line(name, line)

    if match1:
        # 替换匹配到的数值
        old_value = match1.group(1)
        new_line = line.replace(old_value, str(new_value))
        return new_line
    elif match2:
        # 替换匹配到的数值，半径需要除以 2
        old_value = match2.group(1)
        new_line = line.replace(old_value, str(new_value / 2))
        return new_line
    else:
        # 如果没有匹配到，返回原始行
        return line

def replace_value_in_file(name, new_value, file_path='Thermal_conduction.geo'):
    """
    替换文件中的数值，根据参数名称匹配对应的正则表达式。
    
    参数:
        name (str): 参数名称，例如 'fuel_D_outer' 或 'HP_D_outer'。
        new_value (float): 要替换的新数值。
        file_path (str): 文件路径，默认为 'Thermal_conduction.geo'。
    """
    try:
        # 读取文件内容
        with open(file_path, 'r') as file:
            lines = file.readlines()

        # 替换文件中每一行的数值
        new_lines = [replace_value_in_line(name, line, new_value) for line in lines]

        # 将更新后的内容写回文件
        with open(file_path, 'w') as file:
            file.writelines(new_lines)

        print(f'成功替换文件中的数值: {new_value}')
    except FileNotFoundError:
        print(f'找不到文件: {file_path}')
    except Exception as e:
        print(f'发生错误: {e}')

# 使用示例
# file_path = 'your_file.geo'
# new_value = 123
# replace_value_in_file(file_path, new_value)