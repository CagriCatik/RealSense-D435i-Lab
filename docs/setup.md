# Einrichtung

## Referenzumgebung

Hauptziel ist Ubuntu 24.04 LTS mit Python 3.12; ROS 2 Jazzy kommt optional hinzu. Der Kern setzt Python >=3.11 voraus. Die CI prüft nur den NumPy-Kern unter 3.11–3.13. Das bedeutet keine vollständige SDK-/GPU-/ROS-Freigabe für alle Versionen.

## 1. Hardware prüfen

1. D435i per geeignetem USB-3-Datenkabel direkt anschließen; zum ersten Test keinen Hub verwenden.
2. Offiziellen SDK-Installationsweg für dein Betriebssystem aus [sources.md](sources.md) wählen. Unter Linux gehören passende USB-Zugriffsregeln dazu; sonst kann die Kamera sichtbar, aber nicht zugreifbar sein.
3. `realsense-viewer` starten. Modellname, Seriennummer, Firmware, USB-Modus sowie RGB, Depth, IR und Motion prüfen.
4. Viewer vor dem Start des Labors schließen.

Keine automatischen Firmwareupdates. SDK und Firmware nach der Kompatibilitätstabelle einer konkreten SDK-Version kombinieren; für ROS zusätzlich die SDK-Anforderung des gewählten Wrapper-Releases beachten. Systeminstallation und Python-Bindings nicht unkontrolliert mischen.

## 2. Python-Umgebung

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[camera,viewer]'
rs-lab inspect
```

Windows PowerShell: `py -3.12 -m venv .venv`, danach `.venv\Scripts\Activate.ps1`. Die übrigen Python-/CLI-Befehle sind gleich. Bei Ausführungsrichtlinien die lokale Firmenregel beachten und bei Bedarf direkt `.venv\Scripts\python.exe` verwenden.

Die Extras sind absichtlich getrennt: `viewer`, `camera`, `yolo`, `scan`. Fehlt für deine Python-/OS-/CPU-Kombination ein `pyrealsense2`-Wheel, eine offiziell unterstützte Kombination wählen oder die Bindings nach offizieller SDK-Anleitung bauen. macOS/Apple Silicon und ältere Jetson-/JetPack-Umgebungen sind keine hier geprüften Kameraziele; dort vorerst den Demo-/Replay-Kern nutzen und die SDK-Plattformunterstützung separat prüfen.

Die Versionsbereiche in pyproject.toml sind keine Lockdatei. Für eine funktionierende Hardwareumgebung den tatsächlichen Stand festhalten:

```bash
python -m pip freeze > artifacts/python-environment.txt
rs-lab inspect --output artifacts/device-environment.json
```

Vorher `artifacts` anlegen, falls es noch nicht existiert. Ergänze OS, Kernel, Kamera-Seriennummer/Revision, USB-Topologie, Firmware und Wrapper-Version im Versuchsprotokoll.

## 3. Erster Liveversuch

```bash
rs-lab view --source camera --config configs/default.json
```

Das Profil ist eine Startempfehlung, keine garantierte Gerätekombination. Bei Fehlern zuerst `rs-lab inspect` und den offiziellen Viewer verwenden. 90 FPS Tiefe und maximale RGB-/Tiefenauflösung nicht gleichzeitig voraussetzen.

## Häufige Fehler

| Symptom | Nächster Schritt |
|---|---|
| Kein Gerät | Kabel, Anschluss, Zugriffsregeln und Viewer prüfen |
| Streamkombination unauflösbar | In Diagnose verfügbare Profile prüfen; Auflösung/FPS reduzieren |
| Kamera belegt | Viewer, ROS-Node und andere Kamera-Prozesse schließen |
| Kein GUI-Fenster | Desktop-/Display-Sitzung und OpenCV mit GUI-Unterstützung verwenden |
| Fehlende Tiefenpixel | Abstand, Oberfläche, Reflexion, Licht und Belichtung untersuchen |
| Fehler bei SDK-Deprojektion | Gemeldetes Verzeichnungsmodell untersuchen; keine stillschweigende Pinhole-Näherung |
| Schlechte YOLO-Distanz | Boxzentrum trifft Hintergrund/Loch; Segmentierung und robuste Objektregion als Ausbau |
| Aufnahme läuft langsam | NPZ-Kompression und Datenträger begrenzen Hostdurchsatz; native Aufnahme separat vergleichen |
