# 01 — Gerätecheck und Profile

**Stand:** Adapter vorhanden; Geräteabnahme offen.

## Lernziel und Einordnung

Vergleiche die RGB- und Tiefenprofile. Suche IR1/IR2 und Motion. Einzelprofile sind keine Liste aller gleichzeitig erlaubten Kombinationen.

## Dateien und Voraussetzungen

In diesem Projektordner liegt diese Anleitung. Der ausführbare Code wird gemeinsam im Paket unter `src/realsense_lab/` verwendet: **sdk.py / inspect_devices**. So entstehen keine voneinander abweichenden Kopien der Kameraaufnahme. Python >=3.11, Umgebung aus der Einrichtung; Zusatzbedarf: camera.

## Einrichtung und Ablauf

Arbeitsverzeichnis: Repository-Hauptverzeichnis.

```bash
python -m pip install -e '.[camera]'
```

```bash
rs-lab inspect --output artifacts/device-001.json
```

Gerät, Firmware, USB-Modus, einzelne Streamprofile, Intrinsics und Optionsbereiche werden als JSON ausgegeben. Ohne Gerät ist der Exitcode 2.

## Experiment

Prüfe im offiziellen Viewer dieselben Profile. Dokumentiere, welche RGB-D-Kombination mit deinem USB-Port tatsächlich startet.

## Fehler und Grenzen

Keine Kamera: Datenkabel, Zugriffsregeln und andere Kamera-Prozesse prüfen. Siehe auch [CLI/Formate](../../docs/cli.md) und [Hardware-Abnahme](../../docs/hardware-validation.md).

## Weiter

[Vorheriges Thema](../../README.md) · [Nächstes Thema](../02_multisensor_viewer/TUTORIAL.md) · [Index](../../TUTORIAL_INDEX.md)
