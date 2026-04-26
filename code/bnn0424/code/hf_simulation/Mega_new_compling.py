# Mega_new_compling.py
import pickle
import numpy as np
import openmc
import os
import shutil
import time
import openmc.deplete
import openmc.lib
import scipy.io as sio
import copy
import os

from tensorflow.keras.models import load_model

from tensorflow.keras.layers import LeakyReLU
import MEGA_OpenMC_test
# os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
import Mega_calcule_method
import mega_fenics_test

import datetime
import json

# parameters_dic = parameters_dic
# settings_dic = generater.settings_dic

def copy_file(source_path, destination_path):
    try:
        shutil.copy(source_path, destination_path)
        print(f'成功复制文件从 {source_path} 到 {destination_path}')
    except FileNotFoundError:
        print(f'找不到文件: {source_path}')
    except Exception as e:
        print(f'复制文件时发生错误: {e}')

def nn_postProcess(parameters_dic, pdct_distri, iteration, save_prefix="nn"):
    """
    神经网络后处理，参考原有蒙卡后处理流程，计算相关变量并保存。
    参数:
        parameters_dic: 输入参数字典
        pdct_distri: 神经网络预测的 thermal_tot_vec (长度为N的ndarray或list)
        iteration: 当前迭代次数
        save_prefix: 保存文件名前缀
    返回:
        相关变量字典
    """
    # 提取参数
    heat_power = parameters_dic['heat_power']
    fuel_D_inner = parameters_dic['fuel_D_inner']
    H_core = parameters_dic['H_core']
    temp_pipe = parameters_dic['temp_pipe']
    monolith_T = parameters_dic['monolith_T']
    controldrum_angle = parameters_dic.get('controldrum_angle', 0)
    fuel_cell_ID_list = parameters_dic.get('fuel_cell_ID_list', list(range(len(pdct_distri))))
    omega = parameters_dic.get('relaxation', 1.0)
    # 兼容 pdct_distri 为 list 或 ndarray
    thermal_tot_vec = np.array(pdct_distri).copy()
    N = len(thermal_tot_vec)
    heat_tot_vec = np.zeros(N)
    heat_dev_vec = np.zeros(N)
    flux_tot_vec = np.zeros(N)
    flux_dev_vec = np.zeros(N)
    volume_heat_vec = np.zeros(N)
    volume_heat_vec_list = []
    thermal_tot_vec_list = []

    # 计算功率因子
    heat_power = heat_power / 6
    heat_power_origin = thermal_tot_vec.sum()
    k_power = heat_power / (heat_power_origin * 1.6022e-19)
    volume_vec = H_core * np.pi * (fuel_D_inner * fuel_D_inner) / 4
    SS316_thermal_conductivity = MEGA_OpenMC_test.calc_SS316_k(monolith_T)

    # 反推原始 tally（近似，实际神经网络已输出归一化后的 thermal_tot_vec）
    # 这里假设 pdct_distri = 原 thermal_tot_vec * k_power * 1.6022e-19 / (fuel_D_inner * np.pi * H_core * SS316_thermal_conductivity)
    # 反推原始 tally: tally = pdct_distri * (fuel_D_inner * np.pi * H_core * SS316_thermal_conductivity) / (k_power * 1.6022e-19)
    # 但通常只需要后续变量即可

    # 体积热
    volume_heat_vec = thermal_tot_vec * fuel_D_inner * np.pi * H_core * SS316_thermal_conductivity / (fuel_D_inner * fuel_D_inner * np.pi * H_core / 4)
    # 归一化
    heat_tot_vec = thermal_tot_vec * k_power / volume_vec
    heat_dev_vec = np.zeros_like(heat_tot_vec)  # 神经网络没有 std_dev，置零
    flux_tot_vec = np.zeros_like(heat_tot_vec)
    flux_dev_vec = np.zeros_like(heat_tot_vec)

    for i in range(N):
        volume_heat_vec_list.append(volume_heat_vec[i])
        thermal_tot_vec_list.append(thermal_tot_vec[i])

    # 保存数据
    np.savetxt(f'{save_prefix}_pin_volume_heat.txt', volume_heat_vec)
    np.savetxt(f'{save_prefix}_thermal_tot_vec.txt', thermal_tot_vec)
    np.savetxt(f'{save_prefix}_heat_tot_vec.txt', heat_tot_vec)

    # 保存调试信息
    out = (
        f"{iteration}\n"
        f"thermal_tot_vec={thermal_tot_vec}\n"
        f"thermal_tot_vec_sum={thermal_tot_vec.sum() * (fuel_D_inner * np.pi * H_core * SS316_thermal_conductivity)}\n"
        f"ss316co={SS316_thermal_conductivity}\n"
        f"heat_dev_vec={heat_dev_vec}\n"
    )
    with open(f'{save_prefix}_out_debugdata.txt', 'a+', encoding='utf-8') as fout:
        fout.write(out)

    tally_dic = {
        'heat_mean': heat_tot_vec,
        'heat_dev': heat_dev_vec,
        'flux_mean': flux_tot_vec,
        'flux_dev': flux_dev_vec
    }
    tally_new_dic = {'heat_mean': heat_tot_vec, 'heat_dev': heat_dev_vec} if iteration > 0 else {}

    # 返回所有关键变量
    return {
        "thermal_tot_vec": thermal_tot_vec,
        "volume_heat_vec": volume_heat_vec,
        "heat_tot_vec": heat_tot_vec,
        "heat_dev_vec": heat_dev_vec,
        "flux_tot_vec": flux_tot_vec,
        "flux_dev_vec": flux_dev_vec,
        "tally_dic": tally_dic,
        "tally_new_dic": tally_new_dic,
        "volume_heat_vec_list": volume_heat_vec_list,
        "thermal_tot_vec_list": thermal_tot_vec_list,
        "k_power": k_power,
        "SS316_thermal_conductivity": SS316_thermal_conductivity
    }


