# 14 — ROS 2, TF und RViz

**Stand:** Launch vorhanden; nur Syntaxprüfung, keine ROS-Abnahme.

## Lernziel und Einordnung

Standalone-Python und ROS-Node greifen nicht parallel auf dieselbe Kamera zu. TF trennt Roboter- und optische Achsen. IMU-Interpolation liefert keine absolute Pose.

## Dateien und Voraussetzungen

In diesem Projektordner liegt diese Anleitung. Der ausführbare Code wird gemeinsam im Paket unter `src/realsense_lab/` verwendet: **ros2/d435i.launch.py; ros2/README.md**. So entstehen keine voneinander abweichenden Kopien der Kameraaufnahme. Python >=3.11, Umgebung aus der Einrichtung; Zusatzbedarf: ROS 2 Jazzy + offizieller Wrapper.

## Einrichtung und Ablauf

Arbeitsverzeichnis: Repository-Hauptverzeichnis.

```bash
# Systeminstallation: siehe ros2/README.md
```

```bash
ros2 launch "$PWD/ros2/d435i.launch.py"
```

Der offizielle Wrapper soll RGB, Depth, Cloud und gemeinsame IMU-Ausgabe bereitstellen; konkrete Topics zuerst prüfen.

## Experiment

Folge ros2/README.md. Prüfe Topics, Bildraten, TF und RViz-QoS. Zeichne einen kurzen ros2 bag auf und spiele ihn ohne Kamera ab.

## Fehler und Grenzen

Wrapper-/SDK-Version oder Profil unpassend: Release-Kompatibilität und Launch-Parameter abgleichen. Siehe auch [CLI/Formate](../../docs/cli.md) und [Hardware-Abnahme](../../docs/hardware-validation.md).

## Weiter

[Vorheriges Thema](../13_reconstruction/TUTORIAL.md) · [Nächstes Thema](../15_mapping_robotics/TUTORIAL.md) · [Index](../../TUTORIAL_INDEX.md)
