# V1 — Stationärer Szeneninspektor

Eine fest montierte D435i beobachtet eine dominante Referenzfläche und geeignete Objekte auf deren Kameraseite. RGB-D-Aufnahme, Geometrie, Segmentierung, Messwerte, Tracking, Darstellung und Wiedergabe verwenden denselben Verarbeitungspfad. V2 ergänzt später Kamerapose und mobile Kartierung.

## Erster Versuch ohne Kamera

Aus dem Repository-Hauptverzeichnis mit aktivierter Python-Umgebung:

```bash
python -m pip install -e .
rs-lab scene --source demo --frames 3 --output recordings/scene-demo-001 --export-cloud
rs-lab scene --source replay --input recordings/scene-demo-001 --frames 3 --baseline recordings/scene-demo-001/scene_000000.json
```

Die Demo enthält eine geneigte Ebene und zwei getrennte rechteckige Flächen in 12 bzw. 18 cm Abstand zur Ebene. Sie ist ein geometrischer Testdatensatz mit Rauschen und fehlenden Tiefenpixeln, keine fotorealistische Aufnahme oder vollständiges Volumenmodell. Die Tests vergleichen die medianen Referenzabstände mit diesen Sollwerten. Das zusätzlich ausgegebene 95. Perzentil liegt bei Rauschen etwas über dem Median.

`scene` und `view --scene` verwenden standardmäßig diese Demo. Bestehende Kommandos behalten ihre Box-Demo. Mit `--demo-scene tabletop` lässt sich die neue Szene beispielsweise auch mit `capture` aufnehmen.

## Interaktive Anwendung

```bash
python -m pip install -e '.[viewer]'
rs-lab view --scene --source demo
```

Mit Kamera zusätzlich das `camera`-Extra installieren:

```bash
rs-lab inspect
rs-lab view --scene --source camera --config configs/default.json --scene-config configs/scene.json
```

Kamera fixieren, geeignete Tiefenabstände einhalten und einen überwiegend freien Referenzausschnitt wählen. `configs/scene.json` ist getrennt von Kamera-/Filtereinstellungen. Die Referenz wird im ersten geeigneten Bild kalibriert und bleibt dann fest.

| Bedienung | Wirkung |
|---|---|
| Leertaste | Bild einfrieren/fortsetzen |
| Zwei Klicks im linken RGB-Panel | Bestehende Zweipunktmessung im eingefrorenen Bild |
| C | Referenz und geometrische Tracks zurücksetzen; neu kalibrieren |
| S | Passenden JSON-Bericht, RGB-D-Snapshot und farbige Objektpunktwolke speichern |
| P | Gesamte sichtbare Punktwolke exportieren |
| M | Zweipunktmessung als JSON speichern |
| Q / Escape | Beenden |

Panel 1 zeigt RGB, Objektboxen, IDs und sichtbare Ausdehnung/Höhe. Panel 2 zeigt Tiefe. Panel 3 zeigt Segmentierung. Farben bezeichnen Segmentnummern, keine Klassen oder dauerhaft stabilen Track-IDs. Schwarz bedeutet unbekannte Tiefe; dunkelgrau andere Messpunkte; braun kleine unbestätigte Objektkandidaten; grün die Referenz. Die Segmentierungsauflösung folgt dem Sampling-Stride.

## Verarbeitung und Messgrößen

1. SDK/Replay liefert ausgerichtete Tiefe in Metern und passende Bildgeometrie.
2. RANSAC/SVD bestimmen eine dominante Ebene in der Referenz-ROI.
3. Die Einheitsnormale wird zur Kameraseite orientiert. Das ist kein Schwerkraftnachweis.
4. Punkte im positiven Abstandsband werden Objektkandidaten.
5. Zusammenhängende Nachbarn im gesampelten Raster werden nur bei ausreichender 3D-Nähe gruppiert.
6. Ausreichend große Gruppen erhalten Messwerte und lokale geometrische Track-IDs.

| Berichtsfeld | Bedeutung |
|---|---|
| `xyz_m` | Komponentenweiser Median sichtbarer Punkte in optischen Kamerakoordinaten; kein Volumenschwerpunkt |
| `height_median_m` | Median des vorzeichenbehafteten Abstands zur Referenz |
| `height_above_reference_m` | 95. Perzentil dieses Abstands; kein zertifiziertes Höhenmaß |
| `visible_extent_camera_m` | Sichtbare XYZ-Ausdehnung in Kameraachsen |
| `visible_extent_plane_m` | Sichtbare Ausdehnung entlang zweier fester Ebenentangenten und der Normalen; keine optimierte orientierte Objektbox |
| `reference_rmse_m` | RMS-Abstand aktuell als Ebeneninlier bewerteter Punkte; keine Gesamtmessgenauigkeit |
| `valid_sample_fraction` | Gültige gesampelte Punkte bis zum Maximalabstand / Rasterpunktzahl |
| `reference_inlier_fraction` | Anteil gültiger ROI-Punkte passend zur festen Referenz |
| `status` | `ok` oder `reference_lost`; bei Referenzverlust keine Objektmessungen |

