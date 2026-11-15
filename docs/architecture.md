# Architektur

Ziel: dieselben Algorithmen mit Livekamera, synthetischen Daten und Wiedergabe betreiben. Abhängigkeiten werden an den Grenzen gehalten.

| Modul | Verantwortung | Darf externe Systeme kennen? |
|---|---|---|
| models | Frame und Intrinsics; Form-/Typvertrag | Nein |
| geometry | Deprojektion, Nachbarschaft, Punktwolke, Ebenen, sichtbare Ausdehnung | Nein |
| sources | Deterministische Demo und portable Wiedergabe | Dateiformat |
| storage | Exklusive NPZ-/JSON-/PLY-Ausgabe | Dateisystem |
| analysis | Qualitätskennzahlen und Streamgesundheit | Nein |
| tracking | Metrische, klassenabhängige Zuordnung | Nein |
| imu | CSV-Diagnose von Motion-Zeitreihen | Dateiformat |
| sdk | Gerätesuche, RGB-D, Filter, IR, Motion und native Aufnahme | pyrealsense2 |
| detection | YOLO-Inferenz und RGB/BGR-Übergang | Ultralytics |
| viewer | Darstellung, Tastatur und Mausinteraktion | OpenCV |
| reconstruction | TSDF-Integration mit bekannten Posen | Open3D |
| cli | Konfiguration, Quellenauswahl und Abläufe | Adapter orchestrieren |
| ros2 | Offiziellen ROS-Wrapper starten | ROS 2 |

Core importiert weder CLI noch SDK/GUI/ROS/ML-Adapter. Keine ROS-Installation für Standalone-Python. Kein eigener Kameratreiber: wir verwenden den offiziellen SDK-/ROS-Zugang.

## Frame-Vertrag

RGB uint8 H×W×3; Tiefe float H×W in Metern; passende Intrinsics; Framezähler; Zeitstempel mit Domain. Daten im Kern sind räumlich auf dasselbe Bildraster bezogen. Die SDK-Quelle richtet Tiefe auf RGB aus. Native IR-Bilder bekommen einen separaten Viewer, damit ihre Pixel nicht mit RGB-Intrinsics vermischt werden.

Pinhole-Rechnung akzeptiert nur ein verzeichnungsfreies Modell. Bei anderen Modellen erstellt der Adapter einmal je Geometrie ein Ray-Lookup mit der SDK-Deprojektion. Die Rays werden mit Snapshots gespeichert. Ein vom SDK nicht unterstütztes Deprojektionsmodell führt zu einem Fehler. Für Open3D-TSDF muss die Eingabe bereits pinhole-/rektifiziert sein; Rays allein machen eine verzerrte Farbkamera nicht TSDF-kompatibel.

Zeitstempel unterschiedlicher Domains werden nicht zur gemeinsamen Quellfrequenz verrechnet. Ein Hostdurchsatz ist nicht die Sensorbildrate. RGB-D-Ausrichtung ist keine universelle Garantie zeitgleicher Belichtung.

## Fehler- und Ressourcenverhalten

Kameraquellen sind Kontextmanager. Verarbeitungsausnahmen lösen `stop()` aus. Ausgaben verwenden exklusive Anlage; Snapshots werden zuerst vollständig in eine temporäre Datei geschrieben und dann exklusiv verlinkt. Das benötigt ein Dateisystem mit Hardlink-Unterstützung; für ungeeignete Netzlaufwerke lokal aufnehmen und anschließend kopieren.

Kalibrierung, Firmware und persistente Geräteeinstellungen werden nicht automatisch verändert. Der Explorer friert vor einer Zweipunktmessung ein Bild ein, damit beide Punkte denselben Aufnahmezeitpunkt haben.

## Tests

Die Tests prüfen numerische Achsen/Einheiten, ungültige Tiefe, Verzeichnung, Farbzuordnung, degenerierte Ebenen, Ausreißer, exklusive Speicherung, Wiedergabe, Konfigurationsfehler, Tracking-Gates, Zeitresets und Ressourcenfreigabe. Adapter-Mocks prüfen ausgewählte SDK-Fehlerpfade; sie ersetzen keine Geräteabnahme.
