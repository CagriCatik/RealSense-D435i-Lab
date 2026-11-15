# 05 — Kamerageometrie und Deprojektion

**Stand:** Kernnumerik automatisch geprüft; reale Kalibrierung offen.

## Lernziel und Einordnung

Pinhole: X=(u-ppx)Z/fx und Y=(v-ppy)Z/fy. Verzeichnung wird nicht ignoriert: SDK-Rays oder explizite Ablehnung. Intrinsics müssen zur tatsächlich verwendeten Bildgeometrie passen.

## Dateien und Voraussetzungen

In diesem Projektordner liegt diese Anleitung. Der ausführbare Code wird gemeinsam im Paket unter `src/realsense_lab/` verwendet: **models.py / Intrinsics; geometry.py / deproject, frame_point**. So entstehen keine voneinander abweichenden Kopien der Kameraaufnahme. Python >=3.11, Umgebung aus der Einrichtung; Zusatzbedarf: core.

## Einrichtung und Ablauf

Arbeitsverzeichnis: Repository-Hauptverzeichnis.

```bash
python -m pip install -e .
```

```bash
rs-lab analyze --source demo --pixel 320 240
```

JSON mit XYZ in Metern, lokaler Tiefen-MAD und Anzahl gültiger Nachbarn.

## Experiment

Wähle Pixel links/rechts/oben/unten. Verifiziere die Vorzeichen. Berechne radialen Abstand als Norm von XYZ und vergleiche mit Z.

## Fehler und Grenzen

Ungültige Nachbarschaft: kein Messwert statt scheinbar null Meter. Siehe auch [CLI/Formate](../../docs/cli.md) und [Hardware-Abnahme](../../docs/hardware-validation.md).

## Weiter

[Vorheriges Thema](../04_depth_filters/TUTORIAL.md) · [Nächstes Thema](../06_measurements/TUTORIAL.md) · [Index](../../TUTORIAL_INDEX.md)
