# 04 — Tiefenfilter-Labor

**Stand:** SDK-Filter implementiert; Qualitätsvergleich offen.

## Lernziel und Einordnung

Threshold beschneidet Z; Spatial glättet räumlich, Temporal verwendet Historie. Hole Filling ist standardmäßig aus. Die Kameraquelle richtet vor dem Filtern aus; für Qualitätsarbeit native Filterreihenfolge vergleichen.

## Dateien und Voraussetzungen

In diesem Projektordner liegt diese Anleitung. Der ausführbare Code wird gemeinsam im Paket unter `src/realsense_lab/` verwendet: **sdk.py / CameraSource._filter; configs/*.json**. So entstehen keine voneinander abweichenden Kopien der Kameraaufnahme. Python >=3.11, Umgebung aus der Einrichtung; Zusatzbedarf: camera,viewer.

## Einrichtung und Ablauf

Arbeitsverzeichnis: Repository-Hauptverzeichnis.

```bash
python -m pip install -e '.[camera,viewer]'
```

```bash
rs-lab view --source camera --config configs/raw.json
rs-lab view --source camera --config configs/default.json
rs-lab view --source camera --config configs/static-scene.json
```

Drei nacheinander gestartete Versuche mit verschiedenen Filtern.

## Experiment

Fixiere Kamera/Ziel. Vergleiche eine statische Fläche und ein bewegtes Objekt. Notiere Löcher, Kanten und Trails. Demo/NPZ-Replay wird nicht mit SDK-Filtern neu verarbeitet.

## Fehler und Grenzen

raw ist keine Rohsensoraufnahme: Ausrichtung und Threshold bleiben aktiv. Siehe auch [CLI/Formate](../../docs/cli.md) und [Hardware-Abnahme](../../docs/hardware-validation.md).

## Weiter

[Vorheriges Thema](../03_record_replay/TUTORIAL.md) · [Nächstes Thema](../05_camera_geometry/TUTORIAL.md) · [Index](../../TUTORIAL_INDEX.md)
