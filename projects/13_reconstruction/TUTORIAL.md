# 13 — TSDF-Rekonstruktion mit bekannten Posen

**Stand:** Open3D-Adapter vorhanden; nicht integriert ausgeführt.

## Lernziel und Einordnung

Manifest schema=1 enthält frames mit file und camera_to_world. Die Pose ist eine starre 4x4-Matrix in Metern. Open3D erhält ihre Inverse. Automatische Registrierung und SLAM sind noch nicht enthalten.

## Dateien und Voraussetzungen

In diesem Projektordner liegt diese Anleitung. Der ausführbare Code wird gemeinsam im Paket unter `src/realsense_lab/` verwendet: **reconstruction.py / integrate**. So entstehen keine voneinander abweichenden Kopien der Kameraaufnahme. Python >=3.11, Umgebung aus der Einrichtung; Zusatzbedarf: scan.

## Einrichtung und Ablauf

Arbeitsverzeichnis: Repository-Hauptverzeichnis.

```bash
python -m pip install -e '.[scan]'
```

```bash
rs-lab reconstruct --manifest recordings/scan/manifest.json --output artifacts/tutorial-13.ply
```

Bei gültigen rektifizierten RGB-D-Snapshots und bekannten Posen entsteht ein farbiges Mesh. Eingaben müssen vorher bereitgestellt werden.

## Experiment

Minimalen synthetischen Eingabesatz vorbereiten, bevor der obige Rekonstruktionsbefehl ausgeführt wird:

```bash
rs-lab capture --source demo --frames 1 --output recordings/scan
cp configs/scan-manifest.example.json recordings/scan/manifest.json
```

Die Beispielpose ist nur für diese eine Ansicht bzw. eine tatsächlich feststehende Kamera geeignet. Weitere Aufnahmen müssen ihre eigenen geprüften starren `camera_to_world`-Transformationen erhalten. Dateipfade im Manifest beziehen sich auf dessen Verzeichnis. TSDF-Konstanten des ersten Adapters: 1 cm Voxel, 4 cm Truncation, 3 m maximale Tiefe. Noch kein Qualitäts-/Performance-Benchmark.

Beginne mit einer statischen Kamera und geprüfter Identitätspose. Verwende keine Identitätsposen für bewegte Aufnahmen. Prüfe Maßstab und Transformationsrichtung.

## Fehler und Grenzen

Verzerrte Intrinsics werden abgelehnt; zuerst korrekt rektifizieren. Fehlende Pose darf nicht stillschweigend ersetzt werden. Siehe auch [CLI/Formate](../../docs/cli.md) und [Hardware-Abnahme](../../docs/hardware-validation.md).

## Weiter

[Vorheriges Thema](../12_imu/TUTORIAL.md) · [Nächstes Thema](../14_ros2/TUTORIAL.md) · [Index](../../TUTORIAL_INDEX.md)
