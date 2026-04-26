# MEGA_OpenMC_test.py
import numpy as np
# import openmc
import os
import matplotlib.pyplot as plt
import inspect, re
import random_generate
import openmc
def varname(p):
    """
    获取变量名称的辅助函数。
    """
    for line in inspect.getframeinfo(inspect.currentframe().f_back)[3]:
        m = re.search(r'\bvarname\s*\(\s*([A-Za-z_][A-Za-z0-9_]*)\s*\)', line)
    if m:
        return m.group(1)

def openmcdatawirtedown(outdata, outname):
    """
    将 OpenMC 数据写入文件。
    
    参数:
        outdata: 要写入的数据。
        outname: 数据名称。
    """
    out = outname + ' = ' + str(outdata) + '\n'
    with open('out_openmcdata.txt', 'a+') as fout:
        fout.write(out)

def define_Geo_Mat_Set(parameters_dic, settings_dic):
    """
    定义 OpenMC 的几何、材料和设置。
    
    参数:
        parameters_dic (dict): 参数字典。
        settings_dic (dict): 设置字典。
    
    返回:
        list: 燃料单元 ID 列表。
    """
    # 删除现有的 OpenMC 配置文件
    for filename in ['geometry.xml', 'materials.xml', 'settings.xml', 'tallies.xml']:
        if os.path.exists(filename):
            os.remove(filename)

    # 提取参数
    fuel_D_inner = parameters_dic['fuel_D_inner']
    fuel_D_outer = parameters_dic['fuel_D_outer']
    H_core = parameters_dic['H_core']
    H_core_origin = parameters_dic['H_core_origin']
    drum_D = parameters_dic['drum_D']
    H_reflector = parameters_dic['H_reflector']
    H_gas_plenum = parameters_dic['H_gas_plenum']
    R_reflector = parameters_dic['R_reflector']
    reflector_M_L = parameters_dic['ReflectorM']
    HP_D_outer = parameters_dic['HP_D_outer']
    P_unit_fuel = parameters_dic['P_unit_fuel']
    P_unit_fuel_origin = parameters_dic['P_unit_fuel_origin']
    P_unit_heatpipe = parameters_dic['P_unit_heatpipe']
    solid_rod_R = parameters_dic['solid_rod_R']
    annular_R_inner = parameters_dic['annular_R_inner']
    annular_R_outer = parameters_dic['annular_R_outer']
    wall_1 = parameters_dic['wall_1']
    wall_2 = parameters_dic['wall_2']
    wall_1_origin = parameters_dic['wall_1_origin']
    wall_2_origin = parameters_dic['wall_2_origin']
    fuel_position001 = parameters_dic['thefuelpositionformc001']
    HP_position001 = parameters_dic['heatpipepositionformc001']
    heat_power = parameters_dic['heat_power']
    fuel_T = parameters_dic['fuel_T']
    fuel_T_list = parameters_dic['fuel_T_list']
    monolith_T = parameters_dic['monolith_T']
    temp_pipe = parameters_dic['temp_pipe']
    emergency_control_rod = parameters_dic['emergency_control_rod']
    controlRod_deep = parameters_dic['controlRod_deep']
    controldrum_angle = parameters_dic['controldrum_angle']
    controldrum_rad = controldrum_angle / 180 * np.pi

    # 创建材料
    K = openmc.Material(name='K')
    K.set_density('g/cm3', 1.29)
    K.add_element('K', 1, 'ao')

    Al2O3 = openmc.Material(name='Al2O3')
    Al2O3.set_density('g/cm3', reflector_M_L[1])
    for i in reflector_M_L[0]:
        if i[0] == 'N':
            Al2O3.add_nuclide(i[1], i[2], 'ao')
        elif i[0] == 'E':
            Al2O3.add_element(i[1], i[2], 'ao')

    B4C = openmc.Material(name='B4C')
    B4C.add_nuclide('B10', 3.63, 'ao')
    B4C.add_nuclide('B11', 0.37, 'ao')
    B4C.add_element('C', 1, 'ao')
    B4C.set_density('g/cm3', 2.51)

    BeO = openmc.Material(name='BeO')
    BeO.add_element('Be', 1, 'ao')
    BeO.add_element('O', 1, 'ao')
    BeO.set_density('g/cm3', 3.01)

    He = openmc.Material(name='He')
    He.set_density('g/cm3', 1.0156)
    He.add_element('He', 1, 'ao')

    drum_reflector = openmc.Material(name='drum reflector')
    drum_reflector.set_density('g/cm3', reflector_M_L[1])
    for i in reflector_M_L[0]:
        if i[0] == 'N':
            drum_reflector.add_nuclide(i[1], i[2], 'ao')
        elif i[0] == 'E':
            drum_reflector.add_element(i[1], i[2], 'ao')

    gas = openmc.Material(name='gas')
    gas.set_density('g/cm3', 1.0156)
    gas.add_element('He', 1, 'ao')

    # 计算单体密度
    if settings_dic['Mode'] == 3:
        monolith_density_origin = 8.03
        volum_hole_origin = (np.pi * (112 * fuel_D_outer**2 + 72 * HP_D_outer**2) / 4) * H_core_origin
        volume_monolith_origin = (np.sqrt(3) / 3 * (wall_2_origin**2 - wall_1_origin**2) * H_core_origin) - volum_hole_origin
        volum_hole = (np.pi * (112 * fuel_D_outer**2 + 72 * HP_D_outer**2) / 4) * H_core
        volume_monolith = (np.sqrt(3) / 3 * (wall_2**2 - wall_1**2) * H_core) - volum_hole
        monolith_density = volume_monolith_origin / volume_monolith * monolith_density_origin
    else:
        monolith_density = 8.03

    SS316 = openmc.Material(name='SS316')
    SS316.add_element('C', 0.08 * 0.01, 'wo')
    SS316.add_element('Si', 1 * 0.01, 'wo')
    SS316.add_element('Mn', 2 * 0.01, 'wo')
    SS316.add_element('P', 0.045 * 0.01, 'wo')
    SS316.add_element('S', 0.03 * 0.01, 'wo')
    SS316.add_element('Cr', 17 * 0.01, 'wo')
    SS316.add_element('Ni', 12 * 0.01, 'wo')
    SS316.add_element('Fe', 65.345 * 0.01, 'wo')
    SS316.add_element('Mo', 2.5 * 0.01, 'wo')
    SS316.set_density('g/cm3', monolith_density)

    # 计算燃料密度
    if settings_dic['Mode'] == 3:
        fuel_density_origin = 10.52
        volum_fuel_origin = (np.pi * fuel_D_inner**2 / 4) * H_core_origin
        volum_fuel = (np.pi * fuel_D_inner**2 / 4) * H_core
        fuel_density = volum_fuel_origin / volum_fuel * fuel_density_origin
    else:
        fuel_density = 10.52

    fuel_enrichment = parameters_dic['fuel']
    proportion_for_235238 = 1 - 1.25 / 10.52

    fuel = openmc.Material(name=f"{fuel_enrichment * 100}%_UO2")
    fuel.add_nuclide('U235', fuel_enrichment, 'wo')
    fuel.add_nuclide('U238', proportion_for_235238 - fuel_enrichment, 'wo')
    fuel.add_nuclide('O16', 1.25 / 10.52, 'wo')
    fuel.set_density('g/cm3', fuel_density)

    # 导出材料到 XML
    materials = openmc.Materials([fuel, K, SS316, Al2O3, B4C, BeO, He, drum_reflector, gas])
    materials.export_to_xml()

    # 燃料顶部边界
    fuel_top_boundary = openmc.ZPlane(z0=H_core / 2)
    fuel_bottom_boundary = openmc.ZPlane(z0=-H_core / 2)
    reflector_top_boundary = openmc.ZPlane(z0=H_core / 2 + H_reflector, boundary_type='vacuum')
    reflector_bottom_boundary = openmc.ZPlane(z0=-(H_core / 2 + H_reflector))
    reflector_outer = openmc.ZCylinder(x0=wall_2 - wall_2_origin, y0=0, r=R_reflector, boundary_type='vacuum')
    reactor_bottom_boundary = openmc.ZPlane(z0=-(H_core / 2 + H_reflector + H_gas_plenum), boundary_type='vacuum')
    ang_mesh = np.pi / 6
    outerWalls_1 = openmc.XPlane(x0=wall_1)
    outerWalls_2 = openmc.XPlane(x0=wall_2)
    outerWalls_3 = openmc.Plane(a=1, b=np.sqrt(3), boundary_type='reflective')
    outerWalls_4 = openmc.Plane(a=-1, b=np.sqrt(3), boundary_type='reflective')
    outerWalls_5 = openmc.XPlane(x0=0.4)

    # 控制鼓
    drum_1_outer = openmc.ZCylinder(x0=wall_2 + drum_D / 2, y0=0, r=drum_D / 2)
    drum_1_inner = openmc.ZCylinder(x0=wall_2 + drum_D / 2 - 2 * np.cos(controldrum_rad), y0=0 + 2 * np.sin(controldrum_rad), r=drum_D / 2)

    # 紧急控制棒
    solid_rod = openmc.ZCylinder(x0=0, y0=0, r=solid_rod_R)
    annular_rod_inner = openmc.ZCylinder(x0=0, y0=0, r=annular_R_inner)
    annular_rod_outer = openmc.ZCylinder(x0=0, y0=0, r=annular_R_outer)

    # 定义根宇宙
    root_universe = openmc.Universe(universe_id=1995073100, name='root universe')
    all_cladding_cell = openmc.Cell(fill=SS316)
    all_cladding_cell.region = -reflector_outer

    # 创建紧急控制棒
    emergency_rod_cell = openmc.Cell(name='emergency_rod')
    if parameters_dic['emergency_control_rod'] == 'solid':
        emergency_rod_cell.fill = B4C
        plane = openmc.ZPlane(z0=H_core / 2 + H_reflector - controlRod_deep)
        emergency_rod_cell.region = -reflector_top_boundary & +plane & -solid_rod & +outerWalls_3 & -outerWalls_4
        root_universe.add_cell(emergency_rod_cell)
        outer_1_cell = openmc.Cell(name='outer_1_cell', fill=He, region=-reflector_top_boundary & +plane & -outerWalls_1 & +solid_rod & +outerWalls_3 & -outerWalls_4)
        outer_2_cell = openmc.Cell(name='outer_2_cell', fill=He, region=+reactor_bottom_boundary & -plane & -outerWalls_1 & +outerWalls_3 & -outerWalls_4)
        root_universe.add_cell(outer_1_cell)
        root_universe.add_cell(outer_2_cell)
    elif parameters_dic['emergency_control_rod'] == 'annular':
        emergency_rod_cell.fill = B4C
        plane = openmc.ZPlane(z0=H_core / 2 + H_reflector - controlRod_deep)
        emergency_rod_cell.region = -reflector_top_boundary & +plane & +annular_rod_inner & -annular_rod_outer & +outerWalls_3 & -outerWalls_4
        root_universe.add_cell(emergency_rod_cell)
        outer_1_cell = openmc.Cell(name='outer_1_cell', fill=He, region=-reflector_top_boundary & +plane & -annular_rod_inner & +outerWalls_3 & -outerWalls_4)
        outer_2_cell = openmc.Cell(name='outer_2_cell', fill=He, region=-reflector_top_boundary & +plane & +annular_rod_outer & -outerWalls_1 & +outerWalls_3 & -outerWalls_4)
        outer_3_cell = openmc.Cell(name='outer_3_cell', fill=He, region=+reflector_bottom_boundary & -plane & -outerWalls_1 & +outerWalls_3 & -outerWalls_4)
        root_universe.add_cell(outer_1_cell)
        root_universe.add_cell(outer_2_cell)
        root_universe.add_cell(outer_3_cell)
    elif parameters_dic['emergency_control_rod'] == 'no control rod':
        emergency_rod_cell.fill = He
        emergency_rod_cell.region = -reflector_top_boundary & +reflector_bottom_boundary & -outerWalls_1 & +outerWalls_3 & -outerWalls_4
        root_universe.add_cell(emergency_rod_cell)

    # 创建控制鼓 1
    drum_1_universe = openmc.Universe(name='control drum1')
    drum_1_B4C_cell = openmc.Cell(name='drum_1_B4C')
    drum_1_B4C_cell.fill = B4C
    drum_1_B4C_cell.region = -reflector_top_boundary & +reactor_bottom_boundary & -drum_1_outer & +drum_1_inner
    drum_1_universe.add_cell(drum_1_B4C_cell)
    drum_1_reflector_cell = openmc.Cell(name='drum_1_reflector')
    drum_1_reflector_cell.fill = drum_reflector
    drum_1_reflector_cell.region = -reflector_top_boundary & +reactor_bottom_boundary & -drum_1_inner & -drum_1_outer
    drum_1_universe.add_cell(drum_1_reflector_cell)

    drum_1_cell = openmc.Cell(name='drum1')
    drum_1_cell.fill = drum_1_universe
    drum_1_cell.region = -reflector_top_boundary & +reactor_bottom_boundary & -drum_1_outer
    root_universe.add_cell(drum_1_cell)

    # 创建热管单元
    HPcount = 0
    for i in range(4, 13):
        for j in range(i):
            x = HP_position001[HPcount][0] - 0.01
            y = HP_position001[HPcount][1]
            HP_boundary = openmc.ZCylinder(x0=x, y0=y, r=HP_D_outer / 2.)
            HP_cell = openmc.Cell(fill=K, region=-HP_boundary)
            root_universe.add_cell(HP_cell)
            all_cladding_cell.region = all_cladding_cell.region & +HP_boundary & +outerWalls_1 & +outerWalls_3 & -outerWalls_2 & -outerWalls_4 & -fuel_top_boundary & +fuel_bottom_boundary
            HP_cell.region = HP_cell.region & -reflector_top_boundary & +fuel_bottom_boundary
            HP_cell.temperature = temp_pipe
            HPcount += 1

    fuel_cell_ID_list = []
    fuelcount = 0
    for i in range(3, 11):
        for j in range(i):
            x = fuel_position001[fuelcount][0] - 0.01
            y = fuel_position001[fuelcount][1]
            fuel_1_boundary = openmc.ZCylinder(x0=x, y0=y, r=fuel_D_inner / 2.)
            fuel1_id = np.arange(1, 33, 2)
            fuel_1_cell = openmc.Cell(fill=fuel, region=-fuel_1_boundary)
            fuel_1_cell.id = fuel1_id[i - 3] * 1000 + (j + 1) * 10
            fuel_cell_ID_list.append(fuel1_id[i - 3] * 1000 + (j + 1) * 10)
            He_1_boundary = openmc.ZCylinder(x0=x, y0=y, r=fuel_D_outer / 2.)
            He_1_cell = openmc.Cell(fill=He, region=+fuel_1_boundary & -He_1_boundary)
            root_universe.add_cell(fuel_1_cell)
            root_universe.add_cell(He_1_cell)
            all_cladding_cell.region = all_cladding_cell.region & +He_1_boundary & +outerWalls_1 & +outerWalls_3 & -outerWalls_2 & -outerWalls_4 & -fuel_top_boundary & +fuel_bottom_boundary
            fuel_1_cell.region = fuel_1_cell.region & -fuel_top_boundary & +fuel_bottom_boundary
            fuel_1_cell.temperature = fuel_T_list[fuelcount]
            fuelcount += 1
            He_1_cell.region = He_1_cell.region & -fuel_top_boundary & +fuel_bottom_boundary

    for i in range(4, 12):
        for j in range(i):
            x = fuel_position001[fuelcount][0] - 0.01
            y = fuel_position001[fuelcount][1]
            fuel_2_boundary = openmc.ZCylinder(x0=x, y0=y, r=fuel_D_inner / 2.)
            fuel2_id = np.arange(2, 34, 2)
            fuel_2_cell = openmc.Cell(fill=fuel, region=-fuel_2_boundary)
            fuel_2_cell.id = fuel2_id[i - 4] * 1000 + (j + 1) * 10
            fuel_cell_ID_list.append(fuel2_id[i - 4] * 1000 + (j + 1) * 10)
            He_2_boundary = openmc.ZCylinder(x0=x, y0=y, r=fuel_D_outer / 2.)
            He_2_cell = openmc.Cell(fill=He, region=+fuel_2_boundary & -He_2_boundary)
            root_universe.add_cell(fuel_2_cell)
            root_universe.add_cell(He_2_cell)
            all_cladding_cell.region = all_cladding_cell.region & +He_2_boundary & +outerWalls_1 & +outerWalls_3 & -outerWalls_2 & -outerWalls_4 & -fuel_top_boundary & +fuel_bottom_boundary
            fuel_2_cell.region = fuel_2_cell.region & -fuel_top_boundary & +fuel_bottom_boundary
            fuel_2_cell.temperature = fuel_T_list[fuelcount]
            fuelcount += 1
            He_2_cell.region = He_2_cell.region & -fuel_top_boundary & +fuel_bottom_boundary

    all_cladding_cell.temperature = monolith_T
    root_universe.add_cell(all_cladding_cell)

    top_reflector_cell = openmc.Cell(fill=BeO, region=+outerWalls_1 & +outerWalls_3 & -outerWalls_2 & -outerWalls_4 & -reflector_top_boundary & +fuel_top_boundary)
    root_universe.add_cell(top_reflector_cell)

    reflector_radial_cell = openmc.Cell(name='reflector')
    reflector_radial_cell.fill = Al2O3
    reflector_radial_cell.region = +drum_1_outer & -reflector_top_boundary & +reactor_bottom_boundary & -reflector_outer & +outerWalls_2 & +outerWalls_3 & -outerWalls_4
    reflector_radial_cell.temperature = temp_pipe
    root_universe.add_cell(reflector_radial_cell)

    bottom_reflector_cell = openmc.Cell(name='bottom reflector')
    bottom_reflector_cell.fill = BeO
    bottom_reflector_cell.region = -fuel_bottom_boundary & +reflector_bottom_boundary & +outerWalls_1 & +outerWalls_3 & -outerWalls_2 & -outerWalls_4
    bottom_reflector_cell.temperature = temp_pipe
    root_universe.add_cell(bottom_reflector_cell)

    gas_plenum_cell = openmc.Cell(name='gas plenum')
    gas_plenum_cell.fill = gas
    gas_plenum_cell.region = -reflector_bottom_boundary & +reactor_bottom_boundary & +outerWalls_3 & -outerWalls_2 & -outerWalls_4
    root_universe.add_cell(gas_plenum_cell)

    geometry = openmc.Geometry(root_universe)
    geometry.export_to_xml()

    settings_MC_dic = settings_dic['settings_MC_dic']
    settings_file = openmc.Settings()
    settings_file.batches = settings_MC_dic['batches']
    settings_file.inactive = settings_MC_dic['inactive']
    settings_file.particles = settings_MC_dic['particles']
    settings_file.temperature['method'] = 'interpolation'
    bounds = [-R_reflector / 2, -R_reflector / 2, -R_reflector / 2, R_reflector / 2, R_reflector / 2, R_reflector / 2]
    uniform_dist = openmc.stats.Box(bounds[:3], bounds[3:], only_fissionable=True)
    settings_file.source = openmc.source.Source(space=uniform_dist)
    settings_file.export_to_xml()

    tallies = openmc.Tallies()
    for i in range(len(fuel_cell_ID_list)):
        cell_tally = openmc.Tally(name='cell tally' + str(fuel_cell_ID_list[i]))
        cell_tally.filters = [openmc.DistribcellFilter(fuel_cell_ID_list[i])]
        cell_tally.scores = ['heating', 'flux']
        tallies.append(cell_tally)

    energy_bins = np.logspace(np.log10(1e-3), np.log10(20.0e6), 101)
    fine_energy_filter = openmc.EnergyFilter(energy_bins)
    energy_tally = openmc.Tally(name='energy tally')
    energy_tally.filters.append(fine_energy_filter)
    energy_tally.scores = ['flux']
    tallies.append(energy_tally)

    mesh = openmc.RegularMesh()
    mesh.dimension = [100, 100]
    mesh.lower_left = [0, -40]
    mesh.upper_right = [80, 40]
    mesh_filter = openmc.MeshFilter(mesh)

    tally = openmc.Tally(name='fluxdis')
    tally.filters = [mesh_filter]
    tally.scores = ['flux', 'heating', 'fission']
    tallies.append(tally)

    meshz = openmc.RegularMesh()
    meshz.dimension = [100, 1, 210]
    meshz.lower_left = [0, -0.5, -115]
    meshz.upper_right = [100, 0.5, 95]
    meshz_filter = openmc.MeshFilter(meshz)

    tally = openmc.Tally(name='fluxdisz')
    tally.filters = [meshz_filter]
    tally.scores = ['flux', 'heating', 'fission']
    tallies.append(tally)

    meshp = openmc.RegularMesh()
    meshp.dimension = [800, 1200]
    meshp.lower_left = [wall_1, -30]
    meshp.upper_right = [wall_2, 30]
    meshp_filter = openmc.MeshFilter(meshp)

    tally = openmc.Tally(name='fluxdisp')
    tally.filters = [meshp_filter]
    tally.scores = ['flux', 'heating', 'fission']
    tallies.append(tally)

    meshzp = openmc.RegularMesh()
    meshzp.dimension = [400, 1, 1500]
    meshzp.lower_left = [wall_1, -0.5, -H_core / 2]
    meshzp.upper_right = [wall_2, 0.5, H_core / 2]
    meshzp_filter = openmc.MeshFilter(meshzp)

    tally = openmc.Tally(name='fluxdiszp')
    tally.filters = [meshzp_filter]
    tally.scores = ['flux', 'heating', 'fission']
    tallies.append(tally)

    tallies.export_to_xml()

    return fuel_cell_ID_list

