import time
import numpy as np
import vtk
from vtk.util.numpy_support import vtk_to_numpy
import os
from subprocess import call
from multiprocessing import Pool

"""
Multi-Physics Code for Heat-pipe Reactor
MPCH 2.0.0
Wei Xiao
Shanghai Jiao Tong University
School of Nuclear Science and Engineering
bearsanxw@gmail.com
Oct 15, 2020

核心功能：
1. 读取非结构化网格 VTK 文件，提取节点位移、单元应力等核心数据
2. 计算主应力（基于应力分量推导）
3. 定位孔洞附近节点 / 单元，统计孔洞周边数据（平均 / 最大数值、应力分布）
4. 处理单体外围节点数据，计算单体平均 / 最大参数
5. 更新孔洞位置（结合节点位移数据修正）
关键组件：
- vtk_2d_process 类：核心处理类，封装孔洞分析、应力计算、数据统计功能
- get_Vertices_Data 函数：快速提取 VTK 文件的节点位移与坐标数据
- getnewposition 函数：基于 VTK 位移数据更新孔洞实际位置
"""

def get_Vertices_Data(filename):
    """
    从 VTK 文件中获取节点数据和位移数据。

    参数:
        filename (str): VTK 文件路径。

    返回:
        tuple: 包含位移数据和节点坐标的元组。
    """
    reader = vtk.vtkXMLUnstructuredGridReader()
    reader.SetFileName(filename)
    reader.Update()
    output = reader.GetOutput()

    # 获取点数据
    disp_vtk_array = output.GetPointData().GetArray(0)
    cal_data = vtk_to_numpy(disp_vtk_array)

    # 获取节点坐标
    nodes_vtk_array = output.GetPoints().GetData()
    nodes_vec = vtk_to_numpy(nodes_vtk_array)

    return cal_data, nodes_vec

