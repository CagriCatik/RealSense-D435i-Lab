# V3 — Semantische Objektkarte

V3 erweitert eine V2-Kartensitzung um Objektlandmarken. Eine akzeptierte Kamerapose und gültige Tiefenpunkte machen aus einer 2D-Erkennung eine Beobachtung in Kartenkoordinaten. Wiederholte Beobachtungen werden klassenbezogen und räumlich zugeordnet. Die Karte enthält lokale Sitzungs-IDs und nachvollziehbare Belege, keine garantierte Objektidentität oder globale Referenz.

## Demo ohne Modell

```bash
rs-lab map --semantic --frames 12 --output recordings/semantic-001
rs-lab objects --input recordings/semantic-001/semantic_map.json --confirmed
```

Der NumPy-Demodetektor verwendet ausschließlich die bekannten Farben der Raumsimulation: `demo_crate` und `demo_cabinet`. Er ist kein trainiertes Modell und erkennt keine allgemeinen realen Objekte. Die Odometrie erhält weiterhin keine Sollposen. Die ausgeführte Standardsequenz liefert zwölf akzeptierte Bilder, zwei bestätigte Landmarken und 24 Beobachtungen; das belegt die Verarbeitungskette in dieser Szene, keine Hardware-/Modellgenauigkeit.

## Mit Kamera und YOLO

```bash
python -m pip install -e '.[camera,viewer,yolo]'
rs-lab map --source camera --semantic --weights /pfad/zu/modell.pt --semantic-config configs/semantic.json --frames 300 --output recordings/semantic-real-001 --preview
```

