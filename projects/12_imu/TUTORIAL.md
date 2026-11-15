# 12 — IMU-Aufnahme und Diagnose

**Stand:** CSV-Auswertung geprüft; Motion-Adapter und reale Rate offen.

## Lernziel und Einordnung

Die angebotenen Profile werden dynamisch gewählt. Die Callback-Queue zählt Software-Überläufe. Stationär lassen sich Gyro-Bias und Accel-Norm untersuchen; keine automatische Kalibrierschreibung.

## Dateien und Voraussetzungen

In diesem Projektordner liegt diese Anleitung. Der ausführbare Code wird gemeinsam im Paket unter `src/realsense_lab/` verwendet: **sdk.py / collect_motion; imu.py / summarize_imu**. So entstehen keine voneinander abweichenden Kopien der Kameraaufnahme. Python >=3.11, Umgebung aus der Einrichtung; Zusatzbedarf: camera.

## Einrichtung und Ablauf

Arbeitsverzeichnis: Repository-Hauptverzeichnis.

```bash
python -m pip install -e '.[camera]'
```

```bash
rs-lab imu --seconds 10 --output recordings/tutorial-12.csv
rs-lab imu-report --input recordings/tutorial-12.csv
```

Getrennte Accel-/Gyro-Samples mit Domain und Zeitstempel, danach Mittelwert, Streuung und beobachtete Rate.

## Experiment

Erst stationär messen, dann um bekannte Achsen drehen. Vergleiche tatsächliche Intervallrate mit angebotenem Profil. Beide IMU-Revisionen berücksichtigen.

## Fehler und Grenzen

Zeitreihen nicht nach Zeilennummer koppeln. IMU-Fusion und driftfreie Position sind nicht implementiert. Siehe auch [CLI/Formate](../../docs/cli.md) und [Hardware-Abnahme](../../docs/hardware-validation.md).

## Weiter

[Vorheriges Thema](../11_tracking/TUTORIAL.md) · [Nächstes Thema](../13_reconstruction/TUTORIAL.md) · [Index](../../TUTORIAL_INDEX.md)
