"""Detection validation and robust visible-surface localization. NumPy only."""
from dataclasses import dataclass
import json
from pathlib import Path

import numpy as np

from .geometry import frame_cloud
from .odometry import transform_points, validate_pose


@dataclass(frozen=True)
class SemanticConfig:
    confidence: float = .5
    stride: int = 4
    min_points: int = 12
    max_depth_m: float = 3.
    box_margin: float = .15
    depth_band_m: float = .025
    max_depth_mad_m: float = .08
    association_m: float = .25
    duplicate_iou: float = .6
    min_observations: int = 3
    max_landmarks: int = 1000
    history_limit: int = 100
    excluded_labels: tuple = ("person",)

    def __post_init__(self):
        for name in ("stride", "min_points", "min_observations", "max_landmarks", "history_limit"):
            if type(getattr(self, name)) is not int or getattr(self, name) < 1:
                raise ValueError(f"{name} must be a positive integer")
        for name in ("confidence", "max_depth_m", "depth_band_m", "max_depth_mad_m", "association_m", "duplicate_iou"):
            value = getattr(self, name)
            if type(value) not in (int, float) or not np.isfinite(value) or value <= 0:
                raise ValueError(f"{name} must be positive and finite")
        if self.confidence > 1 or self.duplicate_iou > 1:
            raise ValueError("Confidence and duplicate_iou must be <=1")
        if type(self.box_margin) not in (int, float) or not 0 <= self.box_margin < .5:
            raise ValueError("box_margin must be in [0,0.5)")
        if not isinstance(self.excluded_labels, (tuple, list)) or not all(
                isinstance(label, str) and label.strip() for label in self.excluded_labels):
            raise ValueError("excluded_labels must be a list of non-empty strings")

    @classmethod
    def load(cls, path=None):
        if path is None:
            return cls()
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(data, dict) or set(data)-set(cls.__dataclass_fields__):
            raise ValueError("Semantic config must be an object with known keys")
        return cls(**data)


def validate_detection(item):
    if not isinstance(item, dict) or not isinstance(item.get("label"), str) or not item["label"].strip():
        raise ValueError("Detection needs a non-empty class label")
    confidence = item.get("confidence")
    if type(confidence) not in (int, float) or not np.isfinite(confidence) or not 0 <= confidence <= 1:
        raise ValueError("Detection confidence must be in [0,1]")
    box = np.asarray(item.get("xyxy"), dtype=float)
    if box.shape != (4,) or not np.isfinite(box).all() or box[0] >= box[2] or box[1] >= box[3]:
        raise ValueError("Detection box must be finite [x0,y0,x1,y1] with positive area")
    polygon = item.get("polygon_xy")
    if polygon is not None:
        polygon = np.asarray(polygon, dtype=float)
        if polygon.ndim != 2 or polygon.shape[1] != 2 or not 3 <= len(polygon) <= 2048 or not np.isfinite(polygon).all():
            raise ValueError("Mask polygon needs 3..2048 finite image-coordinate vertices")
    return box, polygon


def box_iou(a, b):
    low, high = np.maximum(a[:2], b[:2]), np.minimum(a[2:], b[2:])
    overlap = np.prod(np.maximum(high-low, 0))
    union = np.prod(a[2:]-a[:2])+np.prod(b[2:]-b[:2])-overlap
    return float(overlap/union)


def _inside_polygon(pixels, polygon):
    x, y = pixels[:, 1], pixels[:, 0]
    inside = np.zeros(len(pixels), bool)
    for a, b in zip(polygon, np.roll(polygon, -1, axis=0)):
        if a[1] == b[1]:
            continue
        crosses = (a[1] > y) != (b[1] > y)
        inside ^= crosses & (x < (b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0])
    return inside


def _localize(points, pixels, box, polygon, pose, cfg):
    low, high = box[:2].copy(), box[2:].copy()
    if polygon is None:
        margin = (high-low)*cfg.box_margin
        low, high = low+margin, high-margin
    y, x = pixels[:, 0], pixels[:, 1]
    selected = (x >= low[0]) & (x < high[0]) & (y >= low[1]) & (y < high[1])
    if polygon is not None:
        selected &= _inside_polygon(pixels, polygon)
    xyz = points[selected]
    if len(xyz) < cfg.min_points:
        raise ValueError("insufficient_depth")
    median = float(np.median(xyz[:, 2]))
    mad = float(np.median(np.abs(xyz[:, 2]-median)))
    if mad > cfg.max_depth_mad_m:
        raise ValueError("mixed_depth")
    xyz = xyz[np.abs(xyz[:, 2]-median) <= max(cfg.depth_band_m, 3*mad)]
    if len(xyz) < cfg.min_points:
        raise ValueError("insufficient_depth")
    camera_center = np.median(xyz, axis=0)
    world = transform_points(xyz, pose)
    return {"xyz_camera_m": camera_center.tolist(),
            "xyz_world_m": transform_points(camera_center[None, :], pose)[0].tolist(),
            "visible_min_world_m": world.min(axis=0).tolist(),
            "visible_max_world_m": world.max(axis=0).tolist(),
            "depth_mad_m": mad, "sampled_points": len(xyz),
            "localization": "polygon_depth" if polygon is not None else "inner_box_depth"}


def localize_detections(frame, detections, pose, config=None):
    cfg = config or SemanticConfig()
    pose = validate_pose(pose)
    if not isinstance(detections, list):
        raise ValueError("Detector output must be a list")
    points, pixels = frame_cloud(frame, cfg.stride, cfg.max_depth_m)
    candidates, rejected = [], []
    for index, item in enumerate(detections):
        try:
            box, polygon = validate_detection(item)
        except (ValueError, TypeError) as exc:
            rejected.append({"detection_index": index, "reason": "invalid_detection", "detail": str(exc)})
            continue
        if item["confidence"] < cfg.confidence or item["label"] in cfg.excluded_labels:
            reason = "excluded_label" if item["label"] in cfg.excluded_labels else "low_confidence"
            rejected.append({"detection_index": index, "reason": reason})
            continue
        candidates.append((index, item, box, polygon))
    accepted, retained = [], []
    for index, item, box, polygon in sorted(candidates, key=lambda row: (-row[1]["confidence"], row[0])):
        if any(item["label"] == label and box_iou(box, other) >= cfg.duplicate_iou for label, other in retained):
            rejected.append({"detection_index": index, "reason": "duplicate_detection"})
            continue
        retained.append((item["label"], box))
        try:
            location = _localize(points, pixels, box, polygon, pose, cfg)
        except ValueError as exc:
            rejected.append({"detection_index": index, "reason": str(exc)})
            continue
        accepted.append(dict(location, detection_index=index, label=item["label"],
                             confidence=item["confidence"], xyxy=box.tolist()))
    return accepted, rejected
