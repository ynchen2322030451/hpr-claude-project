import os
import re
import shutil
# from dolfin import *

def get_initial_values_set(setting_file, index=None):
    content = setting_file.read()
    # 使用正则表达式提取数值
    fuelDinner_matches = re.findall(r'"fuel_D_inner": ([\d.]+)', content)
    fuelDouter_matches = re.findall(r'"fuel_D_outer": ([\d.]+)', content)
    Hcore_matches = re.findall(r'"H_core": ([\d.]+)', content)
    HPDouter_matches = re.findall(r'"HP_D_outer": ([\d.]+)', content)
    P_unit_fuel_matches = re.findall(r'"P_unit_fuel": ([\d.]+)', content)
    wall_1_matches = re.findall(r'"wall_1": ([\d.]+)', content)
    wall_2_matches = re.findall(r'"wall_2": ([\d.]+)', content)
    heat_power_matches = re.findall(r'"heat_power": ([\d.]+)', content)
    fuel_T_matches = re.findall(r'"fuel_T": ([\d.]+)', content)
    monolith_T_matches = re.findall(r'"monolith_T": ([\d.]+)', content)
    temp_pipe_matches = re.findall(r'"temp_pipe": ([\d.]+)', content)
    fuel_matches = re.findall(r'"fuel": ([\d.]+)', content)
    
    def get_value(matches, index):
        if index == None:
            if matches:
                return matches
            else:
                return "N/A"
        elif len(matches) > index:
            return float(matches[index])
        else:
            return "N/A"
    
    return [
        get_value(fuelDinner_matches, index),
        get_value(fuelDouter_matches, index),
        get_value(Hcore_matches, index),
        get_value(HPDouter_matches, index),
        get_value(P_unit_fuel_matches, index),
        get_value(wall_1_matches, index),
        get_value(wall_2_matches, index),
        get_value(heat_power_matches, index),
        get_value(fuel_T_matches, index),
        get_value(monolith_T_matches, index),
        get_value(temp_pipe_matches, index),
        get_value(fuel_matches, index)
    ]

def get_initial_values_set2(setting_file, index=None):
    content = setting_file.read()
    # 使用正则表达式提取数值
    fuelDinner_matches = re.findall(r'"fuel_D_inner": ([\d.]+)', content)
    fuelDouter_matches = re.findall(r'"fuel_D_outer": ([\d.]+)', content)
    Hcore_matches = re.findall(r'"H_core": ([\d.]+)', content)
    HPDouter_matches = re.findall(r'"HP_D_outer": ([\d.]+)', content)
    P_unit_fuel_matches = re.findall(r'"P_unit_fuel": ([\d.]+)', content)
    wall_1_matches = re.findall(r'"wall_1": ([\d.]+)', content)
    # wall_2_matches = re.findall(r'"wall_2": ([\d.]+)', content)
    heat_power_matches = re.findall(r'"heat_power": ([\d.]+)', content)
    fuel_T_matches = re.findall(r'"fuel_T": ([\d.]+)', content)
    monolith_T_matches = re.findall(r'"monolith_T": ([\d.]+)', content)
    temp_pipe_matches = re.findall(r'"temp_pipe": ([\d.]+)', content)
    fuel_matches = re.findall(r'"fuel": ([\d.]+)', content)
    
    def get_value(matches, index):
        if index == None:
            if matches:
                return matches
            else:
                return "N/A"
        elif len(matches) > index:
            return float(matches[index])
        else:
            return "N/A"
    
    return [
        get_value(fuelDinner_matches, index),
        get_value(fuelDouter_matches, index),
        get_value(Hcore_matches, index),
        get_value(HPDouter_matches, index),
        # get_value(P_unit_fuel_matches, index),
        # get_value(wall_1_matches, index),
        # get_value(wall_2_matcmatches, index),
        get_value(fuel_T_matches, index),
        get_value(monolith_T_matches, index),
        get_value(temp_pipe_matches, index),
        get_value(fuel_matches, index)
    ]

def count_numeric_folders(input_folder):
    numeric_folders_count = 0
    for folder in os.listdir(input_folder):
        if folder.isnumeric():  # 检查文件夹名称是否为纯数字
            numeric_folders_count += 1
    return numeric_folders_count
# def get_initial_values_set2(setting_file, index=None):

def caluSS316ThermalConduct(monolith_T):# FROM COUPLING CODE
    SS316_thermal_conductivity = ((monolith_T-923.15)*(1/75)+23.2)/100
    return SS316_thermal_conductivity

def get_keff(printout_file):
    content = printout_file.read()
    # 使用正则表达式提取k-eff数值
    printout_matches_keffs = re.findall(r'k-eff:([\d.]+)', content)
    printout_matches_stds = re.findall(r'std: ([\d.]+)', content)
    if printout_matches_keffs:
        return printout_matches_keffs[0], printout_matches_stds[0]
    else:
        return "N/A"

def get_monotemp_mean_max(printout_file):
    content = printout_file.read()
    # 使用正则表达式提取monotemp_mean_max数值
    monolith_mean_temperatures = re.findall(r'monolith new temperature:([\d.]+)', content)
    monolith_max_temperatures = re.findall(r'the max monolith temperature: ([\d.]+)', content)
    monolith_mean_temperature = monolith_mean_temperatures[0]
    monolith_max_temperature = monolith_max_temperatures[0]
    if monolith_mean_temperature and monolith_max_temperature:
        return monolith_mean_temperature, monolith_max_temperature
    else:
        return "N/A"


def get_new_geo_temp(printout_file, i):
    content = printout_file.read()
    # 使用正则表达式提取geo、temp数值
    Hcore_matches = re.findall(r'New Hcore: ([\d.]+)', content)
    H_core = Hcore_matches[i] if Hcore_matches else "N/A"
    P_unit_fuel_matches = re.findall(r'New pitch: ([\d.]+) cm', content)
    P_unit_fuel = P_unit_fuel_matches[i] if P_unit_fuel_matches else "N/A"
    wall_1_matches = re.findall(r'New wall1: ([\d.]+) cm', content)
    wall_1 = wall_1_matches[i] if wall_1_matches else "N/A"
    wall_2_matches = re.findall(r'New wall2: ([\d.]+) cm', content)
    wall_2 = wall_2_matches[i] if wall_2_matches else "N/A"
    fuel_T_matches = re.findall(r'fuel new temperature: ([\d.]+)', content)
    fuel_T = fuel_T_matches[i] if fuel_T_matches else "N/A"
    monolith_T_matches = re.findall(r'monolith new temperature:([\d.]+)', content)
    monolith_T = monolith_T_matches[i] if monolith_T_matches else "N/A"
    monolith_T = float(monolith_T) - 300 if monolith_T_matches and float(monolith_T) > 1200 else monolith_T

    return H_core, P_unit_fuel, wall_1, wall_2, fuel_T, monolith_T

def get_geo_vecs(printout_file):
    '''New wall2: 29.91981116748243 cm
    New pitch_fuel: 1.6159222909020048 cm
    New pitch_HP: 2.7988595089253674 cm
    New Hcore: 152.319292614155 cm
    Relative change of monolith volume: 0.036384578331906454'''
    content = printout_file.read()
    # 使用正则表达式提取monotemp_mean_max数值
    wall2 = re.findall(r'New wall2: ([\d.]+) cm', content)
    pitch_fuel = re.findall(r'New pitch_fuel: ([\d.]+) cm', content)
    pitch_HP = re.findall(r'New pitch_HP: ([\d.]+) cm', content)
    Hcore = re.findall(r'New Hcore: ([\d.]+) cm', content)
    volume = re.findall(r'Relative change of monolith volume: ([\d.]+)', content)
    if wall2 and pitch_fuel and pitch_HP and Hcore and volume:
        return wall2[0], pitch_fuel[0], pitch_HP[0], Hcore[0], volume[0]
    else:
        return "N/A"

def get_thermal_tot_vec(outdebug_file):
    content = outdebug_file.read()
    printout_matches = re.findall(r'thermal_tot_vec=\[([\d\s.]+)\]', content)
    vecs = []
    for match in printout_matches:
        vecs.append([float(x) for x in match.split()])
    return vecs

def get_heatpipe_temp(out_fenicsdata_heatpipe_process):
    content = out_fenicsdata_heatpipe_process.read()
    hp_step_matches = re.findall(r'HP_step_in\s*=\s*(\d+)', content)
    heatpipe_temp_matches = re.findall(r'self\.heatpipe_temp_list\s*=\s*\[([\d\s.,]+)\]', content)
    heatpipe_temp_matches_vecs = []
    hp_step_matches_list = []
    for match in heatpipe_temp_matches:
        heatpipe_temp_matches_vecs.append([float(x) for x in match.split(',')])
    for match in hp_step_matches:
        hp_step_matches_list.append(int(match))
    return hp_step_matches_list, heatpipe_temp_matches_vecs

def get_mono_consts(out_the_thermal_data):
    content = out_the_thermal_data.read()
    mono_consts = re.findall(r'the ss316 con=([\d.]+)', content)
    return mono_consts

def get_mono_temps(PrintOut):
    content = PrintOut.read()
    mono_temps = re.findall(r'monolith new temperature:([\d.]+)', content) 
    return mono_temps

# def extract_and_write_keff(input_folder, output_file): # 124数，11 + 1 + 112
#     with open(output_file, 'w') as output:
#         # 遍历主目录下的文件夹
#         for folder in os.listdir(input_folder):
#             folder_path_0 = os.path.join(input_folder, folder)
#             if os.path.isdir(folder_path_0) and folder != '__pycache__':
#             # 确保是文件夹
#                 for folder_count in sorted(os.listdir(folder_path_0), key=lambda x: int(x)):
#                     folder_path = os.path.join(folder_path_0, folder_count)
#                     if os.path.isdir(folder_path):
#                         NN_keff_distri_path = os.path.join(folder_path, 'NN_keff_distri.txt')

#                         if os.path.exists(NN_keff_distri_path):
#                             with open(NN_keff_distri_path, 'r') as NN_keff_distri:
#                                 content = NN_keff_distri.read()
#                                 data_list = content.replace('[', '')
#                                 data_list2 = data_list.replace(']', '')
#                                 output.write(data_list2)
                            
def predict_power_distribution(input_folder, output_file):
    with open(output_file, 'w') as output:
        # 遍历主目录下的文件夹
        for folder in os.listdir(input_folder):
            folder_path_0 = os.path.join(input_folder, folder)
            if os.path.isdir(folder_path_0) and folder != '__pycache__':
                # 确保是文件夹
                for folder_count in os.listdir(folder_path_0):
                    folder_path = os.path.join(folder_path_0, folder_count)
                    if os.path.isdir(folder_path):
                    # 找到输出文件的路径
                        setting_file_path = os.path.join(folder_path, 'setting.txt')
                        outdebug_file_path = os.path.join(folder_path, 'pdct_distri.txt')
                        printout_file_path = os.path.join(folder_path, 'PrintOut.txt')

                        if os.path.exists(setting_file_path):
                            with open(setting_file_path, 'r') as setting_file:
                                fuelDinner, fuelDouter, H_core, HP_D_outer, P_unit_fuel,\
                                    wall_1, wall_2, heat_power, fuel_T, monolith_T, temp_pipe, fuel = get_initial_values_set(setting_file, 0)
                                
                                if os.path.exists(outdebug_file_path):
                                    with open(outdebug_file_path, 'r') as outdebug_file:
                                        vecs = get_thermal_tot_vec(outdebug_file)
                                        vec = vecs[0]

                                        if "N/A" in [fuelDinner, fuelDouter, H_core, HP_D_outer,
                                                P_unit_fuel, wall_1, wall_2, heat_power, fuel_T,
                                                monolith_T, temp_pipe, fuel, vec]:
                                            continue

                                        output.write(f"{fuelDinner},{fuelDouter},{H_core},{HP_D_outer},"
                                                    f"{P_unit_fuel},{wall_1},{wall_2},{heat_power},{fuel_T},"
                                                    f"{monolith_T},{temp_pipe},{fuel},")
                                        output.write(','.join(map(str, vec)) + '\n')

                                        if len(vecs) > 1:
                                            count_num = len(vecs)
                                            for i in range(count_num - 1):
                                                if os.path.exists(printout_file_path):
                                                    with open(printout_file_path, 'r') as print_out_file:
                                                        H_core, P_unit_fuel, wall_1, wall_2, fuel_T, monolith_T = get_new_geo_temp(print_out_file, i)
                                                        vec = vecs[i + 1] if vecs else "N/A"
                                                        if "N/A" in [fuelDinner, fuelDouter, H_core, HP_D_outer,
                                                                    P_unit_fuel, wall_1, wall_2, heat_power, fuel_T,
                                                                    monolith_T, temp_pipe, fuel, vec]:
                                                            continue
                                                        output.write(f"{fuelDinner},{fuelDouter},{H_core},{HP_D_outer},"
                                                            f"{P_unit_fuel},{wall_1},{wall_2},{heat_power},{fuel_T},"
                                                            f"{monolith_T},{temp_pipe},{fuel},") #12个几何、功率、温度等输入参数
                                                        output.write(','.join(map(str, vec)) + '\n')

