# CLI und Formate

`rs-lab --help` und `rs-lab BEFEHL --help` sind die verbindliche Parameterübersicht.

| Befehl | Aufgabe |
|---|---|
| inspect | Geräte, Firmware, USB-Modus, Sensorprofile, Intrinsics und Optionsbereiche als JSON |
| view | Explorer mit Messung; optional YOLO und metrische Track-IDs |
| scene | Stationäre Referenzfläche, Objektsegmentierung und Vergleich; JSON-/NPZ-/PLY-Sitzung |
| infrared | Linkes/rechtes natives IR-Bild; eigene Kamerasitzung |
| capture | Ausgerichtete RGB-D-Snapshots; optional zusätzlich native SDK-Aufnahme |
| analyze | Erste Szene: Tiefenstatistik, sichtbare Ausdehnung, dominante Ebene, optionale Punktmessung |
| export | Erstes Bild als farbige PLY-Punktwolke |
| benchmark | Beobachtete Sequenzlücken, Zeitintervalle und Hostdurchsatz |
| imu | Eigenständige Motion-Sitzung; CSV mit getrennten Accel-/Gyro-Zeitstempeln |
| imu-report | Mittelwert, Streuung und beobachtete Motion-Rate |
| reconstruct | Open3D-TSDF mit expliziten bekannten Kameraposen |

## Quellen

`--source demo` ist Standard und benötigt keine Kamera. `camera` nutzt RGB und Tiefe. `replay --input VERZEICHNIS` liest alphabetisch sortierte Lab-NPZ-Dateien. `native --input DATEI` lässt das installierte SDK seine native Aufzeichnung öffnen. Keine automatische Formatkonvertierung und keine Behauptung, dass jede SDK-Aufnahme eine beliebige ROS-Bag-Datei ist.

`--frames` begrenzt die Verarbeitung. Demo/Wiedergabe werden bei Aufnahme und Benchmark nicht künstlich auf Sensorbildrate gedrosselt; der Viewer begrenzt seine Darstellung. Analyse/Export verwenden jeweils nur das erste Bild.

`--demo-scene box|tabletop` wählt die synthetische Szene. `scene` und `view --scene` wählen ohne Angabe tabletop; alle übrigen Befehle bleiben bei box. `scene --output` erwartet ein neues Verzeichnis und schreibt je Bild einen Bericht mit Snapshot. `--baseline` vergleicht gegen einen gültigen Bericht desselben festen Aufbaus. `--export-cloud` ergänzt Objekt-PLYs und braucht `--output`. [Szenenanleitung](scene-inspector.md)

```bash
rs-lab capture --source camera --frames 300 --output recordings/rgbd-001 --native-record recordings/native-001.bag
rs-lab view --source native --input recordings/native-001.bag
rs-lab analyze --source replay --input recordings/rgbd-001 --pixel 320 240
```

Die Dateiendung für native Aufnahmen muss zur installierten SDK-Version passen. SDK-Dokumentation und Beispiele aktueller Entwicklungsversionen beschreiben teils auch neuere Container. Das Lab erzwingt deshalb keine bestimmte native Dateiendung. Native Aufnahme enthält die hier aktivierten RGB-/Depth-Streams, nicht automatisch IR und Motion. Für eine gemeinsame vollständige Multisensor-Aufnahme zunächst den offiziellen Viewer bzw. ROS-Bag-Workflow nutzen. Lab-NPZ enthält gefilterte/ausgerichtete RGB-D-Daten, keine Rohstereo-/IMU-Daten.

## Snapshot-Schema 1

NPZ ohne Pickle: `color`, `depth_m`, `metadata` als JSON-Skalar, optional `rays`. Metadaten: Schema, Intrinsics inklusive Modell/Koeffizienten, Timestamp, Domain, Framezähler. Snapshot-Aufnahmen sind absichtlich eine einfache portable Schnittstelle; keine Echtzeit-/Kompressionsgarantie. Quellkonfiguration und Firmware separat mit dem Versuch archivieren.

## Filterkonfiguration

JSON mit strikter Schlüssel-/Typprüfung. `default.json` aktiviert räumliche Glättung; `raw.json` schaltet die drei Glättungs-/Füllfilter aus, enthält aber weiterhin einen großzügigen Tiefen-Threshold. Das ist kein Sensor-Rohdatenmodus. `static-scene.json` aktiviert zusätzlich temporale Filterung.

Kameraablauf: RGB-Ausrichtung → Threshold → optional Disparität → Spatial → Temporal → Tiefe → optional Hole Filling. Diese einfache Reihenfolge ist implementiert; in Qualitätsversuchen mit nativer Tiefenfilterung vor Ausrichtung vergleichen. Demo/portable Wiedergabe nutzen ihre vorhandenen Tiefendaten unverändert; SDK-Filter laufen nur auf SDK-Quellen. `max_depth_m` begrenzt zusätzlich Analyse und Punktwolkenexport; der Viewer skaliert seine Farbkarte damit.

Exitcodes: 0 Erfolg, 2 Eingabe-/Gerätefehler oder keine Kamera bei inspect, 130 Unterbrechung. GUI-Fehler ohne Desktop lassen sich nicht auf allen OpenCV-Builds als Python-Ausnahme behandeln.
