# 15 — Mapping und Robotikplanung

**Stand:** Ausbauprojekt; kein SLAM-/Nav2-Stack implementiert.

## Lernziel und Einordnung

Mapping braucht Pose/Odometrie, korrekte Zeit-/TF-Bezüge und eine Repräsentation unbekannter Bereiche. Der vorgesehene externe SLAM-Einstieg ist RTAB-Map.

## Dateien und Voraussetzungen

In diesem Projektordner liegt diese Anleitung. Der ausführbare Code wird gemeinsam im Paket unter `src/realsense_lab/` verwendet: **analysis.py / summarize als Baustein; docs/roadmap.md R7–R11**. So entstehen keine voneinander abweichenden Kopien der Kameraaufnahme. Python >=3.11, Umgebung aus der Einrichtung; Zusatzbedarf: core für Vorarbeit; ROS/RTAB-Map später.

## Einrichtung und Ablauf

Arbeitsverzeichnis: Repository-Hauptverzeichnis.

```bash
Siehe ../../ros2/README.md für die Systeminstallation.
```

```bash
rs-lab analyze --source demo
```

Die ausführbare Vorarbeit ist Tiefen-/Ebenenanalyse. Eine Karte oder autonome Fahrt wird noch nicht erzeugt.

## Experiment

Definiere zuerst eine aufgezeichnete Referenzroute, erwartete Frames und Fehlermaße. Ergänze Montage-TF, Odometrie und später LiDAR, bevor du Navigation auf Hardware freigibst.

## Fehler und Grenzen

Keine Hindernisfreiheit aus schwarzen Tiefenpixeln ableiten; fehlende Messung bleibt unbekannt. Siehe auch [CLI/Formate](../../docs/cli.md) und [Hardware-Abnahme](../../docs/hardware-validation.md).

## Weiter

[Vorheriges Thema](../14_ros2/TUTORIAL.md) · [Nächstes Thema](../16_benchmarks/TUTORIAL.md) · [Index](../../TUTORIAL_INDEX.md)
