# 07 — Punktwolken und Export

**Stand:** Deprojektion/Farbzuordnung/PLY geprüft; Liveansicht offen.

## Lernziel und Einordnung

Stride überspringt Pixel für geringere Punktzahl. Nur endliche positive Tiefen bis zum Limit werden exportiert; Farben kommen aus den zugehörigen RGB-Pixeln.

## Dateien und Voraussetzungen

In diesem Projektordner liegt diese Anleitung. Der ausführbare Code wird gemeinsam im Paket unter `src/realsense_lab/` verwendet: **geometry.py / frame_cloud; storage.py / write_ply**. So entstehen keine voneinander abweichenden Kopien der Kameraaufnahme. Python >=3.11, Umgebung aus der Einrichtung; Zusatzbedarf: core.

## Einrichtung und Ablauf

Arbeitsverzeichnis: Repository-Hauptverzeichnis.

```bash
python -m pip install -e .
```

```bash
rs-lab export --source demo --output artifacts/tutorial-07.ply
rs-lab analyze --source demo
```

Farbige ASCII-PLY in optischen Kamerakoordinaten und Punktwolkenstatistik.

## Experiment

Öffne PLY in einem 3D-Werkzeug. Untersuche die 1,2-m-Vordergrundfläche und den 2-m-Hintergrund. Drehe die Ansicht und prüfe die Achsen.

## Fehler und Grenzen

Erwarte keine geschlossene Oberfläche: eine einzelne Ansicht enthält nur sichtbare Punkte. Siehe auch [CLI/Formate](../../docs/cli.md) und [Hardware-Abnahme](../../docs/hardware-validation.md).

## Weiter

[Vorheriges Thema](../06_measurements/TUTORIAL.md) · [Nächstes Thema](../08_planes_obstacles/TUTORIAL.md) · [Index](../../TUTORIAL_INDEX.md)
