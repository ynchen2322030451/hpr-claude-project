from dolfin import *
from subprocess import call
import os
import numpy as np
import math
import matplotlib.pyplot as plt


'''
热管反应堆 Fenics 有限元热 - 结构耦合计算模块
核心用途：基于 Fenics 框架，实现热管反应堆关键多物理场计算，包括 2D 热传导、2D 结构应力 / 热膨胀、3D 热膨胀，支持材料参数扰动与结果输出
关键函数说明：
1. check_and_remove：辅助函数，删除旧计算文件（如.xml.gz、.pvd、.vtu），避免文件冲突导致计算错误
2. fenic_expansion_z：3D 热膨胀计算，输入平均单体温度与材料参数，输出 Z 方向位移结果（保存为 PVD/VTU 文件）
3. fenic_conduction_xy：2D 核心计算，集成热传导（获取热管热通量、边界温度）、热膨胀（位移）、结构应力分析，输出温度、位移、应力结果文件及关键数据（热通量、平均单体温度）
核心依赖：Fenics（有限元求解）、numpy（数值计算）、subprocess（调用 dolfin-convert 转换网格）
关键输入：
- 材料参数（弹性模量 E、泊松比 nu、热膨胀系数 alpha，通过 material_params 字典传入，支持温度依赖计算）
- 几何网格文件（.msh 格式，需提前生成，函数内自动转换为 Fenics 可识别的.xml.gz 格式）
- 边界条件（温度、固定约束）、热通量数据、失效热管列表（loseHp）
输出结果：
- 可视化文件：温度、位移、应力的 PVD（结果序列）与 VTU（单步结果）文件
- 数值数据：热管热通量、热管边界温度、单体平均温度（供后续耦合计算使用）
'''
# 检查文件是否存在，如果存在则删除，避免错误
def check_and_remove(filename):
    """
    检查文件是否存在，如果存在则删除。
    
    参数:
        filename (str): 文件路径。
    """
    if os.path.exists(filename):
        os.remove(filename)

def fenic_expansion_z(average_monolith_temp, material_params, file_name_Basis_Expansion_Z='Thermal_expansion_z'):
    """
    计算 3D 热膨胀问题，并支持材料参数的扰动。

    参数:
        average_monolith_temp (float): 平均单体温度。
        material_params (dict): 包含材料参数的字典，包括 E_slope, E_intercept, nu, alpha_base, alpha_slope。
        file_name_Basis_Expansion_Z (str): 基础文件名（不带扩展名）。
    """
    # 删除旧的文件，避免冲突
    check_and_remove(file_name_Basis_Expansion_Z + '.xml.gz')
    check_and_remove(file_name_Basis_Expansion_Z + '_facet_region.xml.gz')
    check_and_remove(file_name_Basis_Expansion_Z + '_physical_region.xml.gz')
    check_and_remove(file_name_Basis_Expansion_Z + '.pvd')
    check_and_remove(file_name_Basis_Expansion_Z + '000000.vtu')

    # 转换网格文件
    call('dolfin-convert {}.msh {}.xml;gzip {}*.xml'.format(file_name_Basis_Expansion_Z, file_name_Basis_Expansion_Z, file_name_Basis_Expansion_Z), shell=True)
    mesh = Mesh('{}.xml.gz'.format(file_name_Basis_Expansion_Z))
    boundaries = MeshFunction("size_t", mesh, "{}_facet_region.xml.gz".format(file_name_Basis_Expansion_Z))
    subdomains = MeshFunction("size_t", mesh, "{}_physical_region.xml.gz".format(file_name_Basis_Expansion_Z))
    V = FunctionSpace(mesh, "CG", 1)

    # 定义试探函数和测试函数
    u = TrialFunction(V)
    v = TestFunction(V)
    bcs = []

    # 设置边界条件
    bound_id = [1, 78]
    for i in range(33, 78, 4):
        bound_id.append(i)
    for i in bound_id:
        bc = DirichletBC(V, average_monolith_temp, boundaries, i)
        bcs.append(bc)

    # 定义测度
    ds = Measure('ds', domain=mesh, subdomain_data=boundaries)
    dx = Measure('dx', domain=mesh, subdomain_data=subdomains)

    # 定义弱形式
    a = (inner(grad(u), grad(v)) * dx)
    L = Constant(0) * v * dx
    u = Function(V, name='temp')
    solve(a == L, u, bcs, solver_parameters={'linear_solver': 'bicgstab', 'preconditioner': 'hypre_amg'})

    # 计算弹性问题
    average_monolith_temp += 300
    # 添加材料参数验证
    if not material_params:
        raise ValueError("材料参数不能为空")
    
    # 修改弹性模量计算公式
    E = (material_params['E_slope'] * average_monolith_temp + material_params['E_intercept']) / 1e6
    nu = material_params['nu']
    alpha = Constant(material_params['alpha_base'] + material_params['alpha_slope'] * average_monolith_temp)
    mu = E / 2 / (1 + nu)
    lmbda = E * nu / (1 + nu) / (1 - 2 * nu)
    alpha = Constant(material_params['alpha_base'] + material_params['alpha_slope'] * average_monolith_temp)

    f = Constant((0, 0, 0))

    def eps(v):
        return sym(grad(v))

    def sigma(v, dT):
        return (lmbda * tr(eps(v)) - alpha * (3 * lmbda + 2 * mu) * dT) * Identity(3) + 2.0 * mu * eps(v)

    Vu = VectorFunctionSpace(mesh, 'Lagrange', 1)
    du = TrialFunction(Vu)
    u_ = TestFunction(Vu)
    Wint = inner(sigma(du, u), eps(u_)) * dx
    aM = lhs(Wint)
    LM = rhs(Wint) + inner(f, u_) * dx

    # 设置边界条件
    bcus = []
    bcu = DirichletBC(Vu.sub(2), Constant(0), boundaries, 1)
    bcus.append(bcu)
    bcu = DirichletBC(Vu.sub(0), Constant(0), boundaries, 33)
    bcus.append(bcu)

    u2 = Function(Vu, name="Displacement")
    solve(aM == LM, u2, bcus)

    # 保存结果到文件
    pvd_file_u2 = File("{}.pvd".format(file_name_Basis_Expansion_Z))
    pvd_file_u2 << u2