def findpeak(mean):
    """
    从二维数组中找到峰值。
    """
    zongshu = 0
    zongzhi = 0
    themax = 0
    for i in mean:
        for j in i:
            if j > 0:
                zongshu += 1
                zongzhi += j
                if j > themax:
                    themax = j
    return themax / (zongzhi / zongshu)

def findmax(mean):
    """
    从二维数组中找到最大值。
    """
    themax = 0
    for i in mean:
        for j in i:
            if j > themax:
                themax = j
    return themax

def findpeak2(mean):
    """
    从一维数组中找到峰值。
    """
    zongshu = 0
    zongzhi = 0
    themax = 0
    for j in mean:
        if j > 0:
            zongshu += 1
            zongzhi += j
            if j > themax:
                themax = j
    return themax / (zongzhi / zongshu)

def postProcess(parameters_dic, fuel_cell_ID_list, iteration, settings_dic, run_dir=None):
    """
    后处理 OpenMC 的结果。
    """
    settings_MC_dic = settings_dic['settings_MC_dic']
    batches = settings_MC_dic['batches']
    heat_power = parameters_dic['heat_power']
    fuel_D_inner = parameters_dic['fuel_D_inner']
    H_core = parameters_dic['H_core']
    temp_pipe = parameters_dic['temp_pipe']
    monolith_T = parameters_dic['monolith_T']
    controldrum_angle = parameters_dic['controldrum_angle']

    heat_tot_vec = np.zeros(112)
    heat_dev_vec = np.zeros(112)
    flux_tot_vec = np.zeros(112)
    flux_dev_vec = np.zeros(112)
    thermal_tot_vec = np.zeros(112)
    volume_heat_vec = np.zeros(112)
    id_tally = np.zeros(112)
    volume_heat_vec_list = []
    thermal_tot_vec_list = []

    if run_dir is None:
        run_dir = os.getcwd()

    statepoint_path = os.path.join(run_dir, f"statepoint.{batches}.h5")
    print(f"[DEBUG] postProcess cwd = {os.getcwd()}")
    print(f"[DEBUG] postProcess statepoint_path = {statepoint_path}")

    sp = openmc.StatePoint(statepoint_path)
    k_eff = sp.k_combined

    with openmc.StatePoint(statepoint_path) as sp:
        for i in range(len(fuel_cell_ID_list)):
            t = sp.get_tally(name='cell tally' + str(fuel_cell_ID_list[i]))
            heat_tot_vec[i] = t.get_values(scores=['heating'], value='mean').item()
            thermal_tot_vec[i] = t.get_values(scores=['heating'], value='mean').item()
            heat_dev_vec[i] = t.get_values(scores=['heating'], value='std_dev').item()
            flux_tot_vec[i] = t.get_values(scores=['flux'], value='mean').item()
            flux_dev_vec[i] = t.get_values(scores=['flux'], value='std_dev').item()

        heat_power = heat_power / 6
        heat_power_origin = heat_tot_vec.sum()
        k_power = heat_power / (heat_power_origin * 1.6022e-19)

        volume_vec = H_core * np.pi * (fuel_D_inner * fuel_D_inner) / 4
        SS316_thermal_conductivity = calc_SS316_k(
            monolith_T,
            parameters_dic=parameters_dic
        )
        thermal_tot_vec = thermal_tot_vec * k_power * 1.6022e-19 / (fuel_D_inner * np.pi * H_core * SS316_thermal_conductivity)
        volume_heat_vec = heat_tot_vec * k_power * 1.6022e-19 / (fuel_D_inner * fuel_D_inner * np.pi * H_core / 4)

        heat_tot_vec = heat_tot_vec * k_power / volume_vec
        heat_dev_vec = heat_dev_vec * k_power / volume_vec
        flux_tot_vec = flux_tot_vec * k_power / volume_vec
        flux_dev_vec = flux_dev_vec * k_power / volume_vec

        if iteration > 0:
            heat_tot_new_vec = heat_tot_vec
            heat_dev_new_vec = heat_dev_vec
            heat_tot_vec = heat_tot_new_vec
            heat_dev_vec = heat_dev_new_vec

        tally_dic = {'heat_mean': heat_tot_vec, 'heat_dev': heat_dev_vec, 'flux_mean': flux_tot_vec, 'flux_dev': flux_dev_vec}
        tally_new_dic = {'heat_mean': heat_tot_vec, 'heat_dev': heat_dev_vec} if iteration > 0 else {}

        for i in range(len(fuel_cell_ID_list)):
            volume_heat_vec_list.append(volume_heat_vec[i])
        np.savetxt('pin_volume_heat.txt', volume_heat_vec)
        for i in range(len(fuel_cell_ID_list)):
            thermal_tot_vec_list.append(thermal_tot_vec[i])

        thepeak = []
        tally = sp.get_tally(name='fluxdisp')
        fission = tally.get_slice(scores=['fission'])
        thepeakof = findpeak(fission.mean)
        thepeak.append(thepeakof)

        heatingpower = tally.get_slice(scores=['flux'])
        heatingpower.mean.shape = (1200, 800)
        thepeakof = findpeak(heatingpower.mean)
        thepeak.append(thepeakof)

        tally = sp.get_tally(name='fluxdiszp')
        fission = tally.get_slice(scores=['fission'])
        fission.mean.shape = (1500, 400)
        thepeakof = findpeak(fission.mean)
        thepeak.append(thepeak)

        heatingpower = tally.get_slice(scores=['flux'])
        heatingpower.mean.shape = (1500, 400)
        thepeakof = findpeak(heatingpower.mean)
        thepeak.append(thepeakof)

        thepeak.append(findpeak2(thermal_tot_vec))
        cal_total_fuel_constant = fuel_D_inner * np.pi * H_core * SS316_thermal_conductivity

    return k_eff, k_power, thermal_tot_vec_list, volume_heat_vec, temp_pipe, tally_dic, tally_new_dic, thepeak, cal_total_fuel_constant