def predict_mono_avg_temp(input_folder, output_file):
    #输入：功率分布、热管壁温分布、基体导热率
    #输出：基体平均温度
    with open(output_file, 'w') as output:
        # 遍历主目录下的文件夹
        for folder in os.listdir(input_folder):
            folder_path_0 = os.path.join(input_folder, folder)
            if os.path.isdir(folder_path_0):
            # 确保是文件夹
                for folder_count in os.listdir(folder_path_0):
                    folder_path = os.path.join(folder_path_0, folder_count)
                    if os.path.isdir(folder_path):
                    # 找到输出文件的路径
                        outdebug_file_path = os.path.join(folder_path, 'out_debugdata.txt')
                        out_fenicsdata_heatpipe_process_path = os.path.join(folder_path, 'out_fenicsdata_heatpipe_process.txt')
                        out_the_thermal_data_path = os.path.join(folder_path, 'out_the_thermal_data.txt')
                        PrintOut_path = os.path.join(folder_path, 'PrintOut.txt')

                        # 检查输出文件是否存在
                        if os.path.exists(outdebug_file_path):
                            with open(outdebug_file_path, 'r') as outdebug_file:
                                vecs = get_thermal_tot_vec(outdebug_file)
                                vec = vecs[0] if vecs else "N/A"

                                if os.path.exists(out_fenicsdata_heatpipe_process_path):
                                    with open(out_fenicsdata_heatpipe_process_path, 'r') as out_fenicsdata_heatpipe_process:
                                        hp_step_matches, temps = get_heatpipe_temp(out_fenicsdata_heatpipe_process)
                                        indices_of_zero = [i for i, x in enumerate(hp_step_matches) if x == 0]
                                        if len(indices_of_zero) > 1:
                                            index = indices_of_zero[1] - 1
                                            temp = temps[index] if temps else "N/A"# 72个输入HP温度
                                        else:
                                            temp = temps[-1] if temps else "N/A"# 72个输入HP温度

                                    if os.path.exists(out_the_thermal_data_path):
                                        with open(out_the_thermal_data_path, 'r') as out_the_thermal_data: 
                                            mono_consts = get_mono_consts(out_the_thermal_data)
                                            mono_const = mono_consts[0] if mono_consts else "N/A"
                                            # output.write(f"{mono_const},") # 1个输入基体热导率

                                        if os.path.exists(PrintOut_path):
                                            with open(PrintOut_path, 'r') as PrintOut:
                                                mono_temps = get_mono_temps(PrintOut)
                                                mono_temp = mono_temps[0] if mono_temps else "N/A"
                                                mono_temp = float(mono_temp) - 300 if mono_temps and float(mono_temp) > 1200 else mono_temp

                                                if "N/A" in [vec, temp, mono_const, mono_temp]:
                                                    continue
                                                vec_str = ','.join(map(str, vec))
                                                temp_str = ','.join(map(str, temp))
                                                output.write(f"{vec_str},{temp_str},{mono_const},")
                                                output.write(f"{mono_temp}\n") # 1个输出基体平均温度

                                                if len(vecs) > 1:
                                                    count_num = len(vecs)
                                                    for i in range(count_num - 1):
                                                        j = i + 1
                                                        vec = vecs[j]
                                                        if j == count_num - 1:
                                                            temp = temps[-1]
                                                        else:
                                                            index = indices_of_zero[j] - 1
                                                            temp = temps[index] if temp else "N/A"
                                                        mono_const = mono_consts[j] if mono_const else "N/A"
                                                        mono_temp = mono_temps[j] if j < len(mono_temps) else "N/A"
                                                        if "N/A" in [vec, temp, mono_const, mono_temp]:
                                                            continue
                                                        vec_str = ','.join(map(str, vec))
                                                        temp_str = ','.join(map(str, temp))
                                                        output.write(f"{vec_str},{temp_str},{mono_const},")
                                                        output.write(f"{mono_temp}\n") # 1个输出基体平均温度
                                                    

def predict_HP_temp_distri(input_folder, output_file):
    #输入：热管直径HP_D_outer、燃料棒直径fuelDinner、热管平均温度、燃料棒功率分布
    #输出：HP温度分布
    with open(output_file, 'w') as output:
        # 遍历主目录下的文件夹
        for folder in os.listdir(input_folder):
            folder_path_0 = os.path.join(input_folder, folder)

            # 确保是文件夹
            if os.path.isdir(folder_path_0):
                for folder_count in os.listdir(folder_path_0):
                    folder_path = os.path.join(folder_path_0, folder_count)
                    if os.path.isdir(folder_path):
                    #输入：热管直径HP_D_outer、燃料棒直径fuelDinner、热管平均温度
                        setting_file_path = os.path.join(folder_path, 'setting.txt')
                        if os.path.exists(setting_file_path):
                            with open(setting_file_path, 'r') as setting_file:
                                fuelDinner, fuelDouter, H_core, HP_D_outer, P_unit_fuel,\
                                    wall_1, wall_2, heat_power, fuel_T, monolith_T, temp_pipe, fuel = get_initial_values_set(setting_file, 0)

                                #输入：功率分布
                                distri_path = os.path.join(folder_path, 'pdct_distri.txt')
                                if os.path.exists(distri_path):
                                    with open(distri_path, 'r') as distri_file:
                                        content = distri_file.read()
                                        data_list = content.replace(' ', ',')
                                        data_list = data_list.replace('\n', ',')
                                        
                                        #输出：HP温度分布
                                        out_fenicsdata_heatpipe_process_path = os.path.join(folder_path, 'out_fenicsdata_heatpipe_process.txt')
                                        if os.path.exists(out_fenicsdata_heatpipe_process_path):
                                            with open(out_fenicsdata_heatpipe_process_path, 'r') as out_fenicsdata_heatpipe_process:
                                                hp_step_matches, temps = get_heatpipe_temp(out_fenicsdata_heatpipe_process)
                                                indices_of_zero = [i for i, x in enumerate(hp_step_matches) if x == 0]
                                                if len(indices_of_zero) > 1:
                                                    index = indices_of_zero[1] - 1
                                                    temp = temps[index] if temps else "N/A"# 72个输入HP温度
                                                else:
                                                    temp = temps[-1] if temps else "N/A"# 72个输入HP温度

                                                
                                                # temp = 
                                                output.write(f"{HP_D_outer},{fuelDinner},{temp_pipe},")
                                                output.write(data_list)
                                                output.write(','.join(map(str, temp)) + '\n')

def predict_keff_for_sobol(input_folder, output_file, filename = None): # 9+1+112 = 122
    #输入：9
    #输出：keff+powerdistri
    with open(output_file, 'w') as output:
        # 遍历主目录下的文件夹
        for folder in os.listdir(input_folder):
            folder_path_0 = os.path.join(input_folder, folder)
            # if os.path.isdir(folder_path_0) and folder != '__pycache__':
            if os.path.isdir(folder_path_0) and folder == filename:
            # 确保是文件夹
                folder_tot_count = count_numeric_folders(folder_path_0)
                num_10_count = 10 * int(folder_tot_count/10)
                if num_10_count > 0:
                    for folder_count in sorted([x for x in os.listdir(folder_path_0) if x.isdigit()], key=lambda x: int(x)):
                        if folder_count.isnumeric():  # 检查文件夹名称是否为纯数字
                            folder_count_0 = int(folder_count)
                            if folder_count_0 < num_10_count:
                            # 确保是文件夹
                            # if os.path.isdir(folder_path_0):
                            #     for folder_count in os.listdir(folder_path_0):
                                folder_path = os.path.join(folder_path_0, str(folder_count_0))
                                if os.path.isdir(folder_path):
                                #输入：热管直径HP_D_outer、燃料棒直径fuelDinner、热管平均温度
                                    setting_file_path = os.path.join(folder_path, 'setting.txt')
                                    if os.path.exists(setting_file_path):
                                        with open(setting_file_path, 'r') as setting_file:
                                            # fuelDinner, fuelDouter, H_core, HP_D_outer, P_unit_fuel,\
                                            #     wall_1, fuel_T, monolith_T, temp_pipe, fuel = get_initial_values_set(setting_file, 0)
                                            
                                            fuelDinner, fuelDouter, H_core, HP_D_outer, P_unit_fuel,\
                                                wall_1, fuel_T, monolith_T, temp_pipe, fuel = get_initial_values_set(setting_file, 0)

                                            #输入：功率分布
                                            NN_keff_distri_path = os.path.join(folder_path, 'NN_keff_distri.txt')
                                            # distri_path = os.path.join(folder_path, 'pdct_distri.txt')
                                            # if os.path.exists(NN_keff_distri_path):
                                            #     with open(NN_keff_distri_path, 'r') as distri_file:
                                            #         content = distri_file.read()
                                            #         data_list = content.replace(' ', '')
                                            #         data_list = data_list.replace(' ', '')
                                            #         # data_list = data_list.replace('\n', '')
                                            #         data_list = data_list.replace('[', '')
                                            #         data_list = data_list.replace(']', '')
                                            #         # data_list = data_list.replace('\n', ',')
                                                    
                                            
                                            output.write(f"{fuelDinner},{fuelDouter},{H_core},{HP_D_outer},{P_unit_fuel},{wall_1},{fuel_T},{monolith_T},{temp_pipe},{fuel}\n")
                                                    # output.write(data_list)
                                                    # output.write(','.join(map(str, temp)) + '\n')

