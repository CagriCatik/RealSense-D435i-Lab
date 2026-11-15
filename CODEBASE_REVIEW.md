# Entwicklungsprüfung 0.4.0

## Ergebnis

Das neue Repository hat eine gemeinsame RGB-D-Verarbeitung statt duplizierter Projektskripte. Numerik, Aufzeichnungsformat, Wiedergabe und Tracking sind automatisch geprüft. Kamera-, GUI-, ML-, Open3D- und ROS-Zugänge sind ausdrücklich getrennte Integrationsbereiche. Vollständige D435i-Funktionsabdeckung ist die Roadmap, nicht der behauptete Auslieferungszustand.

## V1-Szeneninspektor

Neu: stationäre Referenzkalibrierung, Objektcluster mit 3D-Nachbarschaftsgate, sichtbare Maße/Höhe, lokale IDs, Replay und Baseline-Vergleich. Dazu kommen gepaarte JSON-/NPZ-/Objekt-PLY-Ausgabe sowie ein Explorer-Modus. Eine geneigte synthetische Referenz und zwei Flächen in 12/18 cm Abstand dienen als numerischer Nachweis. Referenzverlust liefert keine veralteten Objektwerte. Kamerabewegung entlang der Ebene kann trotzdem unentdeckt bleiben; feste Montage ist erforderlich. UI-Grenztests ersetzen keine echte Desktopabnahme.

## V2 lokale Kartierung

Neu sind geometrische projektive point-to-plane-Odometrie, beobachtbarkeits-/residuen-/bewegungsabhängige Annahme, inverse Poseverkettung, farbige Voxelmittelung mit Kapazitätsgrenze und ein verriegelter Trackingverlust-Zustand. Die Raumdemo liefert unabhängige Sollposen; diese werden nicht in die Verarbeitung eingespeist. Automatische Tests prüfen die Schätzung, Rotations-/Translationsverkettung, Einzelwand-Degeneration, Zeitfehler, Kapazitätsfehler, Journal/Manifest und Replay. Die Karten-Vorschau wird an einer simulierten UI-Grenze geprüft. Ein eigener ROS-Launch für Kamera/IMU/RTAB-Map wird nur syntaktisch geprüft. Das NumPy-Verfahren verwendet Tiefe, nicht RGB-Photometrie, und hat weder Loop Closure noch IMU-Fusion oder globale Optimierung. Reale Drift-/Robustheitsnachweise bleiben offen.

## V3 semantische Objektkarte und README

V3 lokalisiert Detektionen in Maskenpolygonen oder inneren Boxregionen, filtert Tiefe und transformiert sichtbare Punkte mit akzeptierten Kameraposen. Statische Landmarken werden klassen-/distanzabhängig eins-zu-eins zugeordnet. Tests prüfen Trennung gleicher Klassen, bewegte Kamera bei gleichem Weltobjekt, ungültige/gemischte Tiefe, Klassen-/Konfidenz-/Duplikatgates, Historien- und Kapazitätsgrenzen sowie Abfrage/Export. Frame-Fingerabdrücke verhindern stillen Replay mit geänderten RGB-D-Daten. Die Modell-API-Grenze wird simuliert geprüft; die komplette Demo verwendet ausdrücklich bekannte synthetische Farben statt eines trainierten Modells. Reale Detektion, Posefehler und schwierige Identitäten bleiben offen. Das README enthält einen dynamischen Workflow-Badge, deklarierte Versions-/Ziel-/Lizenz-/Hardware-Badges sowie eine regenerierbare Abbildung der ausgeführten Demo.

## Geprüfter Umfang

Python-Paket, Konfigurationen, Unit-/CLI-/Adaptergrenztests, ROS-Launch, Workflow und alle 16 Lernprojekte wurden bei Erstellung geprüft. Die Projektordner enthalten Tutorials; sie verwenden die gemeinsamen Module unter src/realsense_lab und behaupten keine eigenen nicht vorhandenen Skripte. Lokale Markdownlinks und die Projektanzahl werden automatisch geprüft.

| Bereich | Befund |
|---|---|
| Aufnahme/Geometrie | Einheiten und Achsen explizit; Geometrievertrag, Tiefenskalierung und SDK-Fehlerpfade getestet |
| Replay/Export | RGB-D-Metadaten/Rays erhalten; Schema- und Überschreibschutz geprüft |
| Filter/IR/Motion | SDK-Adapter vorhanden; konkrete Profile, Filterqualität und echte Raten müssen an Hardware gemessen werden |
| Detektion/Tracking | Inferenz optional; Zuordnung numerisch geprüft; Boxzentrum- und Kamerabewegungsgrenzen dokumentiert |
| Rekonstruktion | Bekannte starre Posen erforderlich; keine automatische Registrierung, kein ausgeführter Open3D-Nachweis |
| ROS 2 | Offizieller Wrapper wird eingebunden; Launch nur syntaktisch geprüft |
| Curriculum | 16 Tutorials mit tatsächlichen Kommandos/Bausteinen; geplante Projekte entsprechend markiert |
| Abhängigkeiten | Kern nur NumPy; SDK/GUI/YOLO/Open3D lazy; Versionsbereiche noch keine Hardware-Lockdatei |

## Offene Integrationsrisiken und nächste Schritte

1. An einer D435i die Profilkombination, RGB-Depth-Ausrichtung, deprojizierte Geometrie und IMU-Raten nach H01–H12 prüfen.
2. Mit konkretem SDK-/Firmwarestand native Container und Wiedergabe-EOF prüfen. Nur RGB8/BGR8-Native-Farbframes werden akzeptiert.
3. Optionalen YOLO- und Open3D-Adapter installieren und mit Referenzdaten integriert prüfen. Der Open3D-Dokumentationsabruf war bei der Erstellung nicht erfolgreich.
4. ROS-Launch mit einer festgehaltenen Jazzy-/Wrapper-/SDK-Kombination testen; reale Topics, TF und QoS bestätigen.
5. Danach Roadmap R2–R4 für vollständige Gerätesteuerung, Sensoraufzeichnung und Qualitätsnachweise bearbeiten.

Keine realen Hardware-, Tiefengenauigkeits-, Modell- oder SLAM-Ergebnisse wurden erfunden. Die automatischen Prüfungen erlauben keine Herstellerkonformitätsaussage.
