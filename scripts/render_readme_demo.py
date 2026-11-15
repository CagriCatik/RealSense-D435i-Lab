"""Regenerate the README illustration from a real run of the synthetic V3 pipeline."""
import json
from pathlib import Path
import tempfile
from xml.sax.saxutils import escape

import numpy as np

from realsense_lab.mapping_app import map_session
from realsense_lab.odometry import MappingConfig
from realsense_lab.room_demo import MovingRoomSource
from realsense_lab.semantic_app import SemanticSession
from realsense_lab.semantic_sources import DemoDetector


def main():
    with tempfile.TemporaryDirectory() as directory:
        target = Path(directory)/"demo"
        summary = map_session(MovingRoomSource(12), target, MappingConfig(), 12,
                              semantic=SemanticSession(DemoDetector()))
        report = json.loads((target/"semantic_map.json").read_text())
        lines = (target/"map.ply").read_text().splitlines()
        data = np.array([[float(v) for v in row.split()] for row in lines[lines.index("end_header")+1:]])
    elements = ['<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="520" viewBox="0 0 1200 520" role="img" aria-labelledby="title desc">',
        '<title id="title">Synthetische semantische Objektkarte aus der V3-Pipeline</title>',
        '<desc id="desc">Zwölf RGB-D-Ansichten werden registriert; zwei anhand bekannter Demofarben erkannte Objektflächen werden zu Kartenobjekten zusammengeführt. Kein trainiertes Modell.</desc>',
        '<rect width="1200" height="520" rx="18" fill="#0d1524"/>',
        '<rect x="16" y="16" width="768" height="488" rx="12" fill="#142236"/>',
        '<text x="40" y="53" fill="#7ee4d0" font-family="sans-serif" font-size="14" letter-spacing="2">RGB-D → POSE → OBJECT MAP</text>',
        '<text x="40" y="82" fill="#e6eef7" font-family="sans-serif" font-size="21">Ausgeführte synthetische V3-Demo</text>']

    def pixel(point):
        x, y, z = point
        return 350+x*190+z*65, 425-z*105+y*105

    # Deterministic display sampling, not a new map estimation step.
    for row in data[::max(1, len(data)//1100)]:
        x, y = pixel(row[:3])
        color = '#'+''.join(f'{int(v):02x}' for v in row[3:])
        elements.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="1.2" fill="{color}" opacity="0.8"/>')
    path = ' '.join(f'{pixel(np.array(entry["camera_to_world"])[:3,3])[0]:.1f},{pixel(np.array(entry["camera_to_world"])[:3,3])[1]:.1f}'
                    for entry in summary["trajectory"] if entry["camera_to_world"] is not None)
    elements.append(f'<polyline points="{path}" fill="none" stroke="#f5c66b" stroke-width="4"/>')
    for index, obj in enumerate(report["objects"]):
        x, y = pixel(obj["xyz_world_m"])
        elements.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="8" fill="#101a2a" stroke="#7ee4d0" stroke-width="3"/>')
        elements.append(f'<text x="{x+14:.1f}" y="{y-12:.1f}" fill="#fff" font-family="sans-serif" font-size="14">{escape(obj["label"])}</text>')
        top = 204+index*111
        xyz = ', '.join(f'{value:.2f}' for value in obj["xyz_world_m"])
        elements.extend([
            f'<text x="815" y="{top}" fill="#7ee4d0" font-family="monospace" font-size="13">{escape(obj["object_id"])}</text>',
            f'<text x="815" y="{top+28}" fill="#e6eef7" font-family="sans-serif" font-size="22">{escape(obj["label"])}</text>',
            f'<text x="815" y="{top+52}" fill="#9fb4cc" font-family="sans-serif" font-size="14">XYZ [{xyz}] m</text>',
            f'<text x="815" y="{top+75}" fill="#9fb4cc" font-family="sans-serif" font-size="14">{obj["observation_count"]} Beobachtungen · {obj["status"]}</text>'])
    elements.extend([
        '<text x="815" y="64" fill="#e6eef7" font-family="sans-serif" font-size="24">Eine Karte. Stabile IDs.</text>',
        f'<text x="815" y="99" fill="#9fb4cc" font-family="sans-serif" font-size="16">{summary["frames"]} Frames · {len(report["objects"])} Objekte</text>',
        '<text x="815" y="133" fill="#7ee4d0" font-family="sans-serif" font-size="14">NumPy-Kern · offline reproduzierbar</text>',
        '<text x="40" y="477" fill="#9fb4cc" font-family="sans-serif" font-size="13">Optische Kartenachsen · gelb: geschätzter Kamerapfad · grün: Objektpositionen</text>',
        '<text x="815" y="460" fill="#f5c66b" font-family="sans-serif" font-size="13">Bekannte Demofarben, kein KI-Modell.</text>',
        '<text x="815" y="483" fill="#9fb4cc" font-family="sans-serif" font-size="13">Hardware-/Modellabnahme bleibt offen.</text>', '</svg>'])
    output = Path(__file__).resolve().parents[1]/"docs"/"assets"/"semantic-demo.svg"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text('\n'.join(elements)+'\n', encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
