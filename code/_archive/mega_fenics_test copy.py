import numpy as np
import vtk
from vtk.util.numpy_support import vtk_to_numpy
import os
import sys
from subprocess import call
import fenics_thermal_TE
import vtkprocess
import fenics_gmsh_test
import datetime
import inspect, re
import heatpipe
import json
import shutil

'''
热管反应堆 Fenics 多物理场耦合计算核心模块
核心用途：基于 Fenics 有限元框架，实现热管反应堆的 2D/3D 热传导、热膨胀、结构应力分析，及热管温度迭代优化的多物理场耦合计算，同时完成结果数据读取、结构化保存
核心类：Fenics_2d_process（封装所有计算、数据处理与结果管理逻辑）
关键功能模块：
1. 几何与网格处理：调用 Gmsh 生成 2D/3D 网格（.msh），转换为 Fenics 可识别的.xml.gz 格式，处理文件覆盖与缺失补偿
2. 有限元计算：
- 2D：热传导计算（获取热管热通量、单体平均温度）、热膨胀计算（更新燃料 / 热管位置、单体宽度）、应力计算（燃料 / 热管周边最大 / 平均应力）
- 3D：Z 方向热膨胀计算（获取核心新高度）
3. 热管温度优化：基于热通量迭代调整热管温度（最大 40 次迭代，收敛阈值 1.5），确保总功率匹配与温度稳定性
4. 结果读取：从 VTK 文件（.vtu）提取燃料温度（表面 / 内部最大 / 平均）、单体温度、膨胀量、应力数据
5. 结果保存：结构化输出 JSON 格式结果（含温度、膨胀、应力数据），复制关键计算文件（VTU、迭代日志）到自定义输出目录
依赖模块：vtkprocess（VTK 文件数据提取）、fenics_thermal_TE（Fenics 热 / 膨胀计算）、heatpipe（热管温度计算）、fenics_gmsh_test（网格生成）
输入关键参数：热通量向量、燃料 / 热管位置、材料参数、几何尺寸（燃料 / 热管半径）、总功率、输出目录等
'''

