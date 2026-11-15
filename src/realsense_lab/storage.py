"""Portable aligned RGB-D snapshots. No pickle; exclusive, atomic writes."""
from dataclasses import asdict
import json
import os
from pathlib import Path
import tempfile

import numpy as np

from .models import Frame, Intrinsics


def save_frame(path, frame: Frame) -> None:
    path = Path(path)
    if path.suffix != ".npz":
        raise ValueError("Snapshots need a .npz extension")
    path.parent.mkdir(parents=True, exist_ok=True)
    metadata = {"schema": 1, "intrinsics": asdict(frame.intrinsics),
                "timestamp_ms": frame.timestamp_ms, "number": frame.number,
                "timestamp_domain": frame.timestamp_domain}
    fd, temp = tempfile.mkstemp(dir=path.parent, suffix=".npz")
    try:
        with os.fdopen(fd, "wb") as stream:
            arrays = {"color": frame.color, "depth_m": frame.depth_m,
                      "metadata": np.array(json.dumps(metadata))}
            if frame.rays is not None:
                arrays["rays"] = frame.rays
            np.savez_compressed(stream, **arrays)
        os.link(temp, path)  # fails if target exists, unlike rename/replace
    finally:
        os.unlink(temp)


def load_frame(path) -> Frame:
    with np.load(path, allow_pickle=False) as data:
        metadata = json.loads(str(data["metadata"].item()))
        if metadata["schema"] != 1:
            raise ValueError("Unsupported snapshot schema")
        k = metadata["intrinsics"]
        k["coeffs"] = tuple(k["coeffs"])
        return Frame(data["color"].copy(), data["depth_m"].copy(), Intrinsics(**k),
                     metadata["timestamp_ms"], metadata["number"],
                     metadata["timestamp_domain"],
                     data["rays"].copy() if "rays" in data else None)


def write_ply(path, points: np.ndarray, colors: np.ndarray) -> None:
    path = Path(path)
    if points.shape != colors.shape or points.ndim != 2 or points.shape[1] != 3:
        raise ValueError("Expected matching Nx3 XYZ and RGB")
    if not np.isfinite(points).all() or colors.dtype != np.uint8:
        raise ValueError("Expected finite points and uint8 colors")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="ascii") as stream:
        stream.write("ply\nformat ascii 1.0\n")
        stream.write(f"element vertex {len(points)}\n")
        stream.write("property float x\nproperty float y\nproperty float z\n")
        stream.write("property uchar red\nproperty uchar green\nproperty uchar blue\nend_header\n")
        for point, rgb in zip(points, colors):
            stream.write(" ".join(f"{float(v):.7f}" for v in point) + " "
                         + " ".join(str(int(v)) for v in rgb) + "\n")


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        json.dump(data, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write("\n")