def predict_HP_temp_distri_for_sobol(input_folder, output_file):
    #输入：热管直径HP_D_outer、燃料棒直径fuelDinner、热管平均温度、燃料棒功率分布
    #输出：HP温度分布
    with open(output_file, 'w') as output:
        # 遍历主目录下的文件夹
        for folder in os.listdir(input_folder):
            folder_path_0 = os.path.join(input_folder, folder)
            if os.path.isdir(folder_path_0) and folder != '__pycache__':
            # if os.path.isdir(folder_path_0) and folder == '2024_03_22_23_12_36':
            # 确保是文件夹
                folder_tot_count = count_numeric_folders(folder_path_0)
                num_18_count = 18 * int(folder_tot_count/18)
                if num_18_count > 0:
                    for folder_count in sorted(os.listdir(folder_path_0), key=lambda x: int(x)):
                        if folder_count.isnumeric():  # 检查文件夹名称是否为纯数字
                            folder_count_0 = int(folder_count)
                            if folder_count_0 < num_18_count:
                            # 确保是文件夹
                            # if os.path.isdir(folder_path_0):
                            #     for folder_count in os.listdir(folder_path_0):
                                folder_path = os.path.join(folder_path_0, str(folder_count_0))
                                if os.path.isdir(folder_path):
                                #输入：热管直径HP_D_outer、燃料棒直径fuelDinner、热管平均温度
                                    setting_file_path = os.path.join(folder_path, 'setting.txt')
                                    if os.path.exists(setting_file_path):
                                        with open(setting_file_path, 'r') as setting_file:
                                            fuelDinner, fuelDouter, H_core, HP_D_outer, P_unit_fuel,\
                                                wall_1, wall_2, heat_power, fuel_T, monolith_T, temp_pipe, fuel = get_initial_values_set(setting_file, 0)

                                            #输入：功率分布
                                            distri_path = os.path.join(folder_path, 'pdct_distri.txt')
                                            if os.path.exists(distri_path):
                                                with open(distri_path, 'r') as distri_file:
                                                    content = distri_file.read()
                                                    data_list = content.replace(' ', ',')
                                                    data_list = data_list.replace('\n', ',')
                                                    
                                                    #输出：HP温度分布
                                                    out_fenicsdata_heatpipe_process_path = os.path.join(folder_path, 'out_fenicsdata_heatpipe_process.txt')
                                                    if os.path.exists(out_fenicsdata_heatpipe_process_path):
                                                        with open(out_fenicsdata_heatpipe_process_path, 'r') as out_fenicsdata_heatpipe_process:
                                                            hp_step_matches, temps = get_heatpipe_temp(out_fenicsdata_heatpipe_process)
                                                            indices_of_zero = [i for i, x in enumerate(hp_step_matches) if x == 0]
                                                            if len(indices_of_zero) > 1:
                                                                index = indices_of_zero[1] - 1
                                                                temp = temps[index] if temps else "N/A"# 72个输入HP温度
                                                            else:
                                                                temp = temps[-1] if temps else "N/A"# 72个输入HP温度

                                                            
                                                            # temp = 
                                                            output.write(f"{HP_D_outer},{fuelDinner},{temp_pipe},")
                                                            output.write(data_list)
                                                            output.write(','.join(map(str, temp)) + '\n')

def predict_mono_temp(input_folder, output_file):
    #输入：功率分布、热管壁温、基体导热率(基体初始温度)
    #输出：基体mean温度、基体max温度
    with open(output_file, 'w') as output:
        # 遍历主目录下的文件夹
        for folder in os.listdir(input_folder):
            folder_path_0 = os.path.join(input_folder, folder)

            # 确保是文件夹
            if os.path.isdir(folder_path_0):
                for folder_count in os.listdir(folder_path_0):
                    folder_path = os.path.join(folder_path_0, folder_count)
                    if os.path.isdir(folder_path):
                        #输入：基体初始温度
                        setting_file_path = os.path.join(folder_path, 'setting.txt')
                        if os.path.exists(setting_file_path):
                            with open(setting_file_path, 'r') as setting_file:
                                fuelDinner, fuelDouter, H_core, HP_D_outer, P_unit_fuel,\
                                    wall_1, wall_2, heat_power, fuel_T, monolith_T, temp_pipe, fuel = get_initial_values_set(setting_file, 0)

                                #输入：功率分布
                                distri_path = os.path.join(folder_path, 'pdct_distri.txt')
                                if os.path.exists(distri_path):
                                    with open(distri_path, 'r') as distri_file:
                                        content = distri_file.read()
                                        data_list = content.replace(' ', ',')
                                        data_list = data_list.replace('\n', ',')
                                        
                                        #输入：HP温度分布
                                        out_fenicsdata_heatpipe_process_path = os.path.join(folder_path, 'out_fenicsdata_heatpipe_process.txt')
                                        if os.path.exists(out_fenicsdata_heatpipe_process_path):
                                            with open(out_fenicsdata_heatpipe_process_path, 'r') as out_fenicsdata_heatpipe_process:
                                                hp_step_matches, temps = get_heatpipe_temp(out_fenicsdata_heatpipe_process)
                                                indices_of_zero = [i for i, x in enumerate(hp_step_matches) if x == 0]
                                                if len(indices_of_zero) > 1:
                                                    index = indices_of_zero[1] - 1
                                                    temp = temps[index] if temps else "N/A"# 72个输入HP温度
                                                else:
                                                    temp = temps[-1] if temps else "N/A"# 72个输入HP温度

                                                #输入：基体导热率
                                                mono_conduc = caluSS316ThermalConduct(monolith_T) if monolith_T else "N/A"

                                                #输出：基体mean温度、基体max温度
                                                PrintOut_path = os.path.join(folder_path, 'PrintOut.txt')
                                                if os.path.exists(PrintOut_path):
                                                    with open(PrintOut_path, 'r') as PrintOut:
                                                        monolith_mean_temperature, monolith_max_temperature = get_monotemp_mean_max(PrintOut)

                                                        if "N/A" in [data_list, temp, mono_conduc, monolith_mean_temperature, monolith_max_temperature]:
                                                            continue
                                                        # output.write(f"{fuelDinner},")
                                                        # # output.write(f"{fuelDouter},")
                                                        # output.write(f"{H_core},")
                                                        # output.write(f"{HP_D_outer},")
                                                        # # output.write(f"{wall_1},")
                                                        # output.write(f"{wall_2},")
                                                        # output.write(f"{P_unit_fuel},")
                                                        # # output.write(f"{heat_power},")
                                                        # output.write(f"{fuel_T},")
                                                        # output.write(f"{monolith_T},")
                                                        # output.write(f"{temp_pipe},")
                                                        # output.write(f"{fuel},")


                                                        output.write(f"{fuelDinner},")
                                                        # output.write(f"{fuel_D_outer},")
                                                        output.write(f"{H_core},")
                                                        output.write(f"{HP_D_outer},")
                                                        # output.write(f"{wall_1},")
                                                        # output.write(f"{wall_2},")
                                                        # output.write(f"{P_unit_fuel},")
                                                        # output.write(f"{heat_power},")
                                                        output.write(f"{fuel_T},")
                                                        output.write(f"{monolith_T},")
                                                        output.write(f"{temp_pipe},")
                                                        output.write(f"{fuel},")
                                                        output.write(f"{wall_2},")
                                                        output.write(f"{P_unit_fuel},") 


                                                        output.write(data_list)
                                                        output.write(','.join(map(str, temp)) + ',')
                                                        output.write(f"{mono_conduc},{monolith_mean_temperature},{monolith_max_temperature}\n")

def predict_mono_temp_for_sobol(input_folder, output_file):
    #输入：功率分布、热管壁温、基体导热率(基体初始温度)
    #输出：基体mean温度、基体max温度
    with open(output_file, 'w') as output:
        # 遍历主目录下的文件夹
        for folder in os.listdir(input_folder):
            folder_path_0 = os.path.join(input_folder, folder)
            if os.path.isdir(folder_path_0) and folder != '__pycache__':
            # if os.path.isdir(folder_path_0) and folder == '2024_03_22_23_12_36':
            # 确保是文件夹
                folder_tot_count = count_numeric_folders(folder_path_0)
                num_18_count = 18 * int(folder_tot_count/18)
                if num_18_count > 0:
                    for folder_count in sorted(os.listdir(folder_path_0), key=lambda x: int(x)):
                        if folder_count.isnumeric():  # 检查文件夹名称是否为纯数字
                            folder_count_0 = int(folder_count)
                            if folder_count_0 < num_18_count:
                                folder_path = os.path.join(folder_path_0, str(folder_count_0))
                                if os.path.isdir(folder_path):
                                    #输入：基体初始温度
                                    setting_file_path = os.path.join(folder_path, 'setting.txt')
                                    if os.path.exists(setting_file_path):
                                        with open(setting_file_path, 'r') as setting_file:
                                            fuelDinner, fuelDouter, H_core, HP_D_outer, P_unit_fuel,\
                                                wall_1, wall_2, heat_power, fuel_T, monolith_T, temp_pipe, fuel = get_initial_values_set(setting_file, 0)

                                            #输入：功率分布
                                            distri_path = os.path.join(folder_path, 'pdct_distri.txt')
                                            if os.path.exists(distri_path):
                                                with open(distri_path, 'r') as distri_file:
                                                    content = distri_file.read()
                                                    data_list = content.replace(' ', ',')
                                                    data_list = data_list.replace('\n', ',')
                                                    
                                                    #输入：HP温度分布
                                                    out_fenicsdata_heatpipe_process_path = os.path.join(folder_path, 'out_fenicsdata_heatpipe_process.txt')
                                                    if os.path.exists(out_fenicsdata_heatpipe_process_path):
                                                        with open(out_fenicsdata_heatpipe_process_path, 'r') as out_fenicsdata_heatpipe_process:
                                                            hp_step_matches, temps = get_heatpipe_temp(out_fenicsdata_heatpipe_process)
                                                            indices_of_zero = [i for i, x in enumerate(hp_step_matches) if x == 0]
                                                            if len(indices_of_zero) > 1:
                                                                index = indices_of_zero[1] - 1
                                                                temp = temps[index] if temps else "N/A"# 72个输入HP温度
                                                            else:
                                                                temp = temps[-1] if temps else "N/A"# 72个输入HP温度

                                                            #输入：基体导热率
                                                            mono_conduc = caluSS316ThermalConduct(monolith_T) if monolith_T else "N/A"

                                                            #输出：基体mean温度、基体max温度
                                                            PrintOut_path = os.path.join(folder_path, 'PrintOut.txt')
                                                            if os.path.exists(PrintOut_path):
                                                                with open(PrintOut_path, 'r') as PrintOut:
                                                                    monolith_mean_temperature, monolith_max_temperature = get_monotemp_mean_max(PrintOut)

                                                                    if "N/A" in [data_list, temp, mono_conduc, monolith_mean_temperature, monolith_max_temperature]:
                                                                        continue

                                                                    output.write(data_list)
                                                                    output.write(','.join(map(str, temp)) + ',')
                                                                    output.write(f"{mono_conduc},{monolith_mean_temperature},{monolith_max_temperature}\n")
                                                        
