# RealSense D435i Lab

Ein praktisches RGB-D-/IMU-Labor für Çağrı Çatık: Kamerafunktionen verstehen, Messungen nachvollziehen und daraus 3D-Wahrnehmungs- und Robotikprojekte entwickeln.

**Version 0.2.0:** Stationärer Szeneninspektor als erste zusammenhängende Anwendung: Referenzfläche kalibrieren, Objektflächen segmentieren, Positionen und sichtbare Ausdehnungen messen, Track-IDs anzeigen und gespeicherte Szenen vergleichen. Dazu bleiben Kameraadapter, Aufnahme/Wiedergabe, 3D Object Explorer, optionales YOLO, IMU und ROS-/TSDF-Einstiege verfügbar. Mobile Kartierung, vollständige Objektvermessung und Navigation sind Ausbauprojekte; siehe [Funktionsmatrix](docs/capabilities.md).

**Prüfstand:** Die automatischen Kern- und Integrationstests laufen ohne Kamera. Die D435i, grafische Desktopfunktionen und optionalen ML-/ROS-/Open3D-Integrationen müssen an deiner Hardware abgenommen werden. Dieses Repository ist keine Herstellerzertifizierung.

## Sofort ausprobieren — ohne Kamera

Python 3.11 oder neuer; Hauptziel: Ubuntu 24.04 / Python 3.12.

```bash
git clone https://github.com/CagriCatik/RealSense-D435i-Lab.git
cd RealSense-D435i-Lab
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
rs-lab analyze --source demo --pixel 320 240
rs-lab capture --source demo --frames 10 --output recordings/demo
rs-lab export --source replay --input recordings/demo --output artifacts/demo.ply
python -m unittest discover -s tests -v
```

Grafischen Explorer starten:

```bash
python -m pip install -e '.[viewer]'
rs-lab view --source demo
```

Der Explorer zeigt RGB, farbige Tiefe und eine Vogelperspektive der Punktwolke. **Leertaste** friert ein Bild ein; zwei Klicks im linken RGB-Bild messen den 3D-Abstand. `S` speichert einen RGB-D-Snapshot, `P` eine farbige PLY-Punktwolke, `M` die Zweipunktmessung als JSON, `Q` beendet. Die Vogelperspektive ist eine Projektion, kein frei drehbarer 3D-Renderer.

## Mit deiner D435i

Zuerst [Einrichtung](docs/setup.md) lesen und die Kamera im offiziellen RealSense Viewer prüfen.

```bash
python -m pip install -e '.[camera,viewer]'
rs-lab inspect --output artifacts/device.json
rs-lab view --source camera --config configs/default.json
rs-lab infrared --config configs/default.json
rs-lab capture --source camera --frames 100 --output recordings/session-001
rs-lab benchmark --source camera --frames 300 --output artifacts/stream-health.json
rs-lab imu --seconds 10 --output recordings/imu-001.csv
rs-lab imu-report --input recordings/imu-001.csv
```

Die vorgeschlagenen Profile werden vor dem Start als Kombination vom SDK auflösbar geprüft. Die Diagnose listet Einzelprofile; sie garantiert nicht, dass alle gemeinsam nutzbar sind. Kamera immer nur in einer Anwendung gleichzeitig öffnen.

## V1: Stationärer Szeneninspektor

```bash
# Zwei synthetische Objektflächen auf einer geneigten Referenzfläche analysieren
rs-lab scene --source demo --output recordings/scene-001 --export-cloud

# Gespeicherte Szene analysieren und mit dem ersten Bericht vergleichen
rs-lab scene --source replay --input recordings/scene-001 --baseline recordings/scene-001/scene_000000.json

# Interaktive Segmentierung und Objektmaße: Demo oder feste D435i
rs-lab view --scene --source demo
rs-lab view --scene --source camera --scene-config configs/scene.json
```

Im Szenenmodus zeigt das dritte Panel Referenzfläche (grün), geometrische Objekte (farbig), andere Messpunkte (dunkel) und fehlende Tiefe (schwarz). `C` kalibriert die Referenz neu. `S` speichert zusammengehörige RGB-D-, JSON- und Objekt-PLY-Dateien. Position, sichtbare Flächenausdehnung und Höhe relativ zur Referenz erscheinen im Bericht; die Anzeige zeigt Track-ID, Ausdehnungen und Höhe.

Die Kamera muss feststehen. Die Referenz ist eine vom Anwender ausgewählte dominante Fläche, kein automatisch bestätigter Boden. Die synthetische Demo enthält Flächen mit bekannten 12/18 cm Abstand zur Referenz; daraus folgt keine reale D435i-Genauigkeit. [Ablauf, Einstellungen und Grenzen](docs/scene-inspector.md)

## YOLO und räumliches Tracking

```bash
python -m pip install -e '.[camera,viewer,yolo]'
rs-lab view --source camera --weights /pfad/zu/deinem/modell.pt
```

Das Modell muss lokal vorhanden sein. Es wird kein Modell automatisch heruntergeladen. Entfernungen stammen aus dem Median einer kleinen Tiefennachbarschaft am Boxzentrum. Bei fehlender Tiefe bleibt die Entfernung unbekannt. Die metrische Zuordnung ist ein einfaches Lernverfahren; sie ersetzt keine robuste Instanzsegmentierung oder Wiedererkennung. [Details](projects/10_yolo_3d/TUTORIAL.md)

## Lernen und erweitern

| Einstieg | Inhalt |
|---|---|
| [Tutorial-Index](TUTORIAL_INDEX.md) | 16 Projekte in sinnvoller Reihenfolge |
| [Funktionsmatrix](docs/capabilities.md) | Was implementiert, geprüft oder noch geplant ist |
| [Spezifikation](docs/specification.md) | Hardwaregrenzen, Revisionen und Messbedingungen |
| [Architektur](docs/architecture.md) | Modulgrenzen, Einheiten und Datenfluss |
| [CLI](docs/cli.md) | Befehle und Aufnahmeformate |
| [Szeneninspektor](docs/scene-inspector.md) | Stationäre Anwendung, Aufnahmevergleich und Abnahme |
| [Hardware-Abnahme](docs/hardware-validation.md) | Konkrete Prüfungen an deiner Kamera |
| [Roadmap](docs/roadmap.md) | Ausbau bis Rekonstruktion, SLAM und Robotik |
| [Offizielle Quellen](docs/sources.md) | Hersteller, SDK, ROS-Wrapper und Integrationen |
| [ROS 2](ros2/README.md) | Jazzy-Einstieg mit RGB-D, IMU, TF und RViz |

## Projektregeln

- Längen in Metern; Tiefenwerte sind axiale Z-Werte, nicht automatisch euklidische Entfernung.
- Optische Achsen: x rechts, y unten, z vorwärts. ROS-Roboterachsen sind anders.
- Fehlende Tiefe ist unbekannt. Sie ist kein Beweis für freien Raum.
- Streuung/MAD ist keine garantierte Genauigkeit.
- Farb-/Tiefen-Ausrichtung löst räumliche Zuordnung; unterschiedliche Belichtungszeitpunkte und Verdeckungen bleiben relevant.
- Ausgaben werden nicht überschrieben. Verwende pro Versuch neue Namen.
- Aufnahmen, große Modelle und generierte Artefakte bleiben außerhalb von Git.

Lizenz: [MIT](LICENSE). Abhängigkeiten und Modellgewichte behalten ihre eigenen Lizenzen.
