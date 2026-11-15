"""Application boundary for paired inspection reports and their exact source frame."""
from pathlib import Path

import numpy as np

from .storage import save_frame, write_json, write_ply


def save_scene(stem, frame, result, export_cloud=False):
    stem = Path(stem)
    paths = [stem.with_suffix(".npz"), stem.with_suffix(".json")]
    if export_cloud:
        paths.append(stem.with_suffix(".ply"))
    if any(path.exists() for path in paths):
        raise FileExistsError("Scene output already exists; choose a new session/name")
    save_frame(paths[0], frame)
    report = dict(result.report, snapshot_file=paths[0].name)
    write_json(paths[1], report)
    if export_cloud:
        stride = result.report["settings"]["stride"]
        cells = result.pixels//stride
        selected = result.labels[cells[:, 0], cells[:, 1]] > 0
        points, pixels = result.points[selected], result.pixels[selected]
        colors = frame.color[pixels[:, 0], pixels[:, 1]] if len(pixels) else np.empty((0, 3), np.uint8)
        write_ply(paths[2], points, colors)