def predict_expansion(input_folder, output_file):
    #输入：功率分布、热管壁温、基体导热率(基体初始温度)
    #输出：膨胀的5个几何参数
    '''New wall2: 29.91981116748243 cm
    New pitch_fuel: 1.6159222909020048 cm
    New pitch_HP: 2.7988595089253674 cm
    New Hcore: 152.319292614155 cm
    Relative change of monolith volume: 0.036384578331906454'''
    with open(output_file, 'w') as output:
        # 遍历主目录下的文件夹
        for folder in os.listdir(input_folder):
            folder_path_0 = os.path.join(input_folder, folder)

            # 确保是文件夹
            if os.path.isdir(folder_path_0):
                for folder_count in os.listdir(folder_path_0):
                    folder_path = os.path.join(folder_path_0, folder_count)
                    if os.path.isdir(folder_path):
                    # 找到输出文件的路径
                        outdebug_file_path = os.path.join(folder_path, 'out_debugdata.txt')
                        out_fenicsdata_heatpipe_process_path = os.path.join(folder_path, 'out_fenicsdata_heatpipe_process.txt')
                        out_the_thermal_data_path = os.path.join(folder_path, 'out_the_thermal_data.txt')
                        PrintOut_path = os.path.join(folder_path, 'PrintOut.txt')
                        setting_file_path = os.path.join(folder_path, 'setting.txt')

                        # 检查输出文件是否存在
                        # 输入：功率分布
                        distri_path = os.path.join(folder_path, 'pdct_distri.txt')
                        if os.path.exists(distri_path):
                            with open(distri_path, 'r') as distri_file:
                                content = distri_file.read()
                                data_list = content.replace(' ', ',')
                                data_list = data_list.replace('\n', ',')

                                # 输入：热管壁温                           
                                if os.path.exists(out_fenicsdata_heatpipe_process_path):
                                    with open(out_fenicsdata_heatpipe_process_path, 'r') as out_fenicsdata_heatpipe_process:
                                        hp_step_matches, temps = get_heatpipe_temp(out_fenicsdata_heatpipe_process)
                                        indices_of_zero = [i for i, x in enumerate(hp_step_matches) if x == 0]
                                        if len(indices_of_zero) > 1:
                                            index = indices_of_zero[1] - 1
                                            temp = temps[index] if temps else "N/A"# 72个输入HP温度
                                        else:
                                            temp = temps[-1] if temps else "N/A"# 72个输入HP温度

                                    # 输入：基体导热率(基体初始温度)
                                    if os.path.exists(setting_file_path):
                                        with open(setting_file_path, 'r') as setting_file:
                                            fuelDinner, fuelDouter, H_core, HP_D_outer, P_unit_fuel,\
                                                wall_1, wall_2, heat_power, fuel_T, monolith_T, temp_pipe, fuel = get_initial_values_set(setting_file, 0)
                                            mono_conduc = caluSS316ThermalConduct(monolith_T) if monolith_T else "N/A"

                                        #输出：膨胀的5个几何参数
                                        if os.path.exists(PrintOut_path):
                                            with open(PrintOut_path, 'r') as PrintOut:
                                                wall2, pitch_fuel, pitch_HP, Hcore, volume = get_geo_vecs(PrintOut)
                                                
                                                if "N/A" in [data_list, temp, mono_conduc, wall2, pitch_fuel, pitch_HP, Hcore, volume]:
                                                    continue
                                                output.write(f"{fuelDinner},")
                                                # output.write(f"{fuel_D_outer},")
                                                output.write(f"{H_core},")
                                                output.write(f"{HP_D_outer},")
                                                # output.write(f"{wall_1},")
                                                # output.write(f"{wall_2},")
                                                # output.write(f"{P_unit_fuel},")
                                                # output.write(f"{heat_power},")
                                                output.write(f"{fuel_T},")
                                                output.write(f"{monolith_T},")
                                                output.write(f"{temp_pipe},")
                                                output.write(f"{fuel},")
                                                output.write(f"{wall_2},")
                                                output.write(f"{P_unit_fuel},") 


                                                output.write(f"{wall2},")
                                                output.write(f"{pitch_fuel},")
                                                output.write(f"{Hcore}\n")
                                                # output.write(f"{wall_2},")

                                                
def predict_fuel_temp(input_folder, output_file):
    #输入：功率分布、热管壁温、基体导热率(基体初始温度)
    #输出：各燃料边界温度
    with open(output_file, 'w') as output:
        # 遍历主目录下的文件夹
        for folder in os.listdir(input_folder):
            folder_path_0 = os.path.join(input_folder, folder)

            # 确保是文件夹
            if os.path.isdir(folder_path_0):
                for folder_count in os.listdir(folder_path_0):
                    folder_path = os.path.join(folder_path_0, folder_count)
                    if os.path.isdir(folder_path):
                        #输入：基体初始温度
                        setting_file_path = os.path.join(folder_path, 'setting.txt')
                        if os.path.exists(setting_file_path):
                            with open(setting_file_path, 'r') as setting_file:
                                fuelDinner, fuelDouter, H_core, HP_D_outer, P_unit_fuel,\
                                    wall_1, wall_2, heat_power, fuel_T, monolith_T, temp_pipe, fuel = get_initial_values_set(setting_file, 0)

                                #输入：功率分布
                                distri_path = os.path.join(folder_path, 'pdct_distri.txt')
                                if os.path.exists(distri_path):
                                    with open(distri_path, 'r') as distri_file:
                                        content = distri_file.read()
                                        data_list = content.replace(' ', ',')
                                        data_list = data_list.replace('\n', ',')
                                        
                                        #输入：HP温度分布
                                        out_fenicsdata_heatpipe_process_path = os.path.join(folder_path, 'out_fenicsdata_heatpipe_process.txt')
                                        if os.path.exists(out_fenicsdata_heatpipe_process_path):
                                            with open(out_fenicsdata_heatpipe_process_path, 'r') as out_fenicsdata_heatpipe_process:
                                                hp_step_matches, temps = get_heatpipe_temp(out_fenicsdata_heatpipe_process)
                                                indices_of_zero = [i for i, x in enumerate(hp_step_matches) if x == 0]
                                                if len(indices_of_zero) > 1:
                                                    index = indices_of_zero[1] - 1
                                                    temp = temps[index] if temps else "N/A"# 72个输入HP温度
                                                else:
                                                    temp = temps[-1] if temps else "N/A"# 72个输入HP温度

                                                #输入：基体导热率
                                                mono_conduc = caluSS316ThermalConduct(monolith_T) if monolith_T else "N/A"

                                                #输出：各燃料边界温度
                                                PrintOut_path = os.path.join(folder_path, 'fuel_T_list.txt')
                                                if os.path.exists(PrintOut_path):
                                                    with open(PrintOut_path, 'r') as PrintOut:
                                                        content = PrintOut.read()
                                                        fuel_T_list = content.replace('\n', ',')
                                                        fuel_T_list = fuel_T_list.rstrip(', ')
                                                        # fuel_T_list = fuel_T_list[:-1]

                                                        if "N/A" in [data_list, temp, mono_conduc, fuel_T_list]:
                                                            continue

                                                        output.write(data_list)
                                                        output.write(','.join(map(str, temp)) + ',')
                                                        output.write(f"{mono_conduc},")
                                                        output.write(fuel_T_list + '\n')

# def predict_fuel_temp_no_nan(input_folder, output_file):
#     #输入：功率分布、热管壁温、基体导热率(基体初始温度)
#     #输出：各燃料边界温度
#     with open(output_file, 'w') as output:
#         # 遍历主目录下的文件夹
#         for folder in os.listdir(input_folder):
#             folder_path_0 = os.path.join(input_folder, folder)

#             # 确保是文件夹
#             if os.path.isdir(folder_path_0):
#                 for folder_count in os.listdir(folder_path_0):
#                     folder_path = os.path.join(folder_path_0, folder_count)
#                     if os.path.isdir(folder_path):
#                         #输入：基体初始温度
#                         setting_file_path = os.path.join(folder_path, 'setting.txt')
#                         if os.path.exists(setting_file_path):
#                             with open(setting_file_path, 'r') as setting_file:
#                                 fuelDinner, fuelDouter, H_core, HP_D_outer, P_unit_fuel,\
#                                     wall_1, wall_2, heat_power, fuel_T, monolith_T, temp_pipe, fuel = get_initial_values_set(setting_file, 0)

#                                 #输入：功率分布
#                                 distri_path = os.path.join(folder_path, 'pdct_distri.txt')
#                                 if os.path.exists(distri_path):
#                                     with open(distri_path, 'r') as distri_file:
#                                         content = distri_file.read()
#                                         data_list = content.replace(' ', ',')
#                                         data_list = data_list.replace('\n', ',')
                                        
#                                         #输入：HP温度分布
#                                         out_fenicsdata_heatpipe_process_path = os.path.join(folder_path, 'out_fenicsdata_heatpipe_process.txt')
#                                         if os.path.exists(out_fenicsdata_heatpipe_process_path):
#                                             with open(out_fenicsdata_heatpipe_process_path, 'r') as out_fenicsdata_heatpipe_process:
#                                                 hp_step_matches, temps = get_heatpipe_temp(out_fenicsdata_heatpipe_process)
#                                                 indices_of_zero = [i for i, x in enumerate(hp_step_matches) if x == 0]
#                                                 if len(indices_of_zero) > 1:
#                                                     index = indices_of_zero[1] - 1
#                                                     temp = temps[index] if temps else "N/A"# 72个输入HP温度
#                                                 else:
#                                                     temp = temps[-1] if temps else "N/A"# 72个输入HP温度

#                                                 #输入：基体导热率
#                                                 mono_conduc = caluSS316ThermalConduct(monolith_T) if monolith_T else "N/A"

#                                                 #输出：各燃料边界温度
#                                                 PrintOut_path = os.path.join(folder_path, 'fuel_T_list.txt')
#                                                 if os.path.exists(PrintOut_path):
#                                                     with open(PrintOut_path, 'r') as PrintOut:
#                                                         content = PrintOut.read()
#                                                         fuel_T_list = content.replace('\n', ',')
#                                                         fuel_T_list = fuel_T_list.rstrip(', ')
#                                                         # fuel_T_list = fuel_T_list[:-1]

#                                                         if "N/A" in [data_list, temp, mono_conduc, fuel_T_list] or 'nan' in fuel_T_list.lower():
#                                                             continue

#                                                         output.write(data_list)
#                                                         output.write(','.join(map(str, temp)) + ',')
#                                                         output.write(f"{mono_conduc},")
#                                                         output.write(fuel_T_list + '\n')
                  
def predict_fuel_temp_no_nan(input_folder, output_file):
    # 输入：功率分布、热管壁温、基体导热率(基体初始温度)
    # 输出：各燃料边界温度
    with open(output_file, 'w') as output:
        # 遍历主目录下的文件夹
        for folder in os.listdir(input_folder):
            folder_path_0 = os.path.join(input_folder, folder)
            # 确保是文件夹
            if os.path.isdir(folder_path_0):
                for folder_count in os.listdir(folder_path_0):
                    folder_path = os.path.join(folder_path_0, folder_count)
                    if os.path.isdir(folder_path):
                        # 输入：基体初始温度
                        setting_file_path = os.path.join(folder_path, 'setting.txt')
                        if os.path.exists(setting_file_path):
                            with open(setting_file_path, 'r') as setting_file:
                                # 获取初始值
                                fuel_D_inner, fuel_D_outer, H_core, HP_D_outer, P_unit_fuel, \
                                    wall_1, wall_2, heat_power, fuel_T, monolith_T, temp_pipe, fuel = get_initial_values_set(setting_file, 0)
                                
                                # 输入：功率分布
                                distri_path = os.path.join(folder_path, 'pdct_distri.txt')
                                if os.path.exists(distri_path):
                                    with open(distri_path, 'r') as distri_file:
                                        content = distri_file.read()
                                        data_list = content.replace(' ', ',')
                                        data_list = data_list.replace('\n', ',')
                                        
                                        # 输入：HP温度分布
                                        out_fenicsdata_heatpipe_process_path = os.path.join(folder_path, 'out_fenicsdata_heatpipe_process.txt')
                                        if os.path.exists(out_fenicsdata_heatpipe_process_path):
                                            with open(out_fenicsdata_heatpipe_process_path, 'r') as out_fenicsdata_heatpipe_process:
                                                hp_step_matches, temps = get_heatpipe_temp(out_fenicsdata_heatpipe_process)
                                                indices_of_zero = [i for i, x in enumerate(hp_step_matches) if x == 0]
                                                if len(indices_of_zero) > 1:
                                                    index = indices_of_zero[1] - 1
                                                    temp = temps[index] if temps else "N/A"  # 72个输入HP温度
                                                else:
                                                    temp = temps[-1] if temps else "N/A"  # 72个输入HP温度
                                                
                                                # 输入：基体导热率
                                                mono_conduc = caluSS316ThermalConduct(monolith_T) if monolith_T else "N/A"
                                                
                                                # 输出：各燃料边界温度
                                                PrintOut_path = os.path.join(folder_path, 'fuel_T_list.txt')
                                                if os.path.exists(PrintOut_path):
                                                    with open(PrintOut_path, 'r') as PrintOut:
                                                        content = PrintOut.read()
                                                        fuel_T_list = content.replace('\n', ',')
                                                        fuel_T_list = fuel_T_list.rstrip(', ')
                                                        if "N/A" in [data_list, temp, mono_conduc, fuel_T_list] or 'nan' in fuel_T_list.lower():
                                                            continue
                                                        
                                                        # 先保存 11 个参数
                                                        output.write(f"{fuel_D_inner},")
                                                        # output.write(f"{fuel_D_outer},")
                                                        output.write(f"{H_core},")
                                                        output.write(f"{HP_D_outer},")
                                                        # output.write(f"{wall_1},")
                                                        # output.write(f"{wall_2},")
                                                        # output.write(f"{P_unit_fuel},")
                                                        # output.write(f"{heat_power},")
                                                        output.write(f"{fuel_T},")
                                                        output.write(f"{monolith_T},")
                                                        output.write(f"{temp_pipe},")
                                                        output.write(f"{fuel},")
                                                        output.write(f"{wall_2},")
                                                        output.write(f"{P_unit_fuel},")                                                     
                                                        # 再保存其他数据
                                                        output.write(data_list)
                                                        output.write(','.join(map(str, temp)) + ',')
                                                        output.write(f"{mono_conduc},")
                                                        output.write(fuel_T_list + '\n')

