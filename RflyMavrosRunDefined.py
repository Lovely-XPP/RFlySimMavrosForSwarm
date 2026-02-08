import ReqCopterSim
import sys
import RflyMavrosStart
import os
import json
from Utils import get_package_src_directory

hot_region_search_config = "config-9.json"
MAX_VEHICLE = 50
# 将初始位置写入自定义包json
hot_region_search_config_file = os.path.join(get_package_src_directory('hot_region_search'), 'configs', hot_region_search_config)
with open(hot_region_search_config_file, 'r') as f:
    config_data = json.load(f)
try:
    topology = config_data['topology']
    if not topology or len(topology) != len(topology[0]) or not topology[0]:
        raise KeyError('Topology is not defined')
    VehicleNum = len(topology)
except:
    # 获取无人机数量
    try:
        # 获取用户输入
        vehicle_num_input = input("Please input UAV swarm number: ")
        
        # 检查是否是整数
        VehicleNum = int(vehicle_num_input)
        
        # 检查是否是正整数
        if VehicleNum > 0:
            # 检查是否超过最大数量
            if VehicleNum > MAX_VEHICLE:
                print(f"The vehicle number should be 1 - {MAX_VEHICLE}.")
                sys.exit(0)
        else:
            print("Not a positive integer")
            sys.exit(0)
    except ValueError:
        print("Not an integer")
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

init_x = 0
init_y = 0
interval = 20
sqrt_count = 3
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
    uav_init_x = ((i - 1) // sqrt_count) * interval + init_x
    uav_init_y = ((i - 1) % sqrt_count) * interval + init_y
    req.sendReSimXYyaw(TargetID, [uav_init_x, uav_init_y, 0]) # 设置初始位置
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