`--weights` verlangt eine lokale Datei. Detektions- und Segmentierungsmodelle werden unterstützt, reine Klassifikationsausgabe wird abgelehnt. Das Modell bestimmt die Klassen. Sein Dateiname und SHA256-Fingerabdruck werden protokolliert. Bei Segmentierung verwendet der Adapter `masks.xy`: Polygone in Originalbildkoordinaten nach der offiziellen [Ultralytics-Referenz](https://docs.ultralytics.com/reference/engine/results/). Bounding Boxes und Farbkonvertierung bleiben getrennt von der Kernauswertung.

Die Karten-Vorschau zeichnet aktuelle akzeptierte Objektboxen in RGB und bisher bekannte Landmarken in der Draufsicht. Der Text zeigt Sitzungs-ID und Klasse; tentative/confirmed unterscheiden sich farblich. Alte Landmarken bleiben nach Trackingverlust als bisherige Karte sichtbar, erhalten aber keine neuen Beobachtungen.

## Lokalisation

Ein Detektionsdatensatz enthält `label`, `confidence`, `xyxy=[x0,y0,x1,y1]` und optional `polygon_xy=[[x,y],...]`. Koordinaten beziehen sich auf das ausgerichtete RGB-/Tiefenraster. Der Kern prüft Klassenname, Konfidenz, Box und endliche Polygonkoordinaten (3 bis 2048 Punkte).

Ohne Polygon wird der Boxrand um `box_margin` verkleinert. Mit Polygon werden dessen gesampelte Innenpunkte verwendet; der Kern berechnet die Polygonzugehörigkeit ohne OpenCV. Nur endliche positive Tiefen bis `max_depth_m` zählen. Eine zu große Tiefen-MAD führt zu `mixed_depth`; sonst behält das Verfahren Punkte innerhalb `max(depth_band_m, 3*MAD)` um den Tiefenmedian. Es muss eine Mindestzahl von Punkten übrig bleiben.

Die Position ist der komponentenweise Median sichtbarer Kamerapunkte, mit der akzeptierten `camera_to_world`-Pose transformiert. Die beobachteten Min-/Max-Werte werden aus den transformierten sichtbaren Punkten gebildet. Es werden keine verdeckten Oberflächen oder Volumenschwerpunkte erfunden. Der Kern kann weiterhin von dominantem Hintergrund in einer falschen Box/Maske getäuscht werden; Tiefenfilter sind kein Nachweis korrekter Instanzsegmentierung.

## Zuordnung und Bestätigung

| Regel | Verhalten |
|---|---|
| Klasse | Nur exakt gleiche Klassen werden zusammengeführt |
| Räumliches Gate | Neue Position muss nahe an einer bestehenden Landmarkenposition liegen |
| Eins-zu-eins pro Frame | Eine Landmarke bekommt höchstens eine Beobachtung aus diesem Bild |
| Doppelte Boxen | Überlappende Boxen derselben Klasse werden nach Konfidenz reduziert |
| Neue Landmarke | Kein passender vorhandener Eintrag: neue Sitzungs-ID |
| Bestätigung | Ab `min_observations` unterschiedlichen Frame-Identitäten wird `tentative` zu `confirmed` |
| Trackingverlust | Keine Inferenz oder semantische Fusion ohne akzeptierte Pose |
| Kapazität | Neue Objekte oberhalb `max_landmarks` werden mit Begründung verworfen; bestehende Einträge bleiben nutzbar |

Die Zuordnung sortiert passende Klassen-/Distanzpaare und vergibt sie einmalig. Sie enthält keine gelernte Re-ID, globale optimale Zuordnung, Labelkorrektur, Bewegungsverfolgung oder Cross-Session-Zusammenführung. Gleiche Klassen in unmittelbarer Nähe, Verdeckung, falsche Klassen und driftende Kameraposen bleiben schwierige Fälle. Ein Objekt kann verschwinden und später wieder zugeordnet werden, solange Position und Klasse passen; korrekte Identität ist damit nicht bewiesen.

Position und Konfidenz werden über akzeptierte Beobachtungen gemittelt; Positionsstreuung wird mit einer laufenden Statistik gespeichert. Sie beschreibt Variation der sichtbaren Oberflächenpositionen und enthält auch Pose-/Blickwinkel-/Detektionsfehler. Sie ist weder kalibrierte Messunsicherheit noch eine statistisch kalibrierte Klassenwahrscheinlichkeit. Vereinigte sichtbare Boxen können durch Drift wachsen.

`person` ist standardmäßig ausgeschlossen. Andere bewegte Objekte werden nicht automatisch als dynamisch erkannt. Eine statische Landmarkenkarte braucht überwiegend statische Objekte; eine Änderung dieser Filter hebt diese Annahme nicht auf. Wiederholte Fehler können ebenfalls den Status `confirmed` erreichen.

## Quellenbezug und Wiedergabe

```bash
rs-lab map --source replay --input recordings/semantic-001 --semantic --frames 12 --output recordings/semantic-replay-001
# Ein bestimmtes Journal verwenden
rs-lab map --source replay --input recordings/semantic-001 --semantic --detections recordings/semantic-001/detections.jsonl --frames 12 --output recordings/semantic-replay-002
```

Replay findet das Detektionsjournal neben den Snapshots automatisch, sofern weder `--weights` noch `--detections` angegeben wurde. So kann derselbe Lauf ohne ML-Abhängigkeiten wiederholt werden. Ein neues lokales Modell kann stattdessen explizit mit `--weights` zur erneuten Inferenz eingesetzt werden.

Jede Detektionszeile enthält `detection_schema=1`, Zeitdomain, Framezähler, Zeitstempel, Quelldatei, Detektionen, Detektor-Metadaten und `frame_sha256`. Der Fingerabdruck umfasst Intrinsics, RGB, Tiefe und gegebenenfalls Rays samt Datentypen. Doppelte Identitäten, fehlende Zeilen oder ein geänderter Inhalt werden abgelehnt. Eine ursprünglich wegen Trackingverlust übersprungene Inferenz ist kein gültiger leeres-Detektions-Nachweis: Wenn eine neue Posekonfiguration dieses Bild wieder akzeptiert, muss dafür erneut inferiert werden.

`observations.jsonl` verknüpft jede akzeptierte Beobachtung mit Quelldatei, Detektionsindex, Box, Klasse, Konfidenz, Pose, Kamera-/Weltposition, sichtbaren Grenzen und Tiefenstatistik. Ablehnungen enthalten Gründe wie `insufficient_depth`, `mixed_depth`, `excluded_label`, `duplicate_detection`, `landmark_capacity` oder `pose_unavailable`. Die Landkarten-JSON behält die letzten `history_limit` Beobachtungen je Objekt; Zähler und erste/letzte Sichtung beziehen sich auf die gesamte Sitzung. Das vollständige Journal bleibt separat erhalten. Die Frame-Identitäten werden während der Sitzung zur Duplikaterkennung gespeichert.

## Ausgaben und Abfrage

Zusätzlich zu V2 entstehen `semantic_map.json`, `detections.jsonl`, `observations.jsonl`, `objects.csv` und `objects.ply`. PLY enthält einen Punkt je Landmarkenposition, einschließlich tentativer Einträge; IDs/Klassen stehen in JSON/CSV. Geometrische Voxelkarte und Objektpositionspunkte bleiben getrennte Dateien. Die Objektkarte übernimmt den Mappingstatus; bei Trackingverlust ist sie eine bisherige Teilkarte.

```bash
rs-lab objects --input recordings/semantic-001/semantic_map.json --label demo_crate --confirmed --min-observations 3
rs-lab objects --input recordings/semantic-001/semantic_map.json --details --output artifacts/objects-details.json
```

Die Klassenabfrage ignoriert Groß-/Kleinschreibung und vergleicht den vollständigen Namen. Standardausgabe: ID, Klasse, Status, Position, Beobachtungszahl und mittlere Detektionskonfidenz. `--details` ergänzt die im Kartenbericht gespeicherten Felder einschließlich jüngerer Belege. Alle Dateiausgaben werden exklusiv angelegt.

## Konfiguration und Grenzen

`configs/semantic.json` steuert Konfidenz, Punkt-Sampling, Mindestpunktzahl, Tiefenbereich, Boxrand, Tiefenband/MAD-Gate, Zuordnungsdistanz, Duplikat-IoU, Bestätigungszahl, Landmarkenkapazität, Historienlänge und ausgeschlossene Labels. Kamera-, Mapping- und Semantikkonfiguration bleiben getrennt. `--weights`, `--detections` und `--semantic-config` erfordern `--semantic`; Modell und aufgezeichnetes Journal schließen sich aus.

V3 nutzt den lokalen V2-Kartenrahmen der ersten Kamera und erbt dessen Drift-/Trackinggrenzen. Es gibt keine automatische Korrektur der Landmarken nach RTAB-Map-Loop-Closure und keinen automatischen Import von ROS-Posen. V4-Belegung, Navigation und dynamische Objekte sind weiter offen.

Geprüft werden bekannte starre Transformationen, Maskengeometrie, fehlende/gemischte Tiefe, Duplikate, Klassen-/Distanzgates, eins-zu-eins-Zuordnung, Historiengrenzen, Ausfall der Pose, Fingerabdrücke, Datenexport, Abfrage und reproduzierbarer Demo-Replay. Die YOLO-API-Grenze wird simuliert geprüft. Tatsächliche Modellqualität, GPU-Inferenz, Kamera und Desktop bleiben nach [Hardware-Abnahme](hardware-validation.md) zu prüfen.
