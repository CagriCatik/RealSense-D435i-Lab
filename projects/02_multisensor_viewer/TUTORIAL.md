# 02 — RGB-D- und IR-Viewer

**Stand:** Adapter vorhanden; Desktop-/Kameraabnahme offen.

## Lernziel und Einordnung

Beende den Explorer vor IR. RGB- und IR-Pixel gehören zu unterschiedlichen Kameramodellen. Motion wird separat in Projekt 12 untersucht.

## Dateien und Voraussetzungen

In diesem Projektordner liegt diese Anleitung. Der ausführbare Code wird gemeinsam im Paket unter `src/realsense_lab/` verwendet: **viewer.py / show; sdk.py / infrared_view**. So entstehen keine voneinander abweichenden Kopien der Kameraaufnahme. Python >=3.11, Umgebung aus der Einrichtung; Zusatzbedarf: camera,viewer.

## Einrichtung und Ablauf

Arbeitsverzeichnis: Repository-Hauptverzeichnis.

```bash
python -m pip install -e '.[camera,viewer]'
```

```bash
rs-lab view --source camera
rs-lab infrared
```

RGB, ausgerichtete Tiefe und Vogelperspektive erscheinen im Explorer. IR startet eine getrennte linke/rechte Stereoansicht.

## Experiment

Vergleiche nahe Objektkanten in RGB und Tiefenbild. Suche bewusst Verdeckungsbereiche und Randlöcher.

## Fehler und Grenzen

Kein Desktop: zuerst Demo/Analyse ohne GUI ausführen. Siehe auch [CLI/Formate](../../docs/cli.md) und [Hardware-Abnahme](../../docs/hardware-validation.md).

## Weiter

[Vorheriges Thema](../01_device_diagnostics/TUTORIAL.md) · [Nächstes Thema](../03_record_replay/TUTORIAL.md) · [Index](../../TUTORIAL_INDEX.md)
