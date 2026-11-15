# 11 — Räumliches Tracking

**Stand:** Zuordnung, IDs, Ablauf und Zeitresets geprüft; Livequalität offen.

## Lernziel und Einordnung

Greedy-Zuordnung verwendet metrische Distanz und ein Gate. Geschwindigkeit ist Positionsänderung pro Zeit. Clock-Reset setzt Tracks zurück; fehlende Tiefe erzeugt keine falsche Nullposition.

## Dateien und Voraussetzungen

In diesem Projektordner liegt diese Anleitung. Der ausführbare Code wird gemeinsam im Paket unter `src/realsense_lab/` verwendet: **tracking.py / Tracker; viewer.py / show**. So entstehen keine voneinander abweichenden Kopien der Kameraaufnahme. Python >=3.11, Umgebung aus der Einrichtung; Zusatzbedarf: camera,viewer,yolo.

## Einrichtung und Ablauf

Arbeitsverzeichnis: Repository-Hauptverzeichnis.

```bash
python -m pip install -e '.[camera,viewer,yolo]'
```

```bash
rs-lab view --source camera --weights /pfad/zu/deinem/modell.pt
```

YOLO-Detektionen erhalten bei gültiger Tiefe klassenabhängige Track-IDs.

## Experiment

Lass zwei gleichartige Objekte kreuzen. Bewege die Kamera: ohne Egobewegungskompensation ist Geschwindigkeit relativ zur Kamera und kann irreführend sein.

## Fehler und Grenzen

ID-Wechsel bei Verdeckung ist eine bekannte Grenze; kein Re-ID-/Kalman-/Welttracking implementiert. Siehe auch [CLI/Formate](../../docs/cli.md) und [Hardware-Abnahme](../../docs/hardware-validation.md).

## Weiter

[Vorheriges Thema](../10_yolo_3d/TUTORIAL.md) · [Nächstes Thema](../12_imu/TUTORIAL.md) · [Index](../../TUTORIAL_INDEX.md)

## V3-Erweiterung

`rs-lab map --semantic --frames 12 --output recordings/semantic-demo-001` verbindet Detektion, Kamerapose und statische Objektlandmarken. Die Demo verwendet bekannte Farben; reale Inferenz benötigt ein lokales Modell. Klassen-/Distanzzuordnung, Quellenbezug, Fingerabdruck-Replay und `objects`-Abfrage stehen in der [V3-Anleitung](../../docs/semantic-mapping.md). Diese Karten-IDs sind von den kamerarelativ bewegten Tracks im bisherigen Explorer getrennt.
