# import pickle
import numpy as np
# import openmc
# import os
# import shutil
# import time
# import openmc.deplete
# import openmc.lib
# import scipy.io as sio
# import copy
# from tensorflow.keras.models import load_model
# import MEGA_OpenMC_test

# import Mega_calcule_method
# import mega_fenics_test

# import datetime
# import json

fenicsoutdata_dic = {
    'average_fuel_temp': 967.585141219741,
    'max_temp': 1015.7135841237631,
    'max_monolith_temp': 975.7473079552562,
    'average_monolith_temp': 929.7374628353697,
    'fuel_temp_ave_vec': [994.2492486353722, 997.2877162882907, 994.2470690558845],
    'newfuelposition': [[10.457277282960481, -2.806246493654665], [10.457547857540611, -0.0006280029116743005], [10.457277124497793, 2.8049918286092916]],
    'newheatpipeposition': [[9.64786375542126, -4.208273859240572], [9.64798082647225, -1.4030967852829117]],
    'newwall2': 29.902599357465633,
    'height': 152.25210594545396
}

def savefenics_data():
        fenics_dic= fenicsoutdata_dic
        output_file = 'else_data.txt'
        # save_file_path = 
        # 将所有数组按列组合成一个大的二维数组
        with open(output_file, 'w') as output:
            for key in fenics_dic:
                if key in ['fuel_temp_ave_vec', 'newfuelposition', 'newheatpipeposition']:
                    value = fenics_dic[key]
                    np.savetxt('' + f'{key}.txt', value)
                else:
                    value = fenics_dic[key]
                    output.write(str(value) + '\n')
savefenics_data()