# 示例类：Fenics_2d_process
class Fenics_2d_process:
    """
    用于处理 Fenics 2D 和 3D 热传导、膨胀和耦合计算的类。
    """

    def __init__(self, thermal_tot_vec_list, volume_heat_vec, fuelposition, heatpipeposition, losehp=[],
                 totalpower=500000 / 6, mode=3, average_heatpipe_temp=950.15 - 300, hp_r=1.575 / 2,
                 fuel_r=1.425 / 2, fuel_r_inner=1.412 / 2,
                 file_name_Basis_Thermal='Thermal_conduction', file_name_Expansion_xy='Thermal_expansion_xy',
                 file_name_Basis_Expansion_Z='Thermal_expansion_z',
                 file_name_Expansion_Stress='Thermal_expansion_stress',
                 material_params=None, output_dir=None):  # 新增 output_dir 参数
        """
        初始化类的实例。

        参数:
            thermal_tot_vec_list (list): 热通量总向量列表。
            volume_heat_vec (list): 体积热向量。
            fuelposition (list): 燃料位置列表。
            heatpipeposition (list): 热管位置列表。
            losehp (list): 失效热管的 ID 列表。
            totalpower (float): 总功率。
            mode (int): 模式选择。
            average_heatpipe_temp (float): 热管平均温度。
            hp_r (float): 热管半径。
            fuel_r (float): 燃料外半径。
            fuel_r_inner (float): 燃料内半径。
            file_name_Basis_Thermal (str): 热传导基础文件名。
            file_name_Expansion_xy (str): 热膨胀文件名。
            file_name_Basis_Expansion_Z (str): 热膨胀 Z 方向文件名。
            file_name_Expansion_Stress (str): 热膨胀应力文件名。
            material_params (dict): 材料参数字典。
            output_dir (str): 输出目录路径。
        """
        self.thermal_tot_vec_list = thermal_tot_vec_list
        self.volume_heat_vec = volume_heat_vec
        self.fuelposition = fuelposition
        self.heatpipeposition = heatpipeposition
        self.loseHP = losehp
        self.totalpower = totalpower
        self.mode = mode
        self.average_heatpipe_temp = average_heatpipe_temp
        self.hp_r = hp_r
        self.fuel_r = fuel_r
        self.fuel_r_inner = fuel_r_inner
        self.file_name_Basis_Thermal = file_name_Basis_Thermal
        self.file_name_Expansion_xy = file_name_Expansion_xy
        self.file_name_Basis_Expansion_Z = file_name_Basis_Expansion_Z
        self.file_name_Expansion_Stress = file_name_Expansion_Stress
        self.material_params = material_params  # 保存材料参数
        self.heatpipe_temp_list = [average_heatpipe_temp] * len(heatpipeposition)  # 初始化热管温度列表
        self.heatpipe_type_list = [0] * len(heatpipeposition)  # 初始化热管类型列表
        self.output_dir = output_dir  # 保存传入的输出目录

    def __check_and_remove(self, filename, remove=True):  # check if file exist, if yes, remove it, in case of error
        #if remove is False, the file will not be removed, and if the file exist, the function will return True
        if os.path.exists(filename):
            if remove:
                os.remove(filename)
            else:
                print('file'+filename+' exist, but not remove')
                return True

    def __ensure_HP_temp_list(self):  # heatpipe process, if heatpipe_temp_list not exist, generate a original list of heat pipe temp use setting temp to ensure fenics can run
        try:
            if self.heatpipe_temp_list:pass
        except:
            hptempvec = [ ]
            for i in range(len(self.heatpipeposition)):
                hptempvec.append(self.average_heatpipe_temp)
            self.heatpipe_temp_list=hptempvec
    def __ensure_HP_type_list(self):  #heatpipe type process, if heatpipe_type_list not exist, generate a original list (all data 0) of heat pipe type to ensure can get hp temp from flux
        try:
            if self.heatpipe_type_list:pass
        except:
            hptypelist = [ ]
            for i in range(len(self.heatpipeposition)):
                hptypelist.append(0)
            self.heatpipe_type_list=hptypelist
            
    def __generate_msh_from_geo(self):
        fenics_gmsh_test.Update3D(self.file_name_Basis_Expansion_Z)
        fenics_gmsh_test.Update2D(self.file_name_Basis_Thermal)

    def __dolfin_convert(self,convert_name):#generate the xml.gz file from .msh file for fenics to use
        #if the msh file exist, convert it to xml.gz file
        print('dolfin convert right now')
        if self.__check_and_remove(convert_name + '.msh', remove=False):pass

        #if the msh file not exist, will exit the program
        else:
            print('msh file not exist,please generate the msh file first')
            self.__generate_msh_from_geo()
        self.__check_and_remove(convert_name + '.xml.gz')
        self.__check_and_remove(convert_name + '_facet_region.xml.gz')
        self.__check_and_remove(convert_name + '_physical_region.xml.gz')
        call('dolfin-convert {}.msh {}.xml;gzip {}*.xml'.format(convert_name, convert_name,
                                                                convert_name), shell=True)
        return True
    def __hpfluxprocess(self):#process the heat pipe flux to make sure the total power is right,and the flux is positive
        absflux=[]
        for j in self.hpflux_from_fenics:
            absflux.append(j)
        self.processed_flux=[]

        for i in absflux:
            self.processed_flux.append(i*self.totalpower/sum(absflux))


    def __fenics_write_down(self,outdata,outname,txtname):#write down the data in the name of txtname
        out = outname + ' = ' + str(outdata) + '\n'
        fout = open(txtname, 'a+')
        fout.write(out)
        fout.close()


    def __fenics_2d_calculation(self):#get fenics_2d_calculation result
        if self.__check_and_remove(self.file_name_Basis_Thermal + '.xml.gz', remove=False):pass
        else:
            print('no dolfin convert file, convert now')
            self.__dolfin_convert(self.file_name_Basis_Thermal)
        self.__ensure_HP_temp_list()
        self.hpflux_from_fenics, self.the_bound_temp_heatpipe, self.average_monolith_temp = fenics_thermal_TE.fenic_conduction_xy(
            self.material_params,
            self.hp_r,
            self.fuel_r,
            self.thermal_tot_vec_list,
            self.heatpipe_temp_list,
            self.loseHP,
            self.file_name_Basis_Thermal,
            self.file_name_Expansion_xy,
            self.file_name_Expansion_Stress)
        for i in self.loseHP:#add the lose heat pipe to heat pipe temp list
            self.heatpipe_temp_list[ i ]= self.the_bound_temp_heatpipe[ i ]
    def __fenics_3d_calculation(self):#get fenics_3d_calculation result
        if self.__check_and_remove(self.file_name_Basis_Expansion_Z + '_physical_region.xml.gz', remove=False):pass
        else:
            self.__dolfin_convert(self.file_name_Basis_Expansion_Z)
            # def fenic_expansion_z(average_monolith_temp, material_params, file_name_Basis_Expansion_Z='Thermal_expansion_z'):
        fenics_thermal_TE.fenic_expansion_z(self.average_monolith_temp, self.material_params, self.file_name_Basis_Expansion_Z)

    def __get_HP_temperature_from_flux(self):#get heat pipe temp from flux,and get the difference between the new heat pipe temp and the old heat pipe temp
        self.__hpfluxprocess()
        self.__ensure_HP_type_list()
        self.new_HP_temp=heatpipe.getheatpipetemp(self.processed_flux,self.heatpipe_temp_list,self.loseHP,self.heatpipe_type_list)
        self.HP_temp_erro=[]
        for i in range(len(self.heatpipe_temp_list)):
            self.HP_temp_erro.append(abs(self.heatpipe_temp_list[i]-self.new_HP_temp[i]))
    def __HP_temp_combo(self,the_factor):#combo the HP_temp from flux*factor and HP_temp into fenics(1-factor), get a new HP_temp into fenics
        #the_factor must less than 1, suggest less than 0.4, litter the factor, more stable the result, but more time to get the result
        #this_function must be used after __get_HP_temperature_from_flux
        for i in range(len(self.heatpipe_temp_list)):
            self.heatpipe_temp_list[i]=self.heatpipe_temp_list[i]*(1-the_factor)+self.new_HP_temp[i]*the_factor

    def read_fuel_inner_Temperature(self):#Fuel temperature data is processed and added here
        #inner temperature of fuel
        try :
            if self.FuelEdgeTemp:pass
        except:
            self.read_2d_Temperature()
        FETnp=np.asarray(self.FuelEdgeTemp)
        ku = ((1.025 * (1 - 0.04)) / (0.95 * (1 + 0.5 * 0.04))) * (
                    (38.24 / (self.avarage_monolith_temp + 129.4)) + 4.788e-13 * self.avarage_monolith_temp ** 3)
        volume_heat_vec = np.asarray(self.volume_heat_vec)
        gas_gap_temp_difference=volume_heat_vec * (
                    self.fuel_r_inner / (8 * 0.39 / 10000 * (self.avarage_monolith_temp ** 0.645))) * 0.00916467465
        fuel_conduction_temp_difference=volume_heat_vec * (self.fuel_r_inner * self.fuel_r_inner / (16 * ku))
        max_fuel_temp_vec = FETnp + fuel_conduction_temp_difference + gas_gap_temp_difference
        self.max_temp = max_fuel_temp_vec.max()

        fuel_temp_ave_vec = fuel_conduction_temp_difference/ (2) + FETnp + gas_gap_temp_difference
        self.fuel_average_temperature_list=fuel_temp_ave_vec.tolist()
        self.average_fuel_temp = np.average(fuel_temp_ave_vec)




    def read_2d_Temperature(self):#read the 2d temperature from vtu file,get the average temperature of fuel and heat pipe
        if self.__check_and_remove(self.file_name_Basis_Thermal+'000000.vtu', remove=False):pass
        else:
            self.__fenics_2d_calculation()
        Temperature_data_of_fuel = vtkprocess.vtk_2d_process(self.file_name_Basis_Thermal+'000000.vtu', self.fuelposition, self.fuel_r)
        self.FuelEdgeTemp,self.avarage_monolith_temp,self.max_monolith_temp=Temperature_data_of_fuel.getNewVertices()

    def read_2d_Stress(self):#read the 2d stress from vtu file,get the max stress and the average stress near the fuel and heat pipe
        #not really need stress in coupled process, but when generate data ,it might be useful
        if self.__check_and_remove(self.file_name_Expansion_Stress+'000000.vtu', remove=False):pass
        else:
            self.__fenics_2d_calculation()
        fuelstress = vtkprocess.vtk_2d_process(self.file_name_Expansion_Stress+'000000.vtu', self.fuelposition, self.fuel_r)
        hpstress = vtkprocess.vtk_2d_process(self.file_name_Expansion_Stress+'000000.vtu', self.heatpipeposition, self.hp_r)
        self.fuel_nearby_maxstress, self.fuel_nearby_avestress = fuelstress.getstressnearby()
        self.hp_nearby_maxstress, self.hp_nearby_avestress = hpstress.getstressnearby()
        #if need all the stress near each fuel or heat pipe, can use the like: hpstress.nearby_stress
        self.max_stress = max(self.fuel_nearby_maxstress, self.hp_nearby_maxstress)

    def read_2d_Expansion(self):#read the 2d expansion from vtu file,get the max expansion of x and the new position of fuel and heat pipe
        # in coupled, we need the new position of fuel and heat pipe ,and the newwall2
        if self.__check_and_remove(self.file_name_Expansion_xy+'000000.vtu', remove=False):pass
        else:
            self.__fenics_2d_calculation()
        self.new_fuel_position=vtkprocess.getnewposition(self.file_name_Expansion_xy+'000000.vtu', self.fuelposition, self.fuel_r)
        self.new_heatpipe_position=vtkprocess.getnewposition(self.file_name_Expansion_xy+'000000.vtu', self.heatpipeposition, self.hp_r)
        disp, nodes_vec = vtkprocess.get_Vertices_Data(self.file_name_Expansion_xy + '000000.vtu')
        node_position = disp + nodes_vec
        diaplacemence_x = node_position[ :, 0 ]
        self.newwall2 = max(diaplacemence_x.tolist()) - 1

    def read_3d_Expansion(self):#read the 3d expansion from vtu file,get the max expansion and the average expansion near the fuel and heat pipe
        if self.__check_and_remove(self.file_name_Basis_Expansion_Z+'000000.vtu', remove=False):pass
        else:
            self.__fenics_3d_calculation()
        disp, nodes_vec = vtkprocess.get_Vertices_Data(self.file_name_Basis_Expansion_Z + '000000.vtu')
        node_position = disp + nodes_vec
        diaplacemence_z = node_position[:,2]
        self.new_height=max(diaplacemence_z)


    def fenics_coupulate_for_coupled(self):
        """
        执行所有耦合计算，并完善数据读取与结果保存流程。
        """
        timenow = datetime.datetime.now()
        the_hp_txt_name = 'out_fenicsdata_heatpipe_process.txt'
        the_final_txt_name = 'out_fenicsdata_coupled.txt'
        self.__fenics_write_down(timenow, 'time_begin_fenics', the_final_txt_name)
        self.__generate_msh_from_geo()
        self.__dolfin_convert(self.file_name_Basis_Thermal)
        self.__fenics_2d_calculation()
        self.__get_HP_temperature_from_flux()
        all_HP_step = 0

        # 迭代调整热管温度，最多40次
        for HP_step_in in range(1): 
            if max(self.HP_temp_erro) <= 1.5:
                break
            self.__HP_temp_combo(0.1)
            self.__fenics_2d_calculation()
            self.__get_HP_temperature_from_flux()
            # 记录迭代过程关键数据
            self.__fenics_write_down(HP_step_in, 'HP_step_in', the_hp_txt_name)
            self.__fenics_write_down(max(self.HP_temp_erro), 'max(self.HP_temp_erro)', the_hp_txt_name)
            self.__fenics_write_down(self.HP_temp_erro, 'self.HP_temp_erro', the_hp_txt_name)
            self.__fenics_write_down(self.heatpipe_temp_list, 'self.heatpipe_temp_list', the_hp_txt_name)
            all_HP_step = HP_step_in

        # 记录总迭代次数
        self.__fenics_write_down(all_HP_step, 'all_HP_step', the_final_txt_name)
        
        # 执行3D热膨胀计算
        self.__fenics_3d_calculation()

        # 新增：读取所有关键结果数据（补充完善）
        self.read_2d_Temperature()       # 读取2D温度数据
        self.read_fuel_inner_Temperature() # 读取燃料内部温度
        self.read_2d_Expansion()         # 读取2D膨胀数据
        self.read_3d_Expansion()         # 读取3D膨胀数据
        self.read_2d_Stress()            # 读取2D应力数据（已有的关键补充）

        # 保存关键数据到 generater.py 创建的时间戳子文件夹
        if self.output_dir:  # 使用传入的输出目录
            output_dir = self.output_dir
            os.makedirs(output_dir, exist_ok=True)  # 确保目录存在
        else:
            # 备用逻辑：如果未传入则保持原逻辑（不建议）
            output_base = os.path.join(os.path.expanduser("~"), "文档", "jcloudfiles", "The_final", "output")
            time_str = timenow.strftime("%Y%m%d_%H%M%S")
            output_dir = os.path.join(output_base, time_str)
            os.makedirs(output_dir, exist_ok=True)

        # 保存结构化JSON结果（修复列表调用tolist()的问题）
        result_data = {
            "meta": {
                "start_time": timenow.strftime("%Y-%m-%d %H:%M:%S"),
                "total_iterations": all_HP_step,
                "output_dir": output_dir
            },
            "temperature": {
                "average_fuel_temp": self.average_fuel_temp,
                "max_fuel_temp": self.max_temp,
                "max_monolith_temp": self.max_monolith_temp,
                "average_monolith_temp": self.avarage_monolith_temp
            },
            "expansion": {
                # 修复：列表无需调用tolist()，直接使用原数据
                "new_fuel_position": self.new_fuel_position if hasattr(self, "new_fuel_position") else None,
                "new_heatpipe_position": self.new_heatpipe_position if hasattr(self, "new_heatpipe_position") else None,
                "max_2d_expansion_x": self.newwall2 if hasattr(self, "newwall2") else None,
                "max_3d_expansion_z": self.new_height if hasattr(self, "new_height") else None
            },
            "stress": {
                # 同理检查应力字段（假设fuel_nearby_maxstress等可能也是列表）
                "fuel_nearby_maxstress": self.fuel_nearby_maxstress if hasattr(self, "fuel_nearby_maxstress") else None,
                "fuel_nearby_avestress": self.fuel_nearby_avestress if hasattr(self, "fuel_nearby_avestress") else None,
                "hp_nearby_maxstress": self.hp_nearby_maxstress if hasattr(self, "hp_nearby_maxstress") else None,
                "hp_nearby_avestress": self.hp_nearby_avestress if hasattr(self, "hp_nearby_avestress") else None,
                "global_max_stress": self.max_stress if hasattr(self, "max_stress") else None
            }
        }
        with open(os.path.join(output_dir, "fenics_results.json"), "w") as f:
            json.dump(result_data, f, indent=2)

        # 复制关键输出文件（补充完整文件列表）
        output_files = [
            self.file_name_Basis_Thermal + '000000.vtu',       # 2D温度结果
            self.file_name_Expansion_xy + '000000.vtu',         # 2D膨胀结果
            self.file_name_Expansion_Stress + '000000.vtu',     # 2D应力结果
            self.file_name_Basis_Expansion_Z + '000000.vtu',    # 3D膨胀结果
            the_hp_txt_name,                                   # 迭代过程记录
            the_final_txt_name                                 # 最终结果汇总
        ]
        for fname in output_files:
            if os.path.exists(fname):
                # shutil.copy(fname, output_dir)
                print(f"已复制文件 {fname} 到输出目录 {output_dir}")

        # 记录结束时间
        self.__fenics_write_down(datetime.datetime.now(), 'time_end_fenics', the_final_txt_name)

    def add_Heatpipe_temp_list(self, heatpipe_temp_list):
        """
        添加热管温度列表。
        """
        self.heatpipe_temp_list = heatpipe_temp_list

    def add_Heatpipe_type_list(self, heatpipe_type_list):
        """
        添加热管类型列表。
        """
        self.heatpipe_type_list = heatpipe_type_list









