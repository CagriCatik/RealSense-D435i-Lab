# 03 — Aufnahme und Wiedergabe

**Stand:** Portable RGB-D-Kette automatisch geprüft; native Kameraaufnahme offen.

## Lernziel und Einordnung

NPZ speichert RGB, axiale Tiefe in Metern, Geometrie, Zeitstempel und Domain; optional SDK-Rays. Das ist keine vollständige Rohstereo-/IMU-Aufnahme.

## Dateien und Voraussetzungen

In diesem Projektordner liegt diese Anleitung. Der ausführbare Code wird gemeinsam im Paket unter `src/realsense_lab/` verwendet: **sources.py / ReplaySource; storage.py / save_frame, load_frame**. So entstehen keine voneinander abweichenden Kopien der Kameraaufnahme. Python >=3.11, Umgebung aus der Einrichtung; Zusatzbedarf: core.

## Einrichtung und Ablauf

Arbeitsverzeichnis: Repository-Hauptverzeichnis.

```bash
python -m pip install -e .
```

```bash
rs-lab capture --source demo --frames 10 --output recordings/tutorial-03
rs-lab analyze --source replay --input recordings/tutorial-03
rs-lab export --source replay --input recordings/tutorial-03 --output artifacts/tutorial-03.ply
```

Zehn NPZ-Dateien, eine JSON-Terminalanalyse und eine farbige PLY-Datei.

## Experiment

Ersetze demo durch camera. Vergleiche vor/nach dem Speichern identische Pixel. Native Formate sind in docs/cli.md beschrieben.

## Fehler und Grenzen

Ausgaben existieren: neue Sitzung verwenden; Dateien werden nicht überschrieben. Siehe auch [CLI/Formate](../../docs/cli.md) und [Hardware-Abnahme](../../docs/hardware-validation.md).

## Weiter

[Vorheriges Thema](../02_multisensor_viewer/TUTORIAL.md) · [Nächstes Thema](../04_depth_filters/TUTORIAL.md) · [Index](../../TUTORIAL_INDEX.md)
