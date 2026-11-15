"""D435i + IMU orientation + RTAB-Map. Existing databases are never reset here."""
from pathlib import Path

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    camera_launch = Path(__file__).with_name("d435i.launch.py")
    topics = [("rgb/image", "/camera/camera/color/image_raw"),
              ("rgb/camera_info", "/camera/camera/color/camera_info"),
              ("depth/image", "/camera/camera/aligned_depth_to_color/image_raw"),
              ("imu", "/rtabmap/imu")]
    common = {"frame_id": "camera_link", "subscribe_depth": True,
              "subscribe_odom_info": True, "approx_sync": True,
              "wait_imu_to_init": True, "qos": 2}
    database = ParameterValue(LaunchConfiguration("database_path"), value_type=str)
    return LaunchDescription([
        DeclareLaunchArgument("database_path", default_value=str(Path.home()/".ros"/"d435i-lab.db"),
                              description="RTAB-Map database; choose a new path for a new survey"),
        IncludeLaunchDescription(PythonLaunchDescriptionSource(str(camera_launch))),
        Node(package="imu_filter_madgwick", executable="imu_filter_madgwick_node",
             name="imu_orientation", namespace="rtabmap", output="screen",
             parameters=[{"use_mag": False, "world_frame": "enu", "publish_tf": False}],
             remappings=[("imu/data_raw", "/camera/camera/imu"), ("imu/data", "/rtabmap/imu")]),
        Node(package="rtabmap_odom", executable="rgbd_odometry", name="odometry",
             namespace="rtabmap", output="screen", parameters=[common], remappings=topics),
        Node(package="rtabmap_slam", executable="rtabmap", name="mapping", namespace="rtabmap",
             output="screen", parameters=[dict(common, database_path=database)], remappings=topics),
        Node(package="rtabmap_viz", executable="rtabmap_viz", name="visualization", namespace="rtabmap",
             output="screen", parameters=[common], remappings=topics),
    ])
