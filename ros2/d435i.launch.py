"""Include the official driver; standalone launch file, not a replacement driver."""
from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource


def generate_launch_description():
    upstream = Path(get_package_share_directory("realsense2_camera"))/"launch"/"rs_launch.py"
    return LaunchDescription([IncludeLaunchDescription(
        PythonLaunchDescriptionSource(str(upstream)),
        launch_arguments={
            "camera_namespace": "camera",
            "camera_name": "camera",
            "enable_color": "true",
            "enable_depth": "true",
            "rgb_camera.color_profile": "640x480x30",
            "depth_module.depth_profile": "848x480x30",
            "align_depth.enable": "true",
            "pointcloud.enable": "true",
            "enable_gyro": "true",
            "enable_accel": "true",
            "unite_imu_method": "2",
            "enable_sync": "true",
        }.items())])
