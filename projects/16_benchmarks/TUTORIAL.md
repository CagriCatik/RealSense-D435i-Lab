# 16 — Qualität und Streamgesundheit

**Stand:** Kennzahlen und Zeit-/Sequenzfehler geprüft; Referenzmessungen offen.

## Lernziel und Einordnung

Demo läuft ungedrosselt: hohe Host-FPS ist keine Kameraleistung. Sequenzlücken sind Beobachtungen am ausgewählten Stream, keine vollständige USB-Verlustmessung.

## Dateien und Voraussetzungen

In diesem Projektordner liegt diese Anleitung. Der ausführbare Code wird gemeinsam im Paket unter `src/realsense_lab/` verwendet: **analysis.py / frame_health; docs/hardware-validation.md**. So entstehen keine voneinander abweichenden Kopien der Kameraaufnahme. Python >=3.11, Umgebung aus der Einrichtung; Zusatzbedarf: core; camera für Hardware.

## Einrichtung und Ablauf

Arbeitsverzeichnis: Repository-Hauptverzeichnis.

```bash
python -m pip install -e '.[core; camera für Hardware]'
```

```bash
rs-lab benchmark --source demo --frames 100 --output artifacts/tutorial-16.json
```

JSON mit Hostdurchsatz, beobachteten Sequenzlücken, Zeitdomains und medianem Quellintervall.

## Experiment

Wiederhole mit --source camera und verschiedenen Lasten. Für Messqualität führe H06 mit Referenzziel und wiederholten Aufnahmen aus.

## Fehler und Grenzen

Kompression, Analyse und Datenträger verändern Hostdurchsatz. Vergleich nur bei dokumentierten gleichen Bedingungen. Siehe auch [CLI/Formate](../../docs/cli.md) und [Hardware-Abnahme](../../docs/hardware-validation.md).

## Weiter

[Vorheriges Thema](../15_mapping_robotics/TUTORIAL.md) · [Nächstes Thema](../../docs/roadmap.md) · [Index](../../TUTORIAL_INDEX.md)