def fenic_conduction_xy(material_params, hp_r, fuel_r, thermal_tot_vec_list, heatpipe_temp, loseHp=[], file_name_Basis_Thermal='Thermal_conduction',
                        file_name_Expansion_xy='Thermal_expansion_xy', file_name_Expansion_Stress='Thermal_expansion_stress',
                        file_name_Temperature_Gradient='Thermal_condition_grad'):
    """
    计算 2D 热传导和膨胀问题。
    
    参数:
        hp_r (float): 热管半径。
        fuel_r (float): 燃料半径。
        thermal_tot_vec_list (list): 每个燃料的热通量。
        heatpipe_temp (list): 热管温度。
        loseHp (list): 设置为绝热的热管 ID 列表。
        file_name_Basis_Thermal (str): 热传导基础文件名。
        file_name_Expansion_xy (str): 热膨胀文件名。
        file_name_Expansion_Stress (str): 热膨胀应力文件名。
        file_name_Temperature_Gradient (str): 温度梯度文件名。
    """
    # 删除旧的文件，避免冲突
    check_and_remove(file_name_Basis_Thermal + '.pvd')
    check_and_remove(file_name_Basis_Thermal + '000000.vtu')
    check_and_remove(file_name_Expansion_Stress + '.pvd')
    check_and_remove(file_name_Expansion_Stress + '000000.vtu')
    check_and_remove(file_name_Temperature_Gradient + '.pvd')
    check_and_remove(file_name_Temperature_Gradient + '000000.vtu')
    check_and_remove(file_name_Basis_Thermal + '_only.pvd')
    check_and_remove(file_name_Basis_Thermal + '_only000000.vtu')
    check_and_remove(file_name_Expansion_xy + '.pvd')
    check_and_remove(file_name_Expansion_xy + '000000.vtu')

    # 删除旧的文件，避免冲突
    fuel_D_outer = fuel_r * 2

    num_fuel = len(thermal_tot_vec_list)

    # 检查并加载网格文件
    mesh_file = f"{file_name_Basis_Thermal}.xml.gz"
    if not os.path.exists(mesh_file):
        raise FileNotFoundError(f"网格文件 {mesh_file} 不存在，请检查文件路径或生成网格文件。")
    mesh = Mesh(mesh_file)

    # 打印 mesh 类型和其他参数类型
    print(f"加载的网格文件: {mesh_file}")
    print(f"mesh 类型: {type(mesh)}")
    print("mesh 内容：", mesh)
    print(f"thermal_tot_vec_list 类型: {type(thermal_tot_vec_list)}")
    print(f"heatpipe_temp 类型: {type(heatpipe_temp)}")
    print(f"loseHp 类型: {type(loseHp)}")

    # 打印 thermal_tot_vec_list 的值范围
    print(f"thermal_tot_vec_list 最小值: {np.min(thermal_tot_vec_list)}, 最大值: {np.max(thermal_tot_vec_list)}")

    # 确保 mesh 是正确的类型
    if not isinstance(mesh, Mesh):
        raise TypeError(f"加载的网格文件类型错误，期望 Mesh 类型，但得到 {type(mesh)}")

    boundaries = MeshFunction("size_t", mesh, "{}_facet_region.xml.gz".format(file_name_Basis_Thermal))
    subdomains = MeshFunction("size_t", mesh, "{}_physical_region.xml.gz".format(file_name_Basis_Thermal))
    V = FunctionSpace(mesh, "CG", 1)
    u = TrialFunction(V)
    v = TestFunction(V)
    bcs = []
    integrals_N = []
    ds = Measure('ds', domain=mesh, subdomain_data=boundaries)
    dS = Measure('dS', domain=mesh, subdomain_data=boundaries)
    dx = Measure('dx', domain=mesh, subdomain_data=subdomains)
    for i in range(0, 72):
        if i in loseHp:
            cos0 = Constant(0)
            integrals_N.append(cos0 * v * ds(i * 6 + 5))
        else:
            bc = DirichletBC(V, heatpipe_temp[i], boundaries, i * 6 + 5)
            bcs.append(bc)

    g = [None] * num_fuel
    g_expression = [None] * num_fuel

    for i in range(num_fuel):
        g[i] = Constant(thermal_tot_vec_list[i] * 4 / fuel_D_outer)

    for i in range(num_fuel):
        integrals_N.append(g[i] * v * dx(i * 6 + 438))
    the_bound_expression = [None] * 4
    the_bound = [None] * 4

    for i in range(4):
        the_bound[i] = Constant(0)
        integrals_N.append(the_bound[i] * v * ds(i + 3341))

    a = (0.8455 * inner(grad(u), grad(v)) * dx(4001) + 0.1545 * inner(grad(u), grad(v)) * dx)
    L = sum(integrals_N)
    u = Function(V, name='temp')
    solve(a == L, u, bcs, solver_parameters={'linear_solver': 'bicgstab', 'preconditioner': 'hypre_amg'})

    f5 = Function(V)
    f5.vector()[:] = 1

    average_monolith_temp = assemble(1 * u * dx(4001)) / assemble(1 * f5 * dx(4001)) + 300
    print(average_monolith_temp)

    E = (-7e7 * average_monolith_temp + 2e11) / 1e6
    nu = 0.31
    mu = E / 2 / (1 + nu)
    lmbda = E * nu / (1 + nu) / (1 - 2 * nu)
    alpha = Constant(1e-5 + 5e-9 * average_monolith_temp)

    E = (material_params['E_slope'] * average_monolith_temp + material_params['E_intercept']) / 1e6
    nu = material_params['nu']
    alpha = Constant(material_params['alpha_base'] + material_params['alpha_slope'] * average_monolith_temp)
    mu = E / 2 / (1 + nu)
    lmbda = E * nu / (1 + nu) / (1 - 2 * nu)
    alpha = Constant(material_params['alpha_base'] + material_params['alpha_slope'] * average_monolith_temp)

    f = Constant((0, 0))

    def eps(v):
        return sym(grad(v))

    def sigma(v, dT):
        return (lmbda * tr(eps(v)) - alpha * (3 * lmbda + 2 * mu) * dT) * Identity(2) + 2.0 * mu * eps(v)

    Vu = VectorFunctionSpace(mesh, 'CG', 2)
    du = TrialFunction(Vu)
    u_ = TestFunction(Vu)
    Wint = inner(sigma(du, u), eps(u_)) * dx(4001)
    aM = lhs(Wint)
    LM = rhs(Wint) + inner(f, u_) * dx(4001)

    bcus = []
    for i in range(3341, 3345):
        if i == 3342:
            pass
        else:
            bcu = DirichletBC(Vu.sub(0), Constant(0), boundaries, 3344)
            bcus.append(bcu)

    u2 = Function(Vu, name="Displacement")
    solve(aM == LM, u2, bcus)
    bcus2 = []

    u3 = Function(Vu, name="Displacementnolimit")
    solve(aM == LM, u3, bcus2)
    print('solve done')

    # 输出 2D displacement
    pvd_file_u2 = File("{}.pvd".format(file_name_Expansion_xy))
    pvd_file_u2 << u2

    # 输出 2D stress
    W = TensorFunctionSpace(mesh, 'Discontinuous Lagrange', 0)
    stress_proj = project(sigma(u3, u), V=W)
    pvd_file_si = File("{}.pvd".format(file_name_Expansion_Stress))
    pvd_file_si << stress_proj  # 确保使用正确的文件名

    pvd_file_u = File("{}.pvd".format(file_name_Basis_Thermal))
    pvd_file_u << u
    print('allpvdout')

    the_bound_temp_heatpipe = []
    the_bound_temp_fuel = []

    for i in range(72):
        if i in loseHp:
            the_bound_temp_heatpipe.append(assemble(1 * u * ds(i * 6 + 5)) / assemble(1 * f5 * ds(i * 6 + 5)))
        else:
            the_bound_temp_heatpipe.append(heatpipe_temp[i])

    hpflux = []
    for i in range(0, 72):
        if i in loseHp:
            hpflux.append(0)
        else:
            n = FacetNormal(mesh)
            flux = -1 * dot(n, nabla_grad(u)) * ds(i * 6 + 5)
            total_flux = assemble(flux)
            hpflux.append(total_flux)
    print('fenics done')
    return hpflux, the_bound_temp_heatpipe, average_monolith_temp

