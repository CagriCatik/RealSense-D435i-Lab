# 10 — YOLO mit 3D-Position

**Stand:** Inferenzadapter vorhanden; Modell-/Hardwareabnahme offen.

## Lernziel und Einordnung

RGB wird am Adapter nach BGR konvertiert. Ein robuster Median am Boxzentrum liefert Z, anschließend erfolgt Deprojektion. Die Position kann Hintergrund statt Objekt treffen; keine echte 3D-Box.

## Dateien und Voraussetzungen

In diesem Projektordner liegt diese Anleitung. Der ausführbare Code wird gemeinsam im Paket unter `src/realsense_lab/` verwendet: **detection.py / Detector.predict**. So entstehen keine voneinander abweichenden Kopien der Kameraaufnahme. Python >=3.11, Umgebung aus der Einrichtung; Zusatzbedarf: camera,viewer,yolo.

## Einrichtung und Ablauf

Arbeitsverzeichnis: Repository-Hauptverzeichnis.

```bash
python -m pip install -e '.[camera,viewer,yolo]'
```

```bash
rs-lab view --source camera --weights /pfad/zu/deinem/modell.pt
```

Boxen, Klassen, optionale Track-IDs und Z-Werte im Livebild. Modell muss lokal existieren.

## Experiment

Vergleiche zentrale/seitliche Position, Verdeckung und fehlende Tiefe. Nächster Ausbau: Instanzmaske statt Boxzentrum.

## Fehler und Grenzen

Kein gültiger Tiefenwert: depth unknown; Klassifikation und Distanzqualität getrennt beurteilen. Siehe auch [CLI/Formate](../../docs/cli.md) und [Hardware-Abnahme](../../docs/hardware-validation.md).

## Weiter

[Vorheriges Thema](../09_object_dimensions/TUTORIAL.md) · [Nächstes Thema](../11_tracking/TUTORIAL.md) · [Index](../../TUTORIAL_INDEX.md)
