# Funktionsmatrix

Stand 0.4.0. **Kern geprüft** heißt: automatischer Test mit synthetischen Daten. **Adapter vorhanden** heißt: ausführbarer Integrationscode, noch keine Hardware-/Desktop-/Modellabnahme. Kein Eintrag ist derzeit an einer physischen D435i in dieser Entwicklungsumgebung abgenommen.

| Funktion | Umsetzung | Softwareprüfung | Hardware/Integration | Referenz |
|---|---|---|---|---|
| Modell/Firmware/USB/Seriennummer | `inspect` | Fehler-/CLI-Pfade; Gerätedaten offen | Offen | S2–S5 |
| Angebotene Einzelprofile | `inspect` | Adapter vorhanden | Offen | S3, S5 |
| RGB-D-Profilkombination | SDK `can_resolve` beim Öffnen | SDK-Mocks | Offen | S3, S5 |
| RGB + axiale Tiefe in Metern | CameraSource / Frame | Kernvertrag geprüft | Offen | S1, S5 |
| Linkes/rechtes IR | `infrared` | Adapter vorhanden | Offen | S5 |
| Beschleunigung/Gyroskop | `imu` mit dynamischer Profilwahl | CSV-Auswertung geprüft | Offen, Rate/Lücken prüfen | S2, S4 |
| Intrinsics/Verzeichnung | Diagnose + Frame | Kern/Ray-Pfad geprüft | Offen | S5, S7 |
| RGB-Depth-Extrinsics/Ausrichtung | SDK-Alignment | Adapter vorhanden | Offen, Occlusion prüfen | S5, S7 |
| Vollständiger Extrinsics-Export | Offizieller SDK/ROS-Zugang; Lab-Export geplant | Nicht implementiert | Offen | S4, S5, S9 |
| Threshold/Disparity/Spatial/Temporal/Hole Filling | JSON + SDK-Filter | Adapter vorhanden | Vergleichsmessung offen | S6 |
| Decimation/Rotation/HDR-Filter | Ausbau nach Geräte-/SDK-Unterstützung | Nicht implementiert | Offen | S3, S6 |
| Belichtung/Gain/Emitter/Projektorsteuerung | Optionsbereiche lesbar; Ändern derzeit im offiziellen Viewer | Lab-Schreibzugang geplant | Offen | S3, S5 |
| Visual Presets / Advanced Mode JSON | Offizieller Viewer; eigener Import/Export geplant | Nicht implementiert | Offen | S5, S12 |
| Native RGB-D-Aufnahme/Wiedergabe | CameraSource | Adapter vorhanden | SDK-/Containerprüfung offen | S8 |
| Gemeinsame native RGB/Depth/IR/IMU-Aufnahme | Viewer/ROS-Workflow; Lab-Ausbau geplant | Nicht implementiert | Offen | S4, S8–S10 |
| Portable RGB-D-Aufnahme/Wiedergabe | NPZ-Schema 1 | Kern + End-to-End geprüft | Keine Rohdatenvollständigkeit | Eigenes Format |
| Pixel-zu-3D / Zweipunktabstand | Core + eingefrorenes Explorer-Bild | Numerik geprüft; GUI offen | Referenzmessung offen | S7 |
| Farbige Punktwolke / PLY | Core + CLI + Vogelperspektive | Export/Zuordnung geprüft | Liveansicht offen | S5, S7 |
| Dominante Ebene | RANSAC + SVD | Ausreißer/Degeneration geprüft | Reale Oberflächen offen | Eigener Algorithmus |
| Boden/Hindernisse/freier Raum | Ebenenbaustein vorhanden, Semantik/Belegung geplant | Nicht fertig | Offen | Ausbau |
| Sichtbare XYZ-Ausdehnung | `analyze` | Kern geprüft | Keine vollständige Objektvermessung | Eigenes Verfahren |
| Referenzgestützte sichtbare Objektmaße | `scene` / `view --scene`: feste Ebene, 3D-Cluster, Position/Ausdehnung/Höhe | Synthetische Numerik, Replay und UI-Grenze geprüft | Reale Referenzkörper/GUI offen; keine vollständigen Körpermaße | Eigenes Verfahren |
| Szenenvergleich | Einmalige geometrische Baseline-Zuordnung, signierte Messwertdifferenzen | Zuordnung/Fehlerfälle geprüft | Unveränderter Kameraaufbau erforderlich | Eigenes Verfahren |
| YOLO + räumliche Position | Explorer mit Zentrum; V3 mit Maskenpolygon oder innerer Box und Tiefenfilter | Adapter-/RGB-BGR-/Polygon-Grenze simuliert geprüft | Modell/GPU/Live offen | S14, S17 |
| Semantische Objektkarte | `map --semantic`: Weltpositionen, Klassen-/Distanzgates, Sitzungs-IDs, wiederholte Beobachtungen | Starre Transformation, Kamerawechsel, Zuordnung, Tiefe und Historienspeicher geprüft | Reale Objektqualität/Drift/Identität offen | Eigenes Verfahren |
| Semantik-Replay und Abfrage | Detektions-/Beobachtungsjournal, Frame-Fingerabdruck, JSON/CSV/PLY und `objects` | Demo-Replay, Inhaltsänderung, Export/Abfrage geprüft | Kein trainiertes Modell im synthetischen Nachweis | Eigene Formate |
| Metrisches Objekttracking | Klassen-Gate + Greedy-Zuordnung | ID/Gates/Zeitsprünge geprüft | Kamerabewegung nicht kompensiert | Eigenes Verfahren |
| IMU-Bias-/Rauschdiagnose | Stationäre CSV-Auswertung | Kern geprüft | Stationarität/Kalibrierung offen | S4 |
| IMU-Orientierungsfusion / VIO | Geplant | Nicht implementiert | Offen | S4 |
| TSDF mit bekannten Posen | Optionaler Open3D-Adapter | Syntax; noch kein Open3D-Lauf | Offen | S15 |
| Lokale automatische Registrierung | `map`: NumPy-Projektions-/point-to-plane-Odometrie und Poseverkettung | Bekannte Bewegung/Skalierung, Degeneration und Fehlermodi geprüft | Echte Kamera/Drift/Robustheit offen | Eigener Algorithmus |
| Farbige mobile Voxelkarte | Begrenzte Fusion akzeptierter Posen, Trajektorie/Journal/Replay/TSDF-Manifest | Synthetische Sequenz und Replay geprüft | Keine globale Optimierung; Open3D-Mesh separat offen | Eigene Verarbeitung |
| ROS 2 / TF / RViz | Upstream-Launch eingebunden, Anleitung | Syntax; ROS-Lauf offen | Offen | S9, S10 |
| ROS-SLAM / Navigation | RTAB-Map-Launch vorhanden; Nav2 bleibt geplant | ROS-Launch nur Syntaxprüfung; NumPy ist kein vollständiger SLAM-Backend | ROS-/Hardwareabnahme offen | S16 |
| Zeitstempel/Sequenzzähler | Pro Frame mit Domain | Kern geprüft | Echte Zeit-/Verlustmessung offen | S4, S8 |
| Vollständige SDK-Frame-Metadaten | Geplant | Nicht implementiert | Offen | S3 |
| Streamgesundheit/Hostdurchsatz | `benchmark` | Kern geprüft | Last-/USB-Prüfung offen | Eigene Messung |
| Tiefengenauigkeit/Fill-Rate/Rauschen | Statistik + manuelles Abnahmeverfahren | Teilweise | Referenzaufbau offen | S1, S2 |
| Tiefen-/IMU-Kalibrierung | Dokumentierter offizieller Workflow | Keine automatischen Geräteschreibzugriffe | Offen | S4, S11 |
| Mehrkamera/externe Synchronisation | Erweiterungsprojekt | Nicht implementiert | Zweite Kamera/Kabel nötig | S2, S13 |
| Elektrik/Mechanik/Umweltgrenzen | Datenblattreferenz | Keine Softwareprüfung möglich | Aufbau prüfen | S2 |

Quellen-IDs: [sources.md](sources.md). „Alles“ bedeutet hier eine überprüfbare Abdeckungsplanung, keine Behauptung, bereits jede SDK-Funktion und Anwendung fertiggestellt zu haben. Die offenen Funktionen stehen in [roadmap.md](roadmap.md).
