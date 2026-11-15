# 09 — Sichtbare Ausdehnung und Objektvermessung

**Stand:** Sichtbare AABB geprüft; vollständige Objektvermessung geplant.

## Lernziel und Einordnung

Maximaler minus minimaler XYZ-Wert ergibt achsenparallele Ausdehnung. Objektmaße brauchen zusätzliche Segmentierung, Referenzebene und Verdeckungsbehandlung.

## Dateien und Voraussetzungen

In diesem Projektordner liegt diese Anleitung. Der ausführbare Code wird gemeinsam im Paket unter `src/realsense_lab/` verwendet: **geometry.py / bounding_box**. So entstehen keine voneinander abweichenden Kopien der Kameraaufnahme. Python >=3.11, Umgebung aus der Einrichtung; Zusatzbedarf: core.

## Einrichtung und Ablauf

Arbeitsverzeichnis: Repository-Hauptverzeichnis.

```bash
python -m pip install -e .
```

```bash
rs-lab analyze --source demo
```

visible_bounds beschreibt die sichtbare Gesamtszene, nicht ein fertig segmentiertes Objekt.

## Experiment

Isoliere im Python-Kern eine geeignete Objektregion. Vergleiche sichtbare Box und Referenzkörper; kennzeichne verdeckte Seiten als unbekannt.

## Fehler und Grenzen

Hintergrund in der Punktmenge vergrößert die Box; nicht als Objektabmessung ausgeben. Siehe auch [CLI/Formate](../../docs/cli.md) und [Hardware-Abnahme](../../docs/hardware-validation.md).

## Weiter

[Vorheriges Thema](../08_planes_obstacles/TUTORIAL.md) · [Nächstes Thema](../10_yolo_3d/TUTORIAL.md) · [Index](../../TUTORIAL_INDEX.md)
