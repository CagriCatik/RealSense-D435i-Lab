# 15 — Mapping und Robotikplanung

**Stand:** Lokale Kartierung automatisch geprüft; ROS-/RTAB-Map-Launch vorhanden, reale Abnahme offen; Nav2 geplant.

[V2-Anleitung](../../docs/mobile-mapping.md)

## Lernziel und Einordnung

Mapping braucht Pose/Odometrie, korrekte Zeit-/TF-Bezüge und eine Repräsentation unbekannter Bereiche. Der vorgesehene externe SLAM-Einstieg ist RTAB-Map.

## Dateien und Voraussetzungen

In diesem Projektordner liegt diese Anleitung. Der ausführbare Code wird gemeinsam im Paket unter `src/realsense_lab/` verwendet: **odometry.py / ProjectiveOdometry; mapping.py / LocalMapper; mapping_app.py; ros2/mapping.launch.py**. So entstehen keine voneinander abweichenden Kopien der Kameraaufnahme. Python >=3.11, Umgebung aus der Einrichtung; Zusatzbedarf: NumPy für lokale Kartierung; ROS/RTAB-Map für den getrennten SLAM-Einstieg.

## Einrichtung und Ablauf

Arbeitsverzeichnis: Repository-Hauptverzeichnis.

```bash
python -m pip install -e .
# ROS-Systeminstallation separat: siehe ros2/README.md
```

```bash
rs-lab map --source demo --frames 12 --output recordings/tutorial-15
```

Es entstehen eine farbige lokale Voxelkarte, eine geschätzte Trajektorie, RGB-D-Snapshots, ein Statusjournal und ein TSDF-Posemanifest. Autonome Fahrt ist nicht implementiert.

## Experiment

Definiere zuerst eine aufgezeichnete Referenzroute, erwartete Frames und Fehlermaße. Ergänze Montage-TF, Odometrie und später LiDAR, bevor du Navigation auf Hardware freigibst.

## Fehler und Grenzen

Keine Hindernisfreiheit aus schwarzen Tiefenpixeln ableiten; fehlende Messung bleibt unbekannt. Siehe auch [CLI/Formate](../../docs/cli.md) und [Hardware-Abnahme](../../docs/hardware-validation.md).

## Weiter

[Vorheriges Thema](../14_ros2/TUTORIAL.md) · [Nächstes Thema](../16_benchmarks/TUTORIAL.md) · [Index](../../TUTORIAL_INDEX.md)