def calc_SS316_k(T, parameters_dic=None):
    """
    计算 SS316 在给定温度下的热导率，支持从参数字典读取扰动参数。

    参数:
        T (float): 温度，单位为开尔文 (K)
        parameters_dic (dict, 可选): 包含扰动参数的字典，支持如下键：
            'SS316_T_ref', 'SS316_k_ref', 'SS316_alpha', 'SS316_scale'

    返回:
        float: 热导率，单位为 W/(m·K)
    """
    if parameters_dic is not None:
        T_ref = parameters_dic.get('SS316_T_ref', 923.15)
        k_ref = parameters_dic.get('SS316_k_ref', 23.2)
        alpha = parameters_dic.get('SS316_alpha', 1/75)
        scale = parameters_dic.get('SS316_scale', 1/100)
    else:
        T_ref = 923.15
        k_ref = 23.2
        alpha = 1/75
        scale = 1/100
    k = ((T - T_ref) * alpha + k_ref) * scale
    return k

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
    heat_power = parameters_dic['heat_power']
    fuel_D_inner = parameters_dic['fuel_D_inner']
    H_core = parameters_dic['H_core']
    temp_pipe = parameters_dic['temp_pipe']
    monolith_T = parameters_dic['monolith_T']
    controldrum_angle = parameters_dic.get('controldrum_angle', 0)
    fuel_cell_ID_list = parameters_dic.get('fuel_cell_ID_list', list(range(len(pdct_distri))))
    omega = parameters_dic.get('relaxation', 1.0)

    # 关键：从 parameters_dic 读取扰动后的经验参数
    SS316_thermal_conductivity = calc_SS316_k(
        monolith_T,
        parameters_dic=parameters_dic
    )

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
    #kpower不对
    k_power = heat_power / (heat_power_origin * 1.6022e-19)
    volume_vec = H_core * np.pi * (fuel_D_inner * fuel_D_inner) / 4

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
    with open(f'{save_prefix}_out_debugdata.txt', 'a+') as fout:
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