class coupling_Computation:
    def __init__(self, parameters_dic, settings_dic):
        """
        初始化计算类，支持材料参数的扰动。
        """
        self.parameters_dic = copy.deepcopy(parameters_dic)
        self.settings_dic = copy.deepcopy(settings_dic)
        self.init_parameters_dic = copy.deepcopy(parameters_dic)
        self.init_settings_dic = copy.deepcopy(settings_dic)

        self.path = os.getcwd()
        self.__writeSettings()

        self.material_params = self.__extract_material_params()

    def __extract_material_params(self):
        """
        从 settings_dic 中提取材料参数。

        返回:
            dict: 包含材料参数的字典。
            'E_slope': 7e6,
            'E_intercept': 2e10,
            'nu': 0.031,
            'alpha_base': 1e-6,
            'alpha_slope': 5e-10,
            'SS316_T_ref': 92.315,
            'SS316_k_ref': 2.32,
            'SS316_alpha': 1/750,
            'SS316_scale': 0.001
        """
        material_keys = ['E_slope', 'E_intercept', 'nu', 'alpha_base', 'alpha_slope', 'SS316_T_ref', 'SS316_k_ref', 'SS316_alpha']
        material_params = {}
        for key in material_keys:
            if f"{key}" in self.init_settings_dic['material_params_samples']:
                material_params[key] = self.init_settings_dic['material_params_samples'][f"{key}"]
                print(f"提取的材料参数 {key}_values: {material_params[key]}")  # 添加打印语句
        return material_params

    def __createSubFolder(self, folder_name):
        """
        Create a sub folder in each step
        """
        self.file_path = self.path + '/' + folder_name
        if not os.path.exists(self.file_path):
            os.mkdir(self.file_path)

    def __printOut(self, print_str):
        """
        Print out information and save it
        """
        print(print_str)
        with open('{}/PrintOut.txt'.format(self.path), 'a', encoding='utf-8') as file_obj:
            file_obj.write(print_str + '\n')

    def __printBegining(self):
        self.__printOut('====================================================\n' + \
                        '=     Multi-Physics Code for Heat-pipe reactor     =\n' + \
                        '=                     MegaPower                    =\n' + \
                        '=                  OpenMC + Fenics                 =\n' + \
                        '=                   Version: 2.1.0                 =\n' + \
                        '=                    Mar 08 2022                   =\n' + \
                        '====================================================\n' + \
                        '             Folder name: {}'.format(self.path))

    def __writeSettings(self):
        """
        Write down settings of computation
        """
        to_write_list = [self.parameters_dic, self.settings_dic]
        file = open((self.path + '/setting.txt'), 'w')
        file.write('Simulation Settings')
        file.write('\n')
        for item in to_write_list:
            js = json.dumps(item, indent=0)
            file.write(js)
            file.write('\n')
        file.close()

    def __initilizeposition(self):
        wall_1 = self.parameters_dic['wall_1']
        HP_D_outer = self.parameters_dic['HP_D_outer']
        P_unit_fuel = self.parameters_dic['P_unit_fuel']
        P_unit_heatpipe = self.parameters_dic['P_unit_heatpipe']
        fuel_D_outer = self.parameters_dic['fuel_D_outer']
        fuel_D_inner = self.parameters_dic['fuel_D_inner']

        thefuelpositionformesh = []

        for i in range(3, 11):
            X_1_num = np.arange(wall_1 + HP_D_outer / 2 + P_unit_fuel / 2, 10000,
                                P_unit_fuel * 1.5)
            Y_1_num = np.arange(float(-P_unit_heatpipe * 1.5 + P_unit_fuel * np.sqrt(3) / 2), -1000,
                                float(-P_unit_fuel * np.sqrt(3) / 2))
            for j in range(i):
                x = X_1_num[i - 3]
                y = Y_1_num[i - 3] + j * P_unit_heatpipe

                thefuelpositionformesh.append([x, y])

        for i in range(4, 12):
            X_2_num = np.arange(wall_1 + P_unit_fuel / 2 + HP_D_outer / 2 + P_unit_fuel / 2, 10000,
                                P_unit_fuel * 1.5)
            Y_2_num = np.arange(float(-P_unit_heatpipe * 1.5), -1000,
                                float(-P_unit_fuel * np.sqrt(3) / 2))
            for j in range(i):
                x = X_2_num[i - 4]
                y = Y_2_num[i - 4] + j * P_unit_heatpipe
                thefuelpositionformesh.append([x, y])
        heatpipepositionformesh = []
        for i in range(4, 13):
            X_num = np.arange(wall_1 + HP_D_outer / 2, 1000, P_unit_fuel * 1.5)
            Y_num = np.arange(-float(P_unit_heatpipe * 1.5), -1000, float(-P_unit_heatpipe / 2))
            for j in range(i):
                x = X_num[i - 4]
                y = Y_num[i - 4] + j * P_unit_heatpipe
                heatpipepositionformesh.append([x, y])
        self.heatpipepositionformesh=heatpipepositionformesh
        self.thefuelpositionformesh=thefuelpositionformesh
        self.parameters_dic.update(heatpipepositionformc001=heatpipepositionformesh)
        self.parameters_dic.update(thefuelpositionformc001=thefuelpositionformesh)

    def __initilizeOpenMC(self):
        self.num_cells = 112
        fuel_T_list = []
        self.fuel_T = self.parameters_dic['fuel_T']
        for i in range(0, self.num_cells):
            fuel_T_list.append(self.fuel_T)
        FTLnp = np.asarray(fuel_T_list)
        self.parameters_dic.update(fuel_T_list=FTLnp)
        self.fuel_cell_ID_list = MEGA_OpenMC_test.define_Geo_Mat_Set(self.parameters_dic, self.settings_dic)
        return

    def __initilizeThermalTE(self):
        namedic=self.settings_dic['settings_Name_dic']
        self.Expansion_name_xy = namedic['Expansion_name_xy']
        self.Conduction_name_xy = namedic['Conduction_name_xy']

    def __initilizeVariable(self):
        num_col = self.num_cells
        iteration = self.iteration
        self.mode=self.settings_dic['Mode']

        if self.settings_dic['settings_MC_dic']['tally_method'] == 'mesh_tally':
            self.heat_error_vec = np.zeros(iteration - 1)
            # self.heat_weighted_error_vec = np.zeros(iteration-1)
            # to do with the convergence

        # The mean value and standard deviation of eigen value in each iteration
        self.k_eff_mean_vec = np.zeros(iteration)
        self.k_eff_dev_vec = np.zeros(iteration)

        if self.settings_dic['settings_MC_dic']['tally_method'] == 'mesh_tally':
            # The error, mean value and standard deviation of power distribution in each cell
            self.heat_error_mat = np.zeros((iteration - 1, num_col))  # num_col =num_cells=row*col in this is 352
            self.heat_mean_mat = np.zeros((iteration, num_col))
            self.heat_dev_mat = np.zeros((iteration, num_col))

            # The mean value and standard deviation of flux distribution in each cell
            self.flux_mean_mat = np.zeros((iteration, num_col))
            self.flux_dev_mat = np.zeros((iteration, num_col))
        self.temp_pipe = self.parameters_dic['temp_pipe']
        self.initial_temp = 300
        self.temp_error_vec = np.zeros(iteration)
        self.mode=self.settings_dic['Mode']
        self.wall_vec = np.zeros((iteration + 1, 2))
        self.P_fuel_vec = np.zeros(iteration + 1)
        self.H_core_vec = np.zeros(iteration + 1)
        self.wall_vec[0, 0] = self.parameters_dic['wall_1_origin']
        self.wall_vec[0, 1] = self.parameters_dic['wall_2_origin']
        self.P_fuel_vec[0] = self.parameters_dic['P_unit_fuel_origin']
        self.H_core_vec[0] = self.parameters_dic['H_core_origin']
        self.__printOut

    def __initilizeCalculation(self, depletion):
        self.iteration = self.settings_dic['iteration']
        self.__initilizeposition()
        self.__initilizeOpenMC()
        self.__initilizeThermalTE()

    def __runOpenMC(self):
        # Run transport simulation only
        time_start = time.time()
        self.__printOut('========OpenMC running========')
        import os
        current_work_dir = os.getcwd()  # 获取当前工作目录
        # print("OpenMC 运行时的当前工作目录：", current_work_dir)
        # print("该目录下的文件列表：", os.listdir(current_work_dir))  # 查看目录下已有文件
    
        openmc.run(output=self.settings_dic['settings_MC_dic']['Output'])

        time_end = time.time()

        self.__printOut('OpenMC run time: {} sec'.format((time_end - time_start)))

    def __collectInforMC(self):
        i = self.iter_step
        if self.settings_dic['settings_MC_dic']['tally_method'] == 'mesh_tally':
            # Collect information of OpenMC results
            k_eff_comb, k_power, thermal_tot_vec_list, volume_heat_vec, temp_pipe, tally_dic, tally_new_dic, thepeak, cal_total_fuel_constant = MEGA_OpenMC_test.postProcess(
                self.parameters_dic,self.fuel_cell_ID_list, self.iteration, self.settings_dic)

            '''print('id_list')
            print(self.fuel_cell_ID_list)
            print('vec')
            print(thermal_tot_vec_list)'''
            # self.thermal_tot_vec_list = thermal_tot_vec_list

            # update the mat
            if self.iter_step > 0:
                self.heat_mean_mat[i, :] = tally_new_dic['heat_mean']
                self.heat_dev_mat[i, :] = tally_new_dic['heat_dev']
            else:
                self.heat_mean_mat[i, :] = tally_dic['heat_mean']
                self.heat_dev_mat[i, :] = tally_dic['heat_dev']

            self.flux_mean_mat[i, :] = tally_dic['flux_mean']
            self.flux_dev_mat[i, :] = tally_dic['flux_dev']

            # Only for calculate error
            self.heat_mean_vec = tally_dic['heat_mean']
            self.heat_dev_vec = tally_dic['heat_dev']
        # k-eff mean value and standard deviation
        self.k_eff_mean_vec[i] = k_eff_comb.nominal_value
        self.k_eff_dev_vec[i] = k_eff_comb.std_dev
        self.themaxflux = Mega_calcule_method.devide_heatflux_to_heatpipe(thermal_tot_vec_list)
        # Print out the information of the eigenvalue
        self.__printOut('k-eff:{}, std: {}'.format(k_eff_comb.nominal_value, k_eff_comb.std_dev))
        #this part is to write some data to a txt file,can be refactored to a more parsimonious format
        #also can add the data you want to write
        out = ''
        out = out + 'theangle ' + str(self.parameters_dic['controldrum_angle'])+' power '+str(self.parameters_dic['heat_power'])+' reflector_M '+str(self.parameters_dic['ReflectorM'])+' pipetemp '+str(self.temp_pipe)

        out = out + ' keffvalue ' + str(k_eff_comb.nominal_value) + ' ' + str(k_eff_comb.std_dev) + ' peak '
        for j in thepeak:
            out = out + str(j) + ' '
        out = out + 'themaxflux ' + str(self.themaxflux)
        out = out + '\n'
        fout = open('out_keff.txt', 'a+')
        fout.write(out)
        fout.close()
        th_out = '['
        th_out_total = '['
        the_sum_flux = 0
        the_power_title = 'the set power=' + str(self.parameters_dic['heat_power'] / 6) + ' '
        for i in thermal_tot_vec_list:
            the_sum_flux = the_sum_flux + i * cal_total_fuel_constant
        the_power_title = the_power_title + 'the cal power=' + str(the_sum_flux) + ' the ss316 con=' + str(
            cal_total_fuel_constant) + '\n'
        th_out = th_out + '\n'
        th_out_total = th_out_total + '\n'
        fout = open('out_the_thermal_data.txt', 'a+')
        fout.write(the_power_title)
        fout.write(out)
        fout.write(th_out)
        fout.write(th_out_total)

        fout.close()

        return thermal_tot_vec_list, volume_heat_vec

    def __printOutErrorMC(self):
        # Maximum relative error of power distribution
        i = self.iter_step
        if self.settings_dic['settings_MC_dic']['tally_method'] == 'mesh_tally':
            if i > 0:
                heat_error = abs(self.heat_mean_mat[i - 1, :] - self.heat_mean_vec) / self.heat_mean_mat[i - 1, :]
                self.heat_error_vec[i - 1] = heat_error.max()
                self.__printOut('Maximum relative change of power distribution: {}'.format(self.heat_error_vec[i - 1]))

                # For test
                self.heat_error_mat[i - 1, :] = heat_error
                heat_error_ave = heat_error.sum() / self.num_cells  # num_cells=352
                self.__printOut('Average relative change of power distribution: ' + str(heat_error_ave))




    def __postProcessMC(self):
        time_start = time.time()

        self.thermal_tot_vec_list, self.volume_heat_vec = self.__collectInforMC()

        # Print out the information of computational error
        self.__printOutErrorMC()


        time_end = time.time()
        self.__printOut('OpenMC post-process time: {} sec'.format((time_end - time_start)))

        ##pass thermal_tot_vec_list tn mesh

        #self.__generateMesh(self.thermal_tot_vec_list)


    def __runThermalTE(self):
        """
        执行热力计算，并保存扰动数据和输出数据。
        """
        time_start = time.time()
        self.__printOut('========Thermal Conduction and Expansion running========')

        # material_params = {key: self.material_params[key][self.iter_step][0] for key in self.material_params}
        material_params = {key: self.settings_dic['material_params'][key] for key in self.settings_dic['material_params']}
        # thermal_tot_vec_list = self.parameters_dic['pdct_distri'][0]
        thermal_tot_vec_list = self.thermal_tot_vec_list
        thermal_tot_vec_list = np.array(thermal_tot_vec_list)
        heat_power_origin = thermal_tot_vec_list.sum()
        heat_power = self.parameters_dic.get('heat_power', 50000000) / 24  # 优先从参数字典获取
        k_power = heat_power / (heat_power_origin * 1.6022e-19)
        # 补充参数从 dic 获取
        material_params = {key: self.settings_dic['material_params'][key] for key in self.settings_dic['material_params']}
        # thermal_tot_vec_list = self.parameters_dic['pdct_distri'][0]
        heat_power_origin = thermal_tot_vec_list.sum()
        heat_power = self.parameters_dic.get('heat_power', 50000000) / 24  # 优先从参数字典获取
        k_power = heat_power / (heat_power_origin * 1.6022e-19)

        H_core = self.parameters_dic.get('H_core')
        fuel_D_inner = self.parameters_dic.get('fuel_D_inner')
        fuel_D_outer = self.parameters_dic.get('fuel_D_outer')
        HP_D_outer = self.parameters_dic.get('HP_D_outer')
        wall_1 = self.parameters_dic.get('wall_1')
        wall_2 = self.parameters_dic.get('wall_2')
        temp_pipe = self.parameters_dic.get('temp_pipe')
        monolith_T = self.parameters_dic.get('monolith_T')
        fuel_T = self.parameters_dic.get('fuel_T')
        volume_vec = H_core * np.pi * (fuel_D_inner * fuel_D_inner) / 4
        # volume_heat_vec 需要根据实际逻辑赋值或计算
        # volume_heat_vec = ...existing code or calculation...
        hp_temp_for_fenics = temp_pipe - self.initial_temp
        SS316_thermal_conductivity = MEGA_OpenMC_test.calc_SS316_k(monolith_T)
        volume_heat_vec = thermal_tot_vec_list * fuel_D_inner * np.pi * H_core * SS316_thermal_conductivity / (fuel_D_inner * fuel_D_inner * np.pi * H_core / 4)
        # 调用 fenics_2d_process 进行计算        
        the_fenics_object = mega_fenics_test.Fenics_2d_process(
            self.thermal_tot_vec_list,
            self.volume_heat_vec,
            self.thefuelpositionformesh,
            self.heatpipepositionformesh,
            losehp=[],
            totalpower=self.parameters_dic['heat_power'] / 6,
            mode=3,
            average_heatpipe_temp=temp_pipe - 300,
            hp_r=HP_D_outer / 2,
            fuel_r=fuel_D_outer / 2,
            fuel_r_inner=fuel_D_inner / 2,
            file_name_Basis_Thermal='Thermal_conduction',
            file_name_Expansion_xy='Thermal_expansion_xy',
            file_name_Basis_Expansion_Z='Thermal_expansion_z',
            file_name_Expansion_Stress='Thermal_expansion_stress',
            material_params=material_params,
            output_dir=self.settings_dic.get('output_dir') 
        )
        the_fenics_object.fenics_coupulate_for_coupled()
        the_fenics_object.read_2d_Temperature()
        the_fenics_object.read_fuel_inner_Temperature()
        the_fenics_object.read_2d_Expansion()
        the_fenics_object.read_2d_Stress()
        the_fenics_object.read_3d_Expansion()

        # for i in range(len(fuel_temp_ave_vec)):
        #     fuel_temp_ave_vec[i] = fuel_temp_ave_vec[i] + self.initial_temp  # 添加初始温度用于OpenMC处理

        # 保存扰动数据和输出数据
        '''"fuel_nearby_maxstress": self.fuel_nearby_maxstress if hasattr(self, "fuel_nearby_maxstress") else None,
                "fuel_nearby_avestress": self.fuel_nearby_avestress if hasattr(self, "fuel_nearby_avestress") else None,
                "hp_nearby_maxstress": self.hp_nearby_maxstress if hasattr(self, "hp_nearby_maxstress") else None,
                "hp_nearby_avestress": self.hp_nearby_avestress if hasattr(self, "hp_nearby_avestress") else None,
                "global_max_stress": self.max_stress if hasattr(self, "max_stress") else None
                '''
        output_data = {
            'average_fuel_temp': the_fenics_object.average_fuel_temp + self.initial_temp,
            'max_temp': the_fenics_object.max_temp + self.initial_temp,
            'max_monolith_temp': the_fenics_object.max_monolith_temp + self.initial_temp,
            'average_monolith_temp': the_fenics_object.average_monolith_temp,
            # 'fuel_temp_ave_vec': the_fenics_object.fuel_average_temperature_list,
            'newfuelposition': the_fenics_object.new_fuel_position,
            'newheatpipeposition': the_fenics_object.new_heatpipe_position,
            'newwall2': the_fenics_object.newwall2,
            'height': the_fenics_object.new_height,
            'fuel_nearby_maxstress': the_fenics_object.fuel_nearby_maxstress,
            'fuel_nearby_avestress': the_fenics_object.fuel_nearby_avestress,
            'hp_nearby_maxstress': the_fenics_object.hp_nearby_maxstress,
            'hp_nearby_avestress': the_fenics_object.hp_nearby_avestress,
            'global_max_stress': max(
                    float(max(the_fenics_object.hp_nearby_maxstress)), 
                    float(max(the_fenics_object.fuel_nearby_maxstress))
                )
        }
        np.save('thermal_output_data.npy', output_data)  # 保存为 NumPy 文件

        # 更新 fenicsoutdata_dic
        self.fenicsoutdata_dic = output_data

        time_end = time.time()
        self.__printOut('Thermal Conduction and Expansion run time: {} sec'.format((time_end - time_start)))

    def __updateTempMat(self):
        i = self.iter_step
        self.monolith_temp = self.parameters_dic['monolith_T']
        self.parameters_dic.update(monolith_T=self.fenicsoutdata_dic['average_monolith_temp'])
        self.monolith_temp_new = self.parameters_dic['monolith_T']
        self.fuel_temp = self.parameters_dic['fuel_T']
        self.parameters_dic.update(fuel_T=self.fenicsoutdata_dic['average_fuel_temp'])
        self.fuel_temp_new = self.parameters_dic['fuel_T']
        # self.parameters_dic.update(fuel_T_list=self.fenicsoutdata_dic['fuel_temp_ave_vec'])

    def __printOutErrorTemp(self):
        i = self.iter_step
        self.temp_pipe = self.parameters_dic['temp_pipe']
        self.__printOut('fuel new temperature: {},monolith new temperature:{}'.format(self.fuel_temp_new, self.monolith_temp_new))
        self.fuel_temp_error = np.abs(self.fuel_temp_new - self.fuel_temp) / np.abs(self.fuel_temp - self.temp_pipe)
        self.monolith_temp_error = np.abs(self.monolith_temp_new - self.monolith_temp) / np.abs(
            self.monolith_temp - self.temp_pipe)

        self.__printOut('Relative error of fuel temperature: {}'.format(self.fuel_temp_error))
        self.__printOut('Relative error of monolith temperature: {}'.format(self.monolith_temp_error))
        self.__printOut('the max fuel center temperature: {}'.format(self.fenicsoutdata_dic['max_temp']))
        self.__printOut('the max monolith temperature: {}'.format(self.fenicsoutdata_dic['max_monolith_temp']))

    def __Tempchange(self):
        time_start = time.time()
        self.__updateTempMat()
        self.__printOutErrorTemp()
        time_end = time.time()
        self.__printOut('Tempchange post-process time: {} sec'.format((time_end - time_start)))

    def __isMode3(self):
        if self.settings_dic['Mode'] == 3:
            return True
        else:
            return False

    def __positionchange(self):
        """
        更新几何参数，检查 Hcore 的更新逻辑。
        """
        self.__printOut(f"更新前的 Hcore: {self.parameters_dic['H_core']}")
        self.parameters_dic['H_core'] = self.fenicsoutdata_dic['height']
        self.__printOut(f"更新后的 Hcore: {self.parameters_dic['H_core']}")
        if self.parameters_dic['H_core'] > 160:  # 添加合理性检查
            self.__printOut("警告: Hcore 更新值异常，可能存在问题")
            # self.parameters_dic['H_core'] = 150  # 恢复默认值

        i = self.iter_step
        pitch=1.6*self.fenicsoutdata_dic['newwall2']/self.parameters_dic['wall_2']
        self.parameters_dic.update(wall_2=self.fenicsoutdata_dic['newwall2'])
        self.parameters_dic.update(H_core=self.fenicsoutdata_dic['height'])
        self.wall_vec[i + 1, 0] = self.parameters_dic['wall_1']
        self.wall_vec[i + 1, 1] = self.parameters_dic['wall_2']
        self.parameters_dic.update(heatpipepositionformc001=self.fenicsoutdata_dic['newheatpipeposition'])
        self.parameters_dic.update(thefuelpositionformc001=self.fenicsoutdata_dic['newfuelposition'])
        self.P_fuel_vec[i + 1] = pitch
        
        self.parameters_dic.update(P_unit_fuel=pitch)
        self.parameters_dic.update(P_unit_heatpipe=pitch * np.sqrt(3))
        self.H_core_vec[i + 1] = self.parameters_dic['H_core']
        self.__printOut('New wall1: {} cm'.format(self.parameters_dic['wall_1']))
        self.__printOut('New wall2: {} cm'.format(self.parameters_dic['wall_2']))
        self.__printOut('New pitch_fuel: {} cm'.format(pitch))
        self.__printOut('New pitch_HP: {} cm'.format(self.parameters_dic['P_unit_heatpipe']))
        self.__printOut('New Hcore: {} cm'.format(self.parameters_dic['H_core']))

        volume_current = np.sqrt(3) * (self.wall_vec[i + 1, 1] ** 2 - self.wall_vec[i + 1, 0] ** 2) * self.H_core_vec[
            i + 1] / 3
        volume_last = np.sqrt(3) * (self.wall_vec[i, 1] ** 2 - self.wall_vec[i, 0] ** 2) * self.H_core_vec[i] / 3
        self.monolith_error = abs(volume_current - volume_last) / volume_current
        self.__printOut('Relative change of monolith volume: {}'.format(self.monolith_error))

        parameters_dic= self.parameters_dic
        current_dir = os.getcwd()
        output_file = 'parameters_and_geo_feom_fenics.txt'
        file_path = os.path.join(current_dir, output_file)
        with open(file_path, 'w', encoding='utf-8') as output:
            for key in parameters_dic:
                if key in [ 'heatpipepositionformc001', 'fuel_T_list', 'pdct_keff', 'pdct_distri', 'pdct_vol_heat']:
                    value = parameters_dic[key]
                    np.savetxt('' + f'{key}.txt', value)
                elif key != 'ReflectorM':
                    value = parameters_dic[key]
                    output.write(str(value) + '\n')

    def __updateOpenMC(self):
        self.fuel_cell_ID_list = MEGA_OpenMC_test.define_Geo_Mat_Set(self.parameters_dic, self.settings_dic)

    def __isConvergent(self):
        """
        检查是否收敛，并打印当前迭代次数。
        """
        self.__printOut(f"当前迭代次数: {self.iter_step + 1}")
        if self.iter_step >= self.iteration - 1:
            return True
        return False

    def __saveData(self, depletion=False):
        i = self.iter_step
        file_path = self.file_path
        file_name = self.Conduction_name_xy
        expansion_name = self.Expansion_name_xy

        conduction_result = {}
        expansion_result = {}

        conduction_result['fuel_temp'] = self.fuel_temp_new
        conduction_result['fuel_temp_error'] = self.fuel_temp_error
        conduction_result['monolith_temp'] = self.monolith_temp_new
        conduction_result['monolith_temp_error'] = self.monolith_temp_error

        expansion_result['wall_mat'] = self.wall_vec[0:i + 1, :]
        expansion_result['pitch_mat'] = self.P_fuel_vec[0:i + 1]
        expansion_result['H_core_mat'] = self.H_core_vec[0:i + 1]

        sio.savemat('{}/result.mat'.format(file_path),
                    { 'conduction_result': conduction_result, 'expansion_result': expansion_result})

        if self.settings_dic['Mode'] != 1:
            if os.path.exists(file_name + '.fld'):
                shutil.copy((file_name + '.fld'), file_path)
            if os.path.exists(file_name + '000000.vtu'):
                shutil.copy((file_name + '000000.vtu'), file_path)
            if os.path.exists(file_name + '_only000000.vtu'):
                shutil.copy((file_name + '_only000000.vtu'), file_path)
            if os.path.exists("Thermal_expansion_stress" + '000000.vtu'):
                shutil.copy(("Thermal_expansion_stress" + '000000.vtu'), file_path)
            if os.path.exists("Thermal_expansion_xy" + '000000.vtu'):
                shutil.copy(("Thermal_expansion_xy" + '000000.vtu'), file_path)
            if os.path.exists("Thermal_expansion_z" + '000000.vtu'):
                shutil.copy(("Thermal_expansion_z" + '000000.vtu'), file_path)
            if os.path.exists("out_fenicsdatahpdata.txt"):
                shutil.copy(("out_fenicsdatahpdata.txt"), file_path)
            if os.path.exists("out_fenicsdata.txt"):
                shutil.copy(("out_fenicsdata.txt"), file_path)

        if self.settings_dic['Mode'] == 3:
            if os.path.exists(expansion_name + '000000.vtk'):
                shutil.copy((expansion_name + '000000.vtk'), file_path)

        if os.path.exists('axial_power.txt'):
            shutil.copy('axial_power.txt', file_path)

        if depletion:
            path = self.path
            cal_step = self.cal_step
            shutil.copy('openmc_simulation_n{}.h5'.format(cal_step), file_path)
            shutil.copy('depletion_results.h5', path)
            np.savetxt('{}/convergence_step.txt'.format(path), self.convergence_step_vec, fmt="%i")
        else:
            path = self.path
            iter_step = self.iter_step
            batches = self.settings_dic['settings_MC_dic']['batches']
            if os.path.exists('statepoint.{}.h5'.format(batches)):
                shutil.copyfile('statepoint.{}.h5'.format(batches),
                                '{}/statepoint.{}_{}.h5'.format(file_path, batches, iter_step))
                
    def __savefenics_data(self):
        fenics_dic= self.fenicsoutdata_dic
        current_dir = os.getcwd()
        array_keys = ['newfuelposition', 'newheatpipeposition', 'fuel_nearby_maxstress', 'fuel_nearby_avestress',
                  'hp_nearby_maxstress', 'hp_nearby_avestress', 'fuel_average_temperature_list']
        for key in array_keys:
            if key in fenics_dic:
                value = fenics_dic[key]
                if isinstance(value, (list, np.ndarray)):  # 确保是数组/列表
                    np.savetxt(os.path.join(current_dir, f'{key}.txt'), np.array(value), fmt='%.6f')
        
        # 保存标量类数据（温度、应力极值等）
        scalar_keys = ['average_fuel_temp', 'max_temp', 'max_monolith_temp', 
                    'average_monolith_temp']  # 可根据实际字段扩展
        with open(os.path.join(current_dir, 'fenics_scalar_data.txt'), 'w', encoding='utf-8') as f:
            for key in scalar_keys:
                if key in fenics_dic:
                    value = fenics_dic[key]
                    f.write(f'{key}: {value}\n')

        self.__printOut('================ Fenics 关键计算结果 ================')
        if 'average_fuel_temp' in fenics_dic:
            self.__printOut(f'平均燃料温度: {fenics_dic["average_fuel_temp"]:.2f} K')
        if 'max_temp' in fenics_dic:
            self.__printOut(f'燃料最高温度: {fenics_dic["max_temp"]:.2f} K')
        if 'max_monolith_temp' in fenics_dic:
            self.__printOut(f'单体最高温度: {fenics_dic["max_monolith_temp"]:.2f} K')
        if 'global_max_stress' in fenics_dic:
            self.__printOut(f'全局最大应力: {fenics_dic["global_max_stress"]:.2f} MPa')
        if 'new_height' in fenics_dic:
            self.__printOut(f'3D 膨胀后高度: {fenics_dic["new_height"]:.2f} cm')
        self.__printOut('====================================================')
        # output_file = 'else_data.txt'
        # file_path = os.path.join(current_dir, output_file)
        # with open(file_path, 'w') as output:
        #     for key in fenics_dic:
        #         if key in ['newfuelposition', 'newheatpipeposition']:
        #             value = fenics_dic[key]
        #             np.savetxt('' + f'{key}.txt', value)
        #         else:
        #             value = fenics_dic[key]
        #             output.write(str(value) + '\n')

    def __saveMaterialParams(self):
        material_params = self.material_params
        current_dir = os.getcwd()
        output_file = 'material_params.txt'
        file_path = os.path.join(current_dir, output_file)

        with open(file_path, 'w', encoding='utf-8') as output:
            for key, values in material_params.items():
                output.write(f"{key}: {values}\n")

        for key, value in self.current_input.items():
            self.__printOut(f"{key}: {value}")

    def transportnew(self, current_input):
        self.__printBegining()
        self.current_input = current_input
        self.__printOut('           Transport-Thermal-Mechanics Coupling       ')
        self.cal_step = 0
        time_allbegin = time.time()
        self.__createSubFolder('Initial')
        self.__initilizeCalculation(depletion=False)
        self.__initilizeVariable()
        self.__saveMaterialParams()
        for self.iter_step in range(self.iteration):
            self.__printOut(
                "====================Iteration {} begins====================".format(self.iter_step + 1))
            start_tot = time.time()
            
            fuel_D_inner = self.parameters_dic['fuel_D_inner']
            fuel_D_outer = self.parameters_dic['fuel_D_outer']
            H_core = self.parameters_dic['H_core']
            HP_D_outer = self.parameters_dic['HP_D_outer']
            wall_1 = self.parameters_dic['wall_1']
            wall_2 = self.parameters_dic['wall_2']
            heat_power =self.parameters_dic['heat_power']
            fuel_T = self.parameters_dic['fuel_T']
            monolith_T = self.parameters_dic['monolith_T']
            temp_pipe = self.parameters_dic['temp_pipe']
            fuel = self.parameters_dic['fuel']
            
            input = [fuel_D_inner,fuel_D_outer,H_core,HP_D_outer,fuel_T,monolith_T,temp_pipe,fuel,wall_2, fuel]
            input_array = np.array(input)
            input = input_array.reshape(1, -1)

            # custom_objects = {
            #     'LeakyReLU': LeakyReLU,
            #     'mse': MeanSquaredError(),  # 注意这里要实例化
            #     'mape': MeanAbsolutePercentageError(),
            #     'mean_absolute_percentage_error': MeanAbsolutePercentageError()
            # }


            # trained_model_path = '/home/cyn/文档/jcloudfiles/NN/trained_h5_file/'
            # model_name_keff = '0227_keff_best'
            # model_keff = load_model(trained_model_path + model_name_keff + '.h5')
            # model_name_distri = '0227_distri_scale'
            # model_distri = load_model('/home/cyn/文档/jcloudfiles/NN/NEW_train_code/2502/trained_h5_file/' + model_name_distri + '_best.h5')
            # model_name_vol_heat = '0403-vol-heat-LeakyReLU'
            # model_vol_heat = load_model(trained_model_path + model_name_vol_heat + '.h5')

            # scaler_path = '/home/yinuochen/documents/NN/scaler_files/'
            # with open(scaler_path + model_name_keff + '_scaler_keff.pkl', 'rb') as f:
            #     scaler_keff = pickle.load(f)
                
            #     input_scaler_keff = scaler_keff.transform(input)
            # with open('/home/cyn/文档/jcloudfiles/NN/NEW_train_code/2502/scaler_files/' + model_name_distri + '_scaler.pkl', 'rb') as f:
            #     scaler_distri = pickle.load(f)
            #     input_scaler_distri = scaler_distri.transform(input)
            # with open(scaler_path + model_name_vol_heat + '_scaler_vol_heat.pkl', 'rb') as f:
            #     scaler_vol_heat = pickle.load(f)
            #     input_scaler_vol_heat = scaler_vol_heat.transform(input)

            # pdct_keff = model_keff.predict(input)
            # pdct_distri = model_distri.predict(input_scaler_distri)
            # pdct_vol_heat = model_vol_heat.predict(input_scaler_vol_heat)
            self.__runOpenMC()
            self.__postProcessMC()
            # self.parameters_dic.update(pdct_keff = pdct_keff)
            # self.parameters_dic.update(pdct_distri = pdct_distri)
            # self.openmc_results = MEGA_OpenMC_test.nn_postProcess(self.parameters_dic, pdct_distri, self.iter_step, save_prefix="nn")
            # self.parameters_dic.update(pdct_vol_heat = pdct_vol_heat)

            self.__runThermalTE()
            self.__savefenics_data()
            self.__Tempchange()

            if self.__isMode3():
                self.__positionchange()
            else:
                self.monolith_error = 0.0

            # Update geometry and material in OpenMC
            self.__updateOpenMC()

            self.cal_step += 1

            end_tot = time.time()
            self.__printOut('Total time: {} sec'.format(end_tot - start_tot))

            if self.__isConvergent():
                self.__saveData()
                break

            else:
                self.__saveData()

        time_allend = time.time()
        self.__printOut('every thing is done, and use time is {} sec'.format(time_allend - time_allbegin))

# def some_function_that_uses_generater():
#     import generater  # 延迟导入，避免循环依赖
#     # 使用 generater 的代码



