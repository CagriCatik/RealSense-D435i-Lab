# 06 — Interaktive 3D-Messung

**Stand:** Numerik geprüft; grafischer Messversuch offen.

## Lernziel und Einordnung

Beide Punkte stammen aus demselben eingefrorenen Frame. Ihre Tiefe wird lokal medianbasiert geschätzt. MAD beschreibt lokale Streuung und keine Hersteller-Messgenauigkeit.

## Dateien und Voraussetzungen

In diesem Projektordner liegt diese Anleitung. Der ausführbare Code wird gemeinsam im Paket unter `src/realsense_lab/` verwendet: **viewer.py / click; geometry.py / frame_point**. So entstehen keine voneinander abweichenden Kopien der Kameraaufnahme. Python >=3.11, Umgebung aus der Einrichtung; Zusatzbedarf: viewer.

## Einrichtung und Ablauf

Arbeitsverzeichnis: Repository-Hauptverzeichnis.

```bash
python -m pip install -e '.[viewer]'
```

```bash
rs-lab view --source demo
```

Nach Leertaste und zwei Klicks im linken Bild erscheint der euklidische 3D-Abstand. M speichert ein JSON-Protokoll.

## Experiment

Miss eine bekannte Strecke an deiner Kamera. Verändere die Nachbarschaft im Code und untersuche Kanten-/Hintergrundmischung.

## Fehler und Grenzen

Klick ohne Einfrieren oder in einem rechten Panel: keine Messung; zuerst Space und links klicken. Siehe auch [CLI/Formate](../../docs/cli.md) und [Hardware-Abnahme](../../docs/hardware-validation.md).

## Weiter

[Vorheriges Thema](../05_camera_geometry/TUTORIAL.md) · [Nächstes Thema](../07_pointclouds/TUTORIAL.md) · [Index](../../TUTORIAL_INDEX.md)