def predict_stress_all(input_folder, output_file, txt_name):
    #输入：功率分布、热管壁温、基体导热率(基体初始温度)->燃料温度分布112、热管壁温分布72、基体导热率1
    #输出：燃料（附近）平均、最大压力；热管（附近）平均、最大压力
    with open(output_file, 'w') as output:
        # 遍历主目录下的文件夹
        for folder in os.listdir(input_folder):
            folder_path_0 = os.path.join(input_folder, folder)

            # 确保是文件夹
            if os.path.isdir(folder_path_0):
                for folder_count in os.listdir(folder_path_0):
                    folder_path = os.path.join(folder_path_0, folder_count)
                    if os.path.isdir(folder_path):
                        #输入：各燃料边界温度
                        PrintOut_path = os.path.join(folder_path, 'fuel_T_list.txt')
                        if os.path.exists(PrintOut_path):
                            with open(PrintOut_path, 'r') as PrintOut:
                                content = PrintOut.read()
                                fuel_T_list = content.replace('\n', ',')
                                fuel_T_list = fuel_T_list.rstrip(', ')
                                # fuel_T_list = fuel_T_list[:-1]

                                if 'nan' in fuel_T_list.lower():
                                    continue

                                # output.write(data_list)
                                # output.write(','.join(map(str, temp)) + ',')
                                # output.write(f"{mono_conduc},")
                                # output.write(fuel_T_list + '\n')
                                #(输入)：基体初始温度
                                setting_file_path = os.path.join(folder_path, 'setting.txt')
                                if os.path.exists(setting_file_path):
                                    with open(setting_file_path, 'r') as setting_file:
                                        fuelDinner, fuelDouter, H_core, HP_D_outer, P_unit_fuel,\
                                            wall_1, wall_2, heat_power, fuel_T, monolith_T, temp_pipe, fuel = get_initial_values_set(setting_file, 0)

                        #         #输入：功率分布
                        #         distri_path = os.path.join(folder_path, 'pdct_distri.txt')
                        #         if os.path.exists(distri_path):
                        #             with open(distri_path, 'r') as distri_file:
                        #                 content = distri_file.read()
                        #                 data_list = content.replace(' ', ',')
                        #                 data_list = data_list.replace('\n', ',')
                                        
                                    #输入：HP温度分布
                                    out_fenicsdata_heatpipe_process_path = os.path.join(folder_path, 'out_fenicsdata_heatpipe_process.txt')
                                    if os.path.exists(out_fenicsdata_heatpipe_process_path):
                                        with open(out_fenicsdata_heatpipe_process_path, 'r') as out_fenicsdata_heatpipe_process:
                                            hp_step_matches, temps = get_heatpipe_temp(out_fenicsdata_heatpipe_process)
                                            indices_of_zero = [i for i, x in enumerate(hp_step_matches) if x == 0]
                                            if len(indices_of_zero) > 1:
                                                index = indices_of_zero[1] - 1
                                                temp = temps[index] if temps else "N/A"# 72个输入HP温度
                                            else:
                                                temp = temps[-1] if temps else "N/A"# 72个输入HP温度

                                            #输入：基体导热率
                                            mono_conduc = caluSS316ThermalConduct(monolith_T) if monolith_T else "N/A"

                                            #输出：燃料（附近）平均、最大压力；热管（附近）平均、最大压力
                                            PrintOut_path = os.path.join(folder_path, txt_name + '.txt')
                                            if os.path.exists(PrintOut_path):
                                                with open(PrintOut_path, 'r') as PrintOut:
                                                    stress_list = PrintOut.read()
                                                    stress_list = stress_list.replace('[', '')
                                                    stress_list = stress_list.replace(']', '')
                                                    stress_list1 = stress_list.split(', ')

                                                    # if "N/A" in [data_list, temp, mono_conduc, stress_list]:
                                                        # continue

                                                    stress_list_float = [float(x) for x in stress_list1]
                                                    if len(stress_list_float) == 72 or len(stress_list_float) == 112:
                                                        # if 'nan' in stress_list.lower():
                                                        #     continue
                                                    # if MEANORMAX == 'MEAN':
                                                    #     stress = mean_value = sum(stress_list_float) / len(stress_list_float)
                                                    # elif MEANORMAX == 'MAX':
                                                    #     stress = max(stress_list_float)

                                                    # output.write(data_list)
                                                        output.write(f"{fuelDinner},")
                                                        # output.write(f"{fuel_D_outer},")
                                                        output.write(f"{H_core},")
                                                        output.write(f"{HP_D_outer},")
                                                        # output.write(f"{wall_1},")
                                                        # output.write(f"{wall_2},")
                                                        # output.write(f"{P_unit_fuel},")
                                                        # output.write(f"{heat_power},")
                                                        output.write(f"{fuel_T},")
                                                        output.write(f"{monolith_T},")
                                                        output.write(f"{temp_pipe},")
                                                        output.write(f"{fuel},")
                                                        output.write(f"{wall_2},")
                                                        output.write(f"{P_unit_fuel},")
                                                        # output.write(fuel_T_list + ',')
                                                        # output.write(','.join(map(str, temp)) + ',')
                                                        # output.write(f"{mono_conduc},")
                                                        output.write(str(stress_list))

def predict_stress(input_folder, output_file, txt_name):
    #输入：功率分布、热管壁温、基体导热率(基体初始温度)->燃料温度分布112、热管壁温分布72、基体导热率1
    #输出：燃料（附近）平均、最大压力；热管（附近）平均、最大压力
    with open(output_file, 'w') as output:
        # 遍历主目录下的文件夹
        for folder in os.listdir(input_folder):
            folder_path_0 = os.path.join(input_folder, folder)

            # 确保是文件夹
            if os.path.isdir(folder_path_0):
                for folder_count in os.listdir(folder_path_0):
                    folder_path = os.path.join(folder_path_0, folder_count)
                    if os.path.isdir(folder_path):
                        #输入：各燃料边界温度
                        PrintOut_path = os.path.join(folder_path, 'fuel_T_list.txt')
                        if os.path.exists(PrintOut_path):
                            with open(PrintOut_path, 'r') as PrintOut:
                                content = PrintOut.read()
                                fuel_T_list = content.replace('\n', ',')
                                fuel_T_list = fuel_T_list.rstrip(', ')
                                # fuel_T_list = fuel_T_list[:-1]

                                if 'nan' in fuel_T_list.lower():
                                    continue

                                # output.write(data_list)
                                # output.write(','.join(map(str, temp)) + ',')
                                # output.write(f"{mono_conduc},")
                                # output.write(fuel_T_list + '\n')
                                #(输入)：基体初始温度
                                setting_file_path = os.path.join(folder_path, 'setting.txt')
                                if os.path.exists(setting_file_path):
                                    with open(setting_file_path, 'r') as setting_file:
                                        fuelDinner, fuelDouter, H_core, HP_D_outer, P_unit_fuel,\
                                            wall_1, wall_2, heat_power, fuel_T, monolith_T, temp_pipe, fuel = get_initial_values_set(setting_file, 0)

                        #         #输入：功率分布
                        #         distri_path = os.path.join(folder_path, 'pdct_distri.txt')
                        #         if os.path.exists(distri_path):
                        #             with open(distri_path, 'r') as distri_file:
                        #                 content = distri_file.read()
                        #                 data_list = content.replace(' ', ',')
                        #                 data_list = data_list.replace('\n', ',')
                                        
                                    #输入：HP温度分布
                                    out_fenicsdata_heatpipe_process_path = os.path.join(folder_path, 'out_fenicsdata_heatpipe_process.txt')
                                    if os.path.exists(out_fenicsdata_heatpipe_process_path):
                                        with open(out_fenicsdata_heatpipe_process_path, 'r') as out_fenicsdata_heatpipe_process:
                                            hp_step_matches, temps = get_heatpipe_temp(out_fenicsdata_heatpipe_process)
                                            indices_of_zero = [i for i, x in enumerate(hp_step_matches) if x == 0]
                                            if len(indices_of_zero) > 1:
                                                index = indices_of_zero[1] - 1
                                                temp = temps[index] if temps else "N/A"# 72个输入HP温度
                                            else:
                                                temp = temps[-1] if temps else "N/A"# 72个输入HP温度

                                            #输入：基体导热率
                                            mono_conduc = caluSS316ThermalConduct(monolith_T) if monolith_T else "N/A"

                                            #输出：燃料（附近）平均、最大压力；热管（附近）平均、最大压力
                                            PrintOut_path = os.path.join(folder_path, txt_name + '.txt')
                                            if os.path.exists(PrintOut_path):
                                                with open(PrintOut_path, 'r') as PrintOut:
                                                    stress_list = PrintOut.read()
                                                    stress_list = stress_list.replace('[', '')
                                                    stress_list = stress_list.replace(']', '')
                                                    # stress_list = stress_list.split(', ')

                                                    # if "N/A" in [data_list, temp, mono_conduc, stress_list]:
                                                        # continue

                                                    # stress_list_float = [float(x) for x in stress_list]
                                                    # if MEANORMAX == 'MEAN':
                                                    #     stress = mean_value = sum(stress_list_float) / len(stress_list_float)
                                                    # elif MEANORMAX == 'MAX':
                                                    #     stress = max(stress_list_float)

                                                    # output.write(data_list)
                                                    output.write(f"{fuelDinner},")
                                                    # output.write(f"{fuel_D_outer},")
                                                    output.write(f"{H_core},")
                                                    output.write(f"{HP_D_outer},")
                                                    # output.write(f"{wall_1},")
                                                    # output.write(f"{wall_2},")
                                                    # output.write(f"{P_unit_fuel},")
                                                    # output.write(f"{heat_power},")
                                                    output.write(f"{fuel_T},")
                                                    output.write(f"{monolith_T},")
                                                    output.write(f"{temp_pipe},")
                                                    output.write(f"{fuel},")
                                                    output.write(f"{wall_2},")
                                                    output.write(f"{P_unit_fuel},")
                                                    # output.write(fuel_T_list + ',')
                                                    # output.write(','.join(map(str, temp)) + ',')
                                                    # output.write(f"{mono_conduc},")
                                                    output.write(str(stress_list))

