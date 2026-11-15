# V2 — Mobile lokale Kartierung

V2 schätzt Bewegung zwischen aufeinanderfolgenden Tiefenbildern, verkettet Kameraposen und fusioniert gültige Ansichten in eine farbige Voxelkarte. RGB wird für Aufnahme/Farbe verwendet; die lokale NumPy-Odometrie verwendet ausschließlich Geometrie. Sie ist kein photometrischer RGB-D-SLAM-Algorithmus. Ein separater ROS-Einstieg bindet RTAB-Map und IMU-Orientierung an.

## Demo und Wiedergabe

Aus dem Repository-Hauptverzeichnis mit aktivierter Umgebung:

```bash
python -m pip install -e .
rs-lab map --source demo --frames 12 --output recordings/map-demo-001
rs-lab map --source replay --input recordings/map-demo-001 --frames 12 --output recordings/map-replay-001
```

Die deterministische Demo bewegt eine Kamera in einer ray-gecasteten statischen Raumszene mit Wänden, Boden/Decke und zwei Quadern. Ihre Sollposen sind nur im Testgenerator verfügbar und werden dem Mapper nicht übergeben. Die automatische Prüfung vergleicht unabhängig geschätzte Posen mit den Sollposen und prüft Transformationsrichtung/Verkettung. Das ist ein Software-Nachweis, keine reale Genauigkeitsangabe.

`map` wählt standardmäßig `room`; andere Kommandos behalten ihre bisherigen Demo-Standards. `--demo-scene room` funktioniert auch mit `capture` und `view`. Die Raumdemo endet nach höchstens 61 Bildern; für längere Versuche Kamera oder eigene Aufnahmen verwenden.

## Mit fester Bildgeometrie bewegte Kamera

```bash
python -m pip install -e '.[camera,viewer]'
rs-lab map --source camera --frames 300 --mapping-config configs/mapping.json --output recordings/map-real-001 --preview
```

Die Kamera wird langsam bewegt; Auflösung/Intrinsics bleiben konstant. Die Szene sollte statisch sein und mehrere unterschiedlich orientierte sichtbare Flächen enthalten. Eine einzelne Wand kann geometrisch nicht alle sechs Bewegungsfreiheitsgrade bestimmen. Das Verfahren verwirft solche degenerierten Fälle, auch wenn die Bilder ähnlich aussehen. Dynamische Objekte, wiederholte Geometrie und große Bewegung können trotzdem falsche Korrespondenzen verursachen.

Die Projektion verlangt pinhole-/rektifizierte Intrinsics (`none`/`distortion.none`). Andere Verzeichnungsmodelle werden explizit abgelehnt; nicht einfach das Modellfeld umbenennen. SDK-Rays allein ersetzen keine dazu passende inverse Bildprojektion. Erst geeignete Rektifizierung ergänzen, falls dein aktives Profil das benötigt.

Die Vorschau zeigt RGB und eine X/Z-Draufsicht im Koordinatensystem der ersten Kamera. Gelb ist die bisher angenommene Trajektorie; bei Verlust erscheint ein roter Status. Sie verwendet einen festen Ausschnitt mit sechs Metern je kürzerer Panelkante; der sichtbare Bereich hängt vom Seitenverhältnis ab und läuft nicht mit der Kamera mit. `Q`/Escape beendet den Versuch mit Export der bisherigen Ergebnisse. Ohne `--preview` werden keine GUI-Pakete benötigt.

## Algorithmus und Qualitätsgates

1. Gültige Tiefenpunkte bilden eine gesampelte Quellpunktwolke.
2. Aus dem aktuellen Zielbild werden lokale Flächennormalen berechnet; Löcher, Randpunkte und Tiefensprünge werden ausgeschlossen.
3. Die aktuelle Transformationsschätzung projiziert Quellpunkte ins Zielbild; nur nahe 3D-Korrespondenzen werden akzeptiert.
4. Robuste point-to-plane-Gauss-Newton-Schritte schätzen eine starre Transformation. Konditionsprüfung erkennt unzureichende geometrische Beobachtbarkeit.
5. Überlappung, Konvergenz, Restfehler und maximale Bewegung müssen die konfigurierten Gates erfüllen.
6. Erst danach werden Weltpose und Voxelkarte aktualisiert.

Diese Gates sind Plausibilitätsprüfungen, kein Beweis korrekter Zuordnung oder kalibrierte Kovarianz. Es gibt keine Bewegungsprädiktion, Multiskalenpyramide, Loop Closure, globale Optimierung, IMU-Fusion oder automatische Relokalisierung im NumPy-Backend. Langfristige Drift bleibt bestehen. Für komplexere Kartierung dient der ROS-/RTAB-Map-Einstieg.

## Koordinaten und Ausgaben

`world` entspricht der ersten akzeptierten Kamera in optischen Achsen (x rechts, y unten, z vorwärts), metrisch. Es ist kein automatisch schwerkraftausgerichteter ROS-`map`-Frame. Die geschätzte Relativtransformation bildet vorherige Kamera auf aktuelle Kamera ab. Deshalb gilt `T_world_current = T_world_previous @ inverse(T_current_previous)`.

| Datei | Inhalt |
|---|---|
| `frame_XXXXXX.npz` | Jeder verarbeitete RGB-D-Frame, auch nach Trackingverlust, mit Geometrie/Zeitidentität |
| `tracking.jsonl` | Nach jedem Bild geflushtes Statusjournal mit relativen Qualitätskennzahlen; verworfene Bilder haben keine Weltpose |
| `trajectory.json` | Abschlussstatus, Konfiguration und Trajektorie mit Status je Bild |
| `manifest.json` | Nur akzeptierte Frames mit `camera_to_world`; Schema kompatibel zum vorhandenen `reconstruct`-Befehl |
| `map.ply` | Farbige Voxelmittelwerte der akzeptierten Ansichten |

