# ROS 2 Jazzy / Ubuntu 24.04

Der Launch-Einstieg verwendet `realsense2_camera` aus dem offiziellen ROS-Wrapper. Das ist kein eigenes catkin-/ament-Kamerapaket. Die Wrapper-Dokumentation listet Ubuntu 24.04/Jazzy; wähle eine konkrete Wrapper-Version und die dazu passende SDK-Version. Siehe [offizielles Repository](https://github.com/realsenseai/realsense-ros).

Nach Installation des offiziellen Wrappers und Sourcen von ROS/gegebenenfalls Workspace:

```bash
source /opt/ros/jazzy/setup.bash
ros2 launch "$PWD/ros2/d435i.launch.py"
```

Aus dem Repository-Hauptverzeichnis starten. Der Launch wurde hier nur auf Python-Syntax geprüft; ROS und Kamera sind in der Entwicklungsumgebung nicht installiert. Profilkombination und Parameternamen mit deiner konkreten Wrapper-Version abgleichen.

```bash
ros2 topic list
ros2 topic hz /camera/camera/color/image_raw
ros2 topic hz /camera/camera/depth/image_rect_raw
ros2 topic hz /camera/camera/imu
ros2 run tf2_ros tf2_echo camera_link camera_color_optical_frame
rviz2
```

Erwartete Topics bei diesen Namen: `/camera/camera/color/image_raw`, `/camera/camera/aligned_depth_to_color/image_raw`, `/camera/camera/depth/color/points`, `/camera/camera/imu`, `/tf`, `/tf_static`. Vor Verwendung mit `ros2 topic list` bestätigen. RViz Fixed Frame zunächst `camera_link`; Image/PointCloud2 hinzufügen, Sensor-QoS bei Bedarf auf Best Effort setzen.

`unite_imu_method=2` bedeutet im vorgesehenen Wrapper Interpolation zur gemeinsamen IMU-Ausgabe. Es erzeugt weder eine absolute Pose noch eine neue physisch synchrone Sensormessung. Roh-Gyro und Roh-Accel getrennt prüfen. `enable_sync` ist kein Ersatz für ein übergreifendes Zeit-/Synchronisationskonzept.

Aufnahme mit dem ROS-2-eigenen Werkzeug, getrennt vom Standalone-Kameraadapter:

```bash
ros2 bag record -o recordings/ros-session-001 /camera/camera/color/image_raw /camera/camera/color/camera_info /camera/camera/aligned_depth_to_color/image_raw /camera/camera/aligned_depth_to_color/camera_info /camera/camera/imu /tf /tf_static
```

Ein bereits vorhandenes `recordings`-Verzeichnis voraussetzen bzw. vorher anlegen. Bei Mehrkamera oder Robotermontage zuerst Namen, extrinsische TFs und Mounting prüfen. Die optischen Kameraframes folgen x rechts/y unten/z vorwärts; ein Roboter-`base_link` üblicherweise x vorwärts/y links/z oben. Keine ungeprüften Identitätstransformationen einsetzen.

RTAB-Map, VIO, Belegungskarte und Navigation sind [Ausbaupakete R7–R11](../docs/roadmap.md). Sie sind noch keine lauffertige SLAM-/Nav2-Konfiguration in diesem Repository.