def predict_stress_mean_max(input_folder, output_file, txt_name, MEANORMAX):
    #输入：功率分布、热管壁温、基体导热率(基体初始温度)->燃料温度分布112、热管壁温分布72、基体导热率1
    #输出：燃料（附近）平均、最大压力；热管（附近）平均、最大压力
    with open(output_file, 'w') as output:
        # 遍历主目录下的文件夹
        for folder in os.listdir(input_folder):
            folder_path_0 = os.path.join(input_folder, folder)

            # 确保是文件夹
            if os.path.isdir(folder_path_0):
                for folder_count in os.listdir(folder_path_0):
                    folder_path = os.path.join(folder_path_0, folder_count)
                    if os.path.isdir(folder_path):
                        #输入：各燃料边界温度
                        PrintOut_path = os.path.join(folder_path, 'fuel_T_list.txt')
                        if os.path.exists(PrintOut_path):
                            with open(PrintOut_path, 'r') as PrintOut:
                                content = PrintOut.read()
                                fuel_T_list = content.replace('\n', ',')
                                fuel_T_list = fuel_T_list.rstrip(', ')
                                # fuel_T_list = fuel_T_list[:-1]

                                if 'nan' in fuel_T_list.lower():
                                    continue

                                # output.write(data_list)
                                # output.write(','.join(map(str, temp)) + ',')
                                # output.write(f"{mono_conduc},")
                                # output.write(fuel_T_list + '\n')
                                #(输入)：基体初始温度
                                setting_file_path = os.path.join(folder_path, 'setting.txt')
                                if os.path.exists(setting_file_path):
                                    with open(setting_file_path, 'r') as setting_file:
                                        fuelDinner, fuelDouter, H_core, HP_D_outer, P_unit_fuel,\
                                            wall_1, wall_2, heat_power, fuel_T, monolith_T, temp_pipe, fuel = get_initial_values_set(setting_file, 0)

                        #         #输入：功率分布
                        #         distri_path = os.path.join(folder_path, 'pdct_distri.txt')
                        #         if os.path.exists(distri_path):
                        #             with open(distri_path, 'r') as distri_file:
                        #                 content = distri_file.read()
                        #                 data_list = content.replace(' ', ',')
                        #                 data_list = data_list.replace('\n', ',')
                                        
                                    #输入：HP温度分布
                                    out_fenicsdata_heatpipe_process_path = os.path.join(folder_path, 'out_fenicsdata_heatpipe_process.txt')
                                    if os.path.exists(out_fenicsdata_heatpipe_process_path):
                                        with open(out_fenicsdata_heatpipe_process_path, 'r') as out_fenicsdata_heatpipe_process:
                                            hp_step_matches, temps = get_heatpipe_temp(out_fenicsdata_heatpipe_process)
                                            indices_of_zero = [i for i, x in enumerate(hp_step_matches) if x == 0]
                                            if len(indices_of_zero) > 1:
                                                index = indices_of_zero[1] - 1
                                                temp = temps[index] if temps else "N/A"# 72个输入HP温度
                                            else:
                                                temp = temps[-1] if temps else "N/A"# 72个输入HP温度

                                            #输入：基体导热率
                                            mono_conduc = caluSS316ThermalConduct(monolith_T) if monolith_T else "N/A"

                                            #输出：燃料（附近）平均、最大压力；热管（附近）平均、最大压力
                                            PrintOut_path = os.path.join(folder_path, txt_name + '.txt')
                                            if os.path.exists(PrintOut_path):
                                                with open(PrintOut_path, 'r') as PrintOut:
                                                    stress_list = PrintOut.read()
                                                    stress_list = stress_list.replace('[', '')
                                                    stress_list = stress_list.replace(']', '')
                                                    stress_list = stress_list.split(', ')

                                                    # if "N/A" in [data_list, temp, mono_conduc, stress_list]:
                                                        # continue

                                                    stress_list_float = [float(x) for x in stress_list]
                                                    if MEANORMAX == 'MEAN':
                                                        stress = mean_value = sum(stress_list_float) / len(stress_list_float)
                                                    elif MEANORMAX == 'MAX':
                                                        stress = max(stress_list_float)

                                                    # output.write(data_list)
                                                    output.write(f"{fuelDinner},")
                                                    # output.write(f"{fuel_D_outer},")
                                                    output.write(f"{H_core},")
                                                    output.write(f"{HP_D_outer},")
                                                    # output.write(f"{wall_1},")
                                                    # output.write(f"{wall_2},")
                                                    # output.write(f"{P_unit_fuel},")
                                                    # output.write(f"{heat_power},")
                                                    output.write(f"{fuel_T},")
                                                    output.write(f"{monolith_T},")
                                                    output.write(f"{temp_pipe},")
                                                    output.write(f"{fuel},")
                                                    output.write(f"{wall_2},")
                                                    output.write(f"{P_unit_fuel},")
                                                    # output.write(fuel_T_list + ',')
                                                    # output.write(','.join(map(str, temp)) + ',')
                                                    # output.write(f"{mono_conduc},")
                                                    output.write(f"{stress}\n")
 
def predict_stress_from_pvd(input_folder, output_file):
    #输入：功率分布、热管壁温、基体导热率(基体初始温度)->燃料温度分布112、热管壁温分布72、基体导热率1
    #输出：燃料（附近）平均、最大压力；热管（附近）平均、最大压力
    with open(output_file, 'w') as output:
        # 遍历主目录下的文件夹
        for folder in os.listdir(input_folder):
            folder_path_0 = os.path.join(input_folder, folder)

            # 确保是文件夹
            if os.path.isdir(folder_path_0):
                for folder_count in os.listdir(folder_path_0):
                    folder_path = os.path.join(folder_path_0, folder_count)
                    if os.path.isdir(folder_path):
                        #输入：各燃料边界温度
                        PrintOut_path = os.path.join(folder_path, 'fuel_T_list.txt')
                        if os.path.exists(PrintOut_path):
                            with open(PrintOut_path, 'r') as PrintOut:
                                content = PrintOut.read()
                                fuel_T_list = content.replace('\n', ',')
                                fuel_T_list = fuel_T_list.rstrip(', ')
                                # fuel_T_list = fuel_T_list[:-1]

                                if 'nan' in fuel_T_list.lower():
                                    continue

                                # output.write(data_list)
                                # output.write(','.join(map(str, temp)) + ',')
                                # output.write(f"{mono_conduc},")
                                # output.write(fuel_T_list + '\n')
                                #(输入)：基体初始温度
                                setting_file_path = os.path.join(folder_path, 'setting.txt')
                                if os.path.exists(setting_file_path):
                                    with open(setting_file_path, 'r') as setting_file:
                                        fuelDinner, fuelDouter, H_core, HP_D_outer, P_unit_fuel,\
                                            wall_1, wall_2, heat_power, fuel_T, monolith_T, temp_pipe, fuel = get_initial_values_set(setting_file, 0)

                        #         #输入：功率分布
                        #         distri_path = os.path.join(folder_path, 'pdct_distri.txt')
                        #         if os.path.exists(distri_path):
                        #             with open(distri_path, 'r') as distri_file:
                        #                 content = distri_file.read()
                        #                 data_list = content.replace(' ', ',')
                        #                 data_list = data_list.replace('\n', ',')
                                        
                                    #输入：HP温度分布
                                    out_fenicsdata_heatpipe_process_path = os.path.join(folder_path, 'out_fenicsdata_heatpipe_process.txt')
                                    if os.path.exists(out_fenicsdata_heatpipe_process_path):
                                        with open(out_fenicsdata_heatpipe_process_path, 'r') as out_fenicsdata_heatpipe_process:
                                            hp_step_matches, temps = get_heatpipe_temp(out_fenicsdata_heatpipe_process)
                                            indices_of_zero = [i for i, x in enumerate(hp_step_matches) if x == 0]
                                            if len(indices_of_zero) > 1:
                                                index = indices_of_zero[1] - 1
                                                temp = temps[index] if temps else "N/A"# 72个输入HP温度
                                            else:
                                                temp = temps[-1] if temps else "N/A"# 72个输入HP温度

                                            #输入：基体导热率
                                            mono_conduc = caluSS316ThermalConduct(monolith_T) if monolith_T else "N/A"

                                            #输出：燃料（附近）平均、最大压力；热管（附近）平均、最大压力
                                            pvd_path = os.path.join(folder_path, 'Thermal_expansion_stress.txt')
                                            if os.path.exists(pvd_path):
                                                stress_list = []
                                                with open(pvd_path, 'r') as pvd_file:
                                                    for line in pvd_file:
                                                        # 处理每一行数据并添加到列表中
                                                        stress_list.append(line.strip())

                                                    # if "N/A" in [data_list, temp, mono_conduc, stress_list]:
                                                        # continue

                                                    # stress_list_float = [float(x) for x in stress_list]
                                                    # if MEANORMAX == 'MEAN':
                                                    #     stress = mean_value = sum(stress_list_float) / len(stress_list_float)
                                                    # elif MEANORMAX == 'MAX':
                                                    #     stress = max(stress_list_float)

                                                    # output.write(data_list)
                                                        output.write(fuel_T_list + ',')
                                                        output.write(','.join(map(str, temp)) + ',')
                                                        output.write(f"{mono_conduc},")
                                                        output.write(str(stress_list) + '\n')

def extract_and_write_iteration_pritout(input_folder, output_file): # 124数，11 + 1 + 112
    # fuel_D_inner,fuel_D_outer,H_core,HP_D_outer,wall_1,wall_2,heat_power,fuel_T,
    # monolith_T,temp_pipe,fuel,k_eff_comb.nominal_value,thermal_tot_vec_list
    variable_names = ['E_slope', 'E_intercept', 'nu', 'alpha_base', 'alpha_slope',
            'SS316_T_ref', 'SS316_k_ref', 'SS316_alpha', 'SS316_scale']
    # 'names': ['FUEL_D_inner', 'FUEL_D_outer', 'H_core', 'HP_D_outer', 'temp_fuel', 'temp_mono', 'temp_pipe', 'Fuel', 'wall2', 'pitch'],#
    with open(output_file, 'w') as output:
        # 遍历主目录下的文件夹
        for folder in os.listdir(input_folder):
            folder_path_0 = os.path.join(input_folder, folder)
            if os.path.isdir(folder_path_0):
            # 确保是文件夹
                for folder_count in os.listdir(folder_path_0):
                    folder_path = os.path.join(folder_path_0, folder_count)
                    if os.path.isdir(folder_path):

                        printout_file_path = os.path.join(folder_path, 'PrintOut.txt')

                        if os.path.exists(printout_file_path):
                            with open(printout_file_path, 'r') as printout_file:
                                keff, std = get_keff(printout_file)
                                # 现在这里还很不完整要补充
                                output.write(f", {keff}, {std}\n") 

