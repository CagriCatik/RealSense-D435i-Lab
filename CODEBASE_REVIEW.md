# Entwicklungsprüfung 0.1.0

## Ergebnis

Das neue Repository hat eine gemeinsame RGB-D-Verarbeitung statt duplizierter Projektskripte. Numerik, Aufzeichnungsformat, Wiedergabe und Tracking sind automatisch geprüft. Kamera-, GUI-, ML-, Open3D- und ROS-Zugänge sind ausdrücklich getrennte Integrationsbereiche. Vollständige D435i-Funktionsabdeckung ist die Roadmap, nicht der behauptete Auslieferungszustand.

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
