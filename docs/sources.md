# Offizielle Quellen

Quellenprüfung: 15.11.2026. Verweise auf `master`/`ros2-master` sind beweglich; für Hardware-Abnahmen SDK- und Wrapper-Release bzw. Commit im Protokoll festhalten.

| ID | Quelle | Verwendung |
|---|---|---|
| S1 | [D435i Produktseite](https://www.realsenseai.com/products/depth-camera-d435i/) | Eckdaten, RGB/Tiefensensor, idealer Bereich |
| S2 | [D400 Datenblatt März 2026](https://www.realsenseai.com/wp-content/uploads/2026/03/RealSense-D400-Series-Datasheet-Mar-2026.pdf) | Profil-/Hardwaregrenzen und IMU-Revisionen |
| S3 | [Offizielles librealsense](https://github.com/realsenseai/librealsense) | Installation, Releases, SDK und Firmwarekompatibilität |
| S4 | [D435i im SDK](https://github.com/realsenseai/librealsense/blob/master/doc/d435i.md) | Motion, Achsen, Zeitstempel und Kalibrierung |
| S5 | [Python-Beispiele](https://github.com/realsenseai/librealsense/tree/master/wrappers/python/examples) | Streamzugriff, Ausrichtung, Pointcloud und Advanced Mode |
| S6 | [Tiefenfilter](https://dev.realsenseai.com/docs/post-processing-filters/) | Spatial/Temporal, Disparität und Hole Filling |
| S7 | [Projektion und Verdeckung](https://dev.realsenseai.com/docs/projection-texture-mapping-and-occlusion-with-intel-realsense-depth-cameras/) | Pixel, 3D, RGB-Zuordnung und Occlusion |
| S8 | [SDK-Aufnahme/Wiedergabe](https://github.com/realsenseai/librealsense/blob/master/doc/record-and-playback.md) | Versionsabhängige native Formate |
| S9 | [Offizieller ROS-Wrapper](https://github.com/realsenseai/realsense-ros) | Jazzy, Launch-Parameter, Topics und SDK-Zuordnung |
| S10 | [ROS-2-Dokumentation](https://dev.realsenseai.com/docs/ros2-wrapper/) | Bilder, PointCloud2, IMU und TF |
| S11 | [D400 Self-Calibration](https://dev.realsenseai.com/docs/intel-realsense-self-calibration-for-d400-series-depth-cameras/) | Voraussetzungen und Grenzen der Tiefenkalibrierung |
| S12 | [D400 Visual Presets](https://dev.realsenseai.com/docs/d400-series-visual-presets/) | Vordefinierte Einstellungen und Advanced Mode |
| S13 | [Mehrkamera-Whitepaper](https://www.intel.com/content/dam/support/us/en/documents/emerging-technologies/intel-realsense-technology/RealSense_Multiple_Camera_WhitePaper.pdf) | Mehrkamera, Bandbreite und Synchronisation |
| S14 | [Ultralytics Predict](https://docs.ultralytics.com/modes/predict/) | BGR-NumPy-Eingabe und Box-Ergebnisse |
| S15 | [Open3D RGB-D Integration](https://www.open3d.org/docs/release/tutorial/pipelines/rgbd_integration.html) | TSDF mit bekannten Posen; lokal noch nicht integriert geprüft |
| S16 | [RTAB-Map ROS](https://github.com/introlab/rtabmap_ros) | Externer SLAM-Einstieg; Integration offen |
| S17 | [Ultralytics Results/Masks](https://docs.ultralytics.com/reference/engine/results/) | Box-/Maskenergebnisse; Polygone in Originalbildkoordinaten |

Herstellerdokumentation ist die Referenz für Kamerafunktionen. YOLO, Tracking, TSDF, SLAM und Robotiknavigation sind zusätzliche Softwareanwendungen; ihre Qualität ist keine zugesicherte Kamerafunktion. Die Open3D-Tutorialseite war bei der Quellenprüfung nicht abrufbar; API und Integration müssen mit installierter Open3D-Version nochmals geprüft werden.
