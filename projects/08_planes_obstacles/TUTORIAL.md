# 08 — Ebenen und Hindernisbausteine

**Stand:** RANSAC-Ebene geprüft; Boden-/Hindernissemantik geplant.

## Lernziel und Einordnung

RANSAC verwirft Ausreißer; SVD verfeinert die Ebene. Ein großes Ebenenmodell kann Wand oder Tisch sein. Es wird nicht automatisch Boden genannt.

## Dateien und Voraussetzungen

In diesem Projektordner liegt diese Anleitung. Der ausführbare Code wird gemeinsam im Paket unter `src/realsense_lab/` verwendet: **geometry.py / fit_plane; analysis.py / summarize**. So entstehen keine voneinander abweichenden Kopien der Kameraaufnahme. Python >=3.11, Umgebung aus der Einrichtung; Zusatzbedarf: core.

## Einrichtung und Ablauf

Arbeitsverzeichnis: Repository-Hauptverzeichnis.

```bash
python -m pip install -e .
```

```bash
rs-lab analyze --source demo --output artifacts/tutorial-08.json
```

Dominante Ebene n.x+d=0 und Inlier-Anteil.

## Experiment

Variiere threshold/iterations über den Python-Kern und vergleiche Ausreißer. Für echte Bodenklassifikation brauchst du Schwerkraft-/Montagebezug.

## Fehler und Grenzen

Degenerierte oder kollineare Punktmengen: Ebene wird verworfen statt erfunden. Siehe auch [CLI/Formate](../../docs/cli.md) und [Hardware-Abnahme](../../docs/hardware-validation.md).

## Weiter

[Vorheriges Thema](../07_pointclouds/TUTORIAL.md) · [Nächstes Thema](../09_object_dimensions/TUTORIAL.md) · [Index](../../TUTORIAL_INDEX.md)
