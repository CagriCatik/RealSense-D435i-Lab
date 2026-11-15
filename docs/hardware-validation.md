# Hardware-Abnahme

Noch nicht durchgeführt: keine physische D435i in dieser Entwicklungsumgebung, keine Desktop-/ROS-/GPU-/Open3D-Abnahme. Automatische Kernprüfungen sind davon getrennt.

## Versuchsprotokoll

Pro Sitzung Datum, OS/Kernel, Python-/SDK-/Wrapper-Version, Firmware, Gerät/Revision, Seriennummer, USB-Modus/Port/Kabel, Profilkombination, Projektor-/Belichtungseinstellung, Filterkonfiguration, Licht, Zieloberfläche, Referenzdistanz und Referenzmessmittel festhalten. Seriennummer beim öffentlichen Teilen bei Bedarf entfernen.

## Prüffolge

| Test | Vorgehen | Erwartung / Nachweis |
|---|---|---|
| H01 Gerät | `rs-lab inspect --output artifacts/device-H01.json` | D435i, RGB/Depth/IR und Motion vorhanden; tatsächliche Profile archiviert |
| H02 RGB-D | Viewer, danach `view --source camera` | Stabile Streams, korrekte Farbe, gültige zentrale Tiefe; keine zweite Kamera-App |
| H03 Ausrichtung | Farbige Objektkante vor Hintergrund | Räumliche Zuordnung plausibel; Verdeckung/Randlöcher separat notieren |
| H04 IR | `infrared` | Zwei plausible getrennte Stereobilder, keine Verwechslung mit RGB |
| H05 3D-Achsen | Kamera vor planem Ziel, Punkte rechts/unten anklicken | x rechts, y unten, z vorwärts; Entfernung in Metern |
| H06 Abstand | Ebene Referenz in mehreren Distanzen, u. a. 2 m | Bias, Streuung, Fill-Rate und Messbedingungen erfassen; nur passende Datenblattbedingung bewerten |
| H07 Bewegung | Bewegtes Objekt; raw/default/static-scene vergleichen | Temporal-Trails und ergänzte Tiefe sichtbar bewerten |
| H08 Persistenz | Live aufnehmen, Kamera schließen, NPZ wiedergeben | Geometrie, Farben und gespeicherte Zeit-/Frameidentität unverändert |
| H09 Native Aufnahme | Native Recording aufnehmen/öffnen | Container zur SDK-Version passend; nur aktivierte Streams erwarten |
| H10 IMU | 10 s stationär, danach kontrollierte Bewegung | Accel-Norm etwa g, Gyro stationär nahe Bias; tatsächliche Rate/Zeitschritte prüfen |
| H11 Last | `benchmark --source camera` mit mehreren Profilen | Sequenzlücken, Host-/Quellraten und USB-/CPU-/Datenträgerlast getrennt protokollieren |
| H12 YOLO | Bekanntes Objekt in mehreren Distanzen, Verdeckung | Boxzentrum, fehlende Tiefe, Label/ID und Position plausibel; keine Genauigkeitsgarantie |
| H13 ROS | Launch starten; Topics/TF/RViz prüfen | RGB, Depth, Cloud und Motion; Achsen/QoS/Zeiten plausibel |
| H14 TSDF | Geprüfte Posen und rektifizierte Aufnahmen integrieren | Oberfläche plausibel; Posekonvention und Maßstab unabhängig prüfen |
| H15 Fehlerpfad | Quelle beenden / unauflösbares Profil / Ausgabe existiert | Verständlicher Fehler; Kamera anschließend wieder nutzbar; keine überschriebenen Daten |

## V1: stationärer Szeneninspektor

H16: Kamera fest montieren, freie Referenz-ROI wählen, geeignete Körper mit unabhängig bekannten Höhen und sichtbaren Abmessungen aufnehmen. `view --scene` prüfen: Segmentierung, Zweipunktmessung, Freeze, C-Neukalibrierung und S-Dateipaar. Danach mit `scene --source replay` nachrechnen und Baseline-Differenzen prüfen. Referenz verdecken/Kamera bewegen: keine veralteten Objektwerte bei erkanntem Referenzverlust. Gleiche Ebene garantiert keine unveränderte Kamerapose. Reale Abnahme offen.

## V2: mobile lokale Kartierung

H17: Kamera langsam durch eine statische geometrisch vielfältige Referenzszene bewegen; `map` mit Aufzeichnung/Journal ausführen. Kamera-/Weltachsen und Maßstab prüfen. Bekannte kurze Wege und Rückkehr zum Start unabhängig vermessen, Drift/Verluste berichten. Einzelwand, fehlende Tiefe, schnelle Bewegung und Zeitfehler prüfen: nach erkanntem Verlust keine weitere Fusion oder aktuelle Weltpose. Teilkarte/Journal und deterministische Wiedergabe vergleichen. ROS-/RTAB-Map-Einstieg separat mit TF/QoS/IMU und neuer Datenbank abnehmen. Noch keine Freigabe für autonome Navigation.

## Tiefenqualität sauber bewerten

Kamera und Ziel fixieren. Eine ausreichend große ebene, geeignete Oberfläche und ein nachvollziehbares Referenzmessmittel verwenden. Abstand auf das definierte Kamera-/Sensorkoordinatensystem beziehen. ROI und mindestens einige hundert Frames pro Bedingung archivieren. Bias = mittlere/mediane gemessene Z minus Referenz-Z; relative Abweichung = Betrag(Bias)/Referenz-Z. Zeitliche Streuung und räumliche Ebenenabweichung getrennt berichten. Die Nachbarschafts-MAD im Explorer ist weder diese gesamte Prüfung noch eine kalibrierte Messunsicherheit.

Tiefen-/IMU-Kalibrierung zunächst mit dem offiziellen Tool und dessen Voraussetzungen ausführen. Vorher/nachher vergleichen; Kalibrierdaten sichern, soweit vom Tool unterstützt. Kein unkontrolliertes Schreiben in den Gerätespeicher.

Ergebnisse als neue Datei unter artifacts/ ablegen; erst nach tatsächlich ausgeführtem Test den Nachweisstatus in capabilities.md aktualisieren.