Eine nur sichtbare Objektoberseite kann eine geringe sichtbare Ausdehnung in Normalenrichtung haben und trotzdem 12 cm über der Referenz liegen. Höhe und sichtbare Ausdehnung werden deshalb getrennt ausgegeben. Vollständige Maße verdeckter Körper bleiben ein Ausbauprojekt.

## Konfiguration

| Parameter | Zweck / Konsequenz |
|---|---|
| `reference_roi` | Normalisierte `[x0,y0,x1,y1]`-Region für Kalibrierung/Referenzprüfung; freie Fläche wählen |
| `plane_threshold_m` | Ebenentoleranz; zu groß vermischt nahe Objekte mit der Fläche |
| `min_plane_points`, `min_plane_fraction` | Mindestunterstützung der Referenz |
| `max_fit_points` | Obergrenze deterministisch gewählter Kalibrierpunkte |
| `min_height_m`, `max_height_m` | Kameraseitiges Abstandsband der Objektkandidaten |
| `cluster_gap_m` | Maximaler 3D-Abstand benachbarter gesampelter Punkte |
| `min_object_points` | Mindestpunktzahl bestätigter Gruppen |
| `stride` | Sampling; beeinflusst Punktzahl, kleinste Objektgröße und Durchsatz |
| `max_depth_m` | Szenentiefenlimit, unabhängig vom SDK-Filterlimit |

Beispiel für eine tatsächlich dort sichtbare freie Tischregion: `reference_roi: [0.05,0.7,0.95,0.95]`. Unbekannte Schlüssel, falsche Typen und ungültige Grenzen führen zu einem Fehler. Die Referenz muss anfangs dominant sein; automatisch wird nicht bewiesen, dass sie ein Tisch oder Boden ist.

## Aufnahme und Vergleich

```bash
rs-lab scene --source camera --frames 10 --scene-config configs/scene.json --output recordings/scene-real-001 --export-cloud
rs-lab scene --source replay --input recordings/scene-real-001 --frames 10 --baseline recordings/scene-real-001/scene_000000.json --output recordings/scene-compare-001
```

`--output` muss neu sein. Je Bild entstehen gleichnamige NPZ und JSON, optional PLY. JSON verweist auf die genaue Quelldatei. PLY enthält bestätigte Objektpunkte mit RGB-Farben, kein vervollständigtes Mesh. Ein Prozess-/Datenträgerfehler kann ein unvollständiges Dateipaar hinterlassen; fehlende Partnerdateien gelten nicht als vollständiger Versuch.

Der Vergleich ordnet Objekte einmalig nach nächster Position in Kamerakoordinaten zu und meldet Positions-, Höhen- und Ausdehnungsdifferenzen sowie nicht zugeordnete Objekte. Das Gate liegt derzeit bei 15 cm. Voraussetzung: **derselbe feste Kameraaufbau**. Keine Objektwiedererkennung oder Posekompensation. Abweichende Intrinsics/deutlich andere Ebenen werden abgelehnt. Gleiche Ebenen beweisen keine unveränderte Pose: Verschiebung entlang einer großen Ebene kann unauffällig bleiben.

## Abnahme und Grenzen

Automatisch geprüft: bekannte geneigte Referenz, zwei Höhen, ungültige Tiefe, 3D-Objekttrennung, Mindestgröße, Referenzverlust, Geometriewechsel, IDs, Baseline-Differenzen, Datenpaar/Replay, Segmentierungsfarben und ausgewählte UI-Aktionen mit simulierter OpenCV-Grenze. Die synthetische Segmentierungsdarstellung wurde visuell kontrolliert. Echte OpenCV-Desktopbedienung und Kameraabnahme stehen aus.

An deiner D435i: Referenzkörper und unabhängiges Messmittel verwenden, Kamera fixieren, mehrere Distanzen/Positionen/Wiederholungen aufnehmen. Bias, Streuung, fehlende Tiefe und Filterwirkung getrennt berichten. Referenz absichtlich verdecken oder Kamera bewegen und Statusverhalten prüfen. Referenzverlust erkennt nicht jede Kamerabewegung.

Berührende Objekte können verschmelzen; Löcher/grobes Sampling können Gruppen teilen. Nicht sichtbare Flächen werden nicht vervollständigt. Es wird keine befahrbare Fläche abgeleitet. Das geometrische Label lautet `geometry_object`; semantische Raumkarte und bewegte Kamera folgen mit V2/V3. Der vorhandene YOLO-Overlay kann mit `view --scene --weights ...` parallel laufen; Klassen werden noch nicht mit Segmentberichten fusioniert.
