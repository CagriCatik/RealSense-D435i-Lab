# D435i: Spezifikation und Grenzen

Grundlagen: [Herstellerproduktseite](https://www.realsenseai.com/products/depth-camera-d435i/) und [D400-Datenblatt, März 2026](https://www.realsenseai.com/wp-content/uploads/2026/03/RealSense-D400-Series-Datasheet-Mar-2026.pdf). Zuletzt als Quellen geprüft: 15.11.2026. Bei späteren Revisionen immer die konkret passende Tabelle heranziehen.

| Eigenschaft | D435i-Einordnung |
|---|---|
| Verfahren | Stereo-Tiefe mit IR-Projektor; kein ToF-Sensor |
| Tiefensensoren | Global Shutter; Tiefenausgabe bis 1280×720 bzw. bis 90 FPS, profilabhängig |
| Tiefensichtfeld | Produktangabe ungefähr 87° horizontal × 58° vertikal |
| RGB | Rolling Shutter; bis 1920×1080 bei 30 FPS |
| Bereich | Produktseite: ideal etwa 0,3–3 m; Datenblatt beschreibt zusätzliche bedingungsabhängige Bereiche |
| Min-Z | Etwa 28 cm bei maximaler Tiefenauflösung; kein universeller Mindestabstand für alle Profile |
| Tiefengenauigkeit | Produktseite nennt <2 % bei 2 m; verbindliche Bewertung nur unter den angegebenen Bedingungen |
| Motion | Dreiachsiger Beschleunigungssensor und dreiachsiges Gyroskop |
| Zusätzliche Bilder | Linker und rechter IR-Stream |

Keine Kombination der einzelnen Maximalwerte erfinden. `inspect` liefert angebotene Einzelprofile; der Kameraadapter prüft die gewünschte RGB-D-Kombination zusätzlich mit dem SDK. USB-Modus, Bandbreite und andere Streams wirken mit.

## IMU-Revisionen

Das Datenblatt unterscheidet unter anderem BMI055 und BMI085. Für die älteren BMI055-Tabellen werden 62,5/250 Hz Beschleunigung und 200/400 Hz Gyroskop genannt; für BMI085 100/200 Hz Beschleunigung und 200/400 Hz Gyroskop. Deshalb wählt die Aufnahme aus den tatsächlich angebotenen Motion-Profilen und speichert beide Zeitreihen getrennt. Nicht aus dem Modellnamen allein auf eine IMU-Revision schließen.

Beschleunigung hat im SDK die Einheit m/s², Drehrate rad/s. Die IMU liefert keine fertige driftfreie Position. Sie enthält keinen Magnetometer für eine absolute magnetische Gierreferenz. Die SDK-D435i-Dokumentation beschreibt Kalibrierung und die Beziehung zum Tiefenkoordinatensystem; ältere Textstellen nennen nur die damalige IMU-Revision.

## Messgrenzen

- Tiefe ist Z entlang der optischen Achse. Radiale Entfernung ist die Norm des 3D-Punktes.
- RGB und Tiefe haben unterschiedliche Sichtfelder; Randbereiche können nach Ausrichtung fehlen.
- Global Shutter der Tiefensensoren macht den RGB-Sensor nicht zum Global-Shutter-Sensor.
- Schwarze, glänzende, transparente oder strukturarme Flächen können ungültige oder falsche Tiefen erzeugen.
- Außenbetrieb ist kein Versprechen gleicher Qualität bei jedem Sonnenlicht.
- Hole Filling und temporale Persistenz können Werte ergänzen, die keine neue direkte Messung sind.
- Ein dominantes Ebenenmodell ist ohne Orientierung/Kontext nicht automatisch ein Bodenmodell.
- Eine sichtbare Punktwolkenausdehnung ist keine vollständige Objektabmessung.
- Ein konfigurierter Filterbereich erweitert nicht die physikalische Reichweite der Kamera.

Elektrische, mechanische, Temperatur-, Montage- und Synchronisationsgrenzen bleiben Gegenstand des vollständigen Datenblatts. Sie werden hier nicht als durch Software nachgewiesen markiert.