def extract_and_write_keff(input_folder, output_file): # 124数，11 + 1 + 112
    # fuel_D_inner,fuel_D_outer,H_core,HP_D_outer,wall_1,wall_2,heat_power,fuel_T,
    # monolith_T,temp_pipe,fuel,k_eff_comb.nominal_value,thermal_tot_vec_list
    variable_names = ['fuel_D_inner', 'fuel_D_outer', 'H_core', 'HP_D_outer', 'wall_1', 'wall_2', 'heat_power',
                   'fuel_T', 'monolith_T', 'temp_pipe', 'fuel', 'k_eff_comb', 'thermal_tot_vec_list']
    # 'names': ['FUEL_D_inner', 'FUEL_D_outer', 'H_core', 'HP_D_outer', 'temp_fuel', 'temp_mono', 'temp_pipe', 'Fuel', 'wall2', 'pitch'],#
    with open(output_file, 'w') as output:
        # 遍历主目录下的文件夹
        for folder in os.listdir(input_folder):
            folder_path_0 = os.path.join(input_folder, folder)
            if os.path.isdir(folder_path_0):
            # 确保是文件夹
                for folder_count in os.listdir(folder_path_0):
                    folder_path = os.path.join(folder_path_0, folder_count)
                    if os.path.isdir(folder_path):
                    # 找到输出文件的路径
                        # setting_file_path = os.path.join(folder_path, 'setting.txt')
                        # printout_file_path = os.path.join(folder_path, 'PrintOut.txt')
                        NN_keff_distri_path = os.path.join(folder_path, 'NN_keff_distri.txt')
                        setting_file_path = os.path.join(folder_path, 'setting.txt')
                        # outdebug_file_path = os.path.join(folder_path, 'out_debugdata.txt')
                        printout_file_path = os.path.join(folder_path, 'PrintOut.txt')

                        if os.path.exists(setting_file_path):
                            with open(setting_file_path, 'r') as setting_file:
                                # fuelDinner, fuelDouter, H_core, HP_D_outer, P_unit_fuel,\
                                #     wall_1, fuel_T, monolith_T, temp_pipe, fuel = get_initial_values_set(setting_file, 0)
                                fuelDinner, fuelDouter, H_core, HP_D_outer,\
                                    fuel_T, monolith_T, temp_pipe, fuel= get_initial_values_set2(setting_file, 0)
                            
                            if os.path.exists(NN_keff_distri_path):
                                with open(NN_keff_distri_path, 'r') as NN_keff_distri:
                                    # fuelDinner, fuelDouter, H_core, HP_D_outer, P_unit_fuel,\
                                    #       wall_1, wall_2, heat_power, fuel_T, monolith_T, temp_pipe, fuel = get_initial_values_set(NN_keff_distri, 0)
                                    content = NN_keff_distri.read()
                                    data_list = content.replace('[', '')
                                    data_list2 = data_list.replace(']', '')
                                    data_list3 = data_list2.replace('\n', '')
                                    if os.path.exists(printout_file_path):
                                        with open(printout_file_path, 'r') as printout_file:
                                            keff, std = get_keff(printout_file)
                                            # output.write(f"{fuelDinner},{fuelDouter},{H_core},{HP_D_outer},")
                                            # output.write(f"{fuel_T},{monolith_T},{temp_pipe},")
                                            # output.write(f"{fuel},") # 10
                                            output.write(data_list3) # 11 + 1 + 112 = 124 只用后面1+112
                                            output.write(f", {keff}, {std}\n") 
                            
def delete_out_files(input_folder, path=None): # 124数，11 + 1 + 112
    if path is not None:
        for folder in os.listdir(input_folder):
            folder_path_0 = os.path.join(input_folder, folder)
            if os.path.isdir(folder_path_0) and folder != '__pycache__':
            # if os.path.isdir(folder_path_0) and folder == '2024_03_22_23_12_36':
            # 确保是文件夹
                folder_tot_count = count_numeric_folders(folder_path_0)
                for folder_count in os.listdir(folder_path_0):
                    if folder_count.isnumeric():  # 检查文件夹名称是否为纯数字
                        folder_path = os.path.join(folder_path_0, folder_count)
                        if os.path.isdir(folder_path):
                            for filename in os.listdir(folder_path):
                                if filename.endswith(".out"):
                                    os.remove(os.path.join(folder_path, filename))
                                    # break
    else:
        folder_path = path
        if os.path.isdir(folder_path):
            for filename in os.listdir(folder_path):
                if filename.endswith(".out"):
                    os.remove(os.path.join(folder_path, filename))
                    # break

def delete_geomsh_files(input_folder, path=None): # 124数，11 + 1 + 112
    if path is not None:
        for folder in os.listdir(input_folder):
            folder_path_0 = os.path.join(input_folder, folder)
            if os.path.isdir(folder_path_0) and folder != '__pycache__':
            # if os.path.isdir(folder_path_0) and folder == '2024_03_22_23_12_36':
            # 确保是文件夹
                folder_tot_count = count_numeric_folders(folder_path_0)
                for folder_count in os.listdir(folder_path_0):
                    if folder_count.isnumeric():  # 检查文件夹名称是否为纯数字
                        folder_path = os.path.join(folder_path_0, folder_count)
                        if os.path.isdir(folder_path):
                            for filename in os.listdir(folder_path):
                                if filename.endswith(".geo"):
                                    os.remove(os.path.join(folder_path, filename))
                                    # break
                                elif filename.endswith(".msh"):
                                    os.remove(os.path.join(folder_path, filename))
                                    # break

def delete_setting_files(input_folder, path=None): # 124数，11 + 1 + 112
    if path is not None:
        for folder in os.listdir(input_folder):
            folder_path_0 = os.path.join(input_folder, folder)
            if os.path.isdir(folder_path_0) and folder != '__pycache__':
            # if os.path.isdir(folder_path_0) and folder == '2024_03_22_23_12_36':
            # 确保是文件夹
                folder_tot_count = count_numeric_folders(folder_path_0)
                for folder_count in os.listdir(folder_path_0):
                    if folder_count.isnumeric():  # 检查文件夹名称是否为纯数字
                        folder_path = os.path.join(folder_path_0, folder_count)
                        if os.path.isdir(folder_path):
                            setting_file_path = os.path.join(folder_path, 'setting.txt')
                            if os.path.exists(setting_file_path):
                                os.remove(setting_file_path)
                            # for filename in os.listdir(folder_path):
                            #     if filename.endswith(".geo"):
                            #         os.remove(os.path.join(folder_path, filename))
                            #         # break
                            #     elif filename.endswith(".msh"):
                            #         os.remove(os.path.join(folder_path, filename))
                                    # break


                    # break

def delete_h5_files(input_folder, path=None): # 124数，11 + 1 + 112
    if path is not None:
        for folder in os.listdir(input_folder):
            folder_path_0 = os.path.join(input_folder, folder)
            if os.path.isdir(folder_path_0) and folder != '__pycache__':
            # if os.path.isdir(folder_path_0) and folder == '2024_03_22_23_12_36':
            # 确保是文件夹
                folder_tot_count = count_numeric_folders(folder_path_0)
                for folder_count in os.listdir(folder_path_0):
                    if folder_count.isnumeric():  # 检查文件夹名称是否为纯数字
                        folder_path = os.path.join(folder_path_0, folder_count)
                        if os.path.isdir(folder_path):
                            for filename in os.listdir(folder_path):
                                if filename.endswith(".h5"):
                                    os.remove(os.path.join(folder_path, filename))
                                    # break
    else:
        folder_path = path
        if os.path.isdir(folder_path):
            for filename in os.listdir(folder_path):
                if filename.endswith(".h5"):
                    os.remove(os.path.join(folder_path, filename))
                    # break

def delete_initial_files(input_folder, path=None): # 124数，11 + 1 + 112
    if path is not None:
        for folder in os.listdir(input_folder):
            folder_path_0 = os.path.join(input_folder, folder)
            if os.path.isdir(folder_path_0) and folder != '__pycache__':
            # if os.path.isdir(folder_path_0) and folder == '2024_03_22_23_12_36':
            # 确保是文件夹
                folder_tot_count = count_numeric_folders(folder_path_0)
                for folder_count in os.listdir(folder_path_0):
                    if folder_count.isnumeric():  # 检查文件夹名称是否为纯数字
                        folder_path = os.path.join(folder_path_0, folder_count)
                        if os.path.isdir(folder_path):
                            for filename in os.listdir(folder_path):
                                file_path = os.path.join(folder_path, filename)
                                if filename.endswith(".xml.gz") or filename.endswith(".pvd") or filename.endswith(".vtu") or filename.endswith(".xml"):
                                    os.remove(file_path)
                                elif os.path.isdir(file_path) and filename == 'Initial':
                                    shutil.rmtree(file_path)
                                    # break
    else:
        folder_path = path
        if os.path.isdir(folder_path):
            for filename in os.listdir(folder_path):
                file_path = os.path.join(folder_path, filename)
                if filename.endswith(".xml.gz") or filename.endswith(".pvd") or filename.endswith(".vtu") or filename.endswith(".xml"):
                    os.remove(file_path)
                elif os.path.isdir(file_path) and filename == 'Initial':
                    shutil.rmtree(file_path)
                    # break

def predict_fenics_all_withoutstress(input_folder, output_file):
    # 输入：9个参数
    # 输出：（温度）各燃料边界温度、热管、基体、（膨胀）、（应力）
    with open(output_file, 'w') as output:
        # 遍历主目录下的文件夹
        for folder in os.listdir(input_folder):
            folder_path_0 = os.path.join(input_folder, folder)
            # 确保是文件夹
            if os.path.isdir(folder_path_0):
                for folder_count in os.listdir(folder_path_0):
                    folder_path = os.path.join(folder_path_0, folder_count)
                    if os.path.isdir(folder_path):
                        # 输入：基体初始温度
                        setting_file_path = os.path.join(folder_path, 'setting.txt')
                        if os.path.exists(setting_file_path):
                            with open(setting_file_path, 'r') as setting_file:
                                # 获取初始值
                                fuel_D_inner, fuel_D_outer, H_core, HP_D_outer, P_unit_fuel, \
                                    wall_1, wall_2, heat_power, fuel_T, monolith_T, temp_pipe, fuel = get_initial_values_set(setting_file, 0)
                                
                                # 输入：功率分布
                                distri_path = os.path.join(folder_path, 'pdct_distri.txt')
                                if os.path.exists(distri_path):
                                    with open(distri_path, 'r') as distri_file:
                                        content = distri_file.read()
                                        data_list = content.replace(' ', ',')
                                        data_list = data_list.replace('\n', ',')
                                        
                                        # HP温度分布
                                        out_fenicsdata_heatpipe_process_path = os.path.join(folder_path, 'out_fenicsdata_heatpipe_process.txt')
                                        if os.path.exists(out_fenicsdata_heatpipe_process_path):
                                            with open(out_fenicsdata_heatpipe_process_path, 'r') as out_fenicsdata_heatpipe_process:
                                                hp_step_matches, temps = get_heatpipe_temp(out_fenicsdata_heatpipe_process)
                                                indices_of_zero = [i for i, x in enumerate(hp_step_matches) if x == 0]
                                                if len(indices_of_zero) > 1:
                                                    index = indices_of_zero[1] - 1
                                                    temp = temps[index] if temps else "N/A"  # 72个输入HP温度
                                                else:
                                                    temp = temps[-1] if temps else "N/A"  # 72个输入HP温度
                                                
                                                # 基体导热率nouse
                                                # mono_conduc = caluSS316ThermalConduct(monolith_T) if monolith_T else "N/A"
                                                
                                                # 燃料边界温度
                                                PrintOut_path = os.path.join(folder_path, 'fuel_T_list.txt')
                                                if os.path.exists(PrintOut_path):
                                                    with open(PrintOut_path, 'r') as PrintOut:
                                                        content = PrintOut.read()
                                                        fuel_T_list = content.replace('\n', ',')
                                                        fuel_T_list = fuel_T_list.rstrip(', ')
                                                        
                                                        
                                                        PrintOut_path = os.path.join(folder_path, 'PrintOut.txt')
                                                        if os.path.exists(PrintOut_path):
                                                            with open(PrintOut_path, 'r') as PrintOut:
                                                                monolith_mean_temperature, monolith_max_temperature = get_monotemp_mean_max(PrintOut)
                                                                
                                                            if os.path.exists(PrintOut_path):
                                                                with open(PrintOut_path, 'r') as PrintOut:
                                                                    wall2, pitch_fuel, pitch_HP, Hcore, volume = get_geo_vecs(PrintOut)
                                                
                                                            
                                                            # stress_file_names = ['hp_nearby_maxstress', 'hp_nearby_avestress']
                                                            # stress_list_all = []
                                                            # for stress_file_name in stress_file_names:
                                                            #     stress_file_path = os.path.join(folder_path, stress_file_name + '.txt')
                                                            #     if os.path.exists(stress_file_path):
                                                            #         with open(stress_file_path, 'r') as PrintOut:
                                                            #             stress_list = PrintOut.read()
                                                            #             stress_list = stress_list.replace('[', '')
                                                            #             stress_list = stress_list.replace(']', '')
                                                            #             stress_list1 = stress_list.split(', ')
                                                            #             stress_list_float = [float(x) for x in stress_list1]

                                                            #             stress_list_all.append(stress_list_float)

                                                            # stress_list_all = stress_list_all.replace('[', '')
                                                            # stress_list_all = stress_list_all.replace(']', '')

                                                            # 先保存 9个参数
                                                            # if "N/A" in [data_list, temp, fuel_T_list] or 'nan' in fuel_T_list.lower() or stress_list_all == []:
                                                            #     continue
                                                            if "N/A" in [data_list, temp, fuel_T_list] or 'nan' in fuel_T_list.lower():
                                                                continue

                                                            output.write(f"{fuel_D_inner},")
                                                            output.write(f"{H_core},")
                                                            output.write(f"{HP_D_outer},")
                                                            output.write(f"{fuel_T},")
                                                            output.write(f"{monolith_T},")
                                                            output.write(f"{temp_pipe},")
                                                            output.write(f"{fuel},")
                                                            output.write(f"{wall_2},")
                                                            output.write(f"{P_unit_fuel},") 


                                                            # output.write(data_list)
                                                            #热管温度72
                                                            output.write(','.join(map(str, temp)) + ',')
                                                            # 燃料温度112
                                                            output.write(fuel_T_list + ',')
                                                            #基体温度2
                                                            output.write(f"{monolith_mean_temperature},{monolith_max_temperature},")

                                                            output.write(f"{wall2},")
                                                            output.write(f"{pitch_fuel},")
                                                            output.write(f"{Hcore}")

                                                            # output.write(str(stress_list_all))
                                                            output.write('\n')