Das Ausgabeverzeichnis muss neu sein. Die Voxelkarte mittelt Position/Farbe pro Zelle und begrenzt die Anzahl gespeicherter Zellen. Überschrittene Kapazität wird vor Änderungen an diesem Fusionsschritt erkannt. Stride/Voxelgröße beeinflussen Detailgrad und Laufzeit. Eine Voxelkarte beschreibt beobachtete Oberflächen, keine Navigationsbelegung oder zertifizierte Freifläche.

Optionaler nachgelagerter TSDF-Versuch, mit installiertem `scan`-Extra:

```bash
rs-lab reconstruct --manifest recordings/map-demo-001/manifest.json --output artifacts/map-demo-001-mesh.ply
```

Der vorhandene Open3D-Adapter bleibt separat integriert zu prüfen. Unsichere/driftende Odometrieposen werden durch TSDF nicht automatisch korrigiert.

## Zustände und Fehler

Das erste ausreichend gültige Bild erhält die Identitätspose (`initialized`); diese Initialisierung beweist noch keine geometrische Beobachtbarkeit. Ab dem nächsten Bild erfolgen alle Odometriegates. Akzeptierte Bilder heißen `tracking`. Fehlende Tiefe/Überlappung, degenerierte Geometrie, fehlende Konvergenz, große Bewegung, Zeitrücksprung/Domainwechsel oder Voxelkapazität führen zu `lost` und verriegeln die Fusion bis zu einer neuen Sitzung. Folgeframes bleiben zur Diagnose gespeichert, bekommen aber keine erfundene Pose. Eine andere Bildgeometrie wird ebenfalls verworfen.

Exitcode 0 bedeutet: die angeforderte bzw. verfügbare Sequenz wurde ohne erkannten Trackingverlust verarbeitet. Er bedeutet keine nachgewiesene Maßhaltigkeit. Exitcode 2 bei Trackingverlust lässt die gültige Teilkarte und Diagnosen bestehen. Abbruch, unzulässige Verzeichnung oder Dateisystemfehler können einen unvollständigen Versuch hinterlassen; Snapshots/Journal bleiben dann vorhanden, Abschlussdateien sind nicht garantiert. Bei einer neuen Szene/Kamerapose eine neue Sitzung beginnen; Teilkarten werden nicht automatisch zusammengefügt.

## Parameter

`configs/mapping.json` ist von Kamera- und Szenenkonfiguration getrennt. `stride`, `max_depth_m`, `correspondence_m`, `normal_edge_m`, `min_correspondences`, `min_overlap`, `max_rmse_m`, `max_translation_m`, `max_rotation_rad`, `max_condition`, `iterations`, `voxel_m` und `max_voxels` steuern die oben beschriebenen Schritte. Ausgangswerte sind Vorschläge für kleine Bewegungen, keine Kameraspezifikation. Größere Gates können Fehlzuordnungen akzeptieren; sie sind kein Ersatz für langsamere Bewegung oder bessere Sicht.

## ROS 2 / RTAB-Map

Nach Installation kompatibler ROS-2-Jazzy-/RealSense-/RTAB-Map-Pakete sowie `imu_filter_madgwick`:

```bash
source /opt/ros/jazzy/setup.bash
ros2 launch "$PWD/ros2/mapping.launch.py" database_path:=/absoluter/pfad/neue-sitzung.db
```

Das Zielverzeichnis vorher anlegen. Dieser Launch startet die Kamera selbst; vorher Standalone-Lab, RealSense Viewer und andere Treiber schließen. Er verwendet unseren Kamera-Launch, filtert IMU-Orientierung und startet RGB-D-Odometrie, Mapping und Visualisierung. Er übergibt kein `-d` zum Löschen vorhandener Datenbanken. Für jeden neuen unabhängigen Scan eine neue Datenbankdatei wählen; bestehende Datenbanken werden von RTAB-Map nach dessen Verhalten weiterverwendet.

Die Konfiguration wurde anhand des offiziellen [D435i-Beispiels](https://github.com/introlab/rtabmap_ros/blob/ros2/rtabmap_examples/launch/realsense_d435i_color.launch.py) erstellt, verwendet aber unsere `/camera/camera/...`-Topics, approximative Bildsynchronisation und Best-Effort-Abonnements. Tatsächliche QoS, Topics, Zeitbezüge und TFs mit der installierten Wrapper-Version prüfen. IMU-Orientierung ohne Magnetometer ist keine absolute Gierreferenz. NumPy-Sitzung und RTAB-Map sind zwei getrennte Backend-Wege; ihre Karten werden nicht automatisch fusioniert.

ROS-/Kamera-/GUI-Abnahme steht aus. Vor einem mobilen Roboterbetrieb zuerst Referenzraum, Trajektorie, Trackingverlust, Drift, TF und Aufzeichnung/Wiedergabe prüfen. Eine [statische semantische Objektkarte](semantic-mapping.md) ist mit V3 als optionaler NumPy-Sitzungsaufsatz vorhanden. Autonome Fahrt und robuste Robotikwahrnehmung bleiben V4; RTAB-Map-Loop-Closure aktualisiert diese NumPy-Landmarken noch nicht automatisch.
