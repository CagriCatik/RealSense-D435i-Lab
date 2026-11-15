# Roadmap zur vollständigen Laborabdeckung

Die erste Version enthält eine ausführbare Basis. Die folgenden Arbeitspakete schließen die in der Funktionsmatrix explizit offenen Teile. Ein Projekt wird erst nach Softwareprüfung und separater Integrations-/Hardwareprüfung als abgenommen geführt.

| Paket | Ergebnis | Abnahme |
|---|---|---|
| R1 Hardware-Baseline | H01–H11 mit deiner D435i; SDK/Firmware/USB dokumentiert | Wiederholbarer Live-/Replay-Versuch und geprüfte Aufnahmeraten |
| R2 Gerätesteuerung | Explizite Optionsänderung, Profilwahl, Presets und Advanced-Mode-JSON mit Validierung | Nicht unterstützte Optionen sauber abgewiesen; vorher/nachher archiviert |
| R3 Vollständige Sensoraufnahmen | Gemeinsame RGB/Depth/IR/IMU-Aufnahme, vollständige Metadaten und Extrinsics | Streamanzahl, Profile, Timestamp-Domains und Wiedergabe geprüft |
| R4 Qualitätslabor | ROI-Zeitreihen, Fill-Rate, Ebenen-RMSE, Bias, Decimation und Profil-/Filter-Sweeps | Referenzszene plus echte Messprotokolle; kein pauschales Genauigkeitsversprechen |
| R5 Objektvermessung | V1 enthält Referenzsegmentierung, Cluster und sichtbare Maße; optimierte Objektbox und Verdeckungsstatus bleiben offen | Synthetischer Kern geprüft; Referenzkörper/physische Maße noch offen |
| R6 Räumliche Detektion | Instanzmaske, robuste Objekt-Tiefe, ausreißerfeste Position | Boxzentrum-versus-Maskenvergleich, schwierige Fälle und ungültige Tiefe |
| R7 Tracking/Fusion | Bewegungskompensation, bessere Zuordnung, IMU-Orientierung und VIO-Anbindung | Zeitsprung, Verdeckung, kreuzende Objekte, bewegte Kamera |
| R8 Freier Raum | Boden anhand Orientierung bestätigen, Cluster, Belegung und unbekannte Bereiche | Kein ungültiger Tiefenpixel wird als frei behandelt |
| R9 Handscanner | RGB-D-Registrierung, Trackingverlust-Erkennung, TSDF und Mesh-Nachbearbeitung | Prüfkörper, Loop-/Posefehler und Rekonstruktionsmaßstab |
| R10 ROS-Mapping | Geprüfte RTAB-Map-Anbindung, Kamera-/Roboter-TF, Aufzeichnung | Mapping einer Referenzstrecke und nachvollziehbarer Drift-/Loopvergleich |
| R11 Robotik | Costmap-Anbindung, Odometrie/LiDAR-Fusion, später Navigation | Erst Wiedergabe/Simulation, dann kontrollierter Hardwareversuch |
| R12 Mehrkamera | Extrinsische Kalibrierung, Synchronisation, USB-Budget, Punktwolkenfusion | Zusatzhardware, elektrische Synchronisationsbedingungen und Zeitfehler geprüft |

Die zusammenhängende Anwendung startet mit [V1: stationärer Szeneninspektor](scene-inspector.md). V1-Software ist implementiert, reale Kamera-/Desktop-Abnahme bleibt offen. V2 ergänzt mobile Kartierung/Kamerapose, V3 eine semantische Objektkarte und V4 Robotikwahrnehmung.

Empfohlene Reihenfolge für Çağrı: R1 → R2/R3 → R4 → R6 → R8 → R10. Das verbindet deine Computer-Vision-Arbeit früh mit deiner ROS-2-Robotik. R5 und R9 sind eigene, gut vorzeigbare Mess-/Scanprojekte.
