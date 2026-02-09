import ReqCopterSim
import sys
import RflyMavrosStart
import os
import json
import math
import re
from Utils import get_package_src_directory

# hot_region_search_config = "config-9.json"
MAX_VEHICLE = 50

# 获取配置文件路径 获取用户输入
config_name_input = input("Please input hot-region-search config name: ")

# 将初始位置写入自定义包json
hot_region_search_config_file = os.path.join(get_package_src_directory(
    'hot_region_search'), 'configs', config_name_input)

# 检查是否是正整数
if os.path.exists(hot_region_search_config_file):
    print(f"Using config file: {hot_region_search_config_file}")
    with open(hot_region_search_config_file, 'r') as f:
        config_data = json.load(f)
        topology = config_data['topology']
        if not topology or len(topology) != len(topology[0]) or not topology[0]:
            raise KeyError('Topology is not defined')
        VehicleNum = len(topology)
else:
    print(f"Config file {hot_region_search_config_file} does not exist")
    sys.exit(0)

req = ReqCopterSim.ReqCopterSim() # 获取局域网内所有CopterSim程序的电脑IP列表
# VehicleNum = 5

if not (RflyMavrosStart.isLinux and RflyMavrosStart.isRosOk):
    print('This demo can only run on with Ros')
    sys.exit(0)

ros_nodes = []

launch_file = os.path.dirname(os.path.abspath(__file__)) + '/px4.launch.xml'  # 修改为你的launch文件路径
config_file = os.path.dirname(os.path.abspath(__file__)) + '/px4_config.yaml'  # 修改为你的yaml文件路径
plugin_file = os.path.dirname(os.path.abspath(__file__)) + '/px4_pluginlists.yaml'  # 修改为你的yaml文件路径

# 读取MavrosRunInit.bat文件，提取变量
# 正则表达式解释：
# ^SET\s+/a\s+ : 匹配行首的 SET /a（忽略大小写）
# (\w+)        : 分组1，匹配变量名（字母、数字、下划线）
# \s*=\s* : 匹配等号，允许前后有空格
# ([\d.-]+)    : 分组2，匹配数值（支持整数、浮点数和负数）
pattern = re.compile(r'^SET\s+/a\s+(\w+)\s*=\s*([\d.-]+)', re.IGNORECASE)
variables = {}
with open(os.path.join(os.path.dirname(__file__), 'MavrosRunInit.bat'), 'r', encoding='utf-8') as f:
    for line in f:
        # 去掉行首尾空格
        line = line.strip()
        match = pattern.match(line)
        if match:
            var_name = match.group(1)
            var_value = match.group(2)
            
            # 尝试转换数值类型，优先转为 int，不行则转 float
            if '.' in var_value:
                variables[var_name] = float(var_value)
            else:
                variables[var_name] = int(var_value)
init_x = variables.get('ORIGIN_POS_X', 0)
init_y = variables.get('ORIGIN_POS_Y', 0)
interval = variables.get('VEHICLE_INTERVAL', 20)
sqrt_count = math.ceil(math.sqrt(VehicleNum))
uav_init_positions = []

for i in range(VehicleNum):
    TargetID = 1 + i # 初始飞机的ID号
    TargetIP = req.getSimIpID(TargetID) # 获取CopterSim的1号程序所在电脑的IP，作为目标IP
    namespace = f"uav_{TargetID}"
    # 注意：如果是本电脑运行的话，那TargetIP是127.0.0.1的本机地址；如果是远程访问，则是192打头的局域网地址。
    # 因此本程序能同时在本机运行，也能在其他电脑运行。
    if TargetIP=='':
        print('Failed to get IP of Copter #',TargetID)
        sys.exit(0)
    
    print(f'UAV {TargetID}: {TargetIP}')

    req.sendReSimIP(TargetID) # 请求回传数据到本电脑
    print(f'UAV {TargetID}: sendReSimIP')
    req.sendReSimUdpMode(TargetID,2) #強制切換MAVLINK_FULL
    print(f'UAV {TargetID}: sendReSimUdpMode')
    uav_init_x = (i // sqrt_count) * interval + init_x
    uav_init_y = (i % sqrt_count) * interval + init_y
    # req.sendReSimXYyaw(TargetID, [uav_init_x, uav_init_y, 0]) # 设置初始位置
    print(f'UAV {TargetID}: sendReSimXYyaw - x: {uav_init_x}, y: {uav_init_y}, yaw: 0')
    uav_init_positions.append([uav_init_x, uav_init_y, 0])
    
    ros = RflyMavrosStart.RflyMavrosStart(TargetID, 
                                          TargetIP, 
                                          namespace=namespace, 
                                          launch_file=launch_file, 
                                          config_file=config_file, 
                                          plugin_file=plugin_file)
    ros_nodes.append(ros)

# 将初始位置写入自定义包json
with open(hot_region_search_config_file, 'r') as f:
    config_data = json.load(f)
    config_data['uav_init_positions'] = uav_init_positions
with open(hot_region_search_config_file, 'w') as f:
    json.dump(config_data, f, indent=4)