from statistics import mean

def predict_fenics_all_withstress(input_folder, output_file):
    # 输入：9个参数
    # 输出：（温度）各燃料边界温度、热管、基体、（膨胀）、（应力）
    with open(output_file, 'w') as output:
        # 遍历主目录下的文件夹
        for folder in os.listdir(input_folder):
            folder_path_0 = os.path.join(input_folder, folder)
            # 确保是文件夹
            if os.path.isdir(folder_path_0):
                for folder_count in os.listdir(folder_path_0):
                    folder_path = os.path.join(folder_path_0, folder_count)
                    if os.path.isdir(folder_path):
                        # 输入：基体初始温度
                        setting_file_path = os.path.join(folder_path, 'setting.txt')
                        if os.path.exists(setting_file_path):
                            with open(setting_file_path, 'r') as setting_file:
                                # 获取初始值
                                fuel_D_inner, fuel_D_outer, H_core, HP_D_outer, P_unit_fuel, \
                                    wall_1, wall_2, heat_power, fuel_T, monolith_T, temp_pipe, fuel = get_initial_values_set(setting_file, 0)
                                
                                # 输入：功率分布
                                distri_path = os.path.join(folder_path, 'pdct_distri.txt')
                                if os.path.exists(distri_path):
                                    with open(distri_path, 'r') as distri_file:
                                        content = distri_file.read()
                                        data_list = content.replace(' ', ',')
                                        data_list = data_list.replace('\n', ',')
                                        
                                        # HP温度分布
                                        out_fenicsdata_heatpipe_process_path = os.path.join(folder_path, 'out_fenicsdata_heatpipe_process.txt')
                                        if os.path.exists(out_fenicsdata_heatpipe_process_path):
                                            with open(out_fenicsdata_heatpipe_process_path, 'r') as out_fenicsdata_heatpipe_process:
                                                hp_step_matches, temps = get_heatpipe_temp(out_fenicsdata_heatpipe_process)
                                                indices_of_zero = [i for i, x in enumerate(hp_step_matches) if x == 0]
                                                if len(indices_of_zero) > 1:
                                                    index = indices_of_zero[1] - 1
                                                    temp = temps[index] if temps else "N/A"  # 72个输入HP温度
                                                else:
                                                    temp = temps[-1] if temps else "N/A"  # 72个输入HP温度
                                                
                                                # 基体导热率nouse
                                                # mono_conduc = caluSS316ThermalConduct(monolith_T) if monolith_T else "N/A"
                                                
                                                # 燃料边界温度
                                                PrintOut_path = os.path.join(folder_path, 'fuel_T_list.txt')
                                                if os.path.exists(PrintOut_path):
                                                    with open(PrintOut_path, 'r') as PrintOut:
                                                        content = PrintOut.read()
                                                        fuel_T_list = content.replace('\n', ',')
                                                        fuel_T_list = fuel_T_list.rstrip(', ')
                                                        
                                                        
                                                        PrintOut_path = os.path.join(folder_path, 'PrintOut.txt')
                                                        if os.path.exists(PrintOut_path):
                                                            with open(PrintOut_path, 'r') as PrintOut:
                                                                monolith_mean_temperature, monolith_max_temperature = get_monotemp_mean_max(PrintOut)
                                                                
                                                            if os.path.exists(PrintOut_path):
                                                                with open(PrintOut_path, 'r') as PrintOut:
                                                                    wall2, pitch_fuel, pitch_HP, Hcore, volume = get_geo_vecs(PrintOut)
                                                
                                                            # stress_file_names = ['hp_nearby_maxstress', 'hp_nearby_avestress']
                                                            stress_file_name = 'hp_nearby_maxstress'
                                                            stress_list_all = []
                                                            # for stress_file_name in stress_file_names:
                                                            stress_file_path = os.path.join(folder_path, stress_file_name + '.txt')
                                                            if os.path.exists(stress_file_path):
                                                                with open(stress_file_path, 'r') as PrintOut:
                                                                    stress_list = PrintOut.read()
                                                                    stress_list = stress_list.replace('[', '')
                                                                    stress_list = stress_list.replace(']', '')
                                                                    stress_list1 = stress_list.split(', ')
                                                                    stress_list_float = [float(x) for x in stress_list1]

                                                                    maxstress = max(stress_list_float)
                                                            stress_file_name = 'hp_nearby_avestress'
                                                            stress_file_path = os.path.join(folder_path, stress_file_name + '.txt')
                                                            if os.path.exists(stress_file_path):
                                                                with open(stress_file_path, 'r') as PrintOut:
                                                                    stress_list = PrintOut.read()
                                                                    stress_list = stress_list.replace('[', '')
                                                                    stress_list = stress_list.replace(']', '')
                                                                    stress_list1 = stress_list.split(', ')
                                                                    stress_list_float = [float(x) for x in stress_list1]

                                                                    # stress_list_all.append(mean(stress_list_float))
                                                                    meanstress = mean(stress_list_float)

                                                            # stress_list_all = stress_list_all.replace('[', '')
                                                            # stress_list_all = stress_list_all.replace(']', '')

                                                            # 先保存 9个参数
                                                                    if "N/A" in [data_list, temp, fuel_T_list] or 'nan' in fuel_T_list.lower():
                                                                        continue
                                                                    # if "N/A" in [data_list, temp, fuel_T_list] or 'nan' in fuel_T_list.lower():
                                                                    #     continue

                                                                    output.write(f"{fuel_D_inner},")
                                                                    output.write(f"{H_core},")
                                                                    output.write(f"{HP_D_outer},")
                                                                    output.write(f"{fuel_T},")
                                                                    output.write(f"{monolith_T},")
                                                                    output.write(f"{temp_pipe},")
                                                                    output.write(f"{fuel},")
                                                                    output.write(f"{wall_2},")
                                                                    output.write(f"{P_unit_fuel},") 


                                                                    # output.write(data_list)
                                                                    #热管温度72
                                                                    output.write(','.join(map(str, temp)) + ',')
                                                                    # 燃料温度112
                                                                    output.write(fuel_T_list + ',')
                                                                    #基体温度2
                                                                    output.write(f"{monolith_mean_temperature},{monolith_max_temperature},")

                                                                    output.write(f"{wall2},")
                                                                    output.write(f"{pitch_fuel},")
                                                                    output.write(f"{Hcore},")

                                                                    # output.write(str(stress_list_all))
                                                                    output.write(f"{maxstress},{meanstress}\n")
                                                                    # output.write('\n')


# 用法示例
# input_folder = r'/home/yinuochen/documents/1218/1218_2'
# input_folder = r'/home/yinuochen/documents/fenics_data'
# input_folder = r'/home/yinuochen/documents/NEW_fenics_data0411'
# input_folder = r'/home/yinuochen/documents/1218/0315-openmc-sobol'
# input_folder = r'/home/yinuochen/documents/1218/0315-openmc-sobol'
# input_folder = '/home/yinuochen/Desktop/7rod'  
input_folder = '/home/tjzs/Documents/fenics_data/fenics_data/new_output'
# input_folder = '/home/cyn/文档/jcloudfiles/Desktop/fenics_data/output'

# input_folder = r'/home/yinuochen/documents/NEW_fenics_data0411'
output_file = r'/home/tjzs/Documents/fenics_data/fenics_data/txt_extract'
# output_file = r'/home/yinuochen/documents/NN/generate-txt/small_for_bayes'

# filename = '2024_11_10_00_00_32'
# filename = '2025_02_18_14_55_03'
# predict_keff_for_sobol(input_folder, output_file + '/' + filename + '.txt', filename)

# extract_and_write_keff(input_folder, output_file + '/' + 'allresults' + '.txt')
def main(path):
    delete_out_files(input_folder, path)
    delete_geomsh_files(input_folder, path)
    delete_initial_files(input_folder, path)
    delete_h5_files(input_folder, path)
    delete_setting_files(input_folder, path)
main(input_folder)
# predict_power_distribution(input_folder, output_file + '/power-distri-NN.txt')
# predict_mono_avg_temp(input_folder, output_file + '/monoavg-temp-NN.txt')
# predict_fuel_temp_no_nan(input_folder, output_file + '/0227fuelborder-temp-NN.txt')
# predict_HP_temp_distri(input_folder, output_file + '/HP_temp_distri_0613.txt')# 再加上！文档和siyuan上的
# predict_HP_temp_distri_for_sobol(input_folder, output_file + '/HP_temp_distri_0406_for_sobol.txt')
# predict_mono_temp(input_folder, output_file + '/0227_mono_temp.txt') # 再加上！文档和siyuan上的
# predict_expansion(input_folder, output_file + '/0227expansion.txt')

# predict_stress_mean_max(input_folder, output_file + '/0317_hp_nearby_maxstress.txt', 'hp_nearby_maxstress', 'MAX')
# predict_stress_mean_max(input_folder, output_file + '/0317_hp_nearby_avestress.txt', 'hp_nearby_avestress', 'MEAN')
# predict_stress_mean_max(input_folder, output_file + '/0317_fuel_nearby_maxstress.txt', 'fuel_nearby_maxstress', 'MAX')
# predict_stress_mean_max(input_folder, output_file + '/0317_fuel_nearby_avestress.txt', 'fuel_nearby_avestress', 'MEAN')

# predict_stress_all(input_folder, output_file + '/0317_fuel_nearby_avestress_all.txt', 'fuel_nearby_avestress_all')
# predict_stress_all(input_folder, output_file + '/0317_fuel_nearby_maxstress_all.txt', 'fuel_nearby_maxstress')
# predict_stress_all(input_folder, output_file + '/0317_hp_nearby_avestress_all.txt', 'hp_nearby_avestress_all_all')
# predict_stress_all(input_folder, output_file + '/0323_hp_nearby_avestress_all.txt', 'hp_nearby_avestress_all')
# predict_stress_all(input_folder, output_file + '/0317_hp_nearby_maxstress_all.txt', 'hp_nearby_maxstress_all')
# predict_fenics_all_withoutstress(input_folder, output_file + '/0323_fenics_allwithoutstress.txt')
# predict_fenics_all_withstress(input_folder, output_file + '/0323_fenics_allwithstress.txt')