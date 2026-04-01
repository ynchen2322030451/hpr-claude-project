import numpy as np

# 示例热通量数据（342 个数据点）
thermal_tot_vec_list = [
    52.48285021186679, 52.940333010979586, 52.4058019311656, 48.17909517150842, 
    48.606524416267774, 48.569741659956605, 48.09614374448702, 39.87080526226745, 
    # ...existing data...
    21.386150882628367, 21.141555824339367, 20.577185380965858, 20.378699582152755, 
    21.152682832766974
]

def arange_fueldata_to_define_order(fuel_data_in_position_order):
    """
    将燃料数据按照特定顺序排列。
    
    参数:
        fuel_data_in_position_order (list): 按位置顺序排列的燃料数据。
    
    返回:
        list: 按定义顺序排列的燃料数据。
    """
    aranged = []
    fuelcount = 0

    # 第一部分数据排列
    for i in range(3, 11):
        for j in range(i):
            aranged.append(fuel_data_in_position_order[fuelcount])
            fuelcount += 1
        fuelcount += i + 1

    # 第二部分数据排列
    fuelcount2 = 3
    for i in range(4, 12):
        for j in range(i):
            aranged.append(fuel_data_in_position_order[fuelcount2])
            fuelcount2 += 1
        fuelcount2 += i

    return aranged

def devide_heatflux_to_heatpipe(a):
    """
    将热通量分配到每个热管，并找到热管的最大热通量。
    
    参数:
        a (list): 热通量数据列表。
    
    返回:
        tuple: 包含最大热通量值、分配到燃料的热通量列表和分配到热管的热通量列表。
    """
    fuel2_begin = 52  # 第二部分燃料数据的起始索引
    b = []  # 分配到燃料的热通量
    countforfuel1 = 0
    countforfuel2 = 0

    # 分配热通量到燃料
    for i in range(3, 12):
        if i != 3:
            temp = []
            for j in range(i):
                temp.append(a[countforfuel2 + fuel2_begin])
                countforfuel2 += 1
            b.append(temp)
        if i != 11:
            temp = []
            for j in range(i):
                temp.append(a[countforfuel1])
                countforfuel1 += 1
            b.append(temp)

    # 创建热管数据结构
    he = []
    for i in range(4, 13):
        temp = [0] * i
        he.append(temp)

    # 分配热通量到热管
    for i in range(len(b)):
        if i % 2 == 0:  # 偶数行
            for j in range(len(b[i])):
                zhi = b[i][j] / 3
                r = int(i / 2)
                he[r][j] += zhi
                he[r][j + 1] += zhi
                he[r + 1][j + 1] += zhi
        else:  # 奇数行
            for j in range(len(b[i])):
                zhi = b[i][j] / 3
                r = int(i / 2)
                he[r][j] += zhi
                he[r + 1][j] += zhi
                he[r + 1][j + 1] += zhi

    # 找到热管的最大热通量
    ma = 0
    for i in he:
        for j in i:
            if j > ma:
                ma = j

    return ma, b, he  # 返回最大值、燃料热通量和热管热通量

# 示例调用
# print(devide_heatflux_to_heatpipe(thermal_tot_vec_list))