class vtk_2d_process:
    """
    用于处理 2D VTK 文件的类，支持获取孔洞附近的点数据、应力计算等。
    """
    def __init__(self, filename, hole_position, hole_r):
        """
        初始化 vtk_2d_process 类。

        参数:
            filename (str): VTK 文件路径。
            hole_position (list): 孔洞位置列表。
            hole_r (float): 孔洞半径。
        """
        self.filename = filename
        self.hole_position = hole_position
        self.hole_r = hole_r
        self.nearbynode_first = []

    def __ma_stress(self, len9_numpy):
        """
        计算主应力。

        参数:
            len9_numpy (numpy.ndarray): 包含应力分量的数组。

        返回:
            float: 主应力值。
        """
        return np.sqrt(np.square(len9_numpy[0] + len9_numpy[4]) - 3 * (len9_numpy[0] * len9_numpy[4] - np.square(len9_numpy[1])))

    def getCellsData(self):
        """
        获取单元数据和单元编号。

        返回:
            tuple: 包含单元数据和单元编号的元组。
        """
        filename = self.filename
        reader = vtk.vtkXMLUnstructuredGridReader()
        reader.SetFileName(filename)
        reader.Update()
        output = reader.GetOutput()

        # 获取单元数据
        disp_vtk_array = output.GetCellData().GetArray(0)
        cell_data = vtk_to_numpy(disp_vtk_array)

        # 获取单元编号
        nodes_vtk_array = output.GetCells().GetData()
        Cell_number = vtk_to_numpy(nodes_vtk_array)

        return cell_data, Cell_number

    def get_hole_nearby_point(self, hole_position_number):
        """
        获取指定孔洞附近的点。

        参数:
            hole_position_number (int): 孔洞编号。

        返回:
            tuple: 包含孔洞编号、附近点列表和孔洞外点数据的元组。
        """
        nodes_disp_vec = self.nodes_disp_vec
        hole_position = self.hole_position
        hole_r = self.hole_r
        try:
            point_data_in_vtk = self.point_data_in_vtk
        except AttributeError:
            pass

        returnlist = [hole_position_number]
        hole_nearby_point = []
        hole_outer_point_sum = 0
        hole_outer_point_num = 0

        for i in range(len(nodes_disp_vec)):
            the_dis = (nodes_disp_vec[i][0] - hole_position[hole_position_number][0]) ** 2 + \
                      (nodes_disp_vec[i][1] - hole_position[hole_position_number][1]) ** 2

            if the_dis >= (hole_r - 0.001) ** 2:  # 找到不在孔洞内的点
                if the_dis <= (hole_r + 0.001) ** 2:  # 找到孔洞附近的点
                    hole_nearby_point.append(i)
                try:  # 计算单体中的点数据
                    hole_outer_point_sum += point_data_in_vtk[i]
                    hole_outer_point_num += 1
                except:
                    pass

        hole_outer_point = [hole_outer_point_sum, hole_outer_point_num]
        returnlist.append(hole_nearby_point)
        return returnlist, hole_outer_point

    def get_nearby_point(self):
        """
        获取所有孔洞附近的点。
        """
        nearby_point = []
        outer_point_data = []
        hole_nearby_node = []

        for i in range(len(self.hole_position)):
            hole_nearby_node.append(self.get_hole_nearby_point(i))

        for i in hole_nearby_node:
            nearby_point.append(i[0][1])
            outer_point_data.append(i[1])

        self.nearby_point = nearby_point
        self.outer_point_data = outer_point_data

    def get_outer_point_sum(self):
        """
        计算单体外点的总和和数量。
        """
        outer_point_sum = 0
        outer_point_number = 0
        for i in self.outer_point_data:
            outer_point_sum += i[0]
            outer_point_number += i[1]
        self.outer_point_sum = outer_point_sum
        self.outer_point_number = outer_point_number

    def handle_hole_nearby_data(self, hole_position_number):
        """
        处理单个孔洞附近的数据。

        参数:
            hole_position_number (int): 孔洞编号。

        返回:
            list: 包含孔洞编号、平均数据和最大数据的列表。
        """
        maxmonolithdata = 0
        returnlist = [hole_position_number]
        point_data_in_vtk = self.point_data_in_vtk
        nearby_point = self.nearby_point
        i = hole_position_number
        sum = np.zeros(point_data_in_vtk[0].shape)

        for j in nearby_point[i]:
            sum += point_data_in_vtk[j]
            try:
                maxmonolithdata = max(maxmonolithdata, point_data_in_vtk[j])
            except:
                pass

        ave = sum / len(nearby_point[i])
        try:
            returnlist.append(ave.tolist())
        except:
            returnlist.append(ave)
        returnlist.append(maxmonolithdata)
        return returnlist

    def handle_nearby_data(self):
        """
        处理所有孔洞附近的数据。

        返回:
            list: 包含每个孔洞附近的平均数据和最大数据的列表。
        """
        hole_data = []
        themaxdata = []
        hole_nearby_node_data = []

        for i in range(len(self.hole_position)):
            hole_nearby_node_data.append(self.handle_hole_nearby_data(i))

        hole_nearby_node_data.sort(key=lambda x: x[0])
        for i in hole_nearby_node_data:
            hole_data.append(i[1])
            themaxdata.append(i[2])

        self.hole_data = hole_data
        self.themaxdata = max(themaxdata)  # 假设单体的最大数据在孔洞附近

    def getstressnearby(self):
        """
        获取孔洞附近的应力数据。

        返回:
            tuple: 包含最大应力和平均应力的元组。
        """
        timebegin = time.time()
        filename = self.filename
        hole_position = self.hole_position
        hole_r = self.hole_r
        nearby_point = []
        nearby_cell = []
        nearby_stress = []
        nearby_maxstress = []
        nearby_avestress = []

        reader = vtk.vtkXMLUnstructuredGridReader()
        reader.SetFileName(filename)
        reader.Update()
        output = reader.GetOutput()

        # 获取单元数据
        Celldata = output.GetCellData().GetArray(0)
        cell_datanp = vtk_to_numpy(Celldata)

        # 获取节点坐标
        nodes_vtk_array = output.GetPoints().GetData()
        nodes_vec = vtk_to_numpy(nodes_vtk_array)
        nodes_disp_vec = nodes_vec
        self.nodes_disp_vec = nodes_disp_vec

        try:
            if self.nearby_point:
                pass
        except AttributeError:
            self.get_nearby_point()

        nearby_point = self.nearby_point

        for i in range(len(nearby_point)):
            Listtemp = []
            for j in range(len(nearby_point[i])):
                cellid2 = vtk.vtkIdList()
                output.GetPointCells(nearby_point[i][j], cellid2)
                for k in range(cellid2.GetNumberOfIds()):
                    Listtemp.append(cellid2.GetId(k))
            nearby_cell.append(list(set(Listtemp)))

        for i in range(len(nearby_cell)):
            hole_nearby_stress = []
            for j in range(len(nearby_cell[i])):
                hole_nearby_stress.append(self.__ma_stress(cell_datanp[nearby_cell[i][j]]))
            hole_nearby_stress = [x for x in hole_nearby_stress if not np.isnan(x)]
            nearby_stress.append(hole_nearby_stress)
            if hole_nearby_stress:
                nearby_maxstress.append(max(hole_nearby_stress))
                nearby_avestress.append(sum(hole_nearby_stress) / len(hole_nearby_stress))
            else:
                nearby_maxstress.append(float('nan'))
                nearby_avestress.append(float('nan'))

        self.nearby_stress = nearby_stress
        self.nearby_maxstress = nearby_maxstress
        self.nearby_avestress = nearby_avestress

        return nearby_maxstress, nearby_avestress

    def update_max_stress(self):
        """
        获取全局最大主应力。

        返回:
            float: 最大应力值。
        """
        Stress_len9_numpy, _ = self.getCellsData()
        stress = []
        for i in Stress_len9_numpy:
            try:
                stress.append(self.__ma_stress(i))
            except Exception:
                pass
        if stress:
            return max(stress)
        else:
            return float('nan')

    def getNewVertices(self):
        """
        获取孔洞附近的点数据以及单体的平均和最大数据。

        返回:
            tuple: 包含孔洞数据、单体平均数据和最大数据的元组。
        """
        filename = self.filename
        hole_position = self.hole_position
        hole_r = self.hole_r
        nearby_point = []

        reader = vtk.vtkXMLUnstructuredGridReader()
        reader.SetFileName(filename)
        reader.Update()
        output = reader.GetOutput()

        disp_vtk_array = output.GetPointData().GetArray(0)
        point_data_in_vtk = vtk_to_numpy(disp_vtk_array)
        self.point_data_in_vtk = point_data_in_vtk

        nodes_vtk_array = output.GetPoints().GetData()
        nodes_vec = vtk_to_numpy(nodes_vtk_array)
        self.nodes_disp_vec = nodes_vec

        try:
            if self.nearby_point:
                pass
        except AttributeError:
            self.get_nearby_point()

        nearby_point = self.nearby_point
        self.get_outer_point_sum()
        the_monolith_data = [self.outer_point_sum, self.outer_point_number]

        the_monolith_ave = (the_monolith_data[0] - point_data_in_vtk.sum() * (len(hole_position) - 1)) / (
                the_monolith_data[1] - len(point_data_in_vtk) * (len(hole_position) - 1))
        self.handle_nearby_data()
        hole_data = self.hole_data
        maxmonolithdata = self.themaxdata
        return hole_data, the_monolith_ave, maxmonolithdata

def getnewposition(filename, hole_position, hole_r):
    """
    获取孔洞的新位置。

    参数:
        filename (str): VTK 文件路径。
        hole_position (list): 孔洞位置列表。
        hole_r (float): 孔洞半径。

    返回:
        list: 孔洞的新位置列表。
    """
    newposition = vtk_2d_process(filename, hole_position, hole_r)
    positionchange, _, _ = newposition.getNewVertices()
    newposition_list = []
    for i in range(len(hole_position)):
        x = hole_position[i][0] + positionchange[i][0]
        y = hole_position[i][1] + positionchange[i][1]
        newposition_list.append([x, y])
    return newposition_list

