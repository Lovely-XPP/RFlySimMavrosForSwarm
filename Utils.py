from ament_index_python.packages import get_package_share_directory
import os

def get_package_src_directory(package_name) -> str:
    # 先获取安装路径
    install_dir = get_package_share_directory(package_name)
    
    # 通常逻辑：从 install/package_name/share 回溯到工作空间根目录
    # 这在标准的 colcon build 结构中有效
    workspace_root = os.path.abspath(os.path.join(install_dir, '../../../../'))
    src_dir = os.path.join(workspace_root, 'src', package_name)
    if not os.path.exists(src_dir):
        src_dir = os.path.join(workspace_root)
    return src_dir